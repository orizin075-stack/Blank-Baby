package jp.oror.reborn.royal;

import com.mojang.blaze3d.vertex.PoseStack;
import java.util.EnumMap;
import java.util.Map;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.LevelRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.ItemInHandLayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.EventBusSubscriber.Bus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterLayerDefinitions;
import net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers;

/**
 * The royals: each role in its own clothes (textures/entity/royal/<role>.png, painted by tools/royal_skins.py) on
 * RoyalModel, the weapons in their hands; the king a little taller than his court, inside his field's light box while
 * it holds.
 */
public final class RoyalRenderer extends MobRenderer<RoyalMob, RoyalModel> {
    static final ModelLayerLocation LAYER = new ModelLayerLocation(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "royal"), "main");
    private static final Map<RoyalRole, ResourceLocation> SKINS = new EnumMap<>(RoyalRole.class);

    static {
        for (RoyalRole role : RoyalRole.values()) {
            SKINS.put(role, ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/royal/" + role.id + ".png"));
        }
    }

    public RoyalRenderer(Context context) {
        super(context, new RoyalModel(context.bakeLayer(LAYER)), 0.5F);
        this.addLayer(new ItemInHandLayer<>(this, context.getItemInHandRenderer()));
    }

    @Override
    public void render(RoyalMob mob, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
        super.render(mob, yaw, partial, pose, buffers, light);
        if (mob.role() == RoyalRole.KING && mob.atField() > 0.0F && !mob.atBreached()) {
            double pulse = 0.04 * Math.sin((mob.tickCount + partial) * 0.12);
            LevelRenderer.renderLineBox(pose, buffers.getBuffer(RenderType.lines()), -0.85 - pulse, -0.15, -0.85 - pulse, 0.85 + pulse, 2.5,
                0.85 + pulse, 0.2F, 0.65F, 1.0F, 0.65F);
        }
    }

    @Override
    protected void scale(RoyalMob mob, PoseStack pose, float partial) {
        float size = switch (mob.role()) {
            case KING -> 1.12F;
            case GENERAL, BODYGUARD -> 1.06F;
            case IMPERIAL -> 1.04F;
            default -> 1.0F;
        };
        pose.scale(size, size, size);
    }

    @Override
    public ResourceLocation getTextureLocation(RoyalMob mob) {
        return SKINS.get(mob.role());
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = Bus.MOD, value = Dist.CLIENT)
    public static class Client {
        @SubscribeEvent
        public static void layers(RegisterLayerDefinitions event) {
            event.registerLayerDefinition(LAYER, RoyalModel::createLayer);
        }

        @SubscribeEvent
        public static void renderers(RegisterRenderers event) {
            for (EntityType<RoyalMob> type : RoyalRegistry.TYPES.values()) {
                event.registerEntityRenderer(type, RoyalRenderer::new);
            }
        }
    }
}
