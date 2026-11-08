package jp.oror.reborn.royal;

import com.mojang.blaze3d.vertex.PoseStack;
import jp.oror.reborn.client.RigModel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.culling.Frustum;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.EvokerRenderer;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Evoker;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers;

/**
 * (056) Azazel drawn as himself (AzazelRig), not as the evoker he is: the evokers' renderer is replaced by one that draws
 * Azazel and his likeness (an evoker whose name is his, RebelLord.makeLord) with his rig, and every other evoker as
 * Minecraft draws it.
 */
public final class AzazelRenderer extends MobRenderer<Evoker, AzazelRig> {
    private AzazelRenderer(Context context) {
        super(context, new AzazelRig(), 0.7F);
        this.addLayer(new Glow(this));
    }

    static AzazelRenderer create(Context context) {
        if (!RigModel.has("azazel")) {
            return null;
        }
        try {
            return new AzazelRenderer(context);
        } catch (RuntimeException ex) {
            return null;
        }
    }

    /** Azazel or his likeness: an evoker bearing his name (names are seen by every client). */
    static boolean isAzazel(Evoker e) {
        Component n = e.getCustomName();
        return n != null && n.getString().contains("アザゼル");
    }

    @Override
    public ResourceLocation getTextureLocation(Evoker e) {
        return this.model.texture;
    }

    @Override
    protected RenderType getRenderType(Evoker e, boolean visible, boolean translucent, boolean glowing) {
        if (visible && this.model.translucent) {
            return RenderType.entityTranslucent(this.getTextureLocation(e));
        }
        return super.getRenderType(e, visible, translucent, glowing);
    }

    @Override
    protected void scale(Evoker e, PoseStack pose, float partial) {
        // the living renderer has scaled by his scale attribute already: fit the rig to his unscaled height
        float s = e.getBbHeight() / Math.max(0.01F, e.getScale()) * 16F / Math.max(1F, this.model.height);
        pose.scale(s, s, s);
    }

    /** The rig's glowing parts (his eyes, the forge-fire of his blade and his feathers' edges), unlit. */
    static final class Glow extends RenderLayer<Evoker, AzazelRig> {
        Glow(RenderLayerParent<Evoker, AzazelRig> parent) {
            super(parent);
        }

        @Override
        public void render(PoseStack pose, MultiBufferSource buffers, int light, Evoker e, float swing, float amount, float partial, float age,
                           float yaw, float pitch) {
            AzazelRig m = this.getParentModel();
            if (m.glowTexture != null) {
                m.renderGlow(pose, buffers.getBuffer(RenderType.eyes(m.glowTexture)), OverlayTexture.NO_OVERLAY);
            }
        }
    }

    /** The evokers' renderer: Azazel by his rig, the rest as ever. */
    public static final class Evokers extends EntityRenderer<Evoker> {
        private final EvokerRenderer<Evoker> plain;
        private final AzazelRenderer azazel;

        public Evokers(Context context) {
            super(context);
            this.plain = new EvokerRenderer<>(context);
            this.azazel = create(context);
            this.shadowRadius = 0.5F;
        }

        private EntityRenderer<Evoker> pick(Evoker e) {
            return this.azazel != null && isAzazel(e) ? this.azazel : this.plain;
        }

        @Override
        public void render(Evoker e, float yaw, float partial, PoseStack pose, MultiBufferSource buffers, int light) {
            this.pick(e).render(e, yaw, partial, pose, buffers, light);
        }

        @Override
        public boolean shouldRender(Evoker e, Frustum frustum, double x, double y, double z) {
            return this.pick(e).shouldRender(e, frustum, x, y, z);
        }

        @Override
        public ResourceLocation getTextureLocation(Evoker e) {
            return this.pick(e).getTextureLocation(e);
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Client {
        private Client() {
        }

        @SubscribeEvent
        public static void renderers(RegisterRenderers event) {
            event.registerEntityRenderer(EntityType.EVOKER, Evokers::new);
        }
    }
}
