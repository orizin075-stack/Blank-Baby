package jp.oror.reborn;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.atomic.AtomicInteger;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.storage.LevelResource;

public final class DialogueArchive {
    private static final ArrayBlockingQueue<DialogueArchive.Entry> QUEUE = new ArrayBlockingQueue<>(2048);
    private static final AtomicInteger PENDING = new AtomicInteger();
    private static final Map<Path, ArrayDeque<JsonObject>> RECENT = new LinkedHashMap<>(128, 0.75F, true);
    private static volatile long written;
    private static volatile long rejected;
    private static volatile String state = "待機";

    public static Path file(Mob mob) {
        return mob.level()
            .getServer()
            .getWorldPath(LevelResource.ROOT)
            .resolve("oror_dialogue")
            .resolve(mob.level().dimension().location().toString().replace(':', '_'))
            .resolve(mob.getUUID() + ".jsonl");
    }

    public static void record(Mob mob, UUID human, String message, String reply, String lesson) {
        if ((Boolean)RebornConfig.DIALOGUE_ARCHIVE.get() && !mob.level().isClientSide) {
            Path file = file(mob);
            JsonObject object = new JsonObject();
            object.addProperty("schema", 1);
            object.addProperty("mob", mob.getUUID().toString());
            object.addProperty("player", human.toString());
            object.addProperty("world_tick", mob.level().getGameTime());
            object.addProperty("message", MobMind.cut(message, 8192));
            object.addProperty("reply", MobMind.cut(reply, 4096));
            object.addProperty("lesson", MobMind.cut(lesson, 1024));
            PENDING.incrementAndGet();
            if (!QUEUE.offer(new DialogueArchive.Entry(file, object))) {
                PENDING.decrementAndGet();
                rejected++;
                state = "記録待ち上限";
            } else {
                synchronized (RECENT) {
                    ArrayDeque<JsonObject> entries = RECENT.computeIfAbsent(file, k -> new ArrayDeque<>());
                    entries.addLast(object);

                    while (entries.size() > 128) {
                        entries.removeFirst();
                    }

                    while (RECENT.size() > 256) {
                        RECENT.remove(RECENT.keySet().iterator().next());
                    }
                }

                CompoundTag n = MobMind.data(mob);
                n.putLong("ArchivedConversations", n.getLong("ArchivedConversations") + 1L);
                n.putString("LatestMemory", MobMind.cut(lesson, 1024));
            }
        }
    }

    public static String retrieve(Path file, UUID human, String query) {
        List<JsonObject> entries;
        synchronized (RECENT) {
            ArrayDeque<JsonObject> cached = RECENT.get(file);
            entries = cached == null ? new ArrayList<>() : new ArrayList<>(cached);
        }

        if (Files.isRegularFile(file)) {
            try (FileChannel channel = FileChannel.open(file, StandardOpenOption.READ)) {
                long offset = Math.max(0L, channel.size() - 2097152L);
                channel.position(offset);
                ByteBuffer buffer = ByteBuffer.allocate((int)(channel.size() - offset));

                while (buffer.hasRemaining() && channel.read(buffer) > 0) {
                }

                String tail = new String(buffer.array(), 0, buffer.position(), StandardCharsets.UTF_8);
                if (offset > 0L) {
                    int newline = tail.indexOf(10);
                    tail = newline < 0 ? "" : tail.substring(newline + 1);
                }

                for (String line : tail.split("\n")) {
                    try {
                        JsonObject item = JsonParser.parseString(line).getAsJsonObject();
                        if (item.get("player").getAsString().equals(human.toString())) {
                            entries.add(item);
                        }
                    } catch (RuntimeException var15) {
                    }
                }
            } catch (IOException var18) {
            }
        }

        String[] words = MobMind.cut(query, 240).toLowerCase(Locale.ROOT).split("[\\s、。,:：]+");
        LinkedHashMap<String, JsonObject> unique = new LinkedHashMap<>();

        for (JsonObject e : entries) {
            if (e.get("player").getAsString().equals(human.toString())) {
                unique.put(e.toString(), e);
            }
        }

        ArrayList<JsonObject> ranked = new ArrayList<>(unique.values());
        ranked.sort(Comparator.<JsonObject>comparingInt(ex -> {
            String text = ex.toString().toLowerCase(Locale.ROOT);
            int score = 0;

            for (String word : words) {
                if (word.length() > 1 && text.contains(word)) {
                    score++;
                }
            }

            return score;
        }).thenComparingLong(ex -> ex.get("world_tick").getAsLong()).reversed());
        StringBuilder out = new StringBuilder();

        for (JsonObject item : ranked.stream().limit(8L).toList()) {
            String value = item.get("message").getAsString() + " → " + item.get("reply").getAsString();
            if (out.length() + value.length() > 4800) {
                break;
            }

            out.append(value).append('\n');
        }

        return out.toString();
    }

    public static boolean flush(long millis) {
        long until = System.nanoTime() + millis * 1000000L;

        while (PENDING.get() > 0 && System.nanoTime() < until) {
            try {
                Thread.sleep(5L);
            } catch (InterruptedException var5) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        return PENDING.get() == 0;
    }

    public static String status() {
        return state + " / 書込=" + written + " / 待機=" + PENDING.get() + " / 未保存=" + rejected;
    }

    private DialogueArchive() {
    }

    static {
        Thread worker = new Thread(() -> {
            while (true) {
                DialogueArchive.Entry entry = null;

                try {
                    entry = QUEUE.take();
                    Files.createDirectories(entry.file().getParent());
                    Files.writeString(entry.file(), entry.content() + "\n", StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
                    written++;
                    state = "記録中";
                } catch (Exception var5) {
                    rejected++;
                    state = "保存エラー：保存先を確認";
                } finally {
                    if (entry != null) {
                        PENDING.decrementAndGet();
                    }
                }
            }
        }, "OROR-dialogue-journal");
        worker.setDaemon(true);
        worker.start();
    }

    private static record Entry(Path file, JsonObject content) {
    }
}
