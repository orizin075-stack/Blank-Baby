package jp.oror.reborn.relic;

import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.RelicArts;
import jp.oror.reborn.RelicPowers;
import jp.oror.reborn.RelicSpec;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.waza.WazaNet;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingHealEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

/**
 * (058) What the techniques leave in the world and the windows they open on their bearers.
 *
 * <ul>
 * <li>Units: turrets, crystals, beasts, drones, magic circles, toy soldiers, depots, the machine god's arms. Each has a
 * place, a life, health that foes beside it wear down (the design's 破壊可能), and a job done every so many ticks: shoot,
 * bite, hold, heal, guard its owner, harry foes with a curse. At most eight to an owner (the design's 総上限は8機).</li>
 * <li>Fields: a ground that works on what is in it for its time (12 s at most): eroding, whirling, a hell gate's
 * wither, a canopy that stops foes' shots.</li>
 * <li>Windows on a bearer: a parry (the blow cancelled and countered, the next blow stronger), stored blows (released
 * as one), a cut on what it takes, a stance on its blows, a short exposure.</li>
 * <li>On foes: weakened healing, a curse that moves on when its bearer dies (twice at most), healing turned into harm.</li>
 * <li>Contracts (甘契の未怪): offered on screen with their terms, nothing paid until agreed; only agreed ones are called in.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RelicWorld {
    public static int suppressed, parried, stored, unitsMade, unitShots, unitsBroken, fieldsMade, fieldTicks, contractsOffered, contractsSigned,
        healCursed, curseJumps, crisisHint;
    private static int nextId = 1;

    private RelicWorld() {
    }

    // ------------------------------------------------------------------------------------------------------ the units

    static final class Unit {
        final int id;
        final UUID owner;
        final Player ownerRef;
        final String kind, art;
        Vec3 pos;
        final Vec3 offset;
        final long until;
        float hp;
        final float maxHp, share, base, heal;
        final int rate, colour;
        final double reach;
        final boolean follows;
        int age;

        Unit(Player owner, String kind, String art, Vec3 pos, Vec3 offset, long until, float hp, float share, float base, int rate, double reach, float heal,
             int colour) {
            this.id = nextId++;
            this.owner = owner.getUUID();
            this.ownerRef = owner;
            this.kind = kind;
            this.art = art;
            this.pos = pos;
            this.offset = offset;
            this.until = until;
            this.hp = hp;
            this.maxHp = hp;
            this.share = share;
            this.base = base;
            this.rate = Math.max(4, rate);
            this.reach = reach;
            this.heal = heal;
            this.colour = colour;
            this.follows = List.of("drone", "bird", "missile", "circle", "toy", "beast", "ground").contains(kind);
        }
    }

    private static final Map<Integer, Unit> UNITS = new LinkedHashMap<>();

    public static int count(Player p, String kind) {
        int n = 0;
        for (Unit u : UNITS.values()) {
            if (u.owner.equals(p.getUUID()) && (kind == null || u.kind.equals(kind))) {
                n++;
            }
        }
        return n;
    }

    public static List<String> unitKinds(Player p) {
        List<String> l = new ArrayList<>();
        UNITS.values().stream().filter(u -> u.owner.equals(p.getUUID())).forEach(u -> l.add(u.kind));
        return l;
    }

    /** Sets units down (the unit op): kind, how many, how long, their health, their blow's share of the base. */
    static void units(RelicArts.Ctx c, JsonObject o) {
        Player p = c.p;
        String kind = RelicTech.str(o, "k", "turret");
        int n = (int) RelicTech.num(o, "n", 1.0);
        place(p, c.art.id, kind, n, (int) RelicTech.num(o, "t", 300.0), (float) RelicTech.num(o, "hp", 200.0), (float) RelicTech.num(o, "m", 0.05), c.base,
            (int) RelicTech.num(o, "rate", 20.0), RelicTech.num(o, "r", 14.0), (float) RelicTech.num(o, "heal", 0.0), c.color);
    }

    public static void place(Player p, String art, String kind, int n, int ticks, float hp, float share, float base, int rate, double reach, float heal,
                             int colour) {
        if (!(p.level() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        for (int i = 0; i < n; i++) {
            // at most eight to an owner: the oldest goes for a new one
            while (count(p, null) >= 8) {
                Unit old = UNITS.values().stream().filter(u -> u.owner.equals(p.getUUID())).findFirst().orElse(null);
                if (old == null) {
                    break;
                }
                remove(sl, old, false);
            }
            double ang = (count(p, null) * 2.39996) + i * 1.3;
            Vec3 off = new Vec3(Math.cos(ang) * 2.8, 0, Math.sin(ang) * 2.8);
            Vec3 at = RelicTech.ground(sl, p.position().add(off));
            if (List.of("drone", "bird", "missile", "circle").contains(kind)) {
                at = at.add(0, 2.2, 0);
            }
            Unit u = new Unit(p, kind, art, at, off, now + Math.min(ticks, 400), hp, share, base, rate, reach, heal, colour);
            UNITS.put(u.id, u);
            unitsMade++;
            RelicNet.toWatchers(p, new RelicNet.Thing(0, u.id, kind, colour, at.x, at.y, at.z, 0.8F, (int) (u.until - now), p.getId(), 1.0F));
            RelicFx.send(p, 4, colour, at, new Vec3(0, 1, 0), 1.2F, 16, 0, 0, "");
        }
    }

    private static void remove(ServerLevel sl, Unit u, boolean broken) {
        UNITS.remove(u.id);
        if (broken) {
            unitsBroken++;
        }
        if (u.ownerRef != null) {
            RelicNet.toWatchers(u.ownerRef, new RelicNet.Thing(2, u.id, u.kind, u.colour, u.pos.x, u.pos.y, u.pos.z, 0, 0, u.ownerRef.getId(), 0));
            RelicFx.send(u.ownerRef, 12, u.colour, u.pos, new Vec3(0, 1, 0), broken ? 1.6F : 0.8F, 10, 0, 0, "");
        }
        if (broken) {
            sl.playSound(null, u.pos.x, u.pos.y, u.pos.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 0.8F, 0.8F);
        }
    }

    private static LivingEntity nearestFoe(Player p, Vec3 at, double r) {
        LivingEntity best = null;
        double bd = r * r;
        for (LivingEntity e : RelicArts.near(p, at, r)) {
            double d = e.position().distanceToSqr(at);
            if (d < bd) {
                bd = d;
                best = e;
            }
        }
        return best;
    }

    private static void strike(Unit u, LivingEntity e, float amount) {
        Player p = u.ownerRef;
        RelicArts.quiet(() -> {
            e.invulnerableTime = 0;
            e.hurt(p.damageSources().playerAttack(p), amount);
        });
        unitShots++;
    }

    private static void tickUnits(ServerLevel sl) {
        long now = sl.getGameTime();
        for (Unit u : new ArrayList<>(UNITS.values())) {
            Player p = u.ownerRef;
            if (p == null || p.level() != sl) {
                if (p == null || p.isRemoved()) {
                    UNITS.remove(u.id);
                }
                continue;
            }
            if (!p.isAlive() || now >= u.until) {
                remove(sl, u, false);
                continue;
            }
            u.age++;
            if (u.follows) {
                Vec3 want = p.position().add(u.offset).add(0, List.of("drone", "bird", "missile", "circle").contains(u.kind) ? 2.2 : 0, 0);
                if (u.kind.equals("beast") || u.kind.equals("ground")) {
                    LivingEntity f = nearestFoe(p, p.position(), u.reach);
                    if (f != null) {
                        want = f.position().add(f.position().subtract(u.pos).normalize().scale(-1.2));
                    }
                }
                Vec3 step = want.subtract(u.pos);
                double len = step.length();
                if (len > 0.05) {
                    u.pos = u.pos.add(step.scale(Math.min(1.0, 0.45 / len)));
                }
                if (u.pos.distanceTo(p.position()) > 24) {
                    u.pos = p.position().add(u.offset);
                }
                if (u.age % 5 == 0) {
                    RelicNet.toWatchers(p, new RelicNet.Thing(1, u.id, u.kind, u.colour, u.pos.x, u.pos.y, u.pos.z, 0.8F, (int) (u.until - now), p.getId(),
                        u.hp / u.maxHp));
                }
            }
            // worn down by foes beside it
            if (u.age % 20 == 0) {
                for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(u.pos, u.pos).inflate(2.5), x -> RelicPowers.enemy(p, x))) {
                    AttributeInstance a = e.getAttribute(Attributes.ATTACK_DAMAGE);
                    u.hp -= e instanceof SupremeEntity ? 60.0F : Math.max(2.0F, a != null ? (float) a.getValue() : 2.0F);
                }
                for (Projectile pr : sl.getEntitiesOfClass(Projectile.class, new AABB(u.pos, u.pos).inflate(1.4),
                    x -> x.getOwner() instanceof LivingEntity o && RelicPowers.enemy(p, o))) {
                    u.hp -= 8.0F;
                    pr.discard();
                }
                if (u.hp <= 0.0F) {
                    remove(sl, u, true);
                    continue;
                }
            }
            if (u.age % u.rate != 0) {
                continue;
            }
            float blow = u.base * u.share;
            switch (u.kind) {
                case "gunner", "crystal", "cannon", "drone", "toy", "missile", "bird", "circle" -> {
                    LivingEntity f = nearestFoe(p, u.pos, u.reach);
                    if (f != null && (u.kind.equals("missile") || u.kind.equals("bird") || hasSight(sl, u.pos, f))) {
                        strike(u, f, blow);
                        Vec3 to = f.position().add(0, f.getBbHeight() * 0.5, 0).subtract(u.pos);
                        RelicFx.send(p, u.kind.equals("missile") || u.kind.equals("toy") ? 1 : 2, u.colour, u.pos, to.normalize(), (float) to.length(), 6,
                            0.25F, 0, "");
                        if (u.kind.equals("circle")) {
                            for (Projectile pr : sl.getEntitiesOfClass(Projectile.class, new AABB(u.pos, u.pos).inflate(3.0),
                                x -> x.getOwner() instanceof LivingEntity o && RelicPowers.enemy(p, o))) {
                                RelicArts.reflect(p, pr);
                            }
                        }
                    }
                }
                case "ground", "beast" -> {
                    LivingEntity f = nearestFoe(p, u.pos, 2.4);
                    if (f != null) {
                        strike(u, f, blow);
                        RelicFx.send(p, 0, u.colour, f.position().add(0, f.getBbHeight() * 0.5, 0), f.position().subtract(u.pos).normalize(), 1.4F, 6, 30,
                            0, "");
                    }
                }
                case "binder" -> {
                    LivingEntity f = nearestFoe(p, u.pos, u.reach);
                    if (f != null) {
                        jp.oror.reborn.Abilities.stun(f, RelicTech.strong(f) ? 0 : 20);
                        f.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 2));
                        strike(u, f, blow);
                        RelicFx.send(p, 8, u.colour, u.pos, f.position().add(0, 1, 0).subtract(u.pos), 1, 10, 0, 0, "");
                    }
                }
                case "warden", "horn" -> {
                    if (p.position().distanceTo(u.pos) <= u.reach) {
                        RelicTech.window(p, "ororTechReduce", now + u.rate + 5, u.kind.equals("warden") ? 0.4F : 0.3F);
                    }
                }
                case "vine" -> {
                    for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(u.pos, u.pos).inflate(u.reach),
                        x -> x == p || !RelicPowers.enemy(p, x) && (x instanceof Player || x.getPersistentData().hasUUID("ororRelicOwner")))) {
                        e.heal(e.getMaxHealth() * u.heal);
                    }
                    RelicFx.send(p, 3, u.colour, u.pos, new Vec3(0, 1, 0), (float) u.reach, 12, 0, 0, "");
                }
                case "lab" -> {
                    for (LivingEntity e : RelicArts.near(p, u.pos, u.reach)) {
                        e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 1));
                        e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1));
                        if (blow > 0) {
                            strike(u, e, blow);
                        }
                    }
                }
                default -> {
                    // arms, depots, the toy box: there to be kept or broken
                }
            }
        }
    }

    private static boolean hasSight(ServerLevel sl, Vec3 from, LivingEntity to) {
        Vec3 at = to.position().add(0, to.getBbHeight() * 0.5, 0);
        return sl.clip(new net.minecraft.world.level.ClipContext(from, at, net.minecraft.world.level.ClipContext.Block.COLLIDER,
            net.minecraft.world.level.ClipContext.Fluid.NONE, to)).getType() == net.minecraft.world.phys.HitResult.Type.MISS;
    }

    // ----------------------------------------------------------------------------------------------------- the fields

    static final class Field {
        final int id;
        final Player owner;
        final String name, art, effect;
        final Vec3 at;
        final double r;
        final long until;
        final float share, base, heal;
        final int rate, amp, colour;
        int age;

        Field(Player owner, String name, String art, Vec3 at, double r, long until, float share, float base, String effect, int amp, int rate, float heal,
              int colour) {
            this.id = nextId++;
            this.owner = owner;
            this.name = name;
            this.art = art;
            this.at = at;
            this.r = r;
            this.until = until;
            this.share = share;
            this.base = base;
            this.effect = effect;
            this.amp = amp;
            this.rate = Math.max(5, rate);
            this.heal = heal;
            this.colour = colour;
        }
    }

    private static final Map<Integer, Field> FIELDS = new LinkedHashMap<>();

    static void field(RelicArts.Ctx c, JsonObject o) {
        if (!(c.p.level() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        // the design: a lasting ground goes within 12 seconds
        int t = (int) Math.min(240.0, RelicTech.num(o, "t", 120.0));
        Vec3 at = RelicTech.at(c);
        Field f = new Field(c.p, RelicTech.str(o, "name", "field"), c.art.id, at, RelicTech.num(o, "r", 6.0), now + t, (float) RelicTech.num(o, "m", 0.0),
            c.base, o.has("e") ? o.get("e").getAsString() : null, (int) RelicTech.num(o, "ea", 0.0), (int) RelicTech.num(o, "rate", 10.0),
            (float) RelicTech.num(o, "heal", 0.0), c.color);
        FIELDS.put(f.id, f);
        fieldsMade++;
        RelicNet.toWatchers(c.p, new RelicNet.Thing(0, f.id, "field:" + f.name, f.colour, at.x, at.y, at.z, (float) f.r, t, c.p.getId(), 1.0F));
    }

    private static void tickFields(ServerLevel sl) {
        long now = sl.getGameTime();
        Iterator<Field> it = FIELDS.values().iterator();
        while (it.hasNext()) {
            Field f = it.next();
            if (f.owner.level() != sl) {
                if (f.owner.isRemoved()) {
                    it.remove();
                }
                continue;
            }
            if (now >= f.until || !f.owner.isAlive()) {
                it.remove();
                RelicNet.toWatchers(f.owner, new RelicNet.Thing(2, f.id, "field:" + f.name, f.colour, f.at.x, f.at.y, f.at.z, 0, 0, f.owner.getId(), 0));
                continue;
            }
            if (++f.age % f.rate != 0) {
                continue;
            }
            fieldTicks++;
            Player p = f.owner;
            for (LivingEntity e : RelicArts.near(p, f.at, f.r)) {
                if (f.share > 0) {
                    RelicArts.quiet(() -> {
                        e.invulnerableTime = 0;
                        e.hurt(p.damageSources().playerAttack(p), f.base * f.share);
                    });
                }
                if (f.effect != null) {
                    e.addEffect(new MobEffectInstance(RelicTech.effect(f.effect), 40, f.amp));
                }
                if (f.name.equals("whirl")) {
                    RelicArts.push(e, f.at.subtract(e.position()).normalize().scale(0.5).add(0, 0.05, 0));
                }
            }
            if (f.heal > 0) {
                for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(f.at, f.at).inflate(f.r), x -> x == p || x instanceof Player q && !RelicPowers.enemy(p, q))) {
                    e.heal(e.getMaxHealth() * f.heal);
                }
            }
            if (f.name.equals("canopy")) {
                // the canopy stops foes' shots coming in (some of them: the design's 一部を遮る)
                for (Projectile pr : sl.getEntitiesOfClass(Projectile.class, new AABB(f.at, f.at).inflate(f.r),
                    x -> x.getOwner() instanceof LivingEntity o && RelicPowers.enemy(p, o))) {
                    if (sl.random.nextFloat() < 0.6F) {
                        pr.discard();
                    }
                }
            }
        }
    }

    public static int fields(Player p) {
        return (int) FIELDS.values().stream().filter(f -> f.owner == p).count();
    }

    @SubscribeEvent
    public static void tick(LevelTickEvent.Post e) {
        if (e.getLevel() instanceof ServerLevel sl) {
            if (!UNITS.isEmpty()) {
                tickUnits(sl);
            }
            if (!FIELDS.isEmpty()) {
                tickFields(sl);
            }
            tickContracts(sl);
        }
    }

    // ------------------------------------------------------------------------------------------ 色鬼 (the colour tag)

    static void colortag(RelicArts.Ctx c, double r, float m) {
        Player p = c.p;
        ServerLevel sl = c.sl;
        int[] colours = {0xFF4A4A, 0x4A8AFF, 0xFFE14A, 0x5ADF5A};
        String[] names = {"赤", "青", "黄", "緑"};
        int safe = sl.random.nextInt(4);
        Vec3 centre = p.position();
        Vec3[] spots = new Vec3[4];
        for (int i = 0; i < 4; i++) {
            double ang = Math.PI / 4 + i * Math.PI / 2;
            spots[i] = RelicTech.ground(sl, centre.add(Math.cos(ang) * r * 0.5, 0, Math.sin(ang) * r * 0.5));
            RelicFx.send(p, 4, colours[i], spots[i].add(0, 0.05, 0), new Vec3(0, 1, 0), (float) (r * 0.3), 50, 0, 0, "");
        }
        RelicFx.send(p, 10, colours[safe], p.position().add(0, p.getBbHeight() + 1.0, 0), new Vec3(0, 1, 0), 2.0F, 50, 0, 0, names[safe] + "！");
        p.displayClientMessage(Component.literal("色鬼――" + names[safe] + "だけが安全").withStyle(ChatFormatting.YELLOW), true);
        RelicArts.Ctx k = c.copy();
        RelicTech.later(sl, 40, () -> {
            for (LivingEntity e : RelicArts.near(p, centre, r)) {
                if (e.position().distanceTo(spots[safe]) > r * 0.3 + 0.5) {
                    k.t = new ArrayList<>(List.of(e));
                    RelicTech.hurt(k, e, k.base * m);
                    RelicFx.send(p, 7, 0xFFE14A, e.position(), new Vec3(0, -1, 0), 1.6F, 14, 0, 0, "");
                }
            }
        });
    }

    // ------------------------------------------------------------------------------------------------- the contracts

    static final class Pact {
        final int id;
        final Player owner;
        final ServerPlayer signer;
        final float heal;
        final String buff, cost;
        final int buffTicks, costTicks;
        final long expires;
        int state; // 0 offered, 1 signed, 2 refused, 3 paid
        long payAt;

        Pact(int id, Player owner, ServerPlayer signer, float heal, String buff, int buffTicks, String cost, int costTicks, long expires) {
            this.id = id;
            this.owner = owner;
            this.signer = signer;
            this.heal = heal;
            this.buff = buff;
            this.buffTicks = buffTicks;
            this.cost = cost;
            this.costTicks = costTicks;
            this.expires = expires;
        }
    }

    private static final Map<Integer, Pact> PACTS = new HashMap<>();
    private static int nextPact = 1_000_000;

    static void offer(RelicArts.Ctx c, JsonObject o) {
        Player p = c.p;
        long now = c.sl.getGameTime();
        double r = RelicTech.num(o, "r", 16.0);
        float heal = (float) RelicTech.num(o, "heal", 0.4);
        String buff = RelicTech.str(o, "e", "strength"), cost = RelicTech.str(o, "cost", "hunger");
        int bt = (int) RelicTech.num(o, "bt", 400.0), ct = (int) RelicTech.num(o, "ct", 600.0);
        List<ServerPlayer> to = new ArrayList<>();
        if (p instanceof ServerPlayer self) {
            to.add(self);
        }
        for (Player q : c.sl.getEntitiesOfClass(Player.class, p.getBoundingBox().inflate(r), q -> q != p && !RelicPowers.enemy(p, q))) {
            if (q instanceof ServerPlayer sq) {
                to.add(sq);
            }
        }
        to.addAll(RelicTest.signers(p));
        for (ServerPlayer q : to) {
            Pact pact = new Pact(nextPact++, p, q, heal, buff, bt, cost, ct, now + 400);
            PACTS.put(pact.id, pact);
            contractsOffered++;
            net.neoforged.neoforge.network.PacketDistributor.sendToPlayer(q, new WazaNet.Offer(pact.id, -1, p.getId(), "最大HPの" + Math.round(heal * 100) + "%回復と" + buffName(buff) + bt / 20 + "秒",
                "30秒後に" + buffName(cost) + ct / 20 + "秒", 20));
        }
    }

    private static String buffName(String e) {
        return switch (e) {
            case "strength" -> "攻撃力上昇";
            case "hunger" -> "空腹";
            case "regen" -> "再生";
            case "weakness" -> "弱体化";
            default -> e;
        };
    }

    /** A player's answer to a relic contract (WazaWorld forwards ids of a million and more here). */
    public static void answer(ServerPlayer q, int id, boolean accept) {
        Pact pact = PACTS.get(id);
        if (pact == null || pact.signer != q && !pact.signer.getUUID().equals(q.getUUID()) || pact.state != 0 || q.level().getGameTime() > pact.expires) {
            return;
        }
        if (!accept) {
            pact.state = 2;
            q.displayClientMessage(Component.literal("契約を断った。何も起きない。").withStyle(ChatFormatting.GRAY), true);
            return;
        }
        pact.state = 1;
        pact.payAt = q.level().getGameTime() + 600;
        contractsSigned++;
        q.heal(q.getMaxHealth() * pact.heal);
        q.addEffect(new MobEffectInstance(RelicTech.effect(pact.buff), pact.buffTicks, 1));
        q.displayClientMessage(Component.literal("契約成立：恩恵を受け取った（代償は30秒後）").withStyle(ChatFormatting.GOLD), true);
        if (q.level() instanceof ServerLevel sl) {
            sl.playSound(null, q.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 0.6F);
        }
    }

    private static void tickContracts(ServerLevel sl) {
        if (PACTS.isEmpty() || (sl.getGameTime() % 10L) != 0L) {
            return;
        }
        long now = sl.getGameTime();
        Iterator<Pact> it = PACTS.values().iterator();
        while (it.hasNext()) {
            Pact pact = it.next();
            if (pact.signer.level() != sl) {
                continue;
            }
            if (pact.state == 0 && now > pact.expires || pact.state == 2 || pact.state == 3 && now > pact.payAt + 2400) {
                it.remove();
            } else if (pact.state == 1 && now >= pact.payAt) {
                pact.state = 3;
                pact.signer.addEffect(new MobEffectInstance(RelicTech.effect(pact.cost), pact.costTicks, 0));
                pact.signer.displayClientMessage(Component.literal("契約の代償を支払った").withStyle(ChatFormatting.DARK_PURPLE), true);
            }
        }
    }

    /** The agreed contracts of this bearer: their signers alone bear the ops (契約の期限, 万未来所有). */
    static void contracts(RelicArts.Ctx c, JsonObject o) {
        List<LivingEntity> signed = new ArrayList<>();
        for (Pact pact : PACTS.values()) {
            if (pact.owner == c.p && (pact.state == 1 || pact.state == 3) && pact.signer.isAlive() && pact.signer.level() == c.sl
                && pact.signer.distanceTo(c.p) < 48 && pact.signer != c.p) {
                signed.add(pact.signer);
            }
        }
        if (signed.isEmpty()) {
            return;
        }
        RelicArts.Ctx k = c.copy();
        k.t = signed;
        // the contract's own terms on those who agreed (the ops apply to them whether or not they are foes)
        for (JsonObject x : RelicTech.list(o, "ops")) {
            String op = x.get("op").getAsString();
            for (LivingEntity e : signed) {
                switch (op) {
                    case "hold" -> e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, (int) RelicTech.num(x, "t", 30.0), 3));
                    case "strip" -> new ArrayList<>(e.getActiveEffects()).stream().filter(m -> m.getEffect().value().isBeneficial())
                        .forEach(m -> e.removeEffect(m.getEffect()));
                    case "dmg" -> e.hurt(c.p.damageSources().indirectMagic(c.p, c.p), Math.min(e.getHealth() - 1.0F, e.getMaxHealth() * 0.3F));
                    default -> {
                    }
                }
            }
        }
    }

    /** The contracts offered to this player and not answered (the CI's stand-ins answer them). */
    public static List<Integer> offeredTo(ServerPlayer q) {
        List<Integer> l = new ArrayList<>();
        PACTS.values().stream().filter(x -> x.signer == q && x.state == 0).forEach(x -> l.add(x.id));
        return l;
    }

    public static int signedFor(Player owner) {
        return (int) PACTS.values().stream().filter(x -> x.owner == owner && x.state >= 1 && x.state != 2).count();
    }

    // ------------------------------------------------------------------------------------------- windows and hooks

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void incoming(LivingIncomingDamageEvent e) {
        LivingEntity v = e.getEntity();
        if (!(v.level() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        CompoundTag d = v.getPersistentData();
        Entity src = e.getSource().getEntity();
        if (v instanceof Player p) {
            d.putString("ororLastHurtType", RelicTech.kindOf(e.getSource()));
            if (src instanceof LivingEntity att && att != p && RelicTech.open(p, "ororTechParry", now)) {
                // the parry: the blow turned aside, the counter at once, the next blow stronger
                e.setCanceled(true);
                parried++;
                d.remove("ororTechParryUntil");
                float counter = d.getFloat("ororTechParryDmg");
                RelicTech.window(p, "ororTechNext", now + 120, Math.max(1.0F, d.getFloat("ororTechParry")));
                RelicArts.quiet(() -> {
                    att.invulnerableTime = 0;
                    att.hurt(p.damageSources().playerAttack(p), counter);
                });
                if (d.getLong("ororTechThrowUntil") >= now) {
                    if (RelicTech.strong(att)) {
                        att.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 4));
                    } else {
                        RelicArts.push(att, RelicArts.flat(att.position().subtract(p.position())).scale(-1.0).add(0, 0.9, 0));
                    }
                }
                RelicFx.send(p, 12, 0xFFFFFF, p.position().add(0, 1.2, 0).add(RelicArts.flat(att.position().subtract(p.position())).scale(0.8)),
                    new Vec3(0, 1, 0), 1.6F, 10, 0, 0, "");
                sl.playSound(null, p.blockPosition(), SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 1.0F, 1.6F);
                return;
            }
            if (src instanceof LivingEntity && RelicTech.open(p, "ororTechStore", now) && d.getInt("ororTechStoredN") < (int) d.getFloat("ororTechStore")) {
                e.setCanceled(true);
                stored++;
                d.putInt("ororTechStoredN", d.getInt("ororTechStoredN") + 1);
                d.putFloat("ororTechStored", d.getFloat("ororTechStored") + e.getAmount());
                RelicFx.send(p, 9, 0x8AE0FF, p.position().add(0, 1.0, 0), new Vec3(0, 1, 0), 1.4F, 8, 0, 0, "");
                return;
            }
            if (RelicTech.open(p, "ororTechExposed", now)) {
                e.setAmount(e.getAmount() * 1.2F);
            }
        }
        if (RelicTech.open(v, "ororTechReduce", now)) {
            e.setAmount(e.getAmount() * (1.0F - Math.min(0.9F, d.getFloat("ororTechReduce"))));
        }
        if (src instanceof Player p && src != v && RelicTech.melee(e.getSource(), p) && !RelicArts.busy()) {
            CompoundTag pd = p.getPersistentData();
            if (RelicTech.open(p, "ororTechNext", now)) {
                e.setAmount(e.getAmount() * Math.max(1.0F, pd.getFloat("ororTechNext")));
                pd.remove("ororTechNextUntil");
            }
            if (pd.getLong("ororTechStanceUntil") > now && CharacterRelics.of(p.getMainHandItem()) != null) {
                switch (pd.getString("ororTechStance")) {
                    case "alloy" -> {
                        if (v.distanceTo(p) <= 4.0F) {
                            v.igniteForSeconds(4.0F);
                        } else {
                            v.setTicksFrozen(Math.max(v.getTicksFrozen(), 160));
                        }
                    }
                    case "heavy" -> v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 2));
                    case "supply" -> p.addEffect(new MobEffectInstance(MobEffects.DIG_SPEED, 60, 2));
                    case "trump" -> v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 1));
                    case "analysis" -> pd.putLong("ororRelicAdaptUntil", now + 100);
                    default -> {
                    }
                }
            }
        }
    }

    @SubscribeEvent
    public static void heal(LivingHealEvent e) {
        LivingEntity v = e.getEntity();
        if (!(v.level() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        CompoundTag d = v.getPersistentData();
        d.putLong("ororHealedAt", now);
        if (d.getLong("ororRegenDownUntil") > now) {
            e.setAmount(e.getAmount() * (1.0F - Math.min(0.95F, d.getFloat("ororRegenDown"))));
        }
        if (d.getLong("ororHealCurseUntil") > now && d.hasUUID("ororHealCurseOwner")) {
            // part of the healing turned to a curse's harm; the healing itself still goes through (the design)
            float harm = e.getAmount() * d.getFloat("ororHealCurseF");
            Player owner = sl.getPlayerByUUID(d.getUUID("ororHealCurseOwner"));
            if (harm > 0.0F) {
                healCursed++;
                RelicTech.later(sl, 2, () -> {
                    if (v.isAlive()) {
                        v.hurt(owner != null ? owner.damageSources().indirectMagic(owner, owner) : v.damageSources().magic(), harm);
                        v.addEffect(new MobEffectInstance(MobEffects.WITHER, 40, 0));
                    }
                });
            }
        }
    }

    @SubscribeEvent
    public static void death(LivingDeathEvent e) {
        LivingEntity v = e.getEntity();
        if (!(v.level() instanceof ServerLevel sl)) {
            return;
        }
        CompoundTag d = v.getPersistentData();
        if (d.getInt("ororCurseJumps") > 0 && d.hasUUID("ororCurseOwner")) {
            Player owner = sl.getPlayerByUUID(d.getUUID("ororCurseOwner"));
            if (owner != null) {
                LivingEntity next = nearestFoe(owner, v.position(), 8.0);
                if (next != null && next != v) {
                    // the curse moves on (twice at most)
                    curseJumps++;
                    CompoundTag n = next.getPersistentData();
                    n.putInt("ororCurseJumps", d.getInt("ororCurseJumps") - 1);
                    n.putUUID("ororCurseOwner", owner.getUUID());
                    next.addEffect(new MobEffectInstance(MobEffects.WITHER, 120, 1));
                    n.putInt("ororLayer_tragedy", Math.min(3, n.getInt("ororLayer_tragedy") + 1));
                    n.putLong("ororLayer_tragedyUntil", sl.getGameTime() + 240);
                    RelicFx.send(owner, 8, 0x8A3AFF, v.position().add(0, 1, 0), next.position().subtract(v.position()), 1, 14, 0, 0, "");
                }
            }
        }
        if (v instanceof Player p) {
            for (Unit u : new ArrayList<>(UNITS.values())) {
                if (u.owner.equals(p.getUUID())) {
                    remove(sl, u, false);
                }
            }
        }
    }

    /** Which harmful effects a living thing carries now (for the CI). */
    static int harmful(LivingEntity e) {
        return (int) e.getActiveEffects().stream().filter(m -> m.getEffect().value().getCategory() == MobEffectCategory.HARMFUL).count();
    }

    static boolean holdsRelic(Player p, String slot) {
        RelicSpec s = CharacterRelics.of(p.getMainHandItem());
        return s != null && s.slot.equals(slot);
    }
}
