package jp.oror.reborn.client;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import java.io.InputStream;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.AnimationUtils;
import net.minecraft.client.model.VillagerModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider.Context;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.VillagerRenderer;
import net.minecraft.client.renderer.entity.WanderingTraderRenderer;
import net.minecraft.client.renderer.entity.layers.CrossedArmsItemLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.WanderingTrader;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.MaceItem;
import net.minecraft.world.item.ProjectileWeaponItem;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.TridentItem;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.EventBusSubscriber.Bus;
import net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterLayerDefinitions;
import net.neoforged.neoforge.client.event.EntityRenderersEvent.RegisterRenderers;

/**
 * Villagers and wandering traders with a weapon or a tool in hand unfold their arms: two arms of their own (the sleeves
 * of their own texture, hands in their own skin colour) that hold the item and swing it when they strike. With nothing
 * in hand, or with goods to show, they stand with their arms folded as ever. The renderers stay the vanilla ones (and so
 * keep every layer other mods add to them), with the model and the hand-held item layers changed.
 */
public final class ArmedVillagers {
    static final ModelLayerLocation ARMS = new ModelLayerLocation(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "armed_villager"), "main");
    static final ModelLayerLocation HANDS = new ModelLayerLocation(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "armed_villager"), "hands");
    static final ResourceLocation HAND = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/villager/hand.png");
    private static final Map<ResourceLocation, Integer> SKIN = new ConcurrentHashMap<>();

    private ArmedVillagers() {
    }

    /** A weapon or a tool, something to hold up and swing; not goods offered for sale. */
    public static boolean armed(LivingEntity e) {
        ItemStack s = e.getMainHandItem();
        if (s.isEmpty()) {
            return false;
        }
        Object item = s.getItem();
        return item instanceof TieredItem || item instanceof TridentItem || item instanceof MaceItem || item instanceof ProjectileWeaponItem
            || item.getClass().getName().contains("GunItem");
    }

    static LayerDefinition arms() {
        MeshDefinition mesh = VillagerModel.createBodyModel();
        PartDefinition root = mesh.getRoot();
        // the upper arms are the folded arms' sleeves (the same texture), the hands come from HANDS
        root.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(44, 22).addBox(-3F, -2F, -2F, 4F, 8F, 4F), PartPose.offset(-5F, 2F, 0F));
        root.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(44, 22).mirror().addBox(-1F, -2F, -2F, 4F, 8F, 4F), PartPose.offset(5F, 2F, 0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    static LayerDefinition hands() {
        MeshDefinition mesh = new MeshDefinition();
        mesh.getRoot().addOrReplaceChild("right_hand", CubeListBuilder.create().texOffs(0, 0).addBox(-3F, 6F, -2F, 4F, 4F, 4F), PartPose.ZERO);
        mesh.getRoot().addOrReplaceChild("left_hand", CubeListBuilder.create().texOffs(0, 0).mirror().addBox(-1F, 6F, -2F, 4F, 4F, 4F), PartPose.ZERO);
        return LayerDefinition.create(mesh, 16, 16);
    }

    /** The skin colour of a villager texture (the cheeks of its face), ARGB. */
    static int skin(ResourceLocation texture) {
        return SKIN.computeIfAbsent(texture, t -> {
            try (InputStream in = Minecraft.getInstance().getResourceManager().open(t); NativeImage img = NativeImage.read(in)) {
                long r = 0, g = 0, b = 0, n = 0;
                for (int[] p : new int[][]{{9, 14}, {14, 14}, {9, 15}, {14, 15}}) {
                    int abgr = img.getPixelRGBA(p[0], p[1]);
                    if ((abgr >>> 24) > 128) {
                        r += abgr & 255;
                        g += (abgr >> 8) & 255;
                        b += (abgr >> 16) & 255;
                        n++;
                    }
                }
                return n == 0 ? 0xFFB98A6A : 0xFF000000 | (int) (r / n) << 16 | (int) (g / n) << 8 | (int) (b / n);
            } catch (Exception e) {
                return 0xFFB98A6A;
            }
        });
    }

    /** The villager model with two arms of its own beside the folded ones; which are shown follows armed(). */
    public static final class Model<T extends LivingEntity> extends VillagerModel<T> {
        final ModelPart arms, body, rightArm, leftArm;

        public Model(ModelPart root) {
            super(root);
            this.arms = root.getChild("arms");
            this.body = root.getChild("body");
            this.rightArm = root.getChild("right_arm");
            this.leftArm = root.getChild("left_arm");
        }

        @Override
        public void setupAnim(T e, float walk, float amount, float age, float yaw, float pitch) {
            super.setupAnim(e, walk, amount, age, yaw, pitch);
            boolean armed = armed(e);
            this.arms.visible = !armed;
            this.rightArm.visible = this.leftArm.visible = armed;
            this.body.yRot = 0F;
            if (!armed) {
                return;
            }
            float stride = walk * 0.6662F;
            this.rightArm.x = -5F;
            this.rightArm.z = 0F;
            this.leftArm.x = 5F;
            this.leftArm.z = 0F;
            this.rightArm.xRot = Mth.cos(stride + Mth.PI) * amount - Mth.PI / 10F;
            this.leftArm.xRot = Mth.cos(stride) * amount;
            this.rightArm.yRot = this.leftArm.yRot = 0F;
            this.rightArm.zRot = this.leftArm.zRot = 0F;
            AnimationUtils.bobArms(this.rightArm, this.leftArm, age);
            if (this.attackTime > 0F) {
                float t = this.attackTime;
                this.body.yRot = Mth.sin(Mth.sqrt(t) * Mth.TWO_PI) * 0.2F;
                this.rightArm.z = Mth.sin(this.body.yRot) * 5F;
                this.rightArm.x = -Mth.cos(this.body.yRot) * 5F;
                this.leftArm.z = -Mth.sin(this.body.yRot) * 5F;
                this.leftArm.x = Mth.cos(this.body.yRot) * 5F;
                this.rightArm.yRot += this.body.yRot;
                this.leftArm.yRot += this.body.yRot;
                this.leftArm.xRot += this.body.yRot;
                float f = 1F - t;
                f *= f;
                f *= f;
                f = 1F - f;
                this.rightArm.xRot -= Mth.sin(f * Mth.PI) * 1.2F + Mth.sin(t * Mth.PI) * -(this.getHead().xRot - 0.7F) * 0.75F;
                this.rightArm.yRot += this.body.yRot * 2F;
                this.rightArm.zRot += Mth.sin(t * Mth.PI) * -0.4F;
            }
        }

        void toHand(HumanoidArm side, PoseStack pose) {
            this.root().translateAndRotate(pose);
            (side == HumanoidArm.LEFT ? this.leftArm : this.rightArm).translateAndRotate(pose);
        }
    }

    /** The folded arms' item, only while the arms are folded. */
    static final class Folded<T extends LivingEntity> extends RenderLayer<T, VillagerModel<T>> {
        private final CrossedArmsItemLayer<T, VillagerModel<T>> inner;

        Folded(RenderLayerParent<T, VillagerModel<T>> parent, ItemInHandRenderer items) {
            super(parent);
            this.inner = new CrossedArmsItemLayer<>(parent, items);
        }

        @Override
        public void render(PoseStack pose, MultiBufferSource buffers, int light, T e, float walk, float amount, float partial, float age, float yaw, float pitch) {
            if (!armed(e)) {
                this.inner.render(pose, buffers, light, e, walk, amount, partial, age, yaw, pitch);
            }
        }
    }

    /** With the arms unfolded: the hands in the villager's skin colour and what they hold. */
    static final class Hands<T extends LivingEntity> extends RenderLayer<T, VillagerModel<T>> {
        private final ItemInHandRenderer items;
        private final ModelPart rightHand, leftHand;
        private final java.util.function.Function<T, ResourceLocation> texture;

        Hands(RenderLayerParent<T, VillagerModel<T>> parent, Context context, java.util.function.Function<T, ResourceLocation> texture) {
            super(parent);
            this.items = context.getItemInHandRenderer();
            ModelPart hands = context.bakeLayer(HANDS);
            this.rightHand = hands.getChild("right_hand");
            this.leftHand = hands.getChild("left_hand");
            this.texture = texture;
        }

        @Override
        public void render(PoseStack pose, MultiBufferSource buffers, int light, T e, float walk, float amount, float partial, float age, float yaw, float pitch) {
            if (!armed(e) || !(this.getParentModel() instanceof Model<T> model)) {
                return;
            }
            int colour = skin(this.texture.apply(e));
            int overlay = LivingEntityRenderer.getOverlayCoords(e, 0F);
            for (HumanoidArm side : HumanoidArm.values()) {
                pose.pushPose();
                model.toHand(side, pose);
                (side == HumanoidArm.LEFT ? this.leftHand : this.rightHand)
                    .render(pose, buffers.getBuffer(RenderType.entityCutoutNoCull(HAND)), light, overlay, colour);
                pose.popPose();
                ItemStack stack = side == e.getMainArm() ? e.getMainHandItem() : e.getOffhandItem();
                if (!stack.isEmpty()) {
                    pose.pushPose();
                    model.toHand(side, pose);
                    pose.mulPose(Axis.XP.rotationDegrees(-90F));
                    pose.mulPose(Axis.YP.rotationDegrees(180F));
                    boolean left = side == HumanoidArm.LEFT;
                    pose.translate((left ? -1F : 1F) / 16F, 0.125F, -0.625F);
                    this.items.renderItem(e, stack, left ? ItemDisplayContext.THIRD_PERSON_LEFT_HAND : ItemDisplayContext.THIRD_PERSON_RIGHT_HAND,
                        left, pose, buffers, light);
                    pose.popPose();
                }
            }
        }
    }

    public static final class VillagerArmed extends VillagerRenderer {
        public VillagerArmed(Context context) {
            super(context);
            this.model = new Model<>(context.bakeLayer(ARMS));
            this.layers.removeIf(l -> l instanceof CrossedArmsItemLayer);
            this.addLayer(new Folded<>(this, context.getItemInHandRenderer()));
            this.addLayer(new Hands<>(this, context, this::getTextureLocation));
        }
    }

    public static final class TraderArmed extends WanderingTraderRenderer {
        public TraderArmed(Context context) {
            super(context);
            this.model = new Model<>(context.bakeLayer(ARMS));
            this.layers.removeIf(l -> l instanceof CrossedArmsItemLayer);
            this.addLayer(new Folded<>(this, context.getItemInHandRenderer()));
            this.addLayer(new Hands<>(this, context, this::getTextureLocation));
        }
    }

    /**
     * The swing's clock. Minecraft runs it only for monsters and players (Monster.aiStep, Player.aiStep), so a villager,
     * a trader or a royal told to swing (the server's swing packet) would never move its arm. For those, when a tick went
     * by with the swing started but its clock not advanced, it is advanced here exactly as LivingEntity.updateSwingTime.
     */
    @EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
    public static final class SwingClock {
        private static final Map<LivingEntity, Integer> BEFORE = new java.util.WeakHashMap<>();

        static boolean ours(net.minecraft.world.entity.Entity e) {
            return e instanceof net.minecraft.world.entity.npc.AbstractVillager || e instanceof jp.oror.reborn.royal.RoyalMob;
        }

        @SubscribeEvent
        public static void before(net.neoforged.neoforge.event.tick.EntityTickEvent.Pre e) {
            if (e.getEntity().level().isClientSide && ours(e.getEntity()) && e.getEntity() instanceof LivingEntity l) {
                BEFORE.put(l, l.swinging ? l.swingTime : Integer.MIN_VALUE);
            }
        }

        @SubscribeEvent
        public static void after(net.neoforged.neoforge.event.tick.EntityTickEvent.Post e) {
            if (!e.getEntity().level().isClientSide || !ours(e.getEntity()) || !(e.getEntity() instanceof LivingEntity l)) {
                return;
            }
            Integer before = BEFORE.remove(l);
            if (!l.swinging || before == null || before != l.swingTime && before != Integer.MIN_VALUE) {
                if (!l.swinging && l.attackAnim > 0F && before != null && before == Integer.MIN_VALUE) {
                    l.attackAnim = 0F;
                }
                return;
            }
            int duration = 6;
            l.swingTime++;
            if (l.swingTime >= duration) {
                l.swingTime = 0;
                l.swinging = false;
            }
            l.attackAnim = (float) l.swingTime / duration;
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = Bus.MOD, value = Dist.CLIENT)
    public static final class Client {
        @SubscribeEvent
        public static void layers(RegisterLayerDefinitions event) {
            event.registerLayerDefinition(ARMS, ArmedVillagers::arms);
            event.registerLayerDefinition(HANDS, ArmedVillagers::hands);
        }

        @SubscribeEvent
        public static void renderers(RegisterRenderers event) {
            event.registerEntityRenderer(EntityType.VILLAGER, VillagerArmed::new);
            event.registerEntityRenderer(EntityType.WANDERING_TRADER, TraderArmed::new);
        }
    }
}
