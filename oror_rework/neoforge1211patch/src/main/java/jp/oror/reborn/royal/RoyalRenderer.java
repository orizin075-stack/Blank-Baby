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

    /** (054) The villager king's four rigs (KingFormRenderer), or null to draw him on this model as before. */
    private final KingFormRenderer kingForms;

    public RoyalRenderer(Context context) {
        super(context, new RoyalModel(context.bakeLayer(LAYER)), 0.5F);
        this.addLayer(new ItemInHandLayer<>(this, context.getItemInHandRenderer()));
        this.kingForms = KingFormRenderer.create(context);
    }

    @Override
    public void render(RoyalMob mob, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
        if (mob.role() == RoyalRole.KING && this.kingForms != null) {
            this.shadowRadius = 0.9F * mob.getScale();
            this.kingForms.render(mob, yaw, partial, pose, buffers, light);
        } else {
            super.render(mob, yaw, partial, pose, buffers, light);
            // (059d) the casting roles' circles, light and sign (V20 07_royal_roles_8.md)
            try {
                RoyalRoleFx.render(mob, partial, pose, buffers);
            } catch (RuntimeException ignored) {
                // a frame without them
            }
        }
        if (mob.role() == RoyalRole.KING) {
            // (059) his field as a membrane of hexagons (ATFieldRenderer); the old light box only if that fails
            boolean drawn;
            try {
                drawn = ATFieldRenderer.render(mob, partial, pose, buffers);
            } catch (RuntimeException error) {
                drawn = false;
            }
            if (!drawn && mob.atField() > 0.0F && !mob.atBreached()) {
                double pulse = 0.04 * Math.sin((mob.tickCount + partial) * 0.12);
                double w = mob.getBbWidth() * 0.5 + 0.3 + pulse, hgt = mob.getBbHeight() + 0.3;
                LevelRenderer.renderLineBox(pose, buffers.getBuffer(RenderType.lines()), -w, -0.15, -w, w, hgt, w, 0.2F, 0.65F, 1.0F, 0.65F);
            }
        }
    }

    /** (054) The villager king's forms, one for each return from death (KingForms): their skins. */
    private static final ResourceLocation[] KING_FORMS = {
        ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/royal/villager_king_1.png"),
        ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/royal/villager_king_2.png"),
        ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/royal/villager_king_3.png")};

    @Override
    protected void scale(RoyalMob mob, PoseStack pose, float partial) {
        float size = switch (mob.role()) {
            // (054) the king grows with each return by his scale attribute (KingForms.strengthen), which the
            // living renderer applies itself
            case KING -> 1.12F;
            case GENERAL, BODYGUARD -> 1.06F;
            case IMPERIAL -> 1.04F;
            default -> 1.0F;
        };
        pose.scale(size, size, size);
    }

    @Override
    public ResourceLocation getTextureLocation(RoyalMob mob) {
        if (mob.role() == RoyalRole.KING && mob.lifePhase() > 0) {
            return KING_FORMS[Math.min(3, mob.lifePhase()) - 1];
        }
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
