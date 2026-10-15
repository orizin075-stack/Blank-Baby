package jp.oror.reborn.client;

import jp.oror.reborn.FamiliarEntity;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;

public final class FamiliarRenderer extends MobRenderer<FamiliarEntity, FamiliarRenderer.Model> {
    private static final String[] STYLES = {"familiar_drone", "familiar_beast", "familiar_sprite", "familiar_curse"};
    private final FamiliarRenderer.Model[] models = new FamiliarRenderer.Model[STYLES.length];

    public FamiliarRenderer(Context c) {
        super(c, new FamiliarRenderer.Model(STYLES[0]), 0.3F);
        this.models[0] = this.model;

        for (int i = 1; i < STYLES.length; i++) {
            this.models[i] = new FamiliarRenderer.Model(STYLES[i]);
        }

        this.addLayer(new FamiliarRenderer.Glow(this));
    }

    public ResourceLocation getTextureLocation(FamiliarEntity e) {
        return this.model.texture;
    }

    public void render(FamiliarEntity e, float yaw, float tick, PoseStack ps, MultiBufferSource b, int light) {
        this.model = this.models[Math.floorMod(e.style(), this.models.length)];
        super.render(e, yaw, tick, ps, b, light);
    }

    protected void scale(FamiliarEntity e, PoseStack ps, float tick) {
        float scale = e.getBbHeight() * 16.0F / this.model.height;
        ps.scale(scale, scale, scale);
    }

    static final class Model extends RigModel<FamiliarEntity> {
        Model(String key) {
            super(key, -1);
        }

        public void setupAnim(FamiliarEntity e, float swing, float amount, float age, float yaw, float pitch) {
            this.animate(e, swing, amount, age, yaw, pitch, 0, 0.0F, e.getTarget() == null ? 0 : 1, e.style());
        }
    }

    private static final class Glow extends RenderLayer<FamiliarEntity, FamiliarRenderer.Model> {
        Glow(FamiliarRenderer p) {
            super(p);
        }

        public void render(
            PoseStack ps, MultiBufferSource b, int light, FamiliarEntity e, float limb, float amount, float tick, float age, float yaw, float pitch
        ) {
            FamiliarRenderer.Model model = this.getParentModel();
            model.renderGlow(ps, b.getBuffer(RenderType.eyes(model.glowTexture)), OverlayTexture.NO_OVERLAY);
        }
    }
}
