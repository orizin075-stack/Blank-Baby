package jp.oror.reborn;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.WeakHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.ClipContext.Block;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.HitResult.Type;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.common.util.BlockSnapshot;
import net.minecraftforge.event.level.BlockEvent.EntityPlaceEvent;

public final class TerrainPlay {
    private static final Map<ServerLevel, Map<Long, Long>> TEMPORARY = new WeakHashMap<>();

    private static void temporary(ServerLevel sl, BlockPos p, long until) {
        TEMPORARY.computeIfAbsent(sl, k -> new HashMap<>()).put(p.asLong(), until);
    }

    public static void cleanup(ServerLevel sl) {
        Map<Long, Long> placed = TEMPORARY.get(sl);
        if (placed != null && !placed.isEmpty() && sl.getGameTime() % 20L == 0L) {
            long now = sl.getGameTime();
            Iterator<Map.Entry<Long, Long>> it = placed.entrySet().iterator();

            while (it.hasNext()) {
                Map.Entry<Long, Long> entry = it.next();
                BlockPos p = BlockPos.of(entry.getKey());
                if (now >= entry.getValue() && sl.hasChunkAt(p)) {
                    BlockState state = sl.getBlockState(p);
                    if (state.is(Blocks.COBWEB) || state.is(Blocks.WATER) && sl.getFluidState(p).isSource()) {
                        sl.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                    }

                    it.remove();
                }
            }
        }
    }

    public static boolean place(Mob m, ServerLevel sl, BlockPos p, BlockState state) {
        if ((Boolean)RebornConfig.AI_TERRAIN.get()
            && sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)
            && sl.hasChunkAt(p)
            && sl.getWorldBorder().isWithinBounds(p)
            && sl.getBlockEntity(p) == null
            && sl.getBlockState(p).canBeReplaced()) {
            BlockState previous = sl.getBlockState(p);
            BlockSnapshot snapshot = BlockSnapshot.create(sl.dimension(), sl, p);
            if (!sl.setBlock(p, state, 3)) {
                return false;
            } else if (MinecraftForge.EVENT_BUS.post(new EntityPlaceEvent(snapshot, sl.getBlockState(p.below()), m))) {
                sl.setBlock(p, previous, 3);
                return false;
            } else {
                return true;
            }
        } else {
            return false;
        }
    }

    public static void fallRescue(Mob m, ServerLevel sl) {
        CompoundTag n = MobMind.data(m);
        long now = sl.getGameTime();
        if (n.contains("RescueWater") && now >= n.getLong("RescueCleanup")) {
            BlockPos p = BlockPos.of(n.getLong("RescueWater"));
            if (sl.hasChunkAt(p) && sl.getBlockState(p).is(Blocks.WATER) && sl.getFluidState(p).isSource()) {
                sl.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
            }

            n.remove("RescueWater");
        }

        if (MobLevels.level(m) >= 3
            && !m.onGround()
            && !m.isInWater()
            && !(m.fallDistance < 3.0F)
            && !(m.getDeltaMovement().y >= -0.1)
            && n.getLong("NextRescue") <= now) {
            Vec3 end = m.position().add(m.getDeltaMovement().x * 2.0, -6.0, m.getDeltaMovement().z * 2.0);
            BlockHitResult hit = sl.clip(new ClipContext(m.position(), end, Block.COLLIDER, Fluid.NONE, m));
            if (hit.getType() == Type.BLOCK && !(m.getY() - hit.getLocation().y > Math.max(3.0, Math.abs(m.getDeltaMovement().y) * 2.5))) {
                BlockPos at = hit.getBlockPos().above();
                boolean evaporates = sl.dimensionType().ultraWarm();
                if (place(m, sl, at, (evaporates ? Blocks.COBWEB : Blocks.WATER).defaultBlockState())) {
                    temporary(sl, at, now + 100L);
                    if (!evaporates) {
                        n.putLong("RescueWater", at.asLong());
                        n.putLong("RescueCleanup", now + 80L);
                    }

                    n.putLong("NextRescue", now + 80L);
                    n.putInt("LandingRescues", n.getInt("LandingRescues") + 1);
                    MobMind.practice(m, "terrain", 3);
                }
            }
        }
    }

    public static boolean bridge(Mob m, LivingEntity target, ServerLevel sl) {
        if (!AdaptiveCombat.guardian(m) && m.onGround() && MobLevels.level(m) >= 2 && !(m.distanceToSqr(target) < 9.0)) {
            CompoundTag n = MobMind.data(m);
            long now = sl.getGameTime();
            if (now < n.getLong("NextBridge")) {
                return false;
            } else {
                Vec3 toward = target.position().subtract(m.position());
                if (toward.horizontalDistanceSqr() < 1.0) {
                    return false;
                } else {
                    toward = new Vec3(toward.x, 0.0, toward.z).normalize();
                    BlockPos p = BlockPos.containing(m.position().add(toward.scale(1.2)).add(0.0, -0.2, 0.0));
                    if (!sl.getBlockState(p).isAir() || !sl.getFluidState(p).isEmpty()) {
                        return false;
                    } else if (place(m, sl, p, Blocks.COBBLESTONE.defaultBlockState())) {
                        n.putLong("NextBridge", now + (long)Math.max(8, 44 - MobLevels.level(m) * 6));
                        n.putInt("BridgeBlocks", n.getInt("BridgeBlocks") + 1);
                        MobMind.practice(m, "terrain", 2);
                        return true;
                    } else {
                        return false;
                    }
                }
            }
        } else {
            return false;
        }
    }

    private TerrainPlay() {
    }
}
