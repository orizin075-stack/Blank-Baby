package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.combat.Exhaustion;
import jp.oror.reborn.combat.MobStamina;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r73) CI check "stamina" (/oror stamina test, STAMINA-RESULT): Exhaustion and the mobs' stamina for everyone. On a
 * cleared floor: a zombie emptied (winded) strikes a cow, a fresh zombie strikes another (the winded blow lands at six
 * tenths); the winded zombie takes a blow (a quarter harder); a cow driven at a run for three seconds (its stamina worn
 * down, though it fights nothing); a fake player emptied (exhausted) strikes a cow (half its weight, its stamina back to
 * nothing), then given back half its stamina gets its wind back; and Epic Fight's player patch has the stamina it reads.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class StaminaTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Stamina");
    public static volatile boolean resultLogged;
    private static ServerLevel level;
    private static BlockPos site;
    private static long started = -1;
    private static FakePlayer fp;
    private static Mob runner;
    private static final List<Entity> MADE = new ArrayList<>();
    private static final List<ChunkPos> FORCED = new ArrayList<>();
    private static final Map<String, Object> OUT = new LinkedHashMap<>();

    private StaminaTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("stamina").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (started >= 0) {
            return 0;
        }
        ServerLevel lv = src.getServer().overworld();
        level = lv;
        OUT.clear();
        BlockPos c = BlockPos.containing(src.getPosition()).offset(-2600, 0, 2900);
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                ChunkPos p = new ChunkPos((c.getX() >> 4) + dx, (c.getZ() >> 4) + dz);
                if (lv.setChunkForced(p.x, p.z, true)) {
                    FORCED.add(p);
                }
            }
        }
        int y = lv.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ());
        site = new BlockPos(c.getX(), Math.max(y, lv.getSeaLevel() + 1), c.getZ());
        for (BlockPos q : BlockPos.betweenClosed(site.offset(-12, -1, -12), site.offset(12, -1, 12))) {
            lv.setBlock(q, Blocks.STONE.defaultBlockState(), 2);
        }
        for (BlockPos q : BlockPos.betweenClosed(site.offset(-12, 0, -12), site.offset(12, 6, 12))) {
            lv.setBlock(q, Blocks.AIR.defaultBlockState(), 2);
        }
        started = lv.getGameTime();
        try {
            mobs(lv);
            player(lv);
        } catch (RuntimeException ex) {
            OUT.put("error", "\"" + ex.toString().replace('"', '\'') + "\"");
            LOG.warn("STAMINA-TEST failed", ex);
        }
        return 1;
    }

    private static Mob make(ServerLevel lv, EntityType<? extends Mob> type, double dx, double dz, boolean noAi) {
        Mob m = type.create(lv);
        m.moveTo(site.getX() + 0.5 + dx, site.getY(), site.getZ() + 0.5 + dz, 0F, 0F);
        m.setNoAi(noAi);
        m.setPersistenceRequired();
        lv.addFreshEntity(m);
        MADE.add(m);
        return m;
    }

    private static float struck(Mob victim, net.minecraft.world.damagesource.DamageSource source, float amount) {
        float before = victim.getHealth();
        victim.invulnerableTime = 0;
        victim.hurt(source, amount);
        return before - victim.getHealth();
    }

    private static void mobs(ServerLevel lv) {
        Mob tired = make(lv, EntityType.ZOMBIE, -6, 0, true), fresh = make(lv, EntityType.ZOMBIE, -6, 4, true);
        Mob cowA = make(lv, EntityType.COW, -4, 0, true), cowB = make(lv, EntityType.COW, -4, 4, true);
        MobStamina.empty(tired);
        OUT.put("zombieWinded", MobStamina.winded(tired));
        float a = struck(cowA, lv.damageSources().mobAttack(tired), 4F), b = struck(cowB, lv.damageSources().mobAttack(fresh), 4F);
        OUT.put("windedBlow", String.format(java.util.Locale.ROOT, "%.2f", a));
        OUT.put("freshBlow", String.format(java.util.Locale.ROOT, "%.2f", b));
        OUT.put("windedBlowWeaker", a > 0 && a < b * 0.75F);
        float taken = struck(tired, lv.damageSources().magic(), 4F);
        OUT.put("windedTaken", String.format(java.util.Locale.ROOT, "%.2f", taken));
        OUT.put("windedTakesMore", taken > 4.5F);
        runner = make(lv, EntityType.COW, 0, -8, false);
        OUT.put("runnerStart", MobStamina.fraction(runner));
    }

    private static void player(ServerLevel lv) {
        fp = new FakePlayer(lv, new GameProfile(UUID.nameUUIDFromBytes("oror_stamina_tester".getBytes()), "[Stamina Tester]"));
        fp.moveTo(site.getX() + 4.5, site.getY(), site.getZ() + 0.5, 0F, 0F);
        fp.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);
        Exhaustion.forget(fp);
        Exhaustion.put(fp, 0F);
        Exhaustion.check(fp);
        OUT.put("playerExhausted", Exhaustion.exhausted(fp));
        Mob cowC = make(lv, EntityType.COW, 6, 0, true), cowD = make(lv, EntityType.COW, 6, 4, true);
        float a = struck(cowC, lv.damageSources().playerAttack(fp), 4F);
        OUT.put("playerExhaustedBlow", String.format(java.util.Locale.ROOT, "%.2f", a));
        OUT.put("playerBlowHalved", a > 1.5F && a < 2.5F);
        OUT.put("playerStaminaReset", Exhaustion.of(fp)[0] <= 0.01F);
        // (CI) not by listing PlayerPatch's methods: that loads client classes on a dedicated server; EfStamina looked up its
        // three by name on the fake player's own patch
        Exhaustion.of(fp);
        boolean efHas = "found".equals(jp.oror.reborn.EfStamina.state());
        OUT.put("efPlayerStamina", efHas);
        OUT.put("cowD", cowD.getId());
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Pre e) {
        if (started < 0 || level == null) {
            return;
        }
        long t = level.getGameTime() - started;
        if (runner != null && runner.isAlive() && t < 60) {
            // driven at a run: a beast in panic
            runner.setDeltaMovement(0.6, runner.getDeltaMovement().y, 0.0);
            if (runner.getX() > site.getX() + 10) {
                runner.teleportTo(site.getX() - 10, site.getY(), runner.getZ());
            }
        }
        if (t == 70) {
            OUT.put("runnerAfter", String.format(java.util.Locale.ROOT, "%.3f", MobStamina.fraction(runner)));
            OUT.put("runnerAt", String.format(java.util.Locale.ROOT, "%.1f %.1f %.1f ground %b alive %b", runner.getX() - site.getX(), runner.getY() - site.getY(),
                runner.getZ() - site.getZ(), runner.onGround(), runner.isAlive()));
            OUT.put("runningWears", MobStamina.fraction(runner) < 0.97F);
            // the player's wind back: half its stamina, a second and a half on
            float[] s = Exhaustion.of(fp);
            Exhaustion.put(fp, s[1] * 0.5F);
            Exhaustion.check(fp);
            OUT.put("playerWindBack", !Exhaustion.exhausted(fp));
            finish();
        }
    }

    private static void finish() {
        boolean pass = !OUT.containsKey("error") && ok("zombieWinded") && ok("windedBlowWeaker") && ok("windedTakesMore") && ok("runningWears")
            && ok("playerExhausted") && ok("playerBlowHalved") && ok("playerStaminaReset") && ok("playerWindBack") && ok("efPlayerStamina");
        StringBuilder s = new StringBuilder("{\"present\":true");
        OUT.forEach((k, v) -> s.append(",\"").append(k).append("\":").append(v instanceof String str ? "\"" + str + "\"" : v));
        s.append(",\"exhaustedBlows\":").append(Exhaustion.exhaustedBlows).append(",\"exhaustedHits\":").append(Exhaustion.exhaustedHits)
            .append(",\"pass\":").append(pass).append('}');
        LOG.info("STAMINA-RESULT {}", s);
        for (Entity x : MADE) {
            if (!x.isRemoved()) {
                x.discard();
            }
        }
        MADE.clear();
        for (ChunkPos p : FORCED) {
            level.setChunkForced(p.x, p.z, false);
        }
        FORCED.clear();
        if (fp != null) {
            Exhaustion.forget(fp);
        }
        started = -1;
        resultLogged = true;
    }

    private static boolean ok(String k) {
        return Boolean.TRUE.equals(OUT.get(k));
    }
}
