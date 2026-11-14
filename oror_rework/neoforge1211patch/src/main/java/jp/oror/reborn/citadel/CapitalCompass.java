package jp.oror.reborn.citadel;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059f) 王都の羅針盤, the Royal Capital Compass (the user: "この世界に入場した時に王都への道を指し示すアイテムを配って
 * ついでに作って"). Every player is given one the first time they enter a world (once; a player of an older world gets it
 * at their next entry), and one is crafted from a compass, three gold ingots and an emerald. Its needle points to the
 * capital nearest its holder (the villager king's palace at its middle: CitadelSites), wherever the world put it, the
 * way a lodestone compass points to its lodestone, and spins in the Nether and the End; a right-click says how far the
 * capital is and which way, and when one is in it.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class CapitalCompass {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Compass");
    public static Item COMPASS;
    public static volatile boolean testLogged;
    private static final String GIVEN = "OrorCapitalCompassGiven";
    private static final String[] DIRECTIONS = {"n", "ne", "e", "se", "s", "sw", "w", "nw"};

    private CapitalCompass() {
    }

    static final class Compass extends Item {
        Compass(Properties properties) {
            super(properties);
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity holder, int slot, boolean selected) {
            // every two seconds or so, the needle set again (the holder may have come nearer another capital)
            if (!level.isClientSide && (level.getGameTime() + slot) % 40 == 0) {
                point(stack, holder.blockPosition());
            }
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            ItemStack stack = player.getItemInHand(hand);
            if (!level.isClientSide) {
                point(stack, player.blockPosition());
                player.displayClientMessage(report(level, player), true);
                level.playSound(null, player.blockPosition(), SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 0.7F, 1.2F);
            }
            return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> lines, TooltipFlag flag) {
            lines.add(Component.translatable("tooltip.oror_supreme_bosses.capital_compass").withStyle(ChatFormatting.GRAY));
            lines.add(Component.translatable("tooltip.oror_supreme_bosses.capital_compass.use").withStyle(ChatFormatting.DARK_GRAY));
        }
    }

    /** The middle of the capital nearest a place (the palace), or null in a world without one. */
    static BlockPos target(BlockPos from) {
        CitadelSites.Site site = CitadelSites.nearest(from, 0);
        if (site == null) {
            site = CitadelSites.capital();
        }
        return site == null ? null : site.center();
    }

    /** The needle set on the capital (a lodestone's mark that needs no lodestone), changed only when it moves. */
    static void point(ItemStack stack, BlockPos from) {
        BlockPos c = target(from);
        if (c == null) {
            return;
        }
        GlobalPos at = GlobalPos.of(Level.OVERWORLD, c);
        LodestoneTracker now = stack.get(DataComponents.LODESTONE_TRACKER);
        if (now == null || now.target().isEmpty() || !now.target().get().equals(at)) {
            stack.set(DataComponents.LODESTONE_TRACKER, new LodestoneTracker(Optional.of(at), false));
        }
    }

    /** "The capital: about 640 blocks, to the north-east", or that one is in it, or that it lies in the Overworld. */
    static Component report(Level level, Entity who) {
        BlockPos c = target(who.blockPosition());
        if (c == null) {
            return Component.translatable("message.oror_supreme_bosses.capital_compass.none");
        }
        if (!level.dimension().equals(Level.OVERWORLD)) {
            return Component.translatable("message.oror_supreme_bosses.capital_compass.elsewhere");
        }
        double dx = c.getX() + 0.5 - who.getX(), dz = c.getZ() + 0.5 - who.getZ();
        int distance = (int) Math.round(Math.sqrt(dx * dx + dz * dz));
        if (distance <= CitadelSites.SIZE * 8) {
            return Component.translatable("message.oror_supreme_bosses.capital_compass.here", distance);
        }
        // north is -z, east is +x: the bearing clockwise from north, in eight points
        double bearing = Math.toDegrees(Math.atan2(dx, -dz));
        int point = Math.floorMod((int) Math.round(bearing / 45.0), 8);
        return Component.translatable("message.oror_supreme_bosses.capital_compass.distance", distance,
            Component.translatable("message.oror_supreme_bosses.capital_compass.dir." + DIRECTIONS[point]));
    }

    /** The compass for a player who has never been given one in this world (true if it was given now). */
    static boolean give(ServerPlayer p) {
        if (COMPASS == null) {
            return false;
        }
        CompoundTag persisted = p.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
        if (persisted.getBoolean(GIVEN)) {
            return false;
        }
        persisted.putBoolean(GIVEN, true);
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, persisted);
        ItemStack stack = new ItemStack(COMPASS);
        point(stack, p.blockPosition());
        if (!p.getInventory().add(stack)) {
            p.drop(stack, false);
        }
        p.sendSystemMessage(Component.translatable("message.oror_supreme_bosses.capital_compass.given").withStyle(ChatFormatting.GOLD));
        return true;
    }

    @SubscribeEvent
    public static void login(PlayerEvent.PlayerLoggedInEvent event) {
        if (event.getEntity() instanceof ServerPlayer p && !(p instanceof FakePlayer)) {
            give(p);
        }
    }

    // ------------------------------------------------------------------------------------------------- registration

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    public static final class Registry {
        private Registry() {
        }

        @SubscribeEvent
        public static void register(RegisterEvent event) {
            event.register(Registries.ITEM, helper -> {
                COMPASS = new Compass(new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));
                helper.register(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "capital_compass"), COMPASS);
            });
        }

        @SubscribeEvent
        public static void tab(BuildCreativeModeTabContentsEvent event) {
            if (COMPASS == null) {
                return;
            }
            if (event.getTabKey() == CreativeModeTabs.TOOLS_AND_UTILITIES
                || event.getTabKey().location().equals(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "supreme_entities"))) {
                event.accept(COMPASS);
            }
        }
    }

    // --------------------------------------------------------------------------------------------- the CI check

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("compass").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> test(c.getSource())))));
    }

    /**
     * /oror compass test: a newcomer at the world's spawn is given the compass once (not again on a second entry), its
     * needle set on the capital's middle, its right-click's words; the recipe is in the game. Logged as COMPASS-RESULT.
     */
    private static int test(CommandSourceStack src) {
        ServerLevel lv = src.getServer().overworld();
        List<String> said = new ArrayList<>();
        FakePlayer fp = new FakePlayer(lv, new GameProfile(UUID.nameUUIDFromBytes("oror_compass_tester".getBytes()), "[Compass Tester]")) {
            @Override
            public void displayClientMessage(Component message, boolean overlay) {
                said.add(message.getString());
            }

            @Override
            public void sendSystemMessage(Component message) {
                said.add(message.getString());
            }
        };
        BlockPos spawn = lv.getSharedSpawnPos();
        fp.moveTo(spawn.getX() + 0.5, spawn.getY(), spawn.getZ() + 0.5, 0F, 0F);
        fp.getInventory().clearContent();
        boolean first = give(fp), again = give(fp);
        int count = 0;
        ItemStack held = ItemStack.EMPTY;
        for (ItemStack s : fp.getInventory().items) {
            if (COMPASS != null && s.is(COMPASS)) {
                count += s.getCount();
                held = s;
            }
        }
        BlockPos capital = target(spawn);
        LodestoneTracker tracker = held.isEmpty() ? null : held.get(DataComponents.LODESTONE_TRACKER);
        String aim = tracker == null || tracker.target().isEmpty() ? "none" : tracker.target().get().pos().toShortString();
        boolean match = capital != null && tracker != null && tracker.target().isPresent() && tracker.target().get().pos().equals(capital)
            && tracker.target().get().dimension().equals(Level.OVERWORLD);
        if (!held.isEmpty()) {
            fp.setItemInHand(InteractionHand.MAIN_HAND, held.copy());
            held.getItem().use(lv, fp, InteractionHand.MAIN_HAND);
        }
        boolean recipe = src.getServer().getRecipeManager().byKey(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "capital_compass"))
            .isPresent();
        boolean pass = COMPASS != null && first && !again && count == 1 && match && recipe;
        StringBuilder words = new StringBuilder();
        for (int i = 0; i < said.size(); i++) {
            words.append(i == 0 ? "" : ",").append('"').append(said.get(i).replace('"', '\'')).append('"');
        }
        LOG.info("COMPASS-RESULT {\"registered\":{},\"spawn\":\"{}\",\"capital\":\"{}\",\"given\":{},\"givenAgain\":{},\"count\":{},"
            + "\"needle\":\"{}\",\"match\":{},\"recipe\":{},\"said\":[{}],\"pass\":{}}", COMPASS != null, spawn.toShortString(),
            capital == null ? "none" : capital.toShortString(), first, again, count, aim, match, recipe, words, pass);
        testLogged = true;
        return 1;
    }
}
