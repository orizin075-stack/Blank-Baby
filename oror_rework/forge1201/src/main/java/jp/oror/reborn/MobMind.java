package jp.oror.reborn;

import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;

public final class MobMind {
    public static final String TAG = "OrorMind";
    public static final List<String> SKILLS = List.of(
        "unarmed", "sword", "axe", "mace", "bow", "crossbow", "trident", "gun", "magic", "shield", "tactics", "healing", "terrain", "teamwork"
    );
    public static final Set<String> STANCES = Set.of("balanced", "aggressive", "defensive", "ranged", "unarmed");

    private MobMind() {
    }

    public static CompoundTag data(Mob mob) {
        CompoundTag root = mob.getPersistentData();
        if (!root.contains("OrorMind", 10)) {
            CompoundTag n = new CompoundTag();
            n.putInt("Schema", 1);
            n.putLong("Born", mob.level().getGameTime());
            n.putLong("LastClock", mob.level().getGameTime());
            n.putString("Stance", "balanced");
            root.put("OrorMind", n);
        }

        return root.getCompound("OrorMind");
    }

    public static void clock(Mob mob) {
        CompoundTag n = data(mob);
        long now = mob.level().getGameTime();
        long last = n.getLong("LastClock");
        long delta = Math.max(0L, now - last);
        n.putLong("Age", saturatingAdd(n.getLong("Age"), delta));
        n.putLong("LastClock", now);
    }

    public static long saturatingAdd(long a, long b) {
        return a > Long.MAX_VALUE - Math.max(0L, b) ? Long.MAX_VALUE : Math.max(0L, a) + Math.max(0L, b);
    }

    public static long age(Mob mob) {
        return Math.max(0L, data(mob).getLong("Age"));
    }

    public static double strength(Mob mob) {
        CompoundTag n = data(mob);
        return MobLevels.power(mob)
            * (1.0 + Math.log1p((double)age(mob) / 24000.0) * 0.3 + Math.log1p((double)Math.max(0L, n.getLong("Experience")) / 40.0) * 0.25);
    }

    public static int skill(Mob mob, String id) {
        return Math.max(0, Math.min(1000000, data(mob).getCompound("Skills").getInt(id)));
    }

    public static void practice(Mob mob, String id, int amount) {
        if (SKILLS.contains(id) && amount > 0) {
            CompoundTag n = data(mob);
            CompoundTag skills = n.getCompound("Skills");
            skills.putInt(id, Math.min(1000000, skill(mob, id) + Math.min(100, amount)));
            n.put("Skills", skills);
            n.putLong("Experience", saturatingAdd(n.getLong("Experience"), (long)Math.min(100, amount)));
        }
    }

    public static String stance(Mob mob) {
        String value = data(mob).getString("Stance");
        return STANCES.contains(value) ? value : "balanced";
    }

    public static String preferred(Mob mob) {
        String value = data(mob).getString("Weapon");
        return SKILLS.contains(value) ? value : "";
    }

    public static void remember(Mob mob, String species, String tactic) {
        CompoundTag n = data(mob);
        CompoundTag opponents = n.getCompound("Opponents");
        if (!opponents.contains(species) && opponents.size() >= 32) {
            opponents.remove(opponents.getAllKeys().stream().sorted().findFirst().orElse(""));
        }

        opponents.putString(species, cut(tactic, 80));
        n.put("Opponents", opponents);
    }

    public static void conversation(Mob mob, UUID player, String message, String reply, String stance, String skill, String lesson) {
        CompoundTag n = data(mob);
        DialogueArchive.record(mob, player, message, reply, lesson);
        if (STANCES.contains(stance)) {
            n.putString("Stance", stance);
        }

        if (SKILLS.contains(skill)) {
            n.putString("Weapon", skill);
        }

        long now = mob.level().getGameTime();
        if (!n.contains("NextTraining") || now >= n.getLong("NextTraining")) {
            practice(mob, skill, 12);
            practice(mob, "tactics", 4);
            n.putLong("NextTraining", now + 100L);
        }

        ListTag logs = n.getList("Conversations", 10);

        while (logs.size() >= 12) {
            logs.remove(0);
        }

        CompoundTag log = new CompoundTag();
        log.putUUID("Player", player);
        log.putString("Message", cut(message, 500));
        log.putString("Reply", cut(reply, 500));
        log.putString("Lesson", cut(lesson, 240));
        log.putLong("Time", now);
        logs.add(log);
        n.put("Conversations", logs);
        CompoundTag relations = n.getCompound("Relations");
        String id = player.toString();
        if (!relations.contains(id) && relations.size() >= 16) {
            relations.remove(relations.getAllKeys().stream().sorted().findFirst().orElse(""));
        }

        relations.putInt(id, Math.min(1000, Math.max(-1000, relations.getInt(id) + 1)));
        n.put("Relations", relations);
        if (mob instanceof SupremeEntity b && b.lore()) {
            LorePowers.grow(b);
        }
    }

    public static String cut(String text, int limit) {
        if (text == null) {
            return "";
        } else {
            String safe = text.replaceAll("[\\p{Cntrl}&&[^\\n]]", "");
            return safe.length() > limit ? safe.substring(0, limit) : safe;
        }
    }

    public static String description(Mob mob) {
        CompoundTag n = data(mob);
        return "Lv."
            + MobLevels.level(mob)
            + (mob instanceof Villager v ? " 取引Lv." + v.getVillagerData().getLevel() : "")
            + " 生存="
            + age(mob) / 24000L
            + "日 経験="
            + n.getLong("Experience")
            + " 戦術="
            + stance(mob)
            + " 習熟="
            + n.getCompound("Skills")
            + " 会話="
            + n.getList("Conversations", 10).size()
            + " 強さ倍率="
            + String.format(Locale.ROOT, "%.2f", strength(mob));
    }
}
