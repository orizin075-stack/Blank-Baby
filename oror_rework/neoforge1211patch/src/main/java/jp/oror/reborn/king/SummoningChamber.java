package jp.oror.reborn.king;

import com.mojang.datafixers.util.Pair;
import java.util.ArrayList;
import java.util.List;
import jp.oror.reborn.StarterKit;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.Container;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CandleBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.LadderBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.LecternBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.LecternBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.saveddata.SavedData;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The player's coming into the world (the user: the player has been called into this world by someone: a magic
 * circle in a cellar, in a forest; rare things and all kinds of magic's materials lie about, ores and every material,
 * and the workshops too).
 * <p>
 * The first time anyone new comes into a world, a summoning chamber is dug under the nearest forest to the world's spawn:
 * a vaulted cellar of deepslate nineteen blocks square, ten blocks under the forest floor; a magic circle in its floor
 * (rings of crying obsidian and amethyst, soul lanterns at the four quarters, candles between); every workshop (crafting
 * table, furnace, blast furnace, smoker, anvil, smithing table, grindstone, stonecutter, loom, cartography table,
 * brewing stand and cauldron, an enchanting table among bookshelves, and Iron's Spells' inscription table, scroll forge,
 * alchemist cauldron and arcane anvil where there are); chests and barrels of rare things, magic's materials, ores and
 * ingots, every material and food; things left lying on the floor (they do not vanish); veins of ore in the walls; the
 * summoner's journal on a lectern; and a ladder up to a hatch in the forest floor.
 * <p>
 * A player new to the world wakes on the circle (a title, the summons' words, a flare of the portal's light); it is
 * where they come back to until they sleep in a bed. A player who was in the world before 054 is left where they are.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class SummoningChamber {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Summoning");
    public static final String MARK = "OrorSummoned";
    static final int HALF = 9, HEIGHT = 6, DEPTH = 10;

    private SummoningChamber() {
    }

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void joined(PlayerEvent.PlayerLoggedInEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p) || !(p.level() instanceof ServerLevel)) {
            return;
        }
        CompoundTag kept = p.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
        if (kept.getBoolean(MARK)) {
            return;
        }
        boolean old = kept.getBoolean(StarterKit.MARK);
        kept.putBoolean(MARK, true);
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, kept);
        if (old) {
            return;
        }
        ServerLevel overworld = p.server.overworld();
        BlockPos circle = Site.of(overworld).circle;
        if (circle == null) {
            circle = build(overworld, overworld.getSharedSpawnPos());
        }
        arrive(p, overworld, circle);
    }

    /** The player wakes on the circle. */
    public static void arrive(ServerPlayer p, ServerLevel sl, BlockPos circle) {
        try {
            p.teleportTo(sl, circle.getX() + 0.5, circle.getY(), circle.getZ() + 0.5, 0F, 0F);
        } catch (RuntimeException ex) {
            p.moveTo(circle.getX() + 0.5, circle.getY(), circle.getZ() + 0.5, 0F, 0F);
        }
        if (p.blockPosition().distManhattan(circle) > 1) {
            // a player without a real connection (the CI's stand-ins) is not moved by the teleport packet
            p.moveTo(circle.getX() + 0.5, circle.getY(), circle.getZ() + 0.5, 0F, 0F);
        }
        p.setRespawnPosition(sl.dimension(), circle, 0F, true, false);
        sl.sendParticles(ParticleTypes.PORTAL, p.getX(), p.getY() + 1, p.getZ(), 200, 1.5, 1.2, 1.5, 0.6);
        sl.sendParticles(ParticleTypes.ENCHANT, p.getX(), p.getY() + 0.2, p.getZ(), 200, 4, 0.2, 4, 1);
        sl.playSound(null, circle, SoundEvents.PORTAL_TRAVEL, SoundSource.AMBIENT, 0.4F, 0.7F);
        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal("召喚").withStyle(ChatFormatting.DARK_PURPLE)));
        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("……応えよ、異界の旅人よ。").withStyle(ChatFormatting.LIGHT_PURPLE)));
        p.sendSystemMessage(Component.literal("……声がする。『応えよ、異界の旅人よ。汝を喚んだのは――』").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.ITALIC));
        p.sendSystemMessage(Component.literal("声は途切れた。足元の魔法陣が、ゆっくりと光を失っていく。").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
        LOG.info("SUMMONED {\"player\":\"{}\",\"at\":[{},{},{}]}", p.getGameProfile().getName(), circle.getX(), circle.getY(), circle.getZ());
    }

    // ---------------------------------------------------------------------------------------------- the cellar

    /** Digs the chamber under the forest nearest to near; returns where the circle's middle is (where one stands). */
    public static BlockPos build(ServerLevel sl, BlockPos near) {
        BlockPos forest = near;
        try {
            Pair<BlockPos, Holder<Biome>> found = sl.findClosestBiome3d(h -> h.is(BiomeTags.IS_FOREST), near, 2400, 32, 64);
            if (found != null) {
                forest = found.getFirst();
            }
        } catch (RuntimeException ex) {
            LOG.warn("SUMMON-FOREST-SEARCH {}", ex.toString());
        }
        sl.getChunk(forest.getX() >> 4, forest.getZ() >> 4);
        int ground = sl.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, forest.getX(), forest.getZ());
        int floor = Math.max(sl.getMinBuildHeight() + 6, ground - DEPTH - HEIGHT);
        BlockPos o = new BlockPos(forest.getX(), floor, forest.getZ());
        for (int cx = (o.getX() - HALF - 1) >> 4; cx <= (o.getX() + HALF + 1) >> 4; cx++) {
            for (int cz = (o.getZ() - HALF - 1) >> 4; cz <= (o.getZ() + HALF + 1) >> 4; cz++) {
                sl.getChunk(cx, cz);
            }
        }
        room(sl, o);
        circle(sl, o);
        workshops(sl, o);
        stores(sl, o);
        lying(sl, o);
        exit(sl, o, ground);
        BlockPos stand = o.above();
        Site s = Site.of(sl);
        s.circle = stand;
        s.setDirty();
        LOG.info("SUMMON-CHAMBER-BUILT {\"at\":[{},{},{}],\"ground\":{},\"forest\":{}}", stand.getX(), stand.getY(), stand.getZ(), ground, forest != near);
        return stand;
    }

    static void set(ServerLevel sl, BlockPos p, BlockState s) {
        sl.setBlock(p, s, 2);
    }

    static void room(ServerLevel sl, BlockPos o) {
        BlockState wall = Blocks.DEEPSLATE_BRICKS.defaultBlockState(), floor = Blocks.POLISHED_BLACKSTONE.defaultBlockState(),
            ceiling = Blocks.DEEPSLATE_TILES.defaultBlockState(), air = Blocks.AIR.defaultBlockState();
        Block[] ores = {Blocks.DEEPSLATE_IRON_ORE, Blocks.DEEPSLATE_GOLD_ORE, Blocks.DEEPSLATE_DIAMOND_ORE, Blocks.DEEPSLATE_EMERALD_ORE,
            Blocks.DEEPSLATE_REDSTONE_ORE, Blocks.DEEPSLATE_LAPIS_ORE, Blocks.DEEPSLATE_COPPER_ORE, Blocks.DEEPSLATE_COAL_ORE};
        int vein = 0;
        for (int x = -HALF - 1; x <= HALF + 1; x++) {
            for (int z = -HALF - 1; z <= HALF + 1; z++) {
                for (int y = 0; y <= HEIGHT + 1; y++) {
                    boolean edge = Math.abs(x) == HALF + 1 || Math.abs(z) == HALF + 1;
                    BlockPos p = o.offset(x, y, z);
                    if (y == 0) {
                        set(sl, p, floor);
                    } else if (y == HEIGHT + 1) {
                        set(sl, p, ceiling);
                    } else if (edge) {
                        // the walls, with veins of ore here and there
                        boolean ore = (x * 7 + z * 13 + y * 5) % 11 == 0 && y < HEIGHT - 1;
                        set(sl, p, ore ? ores[vein++ % ores.length].defaultBlockState() : wall);
                    } else {
                        set(sl, p, air);
                    }
                }
            }
        }
        // pillars at the corners and the middles of the walls, soul lanterns hung from the vault
        for (int[] c : new int[][]{{-HALF, -HALF}, {HALF, -HALF}, {-HALF, HALF}, {HALF, HALF}}) {
            for (int y = 1; y <= HEIGHT; y++) {
                set(sl, o.offset(c[0], y, c[1]), Blocks.POLISHED_DEEPSLATE.defaultBlockState());
            }
        }
        for (int[] c : new int[][]{{-6, -6}, {6, -6}, {-6, 6}, {6, 6}, {0, -7}, {0, 7}, {-7, 0}, {7, 0}}) {
            set(sl, o.offset(c[0], HEIGHT, c[1]), Blocks.SOUL_LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, true));
        }
    }

    static void circle(ServerLevel sl, BlockPos o) {
        for (int x = -6; x <= 6; x++) {
            for (int z = -6; z <= 6; z++) {
                double r = Math.sqrt(x * x + z * z);
                BlockPos p = o.offset(x, 0, z);
                if (r > 4.5 && r <= 5.5) {
                    set(sl, p, ((x + z) & 1) == 0 ? Blocks.CRYING_OBSIDIAN.defaultBlockState() : Blocks.AMETHYST_BLOCK.defaultBlockState());
                } else if (r > 2.5 && r <= 3.3) {
                    set(sl, p, Blocks.PURPUR_BLOCK.defaultBlockState());
                } else if (Math.abs(x) == Math.abs(z) && r <= 2.9 && r > 0) {
                    set(sl, p, Blocks.OBSIDIAN.defaultBlockState());
                }
            }
        }
        set(sl, o, Blocks.CHISELED_DEEPSLATE.defaultBlockState());
        for (int[] c : new int[][]{{0, -5}, {0, 5}, {-5, 0}, {5, 0}}) {
            set(sl, o.offset(c[0], 1, c[1]), Blocks.SOUL_LANTERN.defaultBlockState());
        }
        for (int[] c : new int[][]{{-4, -4}, {4, -4}, {-4, 4}, {4, 4}}) {
            set(sl, o.offset(c[0], 1, c[1]), Blocks.PURPLE_CANDLE.defaultBlockState().setValue(CandleBlock.CANDLES, 4).setValue(CandleBlock.LIT, true));
        }
    }

    static Block block(String id) {
        ResourceLocation rl = ResourceLocation.parse(id);
        return BuiltInRegistries.BLOCK.containsKey(rl) ? BuiltInRegistries.BLOCK.get(rl) : null;
    }

    static void workshops(ServerLevel sl, BlockPos o) {
        // the west wall: the workshops
        Block[] west = {Blocks.CRAFTING_TABLE, Blocks.FURNACE, Blocks.BLAST_FURNACE, Blocks.SMOKER, Blocks.ANVIL, Blocks.SMITHING_TABLE,
            Blocks.GRINDSTONE, Blocks.STONECUTTER, Blocks.LOOM, Blocks.CARTOGRAPHY_TABLE, Blocks.FLETCHING_TABLE, Blocks.BREWING_STAND,
            Blocks.WATER_CAULDRON};
        for (int i = 0; i < west.length; i++) {
            BlockState s = west[i].defaultBlockState();
            if (s.hasProperty(net.minecraft.world.level.block.state.properties.BlockStateProperties.HORIZONTAL_FACING)) {
                s = s.setValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.HORIZONTAL_FACING, Direction.EAST);
            }
            if (west[i] == Blocks.WATER_CAULDRON) {
                s = s.setValue(net.minecraft.world.level.block.LayeredCauldronBlock.LEVEL, 3);
            }
            set(sl, o.offset(-HALF + 1, 1, -6 + i), s);
        }
        // the north wall: the study (an enchanting table among bookshelves, the journal on a lectern) and the
        // magic of Iron's Spells where there is
        for (int x = -6; x <= 6; x++) {
            if (Math.abs(x) >= 2) {
                set(sl, o.offset(x, 1, -HALF + 1), Blocks.BOOKSHELF.defaultBlockState());
                set(sl, o.offset(x, 2, -HALF + 1), Blocks.BOOKSHELF.defaultBlockState());
            }
        }
        set(sl, o.offset(0, 1, -HALF + 3), Blocks.ENCHANTING_TABLE.defaultBlockState());
        BlockPos lectern = o.offset(1, 1, -HALF + 3);
        set(sl, lectern, Blocks.LECTERN.defaultBlockState().setValue(LecternBlock.FACING, Direction.SOUTH));
        if (sl.getBlockEntity(lectern) instanceof LecternBlockEntity le) {
            le.setBook(journal());
            set(sl, lectern, sl.getBlockState(lectern).setValue(LecternBlock.HAS_BOOK, true));
        }
        String[] iss = {"irons_spellbooks:inscription_table", "irons_spellbooks:scroll_forge", "irons_spellbooks:alchemist_cauldron",
            "irons_spellbooks:arcane_anvil"};
        int i = 0;
        for (String id : iss) {
            Block b = block(id);
            if (b != null) {
                set(sl, o.offset(-6 + i * 3, 1, -HALF + 3), b.defaultBlockState());
                i++;
            }
        }
    }

    static ItemStack journal() {
        ItemStack book = new ItemStack(Items.WRITTEN_BOOK);
        List<Filterable<Component>> pages = new ArrayList<>();
        for (String page : new String[]{
            "召喚の記録\n\n陣は成った。異界より、ひとりの旅人を喚ぶ。\n\nこの世界の均衡は、もはや保てぬ。",
            "王は三度死に、三度蘇るという。\n\nその名は、誰も正しく書けぬ。書けば文字が崩れるのだ。\n\n村人どもは彼を村人王と呼ぶ。",
            "東の森の向こう、叛逆者の都には、神に叛いた者が君臨している。\n\n王を斃せるのは、あの者の刃のみ。",
            "旅人よ。王に仕えるも、叛くも、汝の自由だ。\n\nこの地下室にあるものは、すべて汝のものだ。\n\nどうか――",
            "（ここから先は、焼け焦げて読めない）"}) {
            pages.add(Filterable.passThrough(Component.literal(page)));
        }
        book.set(DataComponents.WRITTEN_BOOK_CONTENT, new WrittenBookContent(Filterable.passThrough("召喚者の手記"), "？？？", 0, pages, true));
        return book;
    }

    static ItemStack stack(String id, int n) {
        ResourceLocation rl = ResourceLocation.parse(id);
        if (!BuiltInRegistries.ITEM.containsKey(rl)) {
            return ItemStack.EMPTY;
        }
        Item it = BuiltInRegistries.ITEM.get(rl);
        return new ItemStack(it, Math.min(n, it.getDefaultMaxStackSize()));
    }

    static ItemStack book(ServerLevel sl, net.minecraft.resources.ResourceKey<net.minecraft.world.item.enchantment.Enchantment> key, int level) {
        return net.minecraft.world.item.EnchantedBookItem.createForEnchantment(new EnchantmentInstance(sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT).getHolderOrThrow(key), level));
    }

    /** The east wall: chests and barrels, each kind of thing in its own. */
    static void stores(ServerLevel sl, BlockPos o) {
        List<List<ItemStack>> kinds = new ArrayList<>();
        kinds.add(List.of(stack("minecraft:diamond", 8), stack("minecraft:emerald", 16), stack("minecraft:golden_apple", 4),
            stack("minecraft:ender_pearl", 8), stack("minecraft:name_tag", 2), stack("minecraft:saddle", 1), stack("minecraft:totem_of_undying", 1),
            stack("minecraft:experience_bottle", 16), stack("minecraft:diamond_sword", 1), stack("minecraft:bow", 1), stack("minecraft:arrow", 64),
            book(sl, Enchantments.PROTECTION, 3), book(sl, Enchantments.SHARPNESS, 3), book(sl, Enchantments.EFFICIENCY, 4),
            book(sl, Enchantments.UNBREAKING, 3)));
        kinds.add(List.of(stack("irons_spellbooks:arcane_essence", 32), stack("irons_spellbooks:common_ink", 8), stack("irons_spellbooks:uncommon_ink", 4),
            stack("irons_spellbooks:rare_ink", 2), stack("irons_spellbooks:magic_cloth", 4), stack("irons_spellbooks:blank_rune", 6),
            stack("irons_spellbooks:arcane_ingot", 2), stack("irons_spellbooks:mithril_scrap", 2), stack("minecraft:blaze_powder", 8),
            stack("minecraft:nether_wart", 12), stack("minecraft:glowstone_dust", 16), stack("minecraft:redstone", 32), stack("minecraft:lapis_lazuli", 32),
            stack("minecraft:amethyst_shard", 16), stack("minecraft:ghast_tear", 2), stack("minecraft:phantom_membrane", 4), stack("minecraft:echo_shard", 2),
            stack("minecraft:glass_bottle", 16), stack("minecraft:spider_eye", 8), stack("minecraft:sugar", 16)));
        kinds.add(List.of(stack("minecraft:raw_iron", 32), stack("minecraft:raw_gold", 16), stack("minecraft:raw_copper", 32), stack("minecraft:iron_ingot", 16),
            stack("minecraft:gold_ingot", 8), stack("minecraft:copper_ingot", 16), stack("minecraft:coal", 64), stack("minecraft:obsidian", 8),
            stack("minecraft:quartz", 16), stack("minecraft:diamond_ore", 2), stack("minecraft:emerald_ore", 2)));
        kinds.add(List.of(stack("minecraft:leather", 16), stack("minecraft:string", 16), stack("minecraft:paper", 32), stack("minecraft:book", 8),
            stack("minecraft:oak_log", 64), stack("minecraft:cobblestone", 64), stack("minecraft:glass", 32), stack("minecraft:white_wool", 16),
            stack("minecraft:slime_ball", 8), stack("minecraft:feather", 16), stack("minecraft:flint", 16), stack("minecraft:clay_ball", 32)));
        kinds.add(List.of(stack("minecraft:bread", 16), stack("minecraft:cooked_beef", 16), stack("minecraft:baked_potato", 16), stack("minecraft:apple", 8),
            stack("minecraft:honey_bottle", 4), stack("minecraft:torch", 64)));
        for (int i = 0; i < kinds.size(); i++) {
            for (int twice = 0; twice < 2; twice++) {
                BlockPos at = o.offset(HALF - 1, 1, -5 + i * 2 + twice);
                boolean chest = twice == 0;
                set(sl, at, chest ? Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.WEST) : Blocks.BARREL.defaultBlockState());
                BlockEntity be = sl.getBlockEntity(at);
                if (be instanceof Container c) {
                    List<ItemStack> things = kinds.get(i);
                    int slot = 0;
                    for (int k = twice; k < things.size(); k += 2) {
                        if (!things.get(k).isEmpty() && slot < c.getContainerSize()) {
                            c.setItem(slot++, things.get(k).copy());
                        }
                    }
                    be.setChanged();
                }
            }
        }
    }

    /** Things left lying about the floor (they do not vanish). */
    static void lying(ServerLevel sl, BlockPos o) {
        String[][] about = {{"irons_spellbooks:arcane_essence", "8"}, {"minecraft:amethyst_shard", "6"}, {"minecraft:diamond", "2"},
            {"minecraft:lapis_lazuli", "12"}, {"minecraft:redstone", "12"}, {"minecraft:gold_nugget", "16"}, {"minecraft:book", "3"},
            {"irons_spellbooks:common_ink", "2"}, {"minecraft:glowstone_dust", "8"}, {"minecraft:emerald", "4"}};
        int i = 0;
        for (String[] a : about) {
            ItemStack s = stack(a[0], Integer.parseInt(a[1]));
            if (s.isEmpty()) {
                continue;
            }
            double ang = i * 0.7;
            double r = 6.6 + (i % 3) * 0.5;
            ItemEntity it = new ItemEntity(sl, o.getX() + 0.5 + Math.cos(ang) * r, o.getY() + 1.1, o.getZ() + 0.5 + Math.sin(ang) * r, s);
            it.setUnlimitedLifetime();
            it.setDeltaMovement(0, 0, 0);
            sl.addFreshEntity(it);
            i++;
        }
    }

    /** The way out: a ladder up a shaft in the south wall to a hatch in the forest floor, marked by mossy stones. */
    static void exit(ServerLevel sl, BlockPos o, int ground) {
        int x = o.getX(), z = o.getZ() + HALF + 1;
        for (int y = o.getY() + 1; y <= ground; y++) {
            BlockPos p = new BlockPos(x, y, z);
            set(sl, p, Blocks.LADDER.defaultBlockState().setValue(LadderBlock.FACING, Direction.NORTH));
            set(sl, p.south(), Blocks.DEEPSLATE_BRICKS.defaultBlockState());
            set(sl, p.east(), Blocks.DEEPSLATE_BRICKS.defaultBlockState());
            set(sl, p.west(), Blocks.DEEPSLATE_BRICKS.defaultBlockState());
            if (y > o.getY() + HEIGHT + 1) {
                set(sl, p.north(), Blocks.DEEPSLATE_BRICKS.defaultBlockState());
            }
        }
        BlockPos top = new BlockPos(x, ground + 1, z);
        set(sl, top, Blocks.SPRUCE_TRAPDOOR.defaultBlockState().setValue(TrapDoorBlock.FACING, Direction.NORTH).setValue(TrapDoorBlock.OPEN, true));
        for (int[] c : new int[][]{{-1, -1}, {1, -1}, {-1, 1}, {1, 1}}) {
            set(sl, top.offset(c[0], 0, c[1]), Blocks.MOSSY_COBBLESTONE_WALL.defaultBlockState());
            set(sl, top.offset(c[0], 1, c[1]), Blocks.LANTERN.defaultBlockState());
        }
    }

    /** Where the chamber is, once dug. */
    static final class Site extends SavedData {
        BlockPos circle;

        static Site of(ServerLevel sl) {
            return sl.getDataStorage().computeIfAbsent(new SavedData.Factory<>(Site::new, Site::load, null), "oror_summoning_chamber");
        }

        static Site load(CompoundTag tag, HolderLookup.Provider lookup) {
            Site s = new Site();
            if (tag.contains("Circle")) {
                s.circle = BlockPos.of(tag.getLong("Circle"));
            }
            return s;
        }

        @Override
        public CompoundTag save(CompoundTag tag, HolderLookup.Provider lookup) {
            if (this.circle != null) {
                tag.putLong("Circle", this.circle.asLong());
            }
            return tag;
        }
    }

    /** Where the chamber's circle is (null before anyone new came), for the CI's check. */
    public static BlockPos circle(ServerLevel sl) {
        return Site.of(sl).circle;
    }
}
