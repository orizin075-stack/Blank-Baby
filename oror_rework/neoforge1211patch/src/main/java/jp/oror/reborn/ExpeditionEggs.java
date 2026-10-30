package jp.oror.reborn;

import java.util.List;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.DeferredSpawnEggItem;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.registries.RegisterEvent;

/**
 * Spawn eggs for whole parties, and every royal spawn egg in the creative tabs (045 registered them but listed them in
 * none). The expedition party egg brings four veteran villagers in iron, a smith, an armourer, a toolsmith and a
 * fletcher, who join the nearest village as its expedition corps; the royal expedition egg brings a general with two
 * imperial guards, four kingdom guards and a battle mage.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class ExpeditionEggs {
    public static Item VILLAGE_PARTY, ROYAL_PARTY;

    private ExpeditionEggs() {
    }

    static ResourceLocation id(String path) {
        return ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path);
    }

    @SubscribeEvent
    public static void register(RegisterEvent e) {
        if (e.getRegistryKey().equals(Registries.ITEM)) {
            VILLAGE_PARTY = new PartyEgg(false, 0x6B4F2A, 0xC8C8C8);
            ROYAL_PARTY = new PartyEgg(true, 0x3A2B6B, 0xF6C344);
            e.register(Registries.ITEM, id("expedition_party_spawn_egg"), () -> VILLAGE_PARTY);
            e.register(Registries.ITEM, id("royal_expedition_spawn_egg"), () -> ROYAL_PARTY);
        }
    }

    @SubscribeEvent
    public static void tabs(BuildCreativeModeTabContentsEvent e) {
        if (!e.getTabKey().location().equals(id("supreme_entities")) && !e.getTabKey().equals(CreativeModeTabs.SPAWN_EGGS)) {
            return;
        }
        for (RoyalRole r : RoyalRole.values()) {
            Item egg = BuiltInRegistries.ITEM.get(id(r.id + "_spawn_egg"));
            if (egg != Items.AIR) {
                e.accept(egg);
            }
        }
        e.accept(VILLAGE_PARTY);
        e.accept(ROYAL_PARTY);
    }

    static final class PartyEgg extends DeferredSpawnEggItem {
        private final boolean royal;

        PartyEgg(boolean royal, int background, int highlight) {
            super(royal ? () -> RoyalRegistry.TYPES.get(RoyalRole.GENERAL) : () -> EntityType.VILLAGER, background, highlight, new Item.Properties());
            this.royal = royal;
        }

        @Override
        public InteractionResult useOn(UseOnContext ctx) {
            if (!(ctx.getLevel() instanceof ServerLevel level)) {
                return InteractionResult.SUCCESS;
            }
            BlockPos at = ctx.getClickedPos().relative(ctx.getClickedFace());
            float yaw = ctx.getPlayer() == null ? 0F : ctx.getPlayer().getYRot() + 180F;
            int n = royal ? royalParty(level, at, yaw) : villageParty(level, at, yaw);
            if (ctx.getPlayer() != null && !ctx.getPlayer().getAbilities().instabuild) {
                ctx.getItemInHand().shrink(1);
            }
            return n > 0 ? InteractionResult.CONSUME : InteractionResult.FAIL;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            return InteractionResultHolder.pass(player.getItemInHand(hand));
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
            tooltip.add(Component.literal(royal ? "将軍・近衛兵2・王国衛兵4・王国魔法師団1" : "鍛冶屋・鎧鍛冶・道具鍛冶・矢師の熟練遠征隊4名")
                .withStyle(net.minecraft.ChatFormatting.GRAY));
        }
    }

    /** Ranks of up to four, two blocks apart, facing yaw. */
    private static Vec3 slot(BlockPos at, float yaw, int i) {
        Vec3 f = Vec3.directionFromRotation(0, yaw), side = new Vec3(-f.z, 0, f.x);
        return Vec3.atBottomCenterOf(at).add(side.scale(((i % 4) - 1.5) * 2)).subtract(f.scale((i / 4) * 2.0));
    }

    private static void place(ServerLevel level, Mob m, Vec3 p, float yaw) {
        m.moveTo(p.x, p.y, p.z, yaw, 0F);
        m.setYHeadRot(yaw);
        m.setPersistenceRequired();
        level.addFreshEntity(m);
    }

    static int royalParty(ServerLevel level, BlockPos at, float yaw) {
        RoyalRole[] ranks = {RoyalRole.IMPERIAL, RoyalRole.GENERAL, RoyalRole.IMPERIAL, RoyalRole.MAGE,
            RoyalRole.GUARD, RoyalRole.GUARD, RoyalRole.GUARD, RoyalRole.GUARD};
        int n = 0;
        for (int i = 0; i < ranks.length; i++) {
            RoyalMob m = RoyalRegistry.TYPES.get(ranks[i]).create(level);
            if (m != null) {
                place(level, m, slot(at, yaw, i), yaw);
                n++;
            }
        }
        return n;
    }

    static int villageParty(ServerLevel level, BlockPos at, float yaw) {
        VillagerProfession[] trades = {VillagerProfession.WEAPONSMITH, VillagerProfession.ARMORER, VillagerProfession.TOOLSMITH,
            VillagerProfession.FLETCHER};
        int n = 0;
        for (int i = 0; i < trades.length; i++) {
            Villager v = EntityType.VILLAGER.create(level);
            if (v == null) {
                continue;
            }
            // a journeyman with an expedition behind them: keeps the trade, counts as a veteran of rank 2
            v.setVillagerData(v.getVillagerData().setProfession(trades[i]).setLevel(3));
            v.setVillagerXp(70);
            VillagerLife.data(v).putInt("Veteran", 2);
            VillageExpeditions.veteran(v, 2);
            v.setItemSlot(EquipmentSlot.HEAD, new ItemStack(Items.IRON_HELMET));
            v.setItemSlot(EquipmentSlot.CHEST, new ItemStack(Items.IRON_CHESTPLATE));
            v.setItemSlot(EquipmentSlot.LEGS, new ItemStack(Items.IRON_LEGGINGS));
            v.setItemSlot(EquipmentSlot.FEET, new ItemStack(Items.IRON_BOOTS));
            v.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(trades[i] == VillagerProfession.FLETCHER ? Items.CROSSBOW : Items.IRON_SWORD));
            for (EquipmentSlot s : EquipmentSlot.values()) {
                v.setDropChance(s, 0F);
            }
            place(level, v, slot(at, yaw, i), yaw);
            n++;
        }
        return n;
    }
}
