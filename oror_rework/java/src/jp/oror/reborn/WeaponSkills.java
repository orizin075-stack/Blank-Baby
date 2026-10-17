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
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;

/**
 * The special ability of each weapon kind (weapon_skill.* in the lang files): what a katana, a spear, a hammer or a
 * fist does on top of its stats when it lands a blow, plus the perfect guard of shields and the light arrows of bows.
 * Called from RelicArts.incoming; damage dealt here goes through RelicArts.strike, which keeps it from re-triggering.
 */
public final class WeaponSkills {
    private WeaponSkills() {
    }

    /** A melee blow from a relic weapon in the main hand. */
    static void melee(LivingIncomingDamageEvent e, Player p, LivingEntity v, CharacterRelics.Wield w, ServerLevel sl) {
        long now = sl.getGameTime();
        CompoundTag d = p.getPersistentData();
        // sweep victims of the same swing are hit in the same tick: only the first target gets the skill
        if (d.getLong("ororSkillTick") == now) {
            return;
        }
        d.putLong("ororSkillTick", now);
        // a charged blow: the vanilla attack bar, or - for Epic Fight's own attacks, which do not use that bar - at least
        // one full swing interval (20 / attack speed ticks) since the previous relic blow
        double interval = 20.0 / Math.max(0.25, p.getAttributeValue(Attributes.ATTACK_SPEED));
        boolean full = p.getAttackStrengthScale(0.5F) > 0.9F || now - d.getLong("ororBlowAt") >= interval * 0.9;
        d.putLong("ororBlowAt", now);
        float hit = e.getAmount();
        float pow = w.rank >= 3 ? 1.5F : 1.0F;
        int color = w.spec != null ? w.spec.color : 0xFFFFFF;
        DustParticleOptions dust = RelicEffects.dust(color, 1.4F);
        Vec3 at = v.position().add(0.0, v.getBbHeight() * 0.5, 0.0);
        switch (w.kind.id) {
            case "katana" -> {
                RelicEffects.arc(sl, p, 2.2, 0.5, dust, ParticleTypes.END_ROD);
                int n = combo(d, "ororKatana", now, 40);
                if (full && n >= 3) {
                    d.putInt("ororKatana", 0);
                    announce(p, w);
                    for (LivingEntity t : ahead(p, v.position(), 7.0, 1.6)) {
                        RelicArts.strike(p, t, hit * 1.2F * pow, false);
                    }
                    Vec3 a = p.getEyePosition().add(0.0, -0.3, 0.0);
                    Vec3 b = a.add(p.getLookAngle().scale(9.0));
                    RelicEffects.line(sl, a, b, ParticleTypes.END_ROD, 0.2);
                    RelicEffects.line(sl, a, b, dust, 0.15);
                    RelicEffects.burst(sl, at, ParticleTypes.SWEEP_ATTACK, 4, 0.6, 0.0);
                    RelicEffects.sound(sl, p.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.0F, 1.6F);
                    RelicEffects.sound(sl, p.blockPosition(), SoundEvents.ILLUSIONER_MIRROR_MOVE, 0.8F, 1.8F);
                }
            }
            case "sword" -> {
                RelicEffects.arc(sl, p, 2.0, -0.4, dust, ParticleTypes.CRIT);
                if (full) {
                    announce(p, w);
                    for (LivingEntity t : ahead(p, v.position(), 5.0, 1.4)) {
                        if (t != v) {
                            RelicArts.strike(p, t, hit * 0.7F * pow, false);
                        }
                    }
                    RelicEffects.line(sl, at, at.add(flat(p.getLookAngle()).scale(5.0)), dust, 0.2);
                    RelicEffects.burst(sl, at, ParticleTypes.SWEEP_ATTACK, 3, 0.8, 0.0);
                    RelicEffects.sound(sl, p.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.0F, 1.2F);
                }
            }
            case "greatsword" -> {
                RelicEffects.arc(sl, p, 2.6, 0.9, dust, ParticleTypes.CRIT);
                if (full) {
                    announce(p, w);
                    for (LivingEntity t : around(p, v.position(), 4.0)) {
                        if (t != v) {
                            RelicArts.strike(p, t, hit * 0.8F * pow, false);
                        }
                        lift(t, 0.45);
                    }
                    Vec3 g = v.position().add(0.0, 0.1, 0.0);
                    RelicEffects.shock(sl, g, 40, ParticleTypes.CLOUD, 0.45);
                    RelicEffects.circle(sl, g, 3.5, dust);
                    RelicEffects.burst(sl, g, ParticleTypes.EXPLOSION, 3, 1.0, 0.0);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.ANVIL_LAND, 0.7F, 0.6F);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.0F, 0.7F);
                }
            }
            case "scythe" -> {
                RelicEffects.arc(sl, p, 3.0, 0.2, dust, ParticleTypes.SOUL);
                p.heal(Math.min(8.0F, hit * 0.1F));
                if (full) {
                    if (!(v instanceof SupremeEntity) && v.getHealth() - hit <= v.getMaxHealth() * 0.2F) {
                        announce(p, w);
                        e.setAmount(Math.max(hit, v.getHealth() + 1.0F));
                        RelicEffects.burst(sl, at, ParticleTypes.SOUL, 30, 0.4, 0.08);
                        RelicEffects.burst(sl, at, ParticleTypes.SCULK_SOUL, 12, 0.4, 0.05);
                        RelicEffects.sound(sl, v.blockPosition(), SoundEvents.WARDEN_SONIC_CHARGE, 0.6F, 2.0F);
                    } else {
                        e.setAmount(hit * (v instanceof SupremeEntity ? 1.4F : 1.2F) * pow);
                        RelicEffects.burst(sl, at, ParticleTypes.SOUL, 10, 0.3, 0.05);
                    }
                }
            }
            case "chakram" -> {
                if (full) {
                    announce(p, w);
                    List<LivingEntity> next = around(p, v.position(), 7.0);
                    next.remove(v);
                    next.sort(Comparator.comparingDouble(t -> t.distanceToSqr(v)));
                    Vec3 from = at;
                    for (int i = 0; i < Math.min(next.size(), w.rank >= 3 ? 5 : 3); i++) {
                        LivingEntity t = next.get(i);
                        Vec3 to = t.position().add(0.0, t.getBbHeight() * 0.5, 0.0);
                        RelicEffects.line(sl, from, to, dust, 0.2);
                        RelicEffects.line(sl, from, to, ParticleTypes.CRIT, 0.6);
                        RelicArts.strike(p, t, hit * 0.7F * pow, false);
                        from = to;
                    }
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.CHAIN_BREAK, 0.8F, 1.8F);
                }
                RelicEffects.arc(sl, p, 1.8, 0.0, dust, ParticleTypes.CRIT);
            }
            case "rapier" -> {
                v.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, w.rank >= 3 ? 2 : 1));
                RelicEffects.line(sl, p.getEyePosition().add(0.0, -0.3, 0.0), at, dust, 0.15);
                if (sl.random.nextFloat() < (w.rank >= 3 ? 0.5F : 0.3F)) {
                    announce(p, w);
                    e.setAmount(hit * 2.2F);
                    RelicEffects.burst(sl, at, ParticleTypes.ENCHANTED_HIT, 24, 0.3, 0.3);
                    RelicEffects.burst(sl, at, ParticleTypes.CRIT, 16, 0.2, 0.4);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.PLAYER_ATTACK_CRIT, 1.0F, 1.5F);
                }
            }
            case "polearm" -> {
                RelicEffects.line(sl, p.getEyePosition().add(0.0, -0.3, 0.0), at.add(flat(p.getLookAngle()).scale(1.5)), dust, 0.15);
                if (full) {
                    announce(p, w);
                    for (LivingEntity t : ahead(p, v.position(), 6.5, 1.2)) {
                        if (t != v) {
                            RelicArts.strike(p, t, hit * 0.8F * pow, false);
                        }
                        push(t, flat(p.getLookAngle()).scale(0.8).add(0.0, 0.2, 0.0));
                    }
                    RelicEffects.line(sl, at, at.add(flat(p.getLookAngle()).scale(6.5)), ParticleTypes.END_ROD, 0.3);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.0F, 1.4F);
                }
            }
            case "heavy" -> {
                if (full) {
                    announce(p, w);
                    for (LivingEntity t : around(p, v.position(), 3.5)) {
                        if (t != v) {
                            RelicArts.strike(p, t, hit * 0.6F * pow, false);
                        }
                        t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 3));
                        lift(t, 0.55);
                    }
                    Vec3 g = v.position().add(0.0, 0.1, 0.0);
                    RelicEffects.shock(sl, g, 48, ParticleTypes.POOF, 0.5);
                    RelicEffects.circle(sl, g, 3.2, dust);
                    RelicEffects.burst(sl, g, ParticleTypes.EXPLOSION, 4, 1.2, 0.0);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.ANVIL_LAND, 1.0F, 0.5F);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.STONE_BREAK, 1.0F, 0.6F);
                } else {
                    RelicEffects.burst(sl, at, ParticleTypes.CRIT, 8, 0.3, 0.2);
                }
            }
            case "toyhammer" -> {
                lift(v, v instanceof SupremeEntity ? 0.3 : 1.1);
                RelicEffects.burst(sl, at, ParticleTypes.FIREWORK, 20, 0.3, 0.25);
                RelicEffects.burst(sl, at.add(0.0, 0.6, 0.0), ParticleTypes.HAPPY_VILLAGER, 10, 0.5, 0.0);
                RelicEffects.sound(sl, v.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.2F, 2.0F);
                if (full) {
                    announce(p, w);
                    for (LivingEntity t : around(p, v.position(), 3.0)) {
                        if (t != v) {
                            RelicArts.strike(p, t, hit * 0.5F * pow, false);
                            lift(t, 1.0);
                        }
                    }
                    RelicEffects.shock(sl, v.position().add(0.0, 0.2, 0.0), 30, ParticleTypes.FIREWORK, 0.4);
                }
            }
            case "fist" -> {
                int n = combo(d, "ororFist", now, 30);
                float bonus = 1.0F + Math.min(n, 12) * 0.08F;
                e.setAmount(hit * bonus);
                p.displayClientMessage(Component.translatable("weapon_skill.oror_supreme_bosses.combo").append(Component.literal(" ×" + n)).withStyle(ChatFormatting.GOLD), true);
                RelicEffects.burst(sl, at, ParticleTypes.CRIT, 6 + n, 0.25, 0.3);
                RelicEffects.burst(sl, at, dust, 6, 0.3, 0.0);
                if (n % 5 == 0) {
                    announce(p, w);
                    for (LivingEntity t : around(p, v.position(), 3.0)) {
                        if (t != v) {
                            RelicArts.strike(p, t, hit * bonus * 0.6F * pow, false);
                        }
                        push(t, flat(t.position().subtract(p.position())).normalize().scale(1.2).add(0.0, 0.35, 0.0));
                    }
                    RelicEffects.shock(sl, at, 36, ParticleTypes.POOF, 0.45);
                    RelicEffects.burst(sl, at, ParticleTypes.EXPLOSION, 1, 0.0, 0.0);
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.0F, 0.8F);
                }
            }
            case "whip" -> {
                Vec3 back = p.position().subtract(v.position());
                if (!(v instanceof SupremeEntity) && back.lengthSqr() > 4.0) {
                    push(v, back.normalize().scale(Math.min(1.4, back.length() * 0.25)).add(0.0, 0.25, 0.0));
                }
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 1));
                RelicEffects.line(sl, p.position().add(0.0, 1.2, 0.0), at, dust, 0.18);
                RelicEffects.line(sl, p.position().add(0.0, 1.2, 0.0), at, ParticleTypes.CRIT, 0.7);
                if (full) {
                    List<LivingEntity> next = around(p, v.position(), 5.0);
                    next.remove(v);
                    if (!next.isEmpty()) {
                        announce(p, w);
                        LivingEntity t = next.get(sl.random.nextInt(next.size()));
                        RelicEffects.line(sl, at, t.position().add(0.0, t.getBbHeight() * 0.5, 0.0), dust, 0.18);
                        RelicArts.strike(p, t, hit * 0.8F * pow, false);
                        t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 2));
                    }
                    RelicEffects.sound(sl, v.blockPosition(), SoundEvents.CHAIN_BREAK, 0.9F, 1.3F);
                }
            }
            case "shield" -> {
                // shield bash: a heavy shove and a short daze
                if (!(v instanceof SupremeEntity)) {
                    push(v, flat(v.position().subtract(p.position())).normalize().scale(1.4).add(0.0, 0.3, 0.0));
                }
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 3));
                v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 1));
                RelicEffects.burst(sl, at, dust, 16, 0.4, 0.0);
                RelicEffects.sound(sl, v.blockPosition(), SoundEvents.ANVIL_LAND, 0.5F, 1.6F);
            }
            default -> RelicEffects.burst(sl, at, dust, 8, 0.3, 0.0);
        }
    }

    /** Arrows from relic bows: a burst of light on impact; a fully drawn one also scorches enemies around the target. */
    static void arrow(LivingIncomingDamageEvent e, Player p, LivingEntity v, Arrow a, ServerLevel sl) {
        CompoundTag t = a.getPersistentData();
        int color = t.getInt("ororRelicArrow");
        int rank = t.getInt("ororArrowRank");
        DustParticleOptions dust = RelicEffects.dust(color, 1.6F);
        Vec3 at = v.position().add(0.0, v.getBbHeight() * 0.5, 0.0);
        RelicEffects.burst(sl, at, dust, 20, 0.35, 0.0);
        RelicEffects.burst(sl, at, ParticleTypes.END_ROD, 10, 0.2, 0.12);
        v.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100, 0));
        if (t.getFloat("ororArrowPow") >= 1.0F) {
            float splash = e.getAmount() * (rank >= 3 ? 0.6F : 0.4F);
            for (LivingEntity o : around(p, v.position(), rank >= 3 ? 3.5 : 2.5)) {
                if (o != v) {
                    RelicArts.strike(p, o, splash, true);
                }
            }
            RelicEffects.shock(sl, at, 28, ParticleTypes.END_ROD, 0.3);
            RelicEffects.sound(sl, v.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F, 1.8F);
        }
    }

    /**
     * Perfect guard: an attack from the front that lands within half a second of raising a relic shield is nullified,
     * its attacker is staggered and takes a counter blow, and a projectile flies back. Returns true when it fired.
     */
    static boolean guard(LivingIncomingDamageEvent e, Player vp, ServerLevel sl) {
        if (!vp.isBlocking() || !(vp.getUseItem().getItem() instanceof CharacterRelics.Shield s)) {
            return false;
        }
        long now = sl.getGameTime();
        // vanilla only counts a shield as blocking 5 ticks after it is raised: ticks 5-15 are the perfect window
        if (now - vp.getPersistentData().getLong("ororGuardAt") > 15L) {
            return false;
        }
        Entity src = e.getSource().getEntity();
        Entity direct = e.getSource().getDirectEntity();
        Entity from = direct != null ? direct : src;
        if (from == null || flat(from.position().subtract(vp.position())).dot(flat(vp.getLookAngle())) <= 0.0) {
            return false;
        }
        CharacterRelics.Wield w = s.wield();
        e.setCanceled(true);
        if (direct instanceof Projectile pr && !(direct instanceof LivingEntity)) {
            RelicArts.reflectProjectile(vp, pr);
        }
        if (src instanceof LivingEntity attacker && attacker != vp) {
            RelicArts.strike(vp, attacker, w.damage * 1.5F * (w.rank >= 3 ? 2.0F : 1.0F), false);
            attacker.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 4));
            attacker.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 2));
            if (!(attacker instanceof SupremeEntity)) {
                push(attacker, flat(attacker.position().subtract(vp.position())).normalize().scale(1.6).add(0.0, 0.4, 0.0));
            }
        }
        int color = w.spec != null ? w.spec.color : 0xFFD700;
        Vec3 c = vp.position().add(vp.getLookAngle().scale(0.8)).add(0.0, 1.1, 0.0);
        RelicEffects.burst(sl, c, ParticleTypes.END_ROD, 30, 0.3, 0.25);
        RelicEffects.burst(sl, c, RelicEffects.dust(color, 2.0F), 24, 0.5, 0.0);
        RelicEffects.shock(sl, vp.position().add(0.0, 0.2, 0.0), 36, ParticleTypes.END_ROD, 0.45);
        RelicEffects.sound(sl, vp.blockPosition(), SoundEvents.ANVIL_LAND, 0.8F, 1.8F);
        RelicEffects.sound(sl, vp.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.2F, 1.4F);
        vp.displayClientMessage(Component.translatable("weapon_skill.oror_supreme_bosses.shield").withStyle(ChatFormatting.GOLD), true);
        return true;
    }

    /** While a relic shield is raised, players nearby share its protection (once a second, from CharacterRelics.held). */
    static void sanctuary(Player p, CharacterRelics.Wield w, ServerLevel sl) {
        double r = w.rank >= 3 ? 8.0 : 5.0;
        for (Player o : sl.getEntitiesOfClass(Player.class, p.getBoundingBox().inflate(r), o -> o != p && o.isAlive())) {
            o.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 30, w.rank >= 3 ? 2 : 1));
        }
        RelicEffects.circle(sl, p.position().add(0.0, 0.1, 0.0), r * 0.5, RelicEffects.dust(w.spec != null ? w.spec.color : 0xFFD700, 1.0F));
    }

    // ------------------------------------------------------------------------------------- helpers
    private static void announce(Player p, CharacterRelics.Wield w) {
        p.displayClientMessage(Component.translatable("weapon_skill.oror_supreme_bosses." + w.kind.id).withStyle(ChatFormatting.GOLD), true);
    }

    private static int combo(CompoundTag d, String key, long now, int window) {
        int n = now - d.getLong(key + "At") <= window ? d.getInt(key) + 1 : 1;
        d.putInt(key, n);
        d.putLong(key + "At", now);
        return n;
    }

    private static List<LivingEntity> around(Player p, Vec3 at, double r) {
        return new ArrayList<>(p.level().getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(r), e -> RelicPowers.enemy(p, e) && e.position().distanceTo(at) <= r));
    }

    /** Enemies in a strip from the target onwards, along the player's facing. */
    private static List<LivingEntity> ahead(Player p, Vec3 from, double len, double width) {
        Vec3 d = flat(p.getLookAngle());
        Vec3 a = p.position();
        List<LivingEntity> out = new ArrayList<>();
        double reach = from.subtract(a).dot(d) + len;
        for (LivingEntity e : p.level().getEntitiesOfClass(LivingEntity.class, new AABB(a, a.add(d.scale(reach))).inflate(width + 2.0), e -> RelicPowers.enemy(p, e))) {
            Vec3 q = e.position().subtract(a);
            double t = q.dot(d);
            if (t > 0.0 && t <= reach && q.subtract(d.scale(t)).length() <= width + e.getBbWidth() * 0.5) {
                out.add(e);
            }
        }
        return out;
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
