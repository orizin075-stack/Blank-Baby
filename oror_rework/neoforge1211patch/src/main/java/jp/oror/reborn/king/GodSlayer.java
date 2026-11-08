package jp.oror.reborn.king;

import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.joml.Vector3f;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) 神殺し, the god-slayer: given for good to everyone who fought Baal Zebul to his last death (and to the one
 * who dealt it), kept through death, beyond milk and every cure (the user: it cannot be undone and lasts through
 * death; with it a great many strengths, so that one can fight OROR's own beings as an equal: an AT field, a ceiling
 * on the damage one takes, the gods' undying denied, and the gods weakened by one's blows).
 * <ul>
 * <li>Its strengths: 10 hearts more, half again the attack, 10 armour and 6 toughness, a tenth more speed, half the
 * knockback turned aside, luck.</li>
 * <li>The AT field: 120 points of light that take blows before the body does; a blow of 80 or more breaks it at once
 * (the rest goes through); it comes back, 6 a second, three seconds after the last blow.</li>
 * <li>The ceiling: no single blow takes more than a quarter of one's health (the void and /kill excepted).</li>
 * <li>The gods' undying denied: an OROR being with an undying lore (LorePowers.IMMORTAL) slain by a god-slayer stays
 * dead; their lore's turning aside of a god-slayer's blow is undone (SupremeEntityDeicideMixin); the villager king's
 * field breaks under a god-slayer's blow (RebelPact.onKing).</li>
 * <li>The gods weakened: a god-slayer's blow on a god (an OROR being, the villager king, any boss) strikes half again as
 * hard and weakens it, slows it, withers it and marks it, and for ten seconds strips two fifths of its armour and a
 * quarter of its strength.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GodSlayer {
    private static final Logger LOG = LoggerFactory.getLogger("OROR King");
    public static final String KEY = "OrorGodSlayer";
    static final String FOES = "OrorKingFoes";
    static final ResourceLocation ID = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "god_slayer");
    static final ResourceLocation CURSE = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "deicide_curse");
    static final String CURSE_UNTIL = "OrorDeicideUntil";
    static MobEffect effect;

    private GodSlayer() {
    }

    /** The status's mark among the effects: a beneficial effect no cure takes (it is put back each second). */
    static final class Mark extends MobEffect {
        Mark() {
            super(MobEffectCategory.BENEFICIAL, 0xD8A838);
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    static final class Registration {
        private Registration() {
        }

        @SubscribeEvent
        public static void register(RegisterEvent e) {
            e.register(Registries.MOB_EFFECT, h -> {
                effect = new Mark();
                h.register(ID, effect);
            });
        }
    }

    public static boolean has(Entity e) {
        if (e instanceof Projectile p) {
            e = p.getOwner();
        }
        return e instanceof Player p && KingCourt.kept(p).getBoolean(KEY);
    }

    /** Those the god-slayer's blows weaken: OROR's beings, the villager king, any boss. */
    public static boolean god(Entity e) {
        return e instanceof SupremeEntity || KingCourt.isKing(e) || (e instanceof LivingEntity && e.getType().is(Tags.EntityTypes.BOSSES));
    }

    // ------------------------------------------------------------------------------------------ given

    /** Everyone who struck Baal Zebul is remembered on him. */
    @SubscribeEvent(priority = EventPriority.LOWEST, receiveCanceled = true)
    public static void fought(LivingIncomingDamageEvent e) {
        if (!KingCourt.isKing(e.getEntity()) || ((RoyalMob) e.getEntity()).lifePhase() < 3) {
            return;
        }
        Entity by = e.getSource().getEntity();
        if (by instanceof ServerPlayer p) {
            CompoundTag d = e.getEntity().getPersistentData();
            ListTag l = d.getList(FOES, Tag.TAG_STRING);
            String id = p.getUUID().toString();
            for (Tag t : l) {
                if (t.getAsString().equals(id)) {
                    return;
                }
            }
            l.add(StringTag.valueOf(id));
            d.put(FOES, l);
        }
    }

    /** Baal Zebul's last death: every one who fought him becomes a god-slayer. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void slain(LivingDeathEvent e) {
        if (!KingCourt.isKing(e.getEntity()) || !(e.getEntity().level() instanceof ServerLevel sl)) {
            return;
        }
        RoyalMob king = (RoyalMob) e.getEntity();
        if (king.lifePhase() < 3) {
            return;
        }
        if (e.getSource().getEntity() instanceof ServerPlayer killer) {
            give(killer, sl);
        }
        for (Tag t : king.getPersistentData().getList(FOES, Tag.TAG_STRING)) {
            try {
                ServerPlayer p = sl.getServer().getPlayerList().getPlayer(UUID.fromString(t.getAsString()));
                if (p != null) {
                    give(p, sl);
                }
            } catch (IllegalArgumentException ex) {
                // not a uuid
            }
        }
    }

    public static void give(ServerPlayer p, ServerLevel sl) {
        CompoundTag k = KingCourt.kept(p);
        if (k.getBoolean(KEY)) {
            return;
        }
        k.putBoolean(KEY, true);
        KingCourt.keep(p, k);
        keep(p);
        p.connection.send(new ClientboundSetTitlesAnimationPacket(10, 80, 30));
        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("汝はもはや、神の手の内にはない。").withStyle(ChatFormatting.GOLD)));
        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal("神殺し").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD)));
        p.sendSystemMessage(Component.literal("【神殺し】を得た。この刻印は消えない（死んでも残る）。").withStyle(ChatFormatting.GOLD));
        p.sendSystemMessage(Component.literal("・ATフィールド　・受けるダメージの上限　・神の不死性の否定　・神への弱体化").withStyle(ChatFormatting.YELLOW));
        sl.playSound(null, p.blockPosition(), SoundEvents.WITHER_DEATH, SoundSource.PLAYERS, 1.0F, 0.6F);
        sl.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, p.getX(), p.getY() + 1, p.getZ(), 200, 0.8, 1.2, 0.8, 0.6);
        LOG.info("GOD-SLAYER {}", p.getGameProfile().getName());
    }

    // ------------------------------------------------------------------------------------------ kept

    private static void stat(LivingEntity e, Holder<Attribute> a, AttributeModifier.Operation op, double amount, String name) {
        AttributeInstance in = e.getAttribute(a);
        if (in == null) {
            return;
        }
        ResourceLocation id = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "god_slayer_" + name);
        AttributeModifier m = in.getModifier(id);
        if (m != null && m.amount() == amount) {
            return;
        }
        in.removeModifier(id);
        in.addPermanentModifier(new AttributeModifier(id, amount, op));
    }

    /** The mark and the strengths, put back if anything took them (death, milk, a command). */
    static void keep(ServerPlayer p) {
        stat(p, Attributes.MAX_HEALTH, AttributeModifier.Operation.ADD_VALUE, 20, "health");
        stat(p, Attributes.ATTACK_DAMAGE, AttributeModifier.Operation.ADD_MULTIPLIED_BASE, 0.5, "attack");
        stat(p, Attributes.ARMOR, AttributeModifier.Operation.ADD_VALUE, 10, "armor");
        stat(p, Attributes.ARMOR_TOUGHNESS, AttributeModifier.Operation.ADD_VALUE, 6, "toughness");
        stat(p, Attributes.MOVEMENT_SPEED, AttributeModifier.Operation.ADD_MULTIPLIED_BASE, 0.1, "speed");
        stat(p, Attributes.KNOCKBACK_RESISTANCE, AttributeModifier.Operation.ADD_VALUE, 0.5, "knockback");
        stat(p, Attributes.LUCK, AttributeModifier.Operation.ADD_VALUE, 2, "luck");
        if (effect != null) {
            Holder<MobEffect> h = BuiltInRegistries.MOB_EFFECT.wrapAsHolder(effect);
            if (!p.hasEffect(h)) {
                p.addEffect(new MobEffectInstance(h, MobEffectInstance.INFINITE_DURATION, 0, true, false, true));
            }
        }
    }

    @SubscribeEvent
    public static void tick(PlayerTickEvent.Post e) {
        if (e.getEntity() instanceof ServerPlayer p && p.tickCount % 20 == 0 && KingCourt.kept(p).getBoolean(KEY)) {
            keep(p);
            double[] f = FIELD.computeIfAbsent(p, x -> new double[]{CAPACITY, 0});
            if (p.level().getGameTime() - f[1] > 60 && f[0] < CAPACITY) {
                f[0] = Math.min(CAPACITY, f[0] + 6);
            }
        }
    }

    // ------------------------------------------------------------------------------------------ the field and the ceiling

    static final double CAPACITY = 120, BREAK = 80;
    private static final Map<Player, double[]> FIELD = new WeakHashMap<>();
    private static final DustParticleOptions FIELD_LIGHT = new DustParticleOptions(new Vector3f(1.0F, 0.55F, 0.1F), 1.4F);

    /** Blows on a god-slayer meet the AT field first. */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void field(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p) || !KingCourt.kept(p).getBoolean(KEY) || e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return;
        }
        double[] f = FIELD.computeIfAbsent(p, x -> new double[]{CAPACITY, 0});
        f[1] = p.level().getGameTime();
        float amount = e.getAmount();
        if (f[0] <= 0 || amount <= 0) {
            return;
        }
        ServerLevel sl = (ServerLevel) p.level();
        Entity by = e.getSource().getEntity();
        double a = by != null ? Math.atan2(by.getZ() - p.getZ(), by.getX() - p.getX()) : 0;
        for (int i = 0; i < 8; i++) {
            double t = a + (i - 3.5) * 0.18;
            for (int k = 0; k < 3; k++) {
                sl.sendParticles(FIELD_LIGHT, p.getX() + Math.cos(t) * 1.2, p.getY() + 0.4 + k * 0.6, p.getZ() + Math.sin(t) * 1.2, 1, 0, 0, 0, 0);
            }
        }
        if (amount >= BREAK) {
            float rest = (float) Math.max(0, amount - f[0]);
            f[0] = 0;
            e.setAmount(rest);
            sl.playSound(null, p.blockPosition(), SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 1.2F, 0.6F);
            p.displayClientMessage(Component.literal("ATフィールド崩壊").withStyle(ChatFormatting.RED), true);
            if (rest <= 0) {
                e.setCanceled(true);
            }
            return;
        }
        double took = Math.min(f[0], amount);
        f[0] -= took;
        if (took >= amount) {
            e.setCanceled(true);
        } else {
            e.setAmount((float) (amount - took));
        }
        sl.playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.PLAYERS, 0.8F, 1.6F);
    }

    /** No single blow takes more than a quarter of a god-slayer's health. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void ceiling(LivingDamageEvent.Pre e) {
        if (e.getEntity() instanceof ServerPlayer p && KingCourt.kept(p).getBoolean(KEY) && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            e.setNewDamage(Math.min(e.getNewDamage(), p.getMaxHealth() * 0.25F));
        }
    }

    /** The field made whole again (the CI's check starts from a whole field). */
    static void fieldWhole(Player p) {
        FIELD.remove(p);
    }

    /** The field's state (the CI's check). */
    public static double fieldOf(Player p) {
        double[] f = FIELD.get(p);
        return f == null ? CAPACITY : f[0];
    }

    // ------------------------------------------------------------------------------------------ the gods weakened

    @SubscribeEvent(priority = EventPriority.HIGHEST, receiveCanceled = true)
    public static void deicide(LivingIncomingDamageEvent e) {
        LivingEntity v = e.getEntity();
        if (!god(v) || !has(e.getSource().getEntity()) || !(v.level() instanceof ServerLevel sl)) {
            return;
        }
        e.setAmount(e.getAmount() * 1.5F);
        v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
        v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 100, 1));
        v.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 0));
        v.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0));
        curse(v, true);
        v.getPersistentData().putLong(CURSE_UNTIL, sl.getGameTime() + 200);
        sl.sendParticles(ParticleTypes.SOUL, v.getX(), v.getY() + v.getBbHeight() * 0.6, v.getZ(), 6, 0.4, 0.5, 0.4, 0.02);
    }

    private static void curse(LivingEntity v, boolean on) {
        for (Holder<Attribute> a : java.util.List.of(Attributes.ARMOR, Attributes.ATTACK_DAMAGE)) {
            AttributeInstance in = v.getAttribute(a);
            if (in == null) {
                continue;
            }
            in.removeModifier(CURSE);
            if (on) {
                in.addTransientModifier(new AttributeModifier(CURSE, a == Attributes.ARMOR ? -0.4 : -0.25, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
            }
        }
    }

    @SubscribeEvent
    public static void lift(EntityTickEvent.Post e) {
        if (e.getEntity() instanceof LivingEntity v && !v.level().isClientSide && v.tickCount % 20 == 0) {
            CompoundTag d = v.getPersistentData();
            if (d.contains(CURSE_UNTIL) && v.level().getGameTime() > d.getLong(CURSE_UNTIL)) {
                d.remove(CURSE_UNTIL);
                curse(v, false);
            }
        }
    }
}
