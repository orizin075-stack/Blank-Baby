package jp.oror.reborn.client;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.Map.Entry;
import jp.oror.reborn.AdventureContent;
import jp.oror.reborn.AdventureGameTests;
import jp.oror.reborn.ArsenalGameTests;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.CharacterSpec;
import jp.oror.reborn.CivilizationGameTests;
import jp.oror.reborn.CompatibilityGameTests;
import jp.oror.reborn.EquipmentGameTests;
import jp.oror.reborn.ExtensionGameTests;
import jp.oror.reborn.FusionGameTests;
import jp.oror.reborn.MindGameTests;
import jp.oror.reborn.MobLevels;
import jp.oror.reborn.OrorReborn;
import jp.oror.reborn.PowerGameTests;
import jp.oror.reborn.ProgressionGameTests;
import jp.oror.reborn.RebornGameTests;
import jp.oror.reborn.RegressionGameTests;
import jp.oror.reborn.RelicGameTests;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestBatchFactory;
import net.minecraft.gametest.framework.GameTestInfo;
import net.minecraft.gametest.framework.GameTestRegistry;
import net.minecraft.gametest.framework.GameTestRunner;
import net.minecraft.gametest.framework.GameTestTicker;
import net.minecraft.gametest.framework.MultipleTestTracker;
import net.minecraft.gametest.framework.TestFunction;
import net.minecraft.gametest.framework.GameTestRunner.Builder;
import net.minecraft.gametest.framework.GameTestRunner.StructureSpawner;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.TickEvent.ClientTickEvent;
import net.minecraftforge.gametest.GameTestHooks;
import org.lwjgl.opengl.GL11;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    value = {Dist.CLIENT}
)
public final class ClientSmoke {
    private static final List<Class<?>> TEST_CLASSES = List.of(
        RebornGameTests.class,
        RegressionGameTests.class,
        AdventureGameTests.class,
        RelicGameTests.class,
        MindGameTests.class,
        ProgressionGameTests.class,
        CompatibilityGameTests.class,
        ExtensionGameTests.class,
        ArsenalGameTests.class,
        CivilizationGameTests.class,
        PowerGameTests.class,
        FusionGameTests.class,
        EquipmentGameTests.class
    );
    private static final Set<Long> testChunks = new HashSet<>();
    private static final List<SupremeEntity> serverActors = new ArrayList<>();
    private static volatile List<UUID> actorIds = List.of();
    private static volatile boolean testsPassed;
    private static volatile boolean ready;
    private static volatile int requestedMotion;
    private static volatile int appliedMotion;
    private static volatile int confirmedForm = -1;
    private static volatile UUID tree;
    private static boolean opened;
    private static boolean started;
    private static boolean firstForm;
    private static boolean secondForm;
    private static boolean shot;
    private static int ticks;
    private static int diagnostic;
    private static int verifiedMotion;
    private static long motionDeadline;
    private static long formDeadline;
    private static GameTestRunner runner;
    private static MultipleTestTracker tracker;

    @SubscribeEvent
    public static void tick(ClientTickEvent event) {
        if (event.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        if (Boolean.getBoolean("oror.smoke")) {
            Minecraft mc = Minecraft.getInstance();
            mc.options.pauseOnLostFocus = false;
            SmokeScreens.acknowledge(mc);
            if (++diagnostic % 100 == 0) {
                System.out.println("[OROR_SMOKE] SCREEN " + (mc.screen == null ? "none" : mc.screen.getClass().getSimpleName()));
            }

            if (!opened && mc.screen instanceof TitleScreen) {
                opened = true;
                System.out.println("[OROR_SMOKE] TITLE_READY roster=" + CharacterSpec.ALL.size());
                String world = System.getProperty("oror.smokeWorld", "");
                if (world.isEmpty()) {
                    mc.stop();
                    return;
                }

                mc.createWorldOpenFlows().openWorld(world, mc::stop);
            }

            if (mc.player != null && mc.level != null && mc.getSingleplayerServer() != null) {
                if (!started) {
                    started = true;
                    mc.getSingleplayerServer().execute(() -> startTests(mc));
                }

                if (testsPassed && !ready) {
                    testsPassed = false;
                    mc.getSingleplayerServer().execute(() -> scene(mc));
                }

                if (ready) {
                    if (ticks != 0 || !clientActors(mc).stream().noneMatch(e -> e.getUUID().equals(tree))) {
                        ticks++;
                        verifyMotions(mc);
                        if (ticks == 100) {
                            formDeadline = System.currentTimeMillis() + 60000L;
                            mc.getSingleplayerServer().execute(() -> setTreeForm(1));
                        }

                        SupremeEntity found = clientActors(mc).stream().filter(e -> e.getUUID().equals(tree)).findFirst().orElse(null);
                        if (ticks >= 160 && found != null) {
                            float height = found.getDimensions(found.getPose()).height();
                            if (!firstForm && confirmedForm == 1 && found.form() == 1 && Math.abs(found.getBbHeight() - height) < 0.001F) {
                                firstForm = true;
                                System.out.println("[OROR_SMOKE] FORM=1 CLIENT_HEIGHT=" + height + " PASS");
                                mc.getSingleplayerServer().execute(() -> setTreeForm(0));
                            } else if (firstForm && !secondForm && confirmedForm == 0 && found.form() == 0 && Math.abs(found.getBbHeight() - height) < 0.001F) {
                                secondForm = true;
                                System.out.println("[OROR_SMOKE] FORM=0 CLIENT_HEIGHT=" + height + " PASS");
                            }
                        }

                        if (formDeadline > 0L && !secondForm && System.currentTimeMillis() > formDeadline) {
                            throw new IllegalStateException("Client form sync timed out");
                        } else {
                            if (ticks >= 300 && secondForm && !shot) {
                                shot = true;
                                Screenshot.grab(
                                    mc.gameDirectory, mc.getMainRenderTarget(), msg -> System.out.println("[OROR_SMOKE] SCREENSHOT " + msg.getString())
                                );
                            }

                            if (ticks >= 500 && secondForm && verifiedMotion == 16) {
                                System.out.println("[OROR_SMOKE] COMPLETE clientTicks=" + ticks + " gl_error=" + GL11.glGetError());
                                mc.stop();
                            }
                        }
                    }
                }
            }
        }
    }

    private static List<SupremeEntity> clientActors(Minecraft mc) {
        ArrayList<SupremeEntity> result = new ArrayList<>();

        for (Entity e : mc.level.entitiesForRendering()) {
            if (e instanceof SupremeEntity) {
                SupremeEntity b = (SupremeEntity)e;
                if (actorIds.contains(b.getUUID())) {
                    result.add(b);
                }
            }
        }

        return result;
    }

    private static void startTests(Minecraft mc) {
        ServerLevel sl = mc.getSingleplayerServer().overworld();
        HashSet<String> ownNames = new HashSet<>();

        for (Class<?> clazz : TEST_CLASSES) {
            for (Method method : clazz.getDeclaredMethods()) {
                if (method.isAnnotationPresent(GameTest.class)) {
                    ownNames.add(method.getName());
                    if (GameTestRegistry.getAllTestFunctions().stream().noneMatch(f -> f.testName().endsWith(method.getName()))) {
                        GameTestRegistry.register(method, Set.of());
                    }
                }
            }
        }

        String filter = System.getProperty("oror.testFilter", "");
        List<TestFunction> functions = GameTestRegistry.getAllTestFunctions()
            .stream()
            .filter(f -> ownNames.stream().anyMatch(n -> f.testName().endsWith(n)))
            .filter(f -> filter.isEmpty() || f.testName().matches(filter))
            .toList();
        if (!functions.isEmpty() && (!filter.isEmpty() || functions.size() == ownNames.size())) {
            ServerPlayer player = (ServerPlayer)sl.getServer().getPlayerList().getPlayers().getFirst();
            player.setGameMode(GameType.CREATIVE);
            player.connection.teleport(670.0, 100.0, 670.0, 0.0F, 90.0F);
            runner = Builder.fromBatches(GameTestBatchFactory.fromTestFunction(functions, sl), sl)
                .newStructureSpawner(new ClientSmoke.IsolatedSpawner())
                .build();
            tracker = new MultipleTestTracker(runner.getTestInfos());
            System.out.println("[OROR_RELEASE_TESTS] START total=" + tracker.getTotalCount());
            runner.start();
        } else {
            throw new IllegalStateException("Incomplete own test registry: " + functions.size() + " / " + ownNames.size());
        }
    }

    private static void scene(Minecraft mc) {
        ServerLevel sl = mc.getSingleplayerServer().overworld();
        ArrayList<Entity> stale = new ArrayList<>();
        sl.getAllEntities().forEach(stale::add);

        for (Entity e : stale) {
            if (e.getX() > 500.0 && (e instanceof LivingEntity && !(e instanceof Player) || e instanceof Projectile)) {
                e.discard();
            }
        }

        for (long packed : testChunks) {
            ChunkPos pos = new ChunkPos(packed);
            sl.setChunkForced(pos.x, pos.z, false);
        }

        testChunks.clear();
        int x = 300;
        int z = 300;
        int y = 64;

        for (int cx = 17; cx <= 20; cx++) {
            for (int cz = 17; cz <= 24; cz++) {
                sl.setChunkForced(cx, cz, true);
            }
        }

        for (int dx = -25; dx <= 25; dx++) {
            for (int dz = -20; dz <= 90; dz++) {
                sl.setBlock(new BlockPos(x + dx, y, z + dz), Blocks.STONE.defaultBlockState(), 2);
            }
        }

        int index = 0;

        for (CharacterSpec spec : CharacterSpec.ALL
            .values()
            .stream()
            .sorted(
                Comparator.comparingInt(
                    c -> List.of("innocence", "brutality", "cursed_love", "relentless_research", "forbidden_arcana", "fallen_savior", "sweet_pact", "yggdrasil")
                                .contains(c.id)
                            ? 0
                            : 1
                )
            )
            .toList()) {
            SupremeEntity actor = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(spec.id).get()).create(sl);
            actor.moveTo((double)(x + (index % 5 - 2) * 9), (double)(y + 1), (double)(z + index / 5 * 9), 180.0F, 0.0F);
            actor.setNoAi(true);
            actor.setPersistenceRequired();
            if (!sl.addFreshEntity(actor)) {
                throw new IllegalStateException("Scene actor failed: " + spec.id);
            }

            serverActors.add(actor);
            if (spec.id.equals("yggdrasil")) {
                tree = actor.getUUID();
            }

            index++;
        }

        actorIds = serverActors.stream().<UUID>map(Entity::getUUID).toList();

        for (int rank = 1; rank <= 6; rank++) {
            Villager villager = (Villager)EntityType.VILLAGER.create(sl);
            villager.moveTo((double)(x - 22), (double)(y + 1), (double)(z + rank * 4), 180.0F, 0.0F);
            sl.addFreshEntity(villager);
            MobLevels.set(villager, rank);
            MobLevels.refresh(villager);
            villager.setNoAi(true);
            villager.setCustomName(Component.literal("装備 Lv." + rank));
            villager.setCustomNameVisible(true);
        }

        ServerPlayer player = (ServerPlayer)sl.getServer().getPlayerList().getPlayers().getFirst();
        player.setGameMode(GameType.CREATIVE);
        player.connection.teleport((double)x, (double)(y + 9), (double)(z - 18), 0.0F, 14.0F);

        for (String id : List.of(
            "kokuhaku_weapon", "elseria_focus", "tenki_charm", "innocence_legend", "miyohime_legend", "mels_weapon", "hephaistos_focus", "sweet_pact_legend"
        )) {
            player.getInventory().add(((Item)CharacterRelics.ITEMS.get(id).get()).getDefaultInstance());
        }

        player.getInventory().add(((Item)AdventureContent.GUIDE.get()).getDefaultInstance());
        player.setItemSlot(EquipmentSlot.CHEST, ((ArmorItem)AdventureContent.COAT.get()).getDefaultInstance());
        player.setItemSlot(EquipmentSlot.FEET, ((ArmorItem)AdventureContent.BOOTS.get()).getDefaultInstance());
        player.setItemInHand(InteractionHand.OFF_HAND, ((Item)AdventureContent.TALISMAN.get()).getDefaultInstance());
        System.out.println("[OROR_SMOKE] SPAWNED " + index + " combat=false");
        ready = true;
    }

    private static void setTreeForm(int form) {
        for (SupremeEntity actor : serverActors) {
            if (actor.getUUID().equals(tree)) {
                actor.setForm(form);
                confirmedForm = form;
            }
        }
    }

    private static void verifyMotions(Minecraft mc) {
        List<SupremeEntity> actors = clientActors(mc);
        if (actors.size() != 41) {
            if (ticks > 1200) {
                throw new IllegalStateException("Only " + actors.size() + " / 41 actors tracked");
            }
        } else {
            if (requestedMotion > verifiedMotion && appliedMotion == requestedMotion) {
                boolean synced = actors.stream()
                    .allMatch(a -> a.motion() == requestedMotion && a.motionProgress(0.0F) >= 0.05F && a.motionProgress(0.0F) < 0.95F);
                if (!synced) {
                    if (System.currentTimeMillis() > motionDeadline) {
                        throw new IllegalStateException(
                            "Motion sync timed out: "
                                + requestedMotion
                                + " paused="
                                + mc.isPaused()
                                + " frozen="
                                + mc.level.tickRateManager().isFrozen()
                                + " states="
                                + actors.stream().map(a -> a.spec.id + ":" + a.motion() + ":" + a.motionProgress(0.0F)).toList()
                        );
                    }

                    return;
                }

                if (requestedMotion == 1) {
                    Collection<String> packs = mc.getResourcePackRepository().getSelectedIds();

                    for (String folder : List.of("mowzie_182", "sbw_0892", "jeg_182", "macabre_091_atlas", "geomancy_110_atlas", "golems_guide_3143")) {
                        if (!packs.contains("mod/oror_supreme_bosses:resourcepacks/" + folder)) {
                            throw new IllegalStateException("Missing exact-version animation pack " + folder);
                        }
                    }

                    System.out.println("[OROR_VISUAL_PACKS] PASS packs=6");
                    int itemModels = 0;

                    for (ResourceLocation key : BuiltInRegistries.ITEM.keySet()) {
                        if (key.getNamespace().equals("oror_supreme_bosses")) {
                            ItemStack stack = ((Item)BuiltInRegistries.ITEM.get(key)).getDefaultInstance();
                            if (mc.getItemRenderer().getModel(stack, mc.level, null, 0) == mc.getModelManager().getMissingModel()) {
                                throw new IllegalStateException("Missing native item model " + key);
                            }

                            itemModels++;
                        }
                    }

                    for (int layer = 1; layer <= 2; layer++) {
                        if (mc.getResourceManager()
                            .getResource(
                                new ResourceLocation("oror_supreme_bosses", "textures/models/armor/dragon_furnace_layer_" + layer + ".png")
                            )
                            .isEmpty()) {
                            throw new IllegalStateException("Missing armor layer " + layer);
                        }
                    }

                    System.out.println("[OROR_VISUAL_ITEMS] PASS models=" + itemModels + " armor_layers=2");
                }

                for (SupremeEntity actor : actors) {
                    if (!(mc.getEntityRenderDispatcher().getRenderer(actor) instanceof CharacterRenderer renderer)) {
                        throw new IllegalStateException("Missing renderer " + actor.spec.id);
                    }

                    if (mc.getResourceManager().getResource(renderer.getTextureLocation(actor)).isEmpty()) {
                        throw new IllegalStateException("Missing texture " + actor.spec.id);
                    }

                    CharacterModel model = (CharacterModel)renderer.getModel();
                    model.setupAnim(actor, 1.0F, 0.5F, (float)actor.tickCount + 0.5F, 10.0F, 5.0F);
                    model.root
                        .getAllParts()
                        .forEach(
                            p -> {
                                if (!Float.isFinite(p.x)
                                    || !Float.isFinite(p.y)
                                    || !Float.isFinite(p.z)
                                    || !Float.isFinite(p.xRot)
                                    || !Float.isFinite(p.yRot)
                                    || !Float.isFinite(p.zRot)
                                    || !Float.isFinite(p.xScale)
                                    || p.xScale <= 0.0F
                                    || !Float.isFinite(p.yScale)
                                    || p.yScale <= 0.0F
                                    || !Float.isFinite(p.zScale)
                                    || p.zScale <= 0.0F) {
                                    throw new IllegalStateException("Invalid pose " + actor.spec.id + " " + requestedMotion);
                                }
                            }
                        );
                }

                verifiedMotion = requestedMotion;
                System.out.println("[OROR_VISUAL_MOTION] PASS motion=" + verifiedMotion + " actors=41 textures=41 finite_models=41");
            }

            if (requestedMotion == verifiedMotion && verifiedMotion < 16 && ticks % 12 == 0) {
                motionDeadline = System.currentTimeMillis() + 60000L;
                requestedMotion++;
            }
        }
    }

    @SubscribeEvent
    public static void serverTick(net.minecraftforge.event.TickEvent.ServerTickEvent event) {
        if (event.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        if (Boolean.getBoolean("oror.smoke")) {
            if (runner != null && tracker != null) {
                if (!GameTestHooks.isGametestEnabled()) {
                    GameTestTicker.SINGLETON.tick();
                }

                if (tracker.isDone()) {
                    System.out.println("[OROR_RELEASE_TESTS] COMPLETE total=" + tracker.getTotalCount() + " failed=" + tracker.getFailedRequiredCount());

                    for (GameTestInfo test : runner.getTestInfos()) {
                        System.out.println("[OROR_RELEASE_TEST] " + test.getTestName() + " " + (test.hasSucceeded() ? "PASS" : "FAIL " + test.getError()));
                    }

                    boolean success = !tracker.hasFailedRequired();
                    runner.stop();
                    runner = null;
                    tracker = null;
                    if (!success) {
                        throw new IllegalStateException("Release JAR GameTests failed");
                    }

                    writeRegistryAudit(event.getServer());
                    testsPassed = true;
                }
            }

            if (ready && requestedMotion > appliedMotion) {
                int next = requestedMotion;

                for (SupremeEntity actor : serverActors) {
                    if (!actor.isAlive()) {
                        throw new IllegalStateException(
                            "Scene actor invalid "
                                + actor.spec.id
                                + " health="
                                + actor.getHealth()
                                + " removed="
                                + actor.getRemovalReason()
                                + " live="
                                + (event.getServer().overworld().getEntity(actor.getUUID()) == actor)
                        );
                    }

                    actor.motion(next, 200);
                }

                appliedMotion = next;
                System.out.println("[OROR_MOTION_SERVER] applied=" + next + " actors=" + serverActors.size());
            }
        }
    }

    private static void writeRegistryAudit(MinecraftServer server) {
        JsonObject result = new JsonObject();

        for (Entry<String, Set<ResourceLocation>> entry : Map.of(
                "items", BuiltInRegistries.ITEM.keySet(), "entity_types", BuiltInRegistries.ENTITY_TYPE.keySet()
            )
            .entrySet()) {
            JsonArray rows = new JsonArray();
            entry.getValue().stream().sorted().forEach(key -> rows.add(key.toString()));
            result.add(entry.getKey(), rows);
        }

        JsonArray dimensions = new JsonArray();
        server.levelKeys().stream().map(k -> k.location().toString()).sorted().forEach(dimensions::add);
        result.add("dimensions", dimensions);
        JsonArray recipes = new JsonArray();
        server.getRecipeManager().getRecipeIds().map(Object::toString).sorted().forEach(recipes::add);
        result.add("recipes", recipes);

        try {
            Files.writeString(Path.of("oror_registry_audit.json"), new GsonBuilder().setPrettyPrinting().create().toJson(result));
        } catch (IOException var5) {
            throw new IllegalStateException(var5);
        }
    }

    private static final class IsolatedSpawner implements StructureSpawner {
        private int index;

        public Optional<GameTestInfo> spawnStructure(GameTestInfo test) {
            ServerLevel sl = test.getLevel();
            BlockPos at = new BlockPos(600 + this.index % 4 * 256, 65, 600 + this.index / 4 * 256);
            this.index++;

            for (int x = at.getX() - 8 >> 4; x <= at.getX() + 170 >> 4; x++) {
                for (int z = at.getZ() - 8 >> 4; z <= at.getZ() + 48 >> 4; z++) {
                    sl.setChunkForced(x, z, true);
                    ClientSmoke.testChunks.add(ChunkPos.asLong(x, z));
                }
            }

            test.setNorthWestCorner(at);
            test.prepareTestStructure();
            return Optional.of(test);
        }

        public void onBatchStart(ServerLevel level) {
        }
    }
}
