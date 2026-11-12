package jp.oror.reborn.duel.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import jp.oror.reborn.duel.GrimoireBook;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.extensions.common.IClientItemExtensions;
import net.neoforged.neoforge.client.extensions.common.RegisterClientExtensionsEvent;

/**
 * (059e) The reading pose of the dominion grimoire ({@link GrimoireBook}), seen by everyone: while it is read (in use,
 * its screen open) the reader holds it up before him in both hands (the two-handed hold), it is drawn open in his
 * hands (the item property oror_supreme_bosses:reading, read by its model's override: dominion_grimoire_open), and in
 * his own view it rises to the middle, tilted toward his eyes. Without Duel Dominion nothing is registered.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class GrimoireClient {
    public static final ResourceLocation READING = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "reading");

    private GrimoireClient() {
    }

    private static Item grimoire() {
        Item it = BuiltInRegistries.ITEM.get(GrimoireBook.GRIMOIRE);
        return it == Items.AIR ? null : it;
    }

    static boolean reading(LivingEntity e, ItemStack stack) {
        return e != null && e.isUsingItem() && e.getUseItem() == stack;
    }

    @SubscribeEvent
    public static void setup(FMLClientSetupEvent e) {
        e.enqueueWork(() -> {
            Item book = grimoire();
            if (book != null) {
                ItemProperties.register(book, READING, (stack, level, entity, seed) -> reading(entity, stack) ? 1F : 0F);
            }
        });
    }

    @SubscribeEvent
    public static void extensions(RegisterClientExtensionsEvent e) {
        Item book = grimoire();
        if (book == null) {
            return;
        }
        e.registerItem(new IClientItemExtensions() {
            @Override
            public HumanoidModel.ArmPose getArmPose(LivingEntity entity, InteractionHand hand, ItemStack stack) {
                return reading(entity, stack) ? HumanoidModel.ArmPose.CROSSBOW_HOLD : null;
            }

            @Override
            public boolean applyForgeHandTransform(PoseStack pose, LocalPlayer player, HumanoidArm arm, ItemStack stack, float partialTick,
                                                   float equipProcess, float swingProcess) {
                if (!reading(player, stack)) {
                    return false;
                }
                int side = arm == HumanoidArm.RIGHT ? 1 : -1;
                pose.translate(side * 0.12F, -0.32F + equipProcess * -0.6F, -0.62F);
                pose.mulPose(Axis.XP.rotationDegrees(-18F));
                pose.mulPose(Axis.YP.rotationDegrees(side * -12F));
                return true;
            }
        }, book);
    }
}
