package jp.oror.reborn.arms.sbw.client;

import com.atsuishio.superbwarfare.client.animation.AnimationHelper;
import com.atsuishio.superbwarfare.client.renderer.CustomGunRenderer;
import com.atsuishio.superbwarfare.item.gun.GunGeoItem;
import com.atsuishio.superbwarfare.item.gun.GunItem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.animatable.GeoAnimatable;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.cache.object.GeoBone;

/** Draws the player's arms on the Lefthand / Righthand bones and the muzzle flash on "flare", as Superb Warfare's do. */
public class OrorGunRenderer<T extends GunGeoItem & GeoAnimatable> extends CustomGunRenderer<T> {
    public OrorGunRenderer() {
        super(new OrorGunModel<>());
    }

    @Override
    public void renderRecursively(PoseStack poseStack, T animatable, GeoBone bone, RenderType renderType, MultiBufferSource bufferSource,
                                  VertexConsumer buffer, boolean isReRender, float partialTick, int packedLight, int packedOverlay, int colour) {
        String name = bone.getName();
        boolean arm = name.equals("Lefthand") || name.equals("Righthand");
        bone.setHidden(arm);
        LocalPlayer player = Minecraft.getInstance().player;
        if (player == null) {
            return;
        }
        ItemStack held = player.getMainHandItem();
        if (this.renderPerspective == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND && held.getItem() instanceof GunItem
            && GeoItem.getId(held) == this.getInstanceId(animatable)) {
            AnimationHelper.handleShootFlare(name, poseStack, held, bone, bufferSource, packedLight);
        }
        if (arm) {
            AnimationHelper.renderArms(player, this.renderPerspective, poseStack, name, bone, bufferSource, renderType, packedLight, false);
        }
        super.renderRecursively(poseStack, animatable, bone, renderType, bufferSource, buffer, isReRender, partialTick, packedLight, packedOverlay, colour);
    }
}
