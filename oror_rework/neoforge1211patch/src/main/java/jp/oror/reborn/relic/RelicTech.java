package jp.oror.reborn.relic;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.Abilities;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.RelicArts;
import jp.oror.reborn.RelicPowers;
import jp.oror.reborn.RelicSpec;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.FlyingMob;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.WaterAnimal;
import net.minecraft.world.entity.monster.Drowned;
import net.minecraft.world.entity.monster.Guardian;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.monster.SpellcasterIllager;
import net.minecraft.world.entity.monster.Witch;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ShieldItem;
import net.minecraft.world.item.TridentItem;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.LevelTickEvent;

/**
 * (058) The 123 techniques of the god-slaying weapons (V9 特殊技Ⅰ・Ⅱ・武器専用必殺技), on their own three keys and their
 * own cooldowns, apart from the combo, the right-click arts and the legends' stages.
 *
 * <p>A key press is only a wish: the server checks the weapon in hand, the cooldown and that nothing else is being
 * readied, then the technique is readied for its own time (the stance and the aim, the build, or the finisher's omen:
 * slowed, the warning drawn), released along the look of that moment, and its program runs: what it reaches, what it
 * does, its later moments (after, rep, pts), the 3D shapes the clients draw. A technique cut off (the weapon put away,
 * the bearer dead or gone) costs no cooldown. Damage is the technique's base into the target's defence, through the
 * marks, hit caps and never-lethal rules the program sets.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RelicTech {
    private static final ResourceLocation STANCE = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "relic_tech_stance");
    private static final Map<UUID, Cast> CASTS = new HashMap<>();
    private static final List<Pending> PENDING = new ArrayList<>();
    /** What the CI reads: casts released, cut off, refused (cooldown, no weapon, busy). */
    public static int released, cut, refused;
    public static final List<String> LOG = Collections.synchronizedList(new ArrayList<>());

    private RelicTech() {
    }

    /** One technique being readied or at work. */
    public static final class Cast {
        public final UUID who;
        /** the bearer itself (a CI player is in no level's list of players) */
        public final ServerPlayer player;
        public final RelicV9.Tech t;
        public final long start, release;
        public long until;
        public boolean released, animated;
        public final Map<Integer, Integer> hits = new HashMap<>();
        public int hitcap;
        public boolean anyHit;
        public float dealt;
        public int counter;

        Cast(ServerPlayer player, RelicV9.Tech t, long start, long release) {
            this.who = player.getUUID();
            this.player = player;
            this.t = t;
            this.start = start;
            this.release = release;
        }
    }

    private record Pending(ServerLevel sl, long due, RelicArts.Ctx c, List<JsonObject> ops, Runnable run) {
    }

    // ------------------------------------------------------------------------------------------------------ the keys

    /** The player pressed the key of technique slot 0, 1 or 2. */
    public static void press(ServerPlayer p, int slot) {
        start(p, slot, false);
    }

    /** Readies the technique of the held weapon's slot; forced (the CI) skips the cooldown. True when it began. */
    public static boolean start(ServerPlayer p, int slot, boolean forced) {
        if (slot < 0 || slot > 2 || !p.isAlive() || p.isSpectator() || !(p.level() instanceof ServerLevel sl)) {
            return false;
        }
        RelicSpec s = CharacterRelics.of(p.getMainHandItem());
        RelicV9.Tech[] ts = s == null ? null : RelicV9.of(s.id);
        if (ts == null || ts[slot] == null) {
            p.displayClientMessage(Component.literal("神討伐武器を手に持つと特殊技を使える").withStyle(ChatFormatting.GRAY), true);
            refused++;
            return false;
        }
        if (CASTS.containsKey(p.getUUID())) {
            refused++;
            return false;
        }
        RelicV9.Tech t = ts[slot];
        long now = sl.getGameTime();
        long ready = p.getPersistentData().getCompound("ororTechReady").getLong(t.id);
        if (!forced && now < ready) {
            p.displayClientMessage(Component.literal(t.label + "「" + t.name + "」再使用まで " + ((ready - now + 19) / 20) + "秒")
                .withStyle(ChatFormatting.GRAY), true);
            refused++;
            return false;
        }
        Cast c = new Cast(p, t, now, now + t.windup());
        CASTS.put(p.getUUID(), c);
        AttributeInstance speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null && !speed.hasModifier(STANCE)) {
            speed.addTransientModifier(new AttributeModifier(STANCE, t.slot == 2 ? -0.6 : -0.35, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        }
        RelicNet.toWatchers(p, new RelicNet.Show(p.getId(), t.index, c.start, c.release, 0));
        sl.playSound(null, p.blockPosition(), t.slot == 2 ? SoundEvents.BEACON_POWER_SELECT : SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS,
            1.0F, t.slot == 2 ? 0.6F : 1.3F);
        p.displayClientMessage(Component.literal(t.label + "「" + t.name + "」").withStyle(t.slot == 2 ? ChatFormatting.GOLD : ChatFormatting.AQUA), true);
        if (t.slot == 2) {
            // the finisher's great omen: a circle under the bearer for the whole of it, and its name above
            RelicFx.send(p, 4, t.color, p.position().add(0, 0.05, 0), new Vec3(0, 1, 0), 6.0F, t.windup() + t.forming(), 0, 0, t.name);
            RelicFx.send(p, 10, t.color, p.position().add(0, p.getBbHeight() + 1.2, 0), new Vec3(0, 1, 0), 1.6F, t.windup(), 0, 0, t.name);
        }
        return true;
    }

    public static boolean casting(Player p) {
        return CASTS.containsKey(p.getUUID());
    }

    public static Cast castOf(Player p) {
        return CASTS.get(p.getUUID());
    }

    private static void endCast(ServerLevel sl, Player p, Cast c, int reason) {
        CASTS.remove(c.who);
        if (p != null) {
            AttributeInstance speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
            if (speed != null) {
                speed.removeModifier(STANCE);
            }
            RelicNet.toWatchers(p, new RelicNet.Show(p.getId(), -1, c.start, c.release, reason));
            if (reason == 0 && !c.anyHit) {
                CompoundTag d = p.getPersistentData();
                d.putInt("ororTechMisses", d.getInt("ororTechMisses") + 1);
            }
        }
        if (reason != 0) {
            cut++;
        }
    }

    private static void release(ServerLevel sl, ServerPlayer p, Cast c) {
        c.released = true;
        long now = sl.getGameTime();
        AttributeInstance speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null) {
            speed.removeModifier(STANCE);
        }
        CompoundTag ready = p.getPersistentData().getCompound("ororTechReady");
        ready.putLong(c.t.id, now + c.t.cd);
        p.getPersistentData().put("ororTechReady", ready);
        RelicNet.toPlayer(p, new RelicNet.Ready(c.t.index, now + c.t.cd));
        RelicArts.Ctx f = new RelicArts.Ctx();
        f.origin = p.getEyePosition();
        f.dir = p.getLookAngle().normalize();
        f.at = p.position();
        f.cast = c;
        RelicArts.runTech(c.t.relic, p, c.t.damage, c.t.prog, f, null);
        c.until = now + Math.max(30, c.t.forming() + 40);
        released++;
        LOG.add(c.t.id + " released at " + now);
    }

    @SubscribeEvent
    public static void tick(LevelTickEvent.Post e) {
        if (!(e.getLevel() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        if (!CASTS.isEmpty()) {
            for (Cast c : new ArrayList<>(CASTS.values())) {
                ServerPlayer p = c.player;
                if (p.level() != sl) {
                    if (p.isRemoved() && !p.isAlive()) {
                        endCast(sl, null, c, 1);
                    }
                    continue;
                }
                if (!p.isAlive() || p.isRemoved()) {
                    endCast(sl, p, c, 1);
                    continue;
                }
                if (!c.released) {
                    RelicSpec s = CharacterRelics.of(p.getMainHandItem());
                    if (s == null || !s.id.equals(c.t.relic)) {
                        endCast(sl, p, c, 1);
                        continue;
                    }
                    if (!c.animated && now >= c.release - 6) {
                        c.animated = true;
                        Ef.play(p, c.t.anim);
                    }
                    if (now >= c.release) {
                        release(sl, p, c);
                    }
                } else if (now >= c.until) {
                    endCast(sl, p, c, 0);
                }
            }
        }
        if (!PENDING.isEmpty()) {
            List<Pending> due = new ArrayList<>();
            synchronized (PENDING) {
                Iterator<Pending> it = PENDING.iterator();
                while (it.hasNext()) {
                    Pending x = it.next();
                    if (x.sl == sl && now >= x.due) {
                        due.add(x);
                        it.remove();
                    }
                }
            }
            for (Pending x : due) {
                try {
                    if (x.run != null) {
                        x.run.run();
                    } else if (x.c.p.isAlive() && !x.c.p.isRemoved()) {
                        RelicArts.runTech(x.c.art.id, x.c.p, x.c.base, x.ops, x.c, null);
                    }
                } catch (RuntimeException ex) {
                    LOG.add("pending failed: " + ex);
                }
            }
        }
    }

    /** Runs these ops on a copy of this frame after so many ticks (0: now). */
    public static void later(RelicArts.Ctx c, int ticks, List<JsonObject> ops) {
        RelicArts.Ctx k = c.copy();
        if (ticks <= 0) {
            RelicArts.exec(k, ops);
            return;
        }
        synchronized (PENDING) {
            PENDING.add(new Pending(c.sl, c.sl.getGameTime() + ticks, k, ops, null));
        }
    }

    /** Runs this after so many ticks (the legends' crowning attacks, the crisis guards' timings). */
    public static void later(ServerLevel sl, int ticks, Runnable r) {
        if (ticks <= 0) {
            r.run();
            return;
        }
        synchronized (PENDING) {
            PENDING.add(new Pending(sl, sl.getGameTime() + ticks, null, null, r));
        }
    }

    @SubscribeEvent
    public static void login(PlayerEvent.PlayerLoggedInEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            long now = p.level().getGameTime();
            CompoundTag ready = p.getPersistentData().getCompound("ororTechReady");
            for (RelicV9.Tech t : RelicV9.TECHS) {
                long at = ready.getLong(t.id);
                if (at > now) {
                    RelicNet.toPlayer(p, new RelicNet.Ready(t.index, at));
                }
            }
        }
    }

    // ------------------------------------------------------------------------------------------------- damage hooks

    /** The share a blow of this frame deals this target: hit caps, marks, never-lethal blows. */
    public static float amount(RelicArts.Ctx c, LivingEntity e, float base) {
        float a = base;
        if (c.cast instanceof Cast cast) {
            int n = cast.hits.getOrDefault(e.getId(), 0);
            if (cast.hitcap > 0 && n >= cast.hitcap) {
                return 0.0F;
            }
            cast.hits.put(e.getId(), n + 1);
        }
        CompoundTag d = e.getPersistentData();
        if (RelicArts.busy() && d.getLong("ororArtMarkUntil") > c.sl.getGameTime()) {
            a *= Math.max(1.0F, d.getFloat("ororArtMarkX"));
        }
        if (c.nonlethal) {
            a = Math.min(a, Math.max(0.0F, e.getHealth() - 1.0F));
        }
        return a;
    }

    /** What a blow of this frame took. */
    public static void dealt(RelicArts.Ctx c, LivingEntity e, float hp) {
        if (c.cast instanceof Cast cast && hp > 0.0F) {
            cast.anyHit = true;
            cast.dealt += hp;
        }
    }

    // -------------------------------------------------------------------------------------------------------- the ops

    static double num(JsonObject o, String k, double d) {
        return o.has(k) ? o.get(k).getAsDouble() : d;
    }

    static String str(JsonObject o, String k, String d) {
        return o.has(k) ? o.get(k).getAsString() : d;
    }

    static List<JsonObject> list(JsonObject o, String k) {
        List<JsonObject> l = new ArrayList<>();
        if (o.has(k) && o.get(k).isJsonArray()) {
            for (JsonElement e : o.getAsJsonArray(k)) {
                if (e.isJsonObject()) {
                    l.add(e.getAsJsonObject());
                }
            }
        }
        return l;
    }

    static Vec3 at(RelicArts.Ctx c) {
        return c.at != null ? c.at : c.p.position();
    }

    /** The ground at or just under a point (the point itself in the air with nothing below). */
    static Vec3 ground(ServerLevel sl, Vec3 v) {
        BlockPos b = BlockPos.containing(v.x, v.y + 2, v.z);
        for (int i = 0; i < 10; i++, b = b.below()) {
            if (!sl.getBlockState(b).getCollisionShape(sl, b).isEmpty() && sl.getBlockState(b.above()).getCollisionShape(sl, b.above()).isEmpty()) {
                return new Vec3(v.x, b.getY() + 1.0, v.z);
            }
        }
        return v;
    }

    static boolean strong(LivingEntity e) {
        return e instanceof SupremeEntity || e.getMaxHealth() >= 300.0F || e.getType().is(net.neoforged.neoforge.common.Tags.EntityTypes.BOSSES);
    }

    static List<LivingEntity> enemies(RelicArts.Ctx c) {
        List<LivingEntity> l = new ArrayList<>();
        for (LivingEntity e : c.t) {
            if (e != c.p && RelicPowers.enemy(c.p, e)) {
                l.add(e);
            }
        }
        return l;
    }

    /** The foe the bearer means: the one nearest its look within the reach, else the nearest before it. */
    static LivingEntity focus(RelicArts.Ctx c, double r) {
        Vec3 eye = c.eye(), d = c.look();
        LivingEntity best = null;
        double score = Double.MAX_VALUE;
        for (LivingEntity e : RelicArts.near(c.p, c.p.position(), r)) {
            Vec3 to = e.position().add(0, e.getBbHeight() * 0.5, 0).subtract(eye);
            double len = to.length();
            if (len < 1.0E-3) {
                return e;
            }
            double cos = to.scale(1.0 / len).dot(d);
            if (cos < 0.5 || !c.p.hasLineOfSight(e)) {
                continue;
            }
            double s = (1.0 - cos) * 40.0 + len * 0.05;
            if (s < score) {
                score = s;
                best = e;
            }
        }
        return best;
    }

    public static boolean op(RelicArts.Ctx c, JsonObject o) {
        String op = o.get("op").getAsString();
        Player p = c.p;
        ServerLevel sl = c.sl;
        long now = sl.getGameTime();
        switch (op) {
            case "spot" -> c.t = RelicArts.sorted(RelicArts.near(p, at(c), num(o, "r", 6.0)), at(c), (int) num(o, "n", 12.0));
            case "focus", "predict" -> {
                double r = num(o, "r", 16.0);
                LivingEntity t = focus(c, r);
                c.t = new ArrayList<>();
                if (t != null) {
                    c.t.add(t);
                    Vec3 v = t.position();
                    if (op.equals("predict")) {
                        Vec3 m = t.getDeltaMovement().multiply(1.0, 0.0, 1.0).scale(num(o, "lead", 10.0));
                        v = v.add(m.length() > 6.0 ? m.normalize().scale(6.0) : m);
                    }
                    c.at = v;
                    if (c.victim == null) {
                        c.victim = t;
                    }
                } else {
                    c.at = ground(sl, p.position().add(RelicArts.flat(c.look()).scale(Math.min(8.0, r))));
                }
            }
            case "ahead" -> c.at = ground(sl, p.position().add(RelicArts.flat(c.look()).scale(num(o, "d", 6.0))));
            case "cap" -> {
                int n = (int) num(o, "n", 12.0);
                if (c.t.size() > n) {
                    c.t = new ArrayList<>(c.t.subList(0, n));
                }
            }
            case "pts" -> {
                int n = (int) num(o, "n", 6.0);
                double r = num(o, "r", 6.0), hr = num(o, "hr", 2.5);
                int gap = (int) num(o, "gap", 2.0);
                Vec3 centre = at(c);
                List<JsonObject> sub = list(o, "ops");
                for (int i = 0; i < n; i++) {
                    double ang = i * 2.39996, rad = r * Math.sqrt((i + 0.5) / n);
                    Vec3 pt = ground(sl, centre.add(Math.cos(ang) * rad, 0, Math.sin(ang) * rad));
                    RelicArts.Ctx k = c.copy();
                    k.at = pt;
                    k.t = RelicArts.sorted(RelicArts.near(p, pt, hr), pt, 6);
                    later(k, i * gap, sub);
                }
            }
            case "rows" -> {
                int n = (int) num(o, "n", 3.0);
                double r = num(o, "r", 32.0), w = num(o, "w", 1.5), gap = num(o, "gap", 2.0);
                Vec3 d = c.look(), side = new Vec3(-d.z, 0, d.x);
                side = side.lengthSqr() < 1.0E-6 ? new Vec3(1, 0, 0) : side.normalize();
                List<JsonObject> sub = list(o, "ops");
                for (int i = 0; i < n; i++) {
                    RelicArts.Ctx k = c.copy();
                    k.origin = c.eye().add(side.scale((i - (n - 1) * 0.5) * gap));
                    k.t = RelicArts.line(p, k.origin, d, r, w);
                    RelicArts.exec(k, sub);
                    c.dealt += k.dealt;
                }
            }
            case "hpdmg" -> {
                for (LivingEntity e : enemies(c)) {
                    if (strong(e)) {
                        float extra = (float) Math.min(num(o, "cap", 2000000.0), e.getMaxHealth() * num(o, "pct", 0.05));
                        hurt(c, e, extra);
                    }
                }
            }
            case "hold" -> {
                int t = (int) num(o, "t", 40.0);
                for (LivingEntity e : enemies(c)) {
                    CompoundTag d = e.getPersistentData();
                    if (strong(e)) {
                        // the design: no full binding of the strong, and never over and over: a heavy slowing instead
                        e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, t, 3));
                        Mods.add(e, Attributes.ATTACK_SPEED, "hold", -0.4, t);
                    } else if (now >= d.getLong("ororHoldGrace")) {
                        Abilities.stun(e, t);
                        d.putLong("ororHoldGrace", now + t * 2L);
                    } else {
                        e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, t, 2));
                    }
                }
            }
            case "armor" -> {
                double pct = num(o, "p", 0.3);
                int t = (int) num(o, "t", 160.0);
                for (LivingEntity e : enemies(c)) {
                    Mods.add(e, Attributes.ARMOR, "armor", -pct, t);
                    Mods.add(e, Attributes.ARMOR_TOUGHNESS, "toughness", -pct, t);
                }
            }
            case "atkdown" -> {
                for (LivingEntity e : enemies(c)) {
                    Mods.add(e, Attributes.ATTACK_DAMAGE, "atkdown", -num(o, "p", 0.3), (int) num(o, "t", 120.0));
                }
            }
            case "regendown" -> {
                for (LivingEntity e : enemies(c)) {
                    e.getPersistentData().putLong("ororRegenDownUntil", now + (long) num(o, "t", 160.0));
                    e.getPersistentData().putFloat("ororRegenDown", (float) num(o, "p", 0.7));
                }
            }
            case "stripone" -> {
                boolean any = false;
                for (LivingEntity e : enemies(c)) {
                    for (MobEffectInstance m : new ArrayList<>(e.getActiveEffects())) {
                        if (m.getEffect().value().isBeneficial()) {
                            e.removeEffect(m.getEffect());
                            any = true;
                            break;
                        }
                    }
                }
                if (any) {
                    RelicArts.exec(c, list(o, "then"));
                }
            }
            case "cleanone" -> {
                for (LivingEntity e : c.t) {
                    for (MobEffectInstance m : new ArrayList<>(e.getActiveEffects())) {
                        if (m.getEffect().value().getCategory() == MobEffectCategory.HARMFUL) {
                            e.removeEffect(m.getEffect());
                            break;
                        }
                    }
                }
            }
            case "punish" -> {
                String name = str(o, "e", "weakness");
                int t = (int) num(o, "t", 40.0);
                for (LivingEntity e : enemies(c)) {
                    Punish.apply(e, name, t);
                }
            }
            case "suppress" -> {
                // the focuses on the strong: whatever stops their moving fails, their guard, healing and swing are held
                int t = (int) num(o, "t", 160.0);
                for (LivingEntity e : enemies(c)) {
                    if (strong(e)) {
                        Mods.add(e, Attributes.ARMOR, "suppress_armor", -0.4, t);
                        Mods.add(e, Attributes.ATTACK_SPEED, "suppress_speed", -0.4, t);
                        e.getPersistentData().putLong("ororRegenDownUntil", now + t);
                        e.getPersistentData().putFloat("ororRegenDown", 0.7F);
                        RelicWorld.suppressed++;
                    }
                }
            }
            case "seal" -> {
                int t = (int) num(o, "t", 120.0);
                for (LivingEntity e : enemies(c)) {
                    for (MobEffectInstance m : new ArrayList<>(e.getActiveEffects())) {
                        if (m.getEffect().value().isBeneficial()) {
                            e.removeEffect(m.getEffect());
                        }
                    }
                    Mods.add(e, Attributes.ARMOR, "seal_armor", -1.0, t);
                    Mods.add(e, Attributes.ARMOR_TOUGHNESS, "seal_toughness", -1.0, t);
                    e.getPersistentData().putLong("ororSealUntil", now + t);
                }
            }
            case "shieldbreak" -> {
                for (LivingEntity e : enemies(c)) {
                    boolean shield = e.getMainHandItem().getItem() instanceof ShieldItem || e.getOffhandItem().getItem() instanceof ShieldItem;
                    if (e instanceof Player q && q.isBlocking()) {
                        q.getCooldowns().addCooldown(q.getUseItem().getItem(), 100);
                        q.stopUsingItem();
                        sl.broadcastEntityEvent(q, (byte) 30);
                    } else if (e.isBlocking()) {
                        e.stopUsingItem();
                    }
                    e.getPersistentData().putLong("ororGuardBrokenUntil", now + 100);
                    if (shield) {
                        hurt(c, e, c.base * 0.2F);
                    }
                }
            }
            case "layer" -> {
                String k = "ororLayer_" + str(o, "k", "mark");
                for (LivingEntity e : enemies(c)) {
                    CompoundTag d = e.getPersistentData();
                    int have = d.getLong(k + "Until") > now ? d.getInt(k) : 0;
                    d.putInt(k, (int) Math.min(num(o, "max", 3.0), have + num(o, "n", 1.0)));
                    d.putLong(k + "Until", now + (long) num(o, "t", 200.0));
                }
            }
            case "burst" -> {
                String k = "ororLayer_" + str(o, "k", "mark");
                for (LivingEntity e : enemies(c)) {
                    CompoundTag d = e.getPersistentData();
                    int n = d.getLong(k + "Until") > now ? d.getInt(k) : 0;
                    if (n > 0) {
                        d.remove(k);
                        d.remove(k + "Until");
                        hurt(c, e, (float) (c.base * num(o, "m", 0.1) * n));
                        RelicFx.send(p, 12, c.color, e.position().add(0, e.getBbHeight() * 0.6, 0), new Vec3(0, 1, 0), 0.8F + n * 0.4F, 10, 0, 0, "");
                    }
                }
            }
            case "drain" -> p.heal(c.dealt * (float) num(o, "f", 0.001));
            case "nextx" -> window(p, "ororTechNext", now + (long) num(o, "t", 120.0), (float) num(o, "x", 1.5));
            case "parry" -> {
                window(p, "ororTechParry", now + (long) num(o, "t", 20.0), (float) num(o, "x", 1.5));
                p.getPersistentData().putFloat("ororTechParryDmg", (float) (c.base * num(o, "m", 0.3)));
                p.getPersistentData().putString("ororTechParryArt", c.art.id);
            }
            case "throw" -> p.getPersistentData().putLong("ororTechThrowUntil", p.getPersistentData().getLong("ororTechParryUntil"));
            case "store" -> {
                window(p, "ororTechStore", now + (long) num(o, "t", 60.0), (float) num(o, "n", 3.0));
                p.getPersistentData().putFloat("ororTechStored", 0.0F);
                p.getPersistentData().putInt("ororTechStoredN", 0);
            }
            case "release" -> {
                CompoundTag d = p.getPersistentData();
                int n = d.getInt("ororTechStoredN");
                float stored = d.getFloat("ororTechStored");
                d.remove("ororTechStoreUntil");
                // the stored blows gathered into one: its power from how many, the reflection capped at the base
                float a = (float) Math.min(c.base * num(o, "m", 1.0), c.base * (0.4 + 0.2 * n) + stored * 20.0F);
                for (LivingEntity e : enemies(c)) {
                    hurt(c, e, a);
                }
                d.putFloat("ororTechStored", 0.0F);
                d.putInt("ororTechStoredN", 0);
            }
            case "gravity" -> {
                int t = (int) num(o, "t", 60.0);
                for (LivingEntity e : enemies(c)) {
                    e.addEffect(new MobEffectInstance(MobEffects.LEVITATION, t, 1));
                    // the way back down without the fall's harm (the design limits it)
                    e.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, t + 80, 0));
                }
            }
            case "toy" -> {
                int t = (int) num(o, "t", 100.0);
                double s = num(o, "s", 0.45);
                for (LivingEntity e : enemies(c)) {
                    Mods.add(e, Attributes.SCALE, "toy", s - 1.0, t, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
                    e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, t, 1));
                }
            }
            case "reduce" -> {
                List<LivingEntity> to = o.has("to") ? c.t : List.of(p);
                for (LivingEntity e : to) {
                    if (e == p || !RelicPowers.enemy(p, e)) {
                        window(e, "ororTechReduce", now + (long) num(o, "t", 100.0), (float) num(o, "p", 0.5));
                    }
                }
            }
            case "exposed" -> window(p, "ororTechExposed", now + (long) num(o, "t", 60.0), 1.2F);
            case "stance" -> {
                p.getPersistentData().putString("ororTechStance", str(o, "k", ""));
                p.getPersistentData().putLong("ororTechStanceUntil", now + (long) num(o, "t", 300.0));
            }
            case "after" -> later(c, (int) num(o, "t", 10.0), list(o, "ops"));
            case "rep" -> {
                int n = (int) num(o, "n", 3.0), gap = (int) num(o, "gap", 4.0);
                for (int i = 0; i < n; i++) {
                    later(c, i * gap, list(o, "ops"));
                }
            }
            case "cue" -> RelicFx.cue(c, o);
            case "unit" -> RelicWorld.units(c, o);
            case "field" -> RelicWorld.field(c, o);
            case "ultimate" -> RelicUltimate.start(c);
            case "mimic" -> {
                String last = p.getPersistentData().getString("ororLastHurtType");
                c.t = RelicArts.line(p, c.eye(), c.look(), 18.0, 2.5);
                for (LivingEntity e : enemies(c)) {
                    hurt(c, e, (float) (c.base * num(o, "m", 0.8)));
                    switch (last) {
                        case "fire" -> e.igniteForSeconds(5.0F);
                        case "magic" -> e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
                        case "projectile" -> RelicArts.push(e, c.look().scale(1.4).add(0, 0.3, 0));
                        case "explosion" -> RelicArts.push(e, new Vec3(0, 1.0, 0));
                        default -> e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1));
                    }
                }
                RelicFx.send(p, 2, c.color, c.eye(), c.look(), 18.0F, 10, 0.4F, 0, "");
            }
            case "branch" -> {
                JsonArray a = o.getAsJsonArray("ops");
                if (a != null && !a.isEmpty()) {
                    JsonArray pick = a.get(sl.random.nextInt(a.size())).getAsJsonArray();
                    List<JsonObject> l = new ArrayList<>();
                    pick.forEach(x -> l.add(x.getAsJsonObject()));
                    RelicArts.exec(c, l);
                }
            }
            case "janken" -> {
                String[] hands = {"rock", "scissors", "paper"};
                String[] names = {"グー", "チョキ", "パー"};
                int i = sl.random.nextInt(3);
                RelicFx.send(p, 10, c.color, p.position().add(0, p.getBbHeight() + 1.0, 0), new Vec3(0, 1, 0), 2.2F, 24, 0, 0, names[i]);
                p.displayClientMessage(Component.literal("じゃんけん――" + names[i] + "！").withStyle(ChatFormatting.YELLOW), true);
                later(c, 10, list(o, hands[i]));
            }
            case "colortag" -> RelicWorld.colortag(c, num(o, "r", 16.0), (float) num(o, "m", 1.0));
            case "tag" -> {
                for (LivingEntity e : enemies(c)) {
                    e.getPersistentData().putLong("ororTag_" + str(o, "k", "x"), now + (long) num(o, "t", 200.0));
                }
            }
            case "iftag", "inwater", "strong", "healed", "casters", "poisoned", "aquatic", "fliers", "clear", "friendhurters" -> {
                List<LivingEntity> keep = new ArrayList<>();
                for (LivingEntity e : enemies(c)) {
                    if (matches(op, o, c, e, now)) {
                        keep.add(e);
                    }
                }
                if (!keep.isEmpty()) {
                    RelicArts.Ctx k = c.copy();
                    k.t = keep;
                    k.victim = keep.get(0);
                    RelicArts.exec(k, list(o, "ops"));
                }
            }
            case "nonlethal" -> c.nonlethal = true;
            case "hitcap" -> {
                if (c.cast instanceof Cast cast) {
                    cast.hitcap = (int) num(o, "n", 0.0);
                }
            }
            case "sky" -> {
                BlockPos b = BlockPos.containing(at(c)).above();
                if (!sl.canSeeSky(b)) {
                    // a roof over the point: the bolt stops on it (the design's 遮蔽物への落雷判定)
                    c.t = new ArrayList<>();
                }
            }
            case "elements" -> {
                int k = (c.cast instanceof Cast cast ? cast.counter++ : sl.random.nextInt(5)) % 5;
                for (LivingEntity e : enemies(c)) {
                    switch (k) {
                        case 0 -> e.igniteForSeconds(4.0F);
                        case 1 -> {
                            e.setTicksFrozen(Math.max(e.getTicksFrozen(), 160));
                            e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2));
                        }
                        case 2 -> {
                            e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 1));
                            hurt(c, e, c.base * 0.03F);
                        }
                        case 3 -> e.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1));
                        default -> RelicArts.push(e, RelicArts.flat(e.position().subtract(p.position())).scale(1.2).add(0, 0.4, 0));
                    }
                }
            }
            case "armsdmg" -> {
                int alive = RelicWorld.count(p, "arm");
                float m = (float) (num(o, "m", 0.6) * (0.4 + 0.2 * Math.min(3, alive)));
                for (LivingEntity e : enemies(c)) {
                    hurt(c, e, c.base * m);
                }
            }
            case "depotdmg" -> {
                RelicArts.Ctx k = c.copy();
                k.mult = c.mult * (RelicWorld.count(p, "depot") > 0 ? 1.0F : 0.5F);
                RelicArts.exec(k, list(o, "ops"));
                c.t = k.t;
                c.at = k.at;
            }
            case "stagger" -> {
                for (LivingEntity e : enemies(c)) {
                    e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 20, 5));
                    e.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 20, 2));
                    if (!strong(e)) {
                        RelicArts.push(e, RelicArts.flat(e.position().subtract(p.position())).scale(0.6).add(0, 0.2, 0));
                    }
                }
            }
            case "byfoe" -> {
                LivingEntity f = focus(c, num(o, "r", 15.0));
                String k = f == null ? "none" : ranged(f) ? "ranged" : "melee";
                RelicArts.exec(c, list(o, k));
            }
            case "missguard" -> {
                int misses = p.getPersistentData().getInt("ororTechMisses");
                window(p, "ororTechReduce", now + 200, (float) Math.min(0.6, 0.1 + 0.1 * misses));
            }
            case "reflectdmg" -> {
                for (LivingEntity e : enemies(c)) {
                    boolean weak = e.getArmorValue() < 8 && e.getMaxHealth() < 100.0F;
                    hurt(c, e, (float) (c.base * num(o, "m", 1.0) * (weak ? 0.5 : 1.0)));
                }
            }
            case "absorbills" -> {
                int n = 0;
                for (LivingEntity e : c.t) {
                    if (e == p || !RelicPowers.enemy(p, e)) {
                        for (MobEffectInstance m : new ArrayList<>(e.getActiveEffects())) {
                            if (m.getEffect().value().getCategory() == MobEffectCategory.HARMFUL) {
                                e.removeEffect(m.getEffect());
                                n++;
                            }
                        }
                    }
                }
                CompoundTag d = p.getPersistentData();
                d.putInt("ororDrunk", Math.min(20, d.getInt("ororDrunk") + n));
                d.putLong("ororDrunkUntil", now + 600);
                p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 300, Math.min(4, 1 + n / 2)));
            }
            case "drunk" -> {
                CompoundTag d = p.getPersistentData();
                int n = d.getLong("ororDrunkUntil") > now ? d.getInt("ororDrunk") : 0;
                for (LivingEntity e : enemies(c)) {
                    hurt(c, e, (float) (c.base * num(o, "m", 0.14) * (1.0 + 0.15 * n)));
                }
            }
            case "reverse" -> {
                int t = (int) num(o, "t", 30.0);
                for (LivingEntity e : enemies(c)) {
                    Vec3 v = e.getDeltaMovement();
                    Vec3 away = v.horizontalDistanceSqr() > 1.0E-4 ? new Vec3(-v.x, 0, -v.z).normalize() : RelicArts.flat(e.position().subtract(p.position()));
                    RelicArts.push(e, away.scale(1.2).add(0, 0.25, 0));
                    e.addEffect(new MobEffectInstance(MobEffects.CONFUSION, t, 0));
                }
            }
            case "shuffle" -> {
                List<LivingEntity> l = enemies(c);
                if (l.size() >= 2) {
                    List<Vec3> spots = new ArrayList<>();
                    l.forEach(e -> spots.add(e.position()));
                    Collections.rotate(spots, 1);
                    for (int i = 0; i < l.size(); i++) {
                        l.get(i).teleportTo(spots.get(i).x, spots.get(i).y, spots.get(i).z);
                    }
                } else if (l.size() == 1) {
                    LivingEntity e = l.get(0);
                    Vec3 v = p.position().add(RelicArts.flat(c.look()).scale(3.0));
                    e.teleportTo(v.x, v.y, v.z);
                }
            }
            case "curse" -> {
                for (LivingEntity e : enemies(c)) {
                    CompoundTag d = e.getPersistentData();
                    d.putInt("ororCurseJumps", (int) num(o, "jumps", 2.0));
                    d.putUUID("ororCurseOwner", p.getUUID());
                    d.putString("ororCurseArt", c.art.id);
                    d.putFloat("ororCurseBase", c.base);
                }
            }
            case "healcurse" -> {
                for (LivingEntity e : enemies(c)) {
                    CompoundTag d = e.getPersistentData();
                    d.putLong("ororHealCurseUntil", now + (long) num(o, "t", 300.0));
                    d.putFloat("ororHealCurseF", (float) num(o, "f", 0.5));
                    d.putUUID("ororHealCurseOwner", p.getUUID());
                }
            }
            case "gather" -> {
                for (LivingEntity e : c.t) {
                    if (e != p && !RelicPowers.enemy(p, e) && e.distanceTo(p) > 3.0F) {
                        Vec3 v = p.position().add(RelicArts.flat(e.position().subtract(p.position())).scale(2.0));
                        e.teleportTo(v.x, v.y, v.z);
                        e.fallDistance = 0.0F;
                    }
                }
            }
            case "offer" -> RelicWorld.offer(c, o);
            case "contracts" -> RelicWorld.contracts(c, o);
            default -> {
                return false;
            }
        }
        return true;
    }

    private static boolean matches(String op, JsonObject o, RelicArts.Ctx c, LivingEntity e, long now) {
        return switch (op) {
            case "iftag" -> e.getPersistentData().getLong("ororTag_" + str(o, "k", "x")) > now;
            case "inwater" -> e.isInWater();
            case "strong" -> strong(e);
            case "healed" -> now - e.getPersistentData().getLong("ororHealedAt") < 100;
            case "casters" -> e instanceof SpellcasterIllager || e instanceof Witch || caster(e);
            case "poisoned" -> e.hasEffect(MobEffects.POISON);
            case "aquatic" -> e instanceof WaterAnimal || e instanceof Guardian || e instanceof Drowned || e.isInWater();
            case "fliers" -> e instanceof FlyingMob || !e.onGround();
            case "clear" -> c.p.hasLineOfSight(e);
            case "friendhurters" -> {
                LivingEntity hurt = e.getLastHurtMob();
                yield hurt != null && e.tickCount - e.getLastHurtMobTimestamp() < 200 && (hurt == c.p || !RelicPowers.enemy(c.p, hurt));
            }
            default -> false;
        };
    }

    private static boolean caster(LivingEntity e) {
        String n = e.getClass().getName().toLowerCase(java.util.Locale.ROOT);
        return n.contains("spell") || n.contains("mage") || n.contains("wizard") || n.contains("witch") || n.contains("sorc") || n.contains("necro")
            || n.contains("caster") || n.contains("priest");
    }

    private static boolean ranged(LivingEntity e) {
        ItemStack s = e.getMainHandItem();
        return e instanceof RangedAttackMob || s.getItem() instanceof BowItem || s.getItem() instanceof CrossbowItem || s.getItem() instanceof TridentItem;
    }

    /** A blow of the frame outside its dmg ops (bursts, reflections, the extra share against the strong). */
    static void hurt(RelicArts.Ctx c, LivingEntity e, float amount) {
        float a = amount(c, e, amount * c.mult);
        if (a <= 0.0F || !e.isAlive()) {
            return;
        }
        if (e instanceof SupremeEntity b) {
            jp.oror.reborn.RelicDrops.fracture(b, c.p, a);
        }
        float before = e.getHealth();
        e.invulnerableTime = 0;
        e.hurt(c.p.damageSources().playerAttack(c.p), a);
        c.dealt += Math.max(0.0F, before - e.getHealth());
        dealt(c, e, before - e.getHealth());
    }

    static void window(LivingEntity e, String key, long until, float value) {
        CompoundTag d = e.getPersistentData();
        d.putLong(key + "Until", Math.max(until, d.getLong(key + "Until")));
        d.putFloat(key, value);
    }

    static boolean open(LivingEntity e, String key, long now) {
        return e.getPersistentData().getLong(key + "Until") > now;
    }

    // -------------------------------------------------------------------------------------- the passing modifiers

    /** Attribute modifiers a technique puts on a foe for a while (broken armour, a lowered blow, a toy's size). */
    public static final class Mods {
        private record Mod(int entity, Holder<Attribute> attr, ResourceLocation id, long until) {
        }

        private static final List<Mod> ALL = new ArrayList<>();

        private Mods() {
        }

        static void add(LivingEntity e, Holder<Attribute> attr, String name, double amount, int ticks) {
            add(e, attr, name, amount, ticks, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        }

        static void add(LivingEntity e, Holder<Attribute> attr, String name, double amount, int ticks, AttributeModifier.Operation op) {
            AttributeInstance a = e.getAttribute(attr);
            if (a == null) {
                return;
            }
            ResourceLocation id = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "relic_" + name);
            a.removeModifier(id);
            a.addTransientModifier(new AttributeModifier(id, amount, op));
            long until = e.level().getGameTime() + ticks;
            synchronized (ALL) {
                ALL.removeIf(m -> m.entity == e.getId() && m.id.equals(id));
                ALL.add(new Mod(e.getId(), attr, id, until));
            }
        }

        static void tick(ServerLevel sl) {
            long now = sl.getGameTime();
            synchronized (ALL) {
                ALL.removeIf(m -> {
                    if (now < m.until) {
                        return false;
                    }
                    Entity x = sl.getEntity(m.entity);
                    if (x == null) {
                        return now - m.until > 600;
                    }
                    if (x instanceof LivingEntity le) {
                        AttributeInstance a = le.getAttribute(m.attr);
                        if (a != null) {
                            a.removeModifier(m.id);
                        }
                    }
                    return true;
                });
            }
        }

        public static boolean has(LivingEntity e, String name) {
            synchronized (ALL) {
                return ALL.stream().anyMatch(m -> m.entity == e.getId() && m.id.getPath().equals("relic_" + name));
            }
        }
    }

    @SubscribeEvent
    public static void mods(LevelTickEvent.Post e) {
        if (e.getLevel() instanceof ServerLevel sl && (sl.getGameTime() % 5L) == 0L) {
            Mods.tick(sl);
        }
    }

    // ---------------------------------------------------------------------------------- Epic Fight's swing, if there

    /** Plays the first of these Epic Fight animations this Epic Fight has on the player (nothing without it). */
    static final class Ef {
        private static java.lang.invoke.MethodHandle getPatch, play;
        private static Class<?> living, animations, entityPatch;
        private static boolean looked, broken;
        private static final Map<String, Object> FOUND = new HashMap<>();
        static final List<String> MISSING = new ArrayList<>();
        static int played;
        static String playWhy = "";

        private Ef() {
        }

        static String why = "";

        /**
         * Epic Fight's two methods, found by name and exact type through method handles. Reflection's lists of methods
         * (getMethods, getMethod) load every type their class names, and on a dedicated server one of them is the
         * client's LocalPlayer: the lookup threw there and no technique moved (the third 058 run).
         */
        private static void look() {
            if (looked) {
                return;
            }
            looked = true;
            java.lang.invoke.MethodHandles.Lookup lk = java.lang.invoke.MethodHandles.publicLookup();
            try {
                animations = Class.forName("yesman.epicfight.gameasset.Animations");
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                why += " animations:" + ex;
            }
            try {
                living = Class.forName("yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch");
                entityPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.EntityPatch");
                Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
                for (Class<?> ret : new Class<?>[]{entityPatch, living, Object.class}) {
                    try {
                        getPatch = lk.findStatic(caps, "getEntityPatch", java.lang.invoke.MethodType.methodType(ret, Entity.class, Class.class));
                        break;
                    } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                        // another erasure of its return
                    }
                }
                if (getPatch == null) {
                    why += " no getEntityPatch";
                }
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                why += " caps:" + ex;
            }
            broken = animations == null || living == null;
        }

        /** playAnimationSynchronized(animation, float), its first parameter's type found from an animation itself. */
        private static java.lang.invoke.MethodHandle play(Object anim) {
            if (play != null || anim == null) {
                return play;
            }
            java.lang.invoke.MethodHandles.Lookup lk = java.lang.invoke.MethodHandles.publicLookup();
            java.util.ArrayDeque<Class<?>> todo = new java.util.ArrayDeque<>();
            java.util.Set<Class<?>> seen = new java.util.HashSet<>();
            todo.add(anim.getClass());
            while (!todo.isEmpty() && play == null) {
                Class<?> c = todo.poll();
                if (c == null || !seen.add(c)) {
                    continue;
                }
                try {
                    play = lk.findVirtual(living, "playAnimationSynchronized", java.lang.invoke.MethodType.methodType(void.class, c, float.class));
                } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                    if (c.getSuperclass() != null) {
                        todo.add(c.getSuperclass());
                    }
                    Collections.addAll(todo, c.getInterfaces());
                }
            }
            if (play == null) {
                // the old way, by the list of methods: it works wherever the client's classes may be loaded
                try {
                    for (Method m : living.getMethods()) {
                        if (m.getName().equals("playAnimationSynchronized") && m.getParameterCount() == 2 && m.getParameterTypes()[1] == float.class) {
                            play = lk.unreflect(m);
                        }
                    }
                } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                    why += " no playAnimationSynchronized for " + anim.getClass().getName() + " (" + ex.getClass().getSimpleName() + ")";
                }
            }
            return play;
        }

        static Object anim(String name) {
            look();
            if (broken) {
                return null;
            }
            if (FOUND.containsKey(name)) {
                return FOUND.get(name);
            }
            Object a = null;
            try {
                Field f = animations.getField(name);
                a = f.get(null);
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                MISSING.add(name);
            }
            FOUND.put(name, a);
            return a;
        }

        static String play(Player p, List<String> names) {
            if (!ModList.get().isLoaded("epicfight")) {
                return null;
            }
            try {
                look();
                if (broken || getPatch == null) {
                    return null;
                }
                Object patch = getPatch.invokeWithArguments(p, living);
                if (patch == null || !living.isInstance(patch)) {
                    playWhy = "no patch on " + p.getClass().getSimpleName();
                    return null;
                }
                for (String n : names) {
                    Object a = anim(n);
                    java.lang.invoke.MethodHandle h = play(a);
                    if (a != null && h != null) {
                        h.invokeWithArguments(patch, a, 0.05F);
                        played++;
                        return n;
                    }
                }
            } catch (Throwable ex) {
                // the swing goes unanimated
                playWhy = String.valueOf(ex);
            }
            return null;
        }

        /** For the CI: which of the techniques' motions this Epic Fight has. */
        static String census() {
            int found = 0, all = 0;
            java.util.Set<String> seen = new java.util.TreeSet<>();
            for (RelicV9.Tech t : RelicV9.TECHS) {
                for (String n : t.anim) {
                    if (seen.add(n)) {
                        all++;
                        if (anim(n) != null) {
                            found++;
                        }
                    }
                }
            }
            int moving = 0;
            for (RelicV9.Tech t : RelicV9.TECHS) {
                if (t.anim.stream().anyMatch(n -> anim(n) != null)) {
                    moving++;
                }
            }
            look();
            if (!broken && !FOUND.isEmpty()) {
                FOUND.values().stream().filter(java.util.Objects::nonNull).findFirst().ifPresent(Ef::play);
            }
            return found + "/" + all + " techniques " + moving + "/" + RelicV9.TECHS.size() + " missing=" + MISSING + " handles=" + (getPatch != null)
                + "/" + (play != null) + (why.isEmpty() ? "" : " why=" + why);
        }
    }

    // ----------------------------------------------------------------------------------------------- what is known

    /** Whether this damage is a melee blow struck by the player itself. */
    static boolean melee(DamageSource s, Player p) {
        return s.getDirectEntity() == p && !s.is(DamageTypeTags.IS_PROJECTILE);
    }

    static String kindOf(DamageSource s) {
        if (s.is(DamageTypeTags.IS_FIRE)) {
            return "fire";
        }
        if (s.is(DamageTypeTags.IS_PROJECTILE)) {
            return "projectile";
        }
        if (s.is(DamageTypeTags.IS_EXPLOSION)) {
            return "explosion";
        }
        if (s.is(DamageTypeTags.WITCH_RESISTANT_TO) || s.getMsgId().contains("magic")) {
            return "magic";
        }
        return "melee";
    }

    static void particles(ServerLevel sl, Vec3 at, int n) {
        sl.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, n, 0.4, 0.4, 0.4, 0.05);
    }

    static Holder<MobEffect> effect(String n) {
        return RelicArts.effect(n);
    }
}
