package jp.oror.efprobe;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r64, the user: "モブがきちんとEpic fightのモーションや行動やパリイやガードをするか確認 ナイトフォールクラフトも稼働させて比較")
 * One Epic Fight check for two packs: this file is built into OROR (NeoForge 1.21.1, CI test "efprobe") and, unchanged,
 * into a small Forge 1.20.1 mod run on a NightfallCraft (The Casket of Reveries 2.2.9.8) dedicated server. It touches
 * Epic Fight only by reflection, through what both of its versions have: the entity's patch (EpicFightCapabilities),
 * its animator and the animation its base layer plays.
 * <p>
 * Each kind of mob stands in its own walled lane high in the sky with a stand-in player (a fake player with a diamond
 * sword) who keeps two and a half blocks in front of it, faces it and strikes every {@value #SWING} ticks, for
 * {@value #TICKS} ticks; the mob is told to fight him. Every tick the animation the mob plays is read; each strike is
 * judged on the next tick by the mob's health (it landed, or it did nothing: guarded or parried); every drop in the
 * tester's health is a blow of the mob's. Both are made whole again at once, so the fight goes on. One line per mob,
 * EFP {...}; then EFP-RESULT. Animations are sorted by their names: attack, guard, parry, hit (staggered), dodge, move.
 */
public final class EfProbeCore {
    private static final Logger LOG = LoggerFactory.getLogger("OROR EF Probe");
    public static final int TICKS = 600, SWING = 12, Y = 180, SPACING = 16;
    public static volatile boolean done;

    /** What differs between the two loaders. */
    public interface Hooks {
        /** A fake player for lane n that can be hurt (a plain fake player is not), its attack charged when ready(p) is called. */
        Player tester(ServerLevel level, int n);

        void ready(Player p);

        /** The mob's natural gear (finalizeSpawn on this loader). */
        void equip(ServerLevel level, Mob m);
    }

    /** The mobs, the same list in both packs; a weapon after '+' is put in the mob's hand. */
    public static final List<String> MOBS = List.of("minecraft:zombie", "minecraft:zombie+minecraft:iron_sword", "minecraft:husk",
        "minecraft:drowned", "minecraft:skeleton", "minecraft:skeleton+minecraft:iron_sword", "minecraft:stray", "minecraft:wither_skeleton",
        "minecraft:vindicator", "minecraft:pillager", "minecraft:evoker", "minecraft:witch", "minecraft:piglin", "minecraft:piglin_brute",
        "minecraft:zombified_piglin", "minecraft:enderman", "minecraft:spider", "minecraft:ravager", "minecraft:iron_golem", "minecraft:villager+minecraft:iron_sword");

    static final class Lane {
        String id;
        Mob mob;
        Player tester;
        BlockPos at;
        String patch = "none";
        final Map<String, Integer> anims = new TreeMap<>();
        final Map<String, Integer> cats = new TreeMap<>();
        String last = "";
        int swings, landed, nothing, mobHits;
        float swingHp = -1, dmgToTester;
        final List<Float> dealt = new ArrayList<>();
    }

    private static ServerLevel level;
    private static Hooks hooks;
    private static String pack;
    private static final List<Lane> LANES = new ArrayList<>();
    private static int age = -1;

    private EfProbeCore() {
    }

    public static synchronized void start(ServerLevel l, String packName, Hooks h) {
        level = l;
        hooks = h;
        pack = packName;
        done = false;
        LANES.clear();
        age = 0;
        int n = 0, x0 = 24000, z0 = 24000;
        for (String spec : MOBS) {
            String[] parts = spec.split("\\+");
            ResourceLocation key = ResourceLocation.tryParse(parts[0]);
            if (key == null || !BuiltInRegistries.ENTITY_TYPE.containsKey(key)) {
                LOG.info("EFP-SKIP {\"mob\":\"{}\"}", spec);
                continue;
            }
            BlockPos c = new BlockPos(x0 + (n % 5) * SPACING, Y, z0 + (n / 5) * SPACING);
            arena(l, c);
            EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.get(key);
            Entity e = type.create(l);
            if (!(e instanceof Mob m)) {
                LOG.info("EFP-SKIP {\"mob\":\"{}\",\"why\":\"not a mob\"}", spec);
                continue;
            }
            m.moveTo(c.getX() + 0.5, c.getY() + 1, c.getZ() + 2.5, 180F, 0F);
            hooks.equip(l, m);
            if (parts.length > 1) {
                ResourceLocation item = ResourceLocation.tryParse(parts[1]);
                if (item != null && BuiltInRegistries.ITEM.containsKey(item)) {
                    m.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(BuiltInRegistries.ITEM.get(item)));
                }
            }
            m.setPersistenceRequired();
            l.addFreshEntity(m);
            Player p = hooks.tester(l, n);
            p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND_SWORD));
            // (run nfc 1) in the world: Epic Fight's attacks land through their animation's hit box, which finds only what is
            // in the world (no mob there hit the tester once); and a diamond sword's damage (held, its modifiers are only
            // taken up as the player ticks: the strikes did 0.2)
            p.moveTo(c.getX() + 0.5, c.getY() + 1, c.getZ() - 0.5, 0F, 0F);
            var dmg = p.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE);
            if (dmg != null) {
                dmg.setBaseValue(8.0);
            }
            // (run nfc 3, 4) a new player is spared every blow for three seconds, and a fake player does not tick that away:
            // no mob hurt the tester. Taking the blows past Epic Fight's own path broke it (Avalon: "attackResult.resultType
            // is null", and the server stopped), so the spared time itself is cleared; and a thousand health, so it never falls
            unspare(p);
            var hp = p.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH);
            if (hp != null) {
                hp.setBaseValue(1000.0);
            }
            p.setHealth(p.getMaxHealth());
            l.addFreshEntity(p);
            Lane lane = new Lane();
            lane.id = spec;
            lane.mob = m;
            lane.tester = p;
            lane.at = c;
            LANES.add(lane);
            n++;
        }
        LOG.info("EFP-START {\"pack\":\"{}\",\"lanes\":{}}", pack, LANES.size());
    }

    private static java.lang.reflect.Field spared;

    /**
     * ServerPlayer's spawnInvulnerableTime, found as its one private int that holds 60 on a new player (its name differs
     * between the two loaders' runtime mappings), set to 0.
     */
    static void unspare(Player p) {
        try {
            if (spared == null) {
                for (java.lang.reflect.Field f : net.minecraft.server.level.ServerPlayer.class.getDeclaredFields()) {
                    if (f.getType() == int.class && !java.lang.reflect.Modifier.isStatic(f.getModifiers())) {
                        f.setAccessible(true);
                        if (f.getInt(p) == 60) {
                            spared = f;
                            break;
                        }
                    }
                }
                LOG.info("EFP-SPARED {\"field\":\"{}\"}", spared == null ? "none" : spared.getName());
            }
            if (spared != null) {
                spared.setInt(p, 0);
            }
        } catch (Throwable t) {
            LOG.info("EFP-SPARED {\"error\":\"{}\"}", esc(String.valueOf(t)));
        }
    }

    /** A floor of stone and a ring of barriers, five high, around a seven by seven lane. */
    private static void arena(ServerLevel l, BlockPos c) {
        l.setChunkForced(c.getX() >> 4, c.getZ() >> 4, true);
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -4; dz <= 4; dz++) {
                l.setBlock(c.offset(dx, 0, dz), Blocks.STONE.defaultBlockState(), 3);
                for (int dy = 1; dy <= 6; dy++) {
                    boolean wall = Math.abs(dx) == 4 || Math.abs(dz) == 4 || dy == 6;
                    l.setBlock(c.offset(dx, dy, dz), wall ? Blocks.BARRIER.defaultBlockState() : Blocks.AIR.defaultBlockState(), 3);
                }
            }
        }
    }

    public static synchronized void tick() {
        if (age < 0 || level == null) {
            return;
        }
        age++;
        for (Lane lane : LANES) {
            step(lane);
        }
        if (age >= TICKS) {
            finish();
        }
    }

    private static void step(Lane lane) {
        Mob m = lane.mob;
        Player p = lane.tester;
        if (m == null || !m.isAlive() || p == null) {
            return;
        }
        // the animation the mob plays now
        Object patch = patch(m);
        if (patch != null) {
            lane.patch = patch.getClass().getSimpleName();
            String a = animation(patch);
            if (a != null && !a.equals(lane.last)) {
                lane.last = a;
                lane.anims.merge(a, 1, Integer::sum);
                lane.cats.merge(category(a), 1, Integer::sum);
            }
        }
        // the strike of the tick before: did it do anything?
        if (lane.swingHp >= 0) {
            float d = lane.swingHp - m.getHealth();
            if (d > 0.01F) {
                lane.landed++;
                lane.dealt.add(d);
            } else {
                lane.nothing++;
            }
            lane.swingHp = -1;
            m.setHealth(m.getMaxHealth());
        }
        // the mob's blows on the tester
        float hurt = p.getMaxHealth() - p.getHealth();
        if (hurt > 0.01F) {
            lane.mobHits++;
            lane.dmgToTester += hurt;
            p.setHealth(p.getMaxHealth());
        }
        // the tester keeps in front of the mob and strikes
        Vec3 look = m.getLookAngle();
        Vec3 flat = new Vec3(look.x, 0, look.z);
        if (flat.lengthSqr() < 1e-4) {
            flat = new Vec3(0, 0, -1);
        }
        flat = flat.normalize();
        Vec3 spot = m.position().add(flat.scale(2.5));
        double cx = lane.at.getX() + 0.5, cz = lane.at.getZ() + 0.5;
        spot = new Vec3(Math.max(cx - 3.2, Math.min(cx + 3.2, spot.x)), lane.at.getY() + 1, Math.max(cz - 3.2, Math.min(cz + 3.2, spot.z)));
        double dx = m.getX() - spot.x, dz = m.getZ() - spot.z;
        float yaw = (float) (Math.atan2(dz, dx) * 180.0 / Math.PI) - 90F;
        p.moveTo(spot.x, spot.y, spot.z, yaw, 0F);
        p.setYHeadRot(yaw);
        m.setTarget(p);
        if (age % SWING == 0 && age > 20) {
            hooks.ready(p);
            lane.swingHp = m.getHealth();
            lane.swings++;
            p.swing(InteractionHand.MAIN_HAND);
            p.attack(m);
        }
    }

    static String category(String a) {
        String s = a.toLowerCase(java.util.Locale.ROOT);
        if (s.contains("parr")) {
            return "parry";
        }
        if (s.contains("guard") || s.contains("block") || s.contains("shield")) {
            return "guard";
        }
        if (s.contains("hit") || s.contains("stun") || s.contains("knockdown") || s.contains("neutraliz") || s.contains("down")) {
            return "hit";
        }
        if (s.contains("dodge") || s.contains("step") || s.contains("roll") || s.contains("evade")) {
            return "dodge";
        }
        if (s.contains("attack") || s.contains("auto") || s.contains("combo") || s.contains("swing") || s.contains("slash") || s.contains("stab")
            || s.contains("smash") || s.contains("dash") || s.contains("airslash") || s.contains("skill") || s.contains("bite") || s.contains("claw")
            || s.contains("shot") || s.contains("shoot") || s.contains("cast") || s.contains("spell") || s.contains("thrust") || s.contains("sweep")) {
            return "attack";
        }
        if (s.contains("idle") || s.contains("walk") || s.contains("run") || s.contains("chase") || s.contains("sneak") || s.contains("float")
            || s.contains("fall") || s.contains("jump") || s.contains("mount") || s.contains("sit") || s.contains("empty") || s.contains("swim")) {
            return "move";
        }
        return "other";
    }

    private static void finish() {
        int patched = 0, withAttack = 0, withGuard = 0, withParry = 0, blocking = 0;
        for (Lane lane : LANES) {
            Map<String, Object> o = new LinkedHashMap<>();
            o.put("pack", pack);
            o.put("mob", lane.id);
            o.put("patch", lane.patch);
            o.put("held", lane.mob == null ? "" : BuiltInRegistries.ITEM.getKey(lane.mob.getMainHandItem().getItem()).toString());
            o.put("alive", lane.mob != null && lane.mob.isAlive());
            o.put("swings", lane.swings);
            o.put("landed", lane.landed);
            o.put("nothing", lane.nothing);
            o.put("mobHits", lane.mobHits);
            o.put("dmgToTester", Math.round(lane.dmgToTester * 10) / 10.0);
            List<Float> d = new ArrayList<>(lane.dealt);
            d.sort(null);
            o.put("dealtMedian", d.isEmpty() ? 0 : Math.round(d.get(d.size() / 2) * 10) / 10.0);
            o.put("dealtMin", d.isEmpty() ? 0 : Math.round(d.get(0) * 10) / 10.0);
            o.put("cats", lane.cats);
            o.put("anims", lane.anims);
            LOG.info("EFP {}", json(o));
            patched += lane.patch.equals("none") ? 0 : 1;
            withAttack += lane.cats.getOrDefault("attack", 0) > 0 ? 1 : 0;
            withGuard += lane.cats.getOrDefault("guard", 0) > 0 ? 1 : 0;
            withParry += lane.cats.getOrDefault("parry", 0) > 0 ? 1 : 0;
            blocking += lane.nothing > 0 ? 1 : 0;
            if (lane.mob != null) {
                lane.mob.discard();
            }
            if (lane.tester != null) {
                lane.tester.discard();
            }
            level.setChunkForced(lane.at.getX() >> 4, lane.at.getZ() >> 4, false);
        }
        LOG.info("EFP-RESULT {\"pack\":\"{}\",\"mobs\":{},\"patched\":{},\"efAttack\":{},\"efGuard\":{},\"efParry\":{},\"strikesStopped\":{},\"ticks\":{}}",
            pack, LANES.size(), patched, withAttack, withGuard, withParry, blocking, age);
        age = -1;
        done = true;
    }

    static String json(Object o) {
        if (o instanceof Map<?, ?> map) {
            StringBuilder b = new StringBuilder("{");
            for (Map.Entry<?, ?> e : map.entrySet()) {
                if (b.length() > 1) {
                    b.append(',');
                }
                b.append('"').append(esc(String.valueOf(e.getKey()))).append("\":").append(json(e.getValue()));
            }
            return b.append('}').toString();
        }
        if (o instanceof Number || o instanceof Boolean) {
            return String.valueOf(o);
        }
        return "\"" + esc(String.valueOf(o)) + "\"";
    }

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "'");
    }

    // ---- Epic Fight, by method handles only ----
    // (run nfc 1) Class.getMethods() on Epic Fight's classes loads every type their methods name, client classes among
    // them, and on a dedicated server that throws ("Attempted to load class LocalPlayer"): each method is looked up alone,
    // by its name and its type, with the types either version of Epic Fight gives it.
    private static final java.lang.invoke.MethodHandles.Lookup LK = java.lang.invoke.MethodHandles.publicLookup();
    private static java.lang.invoke.MethodHandle getPatch, getAnimator, getPlayerFor, getAnimation;
    private static Class<?> livingPatch;
    private static boolean looked;
    private static final Map<Class<?>, java.lang.invoke.MethodHandle> NAMES = new java.util.HashMap<>();

    private static Class<?> cls(String n) {
        try {
            return Class.forName(n);
        } catch (Throwable t) {
            return null;
        }
    }

    private static java.lang.invoke.MethodHandle virt(Class<?> owner, String name, List<Class<?>> rets, List<Class<?>> params) {
        if (owner == null) {
            return null;
        }
        for (Class<?> r : rets) {
            if (r == null) {
                continue;
            }
            if (params.isEmpty()) {
                try {
                    return LK.findVirtual(owner, name, java.lang.invoke.MethodType.methodType(r));
                } catch (Throwable t) {
                    continue;
                }
            }
            for (Class<?> p : params) {
                if (p == null) {
                    continue;
                }
                try {
                    return LK.findVirtual(owner, name, java.lang.invoke.MethodType.methodType(r, p));
                } catch (Throwable t) {
                    // the other shape
                }
            }
        }
        return null;
    }

    private static void look() {
        if (looked) {
            return;
        }
        looked = true;
        Class<?> caps = cls("yesman.epicfight.world.capabilities.EpicFightCapabilities");
        livingPatch = cls("yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch");
        Class<?> entityPatch = cls("yesman.epicfight.world.capabilities.entitypatch.EntityPatch");
        for (Class<?> ret : new Class<?>[]{entityPatch, livingPatch, Object.class}) {
            if (caps == null || ret == null) {
                continue;
            }
            try {
                getPatch = LK.findStatic(caps, "getEntityPatch", java.lang.invoke.MethodType.methodType(ret, Entity.class, Class.class));
                break;
            } catch (Throwable t) {
                // another erasure
            }
        }
        Class<?> animator = cls("yesman.epicfight.api.animation.Animator");
        Class<?> player = cls("yesman.epicfight.api.animation.AnimationPlayer");
        Class<?> dynamic = cls("yesman.epicfight.api.animation.types.DynamicAnimation");
        Class<?> accessor = cls("yesman.epicfight.api.asset.AssetAccessor");
        getAnimator = virt(livingPatch, "getAnimator", java.util.Arrays.asList(animator, cls("yesman.epicfight.api.animation.ServerAnimator")), List.of());
        getPlayerFor = virt(animator, "getPlayerFor", java.util.Arrays.asList(player, java.util.Optional.class), java.util.Arrays.asList(accessor, dynamic));
        getAnimation = virt(player, "getAnimation", java.util.Arrays.asList(accessor, dynamic, Object.class), List.of());
        if (getAnimation == null) {
            getAnimation = virt(player, "getRealAnimation", java.util.Arrays.asList(accessor, dynamic, Object.class), List.of());
        }
        LOG.info("EFP-API {\"patch\":{},\"animator\":{},\"playerFor\":{},\"animation\":{}}", getPatch != null, getAnimator != null,
            getPlayerFor != null, getAnimation != null);
    }

    private static Object patch(LivingEntity e) {
        look();
        if (getPatch == null || livingPatch == null) {
            return null;
        }
        try {
            Object p = getPatch.invoke(e, livingPatch);
            if (p instanceof java.util.Optional<?> o) {
                p = o.orElse(null);
            }
            return livingPatch.isInstance(p) ? p : null;
        } catch (Throwable t) {
            tell("patch", t);
            return null;
        }
    }

    /** The name of the animation the patch's base layer plays, whatever the version's shape of it. */
    private static String animation(Object patch) {
        if (getAnimator == null || getPlayerFor == null || getAnimation == null) {
            return null;
        }
        try {
            Object animator = getAnimator.invoke(patch);
            Object player = getPlayerFor.invoke(animator, (Object) null);
            if (player instanceof java.util.Optional<?> o) {
                player = o.orElse(null);
            }
            if (player == null) {
                return null;
            }
            return name(getAnimation.invoke(player), 0);
        } catch (Throwable t) {
            tell("animation", t);
            return null;
        }
    }

    static String name(Object anim, int depth) throws Throwable {
        if (anim == null) {
            return "none";
        }
        Class<?> c = anim.getClass();
        java.lang.invoke.MethodHandle h = NAMES.computeIfAbsent(c, k -> {
            for (String n : new String[]{"registryName", "getRegistryName", "getLocation", "location", "getId"}) {
                java.lang.invoke.MethodHandle x = virt(k, n, List.of(ResourceLocation.class), List.of());
                if (x != null) {
                    return x;
                }
            }
            return null;
        });
        if (h != null) {
            Object r = h.invoke(anim);
            if (r != null) {
                return String.valueOf(r);
            }
        }
        if (depth == 0) {
            java.lang.invoke.MethodHandle get = virt(c, "get", List.of(Object.class), List.of());
            if (get != null) {
                Object inner = get.invoke(anim);
                if (inner != null && inner != anim) {
                    return name(inner, 1);
                }
            }
        }
        return anim.toString();
    }

    private static boolean told;

    private static void tell(String what, Throwable t) {
        if (told) {
            return;
        }
        told = true;
        LOG.info("EFP-API {\"{}\":\"{}\"}", what, esc(String.valueOf(t)));
    }
}
