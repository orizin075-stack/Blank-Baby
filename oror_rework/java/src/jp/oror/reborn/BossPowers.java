package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * The 41 characters fight with their relic weapon's kind (v0.17.6):
 * - a signature attack every few seconds, telegraphed for 0.6 s at the spot it will strike (dodgeable);
 * - awakening at half health: the legend weapon in hand, a barrier of half its health, a damaging aura and
 *   twice as many signature attacks;
 * - resolve: very large single hits are compressed (damage above 20 grows sub-linearly) and one hit takes at most 8%
 *   of max health (6% awakened), so relic weapons and arts cannot erase them in one or two blows. Ordinary weapons
 *   are unaffected. Characters running on a lore soul pool are left as they are.
 * Called from WorldEvents (entity tick, incoming damage); works the same for wild bosses and for characters a player
 * has befriended, whose targets are the player's enemies.
 */
public final class BossPowers {
    private BossPowers() {
    }

    // ------------------------------------------------------------------------------------- tick
    static void tick(SupremeEntity b, ServerLevel sl) {
        if (!b.isAlive() || b.isNoAi()) {
            return;
        }
        long now = sl.getGameTime();
        CompoundTag d = b.getPersistentData();
        LivingEntity t = b.getTarget();
        boolean awake = d.getBoolean("ororAwakened");
        float frac = b.getHealth() / Math.max(1.0F, b.getMaxHealth());
        if (!awake && t != null && frac <= 0.5F) {
            awaken(b, sl, d);
            awake = true;
        } else if (awake && t == null && frac >= 0.99F) {
            d.putBoolean("ororAwakened", false);
            hold(b, "_weapon");
        }
        int color = color(b);
        if (t != null && now % 10L == 0L) {
            double a = now * 0.3;
            for (int i = 0; i < 6; i++) {
                double q = a + Math.PI * 2.0 * i / 6.0;
                sl.sendParticles(RelicEffects.dust(color, awake ? 1.6F : 1.0F), b.getX() + Math.cos(q) * 1.3, b.getY() + 0.15, b.getZ() + Math.sin(q) * 1.3, 1, 0.0, 0.0, 0.0, 0.0);
            }
        }
        if (awake && t != null && now % 20L == 0L) {
            float aura = b.spec.damage * 0.5F;
            for (LivingEntity e : enemies(b, b.position(), 4.5)) {
                hit(b, e, aura);
            }
            RelicEffects.circle(sl, b.position().add(0.0, 0.1, 0.0), 4.5, RelicEffects.dust(color, 1.2F));
        }
        long fire = d.getLong("ororSigFire");
        if (fire > 0L) {
            if (now >= fire) {
                d.putLong("ororSigFire", 0L);
                if (t != null && t.isAlive()) {
                    Vec3 aim = new Vec3(d.getDouble("ororSigX"), d.getDouble("ororSigY"), d.getDouble("ororSigZ"));
                    signature(b, sl, t, aim, awake, color);
                }
            }
        } else if (t != null && now >= d.getLong("ororSigAt") && b.distanceToSqr(t) < 576.0) {
            Vec3 aim = t.position();
            d.putLong("ororSigFire", now + 12L);
            d.putLong("ororSigAt", now + (awake ? 45L : (b.lore() ? 90L : 140L)));
            d.putDouble("ororSigX", aim.x);
            d.putDouble("ororSigY", aim.y);
            d.putDouble("ororSigZ", aim.z);
            telegraph(b, sl, aim, color);
        }
    }

    /** Half health: the legend form. */
    private static void awaken(SupremeEntity b, ServerLevel sl, CompoundTag d) {
        d.putBoolean("ororAwakened", true);
        hold(b, "_legend");
        b.shield += b.getMaxHealth() * 0.5F;
        b.cooldown = 0;
        int color = color(b);
        RelicEffects.show(sl, b, color, 3);
        RelicEffects.shock(sl, b.position().add(0.0, 0.3, 0.0), 64, ParticleTypes.END_ROD, 0.8);
        RelicEffects.circle(sl, b.position().add(0.0, 0.1, 0.0), 6.0, RelicEffects.dust(color, 2.0F));
        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ENDER_DRAGON_GROWL, 1.2F, 0.8F);
        Component title = Component.literal(b.spec.name + "　")
            .append(Component.translatable("relic_art.oror_supreme_bosses." + b.spec.id + "_legend.title"))
            .append(Component.translatable("boss_skill.oror_supreme_bosses.awaken"))
            .withStyle(ChatFormatting.GOLD);
        for (Player p : sl.getEntitiesOfClass(Player.class, b.getBoundingBox().inflate(64.0))) {
            p.displayClientMessage(title, true);
        }
    }

    private static void hold(SupremeEntity b, String slot) {
        DeferredItem<Item> relic = CharacterRelics.ITEMS.get(b.spec.id + slot);
        if (relic != null && !b.getMainHandItem().is(relic.get())) {
            b.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(relic.get()));
            b.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
        }
    }

    /** The warning: a circle where the blow will land and a rising sound. */
    private static void telegraph(SupremeEntity b, ServerLevel sl, Vec3 aim, int color) {
        DustParticleOptions dust = RelicEffects.dust(color, 1.5F);
        RelicEffects.circle(sl, aim.add(0.0, 0.1, 0.0), 2.5, dust);
        RelicEffects.line(sl, b.position().add(0.0, 1.0, 0.0), aim.add(0.0, 0.2, 0.0), dust, 0.6);
        sl.sendParticles(ParticleTypes.END_ROD, aim.x, aim.y + 0.2, aim.z, 12, 0.6, 0.05, 0.6, 0.02);
        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, 1.0F, 0.7F);
    }

    // ------------------------------------------------------------------------------------- signature attacks
    private static void signature(SupremeEntity b, ServerLevel sl, LivingEntity t, Vec3 aim, boolean awake, int color) {
        CharacterRelics.Kind k = CharacterRelics.kindOf(b.spec.id);
        float dmg = b.spec.damage * (awake ? 2.5F : 1.5F);
        DustParticleOptions dust = RelicEffects.dust(color, 1.6F);
        Vec3 from = b.position().add(0.0, b.getBbHeight() * 0.5, 0.0);
        Vec3 dir = flat(aim.subtract(b.position()));
        announce(b, sl, k.id);
        switch (k.id) {
            case "katana" -> {
                Vec3 end = aim.add(dir.scale(3.0));
                for (LivingEntity e : strip(b, b.position(), end, 1.6)) {
                    hit(b, e, dmg * 1.5F);
                }
                RelicEffects.line(sl, from, end.add(0.0, 1.0, 0.0), ParticleTypes.END_ROD, 0.25);
                RelicEffects.line(sl, from, end.add(0.0, 1.0, 0.0), dust, 0.2);
                if (sl.noCollision(b, b.getBoundingBox().move(end.subtract(b.position())))) {
                    b.teleportTo(end.x, end.y, end.z);
                }
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.2F, 1.5F);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ILLUSIONER_MIRROR_MOVE, 1.0F, 1.6F);
            }
            case "sword", "rapier" -> {
                Vec3 end = b.position().add(dir.scale(14.0));
                for (LivingEntity e : strip(b, b.position(), end, 1.5)) {
                    hit(b, e, dmg * (k.id.equals("rapier") ? 1.0F : 1.3F));
                    if (k.id.equals("rapier")) {
                        e.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
                    }
                }
                for (double s = 1.0; s < 14.0; s += 2.0) {
                    Vec3 q = from.add(dir.scale(s));
                    sl.sendParticles(ParticleTypes.SWEEP_ATTACK, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
                }
                RelicEffects.line(sl, from, from.add(dir.scale(14.0)), dust, 0.25);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.2F, 1.0F);
            }
            case "greatsword", "heavy", "toyhammer" -> {
                double r = awake ? 7.0 : 5.0;
                for (LivingEntity e : enemies(b, aim, r)) {
                    hit(b, e, dmg * 1.5F);
                    lift(e, k.id.equals("toyhammer") ? 1.4 : 0.6);
                    e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2));
                }
                RelicEffects.shock(sl, aim.add(0.0, 0.2, 0.0), 56, ParticleTypes.CLOUD, 0.6);
                RelicEffects.circle(sl, aim.add(0.0, 0.1, 0.0), r, dust);
                sl.sendParticles(ParticleTypes.EXPLOSION, aim.x, aim.y + 0.5, aim.z, 6, r * 0.3, 0.3, r * 0.3, 0.0);
                RelicEffects.sound(sl, net.minecraft.core.BlockPos.containing(aim), SoundEvents.ANVIL_LAND, 1.4F, 0.5F);
                RelicEffects.sound(sl, net.minecraft.core.BlockPos.containing(aim), SoundEvents.FIREWORK_ROCKET_BLAST, 1.6F, 0.5F);
            }
            case "scythe" -> {
                for (LivingEntity e : enemies(b, b.position(), 6.5)) {
                    hit(b, e, dmg * 1.2F);
                    e.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 2));
                }
                RelicEffects.circle(sl, b.position().add(0.0, 1.0, 0.0), 6.0, dust);
                RelicEffects.burst(sl, from, ParticleTypes.SOUL, 40, 2.5, 0.05);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.WARDEN_SONIC_CHARGE, 0.8F, 1.6F);
            }
            case "chakram" -> {
                List<LivingEntity> chain = enemies(b, aim, 12.0);
                chain.sort(Comparator.comparingDouble(e -> e.position().distanceToSqr(aim)));
                Vec3 at = from;
                for (int i = 0; i < Math.min(chain.size(), awake ? 8 : 5); i++) {
                    LivingEntity e = chain.get(i);
                    Vec3 to = e.position().add(0.0, e.getBbHeight() * 0.5, 0.0);
                    RelicEffects.line(sl, at, to, dust, 0.2);
                    hit(b, e, dmg * 1.2F);
                    at = to;
                }
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.CHAIN_BREAK, 1.0F, 1.6F);
            }
            case "polearm" -> {
                Vec3 end = b.position().add(dir.scale(10.0));
                for (LivingEntity e : strip(b, b.position(), end, 1.6)) {
                    hit(b, e, dmg * 1.4F);
                    push(e, dir.scale(1.2).add(0.0, 0.3, 0.0));
                }
                push(b, dir.scale(2.0).add(0.0, 0.25, 0.0));
                RelicEffects.line(sl, from, from.add(dir.scale(10.0)), ParticleTypes.END_ROD, 0.3);
                RelicEffects.line(sl, from, from.add(dir.scale(10.0)), dust, 0.2);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.2F, 1.0F);
            }
            case "fist" -> {
                if (b.position().distanceTo(aim) > 4.0) {
                    push(b, dir.scale(1.8).add(0.0, 0.3, 0.0));
                }
                for (LivingEntity e : enemies(b, aim, 4.5)) {
                    hit(b, e, dmg * 1.6F);
                    push(e, flat(e.position().subtract(aim)).scale(1.6).add(0.0, 0.5, 0.0));
                }
                RelicEffects.shock(sl, aim.add(0.0, 0.5, 0.0), 40, ParticleTypes.POOF, 0.6);
                sl.sendParticles(ParticleTypes.EXPLOSION, aim.x, aim.y + 1.0, aim.z, 2, 0.4, 0.4, 0.4, 0.0);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.4F, 0.6F);
            }
            case "whip" -> {
                for (LivingEntity e : enemies(b, b.position(), 11.0)) {
                    Vec3 to = e.position().add(0.0, e.getBbHeight() * 0.5, 0.0);
                    RelicEffects.line(sl, from, to, dust, 0.2);
                    RelicEffects.line(sl, from, to, ParticleTypes.CRIT, 0.8);
                    hit(b, e, dmg * 0.8F);
                    push(e, b.position().subtract(e.position()).normalize().scale(1.3).add(0.0, 0.3, 0.0));
                    e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 80, 3));
                }
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.CHAIN_BREAK, 1.2F, 0.9F);
            }
            case "magic" -> {
                List<LivingEntity> near = enemies(b, aim, 8.0);
                int bolts = awake ? 9 : 5;
                for (int i = 0; i < bolts && !near.isEmpty(); i++) {
                    bolt(b, sl, near.get(i % near.size()), dmg * 0.8F, dust, false);
                }
                for (LivingEntity e : enemies(b, aim, 3.0)) {
                    hit(b, e, dmg * 1.5F);
                }
                RelicEffects.burst(sl, aim.add(0.0, 1.0, 0.0), dust, 40, 1.2, 0.0);
                RelicEffects.shock(sl, aim.add(0.0, 0.5, 0.0), 24, ParticleTypes.END_ROD, 0.35);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, 1.2F, 1.4F);
            }
            case "gatling" -> {
                for (int i = 0; i < (awake ? 20 : 12); i++) {
                    bolt(b, sl, t, dmg * 0.3F, dust, true);
                }
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, 1.2F, 1.8F);
            }
            case "cannon" -> {
                for (int i = 0; i < (awake ? 5 : 3); i++) {
                    Vec3 at = aim.add((sl.random.nextDouble() - 0.5) * 6.0, 0.0, (sl.random.nextDouble() - 0.5) * 6.0);
                    for (LivingEntity e : enemies(b, at, 4.0)) {
                        hit(b, e, dmg * 1.2F);
                        lift(e, 0.6);
                    }
                    RelicEffects.line(sl, from, at.add(0.0, 0.5, 0.0), ParticleTypes.LARGE_SMOKE, 0.8);
                    sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y + 0.5, at.z, 1, 0.0, 0.0, 0.0, 0.0);
                    RelicEffects.burst(sl, at.add(0.0, 0.5, 0.0), dust, 20, 1.5, 0.0);
                }
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.WITHER_SHOOT, 1.4F, 0.8F);
            }
            case "bow" -> {
                int n = awake ? 11 : 7;
                Vec3 eye = b.getEyePosition();
                Vec3 to = t.getEyePosition().subtract(eye);
                for (int i = 0; i < n; i++) {
                    double yaw = Math.toRadians((i - (n - 1) * 0.5) * 5.0);
                    double c = Math.cos(yaw);
                    double s = Math.sin(yaw);
                    // 1.21 arrows refuse an empty "fired from" weapon stack
                    Arrow a = new Arrow(sl, b, new ItemStack(Items.ARROW), b.getMainHandItem().isEmpty() ? new ItemStack(Items.BOW) : b.getMainHandItem());
                    a.shoot(to.x * c - to.z * s, to.y + to.length() * 0.05, to.x * s + to.z * c, 3.0F, 1.0F);
                    a.setBaseDamage(dmg * 0.6F / 3.0F);
                    a.pickup = AbstractArrow.Pickup.DISALLOWED;
                    sl.addFreshEntity(a);
                }
                RelicEffects.burst(sl, eye, dust, 24, 0.4, 0.0);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ARROW_SHOOT, 1.4F, 0.8F);
            }
            case "shield" -> {
                for (Projectile pr : sl.getEntitiesOfClass(Projectile.class, b.getBoundingBox().inflate(8.0),
                    x -> x.getOwner() instanceof LivingEntity o && b.validEnemy(o))) {
                    Vec3 back = pr.getOwner().position().add(0.0, 1.0, 0.0).subtract(pr.position()).normalize();
                    pr.setOwner(b);
                    pr.setDeltaMovement(back.scale(Math.max(1.2, pr.getDeltaMovement().length() * 1.5)));
                    pr.hasImpulse = true;
                }
                for (LivingEntity e : enemies(b, b.position(), 5.5)) {
                    hit(b, e, dmg * 0.8F);
                    push(e, flat(e.position().subtract(b.position())).scale(1.8).add(0.0, 0.4, 0.0));
                }
                b.shield += b.spec.damage * 3.0F;
                RelicEffects.circle(sl, b.position().add(0.0, 0.1, 0.0), 5.5, dust);
                RelicEffects.shock(sl, b.position().add(0.0, 1.0, 0.0), 40, ParticleTypes.END_ROD, 0.5);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ANVIL_LAND, 1.0F, 1.6F);
            }
            default -> {
                for (LivingEntity e : enemies(b, aim, 4.0)) {
                    hit(b, e, dmg);
                }
                RelicEffects.burst(sl, aim.add(0.0, 1.0, 0.0), dust, 30, 1.2, 0.0);
            }
        }
    }

    /** A hitscan shot from the eyes to a target; walls stop it. Gatling rounds spread a little. */
    private static void bolt(SupremeEntity b, ServerLevel sl, LivingEntity t, float dmg, DustParticleOptions dust, boolean round) {
        Vec3 a = b.getEyePosition();
        Vec3 to = t.position().add(0.0, t.getBbHeight() * 0.6, 0.0);
        if (round) {
            to = to.add((sl.random.nextDouble() - 0.5) * 1.2, (sl.random.nextDouble() - 0.5) * 1.2, (sl.random.nextDouble() - 0.5) * 1.2);
        }
        Vec3 end = to;
        boolean clear = true;
        var wall = sl.clip(new ClipContext(a, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, b));
        if (wall.getType() != HitResult.Type.MISS) {
            end = wall.getLocation();
            clear = false;
        }
        RelicEffects.line(sl, a, end, dust, round ? 0.8 : 0.3);
        if (!round) {
            RelicEffects.line(sl, a, end, ParticleTypes.END_ROD, 1.2);
        }
        if (clear && t.getBoundingBox().inflate(0.4).contains(end)) {
            hit(b, t, dmg);
            sl.sendParticles(round ? ParticleTypes.CRIT : ParticleTypes.ENCHANT, end.x, end.y, end.z, 6, 0.2, 0.2, 0.2, 0.2);
        }
    }

    private static void announce(SupremeEntity b, ServerLevel sl, String kind) {
        Component name = Component.literal(b.spec.name + "「")
            .append(Component.translatable("boss_skill.oror_supreme_bosses." + kind))
            .append(Component.literal("」"))
            .withStyle(ChatFormatting.RED);
        for (Player p : sl.getEntitiesOfClass(Player.class, b.getBoundingBox().inflate(32.0), p -> b.validEnemy(p))) {
            p.displayClientMessage(name, true);
        }
    }

    // ------------------------------------------------------------------------------------- resolve
    /** Incoming damage to a character (WorldEvents.damage, after every other handler has adjusted the amount). */
    static void incoming(LivingIncomingDamageEvent e, SupremeEntity b) {
        if (e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY) || (b.lore() && b.spec.loreHealth > 0.0F)) {
            return;
        }
        boolean awake = b.getPersistentData().getBoolean("ororAwakened");
        float a = e.getAmount();
        if (a > 20.0F) {
            a = 20.0F + (float) Math.pow(a - 20.0F, awake ? 0.55 : 0.65);
        }
        e.setAmount(Math.min(a, b.getMaxHealth() * (awake ? 0.06F : 0.08F)));
    }

    // ------------------------------------------------------------------------------------- helpers
    private static int color(SupremeEntity b) {
        RelicSpec s = RelicSpec.ALL.get(b.spec.id + "_weapon");
        return s != null ? s.color : b.spec.accent;
    }

    private static List<LivingEntity> enemies(SupremeEntity b, Vec3 at, double r) {
        return new ArrayList<>(b.level().getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(r),
            e -> e != b && b.validEnemy(e) && e.position().distanceTo(at) <= r));
    }

    /** Enemies within width of the segment a-b (feet level). */
    private static List<LivingEntity> strip(SupremeEntity b, Vec3 a, Vec3 c, double width) {
        Vec3 d = c.subtract(a);
        double len = d.length();
        Vec3 u = len < 1.0E-4 ? new Vec3(1.0, 0.0, 0.0) : d.scale(1.0 / len);
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : b.level().getEntitiesOfClass(LivingEntity.class, new AABB(a, c).inflate(width + 2.0), e -> e != b && b.validEnemy(e))) {
            Vec3 q = e.position().subtract(a);
            double s = Math.max(0.0, Math.min(len, q.dot(u)));
            if (q.subtract(u.scale(s)).length() <= width + e.getBbWidth() * 0.5) {
                out.add(e);
            }
        }
        return out;
    }

    private static void hit(SupremeEntity b, LivingEntity e, float amount) {
        e.invulnerableTime = 0;
        e.hurt(b.damageSources().mobAttack(b), amount);
    }

    private static Vec3 flat(Vec3 v) {
        Vec3 f = new Vec3(v.x, 0.0, v.z);
        return f.lengthSqr() < 1.0E-6 ? new Vec3(1.0, 0.0, 0.0) : f.normalize();
    }

    private static void push(LivingEntity e, Vec3 v) {
        e.setDeltaMovement(e.getDeltaMovement().add(v));
        e.hurtMarked = true;
    }

    private static void lift(LivingEntity e, double up) {
        if (!(e instanceof SupremeEntity)) {
            push(e, new Vec3(0.0, up, 0.0));
        }
    }
}
