package jp.oror.reborn.waza;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import jp.oror.reborn.king.KingForms;
import jp.oror.reborn.king.RebelLord;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Evoker;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059c) CI check "royalwaza" (/oror royalwaza test): each of the Villager King's 64 and Azazel's 41 V20 actions (the
 * techniques after the 984: waza_royal.json) begun once by its caster on a platform in the sky, against a zombie that
 * cannot die, and followed to its end. An action passes when it ran through (no error) and went off as many times as it
 * should (its hits, or its one release). What landed is counted beside, by behaviour.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RoyalWazaTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Waza");
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Run {
        ServerLevel level;
        BlockPos at;
        final List<Waza> queue = new ArrayList<>();
        int next;
        Mob caster;
        String casterOf = "";
        Zombie dummy;
        WazaEngine.Cast cast;
        long castAt;
        int tried, passed, landed;
        final List<String> failed = new ArrayList<>();
        final Map<String, int[]> tally = new TreeMap<>();
    }

    private RoyalWazaTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("royalwaza").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        Run r = new Run();
        r.level = level;
        BlockPos s = level.getSharedSpawnPos();
        r.at = new BlockPos(s.getX() - 320, 230, s.getZ() - 320);
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                level.setChunkForced((r.at.getX() >> 4) + dx, (r.at.getZ() >> 4) + dz, true);
            }
        }
        for (int x = -12; x <= 12; x++) {
            for (int z = -12; z <= 12; z++) {
                level.setBlockAndUpdate(r.at.offset(x, -1, z), Blocks.STONE.defaultBlockState());
            }
        }
        r.queue.addAll(Waza.ALL.subList(984, Waza.ALL.size()));
        run = r;
        LOG.info("ROYAL-WAZA-START {\"actions\":{}}", r.queue.size());
        src.sendSuccess(() -> Component.literal("royal waza test: " + r.queue.size()), false);
        return 1;
    }

    private static Mob caster(Run r, Waza w) {
        String kind = w.character().startsWith("king") ? "king" : "azazel";
        if (r.caster != null && r.caster.isAlive() && r.casterOf.equals(kind)) {
            return r.caster;
        }
        if (r.caster != null) {
            r.caster.discard();
        }
        Mob m;
        if (kind.equals("king")) {
            RoyalMob king = RoyalRegistry.TYPES.get(RoyalRole.KING).create(r.level);
            if (king == null) {
                return null;
            }
            king.getPersistentData().putBoolean(KingForms.QUIET, true);
            m = king;
        } else {
            Evoker ev = EntityType.EVOKER.create(r.level);
            if (ev == null) {
                return null;
            }
            ev.getPersistentData().putBoolean(RebelLord.LORD, true);
            ev.setCustomName(Component.literal("アザゼル"));
            m = ev;
        }
        m.setNoAi(true);
        m.setPersistenceRequired();
        m.moveTo(r.at.getX() + 0.5, r.at.getY(), r.at.getZ() + 0.5, 180F, 0F);
        r.level.addFreshEntity(m);
        r.caster = m;
        r.casterOf = kind;
        return m;
    }

    private static Zombie dummy(Run r, Waza w) {
        double d = Math.max(2.2, Math.min(9, w.range() * 0.6));
        if (r.dummy == null || !r.dummy.isAlive()) {
            Zombie z = EntityType.ZOMBIE.create(r.level);
            if (z == null) {
                return null;
            }
            z.setNoAi(true);
            z.setPersistenceRequired();
            z.getAttribute(Attributes.MAX_HEALTH).setBaseValue(4000);
            z.setHealth(4000);
            r.level.addFreshEntity(z);
            r.dummy = z;
        }
        r.dummy.teleportTo(r.at.getX() + 0.5, r.at.getY(), r.at.getZ() + 0.5 - d);
        r.dummy.setHealth(r.dummy.getMaxHealth());
        return r.dummy;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime();
        try {
            if (r.cast == null) {
                if (r.next >= r.queue.size()) {
                    finish(r);
                    return;
                }
                Waza w = r.queue.get(r.next);
                Mob b = caster(r, w);
                LivingEntity t = dummy(r, w);
                if (b == null || t == null) {
                    r.failed.add(w.id() + ":spawn");
                    r.next++;
                    return;
                }
                if (w.character().startsWith("king")) {
                    b.getPersistentData().putInt(Casters.KING_FORM, w.character().charAt(4) - '1');
                }
                b.setTarget(t);
                b.lookAt(t, 180F, 90F);
                r.tried++;
                r.cast = WazaEngine.start(b, w, t, true);
                r.castAt = now;
                return;
            }
            WazaEngine.drive(r.caster, false);
            if (r.dummy != null) {
                r.dummy.setHealth(r.dummy.getMaxHealth());
            }
            Waza w = r.cast.w;
            if (r.cast.ended || now - r.castAt > w.length() + 80) {
                judge(r, w, r.cast);
                WazaWorld.removeCastObjects(r.cast);
                for (Mob f : WazaWorld.summonsOf(r.caster)) {
                    f.discard();
                }
                r.cast = null;
                r.next++;
            }
        } catch (RuntimeException ex) {
            Waza w = r.next < r.queue.size() ? r.queue.get(r.next) : null;
            r.failed.add((w == null ? "?" : w.id()) + ":" + ex.getClass().getSimpleName());
            LOG.error("ROYAL-WAZA error in {}", w == null ? "?" : w.id(), ex);
            r.cast = null;
            r.next++;
        }
    }

    private static void judge(Run r, Waza w, WazaEngine.Cast c) {
        int want = Math.max(1, w.hits().length);
        boolean ok = c.ended && c.fired >= want && c.notes.stream().noneMatch(n -> n.startsWith("cancelled"));
        int[] t = r.tally.computeIfAbsent(w.behaviour().name(), k -> new int[3]);
        t[0]++;
        if (ok) {
            t[1]++;
            r.passed++;
        } else {
            r.failed.add(w.id() + ":fired" + c.fired + "/" + want + (c.ended ? "" : ":unended") + (c.notes.isEmpty() ? "" : ":" + c.notes.get(0)));
        }
        if (c.landed > 0) {
            t[2]++;
            r.landed++;
        }
    }

    private static void finish(Run r) {
        if (r.caster != null) {
            r.caster.discard();
        }
        if (r.dummy != null) {
            r.dummy.discard();
        }
        StringBuilder t = new StringBuilder("{");
        r.tally.forEach((k, v) -> t.append(t.length() > 1 ? "," : "").append('"').append(k).append("\":[").append(v[0]).append(',').append(v[1])
            .append(',').append(v[2]).append(']'));
        t.append('}');
        LOG.info("ROYAL-WAZA-RESULT {\"actions\":{},\"tried\":{},\"passed\":{},\"landed\":{},\"byBehaviour\":{},\"failed\":\"{}\",\"pass\":{}}",
            r.queue.size(), r.tried, r.passed, r.landed, t, String.join(" ", r.failed.subList(0, Math.min(30, r.failed.size()))),
            r.tried == r.queue.size() && r.passed == r.tried);
        run = null;
        resultLogged = true;
    }
}
