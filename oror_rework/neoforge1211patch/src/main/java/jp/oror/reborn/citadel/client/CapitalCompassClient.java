package jp.oror.reborn.citadel.client;

import jp.oror.reborn.citadel.CapitalCompass;
import net.minecraft.client.renderer.item.CompassItemPropertyFunction;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.component.LodestoneTracker;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;

/**
 * (059f) The Royal Capital Compass's needle, turned as a lodestone compass's is (Minecraft's own compass angle, read
 * from the mark its holder's server set on it): its 32 drawings (models/item/capital_compass*.json) chosen by it.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class CapitalCompassClient {
    private CapitalCompassClient() {
    }

    @SubscribeEvent
    public static void setup(FMLClientSetupEvent event) {
        event.enqueueWork(() -> {
            if (CapitalCompass.COMPASS == null) {
                return;
            }
            ItemProperties.register(CapitalCompass.COMPASS, ResourceLocation.withDefaultNamespace("angle"),
                new CompassItemPropertyFunction((level, stack, entity) -> {
                    LodestoneTracker tracker = stack.get(DataComponents.LODESTONE_TRACKER);
                    return tracker == null ? null : tracker.target().orElse(null);
                }));
        });
    }
}
