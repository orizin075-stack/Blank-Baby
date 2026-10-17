package jp.oror.reborn;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * Particle work for relic arts and weapon skills, tinted in the character's colour. Shapes are drawn from the server
 * in one go; a particle sent with count 0 takes (dx, dy, dz) * speed as its velocity, which makes rings expand.
 */
public final class RelicEffects {
    public static DustParticleOptions dust(int color, float scale) {
        return new DustParticleOptions(
            new Vector3f((float)(color >> 16 & 0xFF) / 255.0F, (float)(color >> 8 & 0xFF) / 255.0F, (float)(color & 0xFF) / 255.0F), scale
        );
    }

    /** Cast flourish: a magic circle under the caster, a rising spiral and an outward ring; rank 3 raises a pillar of light. */
    public static void show(ServerLevel sl, Entity e, int color, int rank) {
        DustParticleOptions dust = dust(color, rank == 3 ? 1.8F : 1.2F);
        double r = rank == 3 ? 3.4 : (rank == 2 ? 2.6 : 2.0);
        Vec3 c = e.position().add(0.0, 0.08, 0.0);
        circle(sl, c, r, dust);
        int n = 24 * (2 + rank);
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2.0 * i / 24.0;
            double h = (double)i / n * (1.6 + rank);
            double rr = r * 0.45 * (1.0 - (double)i / n * 0.5);
            sl.sendParticles(dust, c.x + Math.cos(a) * rr, c.y + h, c.z + Math.sin(a) * rr, 1, 0.0, 0.0, 0.0, 0.0);
            if (i % 3 == 0) {
                sl.sendParticles(ParticleTypes.END_ROD, c.x + Math.cos(a + Math.PI) * rr, c.y + h, c.z + Math.sin(a + Math.PI) * rr, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
        shock(sl, c.add(0.0, 0.25, 0.0), rank == 3 ? 56 : 32, ParticleTypes.END_ROD, rank == 3 ? 0.6 : 0.35);
        if (rank == 3) {
            for (double y = 0.0; y < 14.0; y += 0.35) {
                sl.sendParticles(ParticleTypes.END_ROD, c.x, c.y + y, c.z, 2, 0.12, 0.0, 0.12, 0.0);
                sl.sendParticles(dust, c.x, c.y + y, c.z, 2, 0.3, 0.0, 0.3, 0.0);
            }
            sl.sendParticles(ParticleTypes.SONIC_BOOM, c.x, c.y + 1.0, c.z, 1, 0.0, 0.0, 0.0, 0.0);
            sl.sendParticles(ParticleTypes.FIREWORK, c.x, c.y + 1.2, c.z, 60, 0.4, 0.6, 0.4, 0.35);
            sound(sl, e.blockPosition(), SoundEvents.TOTEM_USE, 1.0F, 0.7F);
            sound(sl, e.blockPosition(), SoundEvents.ENDER_DRAGON_GROWL, 0.45F, 1.5F);
        } else {
            sound(sl, e.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, 0.8F, 1.25F);
            sound(sl, e.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F, 0.9F + 0.2F * rank);
        }
    }

    /** A magic circle: two rings and a hexagram between them. */
    public static void circle(ServerLevel sl, Vec3 c, double r, ParticleOptions p) {
        int n = (int)Math.max(24.0, r * 22.0);
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2.0 * i / n;
            sl.sendParticles(p, c.x + Math.cos(a) * r, c.y, c.z + Math.sin(a) * r, 1, 0.0, 0.0, 0.0, 0.0);
            if (i % 2 == 0) {
                sl.sendParticles(p, c.x + Math.cos(a) * r * 0.72, c.y, c.z + Math.sin(a) * r * 0.72, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
        for (int k = 0; k < 6; k++) {
            double a = Math.PI * 2.0 * k / 6.0;
            double b = Math.PI * 2.0 * (k + 2) / 6.0;
            line(sl, c.add(Math.cos(a) * r * 0.72, 0.0, Math.sin(a) * r * 0.72), c.add(Math.cos(b) * r * 0.72, 0.0, Math.sin(b) * r * 0.72), p, 0.25);
        }
    }

    public static void line(ServerLevel sl, Vec3 a, Vec3 b, ParticleOptions p, double step) {
        double len = a.distanceTo(b);
        int n = (int)Math.min(160.0, Math.max(1.0, len / step));
        for (int i = 0; i <= n; i++) {
            Vec3 q = a.add(b.subtract(a).scale((double)i / n));
            sl.sendParticles(p, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
        }
    }

    /** An expanding ring on the ground. */
    public static void shock(ServerLevel sl, Vec3 c, int n, ParticleOptions p, double speed) {
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2.0 * i / n;
            sl.sendParticles(p, c.x, c.y, c.z, 0, Math.cos(a), 0.0, Math.sin(a), speed);
        }
    }

    public static void burst(ServerLevel sl, Vec3 c, ParticleOptions p, int n, double spread, double speed) {
        sl.sendParticles(p, c.x, c.y, c.z, n, spread, spread, spread, speed);
    }

    /** A blade arc in front of an entity at chest height; tilt rolls the arc (radians). */
    public static void arc(ServerLevel sl, Entity who, double radius, double tilt, ParticleOptions p, ParticleOptions edge) {
        Vec3 look = who.getLookAngle();
        double yaw = Math.atan2(look.z, look.x);
        Vec3 c = who.position().add(0.0, who.getBbHeight() * 0.6, 0.0);
        for (int i = 0; i <= 28; i++) {
            double t = (i / 28.0 - 0.5) * Math.PI * 0.9;
            double a = yaw + t;
            double y = Math.sin(t) * Math.sin(tilt) * radius;
            Vec3 q = c.add(Math.cos(a) * radius * Math.cos(tilt * 0.3), y, Math.sin(a) * radius * Math.cos(tilt * 0.3));
            sl.sendParticles(p, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
            if (i % 4 == 0) {
                sl.sendParticles(edge, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
    }

    public static void sound(ServerLevel sl, BlockPos at, SoundEvent s, float volume, float pitch) {
        sl.playSound(null, at, s, SoundSource.PLAYERS, volume, pitch);
    }
}
