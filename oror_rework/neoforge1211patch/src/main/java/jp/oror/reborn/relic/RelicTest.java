package jp.oror.reborn.relic;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.RelicArts;
import jp.oror.reborn.RelicSpec;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (058) /oror relics test, the CI check "relics": every relic of the V9 design put to work by a stand-in player, eight
 * lanes at a time, against husks that count the blows they are dealt and refuse them.
 *
 * <ul>
 * <li>the 123 techniques: each readied by its key's own path (the weapon in hand), released, and judged by what it
 * did: blows on its dummy, effects and broken armour on it, windows opened on its bearer, units or fields set down,
 * contracts offered (RELIC-TECH, one line each);</li>
 * <li>the 41 focuses: the V8 Lv125 punishment on a foe in its fan, and the V9 hold on a strong one;</li>
 * <li>the 41 charms: the crisis guard of its kind, set off by a blow that takes the wearer low;</li>
 * <li>the 41 legends: three uses, three stages in turn, the third's crowning attack begun;</li>
 * <li>the 164 relics' right-click arts without an unknown op; the reward enchantments; the punishment's own clock.</li>
 * </ul>
 * RELIC-RESULT {...} with a pass.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RelicTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Relics");
    public static volatile boolean resultLogged;
    private static final int LANES = 8;

    static final class Tester extends FakePlayer {
        Tester(ServerLevel level, int n) {
            super(level, new GameProfile(UUID.fromString("0f0e0d0c-0b0a-4958-8706-0504030301" + String.format("%02x", n)), "[OROR Relic " + n + "]"));
            this.invulnerableTime = 0;
            try {
                java.lang.reflect.Field f = ServerPlayer.class.getDeclaredField("spawnInvulnerableTime");
                f.setAccessible(true);
                f.setInt(this, 0);
            } catch (ReflectiveOperationException | RuntimeException ex) {
                LOG.warn("RELIC-UNSHIELD {}", ex.toString());
            }
        }

        @Override
        public boolean isInvulnerableTo(net.minecraft.world.damagesource.DamageSource source) {
            return false;
        }
    }

    private static final class Job {
        final String kind, id;
        final int slot;
        long t0 = -1, until;
        boolean done;
        String verdict = "", why = "";

        Job(String kind, String id, int slot) {
            this.kind = kind;
            this.id = id;
            this.slot = slot;
        }
    }

    private static final class Lane {
        int n;
        BlockPos at;
        Tester p, signer;
        Mob dummy, strong;
        final List<Job> jobs = new ArrayList<>();
        int next;
        Job job;
        // what the job's start saw
        int hits, effects, harmful, units, fields, offered, crisis, ultimates, stageBefore;
        float hpBefore, dealt;
        boolean modsBefore;
    }

    private static final List<Lane> LANES_ = new ArrayList<>();
    private static final Map<Integer, Integer> HITS = new HashMap<>();
    /** each dummy's lane player: only its blows count on it */
    private static final Map<Integer, Player> OWNER = new HashMap<>();
    private static final Map<Integer, Float> DEALT = new HashMap<>();
    private static final Map<String, int[]> TALLY = new LinkedHashMap<>();
    private static final List<String> FAILED = new ArrayList<>();
    private static final List<int[]> CHUNKS = new ArrayList<>();
    private static long started = -1;
    private static ServerLevel level;
    private static final Map<String, Object> EXTRA = new LinkedHashMap<>();

    private RelicTest() {
    }

    /** The stand-ins a contract may be offered to (fake players are in no level's list of players). */
    static List<ServerPlayer> signers(Player owner) {
        for (Lane l : LANES_) {
            if (l.p == owner && l.signer != null) {
                return List.of(l.signer);
            }
        }
        return List.of();
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("relics").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (started >= 0) {
            return 0;
        }
        level = src.getServer().overworld();
        BlockPos o = BlockPos.containing(src.getPosition()).offset(-7000, 0, 7000);
        List<Job> all = new ArrayList<>();
        for (RelicV9.Tech t : RelicV9.TECHS) {
            all.add(new Job("tech", t.relic, t.slot));
        }
        for (RelicV9.Info i : RelicV9.RELICS.values()) {
            if (!i.slot.equals("weapon")) {
                all.add(new Job(i.slot, i.id, 0));
            }
        }
        for (int i = 0; i < LANES; i++) {
            Lane l = new Lane();
            l.n = i;
            BlockPos c0 = o.offset((i % 4) * 80, 0, (i / 4) * 112);
            BlockPos c = new BlockPos(((c0.getX() >> 4) << 4) + 8, 0, ((c0.getZ() >> 4) << 4) + 8);
            for (int dx = -1; dx <= 1; dx++) {
                for (int dz = -1; dz <= 2; dz++) {
                    int cx = (c.getX() >> 4) + dx, cz = (c.getZ() >> 4) + dz;
                    level.setChunkForced(cx, cz, true);
                    CHUNKS.add(new int[]{cx, cz});
                }
            }
            int ground = Math.max(level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ()), level.getSeaLevel() + 1) + 3;
            l.at = new BlockPos(c.getX(), ground, c.getZ());
            for (int dx = -20; dx <= 20; dx++) {
                for (int dz = -12; dz <= 36; dz++) {
                    level.setBlock(l.at.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                    for (int h = 0; h < 12; h++) {
                        level.setBlock(l.at.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                    }
                }
            }
            l.p = new Tester(level, i * 2);
            l.signer = new Tester(level, i * 2 + 1);
            l.p.moveTo(l.at.getX() + 0.5, l.at.getY(), l.at.getZ() + 0.5, 0F, 0F);
            l.signer.moveTo(l.at.getX() - 2.5, l.at.getY(), l.at.getZ() + 0.5, 0F, 0F);
            // the other stand-in strikes the wearer in the charms' trials and takes their counters: it must outlast them
            AttributeInstance mh = l.signer.getAttribute(Attributes.MAX_HEALTH);
            if (mh != null) {
                mh.setBaseValue(1000000.0);
            }
            l.signer.setHealth(1000000.0F);
            LANES_.add(l);
        }
        for (int i = 0; i < all.size(); i++) {
            LANES_.get(i % LANES).jobs.add(all.get(i));
        }
        started = level.getGameTime();
        EXTRA.put("punishClock", punishClock());
        EXTRA.put("enchant", enchantCheck());
        EXTRA.put("anims", RelicTech.Ef.census());
        LOG.info("RELIC-START {} jobs in {} lanes at {}", all.size(), LANES, o);
        return 1;
    }

    private static Mob dummy(Lane l, double dist, boolean strong) {
        Mob m = EntityType.HUSK.create(level);
        if (m == null) {
            return null;
        }
        m.moveTo(l.at.getX() + 0.5 + (strong ? 1.5 : 0), l.at.getY(), l.at.getZ() + 0.5 + dist, 180F, 0F);
        m.finalizeSpawn(level, level.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.COMMAND, null);
        // (059c) a grown one each time: one in twenty came a child, half as tall, and so not the same target
        if (m instanceof net.minecraft.world.entity.monster.Zombie z) {
            z.setBaby(false);
        }
        m.setPersistenceRequired();
        m.setNoAi(true);
        m.addTag("oror_relic_dummy");
        if (strong) {
            AttributeInstance a = m.getAttribute(Attributes.MAX_HEALTH);
            if (a != null) {
                a.setBaseValue(600.0);
            }
            m.setHealth(600.0F);
        }
        level.addFreshEntity(m);
        OWNER.put(m.getId(), l.p);
        return m;
    }

    /** The dummies' blows are counted (from their lane's player) and refused. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void incoming(LivingIncomingDamageEvent e) {
        if (started < 0 || !e.getEntity().getTags().contains("oror_relic_dummy")) {
            return;
        }
        if (e.getSource().getEntity() instanceof Tester t && OWNER.get(e.getEntity().getId()) == t) {
            HITS.merge(e.getEntity().getId(), 1, Integer::sum);
            DEALT.merge(e.getEntity().getId(), e.getAmount(), Float::sum);
        }
        e.setCanceled(true);
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (started < 0 || resultLogged || level == null) {
            return;
        }
        long now = level.getGameTime();
        boolean busy = false;
        for (Lane l : LANES_) {
            if (l.job == null || l.job.done) {
                if (l.next >= l.jobs.size()) {
                    continue;
                }
                l.job = l.jobs.get(l.next++);
                setup(l, now);
            }
            busy = true;
            Job j = l.job;
            if (now == j.t0 + 4) {
                run(l, j, now);
            } else if (now >= j.until) {
                judge(l, j, now);
                j.done = true;
            }
        }
        if (!busy || now - started > 20 * 60 * 12) {
            finish(now);
        }
    }

    private static void setup(Lane l, long now) {
        Job j = l.job;
        j.t0 = now;
        // a fresh dummy (and a strong one) before the lane's player for each job; the player whole and unmarked
        if (l.dummy != null) {
            l.dummy.discard();
        }
        if (l.strong != null) {
            l.strong.discard();
        }
        double dist = 5.0;
        if (j.kind.equals("tech")) {
            RelicV9.Tech t = RelicV9.of(j.id)[j.slot];
            dist = Math.max(2.5, Math.min(6.0, t.range * 0.3));
        }
        l.dummy = dummy(l, dist, false);
        l.strong = dummy(l, dist + 1.0, true);
        l.p.moveTo(l.at.getX() + 0.5, l.at.getY(), l.at.getZ() + 0.5, 0F, 0F);
        // the look is the head's: a technique that turned it (a blink behind, a swap) left the next one looking away
        l.p.setYHeadRot(0F);
        l.p.yHeadRotO = 0F;
        l.p.yBodyRot = 0F;
        l.p.setXRot(0F);
        l.p.setHealth(l.p.getMaxHealth());
        l.p.removeAllEffects();
        // the last job's units and fields go (eight at most to an owner: a lane would be full of them)
        RelicWorld.clearFor(level, l.p);
        CompoundTag d = l.p.getPersistentData();
        for (String k : new ArrayList<>(d.getAllKeys())) {
            // and the last job's windows: a guard, an undying or an adaptation left by a legend's stage refused the
            // next charm's blow (the third 058 run)
            if (k.startsWith("ororTech") || k.startsWith("ororCrisis") || k.startsWith("ororUlt") || k.startsWith("ororWorn")
                || (k.startsWith("ororArt") || k.startsWith("ororRelic")) && k.endsWith("Until")) {
                d.remove(k);
            }
        }
        RelicSpec s = RelicSpec.ALL.get(j.id);
        var item = CharacterRelics.ITEMS.get(j.id);
        l.p.setItemInHand(InteractionHand.MAIN_HAND, item == null ? ItemStack.EMPTY : new ItemStack(item.get()));
        j.until = now + 60;
        if (j.kind.equals("tech")) {
            RelicV9.Tech t = RelicV9.of(j.id)[j.slot];
            j.until = now + 8 + t.windup() + t.forming() + 70;
        } else if (j.kind.equals("legend")) {
            j.until = now + 200;
        }
    }

    private static void run(Lane l, Job j, long now) {
        l.hits = HITS.getOrDefault(l.dummy.getId(), 0);
        l.effects = l.dummy.getActiveEffects().size();
        l.harmful = RelicWorld.harmful(l.dummy);
        l.units = RelicWorld.count(l.p, null);
        l.fields = RelicWorld.fields(l.p);
        l.offered = RelicWorld.contractsOffered;
        l.crisis = RelicCrisis.FIRED_BY.getOrDefault(l.p.getUUID(), 0);
        l.ultimates = RelicUltimate.started;
        l.hpBefore = l.p.getHealth();
        switch (j.kind) {
            case "tech" -> {
                // a little hurt first, so what heals shows it
                l.p.setHealth(l.p.getMaxHealth() * 0.6F);
                l.hpBefore = l.p.getHealth();
                if (!RelicTech.start(l.p, j.slot, true)) {
                    j.verdict = "no";
                    j.why = "did not begin";
                }
                if (j.id.startsWith("sweet_pact")) {
                    // the stand-in agrees to what it is offered
                    RelicTech.later(level, RelicV9.of(j.id)[j.slot].windup() + 6, () -> {
                        for (int id : RelicWorld.offeredTo(l.signer)) {
                            RelicWorld.answer(l.signer, id, true);
                        }
                        for (int id : RelicWorld.offeredTo(l.p)) {
                            RelicWorld.answer(l.p, id, true);
                        }
                    });
                }
            }
            case "focus" -> RelicArts.cast(j.id, l.p);
            case "charm" -> {
                // worn; then a blow that takes the wearer low
                CompoundTag d = l.p.getPersistentData();
                d.putString("ororWornCharm", j.id);
                d.putLong("ororWornCharmAt", now);
                l.p.setHealth(l.p.getMaxHealth());
                l.p.invulnerableTime = 0;
                // a mob's blow that takes the wearer to 28% after the difficulty's scaling (halved and one more on
                // easy, half again on hard); a stand-in's blow on a stand-in was refused (the first 058 runs)
                float want = l.p.getMaxHealth() * 0.72F;
                float blow = switch (level.getDifficulty()) {
                    case EASY -> (want - 1.0F) * 2.0F;
                    case HARD -> want / 1.5F;
                    default -> want;
                };
                boolean took = l.p.hurt(l.p.damageSources().mobAttack(l.dummy), blow);
                j.why = "blow=" + blow + " took=" + took;
                if (!took) {
                    // what refused it, for the log; then once more with what stood in the way gone
                    long t = level.getGameTime();
                    StringBuilder w = new StringBuilder(" refusedBy=");
                    for (String k : new ArrayList<>(d.getAllKeys())) {
                        if (k.endsWith("Until") && d.getLong(k) > t) {
                            w.append(k).append(',');
                            d.remove(k);
                        }
                    }
                    w.append(" invulnerableTo=").append(l.p.isInvulnerableTo(l.p.damageSources().mobAttack(l.dummy)))
                        .append(" abilities=").append(l.p.getAbilities().invulnerable).append(" dummyAlive=").append(l.dummy.isAlive());
                    l.p.invulnerableTime = 0;
                    took = l.p.hurt(l.p.damageSources().mobAttack(l.dummy), blow);
                    j.why += w + " again=" + took;
                }
            }
            case "legend" -> {
                l.stageBefore = l.p.getPersistentData().getInt("ororArtCycle_" + j.id);
                for (int i = 0; i < 3; i++) {
                    RelicArts.cast(j.id, l.p);
                }
            }
            default -> {
            }
        }
    }

    private static void judge(Lane l, Job j, long now) {
        int hits = HITS.getOrDefault(l.dummy.getId(), 0) - l.hits;
        int effects = l.dummy.getActiveEffects().size() - l.effects;
        boolean mods = RelicTech.Mods.has(l.dummy, "armor") || RelicTech.Mods.has(l.dummy, "atkdown") || RelicTech.Mods.has(l.dummy, "seal_armor")
            || RelicTech.Mods.has(l.dummy, "toy") || RelicTech.Mods.has(l.strong, "hold");
        long t = now;
        CompoundTag d = l.p.getPersistentData();
        boolean windows = d.getLong("ororTechParryUntil") > l.job.t0 || d.getLong("ororTechStoreUntil") > l.job.t0 || d.getLong("ororTechReduceUntil") > l.job.t0
            || d.getLong("ororTechNextUntil") > l.job.t0 || d.getLong("ororTechStanceUntil") > l.job.t0 || d.getLong("ororTechExposedUntil") > l.job.t0
            || d.getLong("ororArtGuardUntil") > l.job.t0 || d.getLong("ororArtUndyingUntil") > l.job.t0 || d.getLong("ororRelicAdaptUntil") > l.job.t0;
        int units = RelicWorld.count(l.p, null) - l.units;
        int fields = RelicWorld.fields(l.p) - l.fields;
        boolean ok;
        String what;
        switch (j.kind) {
            case "tech" -> {
                boolean offered = RelicWorld.contractsOffered > l.offered;
                boolean healed = l.p.getHealth() > l.hpBefore || !l.p.getActiveEffects().isEmpty();
                ok = !j.verdict.equals("no") && (hits > 0 || effects > 0 || mods || windows || units > 0 || fields > 0 || offered || healed);
                // a technique that only works on blows (a parry, stored blows) or on friends shows it on its bearer; any
                // other must have reached its dummy
                RelicV9.Tech tech = RelicV9.of(j.id)[j.slot];
                boolean needsHit = tech.prog.toString().contains("\"dmg\"") && !windows && units == 0 && fields == 0 && !offered;
                if (needsHit && hits == 0) {
                    ok = false;
                }
                what = "hits=" + hits + " dealt=" + (int) (DEALT.getOrDefault(l.dummy.getId(), 0F) / 1) + " effects=" + effects + " mods=" + mods + " windows="
                    + windows + " units=" + units + " fields=" + fields + " offered=" + offered;
                LOG.info("RELIC-TECH {} {} 「{}」 {} {}", ok ? "ok" : "NO", tech.id, tech.name, what, j.why);
            }
            case "focus" -> {
                RelicV9.Info i = RelicV9.info(j.id);
                String e = punishOf(j.id);
                boolean punished = Punish.under(l.dummy, e) || l.dummy.getPersistentData().getLong("ororPunish_" + e + "Until") > j.t0;
                boolean suppressed = RelicTech.Mods.has(l.strong, "suppress_armor");
                ok = punished && suppressed;
                what = "punished=" + punished + " suppressed=" + suppressed;
                LOG.info("RELIC-FOCUS {} {} {}", ok ? "ok" : "NO", j.id, what);
            }
            case "charm" -> {
                boolean fired = RelicCrisis.FIRED_BY.getOrDefault(l.p.getUUID(), 0) > l.crisis;
                boolean alive = l.p.isAlive() && l.p.getHealth() > 0;
                ok = fired && alive;
                what = "fired=" + fired + " hp=" + (int) l.p.getHealth() + " units=" + units + " " + j.why;
                LOG.info("RELIC-CHARM {} {} {}", ok ? "ok" : "NO", j.id, what);
                l.p.setHealth(l.p.getMaxHealth());
            }
            case "legend" -> {
                int stage = l.p.getPersistentData().getInt("ororArtCycle_" + j.id);
                boolean cycled = stage == (l.stageBefore + 3) % 3;
                boolean crowned = RelicUltimate.started > l.ultimates;
                ok = cycled && crowned;
                what = "stage=" + stage + " crowned=" + crowned + " hits=" + hits;
                LOG.info("RELIC-LEGEND {} {} {}", ok ? "ok" : "NO", j.id, what);
            }
            default -> {
                ok = false;
                what = "";
            }
        }
        int[] tally = TALLY.computeIfAbsent(j.kind, k -> new int[2]);
        tally[0]++;
        if (ok) {
            tally[1]++;
        } else {
            FAILED.add(j.kind + ":" + j.id + (j.kind.equals("tech") ? "#" + j.slot : "") + "(" + what + ")");
        }
    }

    private static String punishOf(String focusId) {
        RelicArts.Art a = RelicArts.of(focusId);
        if (a != null) {
            for (var o : a.cast) {
                if (o.get("op").getAsString().equals("punish")) {
                    return o.get("e").getAsString();
                }
            }
        }
        return "weakness";
    }

    /** The punishment's own clock: Lv125 on, off when due, refused again within its grace. */
    private static String punishClock() {
        Lane l = LANES_.get(0);
        Mob m = dummy(l, 30.0, false);
        if (m == null) {
            return "no dummy";
        }
        boolean on = Punish.apply(m, "slow", 20) && Punish.under(m, "slow");
        boolean again = Punish.apply(m, "slow", 20);
        RelicTech.later(level, 30, () -> {
            EXTRA.put("punishOff", !Punish.under(m, "slow"));
            EXTRA.put("punishGraceRefused", !Punish.apply(m, "slow", 20));
            RelicTech.later(level, 80, () -> {
                EXTRA.put("punishAfterGrace", Punish.apply(m, "slow", 20));
                m.discard();
            });
        });
        return "on=" + on + " refusedWhileOn=" + !again;
    }

    /** The reward enchantments: a relic weapon let fall carries its definition's, once. */
    private static String enchantCheck() {
        int ok = 0, all = 0;
        var reg = level.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        var sharp = reg.getHolder(ResourceKey.create(Registries.ENCHANTMENT, ResourceLocation.withDefaultNamespace("sharpness")));
        var unbreaking = reg.getHolder(ResourceKey.create(Registries.ENCHANTMENT, ResourceLocation.withDefaultNamespace("unbreaking")));
        for (RelicV9.Info i : RelicV9.RELICS.values()) {
            if (i.enchants.isEmpty()) {
                continue;
            }
            all++;
            var item = CharacterRelics.ITEMS.get(i.id);
            if (item == null) {
                continue;
            }
            ItemEntity it = new ItemEntity(level, LANES_.get(0).at.getX(), LANES_.get(0).at.getY() + 1, LANES_.get(0).at.getZ() - 8, new ItemStack(item.get()));
            level.addFreshEntity(it);
            ItemStack s = it.getItem();
            boolean has = unbreaking.isPresent() && s.getEnchantmentLevel(unbreaking.get()) == 125;
            boolean bow = i.enchants.stream().anyMatch(x -> x[0].equals("power"));
            boolean sh = bow || sharp.isPresent() && s.getEnchantmentLevel(sharp.get()) == 125;
            boolean twice = !RelicRewards.enchant(level, s);
            if (has && sh && twice) {
                ok++;
            }
            it.discard();
        }
        return ok + "/" + all;
    }

    private static void finish(long now) {
        resultLogged = true;
        // last, every relic's right-click art once (their side effects no longer matter): no op unknown to the interpreter
        int before = RelicArts.unknownOps;
        Lane l0 = LANES_.get(0);
        for (String id : RelicV9.RELICS.keySet()) {
            try {
                RelicArts.cast(id, l0.p);
            } catch (RuntimeException ex) {
                FAILED.add("art:" + id + "(" + ex + ")");
            }
        }
        EXTRA.put("artsUnknownOps", RelicArts.unknownOps - before);
        for (Lane l : LANES_) {
            if (l.dummy != null) {
                l.dummy.discard();
            }
            if (l.strong != null) {
                l.strong.discard();
            }
        }
        for (int[] c : CHUNKS) {
            level.setChunkForced(c[0], c[1], false);
        }
        int[] tech = TALLY.getOrDefault("tech", new int[2]), focus = TALLY.getOrDefault("focus", new int[2]), charm = TALLY.getOrDefault("charm", new int[2]),
            legend = TALLY.getOrDefault("legend", new int[2]);
        String ench = String.valueOf(EXTRA.get("enchant"));
        boolean clock = Boolean.TRUE.equals(EXTRA.get("punishOff")) && Boolean.TRUE.equals(EXTRA.get("punishGraceRefused"))
            && Boolean.TRUE.equals(EXTRA.get("punishAfterGrace"));
        boolean pass = tech[1] == 123 && focus[1] == 41 && charm[1] == 41 && legend[1] == 41 && ench.equals("82/82") && clock
            && Integer.valueOf(0).equals(EXTRA.get("artsUnknownOps"));
        LOG.info("RELIC-RESULT {\"techniques\":\"{}/{}\",\"focus\":\"{}/{}\",\"charms\":\"{}/{}\",\"legends\":\"{}/{}\",\"enchant\":\"{}\",\"punish\":\"{} off={} grace={} after={}\","
                + "\"released\":{},\"cut\":{},\"refused\":{},\"cues\":{},\"units\":{},\"broken\":{},\"fields\":{},\"parried\":{},\"suppressed\":{},\"crisis\":{},"
                + "\"ultimates\":{},\"rescued\":{},\"offered\":{},\"signed\":{},\"punishApplied\":{},\"punishLifted\":{},\"anims\":\"{}\",\"ticks\":{},"
                + "\"unknownOps\":{},\"failed\":\"{}\",\"pass\":{}}",
            tech[1], tech[0], focus[1], focus[0], charm[1], charm[0], legend[1], legend[0], ench, EXTRA.get("punishClock"), EXTRA.get("punishOff"),
            EXTRA.get("punishGraceRefused"), EXTRA.get("punishAfterGrace"), RelicTech.released, RelicTech.cut, RelicTech.refused, RelicFx.sent,
            RelicWorld.unitsMade, RelicWorld.unitsBroken, RelicWorld.fieldsMade, RelicWorld.parried, RelicWorld.suppressed, RelicCrisis.fired,
            RelicUltimate.started, RelicUltimate.rescued, RelicWorld.contractsOffered, RelicWorld.contractsSigned, Punish.applied, Punish.lifted,
            EXTRA.get("anims"), now - started, EXTRA.get("artsUnknownOps"), String.join(" ", FAILED), pass);
    }

    static Map<Integer, Integer> hits() {
        return HITS;
    }

    static boolean unused(MobEffectInstance m, LivingEntity e, Enchantment x) {
        return m == null && e == null && x == null;
    }
}
