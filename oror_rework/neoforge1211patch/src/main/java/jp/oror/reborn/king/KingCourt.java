package jp.oror.reborn.king;

import java.util.List;
import jp.oror.reborn.royal.RoyalGuns;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.royal.RoyalThreats;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The villager king at peace and at war (the user: he is not hostile from the start; in peace he trades the
 * richest of wares and gives his protection, and his grace as one's standing with him grows; but once one turns on him,
 * one is killed; his boss bar shows only to his enemies).
 * <ul>
 * <li>Spoken to (used) by one who is not the kingdom's enemy: his blessing (加護) once a day (regeneration, resistance,
 * luck, the hero of the village, for twenty minutes) and his trades (enchanted golden apples, totems, elytra, a nether
 * star, netherite, mending, the kingdom's legendary guns...). Every trade raises his favour; his grace (恩寵) comes at
 * 10 (his token, worn round the neck: the hero of the village), at 30 (four more hearts, for good) and at 60 (the
 * king's sword).</li>
 * <li>One who strikes him (by hand, by arrow, by gun) is the king's enemy (王敵) for good: the kingdom's people take
 * them for an enemy wherever they are (RoyalThreats, RoyalThreatsMixin), the king hunts them within 128 blocks (his
 * home is no bound while he does), and the illagers, piglins and endermen take them for a friend (RebelPact).</li>
 * <li>His two boss bars (life and AT field) show only to the players who are his enemies now.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingCourt {
    private static final Logger LOG = LoggerFactory.getLogger("OROR King");
    public static final String ENEMY = "OrorKingEnemy";
    public static final String FAVOUR = "OrorKingFavour";
    public static final String GRACE = "OrorKingGrace";
    public static final String BLESSED_DAY = "OrorKingBlessedDay";
    static final ResourceLocation GRACE_HEALTH = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "king_grace_health");

    private KingCourt() {
    }

    static CompoundTag kept(Player p) {
        return p.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
    }

    static void keep(Player p, CompoundTag kept) {
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, kept);
    }

    public static boolean enemy(Player p) {
        return kept(p).getBoolean(ENEMY);
    }

    public static boolean isKing(Entity e) {
        return e instanceof RoyalMob m && m.role() == RoyalRole.KING;
    }

    /** Marks the player the king's enemy, for good. */
    public static void declare(ServerPlayer p, RoyalMob king) {
        CompoundTag k = kept(p);
        if (k.getBoolean(ENEMY)) {
            return;
        }
        k.putBoolean(ENEMY, true);
        keep(p, k);
        RoyalThreats.register(p);
        int phase = king == null ? 0 : king.lifePhase();
        String who = phase >= 3 ? KingForms.TRUE_NAME : phase == 2 ? KingForms.GARBLED_KING : "村人王";
        p.sendSystemMessage(Component.literal(who + "：……汝を、王敵と定める。逃げても無駄だ。").withStyle(ChatFormatting.DARK_RED));
        p.sendSystemMessage(Component.literal("（邪悪な村人、ピグリン、エンダーマンが、あなたを仲間と見なすようになった）").withStyle(ChatFormatting.GRAY));
        LOG.info("KING-ENEMY {}", p.getGameProfile().getName());
    }

    // ---------------------------------------------------------------------------------------------------- war

    /** One who strikes the king becomes his enemy. */
    @SubscribeEvent
    public static void struck(LivingIncomingDamageEvent e) {
        if (!isKing(e.getEntity()) || e.getEntity().level().isClientSide) {
            return;
        }
        Entity by = e.getSource().getEntity();
        if (by == null && e.getSource().getDirectEntity() instanceof Projectile pr) {
            by = pr.getOwner();
        }
        if (by instanceof ServerPlayer p && !p.isCreative() && !p.isSpectator()) {
            declare(p, (RoyalMob) e.getEntity());
        }
    }

    /** The king hunts his enemies: the nearest within 128 blocks, his home no bound while he does. */
    static void hunt(RoyalMob king, ServerLevel sl, int phase) {
        if (king.tickCount % 20 != 7) {
            return;
        }
        CompoundTag d = king.getPersistentData();
        LivingEntity t = king.getTarget();
        if (t == null || !t.isAlive()) {
            ServerPlayer near = null;
            double best = 128 * 128;
            for (ServerPlayer p : sl.players()) {
                double dd = p.distanceToSqr(king);
                if (dd < best && enemy(p) && !p.isCreative() && !p.isSpectator() && p.isAlive()) {
                    best = dd;
                    near = p;
                }
            }
            if (near != null) {
                if (!d.contains("OrorKingHome") && king.hasRestriction()) {
                    d.putLong("OrorKingHome", king.getRestrictCenter().asLong());
                    d.putInt("OrorKingHomeRadius", (int) king.getRestrictRadius());
                }
                king.clearRestriction();
                king.setTarget(near);
            } else if (d.contains("OrorKingHome")) {
                king.restrictTo(BlockPos.of(d.getLong("OrorKingHome")), Math.max(16, d.getInt("OrorKingHomeRadius")));
                d.remove("OrorKingHome");
            }
        } else if (t instanceof Player p && enemy(p) && king.distanceTo(p) > 24) {
            king.getNavigation().moveTo(p, 1.3);
        }
    }

    /** His boss bars: shown to his enemies near him, to no one else. */
    static void bossBars(RoyalMob king, ServerLevel sl) {
        ServerBossEvent[] bars = KingBars.of(king);
        if (bars == null) {
            return;
        }
        for (ServerPlayer p : sl.players()) {
            boolean show = p.distanceToSqr(king) < 96 * 96 && RoyalThreats.hostilePlayer(p) && !p.isSpectator();
            for (ServerBossEvent bar : bars) {
                if (show) {
                    bar.addPlayer(p);
                } else {
                    bar.removePlayer(p);
                }
            }
        }
    }

    // ---------------------------------------------------------------------------------------------------- peace

    @SubscribeEvent
    public static void spoken(PlayerInteractEvent.EntityInteract e) {
        if (e.getHand() != InteractionHand.MAIN_HAND || !isKing(e.getTarget()) || !(e.getEntity() instanceof ServerPlayer p)
            || !(p.level() instanceof ServerLevel sl)) {
            return;
        }
        RoyalMob king = (RoyalMob) e.getTarget();
        e.setCanceled(true);
        e.setCancellationResult(InteractionResult.SUCCESS);
        if (RebelLord.present(p, king, sl)) {
            return;
        }
        if (RoyalThreats.hostilePlayer(p) || king.getTarget() == p) {
            p.sendSystemMessage(Component.literal("村人王：王に刃を向けた者と、語る言葉はない。").withStyle(ChatFormatting.DARK_RED));
            return;
        }
        bless(p, sl);
        grace(p, sl);
        OrorMerchant.open(p, Component.literal("村人王の宝物庫"), "king", offers(p, sl), KingCourt::traded);
    }

    /** His blessing, once a day: twenty minutes of his protection. */
    static void bless(ServerPlayer p, ServerLevel sl) {
        long day = sl.getDayTime() / 24000L;
        CompoundTag k = kept(p);
        if (k.contains(BLESSED_DAY) && k.getLong(BLESSED_DAY) >= day) {
            return;
        }
        k.putLong(BLESSED_DAY, day);
        keep(p, k);
        int t = 20 * 60 * 20;
        p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, t, 0));
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, t, 0));
        p.addEffect(new MobEffectInstance(MobEffects.LUCK, t, 1));
        p.addEffect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, t, 1));
        if (k.getInt(GRACE) >= 2) {
            p.addEffect(new MobEffectInstance(MobEffects.HEALTH_BOOST, t, 1));
        }
        sl.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, p.getX(), p.getY() + 1, p.getZ(), 40, 0.5, 1, 0.5, 0.3);
        sl.playSound(null, p.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1F, 1.2F);
        p.sendSystemMessage(Component.literal("村人王：旅の者よ、我が加護を授けよう。").withStyle(ChatFormatting.GOLD));
        LOG.info("KING-BLESSING {}", p.getGameProfile().getName());
    }

    /** His grace, as his favour grows: his token at 10, four hearts at 30, his sword at 60. */
    static void grace(ServerPlayer p, ServerLevel sl) {
        CompoundTag k = kept(p);
        int favour = k.getInt(FAVOUR);
        int had = k.getInt(GRACE);
        int now = favour >= 60 ? 3 : favour >= 30 ? 2 : favour >= 10 ? 1 : 0;
        while (had < now) {
            had++;
            switch (had) {
                case 1 -> {
                    ItemStack token = RoyalRegistry.TOKEN == null ? new ItemStack(Items.TOTEM_OF_UNDYING) : new ItemStack(RoyalRegistry.TOKEN);
                    give(p, token);
                    p.sendSystemMessage(Component.literal("村人王：汝の誠を認め、我が印を授ける。首に掛けよ。").withStyle(ChatFormatting.GOLD));
                }
                case 2 -> {
                    AttributeInstance hp = p.getAttribute(Attributes.MAX_HEALTH);
                    if (hp != null && hp.getModifier(GRACE_HEALTH) == null) {
                        hp.addPermanentModifier(new AttributeModifier(GRACE_HEALTH, 8.0, AttributeModifier.Operation.ADD_VALUE));
                    }
                    p.sendSystemMessage(Component.literal("村人王：王の恩寵を。汝の命は、我が民の命と等しく重い。（最大体力＋4ハート）").withStyle(ChatFormatting.GOLD));
                }
                default -> {
                    give(p, kingsSword(sl));
                    p.sendSystemMessage(Component.literal("村人王：我が剣を預ける。王国の友よ。").withStyle(ChatFormatting.GOLD));
                }
            }
            sl.sendParticles(ParticleTypes.HAPPY_VILLAGER, p.getX(), p.getY() + 1, p.getZ(), 30, 0.6, 1, 0.6, 0.1);
            LOG.info("KING-GRACE {\"player\":\"{}\",\"grace\":{},\"favour\":{}}", p.getGameProfile().getName(), had, favour);
        }
        k.putInt(GRACE, had);
        keep(p, k);
    }

    static void traded(Player p, MerchantOffer offer) {
        CompoundTag k = kept(p);
        k.putInt(FAVOUR, k.getInt(FAVOUR) + 1);
        keep(p, k);
        if (p instanceof ServerPlayer sp && sp.level() instanceof ServerLevel sl) {
            grace(sp, sl);
        }
    }

    public static void favour(Player p, int delta) {
        CompoundTag k = kept(p);
        k.putInt(FAVOUR, Math.max(0, k.getInt(FAVOUR) + delta));
        keep(p, k);
    }

    static void give(Player p, ItemStack s) {
        if (!p.getInventory().add(s)) {
            p.drop(s, false);
        }
    }

    static ItemStack kingsSword(ServerLevel sl) {
        var ench = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        ItemStack s = new ItemStack(Items.NETHERITE_SWORD);
        s.set(DataComponents.CUSTOM_NAME, Component.literal("王剣ロイヤル・オース").withStyle(ChatFormatting.GOLD));
        s.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 6);
        s.enchant(ench.getHolderOrThrow(Enchantments.LOOTING), 3);
        s.enchant(ench.getHolderOrThrow(Enchantments.UNBREAKING), 3);
        s.enchant(ench.getHolderOrThrow(Enchantments.MENDING), 1);
        s.enchant(ench.getHolderOrThrow(Enchantments.SWEEPING_EDGE), 3);
        s.set(DataComponents.RARITY, Rarity.EPIC);
        return s;
    }

    // --------------------------------------------------------------------------------------------- his wares

    static MerchantOffer offer(ItemStack sells, Item a, int na, Item b, int nb, int uses) {
        return new MerchantOffer(new ItemCost(a, na), b == null ? java.util.Optional.empty() : java.util.Optional.of(new ItemCost(b, nb)), sells, uses, 0,
            0F);
    }

    static ItemStack book(ServerLevel sl, ResourceKey<Enchantment> key, int level) {
        var ench = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        Holder<Enchantment> h = ench.getHolderOrThrow(key);
        return net.minecraft.world.item.EnchantedBookItem.createForEnchantment(new net.minecraft.world.item.enchantment.EnchantmentInstance(h, level));
    }

    static MerchantOffers offers(Player p, ServerLevel sl) {
        MerchantOffers o = new MerchantOffers();
        o.add(offer(new ItemStack(Items.ENCHANTED_GOLDEN_APPLE, 2), Items.EMERALD_BLOCK, 8, Items.GOLD_BLOCK, 8, 4));
        o.add(offer(new ItemStack(Items.TOTEM_OF_UNDYING), Items.EMERALD_BLOCK, 6, null, 0, 4));
        o.add(offer(new ItemStack(Items.ELYTRA), Items.EMERALD_BLOCK, 24, Items.DIAMOND_BLOCK, 4, 1));
        o.add(offer(new ItemStack(Items.NETHER_STAR), Items.EMERALD_BLOCK, 32, Items.DIAMOND_BLOCK, 8, 1));
        o.add(offer(new ItemStack(Items.NETHERITE_INGOT, 2), Items.EMERALD_BLOCK, 10, Items.DIAMOND, 8, 6));
        o.add(offer(new ItemStack(Items.DIAMOND, 12), Items.EMERALD_BLOCK, 4, null, 0, 8));
        o.add(offer(book(sl, Enchantments.MENDING, 1), Items.EMERALD_BLOCK, 4, Items.BOOK, 1, 4));
        o.add(offer(book(sl, Enchantments.SHARPNESS, 5), Items.EMERALD_BLOCK, 5, Items.BOOK, 1, 4));
        o.add(offer(book(sl, Enchantments.PROTECTION, 4), Items.EMERALD_BLOCK, 5, Items.BOOK, 1, 4));
        o.add(offer(new ItemStack(Items.EXPERIENCE_BOTTLE, 32), Items.EMERALD_BLOCK, 3, null, 0, 8));
        o.add(offer(new ItemStack(Items.SHULKER_BOX), Items.EMERALD_BLOCK, 6, null, 0, 4));
        o.add(offer(new ItemStack(Items.BEACON), Items.EMERALD_BLOCK, 40, Items.NETHERITE_INGOT, 2, 1));
        List<Item> legendary = RoyalGuns.legendary();
        for (int i = 0; i < Math.min(3, legendary.size()); i++) {
            o.add(offer(new ItemStack(legendary.get((int) ((sl.getDayTime() / 24000L + i * 7) % legendary.size()))), Items.EMERALD_BLOCK, 20, Items.NETHERITE_INGOT,
                1, 1));
        }
        if (kept(p).getInt(GRACE) >= 1) {
            o.add(offer(new ItemStack(Items.TRIDENT), Items.EMERALD_BLOCK, 8, null, 0, 2));
            o.add(offer(new ItemStack(Items.HEART_OF_THE_SEA), Items.EMERALD_BLOCK, 12, null, 0, 2));
        }
        return o;
    }
}
