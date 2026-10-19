package jp.oror.reborn;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpRequest.BodyPublishers;
import java.net.http.HttpResponse.BodyHandlers;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent;

public final class TukuyoBridge {
    private static final ExecutorService WORKERS = Executors.newFixedThreadPool(2, r -> {
        Thread t = new Thread(r, "OROR-TUKUYO");
        t.setDaemon(true);
        return t;
    });
    private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2L)).build();
    private static final AtomicInteger FLIGHT = new AtomicInteger();
    private static final Map<MinecraftServer, String> WORLDS = new WeakHashMap<>();
    private static final Set<UUID> PENDING = new HashSet<>();
    private static long retryAfter;
    private static String status = "待機";

    public static String status() {
        return status + " / 実行中=" + FLIGHT.get();
    }

    public static void retry() {
        retryAfter = 0L;
    }

    public static void queue(Mob m, ServerPlayer p, String message) {
        if ((Boolean)RebornConfig.TUKUYO.get() && !request(m, p, message)) {
            CompoundTag n = MobMind.data(m);
            n.putString("TukuyoPendingMessage", MobMind.cut(message, 500));
            n.putUUID("TukuyoPendingPlayer", p.getUUID());
        }
    }

    public static void tick(LivingTickEvent event) {
        if (event.getEntity() instanceof Mob m && m.level() instanceof ServerLevel sl) {
            CompoundTag n = MobMind.data(m);
            String queued = n.getString("TukuyoPendingMessage");
            if (!queued.isEmpty() && m.tickCount % 20 == 0) {
                ServerPlayer p = n.hasUUID("TukuyoPendingPlayer") ? sl.getServer().getPlayerList().getPlayer(n.getUUID("TukuyoPendingPlayer")) : null;
                if (request(m, p, queued)) {
                    n.remove("TukuyoPendingMessage");
                    n.remove("TukuyoPendingPlayer");
                }

                return;
            }

            if (AdaptiveCombat.active(m) && m.getTarget() != null && m.tickCount % 200 == Math.floorMod(m.getId(), 200)) {
                request(m, null, "");
                return;
            }

            return;
        }
    }

    private static String world(ServerLevel level) throws Exception {
        MinecraftServer server = level.getServer();
        String id = WORLDS.get(server);
        if (id != null) {
            return id;
        } else {
            Path path = server.getWorldPath(LevelResource.ROOT).resolve("oror_mind_world.txt");
            if (Files.exists(path)) {
                id = UUID.fromString(Files.readString(path).strip()).toString();
            } else {
                id = UUID.randomUUID().toString();
                Files.writeString(path, id);
            }

            WORLDS.put(server, id);
            return id;
        }
    }

    public static boolean request(Mob m, ServerPlayer player, String message) {
        if ((Boolean)RebornConfig.TUKUYO.get() && System.currentTimeMillis() >= retryAfter && FLIGHT.get() < 2 && !PENDING.contains(m.getUUID())) {
            ServerLevel level = (ServerLevel)m.level();
            CompoundTag n = MobMind.data(m);
            if (message.isEmpty() && n.getLong("NextTukuyo") > level.getGameTime()) {
                return false;
            } else {
                n.putLong("NextTukuyo", level.getGameTime() + 1200L);
                LivingEntity target = m.getTarget();
                JsonObject body = new JsonObject();

                try {
                    body.addProperty("world", world(level));
                } catch (Exception var13) {
                    return false;
                }

                body.addProperty("entity", m.getUUID().toString());
                body.addProperty("health", m.getHealth() / m.getMaxHealth());
                body.addProperty("distance", target == null ? 0.0F : m.distanceTo(target));
                body.addProperty("blocking", target != null && target.isBlocking());
                body.addProperty("sight", target == null || m.getSensing().hasLineOfSight(target));
                body.addProperty("strikes", n.getInt("Strikes"));
                body.addProperty("success", n.getInt("SuccessfulStrikes"));
                body.addProperty("message", MobMind.cut(message, 500));
                UUID entity = m.getUUID();
                UUID human = player == null ? null : player.getUUID();
                MinecraftServer server = level.getServer();
                String endpoint = (String)RebornConfig.TUKUYO_ENDPOINT.get();

                URI uri;
                try {
                    uri = URI.create(endpoint);
                    if (!uri.getScheme().equals("http") || !uri.getHost().equals("127.0.0.1") || !uri.getPath().equals("/v1/mind")) {
                        return false;
                    }
                } catch (RuntimeException var14) {
                    return false;
                }

                PENDING.add(entity);
                FLIGHT.incrementAndGet();
                WORKERS.execute(
                    () -> {
                        try {
                            HttpRequest req = HttpRequest.newBuilder(uri)
                                .timeout(Duration.ofSeconds(10L))
                                .header("Content-Type", "application/json")
                                .POST(BodyPublishers.ofString(body.toString()))
                                .build();
                            HttpResponse<String> response = HTTP.sendAsync(req, BodyHandlers.ofString()).get(10L, TimeUnit.SECONDS);
                            if (response.statusCode() != 200 || response.body().length() > 8192) {
                                throw new IllegalStateException("TUKUYO unavailable");
                            }

                            JsonObject result = JsonParser.parseString(response.body()).getAsJsonObject();
                            String stance = result.get("stance").getAsString();
                            String skill = result.get("skill").getAsString();
                            if (!result.get("ok").getAsBoolean()
                                || !MobMind.STANCES.contains(stance)
                                || !MobMind.SKILLS.contains(skill)
                                || !result.get("individual").getAsString().equals(body.get("world").getAsString() + ":" + entity)
                                || !result.get("decision_sha256").getAsString().matches("[0-9a-f]{64}")) {
                                throw new IllegalArgumentException("TUKUYO response invalid");
                            }

                            server.execute(
                                () -> {
                                    PENDING.remove(entity);
                                    if (level.getEntity(entity) instanceof Mob present && present.isAlive()) {
                                        CompoundTag data = MobMind.data(present);
                                        data.putString("TukuyoDecision", result.get("decision_sha256").getAsString());
                                        data.putString("TukuyoSource", result.get("source_kind").getAsString());
                                        data.putString("Stance", stance);
                                        if (!message.isEmpty()) {
                                            data.putString("Weapon", skill);
                                            MobMind.practice(present, skill, 4);
                                        }

                                        data.putInt("TukuyoDecisions", data.getInt("TukuyoDecisions") + 1);
                                        status = "接続済み 1022.7.9";
                                        ServerPlayer p = human == null ? null : server.getPlayerList().getPlayer(human);
                                        if (p != null) {
                                            String reply = result.has("answer") && !result.get("answer").isJsonNull()
                                                ? result.get("answer").getAsString()
                                                : "経験を記録した。戦術：" + stance + " / 技能：" + skill;
                                            p.sendSystemMessage(Component.literal(MobConversation.name(present) + " [TUKUYO]：" + MobMind.cut(reply, 500)));
                                        }
                                    }
                                }
                            );
                        } catch (Exception var15) {
                            server.execute(() -> {
                                PENDING.remove(entity);
                                status = "未接続（ローカル戦闘継続）";
                                retryAfter = System.currentTimeMillis() + 60000L;
                            });
                        } finally {
                            FLIGHT.decrementAndGet();
                        }
                    }
                );
                return true;
            }
        } else {
            return false;
        }
    }
}
