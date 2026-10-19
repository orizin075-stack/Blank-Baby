package jp.oror.reborn;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.animal.Wolf;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingHurtEvent;

/**
 * Data-driven relic arts. Every relic (and every dungeon replica) has its own program in
 * assets/oror_supreme_bosses/relic_arts.json: "cast" runs on use, "passive" every second while the relic
 * is held in either hand, "hit" when its holder strikes something with it. A program is a list of ops;
 * selector ops choose the current targets and action ops apply to them.
 */
public final class RelicArts {
    public static final Map<String, Art> ALL = load();
    private static final ThreadLocal<Boolean> BUSY = ThreadLocal.withInitial(() -> false);

    public static final class Art {
        public String id;
        public String character;
        public int rank = 1;
        public int cooldown = -1;
        public List<JsonObject> cast = List.of();
        public List<JsonObject> passive = List.of();
        public List<JsonObject> hit = List.of();
    }

    private static Map<String, Art> load() {
        Map<String, Art> out = new HashMap<>();
        try (InputStream in = RelicArts.class.getResourceAsStream("/assets/oror_supreme_bosses/relic_arts.json")) {
            if (in == null) {
                return Collections.unmodifiableMap(out);
            }
            JsonElement root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8));
            JsonObject top = root.getAsJsonObject();
            Iterator<JsonElement> it = top.getAsJsonArray("arts").iterator();
            while (it.hasNext()) {
                JsonObject o = it.next().getAsJsonObject();
                Art a = new Art();
                a.id = o.get("id").getAsString();
                a.character = o.get("character").getAsString();
                a.rank = o.has("rank") ? o.get("rank").getAsInt() : 1;
                a.cooldown = o.has("cd") ? o.get("cd").getAsInt() : -1;
                a.cast = ops(o, "cast");
                a.passive = ops(o, "passive");
                a.hit = ops(o, "hit");
                out.put(a.id, a);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Invalid relic_arts.json", e);
        }
        return Collections.unmodifiableMap(out);
    }

    private static List<JsonObject> ops(JsonObject o, String key) {
        List<JsonObject> list = new ArrayList<>();
        if (o.has(key)) {
            Iterator<JsonElement> it = o.getAsJsonArray(key).iterator();
            while (it.hasNext()) {
                list.add(it.next().getAsJsonObject());
            }
        }
        return list;
    }

    // ------------------------------------------------------------------------------------- entry points
    public static Art of(String id) {
        return ALL.get(id);
    }

    public static boolean cast(String id, Player p) {
        Art a = ALL.get(id);
        if (a == null || !(p.level() instanceof ServerLevel sl)) {
            return false;
        }
        run(a, a.cast, sl, p, null);
        p.getPersistentData().putInt("ororRelicCasts", p.getPersistentData().getInt("ororRelicCasts") + 1);
        return true;
    }

    public static void passive(String id, Player p) {
        Art a = ALL.get(id);
        if (a != null && p.level() instanceof ServerLevel sl && !a.passive.isEmpty()) {
            run(a, a.passive, sl, p, null);
        }
    }

    public static int cooldown(String id, int fallback) {
        Art a = ALL.get(id);
        return a == null || a.cooldown < 0 ? fallback : a.cooldown;
    }

    /** Hooked into LivingHurtEvent before the relic shield logic. Returns true when cancelled. */
    public static boolean incoming(LivingHurtEvent e) {
        LivingEntity v = e.getEntity();
        if (!(v.level() instanceof ServerLevel sl)) {
            return false;
        }
        long now = sl.getGameTime();
        CompoundTag vd = v.getPersistentData();
        if (v instanceof Player vp) {
            if (WeaponSkills.guard(e, vp, sl)) {
                return true;
            }
            if (vd.getLong("ororArtGuardUntil") > now) {
                e.setCanceled(true);
                return true;
            }
            Entity direct = e.getSource().getDirectEntity();
            if (direct instanceof Projectile pr && vd.getLong("ororArtReflectUntil") > now) {
                reflect(vp, pr);
                e.setCanceled(true);
                return true;
            }
            if (vd.getLong("ororArtUndyingUntil") > now && e.getAmount() >= vp.getHealth()) {
                e.setCanceled(true);
                vp.setHealth(vp.getMaxHealth());
                RelicPowers.cleanse(vp);
                vp.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 100, 4));
                sl.sendParticles(ParticleTypes.END_ROD, vp.getX(), vp.getY() + 1.0, vp.getZ(), 60, 0.6, 1.0, 0.6, 0.15);
                sl.playSound(null, vp.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 1.0F, 1.2F);
                return true;
            }
        }
        if (BUSY.get()) {
            return false;
        }
        Entity src = e.getSource().getEntity();
        if (src instanceof Player p && src != v) {
            if (vd.getLong("ororArtMarkUntil") > now) {
                e.setAmount(e.getAmount() * Math.max(1.0F, vd.getFloat("ororArtMarkX")));
            }
            if (e.getSource().getDirectEntity() == p) {
                String id = idOf(p.getMainHandItem());
                Art a = id == null ? null : ALL.get(id);
                if (a != null && !a.hit.isEmpty()) {
                    run(a, a.hit, sl, p, v);
                }
                if (p.getMainHandItem().getItem() instanceof CharacterRelics.Wielded x && x.wield().kind != null) {
                    WeaponSkills.melee(e, p, v, x.wield(), sl);
                }
            } else if (e.getSource().getDirectEntity() instanceof Arrow ar && ar.getPersistentData().contains("ororRelicArrow")) {
                WeaponSkills.arrow(e, p, v, ar, sl);
            }
        }
        return false;
    }

    /** Bosses wield their own relic weapon (rendered with its 3D model); it never drops. */
    public static void equip(SupremeEntity b) {
        if (!b.getMainHandItem().isEmpty() || b.spec == null) {
            return;
        }
        net.minecraftforge.registries.RegistryObject<Item> relic = CharacterRelics.ITEMS.get(b.spec.id + "_weapon");
        if (relic != null) {
            b.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, new ItemStack(relic.get()));
            b.setDropChance(net.minecraft.world.entity.EquipmentSlot.MAINHAND, 0.0F);
        }
    }

    public static String idOf(ItemStack stack) {
        return stack.getItem() instanceof CharacterRelics.Wielded x ? x.wield().art : null;
    }

    // ------------------------------------------------------------------------------------- interpreter
    private static final class Ctx {
        ServerLevel sl;
        Player p;
        Art art;
        float base;
        int color;
        /** Slot scaling (v0.17.6): focus and charm arts hit and heal 2x, buffs one level higher, longer and wider. */
        float heal = 1.0F;
        int amp;
        float span = 1.0F;
        float reach = 1.0F;
        LivingEntity victim;
        List<LivingEntity> t = new ArrayList<>();
    }

    private static void run(Art a, List<JsonObject> program, ServerLevel sl, Player p, LivingEntity victim) {
        boolean outer = !BUSY.get();
        BUSY.set(true);
        try {
            Ctx c = new Ctx();
            c.sl = sl;
            c.p = p;
            c.art = a;
            // v0.17.4: rank 1/2 arts hit 1.5x harder (rank 3 stays at the lore-mode cap)
            c.base = a.rank >= 3 ? 1000000.0F : 3000.0F * a.rank;
            RelicSpec owner = RelicSpec.ALL.get(a.character + "_weapon");
            c.color = owner != null ? owner.color : 0xFFFFFF;
            if (a.id.endsWith("_focus") || a.id.endsWith("_charm")) {
                c.base *= 2.0F;
                c.heal = 2.0F;
                c.amp = 1;
                c.span = 1.5F;
                c.reach = 1.25F;
            } else {
                c.span = 1.25F;
            }
            c.victim = victim;
            if (victim != null) {
                c.t.add(victim);
            }
            exec(c, program);
        } finally {
            if (outer) {
                BUSY.set(false);
            }
        }
    }

    private static void exec(Ctx c, List<JsonObject> program) {
        for (JsonObject o : program) {
            try {
                op(c, o);
            } catch (RuntimeException ex) {
                warn(c.art.id + " op " + o + " failed: " + ex);
            }
        }
    }

    private static double num(JsonObject o, String k, double d) {
        return o.has(k) ? Double.parseDouble(o.get(k).getAsString()) : d;
    }

    private static String str(JsonObject o, String k, String d) {
        return o.has(k) ? o.get(k).getAsString() : d;
    }

    private static void op(Ctx c, JsonObject o) {
        String op = o.get("op").getAsString();
        Player p = c.p;
        ServerLevel sl = c.sl;
        long now = sl.getGameTime();
        switch (op) {
            // ---------- selectors
            case "area" -> c.t = sorted(near(p, p.position(), num(o, "r", 16) * c.reach), p.position(), (int) num(o, "n", 64));
            case "near" -> c.t = sorted(near(p, p.position(), num(o, "r", 24) * c.reach), p.position(), (int) num(o, "n", 1));
            case "around" -> {
                Vec3 at = c.victim != null ? c.victim.position() : p.position();
                List<LivingEntity> l = sorted(near(p, at, num(o, "r", 4) * c.reach), at, (int) num(o, "n", 16));
                if (c.victim != null && o.has("exclude")) {
                    l.remove(c.victim);
                }
                c.t = l;
            }
            case "line" -> c.t = line(p, num(o, "r", 32) * c.reach, num(o, "w", 2.5));
            case "cone" -> c.t = cone(p, num(o, "r", 12) * c.reach, num(o, "a", 90));
            case "chain" -> c.t = chain(p, c.victim, (int) num(o, "n", 6), num(o, "r", 10) * c.reach);
            case "allies" -> c.t = allies(p, num(o, "r", 16) * c.reach);
            case "self" -> {
                c.t = new ArrayList<>();
                c.t.add(p);
            }
            case "victim" -> {
                c.t = new ArrayList<>();
                if (c.victim != null) {
                    c.t.add(c.victim);
                }
            }
            // ---------- harm
            case "dmg" -> {
                float amount = (float) (c.base * num(o, "m", 1.0));
                for (LivingEntity e : c.t) {
                    if (e == p) {
                        continue;
                    }
                    if (e instanceof SupremeEntity b) {
                        RelicDrops.fracture(b, p, amount);
                    }
                    e.invulnerableTime = 0;
                    // v0.17.10: magic damage is the player's (indirectMagic), so kills give experience and player drops
                    e.hurt(o.has("magic") ? p.damageSources().indirectMagic(p, p) : p.damageSources().playerAttack(p), amount);
                    impact(c, e);
                }
            }
            case "execute" -> {
                double pct = num(o, "pct", 0.3);
                for (LivingEntity e : c.t) {
                    if (e == p || !e.isAlive()) {
                        continue;
                    }
                    if (e instanceof SupremeEntity b) {
                        RelicDrops.fracture(b, p, c.base * 2.0F);
                        e.invulnerableTime = 0;
                        e.hurt(p.damageSources().playerAttack(p), c.base * 2.0F);
                    } else if (e.getHealth() <= e.getMaxHealth() * pct || e.getMaxHealth() <= c.base) {
                        e.invulnerableTime = 0;
                        e.hurt(p.damageSources().genericKill(), Float.MAX_VALUE);
                    }
                }
            }
            case "stun" -> c.t.forEach(e -> {
                if (e != p) {
                    Abilities.stun(e, (int) (num(o, "t", 60) * c.span));
                }
            });
            case "eff" -> {
                MobEffect h = effect(str(o, "e", "weakness"));
                for (LivingEntity e : c.t) {
                    if (e != p || o.has("self")) {
                        e.addEffect(new MobEffectInstance(h, (int) (num(o, "t", 100) * c.span), (int) num(o, "a", 0) + c.amp));
                    }
                }
            }
            case "burn" -> c.t.forEach(e -> {
                if (e != p) {
                    e.setSecondsOnFire((int) ((float) num(o, "s", 8)));
                }
            });
            case "freeze" -> c.t.forEach(e -> {
                if (e != p) {
                    e.setTicksFrozen((int) num(o, "t", 300));
                    Abilities.stun(e, (int) num(o, "t", 300) / 3);
                }
            });
            case "mark" -> c.t.forEach(e -> {
                if (e != p) {
                    e.getPersistentData().putLong("ororArtMarkUntil", now + (long) num(o, "t", 200));
                    e.getPersistentData().putFloat("ororArtMarkX", (float) num(o, "x", 2.0));
                    e.setGlowingTag(true);
                }
            });
            case "strip" -> {
                for (LivingEntity e : c.t) {
                    if (e == p) {
                        continue;
                    }
                    for (MobEffectInstance m : new ArrayList<>(e.getActiveEffects())) {
                        if (m.getEffect().isBeneficial()) {
                            e.removeEffect(m.getEffect());
                            if (o.has("steal")) {
                                p.addEffect(new MobEffectInstance(m.getEffect(), m.getDuration(), m.getAmplifier()));
                            }
                        }
                    }
                }
            }
            case "disarm" -> c.t.forEach(e -> {
                if (e instanceof Mob m && !(e instanceof SupremeEntity)) {
                    m.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, ItemStack.EMPTY);
                }
            });
            case "transmute" -> {
                for (LivingEntity e : new ArrayList<>(c.t)) {
                    if (e == p || e instanceof Player || e instanceof SupremeEntity || !e.isAlive() || e.getMaxHealth() > 300.0F) {
                        continue;       // bosses such as the dragon or the wither are never deleted
                    }
                    Mob into = (Mob) (sl.random.nextInt(2) == 0 ? EntityType.PIG.create(sl) : EntityType.COW.create(sl));
                    if (into != null) {
                        into.moveTo(e.getX(), e.getY(), e.getZ(), e.getYRot(), 0.0F);
                        sl.addFreshEntity(into);
                    }
                    sl.sendParticles(ParticleTypes.WITCH, e.getX(), e.getY() + 0.8, e.getZ(), 30, 0.5, 0.8, 0.5, 0.1);
                    e.discard();
                }
            }
            case "lightning" -> {
                for (LivingEntity e : c.t) {
                    if (e == p) {
                        continue;
                    }
                    LightningBolt bolt = (LightningBolt) EntityType.LIGHTNING_BOLT.create(sl);
                    if (bolt != null) {
                        bolt.setVisualOnly(true);
                        bolt.setPos(e.position());
                        sl.addFreshEntity(bolt);
                    }
                }
            }
            case "arrows" -> {
                int n = (int) num(o, "n", 8);
                for (LivingEntity e : c.t) {
                    if (e == p) {
                        continue;
                    }
                    for (int i = 0; i < n; i++) {
                        Arrow ar = (Arrow) EntityType.ARROW.create(sl);
                        if (ar == null) {
                            continue;
                        }
                        ar.moveTo(e.getX() + (sl.random.nextDouble() - 0.5) * 3.0, e.getY() + 8.0 + i * 0.6, e.getZ() + (sl.random.nextDouble() - 0.5) * 3.0);
                        ar.setDeltaMovement(0.0, -2.6, 0.0);
                        ar.setOwner(p);
                        ar.setBaseDamage(num(o, "d", 40));
                        ar.pickup = AbstractArrow.Pickup.DISALLOWED;
                        sl.addFreshEntity(ar);
                    }
                }
            }
            // ---------- motion
            case "knock" -> c.t.forEach(e -> {
                if (e != p) {
                    Vec3 d = e.position().subtract(p.position());
                    push(e, (d.lengthSqr() < 1.0E-4 ? p.getLookAngle() : d.normalize()).scale(num(o, "f", 2.0)).add(0.0, 0.45, 0.0));
                }
            });
            case "pull" -> c.t.forEach(e -> {
                if (e != p) {
                    Vec3 d = p.position().subtract(e.position());
                    push(e, (d.lengthSqr() < 1.0E-4 ? Vec3.ZERO : d.normalize()).scale(num(o, "f", 1.5)).add(0.0, 0.3, 0.0));
                }
            });
            case "launch" -> c.t.forEach(e -> {
                if (e != p) {
                    push(e, new Vec3(0.0, num(o, "f", 1.6), 0.0));
                }
            });
            case "slam" -> c.t.forEach(e -> {
                if (e != p) {
                    push(e, new Vec3(0.0, -num(o, "f", 3.0), 0.0));
                }
            });
            case "blink" -> blink(p, p.position().add(flat(p.getLookAngle()).scale(num(o, "d", 10))));
            case "back" -> blink(p, p.position().add(flat(p.getLookAngle()).scale(-num(o, "d", 6))));
            case "behind" -> {
                if (!c.t.isEmpty() && c.t.get(0) != p) {
                    LivingEntity e = c.t.get(0);
                    blink(p, e.position().add(flat(e.position().subtract(p.position())).scale(1.6)));
                }
            }
            case "swap" -> {
                if (!c.t.isEmpty() && c.t.get(0) != p) {
                    LivingEntity e = c.t.get(0);
                    Vec3 a = p.position();
                    Vec3 b = e.position();
                    p.teleportTo(b.x, b.y, b.z);
                    e.teleportTo(a.x, a.y, a.z);
                }
            }
            case "dash" -> push(p, p.getLookAngle().scale(num(o, "f", 2.4)).add(0.0, 0.2, 0.0));
            case "leap" -> push(p, new Vec3(0.0, num(o, "f", 1.4), 0.0).add(flat(p.getLookAngle()).scale(0.6)));
            // ---------- self / allies
            case "heal" -> {
                for (LivingEntity e : targetsOrSelf(c, o)) {
                    e.heal((float) num(o, "v", 20) * c.heal);
                }
            }
            case "healpct" -> {
                for (LivingEntity e : targetsOrSelf(c, o)) {
                    e.heal((float) (e.getMaxHealth() * Math.min(1.0, num(o, "v", 1.0) * c.heal)));
                }
            }
            case "buff" -> {
                MobEffect h = effect(str(o, "e", "strength"));
                for (LivingEntity e : targetsOrSelf(c, o)) {
                    e.addEffect(new MobEffectInstance(h, (int) (num(o, "t", 200) * c.span), (int) num(o, "a", 0) + c.amp));
                }
            }
            case "cleanse" -> targetsOrSelf(c, o).forEach(RelicPowers::cleanse);
            case "guard" -> window(targetsOrSelf(c, o), "ororArtGuardUntil", now + (long) num(o, "t", 60));
            case "undying" -> window(targetsOrSelf(c, o), "ororArtUndyingUntil", now + (long) num(o, "t", 200));
            case "adapt" -> window(targetsOrSelf(c, o), "ororRelicAdaptUntil", now + (long) num(o, "t", 200));
            case "reflect" -> {
                p.getPersistentData().putLong("ororArtReflectUntil", now + (long) num(o, "t", 40));
                for (Projectile pr : projectiles(p, num(o, "r", 8))) {
                    reflect(p, pr);
                }
            }
            case "erase" -> {
                for (Projectile pr : projectiles(p, num(o, "r", 16))) {
                    sl.sendParticles(ParticleTypes.POOF, pr.position().x, pr.position().y, pr.position().z, 3, 0.1, 0.1, 0.1, 0.02);
                    pr.discard();
                }
            }
            case "food" -> p.getFoodData().setFoodLevel(20);
            case "repair" -> repair(p, (int) num(o, "v", 64));
            case "xp" -> p.giveExperiencePoints((int) num(o, "v", 20));
            case "give" -> p.getInventory().add(new ItemStack(item(str(o, "item", "gold")), (int) num(o, "n", 1)));
            case "summon" -> summon(p, (int) num(o, "n", 2), str(o, "k", "wolf").equals("wolf"));
            case "weather" -> {
                String w = str(o, "w", "clear");
                if (w.equals("clear")) {
                    sl.setWeatherParameters(12000, 0, false, false);
                } else if (w.equals("rain")) {
                    sl.setWeatherParameters(0, 6000, true, false);
                } else {
                    sl.setWeatherParameters(0, 6000, true, true);
                }
            }
            case "time" -> sl.setDayTime((long) num(o, "v", 1000));
            case "snapshot" -> snapshot(p, now);
            case "rewind" -> rewind(p, sl);
            case "cycle" -> {
                JsonArray steps = o.getAsJsonArray("steps");
                String key = "ororArtCycle_" + c.art.id;
                int i = p.getPersistentData().getInt(key);
                int n = 0;
                for (Iterator<JsonElement> it = steps.iterator(); it.hasNext(); it.next()) {
                    n++;
                }
                if (n > 0) {
                    JsonElement step = steps.get(i % n);
                    p.getPersistentData().putInt(key, (i + 1) % n);
                    List<JsonObject> sub = new ArrayList<>();
                    for (Iterator<JsonElement> it = step.getAsJsonObject().getAsJsonArray("ops").iterator(); it.hasNext(); ) {
                        sub.add(it.next().getAsJsonObject());
                    }
                    if (step.getAsJsonObject().has("say")) {
                        p.displayClientMessage(Component.translatable(step.getAsJsonObject().get("say").getAsString()), true);
                    }
                    exec(c, sub);
                }
            }
            case "chance" -> {
                if (sl.random.nextDouble() < num(o, "p", 0.5)) {
                    exec(c, ops(o, "ops"));
                } else if (o.has("else")) {
                    exec(c, ops(o, "else"));
                }
            }
            case "each" -> {
                List<LivingEntity> all = c.t;
                for (LivingEntity e : new ArrayList<>(all)) {
                    c.t = new ArrayList<>();
                    c.t.add(e);
                    List<JsonObject> pick = ops(o, "ops");
                    if (!pick.isEmpty()) {
                        exec(c, List.of(pick.get(sl.random.nextInt(pick.size()))));
                    }
                }
                c.t = all;
            }
            case "low" -> {
                if (p.getHealth() <= p.getMaxHealth() * num(o, "pct", 0.35)) {
                    exec(c, ops(o, "ops"));
                }
            }
            // ---------- presentation
            case "fx" -> fx(c, o);
            case "sound" -> sl.playSound(null, p.blockPosition(), sound(str(o, "s", "chime")), SoundSource.PLAYERS, (float) num(o, "v", 1.0), (float) num(o, "pi", 1.0));
            case "say" -> p.displayClientMessage(Component.translatable(str(o, "k", "")), true);
            default -> warn("unknown op " + op + " in " + c.art.id);
        }
    }

    private static final java.util.Set<String> WARNED = java.util.concurrent.ConcurrentHashMap.newKeySet();

    private static void warn(String msg) {
        if (WARNED.size() < 64 && WARNED.add(msg)) {
            System.err.println("[oror_supreme_bosses] relic art: " + msg);
        }
    }

    // ------------------------------------------------------------------------------------- selectors
    private static List<LivingEntity> near(Player p, Vec3 at, double r) {
        return p.level().getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(r), e -> RelicPowers.enemy(p, e) && e.position().distanceTo(at) <= r);
    }

    private static List<LivingEntity> sorted(List<LivingEntity> list, Vec3 at, int n) {
        List<LivingEntity> out = new ArrayList<>(list);
        out.sort(Comparator.comparingDouble(e -> e.position().distanceToSqr(at)));
        return out.size() > n ? new ArrayList<>(out.subList(0, n)) : out;
    }

    private static List<LivingEntity> line(Player p, double r, double w) {
        Vec3 a = p.getEyePosition();
        Vec3 d = p.getLookAngle().normalize();
        Vec3 b = a.add(d.scale(r));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : p.level().getEntitiesOfClass(LivingEntity.class, new AABB(a, b).inflate(w + 1.0), e -> RelicPowers.enemy(p, e))) {
            Vec3 q = e.position().add(0.0, e.getBbWidth() * 0.5, 0.0).subtract(a);
            double t = Math.max(0.0, Math.min(r, q.dot(d)));
            if (q.subtract(d.scale(t)).length() <= w + e.getBbWidth() * 0.5) {
                out.add(e);
            }
        }
        return sorted(out, p.position(), 64);
    }

    private static List<LivingEntity> cone(Player p, double r, double deg) {
        Vec3 d = flat(p.getLookAngle());
        double cos = Math.cos(Math.toRadians(deg * 0.5));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : near(p, p.position(), r)) {
            Vec3 q = flat(e.position().subtract(p.position()));
            if (q.lengthSqr() < 1.0 || q.normalize().dot(d) >= cos) {
                out.add(e);
            }
        }
        return sorted(out, p.position(), 64);
    }

    private static List<LivingEntity> chain(Player p, LivingEntity start, int n, double r) {
        List<LivingEntity> out = new ArrayList<>();
        LivingEntity cur = start;
        if (cur == null) {
            List<LivingEntity> first = sorted(near(p, p.position(), r * 2.0), p.position(), 1);
            if (first.isEmpty()) {
                return out;
            }
            cur = first.get(0);
        }
        out.add(cur);
        while (out.size() < n) {
            LivingEntity from = cur;
            LivingEntity next = null;
            double best = Double.MAX_VALUE;
            for (LivingEntity e : near(p, from.position(), r)) {
                double dd = e.position().distanceToSqr(from.position());
                if (!out.contains(e) && dd < best) {
                    best = dd;
                    next = e;
                }
            }
            if (next == null) {
                break;
            }
            if (p.level() instanceof ServerLevel sl) {
                Vec3 a = from.position().add(0.0, 1.0, 0.0);
                Vec3 b = next.position().add(0.0, 1.0, 0.0);
                for (int i = 0; i <= 8; i++) {
                    Vec3 q = a.add(b.subtract(a).scale(i / 8.0));
                    sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, q.x, q.y, q.z, 2, 0.05, 0.05, 0.05, 0.0);
                }
            }
            out.add(next);
            cur = next;
        }
        return out;
    }

    private static List<LivingEntity> allies(Player p, double r) {
        return p.level().getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(r),
            v -> v instanceof Player q && !RelicPowers.enemy(p, q)
                || v instanceof SupremeEntity b && p.getUUID().equals(b.owner)
                || v.getPersistentData().hasUUID("ororRelicOwner") && p.getUUID().equals(v.getPersistentData().getUUID("ororRelicOwner")));
    }

    private static List<LivingEntity> targetsOrSelf(Ctx c, JsonObject o) {
        if (o.has("to")) {
            return c.t;
        }
        List<LivingEntity> l = new ArrayList<>();
        l.add(c.p);
        return l;
    }

    // ------------------------------------------------------------------------------------- helpers
    private static Vec3 flat(Vec3 v) {
        Vec3 f = new Vec3(v.x, 0.0, v.z);
        return f.lengthSqr() < 1.0E-6 ? new Vec3(0.0, 0.0, 1.0) : f.normalize();
    }

    private static void push(LivingEntity e, Vec3 v) {
        e.setDeltaMovement(v);
        e.hurtMarked = true;
    }

    private static void window(List<LivingEntity> l, String key, long until) {
        for (LivingEntity e : l) {
            e.getPersistentData().putLong(key, Math.max(until, e.getPersistentData().getLong(key)));
        }
    }

    private static void blink(Player p, Vec3 at) {
        Level l = p.level();
        Vec3 from = p.position();
        for (int i = 0; i < 12; i++) {
            Vec3 q = at.add(from.subtract(at).scale(i / 12.0));
            if (l.hasChunkAt(BlockPos.containing(q)) && l.getWorldBorder().isWithinBounds(BlockPos.containing(q))
                && l.noCollision(p, p.getBoundingBox().move(q.subtract(p.position())))) {
                if (l instanceof ServerLevel sl) {
                    sl.sendParticles(ParticleTypes.REVERSE_PORTAL, from.x, from.y + 1.0, from.z, 30, 0.3, 0.6, 0.3, 0.05);
                    sl.playSound(null, p.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 0.8F, 1.2F);
                }
                p.teleportTo(q.x, q.y, q.z);
                p.fallDistance = 0.0F;
                return;
            }
        }
    }

    private static List<Projectile> projectiles(Player p, double r) {
        return p.level().getEntitiesOfClass(Projectile.class, p.getBoundingBox().inflate(r),
            x -> x.getOwner() != p && (!(x.getOwner() instanceof LivingEntity owner) || RelicPowers.enemy(p, owner)));
    }

    private static void reflect(Player p, Projectile pr) {
        Vec3 v = pr.getDeltaMovement();
        Entity owner = pr.getOwner();
        Vec3 dir = owner instanceof LivingEntity le ? le.position().add(0.0, 1.0, 0.0).subtract(pr.position()).normalize() : v.scale(-1.0).normalize();
        pr.setOwner(p);
        pr.setDeltaMovement(dir.scale(Math.max(1.2, v.length() * 1.5)));
        pr.hasImpulse = true;
    }

    private static void repair(Player p, int amount) {
        for (ItemStack s : p.getInventory().items) {
            if (s.isDamaged()) {
                s.setDamageValue(Math.max(0, s.getDamageValue() - amount));
            }
        }
        for (ItemStack s : p.getAllSlots()) {
            if (s.isDamaged()) {
                s.setDamageValue(Math.max(0, s.getDamageValue() - amount));
            }
        }
    }

    private static void summon(Player p, int count, boolean beast) {
        if (!(p.level() instanceof ServerLevel sl)) {
            return;
        }
        int n = SummonBudget.remaining(sl, p.getUUID(), 6, count);
        for (int i = 0; i < n; i++) {
            Mob e = beast ? (Mob) EntityType.WOLF.create(sl) : (Mob) EntityType.IRON_GOLEM.create(sl);
            if (e == null) {
                continue;
            }
            Vec3 at = p.position().add(i * 2 - 3, 0.0, 3.0);
            e.moveTo(at.x, at.y, at.z, 0.0F, 0.0F);
            if (sl.hasChunkAt(e.blockPosition()) && sl.noCollision(e)) {
                e.setPersistenceRequired();
                if (e instanceof IronGolem g) {
                    g.setPlayerCreated(true);
                }
                if (e instanceof Wolf wolf) {
                    wolf.setTame(true);
                    wolf.setOwnerUUID(p.getUUID());
                }
                CompoundTag tag = e.getPersistentData();
                tag.putUUID("ororRelicOwner", p.getUUID());
                tag.putLong("ororRelicExpire", sl.getGameTime() + 1200L);
                sl.addFreshEntity(e);
            }
        }
    }

    private static void snapshot(Player p, long now) {
        CompoundTag d = p.getPersistentData();
        int i = (int) ((now / 20L) % 6L);
        d.putFloat("ororArtSnapHP" + i, p.getHealth());
        d.putLong("ororArtSnapPos" + i, p.blockPosition().asLong());
        d.putLong("ororArtSnapAt" + i, now);
    }

    private static void rewind(Player p, ServerLevel sl) {
        CompoundTag d = p.getPersistentData();
        long now = sl.getGameTime();
        int best = -1;
        long oldest = Long.MAX_VALUE;
        for (int i = 0; i < 6; i++) {
            long at = d.getLong("ororArtSnapAt" + i);
            if (at > 0 && now - at <= 140 && at < oldest) {
                oldest = at;
                best = i;
            }
        }
        RelicPowers.cleanse(p);
        if (best < 0) {
            p.heal(p.getMaxHealth() * 0.5F);
            return;
        }
        p.setHealth(Math.max(p.getHealth(), Math.min(p.getMaxHealth(), d.getFloat("ororArtSnapHP" + best))));
        BlockPos pos = BlockPos.of(d.getLong("ororArtSnapPos" + best));
        blink(p, Vec3.atBottomCenterOf(pos));
    }

    private static void fx(Ctx c, JsonObject o) {
        ParticleOptions part = particle(str(o, "p", "end_rod"));
        int n = (int) num(o, "n", 24);
        double s = num(o, "s", 0.6);
        String at = str(o, "at", "self");
        ServerLevel sl = c.sl;
        Player p = c.p;
        switch (at) {
            case "t" -> {
                for (LivingEntity e : c.t) {
                    sl.sendParticles(part, e.getX(), e.getY() + 1.0, e.getZ(), n, s, s, s, num(o, "v", 0.05));
                }
            }
            case "line" -> {
                Vec3 a = p.getEyePosition();
                Vec3 d = p.getLookAngle().normalize();
                double r = num(o, "r", 24);
                for (int i = 0; i < n; i++) {
                    Vec3 q = a.add(d.scale(r * i / Math.max(1, n - 1)));
                    sl.sendParticles(part, q.x, q.y, q.z, 1, s * 0.2, s * 0.2, s * 0.2, 0.0);
                }
            }
            case "ring" -> {
                double r = num(o, "r", 4);
                for (int i = 0; i < n; i++) {
                    double a = Math.PI * 2.0 * i / n;
                    sl.sendParticles(part, p.getX() + Math.cos(a) * r, p.getY() + num(o, "y", 0.3), p.getZ() + Math.sin(a) * r, 1, 0.0, 0.0, 0.0, num(o, "v", 0.0));
                }
            }
            case "pillar" -> {
                for (LivingEntity e : c.t) {
                    for (int i = 0; i < 10; i++) {
                        sl.sendParticles(part, e.getX(), e.getY() + i * 0.5, e.getZ(), Math.max(1, n / 10), 0.2, 0.1, 0.2, 0.02);
                    }
                }
            }
            default -> sl.sendParticles(part, p.getX(), p.getY() + 1.0, p.getZ(), n, s, s, s, num(o, "v", 0.05));
        }
    }

    // ------------------------------------------------------------------------------------- vocab
    private static MobEffect effect(String n) {
        return switch (n) {
            case "slow" -> MobEffects.MOVEMENT_SLOWDOWN;
            case "speed" -> MobEffects.MOVEMENT_SPEED;
            case "haste" -> MobEffects.DIG_SPEED;
            case "fatigue" -> MobEffects.DIG_SLOWDOWN;
            case "strength" -> MobEffects.DAMAGE_BOOST;
            case "resist" -> MobEffects.DAMAGE_RESISTANCE;
            case "fireres" -> MobEffects.FIRE_RESISTANCE;
            case "regen" -> MobEffects.REGENERATION;
            case "absorb" -> MobEffects.ABSORPTION;
            case "luck" -> MobEffects.LUCK;
            case "jump" -> MobEffects.JUMP;
            case "water" -> MobEffects.WATER_BREATHING;
            case "dolphin" -> MobEffects.DOLPHINS_GRACE;
            case "invis" -> MobEffects.INVISIBILITY;
            case "night" -> MobEffects.NIGHT_VISION;
            case "health" -> MobEffects.HEALTH_BOOST;
            case "saturation" -> MobEffects.SATURATION;
            case "slowfall" -> MobEffects.SLOW_FALLING;
            case "levitate" -> MobEffects.LEVITATION;
            case "glow" -> MobEffects.GLOWING;
            case "wither" -> MobEffects.WITHER;
            case "poison" -> MobEffects.POISON;
            case "blind" -> MobEffects.BLINDNESS;
            case "dark" -> MobEffects.DARKNESS;
            case "nausea" -> MobEffects.CONFUSION;
            case "hunger" -> MobEffects.HUNGER;
            default -> MobEffects.WEAKNESS;
        };
    }

    private static ParticleOptions particle(String n) {
        return switch (n) {
            case "flame" -> ParticleTypes.FLAME;
            case "soulfire" -> ParticleTypes.SOUL_FIRE_FLAME;
            case "soul" -> ParticleTypes.SOUL;
            case "spark" -> ParticleTypes.ELECTRIC_SPARK;
            case "crit" -> ParticleTypes.CRIT;
            case "enchant" -> ParticleTypes.ENCHANT;
            case "portal" -> ParticleTypes.PORTAL;
            case "rportal" -> ParticleTypes.REVERSE_PORTAL;
            case "dragon" -> ParticleTypes.DRAGON_BREATH;
            case "witch" -> ParticleTypes.WITCH;
            case "happy" -> ParticleTypes.HAPPY_VILLAGER;
            case "bubble" -> ParticleTypes.BUBBLE;
            case "splash" -> ParticleTypes.SPLASH;
            case "smoke" -> ParticleTypes.SMOKE;
            case "bigsmoke" -> ParticleTypes.LARGE_SMOKE;
            case "explosion" -> ParticleTypes.EXPLOSION;
            case "blast" -> ParticleTypes.EXPLOSION_EMITTER;
            case "sonic" -> ParticleTypes.SONIC_BOOM;
            case "snow" -> ParticleTypes.SNOWFLAKE;
            case "heart" -> ParticleTypes.HEART;
            case "firework" -> ParticleTypes.FIREWORK;
            case "sculk" -> ParticleTypes.SCULK_SOUL;
            case "lava" -> ParticleTypes.LAVA;
            case "poof" -> ParticleTypes.POOF;
            case "ash" -> ParticleTypes.WHITE_ASH;
            case "angry" -> ParticleTypes.ANGRY_VILLAGER;
            case "compost" -> ParticleTypes.COMPOSTER;
            case "wax" -> ParticleTypes.WAX_ON;
            default -> ParticleTypes.END_ROD;
        };
    }

    private static SoundEvent sound(String n) {
        return switch (n) {
            case "totem" -> SoundEvents.TOTEM_USE;
            case "stone" -> SoundEvents.STONE_BREAK;
            case "teleport" -> SoundEvents.ENDERMAN_TELEPORT;
            case "glass" -> SoundEvents.GLASS_BREAK;
            case "mirror" -> SoundEvents.ILLUSIONER_MIRROR_MOVE;
            case "spell" -> SoundEvents.EVOKER_CAST_SPELL;
            case "summon" -> SoundEvents.EVOKER_PREPARE_SUMMON;
            case "blast" -> SoundEvents.FIREWORK_ROCKET_BLAST;
            case "wither" -> SoundEvents.WITHER_SHOOT;
            case "sonic" -> SoundEvents.WARDEN_SONIC_CHARGE;
            case "chain" -> SoundEvents.CHAIN_BREAK;
            case "anvil" -> SoundEvents.ANVIL_LAND;
            case "roar" -> SoundEvents.ENDER_DRAGON_GROWL;
            case "smith" -> SoundEvents.VILLAGER_WORK_TOOLSMITH;
            default -> SoundEvents.AMETHYST_BLOCK_CHIME;
        };
    }

    private static Item item(String n) {
        return switch (n) {
            case "diamond" -> Items.DIAMOND;
            case "emerald" -> Items.EMERALD;
            case "netherite" -> Items.NETHERITE_INGOT;
            case "iron" -> Items.IRON_INGOT;
            case "redstone" -> Items.REDSTONE;
            case "bread" -> Items.BREAD;
            case "arrow" -> Items.ARROW;
            case "coal" -> Items.COAL;
            default -> Items.GOLD_INGOT;
        };
    }

    // ------------------------------------------------------------------------------------- weapon shots
    /**
     * Right-click attack of the shooting weapon kinds, stopped by walls. A catalyst fires a bolt at the first enemy on
     * the line of sight and every fourth bolt is a great bolt that bursts; a gatling heats up as it keeps firing
     * (more damage, then burning rounds); a cannon shell bursts and throws enemies up.
     */
    public static void shot(Player p, CharacterRelics.Wield w) {
        if (!(p.level() instanceof ServerLevel sl)) {
            return;
        }
        String mode = w.kind.mode;
        boolean shell = mode.equals("shell");
        boolean gatling = mode.equals("gatling");
        long now = sl.getGameTime();
        CompoundTag d = p.getPersistentData();
        float damage = w.damage * w.kind.shot;
        int color = w.spec != null ? w.spec.color : 0xFFFFFF;
        net.minecraft.core.particles.DustParticleOptions dust = RelicEffects.dust(color, shell ? 2.0F : 1.2F);
        boolean great = false;
        int heat = 0;
        if (gatling) {
            heat = now - d.getLong("ororHeatAt") <= 8L ? Math.min(20, d.getInt("ororHeat") + 1) : 0;
            d.putInt("ororHeat", heat);
            d.putLong("ororHeatAt", now);
            damage *= 1.0F + heat * 0.04F;
        } else if (!shell) {
            int n = d.getInt("ororBolts") + 1;
            d.putInt("ororBolts", n);
            great = n % 4 == 0;
            if (great) {
                damage *= 2.5F;
            }
        }
        double range = shell ? 48.0 : (gatling ? 32.0 : 40.0);
        Vec3 a = p.getEyePosition();
        Vec3 dir = p.getLookAngle().normalize();
        if (shell) {
            // v0.17.11: a shell flies (RelicShells) instead of bursting at once wherever the crosshair points
            Vec3 side = new Vec3(-dir.z, 0.0, dir.x);
            side = side.lengthSqr() < 1.0E-6 ? new Vec3(1.0, 0.0, 0.0) : side.normalize();
            Vec3 muzzle = a.add(dir.scale(0.9)).add(side.scale(0.4)).add(0.0, -0.4, 0.0);
            RelicShells.fire(p, sl, muzzle, dir.scale(2.4).add(0.0, 0.05, 0.0), damage, w.rank >= 3 ? 5.0 : 4.0, color, w.rank >= 3);
            return;
        }
        if (gatling) {
            double j = 0.02 + heat * 0.002;
            dir = dir.add((sl.random.nextDouble() - 0.5) * j, (sl.random.nextDouble() - 0.5) * j, (sl.random.nextDouble() - 0.5) * j).normalize();
        }
        net.minecraft.world.phys.BlockHitResult wall = sl.clip(new net.minecraft.world.level.ClipContext(
            a, a.add(dir.scale(range)), net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, p));
        if (wall.getType() != net.minecraft.world.phys.HitResult.Type.MISS) {
            range = wall.getLocation().distanceTo(a);
        }
        Vec3 far = a.add(dir.scale(range));
        LivingEntity first = null;
        double best = range;
        for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(a, far).inflate(1.5), e -> RelicPowers.enemy(p, e))) {
            java.util.Optional<Vec3> hit = e.getBoundingBox().inflate(0.3).clip(a, far);
            if (hit.isPresent() && hit.get().distanceTo(a) < best) {
                best = hit.get().distanceTo(a);
                first = e;
            }
        }
        Vec3 end = a.add(dir.scale(best));
        // v0.17.10: the trail starts at the weapon (a staff's head, a gun's muzzle) at the right hand, not inside the eyes
        Vec3 side = new Vec3(-dir.z, 0.0, dir.x);
        side = side.lengthSqr() < 1.0E-6 ? new Vec3(1.0, 0.0, 0.0) : side.normalize();
        Vec3 muzzle = a.add(dir.scale(0.8)).add(side.scale(0.4)).add(0.0, mode.equals("bolt") ? 0.0 : -0.4, 0.0);
        Vec3 path = end.subtract(muzzle);
        sl.sendParticles(dust, muzzle.x, muzzle.y, muzzle.z, 4, 0.06, 0.06, 0.06, 0.0);
        int n = (int) Math.min(80.0, path.length() * (gatling ? 1.5 : 2.5));
        for (int i = 1; i <= n; i++) {
            Vec3 q = muzzle.add(path.scale((double) i / n));
            sl.sendParticles(dust, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
            if (i % (gatling ? 3 : 2) == 0) {
                sl.sendParticles(shell ? ParticleTypes.LARGE_SMOKE : (gatling ? ParticleTypes.CRIT : ParticleTypes.END_ROD), q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
        if (shell) {
            double r = w.rank >= 3 ? 5.0 : 4.0;
            for (LivingEntity e : near(p, end, r)) {
                strike(p, e, damage, false);
                if (!(e instanceof SupremeEntity)) {
                    e.setDeltaMovement(e.getDeltaMovement().add(e.position().subtract(end).normalize().scale(0.8).add(0.0, 0.7, 0.0)));
                    e.hurtMarked = true;
                }
            }
            sl.sendParticles(w.rank >= 3 ? ParticleTypes.EXPLOSION_EMITTER : ParticleTypes.EXPLOSION, end.x, end.y, end.z, w.rank >= 3 ? 1 : 5, 0.8, 0.8, 0.8, 0.0);
            RelicEffects.shock(sl, end, 40, ParticleTypes.CLOUD, 0.5);
            RelicEffects.burst(sl, end, dust, 30, r * 0.4, 0.0);
            RelicEffects.burst(sl, end, ParticleTypes.LAVA, 8, 0.6, 0.0);
            sl.playSound(null, p.blockPosition(), SoundEvents.WITHER_SHOOT, SoundSource.PLAYERS, 0.8F, 1.3F);
            sl.playSound(null, BlockPos.containing(end), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 2.0F, 0.5F);
        } else if (gatling) {
            if (first != null) {
                strike(p, first, damage, false);
                if (heat >= 20) {
                    first.setSecondsOnFire((int) (3.0F));
                }
                sl.sendParticles(ParticleTypes.CRIT, end.x, end.y, end.z, 6, 0.15, 0.15, 0.15, 0.2);
            }
            sl.sendParticles(heat >= 20 ? ParticleTypes.FLAME : ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 2, 0.05, 0.05, 0.05, 0.02);
            sl.playSound(null, p.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 0.45F, 1.6F + heat * 0.02F);
        } else if (great) {
            for (LivingEntity e : near(p, end, 3.0)) {
                strike(p, e, damage, true);
            }
            RelicEffects.burst(sl, end, dust, 40, 1.0, 0.0);
            RelicEffects.burst(sl, end, ParticleTypes.END_ROD, 24, 0.2, 0.25);
            RelicEffects.shock(sl, end, 24, ParticleTypes.END_ROD, 0.3);
            sl.playSound(null, BlockPos.containing(end), SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS, 1.0F, 1.6F);
            sl.playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.2F, 0.8F);
            p.displayClientMessage(Component.translatable("weapon_skill.oror_supreme_bosses.magic").withStyle(net.minecraft.ChatFormatting.GOLD), true);
        } else {
            if (first != null) {
                strike(p, first, damage, true);
                sl.sendParticles(ParticleTypes.ENCHANT, end.x, end.y, end.z, 12, 0.2, 0.2, 0.2, 0.4);
                sl.sendParticles(dust, end.x, end.y, end.z, 10, 0.25, 0.25, 0.25, 0.0);
            }
            sl.playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.4F);
        }
    }

    /** Damage from weapon skills and shots: it never re-triggers on-hit arts or weapon skills. */
    static void strike(Player p, LivingEntity e, float amount, boolean magic) {
        boolean outer = !BUSY.get();
        BUSY.set(true);
        try {
            if (e instanceof SupremeEntity b) {
                RelicDrops.fracture(b, p, amount);
            }
            e.invulnerableTime = 0;
            // a plain magic() source has no attacker: bolt kills gave no experience or player drops and nothing fought back
            e.hurt(magic ? p.damageSources().indirectMagic(p, p) : p.damageSources().playerAttack(p), amount);
        } finally {
            if (outer) {
                BUSY.set(false);
            }
        }
    }

    static void reflectProjectile(Player p, Projectile pr) {
        reflect(p, pr);
    }

    /** Where an art's damage lands: a burst in the character's colour, a shock flash for rank 3 arts. */
    private static void impact(Ctx c, LivingEntity e) {
        Vec3 at = e.position().add(0.0, e.getBbHeight() * 0.5, 0.0);
        c.sl.sendParticles(RelicEffects.dust(c.color, 1.6F), at.x, at.y, at.z, 14, 0.35, 0.45, 0.35, 0.0);
        c.sl.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 8, 0.2, 0.3, 0.2, 0.35);
        if (c.art.rank >= 3) {
            c.sl.sendParticles(ParticleTypes.SONIC_BOOM, at.x, at.y, at.z, 1, 0.0, 0.0, 0.0, 0.0);
        }
    }

    public static void tooltip(String id, List<Component> lines) {
        String k = "relic_art.oror_supreme_bosses." + id;
        lines.add(Component.translatable(k + ".name").withStyle(net.minecraft.ChatFormatting.GOLD));
        lines.add(Component.translatable(k + ".desc").withStyle(net.minecraft.ChatFormatting.GRAY));
        Art a = ALL.get(id);
        if (a != null && !a.passive.isEmpty()) {
            lines.add(Component.translatable(k + ".passive").withStyle(net.minecraft.ChatFormatting.AQUA));
        }
        if (a != null && !a.hit.isEmpty()) {
            lines.add(Component.translatable(k + ".hit").withStyle(net.minecraft.ChatFormatting.LIGHT_PURPLE));
        }
    }
}
