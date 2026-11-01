package jp.oror.reborn.arms.sbw;

import com.atsuishio.superbwarfare.data.gun.GunData;
import com.atsuishio.superbwarfare.data.gun.ShootParameters;
import com.atsuishio.superbwarfare.init.ModDamageTypes;
import java.util.List;
import java.util.function.Supplier;
import jp.oror.reborn.arms.sbw.client.RailgunRenderer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.phys.Vec3;
import software.bernie.geckolib.renderer.GeoItemRenderer;

/**
 * 電磁投射砲『天穿』: a 512-block hit-scan slug. It passes up to 32 blocks softer than obsidian and every body on its
 * line (full damage to each, armour ignored), throwing them back, and ends in a shock wave that breaks no blocks.
 */
public class RailgunItem extends OrorGunItem {
    static final double RANGE = 512;
    static final int PIERCE = 32;

    @Override
    public Supplier<? extends GeoItemRenderer<? extends Item>> getRenderer() {
        return RailgunRenderer::new;
    }

    @Override
    public boolean canAdjustZoom(GunData data) {
        return true;
    }

    @Override
    protected void fire(ShootParameters p, double damage, double headshot) {
        ServerLevel level = p.level;
        Entity shooter = p.shooter;
        Vec3 dir = p.shootDirection.normalize();
        OrorBeams.Path path = OrorBeams.trace(level, p.shootPosition, dir, RANGE, PIERCE, false);
        DamageSource source = OrorBeams.source(level, ModDamageTypes.GUN_FIRE_ABSOLUTE, shooter);
        DamageSource head = OrorBeams.source(level, ModDamageTypes.GUN_FIRE_HEADSHOT_ABSOLUTE, shooter);
        List<OrorBeams.Hit> hits = OrorBeams.hits(level, shooter, p.shootPosition, path.end(), 0.35);
        for (OrorBeams.Hit hit : hits) {
            boolean isHead = OrorBeams.headshot(hit);
            OrorBeams.hurt(hit.entity(), isHead ? head : source, (float) (isHead ? damage * headshot : damage));
            if (hit.entity() instanceof LivingEntity living) {
                living.knockback(2.5, -dir.x, -dir.z);
                living.setDeltaMovement(living.getDeltaMovement().add(0, 0.35, 0));
                living.hurtMarked = true;
            }
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, hit.at().x, hit.at().y, hit.at().z, 30, 0.3, 0.3, 0.3, 0.6);
        }
        Vec3 from = OrorBeams.muzzle(shooter, p.shootPosition, dir);
        OrorBeams.draw(level, from, path.end(), OrorBeams.dust(0x4FF3FF, 2.2f), 0.4, ParticleTypes.ELECTRIC_SPARK, 1.5);
        for (int i = 1; i <= 3; i++) {
            Vec3 ring = from.add(dir.scale(i * 1.6));
            level.sendParticles(ParticleTypes.SONIC_BOOM, ring.x, ring.y, ring.z, 1, 0, 0, 0, 0);
        }
        OrorBeams.impact(level, shooter, path.end(), 4.0f, ParticleTypes.ELECTRIC_SPARK);
    }
}
