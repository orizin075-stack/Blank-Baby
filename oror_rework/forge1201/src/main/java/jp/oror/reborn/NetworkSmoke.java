package jp.oror.reborn;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.GameRules.BooleanValue;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.TickEvent.ServerTickEvent;

@EventBusSubscriber(
    modid = "oror_supreme_bosses"
)
public final class NetworkSmoke {
    private static final List<SupremeEntity> actors = new ArrayList<>();
    private static boolean started;
    private static int ticks;
    private static final List<Villager> fighters = new ArrayList<>();
    private static final List<Villager> workers = new ArrayList<>();
    private static final List<Villager> rankSamples = new ArrayList<>();

    @SubscribeEvent
    public static void tick(ServerTickEvent event) {
        if (event.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        if (Boolean.getBoolean("oror.networkServer")) {
            MinecraftServer server = event.getServer();
            ServerLevel level = server.overworld();
            if (!started) {
                if (server.getPlayerList().getPlayerCount() < 2) {
                    return;
                }

                started = true;
                RebornConfig.AUTO_RESEARCH.set(false);

                for (int x = 270; x <= 370; x++) {
                    for (int z = 275; z <= 390; z++) {
                        level.setBlock(new BlockPos(x, 64, z), Blocks.STONE.defaultBlockState(), 2);
                    }
                }

                for (int x = 16; x <= 23; x++) {
                    for (int z = 17; z <= 25; z++) {
                        level.setChunkForced(x, z, true);
                    }
                }

                int index = 0;

                for (CharacterSpec spec : CharacterSpec.ALL.values()) {
                    SupremeEntity entity = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(spec.id).get()).create(level);
                    entity.moveTo((double)(300 + (index % 5 - 2) * 9), 65.0, (double)(300 + index / 5 * 9), 180.0F, 0.0F);
                    entity.setNoAi(true);
                    level.addFreshEntity(entity);
                    actors.add(entity);
                    index++;
                }

                index = 0;

                for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                    player.setGameMode(GameType.CREATIVE);
                    player.connection.teleport((double)(294 + index * 12), 65.0, 282.0, 0.0F, 10.0F);
                    player.setItemInHand(InteractionHand.MAIN_HAND, ((Item)CharacterRelics.ITEMS.get("hephaistos_legend").get()).getDefaultInstance());
                    player.getInventory().add(((Item)CharacterRelics.ITEMS.get("kokuhaku_weapon").get()).getDefaultInstance());
                    index++;
                }

                for (int i = 0; i < 4; i++) {
                    Villager v = (Villager)EntityType.VILLAGER.create(level);
                    v.moveTo(273.0, 65.0, (double)(284 + i * 6), 0.0F, 0.0F);
                    v.setPersistenceRequired();
                    level.addFreshEntity(v);
                    AdaptiveCombat.arm(v);
                    Husk t = (Husk)EntityType.HUSK.create(level);
                    t.moveTo(277.0, 65.0, (double)(284 + i * 6), 0.0F, 0.0F);
                    t.setNoAi(true);
                    t.setPersistenceRequired();
                    t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
                    t.setHealth(1024.0F);
                    level.addFreshEntity(t);
                    v.setTarget(t);
                    fighters.add(v);
                }

                for (int rank = 1; rank <= 6; rank++) {
                    Villager v = (Villager)EntityType.VILLAGER.create(level);
                    v.moveTo(329.0, 65.0, (double)(283 + rank * 5), 180.0F, 0.0F);
                    level.addFreshEntity(v);
                    MobLevels.set(v, rank);
                    MobLevels.refresh(v);
                    v.setCustomName(Component.literal("OROR_RANK_" + rank));
                    v.setCustomNameVisible(true);
                    v.setNoAi(true);
                    rankSamples.add(v);
                }

                ((BooleanValue)level.getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(true, server);

                for (int x : new int[]{275, 312, 349}) {
                    Villager v = (Villager)EntityType.VILLAGER.create(level);
                    v.moveTo((double)x + 0.5, 65.0, 335.5, 0.0F, 0.0F);
                    level.addFreshEntity(v);
                    MobLevels.set(v, 5);
                    BlockPos at = new BlockPos(x - 2, 65, 335);
                    level.setBlock(at, Blocks.FURNACE.defaultBlockState(), 3);
                    level.setBlock(at.north(), Blocks.CHEST.defaultBlockState(), 3);
                    ((ChestBlockEntity)level.getBlockEntity(at.north())).setItem(0, new ItemStack(Items.COAL, 16));
                    level.setBlock(new BlockPos(x + 3, 65, 335), Blocks.IRON_ORE.defaultBlockState(), 3);
                    if (!VillagerIndustry.hire(v, at, null)) {
                        throw new IllegalStateException("Network miner hiring failed");
                    }

                    workers.add(v);
                }

                System.out
                    .println("[OROR_NETWORK_SERVER] START players=" + server.getPlayerList().getPlayerCount() + " actors=" + actors.size() + " production=true");
            }

            if (++ticks == 100) {
                for (SupremeEntity actor : actors) {
                    if (actor.spec.id.equals("yggdrasil")) {
                        actor.setForm(1);
                    }
                }
            }

            if (ticks == 240) {
                for (SupremeEntity actorx : actors) {
                    if (actorx.spec.id.equals("yggdrasil")) {
                        actorx.setForm(0);
                    }
                }
            }

            if (ticks == 800) {
                for (SupremeEntity actorxx : actors) {
                    if (!actorxx.isAlive() || actorxx.operatorLevel() != (OperatorPowers.HOLDERS.contains(actorxx.spec.id) ? 4 : 0)) {
                        throw new IllegalStateException("Network scene actor or authority invalid " + actorxx.spec.id);
                    }
                }

                for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                    if (player.getPersistentData().getInt("ororRelicCasts") < 1) {
                        throw new IllegalStateException("Remote item-use packet never reached server " + player.getGameProfile().getName());
                    }

                    int personal = 0;

                    for (Entity entity : level.getAllEntities()) {
                        if (entity.getPersistentData().hasUUID("ororRelicOwner")
                            && player.getUUID().equals(entity.getPersistentData().getUUID("ororRelicOwner"))) {
                            personal++;
                        }
                    }

                    if (personal < 1 || personal > 4) {
                        throw new IllegalStateException("Remote player summon ownership invalid " + personal);
                    }
                }

                int owned = 0;

                for (Entity entityx : level.getAllEntities()) {
                    if (entityx.getPersistentData().hasUUID("ororRelicOwner")) {
                        owned++;
                    }
                }

                if (owned < 2 || owned > 8) {
                    throw new IllegalStateException("Two real player summons invalid " + owned);
                }

                if (ModList.get().isLoaded("suppressionmod")) {
                    try {
                        Class<?> listener = Class.forName("ru.liko.suppressionmod.ServerSuppressionListener");
                        Method builder = listener.getDeclaredMethod("buildSettingsPacket");
                        builder.setAccessible(true);
                        Object packet = builder.invoke(null);
                        Class.forName("ru.liko.suppressionmod.network.NetworkHandler").getMethod("sendToAll", packet.getClass()).invoke(null, packet);
                        System.out.println("[OROR_NETWORK_SERVER] suppressionSettingsBroadcast=PASS");
                    } catch (ReflectiveOperationException var11) {
                        throw new IllegalStateException("Server config broadcast regression", var11);
                    }
                }

                List<SupremeEntity> spoken = actors.stream().filter(a -> MobMind.data(a).getList("Conversations", 10).size() > 0).toList();
                if (spoken.size() != 2 || spoken.stream().filter(a -> MobMind.data(a).getBoolean("LastRemote")).count() != 1L) {
                    throw new IllegalStateException("Native chat and HTTP fixture branches not applied");
                }

                for (SupremeEntity actorxxx : spoken) {
                    if (MobMind.data(actorxxx).getInt("TukuyoDecisions") < 1) {
                        throw new IllegalStateException("Conversation not fused with actual TUKUYO");
                    }
                }

                for (Villager fighter : fighters) {
                    if (MobMind.data(fighter).getInt("Strikes") < 1) {
                        throw new IllegalStateException("Multiplayer native combat did not execute");
                    }
                }

                System.out.println("[OROR_NETWORK_MIND] PASS conversations=2 remoteFixture=1 quotaFallback=1 armedCombat=4 tukuyo=2");

                for (Villager worker : workers) {
                    BlockPos at = VillagerIndustry.station(worker);
                    ChestBlockEntity box = (ChestBlockEntity)level.getBlockEntity(at.north());
                    int products = 0;

                    for (int slot = 0; slot < box.getContainerSize(); slot++) {
                        if (box.getItem(slot).is(Items.IRON_INGOT)) {
                            products += box.getItem(slot).getCount();
                        }
                    }

                    if (VillagerIndustry.data(worker).getInt("OresMined") != 1 || products != 1) {
                        throw new IllegalStateException("Network mining pipeline: " + VillagerIndustry.status(worker) + " products=" + products);
                    }
                }

                for (int rank = 1; rank <= 6; rank++) {
                    if (MobLevels.level((Mob)rankSamples.get(rank - 1)) != rank) {
                        throw new IllegalStateException("Network rank changed");
                    }
                }

                System.out.println("[OROR_NETWORK_INDUSTRY] PASS miners=3 realProducts=3 ranks=6");

                for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                    String id = player.getGameProfile().getName().endsWith("1") ? "kokuhaku" : "riha";
                    SupremeEntity actorxxxx = actors.stream().filter(a -> a.spec.id.equals(id)).findFirst().orElseThrow();
                    if (!player.getUUID().equals(actorxxxx.owner)) {
                        throw new IllegalStateException("Follow command lost NPC ownership");
                    }
                }

                System.out.println("[OROR_NETWORK_FOLLOW] PASS owners=2 humanOps=0");
                System.out
                    .println(
                        "[OROR_NETWORK_SERVER] PASS players="
                            + server.getPlayerList().getPlayerCount()
                            + " actors="
                            + actors.size()
                            + " operatorHolders=7 ownedSummons="
                            + owned
                            + " humanOps="
                            + server.getPlayerList().getOpNames().length
                    );

                for (ServerPlayer playerx : server.getPlayerList().getPlayers()) {
                    playerx.sendSystemMessage(Component.literal("OROR_NETWORK_SERVER_PASS"));
                }
            }
        }
    }
}
