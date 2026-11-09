package jp.oror.reborn.relic;

import com.google.gson.JsonObject;
import java.util.List;
import jp.oror.reborn.RelicArts;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * (058) The server's side of the techniques' 3D shapes: where a cue op of a program says a shape goes (at the bearer,
 * at the point the technique works at, on each target, along the line it was released along), sent to whoever sees the
 * bearer. The clients draw it (RelicClient); nothing of it is ever decided there.
 */
public final class RelicFx {
    /** The shapes, by the cue op's word (their numbers are the clients'). */
    public static final List<String> KINDS = List.of("slash", "wave", "beam", "ring", "circle", "pillar", "spikes", "rain", "chain", "dome", "text",
        "orb", "flash", "wings", "tree", "clock", "fist", "arrows");
    public static int sent;

    private RelicFx() {
    }

    public static int kind(String k) {
        int i = KINDS.indexOf(k);
        return i < 0 ? 12 : i;
    }

    public static void send(Player p, int kind, int colour, Vec3 at, Vec3 dir, float size, int life, float a, float h, String text) {
        sent++;
        RelicNet.toWatchers(p, new RelicNet.Cue(kind, colour, at.x, at.y, at.z, (float) dir.x, (float) dir.y, (float) dir.z, size, life, a, h, p.getId(),
            text == null ? "" : text.length() > 32 ? text.substring(0, 32) : text));
    }

    static void cue(RelicArts.Ctx c, JsonObject o) {
        Player p = c.p;
        int kind = kind(RelicTech.str(o, "k", "flash"));
        int colour = o.has("c") ? o.get("c").getAsInt() : c.color;
        float s = (float) RelicTech.num(o, "s", 4.0), a = (float) RelicTech.num(o, "a", 0.0), h = (float) RelicTech.num(o, "h", 0.0);
        int life = (int) RelicTech.num(o, "l", 14.0);
        String text = RelicTech.str(o, "txt", "");
        Vec3 chest = p.position().add(0, p.getBbHeight() * 0.6, 0);
        switch (RelicTech.str(o, "at", "self")) {
            case "t" -> {
                int n = 0;
                for (LivingEntity e : c.t) {
                    if (n++ >= 8) {
                        break;
                    }
                    Vec3 at = e.position().add(0, e.getBbHeight() * 0.5, 0);
                    // a chain or a thread runs from the bearer to the target; the rest sit on it
                    Vec3 dir = kind == kind("chain") ? at.subtract(chest) : c.look();
                    send(p, kind, colour, kind == kind("chain") ? chest : at, dir, s, life, a, h, text);
                }
            }
            case "at" -> send(p, kind, colour, RelicTech.at(c).add(0, 0.05, 0), c.look(), s, life, a, h, text);
            case "line" -> send(p, kind, colour, c.eye().add(0, -0.3, 0), c.look(), s, life, a, h, text);
            default -> send(p, kind, colour, kind == kind("ring") || kind == kind("circle") || kind == kind("dome") || kind == kind("spikes")
                || kind == kind("tree") || kind == kind("pillar") ? p.position().add(0, 0.05, 0) : chest, c.look(), s, life, a, h, text);
        }
    }
}
