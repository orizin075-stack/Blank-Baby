package jp.oror.reborn.relic;

import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;
import jp.oror.reborn.RelicArts;
import jp.oror.reborn.RelicPowers;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * (058) The legends' crowning attack: what the third stage adds in the V9 design, played over its 125 ticks (0–20 the
 * stance, 21–60 the forming, 61–100 the attack and the finish, 101–125 the afterglow), in one of five ways by the god:
 *
 * <ul>
 * <li>precise: one special defence of the foe read and undone, then a narrow blow of 1,600,000 and 5% of its maximum
 * health (at most 2,000,000); never on friends.</li>
 * <li>rule: 1,250,000 on up to 12 foes within 18 blocks, their god's condition for 5 s (gravity, a rule's halt, a seal,
 * fate's mark, a toy's size, a curse; a contract only on those who agreed), and 4% (at most 1,500,000).</li>
 * <li>grand: 1,800,000 and 8% (at most 3,000,000); its lasting ground gone within 12 s; a second blow on the same foe
 * only after a grace.</li>
 * <li>machine: a barrage of 1,450,000 and up to six autonomous units (eight with the ones already out) for 20 s; the
 * crowning is shared once each 90 s.</li>
 * <li>rescue: up to 16 friends within 32 blocks healed by 80% and 85% of harm cut for 6 s; foes take only 600,000.</li>
 * </ul>
 */
public final class RelicUltimate {
    public static int started, landed, rescued;
    public static final List<String> LOG = new ArrayList<>();

    private RelicUltimate() {
    }

    static void start(RelicArts.Ctx c) {
        String legend = c.art.id;
        RelicV9.Info info = RelicV9.info(legend);
        if (info == null || info.ultimate == null) {
            return;
        }
        JsonObject u = info.ultimate;
        String k = u.get("k").getAsString();
        Player p = c.p;
        ServerLevel sl = c.sl;
        long now = sl.getGameTime();
        if (k.equals("machine")) {
            long next = p.getPersistentData().getLong("ororUltMachineNext");
            if (now < next) {
                p.displayClientMessage(Component.literal("極致（自律兵装）はまだ使えない：" + (next - now + 19) / 20 + "秒").withStyle(ChatFormatting.GRAY), true);
                return;
            }
            p.getPersistentData().putLong("ororUltMachineNext", now + u.get("cd").getAsLong());
        }
        started++;
        int colour = c.color;
        Vec3 dir = c.look();
        p.displayClientMessage(Component.literal("第三段階の極致").withStyle(ChatFormatting.GOLD), true);
        // 0–20: the stance
        RelicFx.send(p, 4, colour, p.position().add(0, 0.05, 0), new Vec3(0, 1, 0), 5.0F, 125, 1.0F, 0, "");
        RelicFx.send(p, 11, colour, p.position().add(0, p.getBbHeight() + 0.8, 0), dir, 1.6F, 20, 0, 0, "");
        sl.playSound(null, p.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.2F, 0.7F);
        // 21–60: the forming
        RelicTech.later(sl, 21, () -> {
            RelicFx.send(p, 13, colour, p.position().add(0, p.getBbHeight() * 0.6, 0), dir, 3.0F, 40, 0, 0, "");
            RelicFx.send(p, 3, colour, p.position().add(0, 0.05, 0), new Vec3(0, 1, 0), 18.0F, 40, 0, 0, "");
            if (k.equals("precise")) {
                // the foe's special defence read and undone first
                LivingEntity t = RelicTech.focus(c, 48.0);
                if (t != null) {
                    RelicArts.Ctx s = c.copy();
                    s.t = new ArrayList<>(List.of(t));
                    JsonObject seal = new JsonObject();
                    seal.addProperty("op", "seal");
                    seal.addProperty("t", 120);
                    RelicTech.op(s, seal);
                    RelicFx.send(p, 4, colour, t.position().add(0, t.getBbHeight() + 0.3, 0), new Vec3(0, 1, 0), 1.4F, 40, 1.0F, 0, "");
                }
            }
            if (k.equals("machine")) {
                int room = Math.max(0, u.get("total").getAsInt() - RelicWorld.count(p, null));
                int n = Math.min(u.get("units").getAsInt(), Math.max(room, 1));
                RelicWorld.place(p, legend, "cannon", n, u.get("t").getAsInt(), 600.0F, 0.02F, (float) u.get("base").getAsDouble(), 15, 24.0, 0.0F, colour);
            }
        });
        // 61–100: the attack and the finish
        RelicTech.later(sl, 61, () -> attack(c, k, u, colour));
        RelicTech.later(sl, 84, () -> {
            if (!k.equals("rescue")) {
                finish(c, k, u, colour);
            }
        });
        // 101–125: the afterglow
        RelicTech.later(sl, 101, () -> {
            RelicFx.send(p, 12, colour, p.position().add(0, p.getBbHeight() * 0.6, 0), dir, 3.0F, 24, 0, 0, "");
            RelicFx.send(p, 3, 0xFFFFFF, p.position().add(0, 0.05, 0), new Vec3(0, 1, 0), 10.0F, 24, 0, 0, "");
            LOG.add(legend + " " + k + " done");
        });
    }

    private static List<LivingEntity> foes(RelicArts.Ctx c, double r, int n) {
        return RelicArts.sorted(RelicArts.near(c.p, c.p.position(), r), c.p.position(), n);
    }

    private static void attack(RelicArts.Ctx c, String k, JsonObject u, int colour) {
        Player p = c.p;
        ServerLevel sl = c.sl;
        RelicArts.Ctx s = c.copy();
        s.base = (float) u.get("base").getAsDouble();
        switch (k) {
            case "precise" -> {
                LivingEntity t = RelicTech.focus(c, 48.0);
                s.t = t == null ? RelicArts.line(p, c.eye(), c.look(), 48.0, 1.0) : new ArrayList<>(List.of(t));
                RelicFx.send(p, 2, colour, c.eye(), t == null ? c.look() : t.position().add(0, t.getBbHeight() * 0.5, 0).subtract(c.eye()).normalize(),
                    t == null ? 48.0F : (float) t.distanceTo(p), 20, 0.3F, 0, "");
            }
            case "rule" -> {
                s.t = foes(c, u.get("r").getAsDouble(), u.get("n").getAsInt());
                rule(s, u.has("rule") ? u.get("rule").getAsString() : "rule", u.get("t").getAsInt());
                RelicFx.send(p, 4, colour, p.position().add(0, 0.05, 0), new Vec3(0, 1, 0), (float) u.get("r").getAsDouble(), 40, 1.0F, 0, "");
            }
            case "grand" -> {
                s.t = foes(c, 30.0, 16);
                RelicFx.send(p, 5, colour, RelicTech.at(c), new Vec3(0, 1, 0), 6.0F, 30, 0, 30.0F, "");
            }
            case "machine" -> {
                s.t = foes(c, 32.0, 12);
                RelicFx.send(p, 7, colour, p.position().add(c.look().scale(10)), new Vec3(0, -1, 0), 10.0F, 30, 0, 0, "");
            }
            default -> { // rescue
                List<LivingEntity> friends = new ArrayList<>();
                for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(u.get("r").getAsDouble()),
                    x -> x == p || !RelicPowers.enemy(p, x) && (x instanceof Player || x.getPersistentData().hasUUID("ororRelicOwner")))) {
                    if (friends.size() < u.get("n").getAsInt()) {
                        friends.add(e);
                    }
                }
                for (LivingEntity f : friends) {
                    f.heal(f.getMaxHealth() * (float) u.get("heal").getAsDouble());
                    RelicTech.window(f, "ororTechReduce", sl.getGameTime() + u.get("t").getAsLong(), (float) u.get("cut").getAsDouble());
                    RelicFx.send(p, 5, colour, f.position(), new Vec3(0, 1, 0), 1.0F, 30, 0, 6.0F, "");
                    rescued++;
                }
                RelicFx.send(p, 9, colour, p.position(), new Vec3(0, 1, 0), (float) u.get("r").getAsDouble(), 40, 0, 0, "");
                s.t = foes(c, u.get("r").getAsDouble(), 16);
            }
        }
        s.t.removeIf(e -> e == p || !RelicPowers.enemy(p, e));
        for (LivingEntity e : s.t) {
            RelicTech.hurt(s, e, k.equals("grand") || k.equals("machine") ? s.base * 0.5F : s.base);
            landed++;
        }
        sl.playSound(null, p.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.0F, 0.6F);
    }

    /** The finish: the grand and machine barrages' second half, and every crowning's share of the strong's health. */
    private static void finish(RelicArts.Ctx c, String k, JsonObject u, int colour) {
        Player p = c.p;
        RelicArts.Ctx s = c.copy();
        s.base = (float) u.get("base").getAsDouble();
        List<LivingEntity> t = switch (k) {
            case "precise" -> {
                LivingEntity f = RelicTech.focus(c, 48.0);
                yield f == null ? new ArrayList<>() : new ArrayList<>(List.of(f));
            }
            case "rule" -> foes(c, u.get("r").getAsDouble(), u.get("n").getAsInt());
            case "machine" -> foes(c, 32.0, 12);
            default -> foes(c, 30.0, 16);
        };
        t.removeIf(e -> e == p || !RelicPowers.enemy(p, e));
        // a second blow on the same foe only after its grace: the finish is the second, at least 23 ticks on
        for (LivingEntity e : t) {
            if (k.equals("grand") || k.equals("machine")) {
                RelicTech.hurt(s, e, s.base * 0.5F);
            }
            if (u.has("pct") && RelicTech.strong(e)) {
                RelicTech.hurt(s, e, (float) Math.min(u.get("cap").getAsDouble(), e.getMaxHealth() * u.get("pct").getAsDouble()));
            }
            RelicFx.send(p, 12, colour, e.position().add(0, e.getBbHeight() * 0.5, 0), new Vec3(0, 1, 0), 2.4F, 14, 0, 0, "");
        }
        if (k.equals("grand")) {
            JsonObject f = new JsonObject();
            f.addProperty("op", "field");
            f.addProperty("r", 10);
            f.addProperty("t", u.get("field").getAsInt());
            f.addProperty("m", 0.002);
            f.addProperty("rate", 20);
            f.addProperty("name", "afterglow");
            RelicWorld.field(s, f);
        }
    }

    /** The rule gods' condition on those the crowning reaches (5 s at most). */
    private static void rule(RelicArts.Ctx s, String rule, int ticks) {
        Player p = s.p;
        for (LivingEntity e : s.t) {
            switch (rule) {
                case "gravity" -> {
                    e.addEffect(new MobEffectInstance(MobEffects.LEVITATION, ticks, 1));
                    e.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, ticks + 80, 0));
                }
                case "seal" -> new ArrayList<>(e.getActiveEffects()).stream().filter(m -> m.getEffect().value().isBeneficial())
                    .forEach(m -> e.removeEffect(m.getEffect()));
                case "fate" -> {
                    e.getPersistentData().putLong("ororArtMarkUntil", s.sl.getGameTime() + ticks);
                    e.getPersistentData().putFloat("ororArtMarkX", 1.8F);
                }
                case "toy" -> e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, ticks, 3));
                case "curse" -> e.addEffect(new MobEffectInstance(MobEffects.WITHER, ticks, 2));
                case "contract" -> {
                    // only those who agreed to a contract bear a contract's condition
                }
                default -> {
                    if (!RelicTech.strong(e)) {
                        jp.oror.reborn.Abilities.stun(e, ticks);
                    } else {
                        e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, ticks, 3));
                    }
                }
            }
        }
        if (rule.equals("contract")) {
            JsonObject o = new JsonObject();
            com.google.gson.JsonArray ops = new com.google.gson.JsonArray();
            JsonObject hold = new JsonObject();
            hold.addProperty("op", "hold");
            hold.addProperty("t", ticks);
            ops.add(hold);
            o.add("ops", ops);
            RelicWorld.contracts(s, o);
        }
        RelicFx.send(p, 10, s.color, p.position().add(0, p.getBbHeight() + 1.4, 0), new Vec3(0, 1, 0), 2.0F, 40, 0, 0, switch (rule) {
            case "gravity" -> "重力反転";
            case "seal" -> "封印";
            case "fate" -> "運命確定";
            case "toy" -> "玩具化";
            case "curse" -> "呪詛";
            case "contract" -> "契約執行";
            default -> "絶対ルール";
        });
    }
}
