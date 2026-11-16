package jp.oror.reborn.combat;

import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (059h) The user: "回避能力強化して 当たりそうで上手く回避するから当たらないがいい". Every mob that fights (the monsters,
 * the villagers and golems, the kingdom's soldiers, OROR's gods) now slips a blow or a shot at the last moment: the blade
 * comes down where it stood, the arrow passes a hand's breadth from it. A dodge:
 * <ul>
 * <li>comes when the blow is already landing (the moment it would be hurt, before its guard takes it: with its guard up
 * it parries or blocks instead, MobGuard), and for a shot it sees coming (an arrow, a trident, a fireball within seven
 * blocks, no faster than an arrow, on course to strike it within six ticks but not the next) before it arrives, so that
 * the shot flies past;</li>
 * <li>is a quick step to the side the ground allows (a little back, off the blow's line, its face kept to the foe), as far
 * as its own width needs to clear the blow; the swing meets air (its whiff heard), the cut seen through the place it
 * stood, dust kicked up at its feet;</li>
 * <li>takes a quarter to an eighth of its stamina (MobStamina), and a winded mob does not dodge; between two dodges it
 * waits 1.9 seconds down to under half a second: the blow of a combo after a dodge lands;</li>
 * <li>is as likely as it is good (its prowess and gift, MobProwess): from one blow in ten to six (shots landing 5% to
 * 40%, those it sees coming 25% to 88%), each as it stands at full stamina (a little under half that when spent);</li>
 * <li>is never from behind, nor from an explosion, fire, magic or a relic's art, nor while staggered, sealed, its guard
 * broken, riding, asleep or without its AI (a statue, a test's target).</li>
 * </ul>
 * Seen as a step on every mob (its body leans with it: GuardPoses, OROR's rigs and the royals' poses, "dodge_l" and
 * "dodge_r").
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MobDodge {
    private MobDodge() {
    }

    // (059h, the user: "強くてレベル高いモブ程経験積んでるからうまいし　スタミナも多めで　一定にしないで") how well it dodges
    // is its prowess (MobProwess: its level, experience, strength, tactics, what it has learnt dodging, what it is) and
    // its own gift: a fresh zombie slips a blow one time in ten, a seasoned knight four in ten, a god six (with its
    // gift, at most three in four); it dodges again sooner, spends less on a dodge and steps no further than it needs

    /** Its chance of slipping a blow landing (at full stamina). */
    static float blowChance(Mob m) {
        return Math.min(0.75F, MobProwess.lerp(MobProwess.of(m), 0.10F, 0.60F) * MobProwess.gift(m));
    }

    /** Of slipping a shot as it lands. */
    static float shotChance(Mob m) {
        return Math.min(0.55F, MobProwess.lerp(MobProwess.of(m), 0.05F, 0.40F) * MobProwess.gift(m));
    }

    /** Of stepping from a shot it sees coming. */
    static float seenChance(Mob m) {
        return Math.min(0.95F, MobProwess.lerp(MobProwess.of(m), 0.25F, 0.88F) * MobProwess.gift(m));
    }

    /** Ticks between two dodges: 1.9 seconds for the clumsiest, under half a second for a god. */
    static int cooldown(Mob m) {
        return Math.round(MobProwess.lerp(MobProwess.of(m), 38F, 9F) / MobProwess.gift(m));
    }

    /** A dodge's price, as a share of its stamina: a quarter for the clumsiest, an eighth for the best. */
    static float cost(Mob m) {
        return MobStamina.max(m) * MobProwess.lerp(MobProwess.of(m), 0.25F, 0.13F);
    }

    /** Whether it can dodge now (a fighter, on its feet and its own master, not winded, staggered, sealed or riding). */
    static boolean able(Mob m) {
        if (!m.isAlive() || m.isNoAi() || m.isPassenger() || m.isSleeping() || m.isVehicle() && !(m instanceof SupremeEntity)
            || !(m instanceof RoyalMob || m instanceof SupremeEntity || MobGuard.fighter(m))) {
            return false;
        }
        long now = m.level().getGameTime();
        CompoundTag d = m.getPersistentData();
        if (MobStamina.winded(m) || MobGuard.staggered(m) || jp.oror.reborn.RelicArts.busy() || d.getLong("ororSealUntil") > now
            || d.getLong("ororGuardBrokenUntil") > now) {
            return false;
        }
        return now - d.getLong("OrorDodgeAt") >= cooldown(m);
    }

    // ------------------------------------------------------------------------------------------------ a blow landing

    /** A blow or a shot landing on a mob (its guard down): true when it slipped it (the hurt is then undone). */
    public static boolean dodge(Mob m, DamageSource src, float amount) {
        if (!(m.level() instanceof ServerLevel sl) || !able(m) || MobGuard.unblockable(src)) {
            return false;
        }
        Entity direct = src.getDirectEntity();
        LivingEntity attacker = src.getEntity() instanceof LivingEntity l ? l : null;
        if (attacker == m || direct == m || attacker != null && friendly(attacker, m)) {
            return false;
        }
        boolean shot = direct instanceof Projectile;
        boolean melee = !shot && direct != null && direct == attacker;
        if (!shot && !melee) {
            return false;
        }
        // where it comes from: the striker, or the line the shot came in on
        Vec3 from;
        if (shot) {
            Vec3 v = direct.getDeltaMovement();
            from = v.lengthSqr() > 1.0E-4 ? direct.position().subtract(v.normalize().scale(4)) : direct.position();
        } else {
            from = attacker.position();
        }
        Vec3 to = from.subtract(m.position()).multiply(1, 0, 1);
        Vec3 facing = m.getLookAngle().multiply(1, 0, 1);
        if (to.lengthSqr() < 1.0E-6 || facing.lengthSqr() > 1.0E-6 && to.normalize().dot(facing.normalize()) < (shot ? -0.35 : -0.1)) {
            note(m, "OrorDodgeBehind");
            return false;   // from behind: it never saw it
        }
        // it learns from every blow it meets, slipped or not
        MobProwess.learn(m);
        float chance = (shot ? shotChance(m) : blowChance(m)) * (0.45F + 0.55F * MobStamina.fraction(m));
        if (m.getRandom().nextFloat() >= chance) {
            return false;
        }
        Vec3 way = pick(sl, m, to.normalize().scale(-1));
        if (way == null) {
            note(m, "OrorDodgeNoRoom");
            return false;
        }
        if (!MobStamina.spend(m, cost(m))) {
            return false;
        }
        step(sl, m, way, to.normalize().scale(-1), attacker, shot ? direct : null, false);
        return true;
    }

    /** The royals (their own guard first, RoyalMob.defend at the highest priority: what it took never comes here). */
    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void royal(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof RoyalMob r) || r.level().isClientSide) {
            return;
        }
        if (((Object) r) instanceof jp.oror.reborn.mixin.RoyalGuardAccess a && a.oror$guardRemaining() > 0) {
            return;   // its guard is up: the guard's own
        }
        if (dodge(r, e.getSource(), e.getAmount())) {
            e.setCanceled(true);
        }
    }

    // ------------------------------------------------------------------------------------------------ a shot seen coming

    /** Shots already judged by a mob (each is weighed once). */
    private static final Map<Projectile, java.util.Set<Integer>> WEIGHED = new WeakHashMap<>();

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || !(m.level() instanceof ServerLevel sl) || (m.tickCount + m.getId()) % 2 != 0) {
            return;
        }
        if (m.getTarget() == null && m.getLastHurtByMob() == null || !able(m)) {
            return;
        }
        float cost = cost(m);
        if (!MobStamina.has(m, cost)) {
            return;
        }
        AABB body = m.getBoundingBox().inflate(0.3);
        for (Projectile p : sl.getEntitiesOfClass(Projectile.class, m.getBoundingBox().inflate(7.0), x -> x.isAlive() && x.getOwner() != m)) {
            Vec3 v = p.getDeltaMovement();
            // only a shot it can see coming and step from in time: an arrow's speed or slower (a bullet is met when it
            // lands, dodge()), on course to strike it between a tick and a half and six ticks of its flight from now
            if (v.lengthSqr() < 0.09 || v.lengthSqr() > 16.0 || allied(p.getOwner(), m)) {
                continue;
            }
            Vec3 at = p.position();
            if (body.contains(at) || body.clip(at, at.add(v.scale(6))).isEmpty() || body.clip(at, at.add(v.scale(1.5))).isPresent()) {
                continue;
            }
            java.util.Set<Integer> seen = WEIGHED.computeIfAbsent(p, x -> new java.util.HashSet<>());
            if (!seen.add(m.getId())) {
                continue;
            }
            MobProwess.learn(m);
            float chance = seenChance(m) * (0.45F + 0.55F * MobStamina.fraction(m));
            if (m.getRandom().nextFloat() >= chance) {
                continue;
            }
            Vec3 away = v.multiply(1, 0, 1);
            if (away.lengthSqr() < 1.0E-6) {
                continue;   // falling straight down on it: no side to step to
            }
            away = away.normalize();
            Vec3 way = pick(sl, m, away);
            if (way == null || !MobStamina.spend(m, cost)) {
                return;
            }
            LivingEntity owner = p.getOwner() instanceof LivingEntity o ? o : null;
            step(sl, m, way, away, owner, p, true);
            return;
        }
    }

    private static boolean allied(Entity owner, Mob m) {
        return owner instanceof LivingEntity o && (o == m || friendly(o, m));
    }

    /**
     * (CI 68) A blow from its own side is no blow to dodge (the village's and the kingdom's own ways meet it): a mob on its
     * team, the village's folk (its villagers, golems and guards) one of another, the royals one of another. Dodged, a
     * villager struck by mistake by one of his own village was "struck" in the mod's own trial of friendly blows.
     */
    static boolean friendly(LivingEntity a, Mob m) {
        if (a.isAlliedTo(m) || m.isAlliedTo(a)) {
            return true;
        }
        return folk(a) && folk(m) || a instanceof RoyalMob && m instanceof RoyalMob;
    }

    private static boolean folk(Entity e) {
        return e instanceof net.minecraft.world.entity.npc.AbstractVillager || e instanceof net.minecraft.world.entity.animal.IronGolem
            || net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getNamespace().equals("guardvillagers");
    }

    // ------------------------------------------------------------------------------------------------ the step

    /**
     * How far it steps to clear a blow: its own half width and a little, at most four blocks; the better it is, the less
     * it needs (a clumsy hop of 1.3 blocks past its side, a master's 0.75: by a hair).
     */
    private static double reach(Mob m) {
        return Math.min(4.0, m.getBbWidth() * 0.5 + MobProwess.lerp(MobProwess.of(m), 1.3F, 0.75F));
    }

    /**
     * The way to step (a unit vector), the blow coming along {@code away} (from the striker toward the mob): to its left or
     * right off the blow's line, a little back from it, where the ground allows (the side with room, either at random);
     * straight back if neither side has room; null if it is hemmed in.
     */
    private static Vec3 pick(ServerLevel sl, Mob m, Vec3 away) {
        Vec3 side = new Vec3(-away.z, 0, away.x);
        double r = reach(m);
        Vec3 left = side.scale(0.92).add(away.scale(0.38)).normalize(), right = side.scale(-0.92).add(away.scale(0.38)).normalize();
        boolean l = room(sl, m, left.scale(r)), rr = room(sl, m, right.scale(r));
        if (l && rr) {
            return m.getRandom().nextBoolean() ? left : right;
        }
        if (l) {
            return left;
        }
        if (rr) {
            return right;
        }
        return room(sl, m, away.scale(r)) ? away : null;
    }

    /** Room to step so far: its body clear of blocks there, and ground under it within two blocks (unless it flies). */
    private static boolean room(ServerLevel sl, Mob m, Vec3 by) {
        AABB there = m.getBoundingBox().move(by.x, 0.05, by.z);
        if (!sl.noCollision(m, there)) {
            return false;
        }
        // (CI 68) in the air already (a god hovering, a mob in a leap) there is no ground to keep to: Ferdinand, struck 28
        // times hovering over the floor, never had room to dodge
        if (!m.onGround() || m.isNoGravity() || m instanceof net.minecraft.world.entity.FlyingMob) {
            return true;
        }
        BlockPos foot = BlockPos.containing(m.getX() + by.x, m.getY() - 0.2, m.getZ() + by.z);
        for (int i = 0; i < 3; i++) {
            BlockPos q = foot.below(i);
            if (sl.getBlockState(q).isFaceSturdy(sl, q, Direction.UP)) {
                return true;
            }
        }
        return false;
    }

    private static void step(ServerLevel sl, Mob m, Vec3 way, Vec3 away, LivingEntity foe, Entity shot, boolean seen) {
        long now = sl.getGameTime();
        CompoundTag d = m.getPersistentData();
        d.putLong("OrorDodgeAt", now);
        d.putInt("OrorDodges", d.getInt("OrorDodges") + 1);
        d.putInt(shot == null ? "OrorDodgedBlows" : seen ? "OrorDodgedSeen" : "OrorDodgedShots",
            d.getInt(shot == null ? "OrorDodgedBlows" : seen ? "OrorDodgedSeen" : "OrorDodgedShots") + 1);
        Vec3 stood = m.position().add(0, m.getBbHeight() * 0.55, 0);
        // a short hop to the side: about its reach in a quarter second, its feet back down at once
        double speed = 0.42 * Math.max(1.0, reach(m) / 1.4);
        m.setDeltaMovement(way.x * speed, m.onGround() ? 0.2 : Math.max(m.getDeltaMovement().y, 0.05), way.z * speed);
        m.hurtMarked = true;
        m.getNavigation().stop();
        if (foe != null) {
            m.getLookControl().setLookAt(foe, 60F, 60F);
        }
        // the blow meets air: its whiff, the cut through the place it stood, dust at its feet, a breath of the step
        if (shot == null) {
            Vec3 cut = foe == null ? stood : stood.lerp(foe.position().add(0, foe.getBbHeight() * 0.6, 0), 0.25);
            sl.playSound(null, BlockPos.containing(cut), SoundEvents.PLAYER_ATTACK_NODAMAGE, SoundSource.HOSTILE, 0.9F, 0.9F + m.getRandom().nextFloat() * 0.3F);
            sl.sendParticles(ParticleTypes.SWEEP_ATTACK, cut.x, cut.y, cut.z, 1, 0, 0, 0, 0);
        } else {
            // the shot's line past it, drawn in sparks
            Vec3 v = shot.getDeltaMovement().lengthSqr() > 1.0E-6 ? shot.getDeltaMovement().normalize() : away;
            for (int i = -2; i <= 2; i++) {
                Vec3 q = stood.add(v.scale(i * 0.6));
                sl.sendParticles(ParticleTypes.CRIT, q.x, q.y, q.z, 1, 0.02, 0.02, 0.02, 0.0);
            }
            sl.playSound(null, BlockPos.containing(stood), SoundEvents.ARROW_SHOOT, SoundSource.HOSTILE, 0.35F, 1.9F);
        }
        sl.playSound(null, m.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.HOSTILE, 0.3F, 1.9F);
        sl.sendParticles(ParticleTypes.CLOUD, m.getX(), m.getY() + 0.1, m.getZ(), 5, m.getBbWidth() * 0.3, 0.02, m.getBbWidth() * 0.3, 0.03);
        sl.sendParticles(ParticleTypes.WHITE_ASH, stood.x, stood.y, stood.z, 10, m.getBbWidth() * 0.25, m.getBbHeight() * 0.3, m.getBbWidth() * 0.25, 0.01);
        // its left or right, as it faces the blow (facing back along it: its left is the side's positive way)
        Vec3 side = new Vec3(-away.z, 0, away.x);
        boolean toLeft = way.dot(side) >= 0;
        TechniqueShow.send(m, toLeft ? "dodge_l" : "dodge_r", 0, 1, 10, foe == null ? -1 : foe.getId());
    }

    private static void note(Mob m, String key) {
        m.getPersistentData().putInt(key, m.getPersistentData().getInt(key) + 1);
    }

    /** For the checks: dodges (blows, shots landing, shots seen coming), and blows it could not dodge (behind it, no room). */
    public static String tally(LivingEntity m) {
        CompoundTag d = m.getPersistentData();
        return d.getInt("OrorDodges") + " (" + d.getInt("OrorDodgedBlows") + "/" + d.getInt("OrorDodgedShots") + "/" + d.getInt("OrorDodgedSeen")
            + ") behind " + d.getInt("OrorDodgeBehind") + " noRoom " + d.getInt("OrorDodgeNoRoom");
    }
}
