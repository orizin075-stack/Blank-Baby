package jp.oror.reborn.arms.sbw;

import com.atsuishio.superbwarfare.data.gun.ShootParameters;
import com.atsuishio.superbwarfare.init.ModDamageTypes;
import java.util.function.Supplier;
import jp.oror.reborn.arms.sbw.client.LaserGunRenderer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.renderer.GeoItemRenderer;

/**
 * 収束光線銃『神罰』: a 256-block beam a block and a half wide. It passes glass and ice, stops at the first other
 * block, burns and marks everything inside it, and the focus point bursts over five blocks.
 */
public class LaserGunItem extends OrorGunItem {
    static final double RANGE = 256;
    static final double WIDTH = 0.75;
    static final double BURST = 5;

    @Override
    public Supplier<? extends GeoItemRenderer<? extends Item>> getRenderer() {
        return LaserGunRenderer::new;
    }

    @Override
    protected void fire(ShootParameters p, double damage, double headshot) {
        ServerLevel level = p.level;
        Entity shooter = p.shooter;
        Vec3 dir = p.shootDirection.normalize();
        OrorBeams.Path path = OrorBeams.trace(level, p.shootPosition, dir, RANGE, 0, true);
        DamageSource source = OrorBeams.source(level, ModDamageTypes.LASER, shooter);
        DamageSource head = OrorBeams.source(level, ModDamageTypes.LASER_HEADSHOT, shooter);
        for (OrorBeams.Hit hit : OrorBeams.hits(level, shooter, p.shootPosition, path.end(), WIDTH)) {
            boolean isHead = OrorBeams.headshot(hit);
            OrorBeams.hurt(hit.entity(), isHead ? head : source, (float) (isHead ? damage * headshot : damage));
            scorch(hit.entity());
            level.sendParticles(ParticleTypes.FLAME, hit.at().x, hit.at().y, hit.at().z, 24, 0.3, 0.4, 0.3, 0.08);
        }
        // the focus point: everything within five blocks takes a fifth of the beam and burns
        Vec3 end = path.end();
        for (Entity e : level.getEntities(shooter, new AABB(end, end).inflate(BURST), e -> e.isAlive() && e instanceof LivingEntity)) {
            if (e.distanceToSqr(end) <= BURST * BURST && !shooter.isAlliedTo(e)) {
                OrorBeams.hurt(e, source, (float) (damage * 0.2));
                scorch(e);
            }
        }
        Vec3 from = OrorBeams.muzzle(shooter, p.shootPosition, dir);
        OrorBeams.draw(level, from, end, OrorBeams.dust(0xFF2A4A, 3.0f), 0.3, ParticleTypes.END_ROD, 2.0);
        level.sendParticles(ParticleTypes.FLASH, from.x, from.y, from.z, 1, 0, 0, 0, 0);
        OrorBeams.impact(level, shooter, end, 3.0f, ParticleTypes.LAVA);
    }

    private static void scorch(Entity e) {
        e.igniteForSeconds(10);
        if (e instanceof LivingEntity living) {
            living.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0));
            living.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 3));
            living.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 200, 1));
        }
    }
}
