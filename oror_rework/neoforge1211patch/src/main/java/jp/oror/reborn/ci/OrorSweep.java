package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Vindicator;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * /oror sweep (051, CI): everything of OROR's own put to work once, on a stone field far from spawn.
 * <ul>
 * <li>Every living entity of the mod, six at a time in arenas 96 blocks apart, each with a vindicator of 500 health
 * set before it as its target for fifteen seconds: SWEEP-ENTITY says whether it came into the world, lived, moved, and
 * how much it took off the vindicator (and anything else it hurt).</li>
 * <li>Every item of the mod in the hand of a stand-in player beside a vindicator: used (and, if it is held to charge,
 * let go after a second and a half), carried for a second (so that what it does while carried can show), and swung at
 * the vindicator. SWEEP-ITEM says what came of it: things that appeared, damage, effects, a cooldown, the stack used or
 * worn, armour worn, or an exception.</li>
 * <li>The starter kit given to the stand-in player, and its handgun rounds used: SWEEP-KIT.</li>
 * </ul>
 * SWEEP-RESULT sums it up.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class OrorSweep {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Sweep");
    private static final String NS = "oror_supreme_bosses";
    private static final int SLOTS = 6, ENTITY_TICKS = 300, ITEM_TICKS = 6;
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Slot {
        BlockPos at;
        EntityType<?> type;
        Entity subject;
        Vindicator dummy;
        Vec3 start;
        double moved;
        float dummyHealth;
        String error = "";
    }

    private static final class Run {
        ServerLevel level;
        BlockPos origin;
        long started, phaseAt;
        String phase = "entities";
        final List<EntityType<?>> types = new ArrayList<>();
        final List<Item> items = new ArrayList<>();
        int nextType, nextItem;
        final Slot[] slots = new Slot[SLOTS];
        final List<ChunkPos> forced = new ArrayList<>();
        final Map<String, List<String>> entityKinds = new LinkedHashMap<>();
        final Map<String, List<String>> itemKinds = new LinkedHashMap<>();
        Tester tester;
        Vindicator itemDummy;
        Vec3 bench;
        Item item;
        ItemStack held;
        int entitiesBefore, effectsBefore;
        float dummyBefore;
        String itemError = "";
        int heldCountBefore, heldDamageBefore;
        InteractionResult used = InteractionResult.PASS;
    }

    /** The stand-in: a fake player whose swing is always at full strength. */
    static final class Tester extends FakePlayer {
        Tester(ServerLevel level) {
            super(level, new GameProfile(UUID.fromString("0f0e0d0c-0b0a-4908-8706-050403020100"), "[OROR Sweep]"));
        }

        void ready() {
            this.attackStrengthTicker = 200;
        }
    }

    private OrorSweep() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("sweep").requires(s -> s.hasPermission(2))
            .executes(c -> start(c.getSource()))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        BlockPos from = BlockPos.containing(src.getPosition());
        r.origin = from.offset(2600, 0, -2600);
        for (EntityType<?> type : BuiltInRegistries.ENTITY_TYPE) {
            ResourceLocation id = BuiltInRegistries.ENTITY_TYPE.getKey(type);
            if (id.getNamespace().equals(NS)) {
                r.types.add(type);
            }
        }
        for (Item item : BuiltInRegistries.ITEM) {
            if (BuiltInRegistries.ITEM.getKey(item).getNamespace().equals(NS)) {
                r.items.add(item);
            }
        }
        for (int s = 0; s < SLOTS; s++) {
            BlockPos at = r.origin.offset(s * 96, 0, 0);
            for (int dx = -2; dx <= 2; dx++) {
                for (int dz = -2; dz <= 2; dz++) {
                    ChunkPos p = new ChunkPos((at.getX() >> 4) + dx, (at.getZ() >> 4) + dz);
                    if (r.level.setChunkForced(p.x, p.z, true)) {
                        r.forced.add(p);
                    }
                }
            }
        }
        // the item bench, 96 blocks south of the first arena
        BlockPos bench = r.origin.offset(0, 0, 96);
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                ChunkPos p = new ChunkPos((bench.getX() >> 4) + dx, (bench.getZ() >> 4) + dz);
                if (r.level.setChunkForced(p.x, p.z, true)) {
                    r.forced.add(p);
                }
            }
        }
        r.started = r.phaseAt = r.level.getGameTime();
        r.phase = "load";
        run = r;
        LOG.info("SWEEP-START {\"entities\":{},\"items\":{},\"at\":[{},{}]}", r.types.size(), r.items.size(), r.origin.getX(), r.origin.getZ());
        return 1;
    }

    /** A floor of stone 31 across at the ground there, cleared 24 up; returns the standing position. */
    private static BlockPos floor(ServerLevel level, BlockPos at) {
        int y = Math.max(level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, at.getX(), at.getZ()), level.getSeaLevel() + 1);
        for (int dx = -15; dx <= 15; dx++) {
            for (int dz = -15; dz <= 15; dz++) {
                level.setBlock(new BlockPos(at.getX() + dx, y - 1, at.getZ() + dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 24; h++) {
                    BlockPos q = new BlockPos(at.getX() + dx, y + h, at.getZ() + dz);
                    if (!level.getBlockState(q).isAir()) {
                        level.setBlock(q, Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
        }
        return new BlockPos(at.getX(), y, at.getZ());
    }

    private static Vindicator dummy(ServerLevel level, Vec3 at) {
        Vindicator v = EntityType.VINDICATOR.create(level);
        if (v == null) {
            return null;
        }
        v.moveTo(at.x, at.y, at.z, 180F, 0F);
        v.setNoAi(true);
        v.setPersistenceRequired();
        v.getAttribute(Attributes.MAX_HEALTH).setBaseValue(500);
        v.setHealth(500);
        v.addTag("oror_sweep");
        level.addFreshEntity(v);
        return v;
    }

    private static void clear(ServerLevel level, BlockPos at) {
        for (Entity e : level.getEntities((Entity) null, new AABB(at).inflate(48, 64, 48), e -> !(e instanceof Player))) {
            e.discard();
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime();
        long t = now - r.phaseAt;
        try {
            switch (r.phase) {
                case "load" -> {
                    if (t < 60) {
                        return;
                    }
                    for (int s = 0; s < SLOTS; s++) {
                        r.slots[s] = new Slot();
                        r.slots[s].at = floor(r.level, r.origin.offset(s * 96, 0, 0));
                    }
                    r.phase = "entities";
                    r.phaseAt = now;
                    startBatch(r);
                }
                case "entities" -> entityTick(r, t, now);
                case "items" -> itemTick(r, t, now);
                case "print" -> {
                    if (t >= 300) {
                        SweepArms.check(r.level, BlockPos.containing(r.bench).offset(0, 0, -30));
                        finish(r);
                    }
                }
                default -> {
                }
            }
        } catch (Throwable ex) {
            LOG.error("sweep step failed", ex);
            LOG.info("SWEEP-ERROR {\"phase\":\"{}\",\"error\":\"{}\"}", r.phase, esc(ex.toString()));
            finish(r);
        }
    }

    private static void startBatch(Run r) {
        for (Slot s : r.slots) {
            clear(r.level, s.at);
            s.type = null;
            s.subject = null;
            s.error = "";
            if (r.nextType >= r.types.size()) {
                continue;
            }
            s.type = r.types.get(r.nextType++);
            Vec3 c = Vec3.atBottomCenterOf(s.at);
            s.dummy = dummy(r.level, c.add(0, 0, 6));
            try {
                Entity en = s.type.create(r.level);
                if (en != null) {
                    en.moveTo(c.x, c.y, c.z - 6, 0F, 0F);
                    if (en instanceof Mob m) {
                        m.setPersistenceRequired();
                    }
                    if (r.level.addFreshEntity(en)) {
                        s.subject = en;
                        s.start = en.position();
                    }
                }
            } catch (Throwable ex) {
                s.error = ex.toString();
            }
            s.moved = 0;
            s.dummyHealth = s.dummy == null ? 0 : s.dummy.getHealth();
        }
    }

    private static void entityTick(Run r, long t, long now) {
        for (Slot s : r.slots) {
            if (s.subject != null && s.subject.isAlive()) {
                s.moved = Math.max(s.moved, s.subject.position().distanceTo(s.start));
                if (t % 20 == 1 && s.subject instanceof Mob m && s.dummy != null && s.dummy.isAlive()) {
                    m.setTarget(s.dummy);
                }
            }
        }
        if (t < ENTITY_TICKS) {
            return;
        }
        for (Slot s : r.slots) {
            if (s.type == null) {
                continue;
            }
            String id = BuiltInRegistries.ENTITY_TYPE.getKey(s.type).getPath();
            boolean living = s.subject instanceof LivingEntity;
            float dealt = s.dummy == null ? 0 : s.dummyHealth - (s.dummy.isAlive() ? s.dummy.getHealth() : 0);
            String kind = s.subject == null ? "not-spawned" : !living ? "not-living" : !s.subject.isAlive() ? "died"
                : dealt > 0.5F ? "fought" : s.moved > 1.0 ? "moved-no-hit" : "idle";
            r.entityKinds.computeIfAbsent(kind, k -> new ArrayList<>()).add(id);
            LOG.info(String.format(Locale.ROOT, "SWEEP-ENTITY {\"id\":\"%s\",\"kind\":\"%s\",\"alive\":%b,\"health\":%.2f,\"moved\":%.1f,"
                    + "\"dealt\":%.1f,\"dummyAlive\":%b,\"error\":\"%s\"}", id, kind, s.subject != null && s.subject.isAlive(),
                living && s.subject.isAlive() ? ((LivingEntity) s.subject).getHealth() / ((LivingEntity) s.subject).getMaxHealth() : 0F,
                s.moved, dealt, s.dummy != null && s.dummy.isAlive(), esc(s.error)));
        }
        if (r.nextType < r.types.size()) {
            r.phaseAt = now;
            startBatch(r);
            return;
        }
        for (Slot s : r.slots) {
            clear(r.level, s.at);
        }
        // on to the items: the bench, the stand-in and his vindicator
        BlockPos bench = floor(r.level, r.origin.offset(0, 0, 96));
        r.tester = new Tester(r.level);
        r.bench = new Vec3(bench.getX() + 0.5, bench.getY(), bench.getZ() + 0.5);
        r.tester.moveTo(r.bench.x, r.bench.y, r.bench.z, 0F, 0F);
        r.itemDummy = dummy(r.level, Vec3.atBottomCenterOf(bench).add(0, 0, 2.2));
        kit(r);
        r.phase = "items";
        r.phaseAt = now;
    }

    /** The starter kit given to the stand-in, and its rounds used once. */
    private static void kit(Run r) {
        try {
            List<String> given = jp.oror.reborn.StarterKit.give(r.tester);
            StringBuilder inv = new StringBuilder();
            for (int i = 0; i < r.tester.getInventory().getContainerSize(); i++) {
                ItemStack st = r.tester.getInventory().getItem(i);
                if (!st.isEmpty()) {
                    inv.append(inv.length() > 0 ? "," : "").append("\"").append(BuiltInRegistries.ITEM.getKey(st.getItem())).append("x")
                        .append(st.getCount()).append("\"");
                }
            }
            Item rounds = BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("superbwarfare", "handgun_ammo"));
            int before = -1, after = -1;
            String used = "";
            for (int i = 0; i < r.tester.getInventory().getContainerSize(); i++) {
                ItemStack st = r.tester.getInventory().getItem(i);
                if (st.is(rounds)) {
                    before = st.getCount();
                    r.tester.setItemInHand(InteractionHand.MAIN_HAND, st);
                    used = st.use(r.level, r.tester, InteractionHand.MAIN_HAND).getResult().toString();
                    after = r.tester.getMainHandItem().getCount();
                    break;
                }
            }
            LOG.info(String.format(Locale.ROOT, "SWEEP-KIT {\"given\":\"%s\",\"inventory\":[%s],\"armour\":[\"%s\",\"%s\",\"%s\",\"%s\"],"
                    + "\"roundsBefore\":%d,\"roundsUse\":\"%s\",\"roundsAfter\":%d}", given, inv,
                BuiltInRegistries.ITEM.getKey(r.tester.getItemBySlot(EquipmentSlot.HEAD).getItem()),
                BuiltInRegistries.ITEM.getKey(r.tester.getItemBySlot(EquipmentSlot.CHEST).getItem()),
                BuiltInRegistries.ITEM.getKey(r.tester.getItemBySlot(EquipmentSlot.LEGS).getItem()),
                BuiltInRegistries.ITEM.getKey(r.tester.getItemBySlot(EquipmentSlot.FEET).getItem()), before, used, after));
        } catch (Throwable ex) {
            LOG.info("SWEEP-KIT {\"error\":\"{}\"}", esc(ex.toString()));
        }
        r.tester.getInventory().clearContent();
    }

    private static void itemTick(Run r, long t, long now) {
        Tester p = r.tester;
        if (r.itemDummy == null || !r.itemDummy.isAlive()) {
            r.itemDummy = dummy(r.level, p.position().add(0, 0, 2.2));
        }
        long step = t % ITEM_TICKS;
        if (step == 0) {
            if (r.item != null) {
                report(r);
            }
            if (r.nextItem >= r.items.size()) {
                // the arms a right-click does not show: the guns fired, the Blueprinter scanning and printing a house
                try {
                    p.getInventory().clearContent();
                    SweepArms.run(r.level, p, BlockPos.containing(r.bench).offset(0, 0, -30));
                } catch (Throwable ex) {
                    LOG.info("SWEEP-ARMS {\"error\":\"{}\"}", esc(ex.toString()));
                }
                r.phase = "print";
                r.phaseAt = now;
                return;
            }
            r.item = r.items.get(r.nextItem++);
            r.itemError = "";
            p.getInventory().clearContent();
            p.moveTo(r.bench.x, r.bench.y, r.bench.z, 0F, 0F);
            p.setDeltaMovement(Vec3.ZERO);
            p.removeAllEffects();
            p.setHealth(p.getMaxHealth());
            p.getCooldowns().removeCooldown(r.item);
            ItemStack stack = new ItemStack(r.item, Math.min(16, new ItemStack(r.item).getMaxStackSize()));
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            r.held = stack;
            r.heldCountBefore = stack.getCount();
            r.heldDamageBefore = stack.getDamageValue();
            r.dummyBefore = r.itemDummy.getHealth();
            r.effectsBefore = p.getActiveEffects().size();
            r.entitiesBefore = r.level.getEntities((Entity) null, p.getBoundingBox().inflate(32), en -> en != r.itemDummy).size();
            r.used = InteractionResult.PASS;
            try {
                if (r.item instanceof SpawnEggItem) {
                    BlockPos below = p.blockPosition().below().offset(3, 0, 0);
                    r.used = stack.useOn(new UseOnContext(p, InteractionHand.MAIN_HAND,
                        new BlockHitResult(Vec3.atCenterOf(below).add(0, 0.5, 0), Direction.UP, below, false)));
                } else if (r.item instanceof ArmorItem armor) {
                    p.setItemSlot(armor.getEquipmentSlot(), stack.copy());
                    r.used = InteractionResult.SUCCESS;
                } else {
                    r.used = stack.use(r.level, p, InteractionHand.MAIN_HAND).getResult();
                    if (r.used == InteractionResult.PASS || r.used == InteractionResult.FAIL) {
                        BlockPos below = p.blockPosition().below();
                        InteractionResult on = p.getMainHandItem().useOn(new UseOnContext(p, InteractionHand.MAIN_HAND,
                            new BlockHitResult(Vec3.atCenterOf(below).add(0, 0.5, 0), Direction.UP, below, false)));
                        if (on.consumesAction()) {
                            r.used = on;
                        }
                    }
                }
            } catch (Throwable ex) {
                r.itemError = ex.toString();
            }
        } else if (step == 2) {
            // held to charge: let go now; then carried a while, and swung
            try {
                ItemStack now2 = p.getMainHandItem();
                if (p.isUsingItem()) {
                    int dur = now2.getUseDuration(p);
                    now2.releaseUsing(r.level, p, Math.max(0, dur - 30));
                    p.stopUsingItem();
                }
                for (int i = 0; i < 20; i++) {
                    p.getInventory().tick();
                    NeoForge.EVENT_BUS.post(new PlayerTickEvent.Pre(p));
                    NeoForge.EVENT_BUS.post(new PlayerTickEvent.Post(p));
                }
                p.ready();
                p.attack(r.itemDummy);
            } catch (Throwable ex) {
                if (r.itemError.isEmpty()) {
                    r.itemError = ex.toString();
                }
            }
        }
    }

    private static void report(Run r) {
        Tester p = r.tester;
        String id = BuiltInRegistries.ITEM.getKey(r.item).getPath();
        int entities = r.level.getEntities((Entity) null, p.getBoundingBox().inflate(32), en -> en != r.itemDummy).size() - r.entitiesBefore;
        float dealt = r.itemDummy == null ? 0 : r.dummyBefore - (r.itemDummy.isAlive() ? r.itemDummy.getHealth() : 0);
        int effects = p.getActiveEffects().size() - r.effectsBefore;
        boolean cooldown = p.getCooldowns().isOnCooldown(r.item);
        ItemStack now = p.getMainHandItem();
        boolean spent = now.isEmpty() || now.getItem() != r.item || now.getCount() != r.heldCountBefore || now.getDamageValue() != r.heldDamageBefore;
        boolean worn = r.item instanceof ArmorItem;
        float selfHurt = p.getMaxHealth() - p.getHealth();
        String kind = !r.itemError.isEmpty() ? "error"
            : entities > 0 || effects > 0 || cooldown || spent || worn || r.used.consumesAction() ? "did-something"
            : dealt > 1.5F ? "melee-only" : "no-visible-effect";
        r.itemKinds.computeIfAbsent(kind, k -> new ArrayList<>()).add(id);
        LOG.info(String.format(Locale.ROOT, "SWEEP-ITEM {\"id\":\"%s\",\"kind\":\"%s\",\"use\":\"%s\",\"spawned\":%d,\"dealt\":%.1f,\"effects\":%d,"
                + "\"cooldown\":%b,\"spent\":%b,\"selfHurt\":%.1f,\"error\":\"%s\"}", id, kind, r.used, entities, dealt, effects, cooldown, spent,
            selfHurt, esc(r.itemError)));
        // what it spawned goes (its shots, its summons), and the vindicator is made whole
        for (Entity en : r.level.getEntities((Entity) null, p.getBoundingBox().inflate(32), en -> en != r.itemDummy && !(en instanceof Player))) {
            en.discard();
        }
        if (r.itemDummy != null && r.itemDummy.isAlive()) {
            r.itemDummy.setHealth(r.itemDummy.getMaxHealth());
        }
        for (EquipmentSlot slot : EquipmentSlot.values()) {
            p.setItemSlot(slot, ItemStack.EMPTY);
        }
    }

    private static void finish(Run r) {
        StringBuilder b = new StringBuilder();
        for (Map<String, List<String>> m : List.of(r.entityKinds, r.itemKinds)) {
            b.append(b.length() > 0 ? "," : "").append(m == r.entityKinds ? "\"entities\":{" : "\"items\":{");
            int i = 0;
            for (Map.Entry<String, List<String>> en : m.entrySet()) {
                b.append(i++ > 0 ? "," : "").append("\"").append(en.getKey()).append("\":{\"n\":").append(en.getValue().size());
                if (!en.getKey().equals("fought") && !en.getKey().equals("did-something")) {
                    b.append(",\"ids\":[").append(String.join(",", en.getValue().stream().map(s -> "\"" + s + "\"").toList())).append("]");
                }
                b.append("}");
            }
            b.append("}");
        }
        LOG.info("SWEEP-RESULT {{},\"seconds\":{}}", b, (r.level.getGameTime() - r.started) / 20);
        if (r.slots[0] != null) {
            for (Slot s : r.slots) {
                clear(r.level, s.at);
            }
        }
        for (ChunkPos p : r.forced) {
            r.level.setChunkForced(p.x, p.z, false);
        }
        run = null;
        resultLogged = true;
    }

    private static String esc(String s) {
        return s == null ? "" : s.replace("\\", "/").replace("\"", "'").replace("\n", " ");
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
