package jp.oror.reborn.perf;

import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.level.block.Fallable;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;

/**
 * Explosions break blocks, and the blocks are gone (051, the user's report: leaves stuck into the runway). The pack's
 * shells and rockets throw what they break about as falling blocks: leaves, earth, logs, crops that never fall by
 * themselves flew over the capital and set themselves down wherever they came to rest, on the runways and the fields,
 * and the more guns the kingdom had, the more of them. A falling block of anything that does not fall of itself (not
 * sand, gravel, an anvil, concrete powder and the like) is such debris and does not come into the world; the block it
 * was broken from stays broken.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class DebrisGuard {
    public static int stopped;

    private DebrisGuard() {
    }

    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        if (e.getLevel().isClientSide() || !(e.getEntity() instanceof FallingBlockEntity fb)) {
            return;
        }
        if (!(fb.getBlockState().getBlock() instanceof Fallable)) {
            e.setCanceled(true);
            stopped++;
        }
    }
}
