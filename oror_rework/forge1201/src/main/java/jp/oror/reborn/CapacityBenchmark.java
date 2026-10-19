package jp.oror.reborn;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import io.netty.buffer.Unpooled;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.ServerScoreboard;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.scores.PlayerTeam;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.TickEvent.ServerTickEvent;
import net.minecraftforge.network.payload.ModdedNetworkQueryPayload;
import net.minecraftforge.network.registration.NetworkRegistry;

@EventBusSubscriber(
    modid = "oror_supreme_bosses"
)
public final class CapacityBenchmark {
    private static boolean exported;
    private static boolean started;
    private static int ticks;
    private static int round = -1;
    private static int roundTicks;
    private static int bossKills;
    private static int friendlyKills;
    private static int otherDeaths;
    private static int minPlayers = 100000;
    private static long began;
    private static double maxMs;
    private static double totalMs;
    private static SupremeEntity boss;
    private static final List<Mob> army = new ArrayList<>();
    private static final Set<UUID> armyIds = new HashSet<>();
    private static final Set<UUID> bossVictims = new HashSet<>();
    private static final List<JsonObject> rounds = new ArrayList<>();
    private static final String[] GODS = new String[]{"miyohime", "tenki", "mels"};
    private static long roundBegan;

    private static void exportChannels(MinecraftServer server) {
        try {
            Field field = NetworkRegistry.class.getDeclaredField("PAYLOAD_REGISTRATIONS");
            field.setAccessible(true);
            ModdedNetworkQueryPayload packet = ModdedNetworkQueryPayload.fromRegistry((Map)field.get(null));
            FriendlyByteBuf buf = new FriendlyByteBuf(Unpooled.buffer());

            try {
                ModdedNetworkQueryPayload.STREAM_CODEC.encode(buf, packet);
                byte[] bytes = new byte[buf.readableBytes()];
                buf.readBytes(bytes);
                Files.write(server.getWorldPath(LevelResource.ROOT).resolve("load_channels.bin"), bytes);
            } finally {
                buf.release();
            }

            exported = true;
            System.out.println("[OROR_CAPACITY] CHANNELS_READY");
        } catch (Exception var9) {
            throw new IllegalStateException("Load handshake export failed", var9);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent e) {
        if (e.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        if (Boolean.getBoolean("oror.capacity")) {
            MinecraftServer server = e.getServer();
            ServerLevel sl = server.overworld();
            if (!exported) {
                RebornConfig.AUTO_RESEARCH.set(false);
                RebornConfig.NATURAL.set(false);
                exportChannels(server);
            }

            int required = Integer.getInteger("oror.clients", 100);
            if (!started) {
                if (server.getPlayerList().getPlayerCount() < required) {
                    return;
                }

                started = true;
                began = System.nanoTime();

                for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                    p.setGameMode(GameType.CREATIVE);
                    p.connection.teleport(250.0, 65.0, 220.0, 0.0F, 0.0F);
                }

                System.out.println("[OROR_CAPACITY] CONNECTED " + server.getPlayerList().getPlayerCount());
            }

            minPlayers = Math.min(minPlayers, server.getPlayerList().getPlayerCount());
            double ms = (double)server.getAverageTickTimeNanos() / 1000000.0;
            totalMs += ms;
            maxMs = Math.max(maxMs, ms);
            ticks++;
            if (round == -1) {
                if (ticks >= 200) {
                    next(sl);
                }
            } else {
                roundTicks++;
                long alive = army.stream().filter(LivingEntity::isAlive).count();
                if (roundTicks % 100 == 0) {
                    System.out
                        .println(
                            "[OROR_CAPACITY] PROGRESS "
                                + GODS[round]
                                + " ticks="
                                + roundTicks
                                + " alive="
                                + alive
                                + " players="
                                + server.getPlayerList().getPlayerCount()
                        );
                }

                if (alive == 0L || roundTicks >= 1200) {
                    JsonObject result = new JsonObject();
                    result.addProperty("boss", GODS[round]);
                    result.addProperty("spawned", army.size());
                    result.addProperty("survivors", alive);
                    JsonArray residual = new JsonArray();

                    for (Mob m : army) {
                        if (m.isAlive() || !bossVictims.contains(m.getUUID())) {
                            JsonObject row = new JsonObject();
                            row.addProperty("uuid", m.getUUID().toString());
                            row.addProperty("health", m.getHealth());
                            row.addProperty("removed", m.isRemoved());
                            row.addProperty("removal_reason", String.valueOf(m.getRemovalReason()));
                            row.addProperty("same_live_entity", sl.getEntity(m.getUUID()) == m);
                            row.addProperty("distance", m.distanceTo(boss));
                            row.addProperty("target_is_boss", m.getTarget() == boss);
                            row.addProperty("no_ai", m.isNoAi());
                            row.addProperty("position", m.position().toString());
                            residual.add(row);
                        }
                    }

                    result.add("residuals", residual);
                    result.addProperty("boss_alive", boss.isAlive());
                    result.addProperty("boss_health", boss.getHealth());
                    result.addProperty("ticks", roundTicks);
                    result.addProperty("seconds", (double)(System.nanoTime() - roundBegan) / 1.0E9);
                    result.addProperty("boss_or_owned_summon_kills", bossKills);
                    result.addProperty("friendly_kills", friendlyKills);
                    result.addProperty("other_deaths", otherDeaths);
                    result.addProperty("domain_defeats", boss.getPersistentData().getLong("OrorDomainDefeats"));
                    result.addProperty("native_enemy_ai", true);
                    result.addProperty("administrative_kills", false);
                    result.addProperty("enemy_friendly_fire", false);
                    rounds.add(result);
                    System.out.println("[OROR_CAPACITY] ROUND " + result);

                    for (Mob mx : army) {
                        if (!mx.isRemoved()) {
                            mx.discard();
                        }
                    }

                    army.clear();
                    armyIds.clear();
                    boss.discard();
                    if (round + 1 < GODS.length) {
                        next(sl);
                    } else {
                        finish(server);
                    }
                }
            }
        }
    }

    private static void next(ServerLevel sl) {
        round++;
        roundTicks = 0;
        otherDeaths = 0;
        friendlyKills = 0;
        bossKills = 0;
        bossVictims.clear();
        roundBegan = System.nanoTime();

        for (int x = 14; x <= 20; x++) {
            for (int z = 14; z <= 20; z++) {
                sl.setChunkForced(x, z, true);
            }
        }

        for (int x = 244; x <= 298; x++) {
            for (int z = 244; z <= 298; z++) {
                sl.setBlock(new BlockPos(x, 64, z), Blocks.STONE.defaultBlockState(), 2);
            }
        }

        boss = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(GODS[round]).get()).create(sl);
        boss.moveTo(272.0, 65.0, 272.0, 0.0F, 0.0F);
        boss.setPersistenceRequired();
        sl.addFreshEntity(boss);
        ServerScoreboard scoreboard = sl.getScoreboard();
        PlayerTeam team = scoreboard.getPlayerTeam("oror_load_army");
        if (team == null) {
            team = scoreboard.addPlayerTeam("oror_load_army");
        }

        team.setAllowFriendlyFire(false);

        for (int i = 0; i < 1000; i++) {
            Husk m = (Husk)EntityType.HUSK.create(sl);
            m.moveTo(249.0 + (double)(i % 32) * 1.35, 65.0, 249.0 + (double)(i / 32) * 1.35, 0.0F, 0.0F);
            m.setPersistenceRequired();
            MobLevels.set(m, 6);
            sl.addFreshEntity(m);
            MobLevels.refresh(m);
            scoreboard.addPlayerToTeam(m.getScoreboardName(), team);
            m.setTarget(boss);
            army.add(m);
            armyIds.add(m.getUUID());
        }

        boss.setTarget((LivingEntity)army.getFirst());
        if (round == 0) {
            for (ServerPlayer p : sl.getServer().getPlayerList().getPlayers()) {
                for (int i = 0; i < 20; i++) {
                    MobConversation.apply(
                        boss, p.getUUID(), "負荷検証用の個別会話 " + i, new MobConversation.Answer("検証記録 " + i, "balanced", "tactics", "個別記憶", List.of(), false)
                    );
                }
            }
        }

        System.out.println("[OROR_CAPACITY] SPAWN " + GODS[round] + " rank6=1000 nativeAI=true");
    }

    @SubscribeEvent
    public static void death(LivingDeathEvent e) {
        if (Boolean.getBoolean("oror.capacity") && boss != null && armyIds.contains(e.getEntity().getUUID())) {
            Entity source = e.getSource().getEntity();
            label26:
            if (source != boss) {
                if (source instanceof FamiliarEntity f && boss.getUUID().equals(f.creator)) {
                    break label26;
                }

                if (source != null && armyIds.contains(source.getUUID())) {
                    friendlyKills++;
                    return;
                }

                otherDeaths++;
                return;
            }

            bossVictims.add(e.getEntity().getUUID());
            bossKills = bossVictims.size();
        }
    }

    private static void finish(MinecraftServer server) {
        JsonObject report = new JsonObject();
        report.addProperty("requested_protocol_clients", Integer.getInteger("oror.clients", 100));
        report.addProperty("connected_players_at_end", server.getPlayerList().getPlayerCount());
        report.addProperty("minimum_connected_players", minPlayers);
        report.addProperty("ticks", ticks);
        report.addProperty("seconds", (double)(System.nanoTime() - began) / 1.0E9);
        report.addProperty("average_of_rolling_mspt", totalMs / (double)ticks);
        report.addProperty("maximum_rolling_mspt", maxMs);
        report.addProperty("heap_used_mb", (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1048576L);
        report.addProperty("synthetic_archived_turns", 2000);
        report.addProperty("archive_flushed", DialogueArchive.flush(3000L));
        JsonArray array = new JsonArray();
        rounds.forEach(array::add);
        report.add("battles", array);
        boolean pass = minPlayers >= Integer.getInteger("oror.clients", 100)
            && rounds.stream()
                .allMatch(
                    r -> r.get("survivors").getAsInt() == 0
                            && r.get("boss_alive").getAsBoolean()
                            && r.get("boss_or_owned_summon_kills").getAsInt() == 1000
                            && r.get("friendly_kills").getAsInt() == 0
                            && r.get("other_deaths").getAsInt() == 0
                );
        report.addProperty("status", pass ? "PASS" : "FAIL");

        try {
            Files.writeString(
                server.getWorldPath(LevelResource.ROOT).resolve("capacity_results.json"), new GsonBuilder().setPrettyPrinting().create().toJson(report)
            );
        } catch (Exception var5) {
            throw new IllegalStateException(var5);
        }

        System.out.println("[OROR_CAPACITY] COMPLETE " + report);
        server.halt(false);
    }

    private CapacityBenchmark() {
    }
}
