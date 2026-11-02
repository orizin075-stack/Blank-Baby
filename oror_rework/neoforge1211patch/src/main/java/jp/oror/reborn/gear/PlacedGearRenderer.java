package jp.oror.reborn.gear;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;

/**
 * (052) Gear set down (PlacedGear) drawn as its 3D model stood on the floor: each model's scale and the offsets that put
 * its foot on the ground and its middle over the spot (from its OBJ, tools/mc/w3gear.py), turned to face whoever set it
 * down; the armillary turns slowly.
 */
public final class PlacedGearRenderer extends EntityRenderer<PlacedGear> {
    /** scale, the model's lowest y, its centre x and z (item model space, blocks). */
    private static final Map<String, float[]> STAND = Map.ofEntries(Map.entry("squad_banner", new float[]{1.2690F, 0.1875F, 0.5000F, 0.5000F}),
        Map.entry("dragon_core", new float[]{1.4610F, 0.2500F, 0.5000F, 0.5000F}),
        Map.entry("star_shard", new float[]{1.1422F, 0.2500F, 0.5106F, 0.5000F}),
        Map.entry("forge_core", new float[]{1.2409F, 0.1875F, 0.5000F, 0.5000F}),
        Map.entry("omniregistry_treasure", new float[]{1.1393F, 0.0938F, 0.5156F, 0.4844F}));
    private final ItemRenderer items;

    public PlacedGearRenderer(EntityRendererProvider.Context ctx) {
        super(ctx);
        this.items = ctx.getItemRenderer();
        this.shadowRadius = 0.3F;
    }

    @Override
    public void render(PlacedGear e, float yaw, float partial, PoseStack ps, MultiBufferSource buf, int light) {
        ItemStack s = e.item();
        if (!s.isEmpty()) {
            float[] st = STAND.getOrDefault(e.kind(), new float[]{1F, 0F, 0.5F, 0.5F});
            float spin = e.kind().equals("omniregistry_treasure") ? (e.tickCount + partial) * 1.5F : 0F;
            ps.pushPose();
            ps.mulPose(Axis.YP.rotationDegrees(180F - e.getYRot() + spin));
            ps.scale(st[0], st[0], st[0]);
            ps.translate(0.5F - st[2], 0.5F - st[1], 0.5F - st[3]);
            this.items.renderStatic(s, ItemDisplayContext.NONE, light, OverlayTexture.NO_OVERLAY, ps, buf, e.level(), e.getId());
            ps.popPose();
        }
        super.render(e, yaw, partial, ps, buf, light);
    }

    @Override
    public ResourceLocation getTextureLocation(PlacedGear e) {
        return InventoryMenu.BLOCK_ATLAS;
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Setup {
        private Setup() {
        }

        @SubscribeEvent
        public static void renderers(EntityRenderersEvent.RegisterRenderers e) {
            e.registerEntityRenderer(PlacedGear.TYPE, PlacedGearRenderer::new);
        }
    }

    /** What the gear does when worn or set down, under its name. */
    @EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
    public static final class Tips {
        private Tips() {
        }

        @SubscribeEvent
        public static void tooltip(ItemTooltipEvent e) {
            ResourceLocation id = BuiltInRegistries.ITEM.getKey(e.getItemStack().getItem());
            if (!id.getNamespace().equals("oror_supreme_bosses")) {
                return;
            }
            if (WornGear.WEARABLE.contains(id.getPath())) {
                e.getToolTip().add(Component.translatable("tooltip.oror_supreme_bosses.worn." + id.getPath()).withStyle(ChatFormatting.LIGHT_PURPLE));
            }
            if (PlacedGear.PLACEABLE.contains(id.getPath())) {
                e.getToolTip().add(Component.translatable("tooltip.oror_supreme_bosses.placeable." + id.getPath()).withStyle(ChatFormatting.DARK_AQUA));
            }
        }
    }
}
