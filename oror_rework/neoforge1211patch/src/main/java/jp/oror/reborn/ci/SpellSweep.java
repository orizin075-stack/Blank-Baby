package jp.oror.reborn.ci;

import io.redspace.ironsspellbooks.api.spells.SpellData;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.royal.RoyalSpellSafety;
import jp.oror.reborn.royal.RoyalSpells;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (053) /oror spells test: every spell the royals could cast before 053 (each role's whole old catalogue), cast in
 * turn by a royal of that role at a zombie six blocks off, each by a fresh royal, a few seconds each. A royal taken out
 * of the world while casting (its tick threw: CrashNet keeps the server up and logs the error just above) or a cast
 * that throws as it starts is a failure; whether the spell is still the royals' (RoyalSpellSafety) is noted beside it.
 * SPELL-TRY / SPELL-END lines per spell, SPELL-SWEEP-RESULT {...} at the end.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class SpellSweep {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Spells");
    public static volatile boolean resultLogged;

    record Try(RoyalRole role, SpellData spell) {
    }

    private static final class Run {
        ServerLevel level;
        BlockPos at;
        final List<Try> tries = new ArrayList<>();
        int next;
        RoyalMob caster;
        Zombie target;
        long startedAt;
        boolean started;
        final Map<String, String> failed = new TreeMap<>();
        final Map<String, Integer> perRole = new LinkedHashMap<>();
        int cast, kept;
    }

    private static Run run;

    private SpellSweep() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("spells").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        BlockPos o = BlockPos.containing(src.getPosition()).offset(4000, 0, -4000);
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                r.level.setChunkForced((o.getX() >> 4) + dx, (o.getZ() >> 4) + dz, true);
            }
        }
        r.level.getChunk(o);
        int y = Math.max(r.level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, o.getX(), o.getZ()), r.level.getSeaLevel() + 1);
        r.at = new BlockPos(o.getX(), y, o.getZ());
        for (int dx = -12; dx <= 12; dx++) {
            for (int dz = -12; dz <= 12; dz++) {
                r.level.setBlock(r.at.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 12; h++) {
                    r.level.setBlock(r.at.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        java.util.Set<String> seen = new java.util.HashSet<>();
        for (RoyalRole role : RoyalRole.values()) {
            List<SpellData> whole = RoyalSpellSafety.whole(() -> RoyalSpells.catalog(role));
            r.perRole.put(role.name(), whole.size());
            for (SpellData d : whole) {
                if (seen.add(d.getSpell().getSpellId())) {
                    r.tries.add(new Try(role, d));
                }
            }
        }
        run = r;
        LOG.info("SPELL-SWEEP-START {\"spells\":{},\"perRole\":{}}", r.tries.size(), r.perRole);
        return 1;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime();
        if (r.caster == null) {
            if (r.next >= r.tries.size()) {
                finish(r);
                return;
            }
            Try t = r.tries.get(r.next);
            EntityType<RoyalMob> type = RoyalRegistry.TYPES.get(t.role());
            r.caster = type == null ? null : type.create(r.level);
            r.target = EntityType.ZOMBIE.create(r.level);
            if (r.caster == null || r.target == null) {
                r.failed.put(t.spell().getSpell().getSpellId(), "could not make the caster");
                r.next++;
                r.caster = null;
                return;
            }
            r.caster.moveTo(r.at.getX() + 0.5, r.at.getY(), r.at.getZ() + 0.5, -90F, 0F);
            r.target.moveTo(r.at.getX() + 6.5, r.at.getY(), r.at.getZ() + 0.5, 90F, 0F);
            r.target.setNoAi(true);
            r.target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(2000);
            r.target.setHealth(2000F);
            r.level.addFreshEntity(r.caster);
            r.level.addFreshEntity(r.target);
            r.caster.setTarget(r.target);
            r.startedAt = now;
            r.started = false;
            String id = t.spell().getSpell().getSpellId();
            LOG.info("SPELL-TRY {} {} {}", t.role().name(), id, t.spell().getLevel());
            try {
                RoyalSpellSafety.whole(() -> {
                    r.caster.initiateCastSpell(t.spell().getSpell(), t.spell().getLevel());
                    return null;
                });
                r.started = r.caster.isCasting();
            } catch (RuntimeException | LinkageError ex) {
                r.failed.put(id, "starting: " + ex);
                LOG.error("SPELL-THREW " + id, ex);
            }
            return;
        }
        Try t = r.tries.get(r.next);
        String id = t.spell().getSpell().getSpellId();
        boolean gone = r.caster.isRemoved() && r.caster.getHealth() > 0;
        long age = now - r.startedAt;
        if (gone || age >= 70 || age >= 25 && !r.caster.isCasting()) {
            if (gone) {
                r.failed.put(id, "the caster's tick threw (taken out)");
            }
            boolean keep = RoyalSpellSafety.allowed(t.spell());
            if (r.started) {
                r.cast++;
            }
            if (keep) {
                r.kept++;
            }
            LOG.info("SPELL-END {} started={} failed={} kept={} ticks={}", id, r.started, r.failed.containsKey(id), keep, age);
            if (!r.caster.isRemoved()) {
                r.caster.cancelCast();
            }
            for (Entity x : r.level.getEntities((Entity) null, new AABB(r.at).inflate(24), x -> !(x instanceof Player))) {
                x.discard();
            }
            r.caster = null;
            r.target = null;
            r.next++;
        }
    }

    private static void finish(Run r) {
        run = null;
        StringBuilder f = new StringBuilder("{");
        for (Map.Entry<String, String> en : r.failed.entrySet()) {
            if (f.length() > 1) {
                f.append(',');
            }
            f.append('"').append(en.getKey()).append("\":\"").append(en.getValue().replace("\"", "'")).append('"');
        }
        f.append('}');
        List<String> failedKept = new ArrayList<>();
        for (Try t : r.tries) {
            if (r.failed.containsKey(t.spell().getSpell().getSpellId()) && RoyalSpellSafety.allowed(t.spell())) {
                failedKept.add(t.spell().getSpell().getSpellId());
            }
        }
        LOG.info(String.format(Locale.ROOT, "SPELL-SWEEP-RESULT {\"tried\":%d,\"castStarted\":%d,\"keptForRoyals\":%d,\"failed\":%s,\"failedButKept\":%s,"
            + "\"pass\":%b}", r.tries.size(), r.cast, r.kept, f, failedKept.stream().map(s -> "\"" + s + "\"").toList(), failedKept.isEmpty()));
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                r.level.setChunkForced((r.at.getX() >> 4) + dx, (r.at.getZ() >> 4) + dz, false);
            }
        }
        resultLogged = true;
    }
}
