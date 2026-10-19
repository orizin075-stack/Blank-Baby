package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Cannon shells that fly (v0.17.11). A shell was a hitscan line that burst at once wherever the crosshair pointed; now
 * it is a glowing shell with a smoke trail that travels about 2.4 blocks a tick on a slight arc and bursts on the first
 * enemy or block it meets (or after three seconds in the air). No entity is registered: the shells are simulated on
 * the server and drawn with particles, ticked from WorldEvents.levelTick. Used by relic cannons and by characters
 * wielding one (BossArms).
 */
public final class RelicShells {
    private static final double GRAVITY = 0.025;
    private static final List<Shell> LIVE = new ArrayList<>();

    private RelicShells() {
    }

    private static final class Shell {
        final ServerLevel sl;
        final LivingEntity owner;
        final float damage;
        final double radius;
        final DustParticleOptions dust;
        final boolean big;
        Vec3 pos;
        Vec3 vel;
        int life = 60;

        Shell(ServerLevel sl, LivingEntity owner, Vec3 pos, Vec3 vel, float damage, double radius, DustParticleOptions dust, boolean big) {
            this.sl = sl;
            this.owner = owner;
            this.pos = pos;
            this.vel = vel;
            this.damage = damage;
            this.radius = radius;
            this.dust = dust;
            this.big = big;
        }
    }

    /** Fire a shell from a point with a velocity (blocks per tick). */
    static void fire(LivingEntity owner, ServerLevel sl, Vec3 from, Vec3 vel, float damage, double radius, int color, boolean big) {
        LIVE.add(new Shell(sl, owner, from, vel, damage, radius, RelicEffects.dust(color, big ? 2.4F : 1.8F), big));
        sl.sendParticles(ParticleTypes.LARGE_SMOKE, from.x, from.y, from.z, 6, 0.1, 0.1, 0.1, 0.04);
        sl.sendParticles(ParticleTypes.FLAME, from.x, from.y, from.z, 4, 0.05, 0.05, 0.05, 0.05);
        RelicEffects.sound(sl, BlockPos.containing(from), SoundEvents.WITHER_SHOOT, 0.8F, 1.3F);
    }

    /** The velocity that lobs a shell from a to b at about this speed, allowing for the drop. */
    static Vec3 lob(Vec3 a, Vec3 b, double speed) {
        Vec3 d = b.subtract(a);
        double t = Math.max(1.0, d.length() / speed);
        return d.scale(1.0 / t).add(0.0, 0.5 * GRAVITY * t, 0.0);
    }

    static void tick(ServerLevel sl) {
        if (LIVE.isEmpty()) {
            return;
        }
        // a burst can hurt something that fires a new shell: step a snapshot
        List<Shell> here = new ArrayList<>();
        for (Iterator<Shell> it = LIVE.iterator(); it.hasNext(); ) {
            Shell s = it.next();
            if (s.sl == sl) {
                here.add(s);
                it.remove();
            }
        }
        for (Shell s : here) {
            if (step(s)) {
                LIVE.add(s);
            }
        }
    }

    /** One tick of flight; false once the shell has burst. */
    private static boolean step(Shell s) {
        Vec3 next = s.pos.add(s.vel);
        if (!s.sl.hasChunkAt(BlockPos.containing(next))) {
            return false;
        }
        Vec3 end = next;
        var wall = s.sl.clip(new ClipContext(s.pos, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, s.owner));
        boolean hit = false;
        if (wall.getType() != HitResult.Type.MISS) {
            end = wall.getLocation();
            hit = true;
        }
        double best = end.distanceToSqr(s.pos);
        for (LivingEntity e : s.sl.getEntitiesOfClass(LivingEntity.class, new AABB(s.pos, end).inflate(1.0), e -> enemy(s.owner, e))) {
            java.util.Optional<Vec3> at = e.getBoundingBox().inflate(0.3).clip(s.pos, end);
            if (at.isPresent() && at.get().distanceToSqr(s.pos) <= best) {
                best = at.get().distanceToSqr(s.pos);
                end = at.get();
                hit = true;
            }
        }
        // the trail
        for (int i = 1; i <= 3; i++) {
            Vec3 q = s.pos.add(end.subtract(s.pos).scale(i / 3.0));
            s.sl.sendParticles(s.dust, q.x, q.y, q.z, 2, 0.08, 0.08, 0.08, 0.0);
            s.sl.sendParticles(ParticleTypes.SMOKE, q.x, q.y, q.z, 1, 0.05, 0.05, 0.05, 0.0);
        }
        s.sl.sendParticles(s.big ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.FLAME, end.x, end.y, end.z, 2, 0.05, 0.05, 0.05, 0.01);
        if (hit || --s.life <= 0) {
            burst(s, end);
            return false;
        }
        s.pos = next;
        s.vel = s.vel.add(0.0, -GRAVITY, 0.0);
        return true;
    }

    private static void burst(Shell s, Vec3 at) {
        boolean alive = s.owner.isAlive();
        for (LivingEntity e : s.sl.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(s.radius),
            e -> enemy(s.owner, e) && e.position().add(0.0, e.getBbHeight() * 0.5, 0.0).distanceTo(at) <= s.radius + e.getBbWidth() * 0.5)) {
            if (alive) {
                if (s.owner instanceof Player p) {
                    RelicArts.strike(p, e, s.damage, false);
                } else if (s.owner instanceof SupremeEntity b) {
                    BossPowers.hit(b, e, s.damage);
                }
            }
            if (!(e instanceof SupremeEntity)) {
                BossPowers.push(e, BossPowers.flat(e.position().subtract(at)).scale(0.8).add(0.0, 0.6, 0.0));
            }
        }
        s.sl.sendParticles(s.big ? ParticleTypes.EXPLOSION_EMITTER : ParticleTypes.EXPLOSION, at.x, at.y, at.z, s.big ? 1 : 4, 0.6, 0.6, 0.6, 0.0);
        RelicEffects.shock(s.sl, at, 40, ParticleTypes.CLOUD, 0.5);
        RelicEffects.burst(s.sl, at, s.dust, 30, s.radius * 0.4, 0.0);
        RelicEffects.burst(s.sl, at, ParticleTypes.LAVA, 8, 0.6, 0.0);
        RelicEffects.sound(s.sl, BlockPos.containing(at), SoundEvents.FIREWORK_ROCKET_BLAST, 2.0F, 0.5F);
        RelicEffects.sound(s.sl, BlockPos.containing(at), SoundEvents.ANVIL_LAND, 0.5F, 0.5F);
    }

    private static boolean enemy(LivingEntity owner, LivingEntity e) {
        if (e == owner || !e.isAlive()) {
            return false;
        }
        if (owner instanceof Player p) {
            return RelicPowers.enemy(p, e);
        }
        return owner instanceof SupremeEntity b && b.validEnemy(e);
    }
}
