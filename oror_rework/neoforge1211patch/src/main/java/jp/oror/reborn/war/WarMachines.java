package jp.oror.reborn.war;

import java.util.List;
import java.util.function.Consumer;
import jp.oror.reborn.vehicle.RoyalPilots;
import jp.oror.reborn.vehicle.Sbw;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/** The kingdom's tanks and aircraft in the hundred-man battle, crewed and driven by RoyalPilots. */
final class WarMachines {
    private static final String[] TANKS = {"m_1a_2", "t_90a", "ztz_99a"};
    private static final String[] PLANES = {"a_10a", "j_16"};

    private WarMachines() {
    }

    static boolean available() {
        return Sbw.present() && first(TANKS) != null;
    }

    private static String first(String[] ids) {
        for (String id : ids) {
            if (Sbw.has(id)) {
                return id;
            }
        }
        return null;
    }

    /** A crewed vehicle facing the enemy (south), at ground level. */
    static void deploy(ServerLevel level, Vec3 at, boolean air, int seats, Consumer<Mob> crew, Consumer<Entity> machine) {
        String id = air ? first(PLANES) : first(TANKS);
        if (id == null) {
            return;
        }
        BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.containing(at));
        Entity v = RoyalPilots.deploy(level, Vec3.atBottomCenterOf(top), 0F, id, seats, crew);
        if (v != null) {
            machine.accept(v);
        }
    }

    /** Ground vehicles fall back to the battlefield when there is nothing to fight, not to where they were unloaded. */
    static void command(Entity machine, Vec3 center, int field) {
        CompoundTag p = machine.getPersistentData().getCompound("OrorPilot");
        if (!"AIRCRAFT".equals(Sbw.engine(machine)) && machine.position().distanceToSqr(center) > field * field) {
            p.putLong("Home", BlockPos.containing(center).asLong());
            machine.getPersistentData().put("OrorPilot", p);
        }
    }

    static String report(List<Entity> machines) {
        StringBuilder b = new StringBuilder("[");
        for (Entity e : machines) {
            b.append(b.length() > 1 ? "," : "").append(RoyalPilots.report(e));
        }
        return b.append(']').toString();
    }
}
