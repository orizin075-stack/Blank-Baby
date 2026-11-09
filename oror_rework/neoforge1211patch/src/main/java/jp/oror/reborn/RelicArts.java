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
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.DustParticleOptions;
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
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.animal.Wolf;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.AbstractArrow.Pickup;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ClipContext.Block;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.HitResult.Type;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.registries.DeferredItem;

public final class RelicArts {
   public static final Map<String, RelicArts.Art> ALL = load();
   private static final ThreadLocal<Boolean> BUSY = ThreadLocal.withInitial(() -> false);
   private static final Set<String> WARNED = ConcurrentHashMap.newKeySet();
   /** (058) ops the interpreter did not know, for the CI */
   public static int unknownOps;

   private static Map<String, RelicArts.Art> load() {
      Map<String, RelicArts.Art> out = new HashMap<>();

      try {
         Map root;
         try (InputStream in = RelicArts.class.getResourceAsStream("/assets/oror_supreme_bosses/relic_arts.json")) {
            if (in != null) {
               JsonElement rootx = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8));
               JsonObject top = rootx.getAsJsonObject();
               Iterator<JsonElement> it = top.getAsJsonArray("arts").iterator();

               while (it.hasNext()) {
                  JsonObject o = it.next().getAsJsonObject();
                  RelicArts.Art a = new RelicArts.Art();
                  a.id = o.get("id").getAsString();
                  a.character = o.get("character").getAsString();
                  a.rank = o.has("rank") ? o.get("rank").getAsInt() : 1;
                  a.cooldown = o.has("cd") ? o.get("cd").getAsInt() : -1;
                  a.cast = ops(o, "cast");
                  a.passive = ops(o, "passive");
                  a.hit = ops(o, "hit");
                  out.put(a.id, a);
               }

               return Collections.unmodifiableMap(out);
            }

            root = Collections.unmodifiableMap(out);
         }

         return root;
      } catch (Exception var9) {
         throw new IllegalStateException("Invalid relic_arts.json", var9);
      }
   }

   public static List<JsonObject> ops(JsonObject o, String key) {
      List<JsonObject> list = new ArrayList<>();
      if (o.has(key)) {
         Iterator<JsonElement> it = o.getAsJsonArray(key).iterator();

         while (it.hasNext()) {
            list.add(it.next().getAsJsonObject());
         }
      }

      return list;
   }

   public static RelicArts.Art of(String id) {
      return ALL.get(id);
   }

   public static boolean cast(String id, Player p) {
      RelicArts.Art a = ALL.get(id);
      if (a != null && p.level() instanceof ServerLevel sl) {
         run(a, a.cast, sl, p, null);
         p.getPersistentData().putInt("ororRelicCasts", p.getPersistentData().getInt("ororRelicCasts") + 1);
         return true;
      } else {
         return false;
      }
   }

   /**
    * (058) Runs a relic technique's program (or one of its later moments): the art of its relic gives the colour and
    * rank, the technique its own base damage and the frame it was released in.
    */
   public static void runTech(String artId, Player p, float base, List<JsonObject> program, Ctx frame, LivingEntity victim) {
      RelicArts.Art a = ALL.get(artId);
      if (a == null || !(p.level() instanceof ServerLevel sl)) {
         return;
      }

      boolean outer = !BUSY.get();
      BUSY.set(true);

      try {
         RelicArts.Ctx c = frame != null ? frame : new RelicArts.Ctx();
         c.sl = sl;
         c.p = p;
         c.art = a;
         c.base = base;
         RelicSpec owner = RelicSpec.ALL.get(a.character + "_weapon");
         c.color = owner != null ? owner.color : 16777215;
         if (frame == null) {
            c.victim = victim;
            if (victim != null) {
               c.t.add(victim);
            }
         }

         exec(c, program);
      } finally {
         if (outer) {
            BUSY.set(false);
         }
      }
   }

   public static boolean busy() {
      return BUSY.get();
   }

   /** (058) Runs this as a relic's own blow (no hit program of the held relic set off by it, as inside an art). */
   public static void quiet(Runnable r) {
      boolean outer = !BUSY.get();
      BUSY.set(true);

      try {
         r.run();
      } finally {
         if (outer) {
            BUSY.set(false);
         }
      }
   }

   public static void passive(String id, Player p) {
      RelicArts.Art a = ALL.get(id);
      if (a != null && p.level() instanceof ServerLevel sl && !a.passive.isEmpty()) {
         run(a, a.passive, sl, p, null);
      }
   }

   public static int cooldown(String id, int fallback) {
      RelicArts.Art a = ALL.get(id);
      return a != null && a.cooldown >= 0 ? a.cooldown : fallback;
   }

   public static boolean incoming(LivingIncomingDamageEvent e) {
      LivingEntity v = e.getEntity();
      if (v.level() instanceof ServerLevel sl) {
         long var13 = sl.getGameTime();
         CompoundTag vd = v.getPersistentData();
         if (v instanceof Player vp) {
            if (WeaponSkills.guard(e, vp, sl)) {
               return true;
            }

            if (vd.getLong("ororArtGuardUntil") > var13) {
               e.setCanceled(true);
               return true;
            }

            if (e.getSource().getDirectEntity() instanceof Projectile pr && vd.getLong("ororArtReflectUntil") > var13) {
               reflect(vp, pr);
               e.setCanceled(true);
               return true;
            }

            if (vd.getLong("ororArtUndyingUntil") > var13 && e.getAmount() >= vp.getHealth()) {
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
         } else {
            Entity src = e.getSource().getEntity();
            if (src instanceof Player p && src != v) {
               if (vd.getLong("ororArtMarkUntil") > var13) {
                  e.setAmount(e.getAmount() * Math.max(1.0F, vd.getFloat("ororArtMarkX")));
               }

               if (e.getSource().getDirectEntity() == p) {
                  String id = idOf(p.getMainHandItem());
                  RelicArts.Art a = id == null ? null : ALL.get(id);
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
      } else {
         return false;
      }
   }

   public static void equip(SupremeEntity b) {
      if (b.getMainHandItem().isEmpty() && b.spec != null) {
         DeferredItem<Item> relic = CharacterRelics.ITEMS.get(b.spec.id + "_weapon");
         if (relic != null) {
            b.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack((ItemLike)relic.get()));
            b.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
         }
      }
   }

   public static String idOf(ItemStack stack) {
      return stack.getItem() instanceof CharacterRelics.Wielded x ? x.wield().art : null;
   }

   private static void run(RelicArts.Art a, List<JsonObject> program, ServerLevel sl, Player p, LivingEntity victim) {
      boolean outer = !BUSY.get();
      BUSY.set(true);

      try {
         RelicArts.Ctx c = new RelicArts.Ctx();
         c.sl = sl;
         c.p = p;
         c.art = a;
         c.base = a.rank >= 3 ? 1000000.0F : 3000.0F * (float)a.rank;
         RelicSpec owner = RelicSpec.ALL.get(a.character + "_weapon");
         c.color = owner != null ? owner.color : 16777215;
         if (!a.id.endsWith("_focus") && !a.id.endsWith("_charm")) {
            c.span = 1.25F;
         } else {
            c.base *= 2.0F;
            c.heal = 2.0F;
            c.amp = 1;
            c.span = 1.5F;
            c.reach = 1.25F;
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

   public static void exec(RelicArts.Ctx c, List<JsonObject> program) {
      for (JsonObject o : program) {
         try {
            op(c, o);
         } catch (RuntimeException var5) {
            warn(c.art.id + " op " + o + " failed: " + var5);
         }
      }
   }

   public static double num(JsonObject o, String k, double d) {
      return o.has(k) ? Double.parseDouble(o.get(k).getAsString()) : d;
   }

   public static String str(JsonObject o, String k, String d) {
      return o.has(k) ? o.get(k).getAsString() : d;
   }

   public static void op(RelicArts.Ctx c, JsonObject o) {
      String op = o.get("op").getAsString();
      Player p = c.p;
      ServerLevel sl = c.sl;
      long now = sl.getGameTime();
      switch (op) {
         case "area": {
            c.t = sorted(near(p, p.position(), num(o, "r", 16.0) * (double)c.reach), p.position(), (int)num(o, "n", 64.0));
            break;
         }
         case "near": {
            c.t = sorted(near(p, p.position(), num(o, "r", 24.0) * (double)c.reach), p.position(), (int)num(o, "n", 1.0));
            break;
         }
         case "around": {
            Vec3 at = c.victim != null ? c.victim.position() : p.position();
            List<LivingEntity> l = sorted(near(p, at, num(o, "r", 4.0) * (double)c.reach), at, (int)num(o, "n", 16.0));
            if (c.victim != null && o.has("exclude")) {
               l.remove(c.victim);
            }

            c.t = l;
            break;
         }
         case "line": {
            c.t = line(p, c.eye(), c.look(), num(o, "r", 32.0) * (double)c.reach, num(o, "w", 2.5));
            break;
         }
         case "cone": {
            c.t = cone(p, c.look(), num(o, "r", 12.0) * (double)c.reach, num(o, "a", 90.0));
            break;
         }
         case "chain": {
            c.t = chain(p, c.victim, (int)num(o, "n", 6.0), num(o, "r", 10.0) * (double)c.reach);
            break;
         }
         case "allies": {
            c.t = allies(p, num(o, "r", 16.0) * (double)c.reach);
            break;
         }
         case "self": {
            c.t = new ArrayList<>();
            c.t.add(p);
            break;
         }
         case "victim": {
            c.t = new ArrayList<>();
            if (c.victim != null) {
               c.t.add(c.victim);
            }
            break;
         }
         case "dmg": {
            float base = (float)((double)c.base * num(o, "m", 1.0)) * c.mult;

            for (LivingEntity exxxxxxx : new ArrayList<>(c.t)) {
               if (exxxxxxx != p) {
                  float amount = jp.oror.reborn.relic.RelicTech.amount(c, exxxxxxx, base);
                  if (amount <= 0.0F) {
                     continue;
                  }

                  if (exxxxxxx instanceof SupremeEntity b) {
                     RelicDrops.fracture(b, p, amount);
                  }

                  float before = exxxxxxx.getHealth();
                  exxxxxxx.invulnerableTime = 0;
                  exxxxxxx.hurt(o.has("magic") ? p.damageSources().indirectMagic(p, p) : p.damageSources().playerAttack(p), amount);
                  c.dealt += Math.max(0.0F, before - exxxxxxx.getHealth());
                  jp.oror.reborn.relic.RelicTech.dealt(c, exxxxxxx, before - exxxxxxx.getHealth());
                  impact(c, exxxxxxx);
               }
            }
            break;
         }
         case "execute": {
            double pct = num(o, "pct", 0.3);

            for (LivingEntity exxxxxx : c.t) {
               if (exxxxxx != p && exxxxxx.isAlive()) {
                  if (exxxxxx instanceof SupremeEntity b) {
                     RelicDrops.fracture(b, p, c.base * 2.0F);
                     exxxxxx.invulnerableTime = 0;
                     exxxxxx.hurt(p.damageSources().playerAttack(p), c.base * 2.0F);
                  } else if ((double)exxxxxx.getHealth() <= (double)exxxxxx.getMaxHealth() * pct || exxxxxx.getMaxHealth() <= c.base) {
                     exxxxxx.invulnerableTime = 0;
                     exxxxxx.hurt(p.damageSources().genericKill(), Float.MAX_VALUE);
                  }
               }
            }
            break;
         }
         case "stun": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  Abilities.stun(ex, (int)(num(o, "t", 60.0) * (double)c.span));
               }
            });
            break;
         }
         case "eff": {
            Holder<MobEffect> h = effect(str(o, "e", "weakness"));

            for (LivingEntity exxxxx : c.t) {
               if (exxxxx != p || o.has("self")) {
                  exxxxx.addEffect(new MobEffectInstance(h, (int)(num(o, "t", 100.0) * (double)c.span), (int)num(o, "a", 0.0) + c.amp));
               }
            }
            break;
         }
         case "burn": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  ex.igniteForSeconds((float)num(o, "s", 8.0));
               }
            });
            break;
         }
         case "freeze": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  ex.setTicksFrozen((int)num(o, "t", 300.0));
                  Abilities.stun(ex, (int)num(o, "t", 300.0) / 3);
               }
            });
            break;
         }
         case "mark": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  ex.getPersistentData().putLong("ororArtMarkUntil", now + (long)num(o, "t", 200.0));
                  ex.getPersistentData().putFloat("ororArtMarkX", (float)num(o, "x", 2.0));
                  ex.setGlowingTag(true);
               }
            });
            break;
         }
         case "strip": {
            for (LivingEntity exxxx : c.t) {
               if (exxxx != p) {
                  for (MobEffectInstance m : new ArrayList<>(exxxx.getActiveEffects())) {
                     if (((MobEffect)m.getEffect().value()).isBeneficial()) {
                        exxxx.removeEffect(m.getEffect());
                        if (o.has("steal")) {
                           p.addEffect(new MobEffectInstance(m.getEffect(), m.getDuration(), m.getAmplifier()));
                        }
                     }
                  }
               }
            }
            break;
         }
         case "disarm": {
            c.t.forEach(ex -> {
               if (ex instanceof Mob m && !(ex instanceof SupremeEntity)) {
                  m.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
               }
            });
            break;
         }
         case "transmute": {
            for (LivingEntity exxx : new ArrayList<>(c.t)) {
               if (exxx != p && !(exxx instanceof Player) && !(exxx instanceof SupremeEntity) && exxx.isAlive() && !(exxx.getMaxHealth() > 300.0F)) {
                  Mob into = sl.random.nextInt(2) == 0 ? (Mob) EntityType.PIG.create(sl) : (Mob) EntityType.COW.create(sl);
                  if (into != null) {
                     into.moveTo(exxx.getX(), exxx.getY(), exxx.getZ(), exxx.getYRot(), 0.0F);
                     sl.addFreshEntity(into);
                  }

                  sl.sendParticles(ParticleTypes.WITCH, exxx.getX(), exxx.getY() + 0.8, exxx.getZ(), 30, 0.5, 0.8, 0.5, 0.1);
                  exxx.discard();
               }
            }
            break;
         }
         case "lightning": {
            for (LivingEntity exx : c.t) {
               if (exx != p) {
                  LightningBolt bolt = (LightningBolt)EntityType.LIGHTNING_BOLT.create(sl);
                  if (bolt != null) {
                     bolt.setVisualOnly(true);
                     bolt.setPos(exx.position());
                     sl.addFreshEntity(bolt);
                  }
               }
            }
            break;
         }
         case "arrows": {
            int n = (int)num(o, "n", 8.0);

            for (LivingEntity ex : c.t) {
               if (ex != p) {
                  for (int i = 0; i < n; i++) {
                     Arrow ar = (Arrow)EntityType.ARROW.create(sl);
                     if (ar != null) {
                        ar.moveTo(
                           ex.getX() + (sl.random.nextDouble() - 0.5) * 3.0,
                           ex.getY() + 8.0 + (double)i * 0.6,
                           ex.getZ() + (sl.random.nextDouble() - 0.5) * 3.0
                        );
                        ar.setDeltaMovement(0.0, -2.6, 0.0);
                        ar.setOwner(p);
                        ar.setBaseDamage(num(o, "d", 40.0));
                        ar.pickup = Pickup.DISALLOWED;
                        sl.addFreshEntity(ar);
                     }
                  }
               }
            }
            break;
         }
         case "knock": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  Vec3 d = ex.position().subtract(p.position());
                  push(ex, (d.lengthSqr() < 1.0E-4 ? p.getLookAngle() : d.normalize()).scale(num(o, "f", 2.0)).add(0.0, 0.45, 0.0));
               }
            });
            break;
         }
         case "pull": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  Vec3 d = p.position().subtract(ex.position());
                  push(ex, (d.lengthSqr() < 1.0E-4 ? Vec3.ZERO : d.normalize()).scale(num(o, "f", 1.5)).add(0.0, 0.3, 0.0));
               }
            });
            break;
         }
         case "launch": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  push(ex, new Vec3(0.0, num(o, "f", 1.6), 0.0));
               }
            });
            break;
         }
         case "slam": {
            c.t.forEach(ex -> {
               if (ex != p) {
                  push(ex, new Vec3(0.0, -num(o, "f", 3.0), 0.0));
               }
            });
            break;
         }
         case "blink": {
            blink(p, p.position().add(flat(p.getLookAngle()).scale(num(o, "d", 10.0))));
            break;
         }
         case "back": {
            blink(p, p.position().add(flat(p.getLookAngle()).scale(-num(o, "d", 6.0))));
            break;
         }
         case "behind": {
            if (!c.t.isEmpty() && c.t.get(0) != p) {
               LivingEntity e = c.t.get(0);
               blink(p, e.position().add(flat(e.position().subtract(p.position())).scale(1.6)));
            }
            break;
         }
         case "swap": {
            if (!c.t.isEmpty() && c.t.get(0) != p) {
               LivingEntity e = c.t.get(0);
               Vec3 a = p.position();
               Vec3 b = e.position();
               p.teleportTo(b.x, b.y, b.z);
               e.teleportTo(a.x, a.y, a.z);
            }
            break;
         }
         case "dash": {
            push(p, p.getLookAngle().scale(num(o, "f", 2.4)).add(0.0, 0.2, 0.0));
            break;
         }
         case "leap": {
            push(p, new Vec3(0.0, num(o, "f", 1.4), 0.0).add(flat(p.getLookAngle()).scale(0.6)));
            break;
         }
         case "heal": {
            for (LivingEntity ex : targetsOrSelf(c, o)) {
               ex.heal((float)num(o, "v", 20.0) * c.heal);
            }
            break;
         }
         case "healpct": {
            for (LivingEntity ex : targetsOrSelf(c, o)) {
               ex.heal((float)((double)ex.getMaxHealth() * Math.min(1.0, num(o, "v", 1.0) * (double)c.heal)));
            }
            break;
         }
         case "buff": {
            Holder<MobEffect> h = effect(str(o, "e", "strength"));

            for (LivingEntity ex : targetsOrSelf(c, o)) {
               ex.addEffect(new MobEffectInstance(h, (int)(num(o, "t", 200.0) * (double)c.span), (int)num(o, "a", 0.0) + c.amp));
            }
            break;
         }
         case "cleanse": {
            targetsOrSelf(c, o).forEach(RelicPowers::cleanse);
            break;
         }
         case "guard": {
            window(targetsOrSelf(c, o), "ororArtGuardUntil", now + (long)num(o, "t", 60.0));
            break;
         }
         case "undying": {
            window(targetsOrSelf(c, o), "ororArtUndyingUntil", now + (long)num(o, "t", 200.0));
            break;
         }
         case "adapt": {
            window(targetsOrSelf(c, o), "ororRelicAdaptUntil", now + (long)num(o, "t", 200.0));
            break;
         }
         case "reflect": {
            p.getPersistentData().putLong("ororArtReflectUntil", now + (long)num(o, "t", 40.0));

            for (Projectile pr : projectiles(p, num(o, "r", 8.0))) {
               reflect(p, pr);
            }
            break;
         }
         case "erase": {
            for (Projectile pr : projectiles(p, num(o, "r", 16.0))) {
               sl.sendParticles(ParticleTypes.POOF, pr.position().x, pr.position().y, pr.position().z, 3, 0.1, 0.1, 0.1, 0.02);
               pr.discard();
            }
            break;
         }
         case "food": {
            p.getFoodData().setFoodLevel(20);
            break;
         }
         case "repair": {
            repair(p, (int)num(o, "v", 64.0));
            break;
         }
         case "xp": {
            p.giveExperiencePoints((int)num(o, "v", 20.0));
            break;
         }
         case "give": {
            p.getInventory().add(new ItemStack(item(str(o, "item", "gold")), (int)num(o, "n", 1.0)));
            break;
         }
         case "summon": {
            summon(p, (int)num(o, "n", 2.0), str(o, "k", "wolf").equals("wolf"));
            break;
         }
         case "weather": {
            String w = str(o, "w", "clear");
            if (w.equals("clear")) {
               sl.setWeatherParameters(12000, 0, false, false);
            } else if (w.equals("rain")) {
               sl.setWeatherParameters(0, 6000, true, false);
            } else {
               sl.setWeatherParameters(0, 6000, true, true);
            }
            break;
         }
         case "time": {
            sl.setDayTime((long)num(o, "v", 1000.0));
            break;
         }
         case "snapshot": {
            snapshot(p, now);
            break;
         }
         case "rewind": {
            rewind(p, sl);
            break;
         }
         case "cycle": {
            JsonArray steps = o.getAsJsonArray("steps");
            String key = "ororArtCycle_" + c.art.id;
            int i = p.getPersistentData().getInt(key);
            int n = 0;
            Iterator<JsonElement> it = steps.iterator();

            while (it.hasNext()) {
               n++;
               it.next();
            }

            if (n > 0) {
               JsonElement step = steps.get(i % n);
               p.getPersistentData().putInt(key, (i + 1) % n);
               List<JsonObject> sub = new ArrayList<>();
               Iterator<JsonElement> itx = step.getAsJsonObject().getAsJsonArray("ops").iterator();

               while (itx.hasNext()) {
                  sub.add(itx.next().getAsJsonObject());
               }

               if (step.getAsJsonObject().has("say")) {
                  p.displayClientMessage(Component.translatable(step.getAsJsonObject().get("say").getAsString()), true);
               }

               exec(c, sub);
            }
            break;
         }
         case "chance": {
            if (sl.random.nextDouble() < num(o, "p", 0.5)) {
               exec(c, ops(o, "ops"));
            } else if (o.has("else")) {
               exec(c, ops(o, "else"));
            }
            break;
         }
         case "each": {
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
            break;
         }
         case "low": {
            if ((double)p.getHealth() <= (double)p.getMaxHealth() * num(o, "pct", 0.35)) {
               exec(c, ops(o, "ops"));
            }
            break;
         }
         case "fx": {
            fx(c, o);
            break;
         }
         case "sound": {
            sl.playSound(null, p.blockPosition(), sound(str(o, "s", "chime")), SoundSource.PLAYERS, (float)num(o, "v", 1.0), (float)num(o, "pi", 1.0));
            break;
         }
         case "say": {
            p.displayClientMessage(Component.translatable(str(o, "k", "")), true);
            break;
         }
         default: {
            if (!jp.oror.reborn.relic.RelicTech.op(c, o)) {
               unknownOps++;
               warn("unknown op " + op + " in " + c.art.id);
            }
         }
      }
   }

   private static void warn(String msg) {
      if (WARNED.size() < 64 && WARNED.add(msg)) {
         System.err.println("[oror_supreme_bosses] relic art: " + msg);
      }
   }

   public static List<LivingEntity> near(Player p, Vec3 at, double r) {
      return p.level().getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(r), e -> RelicPowers.enemy(p, e) && e.position().distanceTo(at) <= r);
   }

   public static List<LivingEntity> sorted(List<LivingEntity> list, Vec3 at, int n) {
      List<LivingEntity> out = new ArrayList<>(list);
      out.sort(Comparator.comparingDouble(e -> e.position().distanceToSqr(at)));
      return (List<LivingEntity>)(out.size() > n ? new ArrayList<>(out.subList(0, n)) : out);
   }

   public static List<LivingEntity> line(Player p, double r, double w) {
      return line(p, p.getEyePosition(), p.getLookAngle().normalize(), r, w);
   }

   public static List<LivingEntity> line(Player p, Vec3 a, Vec3 d, double r, double w) {
      Vec3 b = a.add(d.scale(r));
      List<LivingEntity> out = new ArrayList<>();

      for (LivingEntity e : p.level().getEntitiesOfClass(LivingEntity.class, new AABB(a, b).inflate(w + 1.0), ex -> RelicPowers.enemy(p, ex))) {
         Vec3 q = e.position().add(0.0, (double)e.getBbWidth() * 0.5, 0.0).subtract(a);
         double t = Math.max(0.0, Math.min(r, q.dot(d)));
         if (q.subtract(d.scale(t)).length() <= w + (double)e.getBbWidth() * 0.5) {
            out.add(e);
         }
      }

      return sorted(out, p.position(), 64);
   }

   public static List<LivingEntity> cone(Player p, double r, double deg) {
      return cone(p, p.getLookAngle(), r, deg);
   }

   public static List<LivingEntity> cone(Player p, Vec3 look, double r, double deg) {
      Vec3 d = flat(look);
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

   public static List<LivingEntity> chain(Player p, LivingEntity start, int n, double r) {
      List<LivingEntity> out = new ArrayList<>();
      LivingEntity cur = start;
      if (start == null) {
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

         for (LivingEntity e : near(p, cur.position(), r)) {
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
               Vec3 q = a.add(b.subtract(a).scale((double)i / 8.0));
               sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, q.x, q.y, q.z, 2, 0.05, 0.05, 0.05, 0.0);
            }
         }

         out.add(next);
         cur = next;
      }

      return out;
   }

   public static List<LivingEntity> allies(Player p, double r) {
      return p.level()
         .getEntitiesOfClass(
            LivingEntity.class,
            p.getBoundingBox().inflate(r),
            v -> v instanceof Player q && !RelicPowers.enemy(p, q)
                  || v instanceof SupremeEntity b && p.getUUID().equals(b.owner)
                  || v.getPersistentData().hasUUID("ororRelicOwner") && p.getUUID().equals(v.getPersistentData().getUUID("ororRelicOwner"))
         );
   }

   public static List<LivingEntity> targetsOrSelf(RelicArts.Ctx c, JsonObject o) {
      if (o.has("to")) {
         return c.t;
      } else {
         List<LivingEntity> l = new ArrayList<>();
         l.add(c.p);
         return l;
      }
   }

   public static Vec3 flat(Vec3 v) {
      Vec3 f = new Vec3(v.x, 0.0, v.z);
      return f.lengthSqr() < 1.0E-6 ? new Vec3(0.0, 0.0, 1.0) : f.normalize();
   }

   public static void push(LivingEntity e, Vec3 v) {
      e.setDeltaMovement(v);
      e.hurtMarked = true;
   }

   public static void window(List<LivingEntity> l, String key, long until) {
      for (LivingEntity e : l) {
         e.getPersistentData().putLong(key, Math.max(until, e.getPersistentData().getLong(key)));
      }
   }

   public static void blink(Player p, Vec3 at) {
      Level l = p.level();
      Vec3 from = p.position();

      for (int i = 0; i < 12; i++) {
         Vec3 q = at.add(from.subtract(at).scale((double)i / 12.0));
         if (l.hasChunkAt(BlockPos.containing(q))
            && l.getWorldBorder().isWithinBounds(BlockPos.containing(q))
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

   public static List<Projectile> projectiles(Player p, double r) {
      return p.level()
         .getEntitiesOfClass(
            Projectile.class,
            p.getBoundingBox().inflate(r),
            x -> x.getOwner() != p && (!(x.getOwner() instanceof LivingEntity owner) || RelicPowers.enemy(p, owner))
         );
   }

   public static void reflect(Player p, Projectile pr) {
      Vec3 v = pr.getDeltaMovement();
      Vec3 dir = pr.getOwner() instanceof LivingEntity le ? le.position().add(0.0, 1.0, 0.0).subtract(pr.position()).normalize() : v.scale(-1.0).normalize();
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

      for (ItemStack sx : p.getAllSlots()) {
         if (sx.isDamaged()) {
            sx.setDamageValue(Math.max(0, sx.getDamageValue() - amount));
         }
      }
   }

   public static void summon(Player p, int count, boolean beast) {
      if (p.level() instanceof ServerLevel sl) {
         int var9 = SummonBudget.remaining(sl, p.getUUID(), 6, count);

         for (int i = 0; i < var9; i++) {
            Mob e = beast ? (Mob)EntityType.WOLF.create(sl) : (Mob)EntityType.IRON_GOLEM.create(sl);
            if (e != null) {
               Vec3 at = p.position().add((double)(i * 2 - 3), 0.0, 3.0);
               e.moveTo(at.x, at.y, at.z, 0.0F, 0.0F);
               if (sl.hasChunkAt(e.blockPosition()) && sl.noCollision(e)) {
                  e.setPersistenceRequired();
                  if (e instanceof IronGolem g) {
                     g.setPlayerCreated(true);
                  }

                  if (e instanceof Wolf wolf) {
                     wolf.setTame(true, true);
                     wolf.setOwnerUUID(p.getUUID());
                  }

                  CompoundTag tag = e.getPersistentData();
                  tag.putUUID("ororRelicOwner", p.getUUID());
                  tag.putLong("ororRelicExpire", sl.getGameTime() + 1200L);
                  sl.addFreshEntity(e);
               }
            }
         }
      }
   }

   public static void snapshot(Player p, long now) {
      CompoundTag d = p.getPersistentData();
      int i = (int)(now / 20L % 6L);
      d.putFloat("ororArtSnapHP" + i, p.getHealth());
      d.putLong("ororArtSnapPos" + i, p.blockPosition().asLong());
      d.putLong("ororArtSnapAt" + i, now);
   }

   public static void rewind(Player p, ServerLevel sl) {
      CompoundTag d = p.getPersistentData();
      long now = sl.getGameTime();
      int best = -1;
      long oldest = Long.MAX_VALUE;

      for (int i = 0; i < 6; i++) {
         long at = d.getLong("ororArtSnapAt" + i);
         if (at > 0L && now - at <= 140L && at < oldest) {
            oldest = at;
            best = i;
         }
      }

      RelicPowers.cleanse(p);
      if (best < 0) {
         p.heal(p.getMaxHealth() * 0.5F);
      } else {
         p.setHealth(Math.max(p.getHealth(), Math.min(p.getMaxHealth(), d.getFloat("ororArtSnapHP" + best))));
         BlockPos pos = BlockPos.of(d.getLong("ororArtSnapPos" + best));
         blink(p, Vec3.atBottomCenterOf(pos));
      }
   }

   public static void fx(RelicArts.Ctx c, JsonObject o) {
      ParticleOptions part = particle(str(o, "p", "end_rod"));
      int n = (int)num(o, "n", 24.0);
      double s = num(o, "s", 0.6);
      String at = str(o, "at", "self");
      ServerLevel sl = c.sl;
      Player p = c.p;
      switch (at) {
         case "t": {
            for (LivingEntity e : c.t) {
               sl.sendParticles(part, e.getX(), e.getY() + 1.0, e.getZ(), n, s, s, s, num(o, "v", 0.05));
            }
            break;
         }
         case "line": {
            Vec3 a = p.getEyePosition();
            Vec3 d = p.getLookAngle().normalize();
            double r = num(o, "r", 24.0);

            for (int i = 0; i < n; i++) {
               Vec3 q = a.add(d.scale(r * (double)i / (double)Math.max(1, n - 1)));
               sl.sendParticles(part, q.x, q.y, q.z, 1, s * 0.2, s * 0.2, s * 0.2, 0.0);
            }
            break;
         }
         case "ring": {
            double r = num(o, "r", 4.0);

            for (int i = 0; i < n; i++) {
               double a = (Math.PI * 2) * (double)i / (double)n;
               sl.sendParticles(part, p.getX() + Math.cos(a) * r, p.getY() + num(o, "y", 0.3), p.getZ() + Math.sin(a) * r, 1, 0.0, 0.0, 0.0, num(o, "v", 0.0));
            }
            break;
         }
         case "pillar": {
            for (LivingEntity e : c.t) {
               for (int i = 0; i < 10; i++) {
                  sl.sendParticles(part, e.getX(), e.getY() + (double)i * 0.5, e.getZ(), Math.max(1, n / 10), 0.2, 0.1, 0.2, 0.02);
               }
            }
            break;
         }
         default: {
            sl.sendParticles(part, p.getX(), p.getY() + 1.0, p.getZ(), n, s, s, s, num(o, "v", 0.05));
         }
      }
   }

   public static Holder<MobEffect> effect(String n) {
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

   public static ParticleOptions particle(String n) {
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

   public static SoundEvent sound(String n) {
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

   public static Item item(String n) {
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

   public static void shot(Player p, CharacterRelics.Wield w) {
      if (p.level() instanceof ServerLevel sl) {
         String mode = w.kind.mode;
         boolean shell = mode.equals("shell");
         boolean gatling = mode.equals("gatling");
         long now = sl.getGameTime();
         CompoundTag d = p.getPersistentData();
         float damage = w.damage * w.kind.shot;
         int color = w.spec != null ? w.spec.color : 16777215;
         DustParticleOptions dust = RelicEffects.dust(color, shell ? 2.0F : 1.2F);
         boolean great = false;
         int heat = 0;
         if (gatling) {
            heat = now - d.getLong("ororHeatAt") <= 8L ? Math.min(20, d.getInt("ororHeat") + 1) : 0;
            d.putInt("ororHeat", heat);
            d.putLong("ororHeatAt", now);
            damage *= 1.0F + (float)heat * 0.04F;
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
            Vec3 side = new Vec3(-dir.z, 0.0, dir.x);
            side = side.lengthSqr() < 1.0E-6 ? new Vec3(1.0, 0.0, 0.0) : side.normalize();
            Vec3 muzzle = a.add(dir.scale(0.9)).add(side.scale(0.4)).add(0.0, -0.4, 0.0);
            RelicShells.fire(p, sl, muzzle, dir.scale(2.4).add(0.0, 0.05, 0.0), damage, w.rank >= 3 ? 5.0 : 4.0, color, w.rank >= 3);
         } else {
            if (gatling) {
               double j = 0.02 + (double)heat * 0.002;
               dir = dir.add((sl.random.nextDouble() - 0.5) * j, (sl.random.nextDouble() - 0.5) * j, (sl.random.nextDouble() - 0.5) * j).normalize();
            }

            BlockHitResult wall = sl.clip(new ClipContext(a, a.add(dir.scale(range)), Block.COLLIDER, Fluid.NONE, p));
            if (wall.getType() != Type.MISS) {
               range = wall.getLocation().distanceTo(a);
            }

            Vec3 far = a.add(dir.scale(range));
            LivingEntity first = null;
            double best = range;

            for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(a, far).inflate(1.5), ex -> RelicPowers.enemy(p, ex))) {
               Optional<Vec3> hit = e.getBoundingBox().inflate(0.3).clip(a, far);
               if (hit.isPresent() && hit.get().distanceTo(a) < best) {
                  best = hit.get().distanceTo(a);
                  first = e;
               }
            }

            Vec3 end = a.add(dir.scale(best));
            Vec3 side = new Vec3(-dir.z, 0.0, dir.x);
            side = side.lengthSqr() < 1.0E-6 ? new Vec3(1.0, 0.0, 0.0) : side.normalize();
            Vec3 muzzle = a.add(dir.scale(0.8)).add(side.scale(0.4)).add(0.0, mode.equals("bolt") ? 0.0 : -0.4, 0.0);
            Vec3 path = end.subtract(muzzle);
            sl.sendParticles(dust, muzzle.x, muzzle.y, muzzle.z, 4, 0.06, 0.06, 0.06, 0.0);
            int n = (int)Math.min(80.0, path.length() * (gatling ? 1.5 : 2.5));

            for (int i = 1; i <= n; i++) {
               Vec3 q = muzzle.add(path.scale((double)i / (double)n));
               sl.sendParticles(dust, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
               if (i % (gatling ? 3 : 2) == 0) {
                  sl.sendParticles(
                     shell ? ParticleTypes.LARGE_SMOKE : (gatling ? ParticleTypes.CRIT : ParticleTypes.END_ROD), q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0
                  );
               }
            }

            if (shell) {
               double r = w.rank >= 3 ? 5.0 : 4.0;

               for (LivingEntity ex : near(p, end, r)) {
                  strike(p, ex, damage, false);
                  if (!(ex instanceof SupremeEntity)) {
                     ex.setDeltaMovement(ex.getDeltaMovement().add(ex.position().subtract(end).normalize().scale(0.8).add(0.0, 0.7, 0.0)));
                     ex.hurtMarked = true;
                  }
               }

               sl.sendParticles(
                  w.rank >= 3 ? ParticleTypes.EXPLOSION_EMITTER : ParticleTypes.EXPLOSION, end.x, end.y, end.z, w.rank >= 3 ? 1 : 5, 0.8, 0.8, 0.8, 0.0
               );
               RelicEffects.shock(sl, end, 40, ParticleTypes.CLOUD, 0.5);
               RelicEffects.burst(sl, end, dust, 30, r * 0.4, 0.0);
               RelicEffects.burst(sl, end, ParticleTypes.LAVA, 8, 0.6, 0.0);
               sl.playSound(null, p.blockPosition(), SoundEvents.WITHER_SHOOT, SoundSource.PLAYERS, 0.8F, 1.3F);
               sl.playSound(null, BlockPos.containing(end), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 2.0F, 0.5F);
            } else if (gatling) {
               if (first != null) {
                  strike(p, first, damage, false);
                  if (heat >= 20) {
                     first.igniteForSeconds(3.0F);
                  }

                  sl.sendParticles(ParticleTypes.CRIT, end.x, end.y, end.z, 6, 0.15, 0.15, 0.15, 0.2);
               }

               sl.sendParticles(heat >= 20 ? ParticleTypes.FLAME : ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 2, 0.05, 0.05, 0.05, 0.02);
               sl.playSound(null, p.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 0.45F, 1.6F + (float)heat * 0.02F);
            } else if (great) {
               for (LivingEntity exx : near(p, end, 3.0)) {
                  strike(p, exx, damage, true);
               }

               RelicEffects.burst(sl, end, dust, 40, 1.0, 0.0);
               RelicEffects.burst(sl, end, ParticleTypes.END_ROD, 24, 0.2, 0.25);
               RelicEffects.shock(sl, end, 24, ParticleTypes.END_ROD, 0.3);
               sl.playSound(null, BlockPos.containing(end), SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS, 1.0F, 1.6F);
               sl.playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.2F, 0.8F);
               p.displayClientMessage(Component.translatable("weapon_skill.oror_supreme_bosses.magic").withStyle(ChatFormatting.GOLD), true);
            } else {
               if (first != null) {
                  strike(p, first, damage, true);
                  sl.sendParticles(ParticleTypes.ENCHANT, end.x, end.y, end.z, 12, 0.2, 0.2, 0.2, 0.4);
                  sl.sendParticles(dust, end.x, end.y, end.z, 10, 0.25, 0.25, 0.25, 0.0);
               }

               sl.playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.4F);
            }
         }
      }
   }

   static void strike(Player p, LivingEntity e, float amount, boolean magic) {
      boolean outer = !BUSY.get();
      BUSY.set(true);

      try {
         if (e instanceof SupremeEntity b) {
            RelicDrops.fracture(b, p, amount);
         }

         e.invulnerableTime = 0;
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

   public static void impact(RelicArts.Ctx c, LivingEntity e) {
      Vec3 at = e.position().add(0.0, (double)e.getBbHeight() * 0.5, 0.0);
      c.sl.sendParticles(RelicEffects.dust(c.color, 1.6F), at.x, at.y, at.z, 14, 0.35, 0.45, 0.35, 0.0);
      c.sl.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 8, 0.2, 0.3, 0.2, 0.35);
      if (c.art.rank >= 3) {
         c.sl.sendParticles(ParticleTypes.SONIC_BOOM, at.x, at.y, at.z, 1, 0.0, 0.0, 0.0, 0.0);
      }
   }

   public static void tooltip(String id, List<Component> lines) {
      if (jp.oror.reborn.relic.RelicText.tooltip(id, lines)) {
         return;
      }

      String k = "relic_art.oror_supreme_bosses." + id;
      lines.add(Component.translatable(k + ".name").withStyle(ChatFormatting.GOLD));
      lines.add(Component.translatable(k + ".desc").withStyle(ChatFormatting.GRAY));
      RelicArts.Art a = ALL.get(id);
      if (a != null && !a.passive.isEmpty()) {
         lines.add(Component.translatable(k + ".passive").withStyle(ChatFormatting.AQUA));
      }

      if (a != null && !a.hit.isEmpty()) {
         lines.add(Component.translatable(k + ".hit").withStyle(ChatFormatting.LIGHT_PURPLE));
      }
   }

   public static final class Art {
      public String id;
      public String character;
      public int rank = 1;
      public int cooldown = -1;
      public List<JsonObject> cast = List.of();
      public List<JsonObject> passive = List.of();
      public List<JsonObject> hit = List.of();
   }

   public static final class Ctx {
      public ServerLevel sl;
      public Player p;
      public RelicArts.Art art;
      public float base;
      public int color;
      public float heal = 1.0F;
      public int amp;
      public float span = 1.0F;
      public float reach = 1.0F;
      public LivingEntity victim;
      public List<LivingEntity> t = new ArrayList<>();
      // (058) a relic technique's frame: where it was released from and towards, the point it works at, its cast
      public Vec3 origin;
      public Vec3 dir;
      public Vec3 at;
      public Object cast;
      public float mult = 1.0F;
      public float dealt;
      public boolean nonlethal;

      /** A copy for a later moment of the same technique (its targets, its point, its cast). */
      public Ctx copy() {
         Ctx c = new Ctx();
         c.sl = this.sl;
         c.p = this.p;
         c.art = this.art;
         c.base = this.base;
         c.color = this.color;
         c.heal = this.heal;
         c.amp = this.amp;
         c.span = this.span;
         c.reach = this.reach;
         c.victim = this.victim;
         c.t = new ArrayList<>(this.t);
         c.origin = this.origin;
         c.dir = this.dir;
         c.at = this.at;
         c.cast = this.cast;
         c.mult = this.mult;
         c.nonlethal = this.nonlethal;
         return c;
      }

      public Vec3 eye() {
         return this.origin != null ? this.origin : this.p.getEyePosition();
      }

      public Vec3 look() {
         return this.dir != null ? this.dir : this.p.getLookAngle().normalize();
      }
   }
}
