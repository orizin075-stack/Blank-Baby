package jp.oror.reborn.combat;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.ItemAbilities;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (052) OROR's guard and parry, for every mob. The royals have always guarded so (RoyalMob.defend): when an enemy comes
 * within five blocks the guard goes up for half a second, every so often; a blow from the front in its first three
 * ticks is parried (the blow undone, a twentieth of its weight taken from the guard's stamina), later in the window it
 * is blocked (three tenths), and a guard without the stamina for a blow breaks, the mob staggering for a second. Mobs
 * of Epic Fight's Combat Evolution and Indestructible keep their own guard; every other mob (the vanilla ones, other
 * mods', OROR's characters) now guards by the royals' rules, scaled to what it is:
 * <ul>
 * <li>a boss (OROR's characters, the bosses' tag: not health, which the pack's mob levels raise) raises its guard every 1.8 seconds,
 * with a deeper stamina, and turns arrows aside as well;</li>
 * <li>an armed mob (a weapon or a shield in hand) every 2.5 seconds; it parries arrows with a blade, and blocks them
 * with a shield;</li>
 * <li>a bare-handed mob every 3.5 seconds, a shorter window, and only parries; its block halves a blow.</li>
 * </ul>
 * A mob struck while its guard is down raises it again in half the time, reading the rhythm of the blows. A parried attacker is
 * thrown back and staggered (Epic Fight's long stun where it has one), which is also what a player's own parry (Epic
 * Fight's) now does to any mob, not only to Indestructible's (NightfallNativeParryFeedbackMixin). The guard is seen:
 * an Epic Fight humanoid plays its guard and parry animations, OROR's characters and the royals their own poses
 * (TechniqueShow), every mob strikes sparks and rings.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MobGuard {
    private MobGuard() {
    }

    enum Tier {
        BOSS(36, 8, 160F), ARMED(50, 10, 80F), BARE(70, 6, 50F);

        final int cycle, window;
        final float stamina;

        Tier(int cycle, int window, float stamina) {
            this.cycle = cycle;
            this.window = window;
            this.stamina = stamina;
        }
    }

    /** A mob's guard: the window its guard is up in, its age, the wait before the next, its stamina and stagger. */
    static final class Guard {
        int remaining, age, delay = 20, stagger;
        float stamina = -1F;
    }

    private static final Map<LivingEntity, Guard> GUARDS = new WeakHashMap<>();
    /** Mob types whose Epic Fight patch guards on its own (Combat Evolution, Indestructible). */
    private static final Map<EntityType<?>, Boolean> NATIVE = new HashMap<>();

    /** Whether a mob guards by these rules (players, the royals, and the mobs of the guarding mods do not). */
    public static boolean guards(LivingEntity e) {
        if (!(e instanceof Mob m) || m instanceof RoyalMob || !m.isAlive() || m.isNoAi()) {
            return false;
        }
        Boolean known = NATIVE.get(m.getType());
        if (known == null) {
            String patch = ModList.get().isLoaded("epicfight") ? Ef.patchClass(m) : "";
            if (patch == null) {
                return true;
            }
            known = patch.contains("combat_evolution") || patch.contains("indestructible");
            NATIVE.put(m.getType(), known);
        }
        return !known;
    }

    static Tier tier(Mob m) {
        if (m instanceof SupremeEntity || m.getType().is(Tags.EntityTypes.BOSSES)) {
            return Tier.BOSS;
        }
        ItemStack main = m.getMainHandItem();
        if (shield(m) || !main.isEmpty() && (main.canPerformAction(ItemAbilities.SWORD_SWEEP) || main.canPerformAction(ItemAbilities.AXE_DIG)
            || armed(m, main))) {
            return Tier.ARMED;
        }
        return Tier.BARE;
    }

    private static boolean armed(Mob m, ItemStack main) {
        double[] dmg = {0};
        main.forEachModifier(EquipmentSlot.MAINHAND, (attribute, modifier) -> {
            if (attribute.value() == Attributes.ATTACK_DAMAGE.value()) {
                dmg[0] += modifier.amount();
            }
        });
        return dmg[0] >= 2;
    }

    static boolean shield(LivingEntity m) {
        return m.getOffhandItem().canPerformAction(ItemAbilities.SHIELD_BLOCK) || m.getMainHandItem().canPerformAction(ItemAbilities.SHIELD_BLOCK);
    }

    private static Guard guard(Mob m) {
        Guard g = GUARDS.get(m);
        if (g == null) {
            g = new Guard();
            GUARDS.put(m, g);
        }
        if (g.stamina < 0) {
            g.stamina = tier(m).stamina;
        }
        return g;
    }

    // ------------------------------------------------------------------------------------------------ raising the guard

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide) {
            return;
        }
        Guard g = GUARDS.get(m);
        LivingEntity t = m.getTarget();
        if (g == null && (t == null || !t.isAlive())) {
            return;
        }
        if (!guards(m)) {
            return;
        }
        g = guard(m);
        Tier tier = tier(m);
        if (g.stagger > 0) {
            g.stagger--;
            g.remaining = 0;
            m.getNavigation().stop();
            return;
        }
        if (g.remaining > 0) {
            g.remaining--;
            g.age++;
            g.stamina = Math.max(0F, g.stamina - 0.08F);
            return;
        }
        g.stamina = Math.min(tier.stamina, g.stamina + 0.4F);
        if (g.delay > 0) {
            g.delay--;
        }
        if (g.delay == 0 && t != null && t.isAlive() && m.distanceTo(t) < 5F && m.getSensing().hasLineOfSight(t)) {
            g.remaining = tier.window;
            g.age = 0;
            g.delay = tier.cycle;
        }
    }

    // ---------------------------------------------------------------------------------------------- meeting the blow

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void hurt(LivingIncomingDamageEvent e) {
        LivingEntity self = e.getEntity();
        if (self.level().isClientSide || !(self instanceof Mob m) || !(self.level() instanceof ServerLevel sl)) {
            return;
        }
        DamageSource src = e.getSource();
        if (!(src.getEntity() instanceof LivingEntity attacker) || attacker == self || unblockable(src)) {
            return;
        }
        boolean projectile = src.getDirectEntity() instanceof Projectile;
        boolean melee = !projectile && src.getDirectEntity() == attacker;
        if (!melee && !projectile || !guards(m)) {
            return;
        }
        Guard g = guard(m);
        if (g.remaining <= 0 || g.stagger > 0) {
            // struck with the guard down: it goes up again sooner, for a later blow of the combo
            if (melee && g.stagger <= 0) {
                g.delay = Math.min(g.delay, tier(m).cycle / 2);
            }
            return;
        }
        Vec3 from = src.getSourcePosition();
        if (from == null) {
            return;
        }
        Vec3 to = from.subtract(m.position()).multiply(1, 0, 1);
        Vec3 facing = m.getLookAngle().multiply(1, 0, 1);
        if (to.lengthSqr() < 1.0E-6 || facing.lengthSqr() < 1.0E-6 || to.normalize().dot(facing.normalize()) < 0.2) {
            return;
        }
        Tier tier = tier(m);
        boolean perfect = g.age <= 2;
        if (projectile && !(tier == Tier.BOSS || shield(m) || perfect && tier == Tier.ARMED)) {
            return;
        }
        float amount = e.getAmount();
        float cost = Math.max(1F, amount * (perfect ? 0.05F : 0.3F));
        if (g.stamina < cost) {
            // the guard breaks under the blow: the blow lands, and the mob staggers
            g.stamina = 0F;
            g.remaining = 0;
            g.stagger = 20;
            count(m, "OrorGuardBreaks");
            sl.playSound(null, m.blockPosition(), SoundEvents.SHIELD_BREAK, SoundSource.HOSTILE, 0.8F, 0.9F);
            sl.sendParticles(ParticleTypes.CRIT, m.getX(), m.getEyeY() - 0.3, m.getZ(), 12, 0.35, 0.3, 0.35, 0.15);
            show(m, "break", 22, attacker);
            return;
        }
        g.stamina -= cost;
        Vec3 contact = m.getEyePosition().lerp(from.add(0, attacker.getBbHeight() * 0.6, 0), 0.35);
        if (perfect) {
            e.setCanceled(true);
            count(m, "OrorParries");
            sl.playSound(null, m.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.8F);
            sl.sendParticles(ParticleTypes.FLASH, contact.x, contact.y, contact.z, 1, 0, 0, 0, 0);
            sl.sendParticles(ParticleTypes.CRIT, contact.x, contact.y, contact.z, 10, 0.2, 0.2, 0.2, 0.25);
            show(m, "parry", 14, attacker);
            if (melee) {
                parried(attacker, m.position());
            }
        } else {
            if (tier == Tier.BARE && !shield(m)) {
                e.setAmount(amount * 0.5F);
            } else {
                e.setCanceled(true);
            }
            count(m, "OrorBlocks");
            sl.playSound(null, m.blockPosition(), SoundEvents.SHIELD_BLOCK, SoundSource.HOSTILE, 0.5F, 1.0F);
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, contact.x, contact.y, contact.z, 6, 0.25, 0.2, 0.25, 0.02);
            show(m, "block", 12, attacker);
        }
    }

    /**
     * The royals guard by their own hand (RoyalMob.defend, at the highest priority): what it parried or blocked is
     * seen here afterwards, shown on their rig, and a parried attacker is thrown back as by any other guard.
     */
    @SubscribeEvent(priority = EventPriority.LOWEST, receiveCanceled = true)
    public static void royal(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof RoyalMob r) || r.level().isClientSide) {
            return;
        }
        CompoundTag d = r.getPersistentData();
        int parries = d.getInt("RoyalParries"), blocks = d.getInt("RoyalBlocks");
        LivingEntity attacker = e.getSource().getEntity() instanceof LivingEntity l ? l : null;
        if (parries > d.getInt("OrorShownParries")) {
            d.putInt("OrorShownParries", parries);
            TechniqueShow.send(r, "parry", 0, 1, 14, attacker == null ? -1 : attacker.getId());
            if (attacker != null && attacker != r && e.getSource().getDirectEntity() == attacker) {
                parried(attacker, r.position());
            }
        } else if (blocks > d.getInt("OrorShownBlocks")) {
            d.putInt("OrorShownBlocks", blocks);
            TechniqueShow.send(r, "block", 0, 1, 12, attacker == null ? -1 : attacker.getId());
        }
    }

    private static boolean unblockable(DamageSource src) {
        return src.is(DamageTypeTags.BYPASSES_INVULNERABILITY) || src.is(DamageTypeTags.IS_EXPLOSION) || src.is(DamageTypeTags.IS_FIRE)
            || src.is(DamageTypes.MAGIC) || src.is(DamageTypes.INDIRECT_MAGIC) || src.is(DamageTypes.THORNS) || src.is(DamageTypes.SONIC_BOOM)
            || src.typeHolder().unwrapKey().map(k -> k.location().getNamespace().equals("irons_spellbooks")).orElse(false);
    }

    private static void count(LivingEntity m, String key) {
        CompoundTag d = m.getPersistentData();
        d.putInt(key, d.getInt(key) + 1);
    }

    /** The guard's moment, seen: Epic Fight's animation on its humanoids, the pose on OROR's own rigs. */
    private static void show(LivingEntity m, String kind, int length, LivingEntity other) {
        if (ModList.get().isLoaded("epicfight")) {
            Ef.play(m, kind);
        }
        TechniqueShow.send(m, kind, 0, 1, length, other == null ? -1 : other.getId());
    }

    /**
     * An attacker parried, by a mob's guard or a player's: thrown back from where it was parried and staggered for
     * most of a second (Epic Fight's long stun on a mob it has a patch for; a mob's own guard down and its legs slowed
     * otherwise; a player only pushed back and slowed a moment).
     */
    public static void parried(LivingEntity attacker, Vec3 from) {
        if (attacker.level().isClientSide || !attacker.isAlive()) {
            return;
        }
        CompoundTag d = attacker.getPersistentData();
        long now = attacker.level().getGameTime();
        if (now - d.getLong("OrorParriedAt") < 4) {
            return;
        }
        d.putLong("OrorParriedAt", now);
        double dx = from.x - attacker.getX(), dz = from.z - attacker.getZ();
        if (dx * dx + dz * dz < 1.0E-4) {
            Vec3 look = attacker.getLookAngle();
            dx = look.x;
            dz = look.z;
        }
        attacker.knockback(attacker instanceof Player ? 0.45 : 0.7, dx, dz);
        attacker.hurtMarked = true;
        count(attacker, "OrorParried");
        if (attacker instanceof Player p) {
            p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 10, 1, false, false, true));
            return;
        }
        if (attacker instanceof Mob mob) {
            mob.getNavigation().stop();
            if (guards(mob)) {
                Guard g = guard(mob);
                g.stagger = Math.max(g.stagger, 16);
            }
        }
        boolean stunned = ModList.get().isLoaded("epicfight") && Ef.stun(attacker);
        if (!stunned) {
            attacker.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 16, 4, false, false, false));
            attacker.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 16, 2, false, false, false));
        }
        TechniqueShow.send(attacker, "parried", 0, 1, 18, -1);
    }

    /** How a mob guards (for the checks): by these rules and its tier, or by its own mod's guard (its patch). */
    public static String describe(Mob m) {
        if (m instanceof RoyalMob) {
            return "royal";
        }
        String patch = ModList.get().isLoaded("epicfight") ? Ef.patchClass(m) : "";
        patch = patch == null ? "?" : patch.isEmpty() ? "no patch" : patch.substring(patch.lastIndexOf('.') + 1);
        return (guards(m) ? "oror " + tier(m).name().toLowerCase(java.util.Locale.ROOT) : "native") + " [" + patch + "]";
    }

    /** What a mob has guarded (for the checks): parries, blocks, broken guards, and times it was parried. */
    public static String tally(LivingEntity m) {
        CompoundTag d = m.getPersistentData();
        return d.getInt("OrorParries") + "/" + d.getInt("OrorBlocks") + "/" + d.getInt("OrorGuardBreaks") + "/" + d.getInt("OrorParried");
    }

    // ------------------------------------------------------------------------------------------------------- Epic Fight

    /** Epic Fight, reached by name, so that this works the same across its versions (and without it). */
    static final class Ef {
        private static Method getPatch, play, stun;
        private static Class<?> humanoid, living;
        private static Object stunLong;
        private static final Map<String, Object> ANIMS = new HashMap<>();
        private static boolean looked, broken;
        private static int alternate;

        private Ef() {
        }

        private static void look() {
            if (looked) {
                return;
            }
            looked = true;
            try {
                Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
                living = Class.forName("yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch");
                getPatch = caps.getMethod("getEntityPatch", net.minecraft.world.entity.Entity.class, Class.class);
                humanoid = Class.forName("yesman.epicfight.world.capabilities.entitypatch.HumanoidMobPatch");
                for (Method method : living.getMethods()) {
                    if (method.getName().equals("playAnimationSynchronized") && method.getParameterCount() == 2
                        && method.getParameterTypes()[1] == float.class) {
                        play = method;
                    }
                }
                Class<?> stunType = Class.forName("yesman.epicfight.world.damagesource.StunType");
                for (Object c : stunType.getEnumConstants()) {
                    if (((Enum<?>) c).name().equals("LONG")) {
                        stunLong = c;
                    }
                }
                for (Method method : humanoid.getMethods()) {
                    if (method.getName().equals("applyStun") && method.getParameterCount() == 2 && method.getParameterTypes()[0] == stunType) {
                        stun = method;
                    }
                }
                Class<?> animations = Class.forName("yesman.epicfight.gameasset.Animations");
                for (String name : new String[]{"LONGSWORD_GUARD_ACTIVE_HIT1", "LONGSWORD_GUARD_ACTIVE_HIT2", "SWORD_GUARD_HIT", "BIPED_COMMON_NEUTRALIZED"}) {
                    try {
                        Field f = animations.getField(name);
                        ANIMS.put(name, f.get(null));
                    } catch (ReflectiveOperationException ex) {
                        // that animation is not in this version: its moment goes without it
                    }
                }
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                broken = true;
            }
        }

        private static Object patch(LivingEntity e) throws ReflectiveOperationException {
            look();
            if (broken || getPatch == null || living == null) {
                return null;
            }
            return getPatch.invoke(null, e, living);
        }

        /** The class of a mob's Epic Fight patch ("" without one, null if it may not have been given one yet). */
        static String patchClass(Mob m) {
            try {
                Object p = patch(m);
                if (p == null) {
                    return m.tickCount > 40 ? "" : null;
                }
                return p.getClass().getName();
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                return "";
            }
        }

        static void play(LivingEntity m, String kind) {
            try {
                Object p = patch(m);
                if (p == null || play == null || !humanoid.isInstance(p)) {
                    return;
                }
                Object anim = switch (kind) {
                    case "parry" -> ANIMS.getOrDefault((alternate++ & 1) == 0 ? "LONGSWORD_GUARD_ACTIVE_HIT1" : "LONGSWORD_GUARD_ACTIVE_HIT2",
                        ANIMS.get("SWORD_GUARD_HIT"));
                    case "block" -> ANIMS.get("SWORD_GUARD_HIT");
                    case "break" -> ANIMS.get("BIPED_COMMON_NEUTRALIZED");
                    default -> null;
                };
                if (anim != null) {
                    play.invoke(p, anim, 0.0F);
                }
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                // the moment goes unanimated
            }
        }

        static boolean stun(LivingEntity m) {
            try {
                Object p = patch(m);
                if (p == null || stun == null || stunLong == null || !humanoid.isInstance(p)) {
                    return false;
                }
                stun.invoke(p, stunLong, 1.0F);
                return true;
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                return false;
            }
        }
    }

    /** Debugging: the id of a mob type, for the checks' notes. */
    static String id(LivingEntity e) {
        return BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();
    }
}
