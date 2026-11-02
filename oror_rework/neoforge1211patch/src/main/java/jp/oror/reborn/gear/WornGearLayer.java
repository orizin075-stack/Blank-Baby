package jp.oror.reborn.gear;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.resources.PlayerSkin;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.client.event.RenderArmEvent;

/**
 * (052) The gear worn on the body, drawn there (WornGear): each piece is the item's worn model (its own 3D model at the
 * size it is worn, with what holds it on: tools/mc/w3worn.py), picked by the item model's override for
 * oror_supreme_bosses:worn, which is 1 only while this layer draws; the piece follows the part it hangs from (the chest,
 * the head, an arm), and its slot's render toggle hides it. The talon on the right hand is also seen in first person.
 */
public final class WornGearLayer<T extends LivingEntity, M extends HumanoidModel<T>> extends RenderLayer<T, M> {
    public static final ResourceLocation WORN = ResourceLocation.fromNamespaceAndPath(WornGear.NS, "worn");
    /** The item property oror_supreme_bosses:worn reads this: set only while a worn piece is drawn. */
    static boolean drawing;

    enum Part {
        BODY, HEAD, RIGHT_ARM, LEFT_ARM
    }

    record Piece(String id, Part part) {
    }

    static final Piece[] PIECES = {new Piece("rewind_talisman", Part.BODY), new Piece("villager_king_token", Part.BODY),
        new Piece("squad_banner", Part.BODY), new Piece("last_bloom", Part.HEAD), new Piece("parry_emblem", Part.LEFT_ARM),
        new Piece("dodge_talon", Part.RIGHT_ARM)};
    private static Item[] items;

    public WornGearLayer(RenderLayerParent<T, M> parent) {
        super(parent);
    }

    static Item[] items() {
        if (items == null) {
            items = new Item[PIECES.length];
            for (int i = 0; i < PIECES.length; i++) {
                items[i] = WornGear.item(PIECES[i].id());
            }
        }
        return items;
    }

    @Override
    public void render(PoseStack ps, MultiBufferSource buf, int light, T e, float limbSwing, float limbSwingAmount, float partial,
        float age, float headYaw, float headPitch) {
        if (!WornGear.CURIOS || e.isInvisible()) {
            return;
        }
        M model = this.getParentModel();
        boolean slim = e instanceof AbstractClientPlayer cp && cp.getSkin().model() == PlayerSkin.Model.SLIM;
        Item[] gear = items();
        for (int i = 0; i < PIECES.length; i++) {
            if (gear[i] == Items.AIR) {
                continue;
            }
            ItemStack s = WornGear.shown(e, gear[i]);
            if (s.isEmpty()) {
                continue;
            }
            Piece piece = PIECES[i];
            ModelPart part = switch (piece.part()) {
                case BODY -> model.body;
                case HEAD -> model.head;
                case RIGHT_ARM -> model.rightArm;
                case LEFT_ARM -> model.leftArm;
            };
            if (!part.visible && piece.part() != Part.BODY) {
                continue;
            }
            ps.pushPose();
            part.translateAndRotate(ps);
            draw(ps, buf, light, e, s, piece.part(), slim);
            ps.popPose();
        }
    }

    /** One piece, from the part's pivot: turned over about x (the model's up is up, its front is the wearer's front). */
    static void draw(PoseStack ps, MultiBufferSource buf, int light, LivingEntity e, ItemStack s, Part part, boolean slim) {
        if (slim && (part == Part.RIGHT_ARM || part == Part.LEFT_ARM)) {
            // the slim arm is three pixels wide, not four, its middle half a pixel nearer the body: the piece narrowed
            // about the arm's middle and moved with it
            float wide = part == Part.RIGHT_ARM ? -1F / 16F : 1F / 16F;
            ps.translate(wide / 2F, 0F, 0F);
            ps.scale(0.75F, 1F, 1F);
            ps.translate(-wide, 0F, 0F);
        }
        ps.mulPose(Axis.XP.rotationDegrees(180F));
        drawing = true;
        try {
            Minecraft.getInstance().getItemRenderer().renderStatic(e, s, ItemDisplayContext.NONE, false, ps, buf, e.level(), light,
                OverlayTexture.NO_OVERLAY, e.getId());
        } finally {
            drawing = false;
        }
    }

    /** The layer on the players' renderers, and the item property the worn models are picked by. */
    @EventBusSubscriber(modid = WornGear.NS, bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Setup {
        private Setup() {
        }

        @SubscribeEvent
        public static void layers(EntityRenderersEvent.AddLayers e) {
            for (PlayerSkin.Model skin : e.getSkins()) {
                EntityRenderer<? extends Player> r = e.getSkin(skin);
                if (r instanceof PlayerRenderer pr) {
                    pr.addLayer(new WornGearLayer<>(pr));
                }
            }
        }

        @SubscribeEvent
        public static void properties(FMLClientSetupEvent e) {
            e.enqueueWork(() -> {
                for (Piece piece : PIECES) {
                    Item it = WornGear.item(piece.id());
                    if (it != Items.AIR) {
                        ItemProperties.register(it, WORN, (stack, level, entity, seed) -> drawing ? 1F : 0F);
                    }
                }
            });
        }
    }

    /** First person: the talon on the bare right hand. */
    @EventBusSubscriber(modid = WornGear.NS, value = Dist.CLIENT)
    public static final class Hands {
        private Hands() {
        }

        @SubscribeEvent
        public static void arm(RenderArmEvent e) {
            AbstractClientPlayer p = e.getPlayer();
            if (!WornGear.CURIOS || e.getArm() != HumanoidArm.RIGHT) {
                return;
            }
            ItemStack s = WornGear.shown(p, items()[5]);
            if (s.isEmpty()) {
                return;
            }
            if (!(Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(p) instanceof PlayerRenderer pr)) {
                return;
            }
            // as PlayerRenderer.renderHand draws the arm: at its pivot, not swung, only its idle sway (0.1 about z)
            PlayerModel<AbstractClientPlayer> pm = pr.getModel();
            PoseStack ps = e.getPoseStack();
            ps.pushPose();
            ps.translate(pm.rightArm.x / 16F, pm.rightArm.y / 16F, pm.rightArm.z / 16F);
            ps.mulPose(Axis.ZP.rotation(0.1F));
            draw(ps, e.getMultiBufferSource(), e.getPackedLight(), p, s, Part.RIGHT_ARM,
                p.getSkin().model() == PlayerSkin.Model.SLIM);
            ps.popPose();
        }
    }
}
