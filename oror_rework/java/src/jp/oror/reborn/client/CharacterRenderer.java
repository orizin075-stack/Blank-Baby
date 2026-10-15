package jp.oror.reborn.client;

import com.mojang.blaze3d.vertex.PoseStack;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import jp.oror.reborn.CharacterSpec;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;

public final class CharacterRenderer extends MobRenderer<SupremeEntity, CharacterModel> {
    /** Nun and the Forbidden Arcana copy other beings; the copy keeps a tint of the shapeshifter. */
    private static final int MIMIC_TINT = 0xFF8A78A8;
    private final Map<String, CharacterModel> forms = new HashMap<>();

    public CharacterRenderer(Context ctx, CharacterSpec s) {
        super(ctx, new CharacterModel(s.id), s.width * 0.35F);
        this.forms.put(s.id, (CharacterModel)this.model);
        this.addLayer(new CharacterRenderer.Glow(this));
        this.addLayer(new MindHeldItems(this, ctx.getItemInHandRenderer(), true));
        if (s.id.equals("yggdrasil") && RigModel.has("yggdrasil_avatar")) {
            this.forms.put("avatar", new CharacterModel("yggdrasil_avatar"));
        }

        if (s.id.equals("nun") || s.id.equals("forbidden_arcana")) {
            for (String id : List.of("eomaia", "teia", "tenki")) {
                this.forms.put(id, new CharacterModel(id, MIMIC_TINT));
            }
        }
    }

    public ResourceLocation getTextureLocation(SupremeEntity e) {
        return ((CharacterModel)this.model).texture;
    }

    public void render(SupremeEntity e, float yaw, float tick, PoseStack ps, MultiBufferSource b, int light) {
        String key = e.spec.id;
        if (key.equals("yggdrasil") && e.form() == 1 && this.forms.containsKey("avatar")) {
            key = "avatar";
        }

        if (e.spec.id.equals("nun") || e.spec.id.equals("forbidden_arcana")) {
            key = switch (e.form()) {
                case 1 -> "eomaia";
                case 2 -> "teia";
                case 3 -> "tenki";
                default -> e.spec.id;
            };
        }

        this.model = this.forms.get(key);
        super.render(e, yaw, tick, ps, b, light);
    }

    protected RenderType getRenderType(SupremeEntity e, boolean visible, boolean translucent, boolean glowing) {
        return ((CharacterModel)this.model).translucent && visible
            ? RenderType.entityTranslucent(this.getTextureLocation(e))
            : super.getRenderType(e, visible, translucent, glowing);
    }

    protected void scale(SupremeEntity e, PoseStack ps, float tick) {
        float scale = e.getBbHeight() * 16.0F / ((CharacterModel)this.model).height;
        ps.scale(scale, scale, scale);
    }

    private static final class Glow extends RenderLayer<SupremeEntity, CharacterModel> {
        Glow(CharacterRenderer p) {
            super(p);
        }

        public void render(
            PoseStack ps, MultiBufferSource b, int light, SupremeEntity e, float limb, float amount, float tick, float age, float yaw, float pitch
        ) {
            CharacterModel model = (CharacterModel)this.getParentModel();
            model.renderGlow(ps, b.getBuffer(RenderType.eyes(model.glowTexture)), OverlayTexture.NO_OVERLAY);
        }
    }
}
