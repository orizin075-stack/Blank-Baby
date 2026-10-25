package jp.oror.reborn.arms.sbw;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.decoration.HangingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.entity.PartEntity;
import org.joml.Vector3f;

/** Hit-scan beams for the OROR guns: what the beam passes, whom it hits, and what everyone sees. */
final class OrorBeams {
    record Hit(Entity entity, Vec3 at, double distance) {
    }

    record Path(Vec3 end, int pierced) {
    }

    /**
     * Marches the beam in quarter blocks. {@code maxPierce} solid blocks are passed (0: stop at the first); blocks with
     * an explosion resistance of obsidian or more, or unbreakable ones, always stop it. {@code glassPasses} lets the
     * beam through glass and ice as light would.
     */
    static Path trace(ServerLevel level, Vec3 start, Vec3 dir, double range, int maxPierce, boolean glassPasses) {
        BlockPos last = null;
        int pierced = 0;
        for (double d = 0; d <= range; d += 0.25) {
            Vec3 p = start.add(dir.scale(d));
            BlockPos pos = BlockPos.containing(p);
            if (pos.equals(last)) {
                continue;
            }
            last = pos;
            if (!level.isLoaded(pos) || level.isOutsideBuildHeight(pos)) {
                return new Path(p, pierced);
            }
            BlockState state = level.getBlockState(pos);
            if (state.isAir() || state.getCollisionShape(level, pos).isEmpty()) {
                continue;
            }
            if (glassPasses && (state.is(Tags.Blocks.GLASS_BLOCKS) || state.is(Tags.Blocks.GLASS_PANES) || state.is(BlockTags.ICE))) {
                continue;
            }
            boolean hard = state.getDestroySpeed(level, pos) < 0 || state.getBlock().getExplosionResistance() >= 1200;
            if (hard || pierced >= maxPierce) {
                return new Path(p, pierced);
            }
            pierced++;
        }
        return new Path(start.add(dir.scale(range)), pierced);
    }

    /** Everything the segment passes within {@code radius}, nearest first; not the shooter, its pets or its team. */
    static List<Hit> hits(ServerLevel level, Entity shooter, Vec3 start, Vec3 end, double radius) {
        List<Hit> out = new ArrayList<>();
        AABB box = new AABB(start, end).inflate(radius + 2);
        for (Entity e : level.getEntities(shooter, box, e -> e.isAlive() && !e.isSpectator() && e.isPickable())) {
            if (e instanceof HangingEntity || e instanceof Projectile || shooter.isAlliedTo(e) || e.isPassengerOfSameVehicle(shooter)) {
                continue;
            }
            if (e instanceof OwnableEntity pet && pet.getOwner() == shooter) {
                continue;
            }
            if (!(e instanceof LivingEntity) && !(e instanceof PartEntity<?>) && !e.getClass().getName().contains("superbwarfare.entity.vehicle")) {
                continue;
            }
            Optional<Vec3> at = e.getBoundingBox().inflate(radius).clip(start, end);
            if (at.isEmpty() && e.getBoundingBox().inflate(radius).contains(start)) {
                at = Optional.of(start);
            }
            at.ifPresent(p -> out.add(new Hit(e, p, p.distanceTo(start))));
        }
        out.sort(Comparator.comparingDouble(Hit::distance));
        return out;
    }

    static DamageSource source(ServerLevel level, ResourceKey<DamageType> type, Entity shooter) {
        return new DamageSource(level.registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(type), shooter, shooter);
    }

    /** True when the beam met the upper quarter of a standing body: the head. */
    static boolean headshot(Hit hit) {
        AABB b = hit.entity().getBoundingBox();
        return hit.entity() instanceof LivingEntity && b.getYsize() > 1.0 && hit.at().y > b.maxY - b.getYsize() * 0.25;
    }

    static void hurt(Entity target, DamageSource source, float amount) {
        target.invulnerableTime = 0;
        target.hurt(source, amount);
        target.invulnerableTime = 0;
    }

    /** The muzzle: a little ahead, right and below the eye, so the beam leaves the gun rather than the face. */
    static Vec3 muzzle(Entity shooter, Vec3 eye, Vec3 dir) {
        Vec3 right = dir.cross(new Vec3(0, 1, 0));
        right = right.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : right.normalize();
        Vec3 up = right.cross(dir).normalize();
        return eye.add(dir.scale(1.1)).add(right.scale(0.28)).add(up.scale(-0.22));
    }

    /** Particles along the beam to every player within 256 blocks of it (long-distance packets, so all of it shows). */
    static void draw(ServerLevel level, Vec3 from, Vec3 to, ParticleOptions core, double coreStep, ParticleOptions spark, double sparkStep) {
        double length = from.distanceTo(to);
        Vec3 dir = length < 1e-6 ? Vec3.ZERO : to.subtract(from).scale(1 / length);
        for (ServerPlayer viewer : level.players()) {
            if (viewer.distanceToSqr(from) > 256 * 256 && viewer.distanceToSqr(to) > 256 * 256) {
                continue;
            }
            for (double d = 0; d <= length; d += d < 64 ? coreStep : coreStep * 2) {
                Vec3 p = from.add(dir.scale(d));
                level.sendParticles(viewer, core, true, p.x, p.y, p.z, 1, 0, 0, 0, 0);
            }
            if (spark != null) {
                for (double d = 0; d <= length; d += d < 64 ? sparkStep : sparkStep * 2) {
                    Vec3 p = from.add(dir.scale(d));
                    level.sendParticles(viewer, spark, true, p.x, p.y, p.z, 2, 0.12, 0.12, 0.12, 0.02);
                }
            }
        }
    }

    static DustParticleOptions dust(int rgb, float scale) {
        return new DustParticleOptions(new Vector3f(((rgb >> 16) & 255) / 255f, ((rgb >> 8) & 255) / 255f, (rgb & 255) / 255f), scale);
    }

    static void impact(ServerLevel level, Entity shooter, Vec3 at, float power, ParticleOptions burst) {
        level.explode(shooter, at.x, at.y, at.z, power, Level.ExplosionInteraction.NONE);
        level.sendParticles(burst, at.x, at.y, at.z, 40, 0.6, 0.6, 0.6, 0.25);
        level.sendParticles(ParticleTypes.FLASH, at.x, at.y, at.z, 2, 0, 0, 0, 0);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.PLAYERS, 3.0f, 0.7f);
    }

    private OrorBeams() {
    }
}
