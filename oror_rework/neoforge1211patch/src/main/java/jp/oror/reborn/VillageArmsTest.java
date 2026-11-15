package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Ravager;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059g) CI check "villagearms" (/oror villagearms test, VILLAGE-ARMS-RESULT), the user: "村人たちが銃を作ったり戦車を作ったり
 * できるか". A village of seven (three of them strong: a weaponsmith, an armorer, a mason; a Guard Villagers guard beside them)
 * on open ground away from the capital, its chests holding iron, gunpowder, redstone, gold and emeralds; the village's own
 * reviews run every two seconds as its survey would (VillageArms, then VillageVehicles), the gunsmith's minute between guns
 * shortened to those two seconds.
 * <ul>
 * <li>Guns: unlocked (six people, metal, emeralds), the gunsmith's table set down, three guns made: the guard's first, then
 * the strongest villagers'.</li>
 * <li>Tank: the village made a castle town (城下町, stage 3), it builds its tank from its chests (iron 96, gunpowder 24,
 * redstone 16, emeralds 48); a ravager (kept still, made whole every tick) comes 30 blocks from the village: the tank
 * is brought out, two strong villagers board it, it drives at the ravager and its gun hits it.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillageArmsTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Village");
    public static volatile boolean resultLogged;
    private static Run run;

    private static final class Run {
        ServerLevel level;
        long started, phaseAt;
        String phase = "guns";
        VillageLedger.Village home;
        VillageProgress.Record rec;
        BlockPos center;
        final List<ChunkPos> forced = new ArrayList<>();
        final List<Entity> made = new ArrayList<>();
        final List<String> phases = new ArrayList<>();
        Mob guard;
        Ravager threat;
        UUID tank;
        String tankType = "", why = "";
        long unlockedAt = -1, tableAt = -1, builtAt = -1, outAt = -1, boardedAt = -1, firstHitAt = -1;
        int maxAboard, tankHits, otherHits, ironBefore, ironAfter;
        double moved, closest = -1;
        float tankDamage;
        boolean guardArmed;
        int villagersArmed;
        final List<String> guns = new ArrayList<>();
        final java.util.TreeSet<String> otherBy = new java.util.TreeSet<>();
        net.minecraft.world.phys.Vec3 tankFrom;
    }

    private VillageArmsTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("villagearms").requires(s -> s.hasPermission(2))
            .then(Commands.literal("test").executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        if (!VillageArms.present()) {
            LOG.info("VILLAGE-ARMS-RESULT {\"present\":false,\"pass\":true}");
            resultLogged = true;
            return 0;
        }
        try {
            return begin(src);
        } catch (RuntimeException ex) {
            LOG.warn("VILLAGE-ARMS failed to start", ex);
            LOG.info("VILLAGE-ARMS-RESULT {\"present\":true,\"error\":\"" + ex.toString().replace('"', '\'') + "\",\"pass\":false}");
            resultLogged = true;
            return 0;
        }
    }

    private static int begin(CommandSourceStack src) {
        ServerLevel level = src.getServer().overworld();
        Run r = new Run();
        r.level = level;
        BlockPos a = dry(level, BlockPos.containing(src.getPosition()));
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                ChunkPos p = new ChunkPos((a.getX() >> 4) + dx, (a.getZ() >> 4) + dz);
                if (level.setChunkForced(p.x, p.z, true)) {
                    r.forced.add(p);
                }
            }
        }
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, a.getX(), a.getZ());
        a = new BlockPos(a.getX(), y, a.getZ());
        // a level green of 70 x 70, open to the sky: the village, its motor pool and the field before it
        for (int x = -35; x <= 35; x++) {
            for (int z = -35; z <= 35; z++) {
                level.setBlock(a.offset(x, -1, z), Blocks.GRASS_BLOCK.defaultBlockState(), 2);
                level.setBlock(a.offset(x, -2, z), Blocks.DIRT.defaultBlockState(), 2);
                for (int h = 0; h < 14; h++) {
                    level.setBlock(a.offset(x, h, z), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        r.center = a;
        level.setBlock(a, Blocks.BELL.defaultBlockState(), 3);
        chest(level, a.offset(-2, 0, -3), new Object[][]{{Items.IRON_INGOT, 64}, {Items.IRON_INGOT, 64}, {Items.IRON_INGOT, 64}, {Items.IRON_INGOT, 32},
            {Items.GOLD_INGOT, 32}});
        chest(level, a.offset(2, 0, -3), new Object[][]{{Items.GUNPOWDER, 64}, {Items.REDSTONE, 64}, {Items.EMERALD, 64}, {Items.EMERALD, 64},
            {Items.EMERALD, 32}, {Items.BREAD, 64}, {Items.COAL_BLOCK, 16}});
        r.home = VillageLedger.get(level).register(a);
        VillageLedger.get(level).setDirty();
        r.rec = VillageProgress.get(level).of(r.home);
        r.rec.stage = Math.max(r.rec.stage, 2);
        // (CI 46: a town sends its strong to a dungeon, and all three were away when the tank was wanted) no expedition in
        // the check; the village keeps two of its strong at home once it has a vehicle all the same (VillageHomeGuard)
        r.rec.nextTrip = Long.MAX_VALUE;
        VillageProgress.get(level).setDirty();
        VillagerProfession[] jobs = {VillagerProfession.WEAPONSMITH, VillagerProfession.ARMORER, VillagerProfession.MASON, VillagerProfession.FARMER,
            VillagerProfession.FARMER, VillagerProfession.LIBRARIAN, VillagerProfession.FISHERMAN};
        for (int i = 0; i < jobs.length; i++) {
            Villager v = EntityType.VILLAGER.create(level);
            if (v == null) {
                continue;
            }
            v.setVillagerData(v.getVillagerData().setProfession(jobs[i]).setLevel(3));
            v.moveTo(a.getX() + 0.5 + (i - 3) * 2, a.getY(), a.getZ() + 5.5, 0F, 0F);
            v.setPersistenceRequired();
            v.getPersistentData().putUUID("OrorVillage", r.home.id);
            level.addFreshEntity(v);
            r.made.add(v);
        }
        EntityType<?> guardType = BuiltInRegistries.ENTITY_TYPE.getOptional(ResourceLocation.parse("guardvillagers:guard")).orElse(null);
        if (guardType != null && guardType.create(level) instanceof Mob g) {
            g.moveTo(a.getX() + 0.5, a.getY(), a.getZ() + 8.5, 0F, 0F);
            g.setPersistenceRequired();
            g.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, new ItemStack(Items.IRON_SWORD));
            level.addFreshEntity(g);
            r.guard = g;
            r.made.add(g);
        }
        level.setDayTime(1000);
        r.started = level.getGameTime();
        r.phaseAt = r.started;
        run = r;
        LOG.info("VILLAGE-ARMS-START {\"at\":[{},{},{}],\"people\":{},\"guard\":{}}", a.getX(), a.getY(), a.getZ(), jobs.length, r.guard != null);
        return 1;
    }

    private static void chest(ServerLevel level, BlockPos at, Object[][] goods) {
        level.setBlock(at, Blocks.CHEST.defaultBlockState(), 3);
        if (level.getBlockEntity(at) instanceof ChestBlockEntity c) {
            for (int i = 0; i < goods.length; i++) {
                c.setItem(i, new ItemStack((Item) goods[i][0], (Integer) goods[i][1]));
            }
        }
    }

    /** Open, dry, level ground well away from the capital (and from the other village checks' fields). */
    private static BlockPos dry(ServerLevel level, BlockPos from) {
        int[][] offsets = {{-3000, 1800}, {1800, -3000}, {-3000, -1000}, {3200, 1200}, {-1000, 3200}, {1200, -3400}};
        jp.oror.reborn.citadel.CitadelSites.Site capital = jp.oror.reborn.citadel.CitadelSites.capital();
        BlockPos best = from.offset(offsets[0][0], 0, offsets[0][1]);
        int bestScore = Integer.MAX_VALUE;
        for (int[] o : offsets) {
            BlockPos c = from.offset(o[0], 0, o[1]);
            if (capital != null && capital.center().distSqr(new BlockPos(c.getX(), capital.center().getY(), c.getZ())) < 1300 * 1300) {
                continue;
            }
            int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE, wet = 0;
            for (int dx = -35; dx <= 35; dx += 35) {
                for (int dz = -35; dz <= 35; dz += 35) {
                    int h = level.getChunkSource().getGenerator().getBaseHeight(c.getX() + dx, c.getZ() + dz, Heightmap.Types.OCEAN_FLOOR_WG, level,
                        level.getChunkSource().randomState());
                    lo = Math.min(lo, h);
                    hi = Math.max(hi, h);
                    wet += h <= level.getSeaLevel() ? 1 : 0;
                }
            }
            int score = hi - lo + wet * 100;
            if (score < bestScore) {
                bestScore = score;
                best = c;
            }
        }
        return best;
    }

    private static void phase(Run r, String next) {
        r.phases.add("[" + (r.level.getGameTime() - r.started) + ",\"" + next + "\"]");
        r.phase = next;
        r.phaseAt = r.level.getGameTime();
    }

    @SubscribeEvent
    public static void hurt(LivingDamageEvent.Post e) {
        Run r = run;
        if (r == null || r.threat == null || e.getEntity() != r.threat) {
            return;
        }
        Entity tank = r.tank == null ? null : r.level.getEntity(r.tank);
        Entity by = e.getSource().getEntity(), direct = e.getSource().getDirectEntity();
        boolean fromTank = tank != null && (by == tank || direct == tank || tank.getPassengers().contains(by)
            || direct != null && "superbwarfare".equals(BuiltInRegistries.ENTITY_TYPE.getKey(direct.getType()).getNamespace())
            && by != null && tank.getPassengers().contains(by));
        if (fromTank) {
            r.tankHits++;
            r.tankDamage += e.getNewDamage();
            if (r.firstHitAt < 0) {
                r.firstHitAt = r.level.getGameTime() - r.started;
            }
        } else {
            r.otherHits++;
            if (r.otherBy.size() < 6 && by != null) {
                r.otherBy.add(BuiltInRegistries.ENTITY_TYPE.getKey(by.getType()).getPath()
                    + (by instanceof net.minecraft.world.entity.LivingEntity le ? "/" + BuiltInRegistries.ITEM.getKey(le.getMainHandItem().getItem()).getPath() : ""));
            }
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long now = r.level.getGameTime(), t = now - r.started, in = now - r.phaseAt;
        try {
            step(r, now, t, in);
        } catch (RuntimeException ex) {
            LOG.warn("VILLAGE-ARMS step failed", ex);
            finish(r, t, ex.toString());
            return;
        }
        if (run != null && t > 3600) {
            finish(r, t, "timeout");
        }
    }

    private static void step(Run r, long now, long t, long in) {
        if (r.threat != null && r.threat.isAlive() && r.threat.getHealth() < r.threat.getMaxHealth()) {
            r.threat.setHealth(r.threat.getMaxHealth());
        }
        if (t % 40 == 5) {
            VillageWork.Survey s = VillageWork.survey(r.level, r.home);
            if (s != null) {
                if (r.phase.equals("guns")) {
                    s.nextGun = 0;                    // the gunsmith's minute between guns: two seconds in the check
                    int before = r.rec.gunsMade;
                    VillageArms.review(r.level, s, r.rec);
                    if (r.rec.guns && r.unlockedAt < 0) {
                        r.unlockedAt = t;
                    }
                    if (r.rec.gunTable != null && r.tableAt < 0) {
                        r.tableAt = t;
                    }
                    if (r.rec.gunsMade > before) {
                        r.guns.add(t + "");
                    }
                } else {
                    if (r.ironBefore == 0) {
                        r.ironBefore = s.stock("iron_ingot");
                    }
                    VillageVehicles.review(r.level, s, r.rec);
                    if (r.rec.vehicles != null && r.rec.vehicles.contains("tank") && r.builtAt < 0) {
                        r.builtAt = t;
                        VillageWork.Survey after = VillageWork.survey(r.level, r.home);
                        r.ironAfter = after != null ? after.stock("iron_ingot") : -1;
                    }
                }
            }
        }
        switch (r.phase) {
            case "guns" -> {
                if (r.rec.gunsMade >= 3 || in > 800) {
                    r.guardArmed = r.guard != null && MobEquipmentUse.kind(r.guard.getMainHandItem()).equals("gun");
                    for (Entity m : r.made) {
                        if (m instanceof Villager v && VillageArms.armed(v)) {
                            r.villagersArmed++;
                        }
                    }
                    r.rec.stage = Math.max(r.rec.stage, 3);
                    // (CI 44: a castle town sends its strongest out on an expedition, and the tank found no crew: the
                    // strong villagers' reasons are logged in VILLAGE-ARMS-WAIT) no expedition while the tank is tried
                    r.rec.nextTrip = Long.MAX_VALUE;
                    VillageProgress.get(r.level).setDirty();
                    phase(r, "tank");
                }
            }
            case "tank" -> {
                if (r.builtAt >= 0) {
                    Ravager rv = EntityType.RAVAGER.create(r.level);
                    if (rv != null) {
                        rv.moveTo(r.center.getX() + 30.5, r.center.getY(), r.center.getZ() + 0.5, 90F, 0F);
                        rv.setNoAi(true);
                        rv.setPersistenceRequired();
                        var max = rv.getAttribute(Attributes.MAX_HEALTH);
                        if (max != null) {
                            max.setBaseValue(190.0);      // under 200: a jet is sent at 200 or more, a tank at 80 or more
                        }
                        rv.setHealth(rv.getMaxHealth());
                        r.level.addFreshEntity(rv);
                        r.threat = rv;
                        r.made.add(rv);
                        for (Entity m : r.made) {
                            if (m instanceof Villager v) {
                                rv.setTarget(v);             // it means the village harm (a ravager is an enemy anyway)
                                break;
                            }
                        }
                    }
                    phase(r, "sortie");
                } else if (in > 400) {
                    finish(r, now - r.started, "no tank built");
                }
            }
            case "sortie" -> {
                if (r.rec.sortie != null && r.rec.sortie.hasUUID("Vehicle")) {
                    r.tank = r.rec.sortie.getUUID("Vehicle");
                    Entity tank = r.level.getEntity(r.tank);
                    if (tank != null) {
                        if (r.outAt < 0) {
                            r.outAt = t;
                            r.tankFrom = tank.position();
                            r.tankType = BuiltInRegistries.ENTITY_TYPE.getKey(tank.getType()).getPath();
                        }
                        int aboard = (int) tank.getPassengers().stream().filter(p -> p instanceof Villager).count();
                        r.maxAboard = Math.max(r.maxAboard, aboard);
                        if (aboard >= 2 && r.boardedAt < 0) {
                            r.boardedAt = t;
                        }
                        r.moved = Math.max(r.moved, tank.position().distanceTo(r.tankFrom));
                        if (r.threat != null) {
                            double d = tank.distanceTo(r.threat);
                            r.closest = r.closest < 0 ? d : Math.min(r.closest, d);
                        }
                        if (t % 100 == 0) {
                            LOG.info(String.format(Locale.ROOT, "VILLAGE-ARMS-TRACK {\"t\":%d,\"phase\":\"%s\",\"tank\":\"%s\",\"aboard\":%d,\"moved\":%.1f,"
                                    + "\"toThreat\":%.1f,\"tankHits\":%d,\"otherHits\":%d}", t, r.rec.sortie.getString("Phase"), r.tankType, aboard, r.moved,
                                r.threat == null ? -1 : tank.distanceTo(r.threat), r.tankHits, r.otherHits));
                        }
                    }
                }
                if (r.outAt < 0 && in % 200 == 60) {
                    r.why = why(r, now);
                    LOG.info("VILLAGE-ARMS-WAIT {}", r.why);
                }
                if (r.tankHits >= 3 || in > 1800) {
                    finish(r, t, r.outAt < 0 ? r.why : "");
                }
            }
            default -> {
            }
        }
    }

    private static void finish(Run r, long t, String note) {
        boolean pass = r.unlockedAt >= 0 && r.tableAt >= 0 && r.rec.gunsMade >= 2 && (r.guard == null || r.guardArmed) && r.villagersArmed >= 1
            && r.builtAt >= 0 && r.outAt >= 0 && r.maxAboard >= 2 && r.tankHits > 0;
        LOG.info(String.format(Locale.ROOT, "VILLAGE-ARMS-RESULT {\"present\":true,\"seconds\":%.1f,\"phases\":[%s],\"unlocked\":%.1f,\"table\":%.1f,"
                + "\"gunsMade\":%d,\"gunsAt\":\"%s\",\"guard\":%b,\"guardArmed\":%b,\"villagersArmed\":%d,\"stage\":%d,\"vehicles\":\"%s\",\"built\":%.1f,"
                + "\"ironBefore\":%d,\"ironAfter\":%d,\"tank\":\"%s\",\"out\":%.1f,\"boarded\":%.1f,\"maxAboard\":%d,\"moved\":%.1f,\"closest\":%.1f,"
                + "\"tankHits\":%d,\"tankDamage\":%.0f,\"firstHit\":%.1f,\"otherHits\":%d,\"otherBy\":\"%s\",\"note\":\"%s\",\"pass\":%b}",
            t / 20.0, String.join(",", r.phases), sec(r.unlockedAt), sec(r.tableAt), r.rec.gunsMade, String.join(" ", r.guns), r.guard != null,
            r.guardArmed, r.villagersArmed, r.rec.stage, r.rec.vehicles == null ? "" : r.rec.vehicles, sec(r.builtAt), r.ironBefore, r.ironAfter,
            r.tankType, sec(r.outAt), sec(r.boardedAt), r.maxAboard, r.moved, r.closest, r.tankHits, r.tankDamage, sec(r.firstHitAt), r.otherHits,
            String.join(" ", r.otherBy),
            note.replace('"', '\''), pass));
        Entity tank = r.tank == null ? null : r.level.getEntity(r.tank);
        if (tank != null) {
            for (Entity p : List.copyOf(tank.getPassengers())) {
                p.stopRiding();
            }
            tank.discard();
        }
        for (Entity m : r.made) {
            if (!m.isRemoved()) {
                m.discard();
            }
        }
        r.rec.sortie = null;
        VillageLedger.get(r.level).villages.remove(r.home.id);
        VillageLedger.get(r.level).setDirty();
        VillageProgress.get(r.level).villages.remove(r.home.id);
        VillageProgress.get(r.level).setDirty();
        for (ChunkPos p : r.forced) {
            r.level.setChunkForced(p.x, p.z, false);
        }
        run = null;
        resultLogged = true;
    }

    /** (CI 43: the tank was built and never brought out) what the village's sortie asks for, as it stands. */
    private static String why(Run r, long now) {
        StringBuilder b = new StringBuilder("{");
        net.minecraft.world.entity.LivingEntity th = VillageVehicles.threat(r.level, r.home);
        b.append("\"threat\":\"").append(th == null ? "none" : BuiltInRegistries.ENTITY_TYPE.getKey(th.getType()).getPath()).append('"');
        b.append(",\"nextSortie\":").append(r.rec.nextSortie - now);
        b.append(",\"vehicles\":\"").append(r.rec.vehicles).append('"');
        b.append(",\"sortie\":").append(r.rec.sortie != null);
        try {
            VillageWork.Survey s = VillageWork.survey(r.level, r.home);
            java.lang.reflect.Method pool = VillageVehicles.class.getDeclaredMethod("pool", ServerLevel.class, VillageWork.Survey.class);
            pool.setAccessible(true);
            Object at = s == null ? null : pool.invoke(null, r.level, s);
            b.append(",\"pool\":\"").append(at instanceof BlockPos p ? p.toShortString() : "none").append('"');
        } catch (ReflectiveOperationException | RuntimeException ex) {
            b.append(",\"pool\":\"").append(ex.getClass().getSimpleName()).append('"');
        }
        // each strong villager as the sortie's crew test sees him: what keeps him from the tank
        b.append(",\"strong\":[");
        boolean first = true;
        for (Entity m : r.made) {
            if (m instanceof Villager v && VillageAI.strong(v)) {
                net.minecraft.nbt.CompoundTag d = VillagerLife.data(v);
                List<String> no = new ArrayList<>();
                if (!v.isAlive() || v.isRemoved()) {
                    no.add("gone");
                }
                if (v.isSleeping()) {
                    no.add("asleep");
                }
                if (VillagerIndustry.miner(v)) {
                    no.add("miner");
                }
                if (v.isPassenger()) {
                    no.add("riding");
                }
                if (d.contains("Trip")) {
                    no.add("trip");
                }
                if (d.hasUUID("Flight")) {
                    no.add("flight");
                }
                if (d.hasUUID("Sortie")) {
                    no.add("sortie");
                }
                if (v.getPersistentData().getBoolean("OrorWanderer")) {
                    no.add("wanderer");
                }
                if (VillageLedger.of(v) != r.home) {
                    no.add("otherVillage");
                }
                b.append(first ? "" : ",").append('"').append(v.getVillagerData().getProfession()).append(':').append(no.isEmpty() ? "free" : String.join("+", no))
                    .append('"');
                first = false;
            }
        }
        b.append("],\"trip\":").append(r.rec.trip != null).append('}');
        return b.toString();
    }

    private static double sec(long ticks) {
        return ticks < 0 ? -1 : ticks / 20.0;
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        run = null;
    }
}
