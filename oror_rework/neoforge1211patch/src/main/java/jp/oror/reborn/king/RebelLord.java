package jp.oror.reborn.king;

import it.unimi.dsi.fastutil.ints.IntList;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import jp.oror.reborn.royal.RoyalThreats;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.LongArrayTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.FireworkExplosion;
import net.minecraft.world.item.component.Fireworks;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.saveddata.SavedData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.ChunkEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) Azazel, the rebel against god, who reigns over the illagers from their city (the user: far weaker than the
 * villager king, but with a blade against him, so that the king cannot be brought down without him; beaten, he drops his
 * crown; presented, the villagers hold a festival; kept and not presented, its keeper is taken for an enemy and killed).
 * <p>
 * Azazel led the angels who fell for teaching men to forge weapons: the weapon-makers' lord. He comes, with his court,
 * the first time the centre of an illager city is loaded (an illager fortress gets his general); an evoker of 400
 * health, his boss bar shown to those he is set against. His blows (his own, his fangs', his vexes') break the king's
 * AT field at once and strike him tenfold (RebelPact.onKing). His likeness, called by his charm, is the same.
 * <p>
 * His crown, presented to the villager king or any villager (used with it in hand): the villagers round about hold a
 * festival for a minute (fireworks, dancing), the presenter is the hero of the village for an hour and the king's
 * favour rises by 50. Kept: after two minutes a warning, after five its keeper is the king's enemy.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RebelLord {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Rebels");
    public static final String LORD = "OrorRebelLord";
    public static final String CROWN = "OrorRebelCrown";
    static final String HELD = "OrorRebelCrownHeld";
    static final ResourceLocation CITY = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "illager_city");
    static final ResourceLocation FORTRESS = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "illager_fortress");
    private static final List<Object[]> PENDING = new ArrayList<>();
    private static final Map<Mob, ServerBossEvent> BARS = new WeakHashMap<>();
    private static final List<long[]> FESTIVALS = new ArrayList<>();
    private static ServerLevel festivalLevel;

    private RebelLord() {
    }

    // ------------------------------------------------------------------------------------------------- the lord

    /** Makes an evoker Azazel (or his likeness). */
    public static void makeLord(Mob m, boolean likeness) {
        m.getPersistentData().putBoolean(LORD, true);
        AttributeInstance hp = m.getAttribute(Attributes.MAX_HEALTH);
        if (hp != null) {
            hp.setBaseValue(likeness ? 240 : 400);
        }
        AttributeInstance armor = m.getAttribute(Attributes.ARMOR);
        if (armor != null) {
            armor.setBaseValue(14);
        }
        m.setHealth(m.getMaxHealth());
        m.setCustomName(Component.literal(likeness ? "アザゼルの化身" : "Lv.5 アザゼル［神に叛きし者］").withStyle(ChatFormatting.DARK_PURPLE));
        m.setCustomNameVisible(true);
        var ench = m.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        ItemStack blade = new ItemStack(Items.NETHERITE_SWORD);
        blade.set(DataComponents.CUSTOM_NAME, Component.literal("叛神剣（王殺し）").withStyle(ChatFormatting.DARK_PURPLE));
        blade.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 5);
        m.setItemSlot(EquipmentSlot.MAINHAND, blade);
        m.setDropChance(EquipmentSlot.MAINHAND, 0F);
        m.setPersistenceRequired();
    }

    /** Whether this one's blow is Azazel's (his own, his likeness's, his fangs' or his vexes'). */
    public static boolean slayer(Entity e) {
        if (e == null) {
            return false;
        }
        if (e.getPersistentData().getBoolean(LORD)) {
            return true;
        }
        if (e instanceof Vex v && v.getOwner() != null) {
            return v.getOwner().getPersistentData().getBoolean(LORD);
        }
        if (e instanceof OwnableEntity o && o.getOwner() != null) {
            return o.getOwner().getPersistentData().getBoolean(LORD);
        }
        return false;
    }

    static ItemStack crown() {
        ItemStack s = new ItemStack(Items.GOLDEN_HELMET);
        CompoundTag t = new CompoundTag();
        t.putBoolean(CROWN, true);
        s.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
        s.set(DataComponents.CUSTOM_NAME, Component.literal("叛神の冠").withStyle(ChatFormatting.DARK_PURPLE));
        s.set(DataComponents.LORE, new ItemLore(List.of(Component.literal("神に叛いた者アザゼルの冠。").withStyle(ChatFormatting.GRAY),
            Component.literal("村人王か村人に献上すれば、王国は祭りを開く。").withStyle(ChatFormatting.GRAY),
            Component.literal("隠し持てば、王国の敵となる。").withStyle(ChatFormatting.RED))));
        s.set(DataComponents.RARITY, Rarity.EPIC);
        s.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        return s;
    }

    public static boolean isCrown(ItemStack s) {
        CustomData cd = s.get(DataComponents.CUSTOM_DATA);
        return cd != null && cd.copyTag().getBoolean(CROWN);
    }

    /** Azazel falls: his crown. A friend of the rebels who strikes him down is one no longer. */
    @SubscribeEvent
    public static void drops(LivingDropsEvent e) {
        LivingEntity dead = e.getEntity();
        if (!dead.getPersistentData().getBoolean(LORD) || dead.getPersistentData().getBoolean(RebelPact.ALLY)) {
            return;
        }
        e.getDrops().add(new ItemEntity(dead.level(), dead.getX(), dead.getY() + 0.5, dead.getZ(), crown()));
        // (054) one time in four his body yields the rebels' hidden grand magic
        if (dead.getRandom().nextInt(4) == 0) {
            e.getDrops().add(new ItemEntity(dead.level(), dead.getX(), dead.getY() + 0.5, dead.getZ(), BrokenPhantasm.scroll()));
        }
        if (e.getSource().getEntity() instanceof ServerPlayer p) {
            if (RebelPact.friend(p)) {
                RebelPact.addFavour(p, -RebelPact.favour(p));
                p.sendSystemMessage(Component.literal("叛逆者たち：……主を、討ったか。裏切り者め。").withStyle(ChatFormatting.DARK_RED));
            }
            p.sendSystemMessage(Component.literal("アザゼル：……王に、尾を振るか……。").withStyle(ChatFormatting.DARK_PURPLE));
            LOG.info("REBEL-LORD-SLAIN {}", p.getGameProfile().getName());
        }
    }

    // ------------------------------------------------------------------------------------------------ the crown

    /** The crown presented (used on the king or a villager): true if it was. */
    public static boolean present(ServerPlayer p, LivingEntity to, ServerLevel sl) {
        ItemStack held = p.getMainHandItem();
        if (!isCrown(held)) {
            return false;
        }
        held.shrink(1);
        CompoundTag k = KingCourt.kept(p);
        k.remove(HELD);
        KingCourt.keep(p, k);
        KingCourt.favour(p, 50);
        KingCourt.grace(p, sl);
        p.addEffect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, 72000, 2));
        Component says = KingCourt.isKing(to) ? Component.literal("村人王：叛逆者アザゼルを討ったか！ 王国を挙げて祝おう！").withStyle(ChatFormatting.GOLD)
            : Component.literal("村人：叛逆者が討たれた！ お祭りだ！").withStyle(ChatFormatting.GOLD);
        for (ServerPlayer o : sl.players()) {
            if (o.distanceToSqr(to) < 128 * 128) {
                o.sendSystemMessage(says);
            }
        }
        festival(sl, to.blockPosition());
        LOG.info("REBEL-CROWN-PRESENTED {}", p.getGameProfile().getName());
        return true;
    }

    @SubscribeEvent
    public static void toVillager(PlayerInteractEvent.EntityInteract e) {
        if (e.getHand() == InteractionHand.MAIN_HAND && e.getTarget() instanceof Villager v && e.getEntity() instanceof ServerPlayer p
            && p.level() instanceof ServerLevel sl && isCrown(p.getMainHandItem()) && present(p, v, sl)) {
            e.setCanceled(true);
            e.setCancellationResult(InteractionResult.SUCCESS);
        }
    }

    /** The crown kept: a warning at two minutes, the king's enmity at five. */
    @SubscribeEvent
    public static void keeper(PlayerTickEvent.Post e) {
        if (e.getEntity() instanceof ServerPlayer p && p.tickCount % 20 == 0) {
            keep(p);
        }
    }

    /** A second of keeping the crown (or of not having it any more). */
    public static void keep(ServerPlayer p) {
        boolean has = false;
        for (ItemStack s : p.getInventory().items) {
            if (isCrown(s)) {
                has = true;
                break;
            }
        }
        CompoundTag k = KingCourt.kept(p);
        if (!has) {
            if (k.contains(HELD)) {
                k.remove(HELD);
                KingCourt.keep(p, k);
            }
            return;
        }
        if (KingCourt.enemy(p)) {
            return;
        }
        int held = k.getInt(HELD) + 20;
        k.putInt(HELD, held);
        KingCourt.keep(p, k);
        if (held == 2400) {
            p.sendSystemMessage(Component.literal("王国の使者：叛神の冠を持つ者よ。王へ献上せよ。さもなくば、汝も叛逆者と見なす。").withStyle(ChatFormatting.GOLD));
        } else if (held >= 6000) {
            p.sendSystemMessage(Component.literal("王国の使者：冠を隠し持つ叛逆者だ！ 討て！").withStyle(ChatFormatting.DARK_RED));
            KingCourt.declare(p, null);
        }
    }

    /** Sets how long the player has kept the crown (the CI's check). */
    public static void setHeld(Player p, int ticks) {
        CompoundTag k = KingCourt.kept(p);
        k.putInt(HELD, ticks);
        KingCourt.keep(p, k);
    }

    // --------------------------------------------------------------------------------------------- the festival

    static void festival(ServerLevel sl, BlockPos at) {
        festivalLevel = sl;
        FESTIVALS.add(new long[]{at.asLong(), sl.getGameTime() + 1200});
        sl.playSound(null, at, SoundEvents.VILLAGER_CELEBRATE, SoundSource.NEUTRAL, 3F, 1F);
    }

    public static int festivals() {
        return FESTIVALS.size();
    }

    @SubscribeEvent
    public static void serverTick(ServerTickEvent.Post e) {
        ServerLevel sl = festivalLevel;
        if (sl != null && !FESTIVALS.isEmpty()) {
            long now = sl.getGameTime();
            FESTIVALS.removeIf(f -> now > f[1]);
            if (now % 10 == 0) {
                for (long[] f : FESTIVALS) {
                    BlockPos at = BlockPos.of(f[0]);
                    List<Villager> people = sl.getEntitiesOfClass(Villager.class, new net.minecraft.world.phys.AABB(at).inflate(64));
                    for (Villager v : people) {
                        if (v.onGround() && sl.random.nextInt(3) == 0) {
                            v.setDeltaMovement(v.getDeltaMovement().add(0, 0.42, 0));
                        }
                        sl.sendParticles(ParticleTypes.HAPPY_VILLAGER, v.getX(), v.getY() + 2, v.getZ(), 2, 0.3, 0.3, 0.3, 0);
                        sl.sendParticles(ParticleTypes.NOTE, v.getX(), v.getY() + 2.3, v.getZ(), 1, 0.2, 0.1, 0.2, 1);
                    }
                    if (now % 40 == 0 && !people.isEmpty()) {
                        Villager v = people.get(sl.random.nextInt(people.size()));
                        ItemStack rocket = new ItemStack(Items.FIREWORK_ROCKET);
                        rocket.set(DataComponents.FIREWORKS, new Fireworks(1, List.of(new FireworkExplosion(FireworkExplosion.Shape.LARGE_BALL,
                            IntList.of(0xFFD700, 0xFF5050, 0x50A0FF), IntList.of(0xFFFFFF), true, true))));
                        sl.addFreshEntity(new FireworkRocketEntity(sl, v.getX(), v.getY() + 1, v.getZ(), rocket));
                    }
                }
            }
        }
        if (!PENDING.isEmpty()) {
            List<Object[]> todo = new ArrayList<>(PENDING);
            PENDING.clear();
            for (Object[] p : todo) {
                court((ServerLevel) p[0], (BlockPos) p[1], (Boolean) p[2]);
            }
        }
        if (!BARS.isEmpty()) {
            bars();
        }
    }

    // --------------------------------------------------------------------------------------- his city, his court

    /** The centre of an illager city (or fortress) loaded for the first time: Azazel (or his general) and his court. */
    @SubscribeEvent
    public static void loaded(ChunkEvent.Load e) {
        if (!(e.getLevel() instanceof ServerLevel sl) || !(e.getChunk() instanceof LevelChunk c)) {
            return;
        }
        var registry = sl.registryAccess().registryOrThrow(Registries.STRUCTURE);
        for (Map.Entry<Structure, StructureStart> en : c.getAllStarts().entrySet()) {
            ResourceLocation id = registry.getKey(en.getKey());
            if ((CITY.equals(id) || FORTRESS.equals(id)) && en.getValue().isValid()) {
                BlockPos centre = en.getValue().getBoundingBox().getCenter();
                Sites sites = Sites.of(sl);
                if (sites.done.add(centre.asLong())) {
                    sites.setDirty();
                    PENDING.add(new Object[]{sl, centre, CITY.equals(id)});
                }
            }
        }
    }

    /** Spawns Azazel and his court (a city) or his general and guards (a fortress) at the centre. */
    public static Mob court(ServerLevel sl, BlockPos centre, boolean city) {
        BlockPos at = sl.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, centre);
        Mob lord = (city ? EntityType.EVOKER : EntityType.VINDICATOR).create(sl);
        if (lord == null) {
            return null;
        }
        lord.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, 0F, 0F);
        lord.finalizeSpawn(sl, sl.getCurrentDifficultyAt(at), MobSpawnType.STRUCTURE, null);
        if (city) {
            makeLord(lord, false);
        } else {
            AttributeInstance hp = lord.getAttribute(Attributes.MAX_HEALTH);
            if (hp != null) {
                hp.setBaseValue(200);
            }
            lord.setHealth(lord.getMaxHealth());
            var ench = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
            ItemStack axe = new ItemStack(Items.NETHERITE_AXE);
            axe.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 5);
            lord.setItemSlot(EquipmentSlot.MAINHAND, axe);
            lord.setDropChance(EquipmentSlot.MAINHAND, 0.1F);
            lord.setCustomName(Component.literal("Lv.4 叛逆の将軍").withStyle(ChatFormatting.DARK_GREEN));
            lord.setCustomNameVisible(true);
            lord.setPersistenceRequired();
            lord.getPersistentData().putBoolean("OrorRebelGeneral", true);
        }
        sl.addFreshEntity(lord);
        for (int i = 0; i < (city ? 4 : 3); i++) {
            Mob g = (i % 2 == 0 ? EntityType.VINDICATOR : EntityType.PILLAGER).create(sl);
            if (g == null) {
                continue;
            }
            g.moveTo(at.getX() + 0.5 + (i - 1.5) * 2, at.getY(), at.getZ() + 2.5, 0F, 0F);
            g.finalizeSpawn(sl, sl.getCurrentDifficultyAt(at), MobSpawnType.STRUCTURE, null);
            g.setPersistenceRequired();
            sl.addFreshEntity(g);
        }
        LOG.info("REBEL-COURT {\"city\":{},\"at\":[{},{},{}]}", city, at.getX(), at.getY(), at.getZ());
        return lord;
    }

    /** Azazel's boss bar: shown to the players near him he is set against (not the rebels' friends). */
    static void bars() {
        for (Map.Entry<Mob, ServerBossEvent> en : List.copyOf(BARS.entrySet())) {
            Mob m = en.getKey();
            ServerBossEvent bar = en.getValue();
            if (!m.isAlive() || !(m.level() instanceof ServerLevel sl)) {
                bar.removeAllPlayers();
                BARS.remove(m);
                continue;
            }
            bar.setProgress(m.getHealth() / m.getMaxHealth());
            if (sl.getGameTime() % 20 != 0) {
                continue;
            }
            for (ServerPlayer p : sl.players()) {
                boolean show = p.distanceToSqr(m) < 64 * 64 && !RebelPact.friend(p) && !p.isSpectator() && (m.getTarget() == p || p.getLastHurtMob() == m);
                if (show) {
                    bar.addPlayer(p);
                } else {
                    bar.removePlayer(p);
                }
            }
        }
    }

    /** Keeps a boss bar for each lord alive and in a fight (each second). */
    @SubscribeEvent
    public static void lordTick(net.neoforged.neoforge.event.tick.EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide || m.tickCount % 20 != 0 || !m.getPersistentData().getBoolean(LORD)
            || m.getPersistentData().getBoolean(RebelPact.ALLY)) {
            return;
        }
        BARS.computeIfAbsent(m, x -> new ServerBossEvent(Component.literal("Lv.5 アザゼル［神に叛きし者］"), BossEvent.BossBarColor.PURPLE,
            BossEvent.BossBarOverlay.NOTCHED_10));
    }

    /** The cities and fortresses whose court has come (so that it comes once). */
    static final class Sites extends SavedData {
        final Set<Long> done = new HashSet<>();

        static Sites of(ServerLevel sl) {
            return sl.getDataStorage().computeIfAbsent(new SavedData.Factory<>(Sites::new, Sites::load, null), "oror_rebel_courts");
        }

        static Sites load(CompoundTag tag, HolderLookup.Provider lookup) {
            Sites s = new Sites();
            for (long l : tag.getLongArray("Done")) {
                s.done.add(l);
            }
            return s;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider lookup) {
            tag.put("Done", new LongArrayTag(new ArrayList<>(this.done)));
            return tag;
        }
    }

    /** Whether the player may be struck by the kingdom (the CI's check). */
    public static boolean hostile(Player p) {
        return RoyalThreats.hostilePlayer(p);
    }
}
