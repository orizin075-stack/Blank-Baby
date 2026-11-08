package jp.oror.reborn.king;

import java.util.List;
import java.util.UUID;
import jp.oror.reborn.VillagerLife;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.AbstractIllager;
import net.minecraft.world.entity.monster.EnderMan;
import net.minecraft.world.entity.monster.Witch;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingChangeTargetEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The rebels against the king: the illagers (and witches), the piglins and the endermen (the user: once one turns
 * on the villager king, the evil villagers, the piglins and the endermen make friends with one; kill the king's
 * expeditions and they trade; their help is needed to bring the king down; they send their picked soldiers when one
 * uses the thing they give).
 * <ul>
 * <li>A friend: the king's enemy (KingCourt.ENEMY). The rebels take no friend for a target, unless that friend has just
 * struck them.</li>
 * <li>Their favour: each of the kingdom's expeditioners a friend kills (a villager on an expedition, a wandering party's
 * member) is 3, each of the king's people 5; each rebel the friend kills takes 5 off. At 5 they trade (used with an
 * empty hand), at 30 they sell the call of their lord's likeness.</li>
 * <li>Their horns (a goat horn they sell): blown, three of their picked soldiers come for five minutes, follow the one
 * who blew it and fight the king's people round them. The lord's call (a charm) brings the likeness of Azazel, their
 * lord, for three minutes.</li>
 * <li>Against the king: the AT field that turns aside all but the greatest blows gives way to the rebels' (their picked
 * soldiers' blows on him count eight times on it), and breaks at once under their lord's, his likeness's or his
 * lord's blade's (RebelLord.SLAYER): the king cannot be brought down without them.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RebelPact {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Rebels");
    public static final String ALLY = "OrorRebelAlly";
    public static final String OWNER = "OrorRebelOwner";
    public static final String UNTIL = "OrorRebelUntil";
    public static final String FAVOUR = "OrorRebelFavour";
    public static final String CALL = "OrorRebelCall";

    private RebelPact() {
    }

    public static boolean member(Entity e) {
        return e instanceof AbstractIllager || e instanceof Witch || e instanceof AbstractPiglin || e instanceof EnderMan;
    }

    static String faction(Entity e) {
        return e instanceof AbstractPiglin ? "piglin" : e instanceof EnderMan ? "ender" : "illager";
    }

    public static boolean friend(Player p) {
        // the king's enemy, or (056) one who carries a certificate of rebellion sealed in villagers' blood
        return p != null && (KingCourt.enemy(p) || RebelCertificate.carries(p));
    }

    public static int favour(Player p) {
        return KingCourt.kept(p).getInt(FAVOUR);
    }

    public static void addFavour(Player p, int delta) {
        CompoundTag k = KingCourt.kept(p);
        int before = k.getInt(FAVOUR);
        int after = Math.max(0, before + delta);
        k.putInt(FAVOUR, after);
        KingCourt.keep(p, k);
        if (before < 5 && after >= 5) {
            p.sendSystemMessage(Component.literal("叛逆者たち：王の犬を狩る者よ。我らと取引しよう。（素手で話しかけると取引できます）").withStyle(ChatFormatting.DARK_GREEN));
        }
        if (before < 30 && after >= 30) {
            p.sendSystemMessage(Component.literal("叛逆者たち：我らが主、アザゼル様の御力を貸そう。").withStyle(ChatFormatting.DARK_GREEN));
        }
    }

    // --------------------------------------------------------------------------------------------- friendship

    /** A rebel takes no friend for a target, unless the friend has just struck it; nor an ally its owner or another ally. */
    @SubscribeEvent
    public static void target(LivingChangeTargetEvent e) {
        LivingEntity who = e.getEntity();
        LivingEntity t = e.getNewAboutToBeSetTarget();
        if (t == null || who.level().isClientSide) {
            return;
        }
        if (member(who) && t instanceof Player p && friend(p) && !provoked(who, p)) {
            e.setCanceled(true);
            return;
        }
        if (who.getPersistentData().getBoolean(ALLY) && (t.getPersistentData().getBoolean(ALLY) || ownerOf(who) != null && t.getUUID().equals(ownerOf(who))
            || t instanceof Player p2 && friend(p2))) {
            e.setCanceled(true);
        }
    }

    static boolean provoked(LivingEntity who, Player p) {
        return who.getLastHurtByMob() == p && who.tickCount - who.getLastHurtByMobTimestamp() < 200;
    }

    static UUID ownerOf(Entity e) {
        CompoundTag d = e.getPersistentData();
        return d.hasUUID(OWNER) ? d.getUUID(OWNER) : null;
    }

    /** Those already set on a friend let go; allies at work (each half second). */
    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || !(m.level() instanceof ServerLevel sl) || m.tickCount % 10 != Math.floorMod(m.getId(), 10)) {
            return;
        }
        if (member(m) && m.getTarget() instanceof Player p && friend(p) && !provoked(m, p)) {
            m.setTarget(null);
            if (m instanceof AbstractPiglin) {
                m.getBrain().eraseMemory(MemoryModuleType.ATTACK_TARGET);
                m.getBrain().eraseMemory(MemoryModuleType.ANGRY_AT);
            }
        }
        if (m.getPersistentData().getBoolean(ALLY)) {
            ally(m, sl);
        }
    }

    /** One of the rebels' picked soldiers at work: gone when its time is up; fights the king's people near its owner; follows. */
    static void ally(Mob m, ServerLevel sl) {
        CompoundTag d = m.getPersistentData();
        if (sl.getGameTime() > d.getLong(UNTIL)) {
            sl.sendParticles(ParticleTypes.POOF, m.getX(), m.getY() + 1, m.getZ(), 20, 0.4, 0.8, 0.4, 0.05);
            m.discard();
            return;
        }
        UUID owner = ownerOf(m);
        Player p = owner == null ? null : sl.getPlayerByUUID(owner);
        LivingEntity t = m.getTarget();
        if (t == null || !t.isAlive() || t == p) {
            LivingEntity pick = null;
            if (p != null) {
                LivingEntity hurt = p.getLastHurtByMob();
                LivingEntity hit = p.getLastHurtMob();
                if (hurt != null && hurt.isAlive() && !hurt.getPersistentData().getBoolean(ALLY) && !member(hurt) && hurt.distanceTo(p) < 24) {
                    pick = hurt;
                } else if (hit != null && hit.isAlive() && !hit.getPersistentData().getBoolean(ALLY) && !member(hit) && hit.distanceTo(p) < 24) {
                    pick = hit;
                }
            }
            if (pick == null) {
                List<LivingEntity> foes = sl.getEntitiesOfClass(LivingEntity.class, m.getBoundingBox().inflate(20),
                    x -> x.isAlive() && (x instanceof RoyalMob || expeditioner(x)));
                pick = foes.stream().min((a, b) -> Double.compare(a.distanceToSqr(m), b.distanceToSqr(m))).orElse(null);
            }
            if (pick != null) {
                m.setTarget(pick);
            } else if (p != null) {
                double dd = m.distanceToSqr(p);
                if (dd > 32 * 32) {
                    m.teleportTo(p.getX() + sl.random.nextGaussian(), p.getY(), p.getZ() + sl.random.nextGaussian());
                } else if (dd > 36) {
                    m.getNavigation().moveTo(p, 1.2);
                }
            }
        }
    }

    // ------------------------------------------------------------------------------------------------- favour

    /** A kingdom's expeditioner: a villager on an expedition or in a wandering party. */
    public static boolean expeditioner(Entity e) {
        if (!(e instanceof Villager v)) {
            return false;
        }
        CompoundTag root = v.getPersistentData();
        return root.getBoolean("OrorWanderer") || root.hasUUID("OrorParty") || !VillagerLife.data(v).getString("Trip").isEmpty();
    }

    @SubscribeEvent
    public static void death(LivingDeathEvent e) {
        if (!(e.getSource().getEntity() instanceof ServerPlayer p)) {
            return;
        }
        LivingEntity dead = e.getEntity();
        if (dead instanceof RoyalMob) {
            if (friend(p)) {
                addFavour(p, 5);
            }
        } else if (expeditioner(dead)) {
            addFavour(p, 3);
            LOG.info("REBEL-FAVOUR {\"player\":\"{}\",\"favour\":{},\"for\":\"expeditioner\"}", p.getGameProfile().getName(), favour(p));
        } else if (member(dead) && friend(p)) {
            addFavour(p, -5);
        }
    }

    // ---------------------------------------------------------------------------------- the king's field gives way

    /** The rebels' blows on the king: their picked soldiers' count eight times on his field; their lord's break it. */
    @SubscribeEvent(priority = net.neoforged.bus.api.EventPriority.HIGHEST)
    public static void onKing(LivingIncomingDamageEvent e) {
        if (!KingCourt.isKing(e.getEntity()) || e.getEntity().level().isClientSide) {
            return;
        }
        RoyalMob king = (RoyalMob) e.getEntity();
        Entity by = e.getSource().getEntity();
        if (by instanceof Mob m && m.getPersistentData().getBoolean(ALLY)) {
            e.setAmount(e.getAmount() * 8F);
        }
        if (RebelLord.slayer(by) || RebelLord.slayer(e.getSource().getDirectEntity())) {
            king.sovereign().incoming(1.0E30F);
            e.setAmount(e.getAmount() * 10F);
            CompoundTag d = king.getPersistentData();
            d.putInt("OrorKingSlain", d.getInt("OrorKingSlain") + 1);
        } else if (GodSlayer.has(by)) {
            // (054) a god-slayer's blow breaks the field too (a later king, another kingdom's)
            king.sovereign().incoming(1.0E30F);
            e.setAmount(e.getAmount() * 5F);
        }
    }

    // ------------------------------------------------------------------------------------------ trades and horns

    @SubscribeEvent
    public static void spoken(PlayerInteractEvent.EntityInteract e) {
        if (e.getHand() != InteractionHand.MAIN_HAND || !member(e.getTarget()) || !(e.getEntity() instanceof ServerPlayer p)
            || !(p.level() instanceof ServerLevel sl) || !p.getMainHandItem().isEmpty() || !friend(p)) {
            return;
        }
        if (favour(p) < 5) {
            p.displayClientMessage(Component.literal("叛逆者たち：王の犬を狩ってから来い。（王の遠征隊を倒すと取引できるようになります）"), true);
            return;
        }
        e.setCanceled(true);
        e.setCancellationResult(InteractionResult.SUCCESS);
        String f = faction(e.getTarget());
        OrorMerchant.open(p, Component.literal(switch (f) {
            case "piglin" -> "ピグリンの闇市";
            case "ender" -> "エンダーマンの虚ろ市";
            default -> "叛逆者の武器庫";
        }), "rebel_" + f, offers(p, sl, f), (pl, o) -> addFavour(pl, 1));
    }

    static ItemStack horn(String faction) {
        ItemStack s = new ItemStack(Items.GOAT_HORN);
        CompoundTag t = new CompoundTag();
        t.putString(CALL, faction);
        s.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
        s.set(DataComponents.CUSTOM_NAME, Component.literal(switch (faction) {
            case "piglin" -> "叛逆の角笛（ピグリン精鋭）";
            case "ender" -> "虚空の呼び笛（エンダーマン精鋭）";
            default -> "叛逆の角笛（イリジャー精鋭）";
        }).withStyle(ChatFormatting.DARK_GREEN));
        s.set(DataComponents.RARITY, Rarity.RARE);
        return s;
    }

    static ItemStack lordCharm() {
        ItemStack s = new ItemStack(Items.ECHO_SHARD);
        CompoundTag t = new CompoundTag();
        t.putString(CALL, "azazel");
        s.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
        s.set(DataComponents.CUSTOM_NAME, Component.literal("叛神の召喚符（アザゼルの化身）").withStyle(ChatFormatting.DARK_PURPLE));
        s.set(DataComponents.RARITY, Rarity.EPIC);
        return s;
    }

    static MerchantOffers offers(Player p, ServerLevel sl, String faction) {
        MerchantOffers o = new MerchantOffers();
        switch (faction) {
            case "piglin" -> {
                o.add(KingCourt.offer(new ItemStack(Items.NETHERITE_SCRAP, 2), Items.GOLD_BLOCK, 4, null, 0, 8));
                o.add(KingCourt.offer(new ItemStack(Items.ANCIENT_DEBRIS), Items.GOLD_BLOCK, 3, null, 0, 8));
                o.add(KingCourt.offer(new ItemStack(Items.CRYING_OBSIDIAN, 8), Items.GOLD_INGOT, 6, null, 0, 8));
                o.add(KingCourt.offer(new ItemStack(Items.BLAZE_ROD, 6), Items.GOLD_INGOT, 8, null, 0, 8));
                o.add(KingCourt.offer(horn("piglin"), Items.GOLD_BLOCK, 12, null, 0, 3));
            }
            case "ender" -> {
                o.add(KingCourt.offer(new ItemStack(Items.ENDER_PEARL, 8), Items.EMERALD, 12, null, 0, 8));
                o.add(KingCourt.offer(new ItemStack(Items.ENDER_EYE, 4), Items.EMERALD, 16, null, 0, 8));
                o.add(KingCourt.offer(new ItemStack(Items.SHULKER_SHELL, 2), Items.EMERALD_BLOCK, 4, null, 0, 4));
                o.add(KingCourt.offer(new ItemStack(Items.CHORUS_FRUIT, 16), Items.EMERALD, 6, null, 0, 8));
                o.add(KingCourt.offer(horn("ender"), Items.EMERALD_BLOCK, 10, Items.ENDER_PEARL, 8, 3));
            }
            default -> {
                o.add(KingCourt.offer(new ItemStack(Items.TOTEM_OF_UNDYING), Items.EMERALD, 32, null, 0, 4));
                var ench = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
                ItemStack axe = new ItemStack(Items.DIAMOND_AXE);
                axe.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 5);
                axe.enchant(ench.getHolderOrThrow(Enchantments.UNBREAKING), 3);
                o.add(KingCourt.offer(axe, Items.EMERALD, 24, null, 0, 4));
                ItemStack bow = new ItemStack(Items.CROSSBOW);
                bow.enchant(ench.getHolderOrThrow(Enchantments.MULTISHOT), 1);
                bow.enchant(ench.getHolderOrThrow(Enchantments.QUICK_CHARGE), 3);
                o.add(KingCourt.offer(bow, Items.EMERALD, 20, null, 0, 4));
                o.add(KingCourt.offer(new ItemStack(Items.OMINOUS_BOTTLE), Items.EMERALD, 16, null, 0, 4));
                o.add(KingCourt.offer(horn("illager"), Items.EMERALD_BLOCK, 8, null, 0, 3));
            }
        }
        if (favour(p) >= 60) {
            // (054) their hidden grand magic, shown only to their truest friends
            o.add(KingCourt.offer(BrokenPhantasm.scroll(), Items.EMERALD_BLOCK, 32, Items.NETHER_STAR, 1, 1));
        }
        if (favour(p) >= 30) {
            o.add(KingCourt.offer(lordCharm(), Items.EMERALD_BLOCK, 16, Items.TOTEM_OF_UNDYING, 1, 2));
        }
        return o;
    }

    /** A horn blown, a charm broken: the rebels' picked soldiers come, or their lord's likeness. */
    @SubscribeEvent
    public static void used(PlayerInteractEvent.RightClickItem e) {
        ItemStack s = e.getItemStack();
        CustomData cd = s.get(DataComponents.CUSTOM_DATA);
        if (cd == null || !(e.getEntity() instanceof ServerPlayer p) || !(p.level() instanceof ServerLevel sl)) {
            return;
        }
        String call = cd.copyTag().getString(CALL);
        if (call.isEmpty()) {
            return;
        }
        e.setCanceled(true);
        e.setCancellationResult(InteractionResult.CONSUME);
        int n = summon(p, sl, call);
        if (n > 0) {
            s.shrink(1);
        }
    }

    /** Brings the picked soldiers (or the lord's likeness) to the player; how many came. */
    public static int summon(ServerPlayer p, ServerLevel sl, String call) {
        List<EntityType<? extends Mob>> who = switch (call) {
            case "piglin" -> List.of(EntityType.PIGLIN_BRUTE, EntityType.PIGLIN_BRUTE, EntityType.PIGLIN);
            case "ender" -> List.of(EntityType.ENDERMAN, EntityType.ENDERMAN, EntityType.ENDERMAN);
            case "azazel" -> List.of(EntityType.EVOKER);
            default -> List.of(EntityType.EVOKER, EntityType.VINDICATOR, EntityType.VINDICATOR);
        };
        long until = sl.getGameTime() + (call.equals("azazel") ? 3600 : 6000);
        int n = 0;
        var ench = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        for (EntityType<? extends Mob> t : who) {
            Mob m = t.create(sl);
            if (m == null) {
                continue;
            }
            double a = sl.random.nextDouble() * Math.PI * 2;
            var at = sl.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                net.minecraft.core.BlockPos.containing(p.getX() + Math.cos(a) * 3, p.getY(), p.getZ() + Math.sin(a) * 3));
            if (Math.abs(at.getY() - p.getY()) > 4) {
                at = p.blockPosition();
            }
            m.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, p.getYRot(), 0F);
            m.finalizeSpawn(sl, sl.getCurrentDifficultyAt(at), MobSpawnType.MOB_SUMMONED, null);
            m.setPersistenceRequired();
            CompoundTag d = m.getPersistentData();
            d.putBoolean(ALLY, true);
            d.putUUID(OWNER, p.getUUID());
            d.putLong(UNTIL, until);
            AttributeInstance hp = m.getAttribute(Attributes.MAX_HEALTH);
            if (call.equals("azazel")) {
                RebelLord.makeLord(m, true);
            } else {
                if (hp != null) {
                    hp.setBaseValue(Math.max(hp.getBaseValue(), 80));
                }
                m.setHealth(m.getMaxHealth());
                if (t == EntityType.VINDICATOR || t == EntityType.PIGLIN_BRUTE) {
                    ItemStack axe = new ItemStack(Items.NETHERITE_AXE);
                    axe.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 5);
                    m.setItemSlot(EquipmentSlot.MAINHAND, axe);
                    m.setDropChance(EquipmentSlot.MAINHAND, 0F);
                }
                m.setCustomName(Component.literal("叛逆の精鋭").withStyle(ChatFormatting.DARK_GREEN));
            }
            sl.addFreshEntity(m);
            sl.sendParticles(call.equals("ender") ? ParticleTypes.PORTAL : ParticleTypes.SMOKE, m.getX(), m.getY() + 1, m.getZ(), 40, 0.4, 0.9, 0.4, 0.2);
            n++;
        }
        sl.playSound(null, p.blockPosition(), call.equals("azazel") ? SoundEvents.EVOKER_PREPARE_SUMMON : SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS,
            2F, 0.7F);
        p.sendSystemMessage(Component.literal(call.equals("azazel") ? "アザゼルの化身：……王を、討つのだな。力を貸そう。" : "叛逆の精鋭が駆けつけた（5分間）")
            .withStyle(ChatFormatting.DARK_GREEN));
        LOG.info("REBEL-CALL {\"player\":\"{}\",\"call\":\"{}\",\"came\":{}}", p.getGameProfile().getName(), call, n);
        return n;
    }
}
