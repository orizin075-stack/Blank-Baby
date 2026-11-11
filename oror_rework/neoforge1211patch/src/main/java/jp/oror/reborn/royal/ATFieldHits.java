package jp.oror.reborn.royal;

import java.util.HashMap;
import java.util.Map;
import jp.oror.reborn.waza.WazaNet;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.network.PacketDistributor;

/**
 * (059, the V20 design's 06_at_field.md) Where a blow met the villager king's AT field, for the membrane drawn round him
 * (ATFieldRenderer): the field's own reckoning (RoyalSovereign.beginHurt) is untouched; this only tells those who see
 * him which way the blow came from and how hard it was against the field's whole (at most every other tick).
 */
public final class ATFieldHits {
    private static final Map<Integer, Long> LAST = new HashMap<>();

    private ATFieldHits() {
    }

    /** RoyalSovereign.beginHurt's head (KingSovereignMixin): a blow at the king while his field holds. */
    public static void struck(RoyalMob mob, DamageSource src, float amount) {
        if (mob == null || mob.level().isClientSide || mob.role() != RoyalRole.KING || mob.atField() <= 0.0F || mob.atBreached()) {
            return;
        }
        long now = mob.level().getGameTime();
        Long last = LAST.get(mob.getId());
        if (last != null && now - last < 2) {
            return;
        }
        if (LAST.size() > 64) {
            LAST.clear();
        }
        LAST.put(mob.getId(), now);
        Entity direct = src.getDirectEntity();
        Vec3 from = direct != null ? direct.getBoundingBox().getCenter() : src.getSourcePosition();
        if (from == null) {
            return;
        }
        Vec3 d = from.subtract(mob.getBoundingBox().getCenter());
        if (d.lengthSqr() < 1.0E-6) {
            return;
        }
        d = d.normalize();
        float capacity = 10000.0F * (float) Math.pow(4, Math.max(0, Math.min(3, mob.lifePhase())));
        PacketDistributor.sendToPlayersTrackingEntity(mob,
            new WazaNet.AtHit(mob.getId(), (float) d.x, (float) d.y, (float) d.z, Math.min(1.0F, Math.max(0.0F, amount) / capacity)));
    }
}
