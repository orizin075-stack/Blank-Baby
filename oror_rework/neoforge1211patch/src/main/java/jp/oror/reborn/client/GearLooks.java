package jp.oror.reborn.client;

import jp.oror.reborn.NightfallArsenal;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;

/**
 * (052) The Nightfall gear seen as it is used and as it recharges, by its cooldown (the item property
 * oror_supreme_bosses:state, read by the item models' overrides): 1 while it is at work (the parry emblem's window, the
 * dodge talon's dash, the squad banner's rally: the first part of its recharge), 0.5 while it recharges (drained of
 * colour; the last bloom closed in a bud until it can bloom again), 0 when it is ready.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class GearLooks {
    public static final ResourceLocation STATE = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "state");

    private GearLooks() {
    }

    @SubscribeEvent
    public static void setup(FMLClientSetupEvent e) {
        e.enqueueWork(() -> {
            // the parry window is a second of the emblem's five-second recharge, the dash half a second of three, the
            // rally a second and a half of thirty; the last bloom has no moment at work, only its long recharge
            register(NightfallArsenal.PARRY.get(), 0.8F);
            register(NightfallArsenal.DODGE.get(), 0.83F);
            register(NightfallArsenal.BANNER.get(), 0.95F);
            register(NightfallArsenal.BLOOM.get(), 2F);
        });
    }

    private static void register(Item item, float atWork) {
        ItemProperties.register(item, STATE, (stack, level, entity, seed) -> {
            LivingEntity who = entity != null ? entity : Minecraft.getInstance().player;
            if (!(who instanceof Player p)) {
                return 0F;
            }
            float left = p.getCooldowns().getCooldownPercent(stack.getItem(), 0F);
            return left <= 0F ? 0F : left > atWork ? 1F : 0.5F;
        });
    }
}
