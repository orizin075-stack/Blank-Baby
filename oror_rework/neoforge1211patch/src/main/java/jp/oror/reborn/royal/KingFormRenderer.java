package jp.oror.reborn.royal;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import jp.oror.reborn.client.RigModel;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * (054) The villager king drawn as one of his four rigs (KingLook, KingRig): the regal villager king, the hero, the
 * broken one, Baal Zebul. The rig is scaled to his hitbox (which grows with each form, KingForms.strengthen: the scale
 * attribute, applied by the living renderer itself). Its glowing parts are drawn again unlit (the rigs' _glow
 * texture). The regal king's guns are held in the rig's hands; the later forms hold their own modelled arms.
 * The broken king leaves afterimages a little off his body, more of them the more broken he is; the god is
 * drawn in his own light.
 */
public final class KingFormRenderer extends MobRenderer<RoyalMob, KingRig> {
    private final KingRig[] forms = new KingRig[4];
    private final ItemInHandRenderer items;
    private boolean ghost;

    private KingFormRenderer(Context context, KingRig first) {
        super(context, first, 0.9F);
        this.items = context.getItemInHandRenderer();
        this.forms[0] = first;
        for (int i = 1; i < 4; i++) {
            this.forms[i] = RigModel.has(KingLook.RIGS[i]) ? new KingRig(KingLook.RIGS[i]) : first;
        }
        this.addLayer(new Glow(this));
        this.addLayer(new Hands(this));
    }

    /** The renderer, or null when the king's rigs are not in the jar (RoyalRenderer then draws his old model). */
    public static KingFormRenderer create(Context context) {
        if (!RigModel.has(KingLook.RIGS[0])) {
            return null;
        }
        try {
            return new KingFormRenderer(context, new KingRig(KingLook.RIGS[0]));
        } catch (RuntimeException ex) {
            return null;
        }
    }

    @Override
    public void render(RoyalMob mob, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
        int form = KingLook.form(mob, partial);
        this.model = this.forms[form];
        this.shadowRadius = 0.9F * mob.getScale();
        if (form == 2) {
            float ruin = KingLook.ruin(mob);
            int h = KingLook.hash(mob.getId(), (int) (mob.level().getGameTime() / 2));
            int ghosts = 1 + (int) (ruin * 3);
            for (int g = 0; g < ghosts; g++) {
                int k = KingLook.hash(h, g);
                if (k % 3 == 0) {
                    continue;
                }
                pose.pushPose();
                pose.translate(((k >> 4) % 9 - 4) * 0.06 * (1 + ruin * 2), ((k >> 9) % 5 - 2) * 0.03, ((k >> 13) % 9 - 4) * 0.06 * (1 + ruin * 2));
                this.ghost = true;
                super.render(mob, yaw, partial, pose, buffers, light);
                this.ghost = false;
                pose.popPose();
            }
        }
        super.render(mob, yaw, partial, pose, buffers, form == 3 ? LightTexture.FULL_BRIGHT : light);
    }

    @Override
    protected boolean isBodyVisible(RoyalMob mob) {
        return !this.ghost && super.isBodyVisible(mob);
    }

    @Override
    protected boolean shouldShowName(RoyalMob mob) {
        return !this.ghost && super.shouldShowName(mob);
    }

    @Override
    public ResourceLocation getTextureLocation(RoyalMob mob) {
        return this.model.texture;
    }

    @Override
    protected RenderType getRenderType(RoyalMob mob, boolean visible, boolean translucent, boolean glowing) {
        if (visible && this.model.translucent) {
            return RenderType.entityTranslucent(this.getTextureLocation(mob));
        }
        return super.getRenderType(mob, visible, translucent, glowing);
    }

    @Override
    protected void scale(RoyalMob mob, PoseStack pose, float partial) {
        // the living renderer has already scaled by his scale attribute: fit the rig to his unscaled height
        float s = mob.getBbHeight() / Math.max(0.01F, mob.getScale()) * 16F / Math.max(1F, this.model.height);
        pose.scale(s, s, s);
    }

    /** The rig's glowing parts, unlit. */
    static final class Glow extends RenderLayer<RoyalMob, KingRig> {
        private final KingFormRenderer owner;

        Glow(KingFormRenderer parent) {
            super(parent);
            this.owner = parent;
        }

        @Override
        public void render(PoseStack pose, MultiBufferSource buffers, int light, RoyalMob mob, float swing, float amount, float partial,
                           float age, float yaw, float pitch) {
            KingRig m = this.getParentModel();
            if (m.glowTexture != null && !this.owner.ghost) {
                m.renderGlow(pose, buffers.getBuffer(RenderType.eyes(m.glowTexture)), OverlayTexture.NO_OVERLAY);
            }
        }
    }

    /** The regal king's held things (his guns, his sword) in the rig's hands; the later forms hold their own arms. */
    static final class Hands extends RenderLayer<RoyalMob, KingRig> {
        private final KingFormRenderer owner;

        Hands(KingFormRenderer parent) {
            super(parent);
            this.owner = parent;
        }

        @Override
        public void render(PoseStack pose, MultiBufferSource buffers, int light, RoyalMob mob, float swing, float amount, float partial,
                           float age, float yaw, float pitch) {
            if (this.getParentModel() != this.owner.forms[0] || this.owner.ghost) {
                return;
            }
            hand(pose, buffers, light, mob, mob.getMainHandItem(), true);
            hand(pose, buffers, light, mob, mob.getOffhandItem(), false);
        }

        private void hand(PoseStack pose, MultiBufferSource buffers, int light, RoyalMob mob, ItemStack stack, boolean right) {
            if (stack.isEmpty()) {
                return;
            }
            pose.pushPose();
            if (this.getParentModel().translateToHand(pose, right)) {
                pose.mulPose(Axis.XP.rotationDegrees(-90.0F));
                pose.mulPose(Axis.YP.rotationDegrees(180.0F));
                pose.translate((right ? 1F : -1F) / 16.0F, 0.125F, -0.125F);
                this.owner.items.renderItem(mob, stack, right ? ItemDisplayContext.THIRD_PERSON_RIGHT_HAND : ItemDisplayContext.THIRD_PERSON_LEFT_HAND,
                    !right, pose, buffers, light);
            }
            pose.popPose();
        }
    }
}
