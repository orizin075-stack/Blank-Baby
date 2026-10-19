package jp.oror.reborn;

import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.levelgen.Heightmap.Types;

public final class EncounterRules {
    public static final Set<String> WANDERERS = Set.of(
        "riha",
        "ferdinand",
        "mels",
        "mary_sue",
        "savior",
        "merlinus",
        "teia",
        "bahamut",
        "nun",
        "arcana",
        "shinra",
        "angra_mainyu",
        "innocence",
        "fallen_savior"
    );

    public static boolean dungeon(String id) {
        return !WANDERERS.contains(id) && !id.equals("sweet_pact");
    }

    public static boolean pactEligible(ServerPlayer p) {
        return p.isAlive()
            && !p.isCreative()
            && !p.isSpectator()
            && p.getHealth() <= p.getMaxHealth() * 0.35F
            && p.level().getGameTime() >= p.getPersistentData().getLong("ororPactNextVisit");
    }

    public static SupremeEntity spawn(ServerLevel sl, String id, BlockPos center, int radius) {
        CharacterSpec spec = CharacterSpec.ALL.get(id);

        for (int i = 0; i < 8; i++) {
            int x = center.getX() + sl.random.nextInt(radius * 2 + 1) - radius;
            int z = center.getZ() + sl.random.nextInt(radius * 2 + 1) - radius;
            BlockPos at = new BlockPos(x, center.getY(), z);
            if (sl.hasChunkAt(at) && sl.getWorldBorder().isWithinBounds(at)) {
                int y = id.equals("sweet_pact") ? center.getY() : sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, x, z);
                if (spec.aquatic()) {
                    if (sl.getFluidState(new BlockPos(x, y - 1, z)).isEmpty()) {
                        continue;
                    }

                    y -= 2;
                } else if (spec.airborne()) {
                    y += 4;
                }

                SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(sl);
                if (b == null) {
                    return null;
                }

                b.moveTo((double)x + 0.5, (double)y, (double)z + 0.5, 0.0F, 0.0F);
                if (sl.noCollision(b) && (spec.aquatic() || sl.getFluidState(b.blockPosition()).isEmpty())) {
                    sl.addFreshEntity(b);
                    return b;
                }
            }
        }

        return null;
    }

    public static void special(ServerLevel sl) {
        if (sl.getGameTime() % 100L == 0L) {
            for (ServerPlayer p : sl.players()) {
                if (pactEligible(p)
                    && sl.getEntitiesOfClass(SupremeEntity.class, p.getBoundingBox().inflate(48.0), b -> b.spec.id.equals("sweet_pact")).isEmpty()
                    && spawn(sl, "sweet_pact", p.blockPosition(), 6) != null) {
                    p.getPersistentData().putLong("ororPactNextVisit", sl.getGameTime() + 24000L);
                }
            }
        }
    }
}
