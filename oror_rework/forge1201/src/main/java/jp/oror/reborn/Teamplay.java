package jp.oror.reborn;

import java.util.Comparator;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

public final class Teamplay {
    public static void coordinate(Mob leader, ServerLevel sl, LivingEntity enemy) {
        if ((Boolean)RebornConfig.COOPERATION.get() && AdaptiveCombat.enemy(leader, enemy) && MobLevels.level(leader) >= 2) {
            CompoundTag n = MobMind.data(leader);
            if (n.getLong("NextCoordination") <= sl.getGameTime()) {
                n.putLong("NextCoordination", sl.getGameTime() + 20L);
                List<Mob> friends = sl.getEntitiesOfClass(
                        Mob.class, leader.getBoundingBox().inflate(16.0), m -> m != leader && AdaptiveCombat.active(m) && AdaptiveCombat.allied(leader, m)
                    )
                    .stream()
                    .sorted(Comparator.comparingDouble(leader::distanceToSqr))
                    .limit(8L)
                    .toList();

                for (Mob friend : friends) {
                    if (!AdaptiveCombat.enemy(friend, friend.getTarget()) && AdaptiveCombat.enemy(friend, enemy)) {
                        friend.setTarget(enemy);
                        MobMind.data(friend).putUUID("SharedTarget", enemy.getUUID());
                        n.putInt("Alerts", n.getInt("Alerts") + 1);
                    }

                    MobMind.remember(friend, BuiltInRegistries.ENTITY_TYPE.getKey(enemy.getType()).toString(), "focus; flanking; protect support");
                }

                if (MobLevels.level(leader) >= 3
                    && (double)leader.getHealth() > (double)leader.getMaxHealth() * 0.5
                    && n.getLong("NextSupport") <= sl.getGameTime()) {
                    Mob weak = friends.stream()
                        .filter(m -> m.distanceToSqr(leader) < 64.0 && (double)m.getHealth() < (double)m.getMaxHealth() * 0.35)
                        .min(Comparator.comparingDouble(LivingEntity::getHealth))
                        .orElse(null);
                    if (weak != null) {
                        leader.setHealth(Math.max(1.0F, leader.getHealth() - 4.0F));
                        weak.heal((float)(4 + MobLevels.level(leader)));
                        weak.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 40, 0));
                        n.putLong("NextSupport", sl.getGameTime() + 100L);
                        n.putInt("Supports", n.getInt("Supports") + 1);
                        MobMind.practice(leader, "teamwork", 1);
                    }
                }
            }
        }
    }

    public static Vec3 formation(Mob m, LivingEntity target, double distance) {
        CompoundTag n = MobMind.data(m);
        if ((Boolean)RebornConfig.COOPERATION.get() && MobLevels.level(m) >= 3 && !(distance < 3.0) && !(distance > 20.0)) {
            String weapon = n.getString("Selected");
            boolean ranged = Set.of("bow", "crossbow", "trident", "gun", "magic").contains(weapon);
            Vec3 d = target.position().subtract(m.position()).normalize();
            double side = (double)(m.getId() % 2 == 0 ? 1 : -1);
            double width = ranged ? 5.0 : 2.0;
            Vec3 position = target.position().add(-d.z * width * side, 0.0, d.x * width * side);
            if (ranged) {
                position = position.subtract(d.scale(9.0));
            }

            Level sl = m.level();
            if (sl.hasChunkAt(BlockPos.containing(position))
                && sl.noCollision(m, m.getBoundingBox().move(position.subtract(m.position())))
                && !sl.getBlockState(BlockPos.containing(position).below()).isAir()) {
                n.putInt("FormationMoves", n.getInt("FormationMoves") + 1);
                return position;
            } else {
                return target.position();
            }
        } else {
            return target.position();
        }
    }

    private Teamplay() {
    }
}
