package jp.oror.reborn.arms.sbw.client;

import com.atsuishio.superbwarfare.client.animation.AnimationHelper;
import com.atsuishio.superbwarfare.client.model.item.CustomGunModel;
import com.atsuishio.superbwarfare.event.ClientEventHandler;
import com.atsuishio.superbwarfare.item.gun.GunGeoItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import software.bernie.geckolib.animatable.GeoAnimatable;
import software.bernie.geckolib.animation.AnimationState;
import software.bernie.geckolib.cache.object.GeoBone;

/**
 * First-person motion for the OROR guns, on the skeleton they share with Superb Warfare's Sentinel: aiming brings the
 * scope (centred at x -0.36, y 4.82) in front of the eye with the Sentinel's offsets, plus Superb Warfare's own recoil,
 * sway and reload shake.
 */
public class OrorGunModel<T extends GunGeoItem & GeoAnimatable> extends CustomGunModel<T> {
    @Override
    public void setCustomAnimations(T animatable, long instanceId, AnimationState<T> animationState) {
        Player player = Minecraft.getInstance().player;
        if (player == null) {
            return;
        }
        ItemStack stack = player.getMainHandItem();
        if (shouldCancelRender(stack, animationState)) {
            return;
        }
        GeoBone gun = getAnimationProcessor().getBone("bone");
        GeoBone shen = getAnimationProcessor().getBone("shen");
        GeoBone camera = getAnimationProcessor().getBone("camera");
        GeoBone main = getAnimationProcessor().getBone("0");
        if (gun == null || shen == null || camera == null || main == null) {
            return;
        }
        double zt = ClientEventHandler.zoomTime;
        double zp = ClientEventHandler.zoomPos;
        double zpz = ClientEventHandler.zoomPosZ;
        gun.setPosX(2.928F * (float) zp);
        gun.setPosY(-0.062F * (float) zp - (float) (0.1F * zpz));
        gun.setPosZ(10.0F * (float) zp + (float) (0.3F * zpz));
        gun.setRotZ((float) (0.05F * zpz));
        gun.setScaleZ(1.0F - 0.7F * (float) zp);
        ClientEventHandler.handleShootAnimation(shen, 1.25F, 2.0F, 3.0F, 2.5F, 1.3F, 1.0F, 0.4F, 0.55F);
        ClientEventHandler.gunRootMove(getAnimationProcessor(), 0.0F, 0.0F, 0.0F, false);
        float numR = (float) (1.0 - 0.9 * zt);
        float numP = (float) (1.0 - 0.98 * zt);
        AnimationHelper.handleReloadShakeAnimation(stack, main, camera, numR, numP);
        ClientEventHandler.handleReloadShake(Math.toDegrees(camera.getRotX()), Math.toDegrees(camera.getRotY()), Math.toDegrees(camera.getRotZ()));
    }
}
