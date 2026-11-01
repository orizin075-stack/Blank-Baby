package jp.oror.reborn.royal;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.ChatFormatting;
import net.minecraft.client.renderer.item.ItemProperties;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.TridentItem;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.ItemTooltipEvent;
import net.neoforged.neoforge.event.entity.player.PlayerContainerEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.registries.RegisterEvent;

/**
 * The forbidden vault's king-slayers as arms of their own (051): 界断 the sword, 断罪 the axe, 天穿 the bow, 堕星 the
 * crossbow and 海嘯 the trident, each with its own look (the vault had kept them as a netherite sword, a bow and so on
 * with a name and a mark in their data, and they looked it). The ones already lying in vaults, the save's and those of
 * capitals generated before, are made over into these the first time a player opens their chest or carries one, with
 * their names, enchantments and the rest of their data; ForbiddenArms takes either for a king-slayer.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class KingslayerArms {
    public static Item SWORD, AXE, BOW, CROSSBOW, TRIDENT;
    private static final Set<Item> ALL = new HashSet<>();

    private KingslayerArms() {
    }

    static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path);
    }

    private static Item.Properties props() {
        return new Item.Properties().fireResistant().rarity(Rarity.EPIC);
    }

    @SubscribeEvent
    public static void register(RegisterEvent e) {
        e.register(Registries.ITEM, helper -> {
            SWORD = new SwordItem(Tiers.NETHERITE, props().attributes(SwordItem.createAttributes(Tiers.NETHERITE, 5, -2.4F)));
            AXE = new AxeItem(Tiers.NETHERITE, props().attributes(AxeItem.createAttributes(Tiers.NETHERITE, 7.0F, -3.0F)));
            BOW = new BowItem(props().durability(1536));
            CROSSBOW = new CrossbowItem(props().durability(1465));
            TRIDENT = new TridentItem(props().durability(1250).attributes(TridentItem.createAttributes())
                .component(DataComponents.TOOL, TridentItem.createToolProperties()));
            helper.register(id("kingslayer_sword"), SWORD);
            helper.register(id("kingslayer_axe"), AXE);
            helper.register(id("kingslayer_bow"), BOW);
            helper.register(id("kingslayer_crossbow"), CROSSBOW);
            helper.register(id("kingslayer_trident"), TRIDENT);
            ALL.addAll(List.of(SWORD, AXE, BOW, CROSSBOW, TRIDENT));
        });
    }

    @SubscribeEvent
    public static void tabs(BuildCreativeModeTabContentsEvent e) {
        if (e.getTabKey().equals(CreativeModeTabs.COMBAT) || e.getTabKey().location().equals(id("supreme_entities"))) {
            for (Item item : new Item[]{SWORD, AXE, BOW, CROSSBOW, TRIDENT}) {
                if (item != null) {
                    e.accept(item);
                }
            }
        }
    }

    /** One of these arms. */
    public static boolean is(ItemStack stack) {
        return ALL.contains(stack.getItem());
    }

    /** A king-slayer kept as a vanilla item made over into its own arm, with all its data; anything else as it is. */
    public static ItemStack convert(ItemStack stack) {
        if (stack.isEmpty() || ALL.isEmpty() || is(stack) || !ForbiddenArms.marked(stack)) {
            return stack;
        }
        Item to = stack.is(Items.NETHERITE_SWORD) ? SWORD : stack.is(Items.NETHERITE_AXE) ? AXE : stack.is(Items.BOW) ? BOW
            : stack.is(Items.CROSSBOW) ? CROSSBOW : stack.is(Items.TRIDENT) ? TRIDENT : null;
        if (to == null) {
            return stack;
        }
        ItemStack made = new ItemStack(to, stack.getCount());
        made.applyComponents(stack.getComponentsPatch());
        return made;
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses")
    public static final class Remake {
        public static volatile boolean testLogged;
        private static final org.slf4j.Logger LOG = org.slf4j.LoggerFactory.getLogger("OROR Arms");

        private Remake() {
        }

        /**
         * /oror arms test (CI): a vault king-slayer as the save holds it (a netherite sword marked, named, enchanted) made
         * over, and whether the arms of 0.17.27 (railgun, laser gun, their rounds, the Blueprinter) are registered.
         */
        @SubscribeEvent
        public static void commands(RegisterCommandsEvent e) {
            e.getDispatcher().register(net.minecraft.commands.Commands.literal("oror").then(net.minecraft.commands.Commands.literal("arms")
                .requires(src -> src.hasPermission(2)).then(net.minecraft.commands.Commands.literal("test").executes(c -> {
                    ItemStack old = new ItemStack(Items.NETHERITE_SWORD);
                    net.minecraft.nbt.CompoundTag tag = new net.minecraft.nbt.CompoundTag();
                    tag.putBoolean(ForbiddenArms.KINGSLAYER, true);
                    old.set(DataComponents.CUSTOM_DATA, net.minecraft.world.item.component.CustomData.of(tag));
                    old.set(DataComponents.CUSTOM_NAME, Component.literal("王殺しの剣「界断」"));
                    net.minecraft.core.Holder<net.minecraft.world.item.enchantment.Enchantment> sharp = c.getSource().registryAccess()
                        .registryOrThrow(Registries.ENCHANTMENT).getHolderOrThrow(net.minecraft.world.item.enchantment.Enchantments.SHARPNESS);
                    old.enchant(sharp, 10);
                    ItemStack made = convert(old);
                    StringBuilder arms = new StringBuilder();
                    for (String n : new String[]{"railgun", "laser_gun", "rail_slug", "focus_cell", "matter_cartridge", "blueprinter",
                        "kingslayer_sword", "kingslayer_axe", "kingslayer_bow", "kingslayer_crossbow", "kingslayer_trident"}) {
                        arms.append(arms.length() > 0 ? "," : "").append("\"").append(n).append("\":")
                            .append(net.minecraft.core.registries.BuiltInRegistries.ITEM.containsKey(id(n)));
                    }
                    LOG.info(String.format(java.util.Locale.ROOT, "KINGSLAYER-TEST {\"made\":\"%s\",\"name\":\"%s\",\"sharpness\":%d,"
                            + "\"kingslayer\":%b,\"oldKingslayer\":%b,\"registered\":{%s}}",
                        net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(made.getItem()), made.getHoverName().getString(),
                        made.getEnchantments().getLevel(sharp), ForbiddenArms.kingslayer(made), ForbiddenArms.kingslayer(old), arms));
                    testLogged = true;
                    return 1;
                }))));
        }

        @SubscribeEvent
        public static void carried(PlayerTickEvent.Post e) {
            Player player = e.getEntity();
            if (player.level().isClientSide || player.tickCount % 20 != 3) {
                return;
            }
            Inventory inv = player.getInventory();
            for (int i = 0; i < inv.getContainerSize(); i++) {
                ItemStack stack = inv.getItem(i);
                ItemStack made = convert(stack);
                if (made != stack) {
                    inv.setItem(i, made);
                }
            }
        }

        @SubscribeEvent
        public static void opened(PlayerContainerEvent.Open e) {
            for (Slot slot : e.getContainer().slots) {
                ItemStack stack = slot.getItem();
                ItemStack made = convert(stack);
                if (made != stack) {
                    slot.set(made);
                }
            }
        }
    }

    /** The bow's and the crossbow's drawn looks (vanilla gives its properties to its own bow and crossbow only). */
    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
    public static final class Looks {
        private Looks() {
        }

        @SubscribeEvent
        public static void setup(FMLClientSetupEvent e) {
            e.enqueueWork(() -> {
                ResourceLocation pull = ResourceLocation.withDefaultNamespace("pull");
                ResourceLocation pulling = ResourceLocation.withDefaultNamespace("pulling");
                ItemProperties.register(BOW, pull, (stack, level, entity, seed) -> entity == null || entity.getUseItem() != stack ? 0F
                    : (stack.getUseDuration(entity) - entity.getUseItemRemainingTicks()) / 20F);
                ItemProperties.register(BOW, pulling, (stack, level, entity, seed) ->
                    entity != null && entity.isUsingItem() && entity.getUseItem() == stack ? 1F : 0F);
                ItemProperties.register(CROSSBOW, pull, (stack, level, entity, seed) -> entity == null || CrossbowItem.isCharged(stack) ? 0F
                    : (stack.getUseDuration(entity) - entity.getUseItemRemainingTicks()) / (float) CrossbowItem.getChargeDuration(stack, entity));
                ItemProperties.register(CROSSBOW, pulling, (stack, level, entity, seed) ->
                    entity != null && entity.isUsingItem() && entity.getUseItem() == stack && !CrossbowItem.isCharged(stack) ? 1F : 0F);
                ItemProperties.register(CROSSBOW, ResourceLocation.withDefaultNamespace("charged"), (stack, level, entity, seed) ->
                    CrossbowItem.isCharged(stack) ? 1F : 0F);
                ItemProperties.register(CROSSBOW, ResourceLocation.withDefaultNamespace("firework"), (stack, level, entity, seed) -> {
                    ChargedProjectiles shot = stack.get(DataComponents.CHARGED_PROJECTILES);
                    return shot != null && shot.contains(Items.FIREWORK_ROCKET) ? 1F : 0F;
                });
            });
        }
    }

    /** What a king-slayer does, under one fresh from the creative tab (the vault's carry it in their lore already). */
    @EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
    public static final class Tips {
        private Tips() {
        }

        @SubscribeEvent
        public static void tooltip(ItemTooltipEvent e) {
            if (is(e.getItemStack()) && !e.getItemStack().has(DataComponents.LORE)) {
                e.getToolTip().add(Component.translatable("item.oror_supreme_bosses.kingslayer.desc1").withStyle(ChatFormatting.RED));
                e.getToolTip().add(Component.translatable("item.oror_supreme_bosses.kingslayer.desc2").withStyle(ChatFormatting.RED));
                e.getToolTip().add(Component.translatable("item.oror_supreme_bosses.kingslayer.desc3").withStyle(ChatFormatting.RED));
            }
        }
    }
}
