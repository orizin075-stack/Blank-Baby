package jp.oror.reborn;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Basic weapon attacks of the 41 characters (v0.17.10), between their abilities and named moves. Before, a character
 * fought only with abilities and moves and stood nine blocks off its target whatever it wielded (that range came from
 * a list older than the weapon kinds), so fist fighters never threw a punch and casters never fired their staff. Now
 * - melee kinds walk into their reach and strike at their kind's pace: fists in quick punch chains with a heavy blow
 *   every third, blades in alternating cuts, spears and rapiers in thrusts, hammers in overhead smashes, shields in
 *   bashes; their ability wind-ups show a weapon pose instead of a spell-casting one;
 * - catalysts fire bolts (every fourth a bursting great bolt), gatlings bursts of rounds, cannons exploding shells and
 *   bows light shots.
 * Characters in lore mode fight through AdaptiveCombat, which fires the same shots (fire()) instead of plain arrows.
 */
public final class BossArms {
    private BossArms() {
    }

    static void tick(SupremeEntity b, ServerLevel sl, LivingEntity t, boolean awake, int color) {
        if (t == null || b.lore() || !b.getPersistentData().getString("ororMove").isEmpty()) {
            return;
        }
        CharacterRelics.Kind k = CharacterRelics.kindOf(b.spec.id);
        CompoundTag d = b.getPersistentData();
        long now = sl.getGameTime();
        double dist = b.distanceTo(t);
        boolean melee = k.mode.equals("melee") || k.mode.equals("guard");
        if (melee && b.windup > 0 && b.motion() == 8) {
            // an ability wind-up: the weapon's power pose instead of the caster's raised hand
            b.motion(power(k), b.windup + 24);
        }
        boolean ready = now >= d.getLong("ororSwingAt") && b.windup == 0;
        if (melee) {
            double reach = 2.0 + k.reach * 0.8 + (b.getBbWidth() + t.getBbWidth()) * 0.5;
            boolean walker = !b.spec.airborne() && !b.spec.aquatic() && !b.spec.model.equals("tree");
            if (walker && dist > reach * 0.8 && dist < 10.0) {
                // the base AI stops nine blocks off: walk the rest of the way into reach
                b.getMoveControl().setWantedPosition(t.getX(), t.getY(), t.getZ(), 1.1);
            }
            if (ready && dist <= reach && b.getSensing().hasLineOfSight(t)) {
                swing(b, sl, t, k, awake, color, d, now);
            }
        } else if (ready && dist <= 22.0 && b.getSensing().hasLineOfSight(t)) {
            int n = d.getInt("ororShots") + 1;
            d.putInt("ororShots", n);
            int gap = switch (k.mode) {
                case "gatling" -> n % 6 == 0 ? 36 : 3;
                case "shell" -> 60;
                case "bow" -> 30;
                default -> 26;
            };
            d.putLong("ororSwingAt", now + (long) Math.max(3, awake ? gap * 2 / 3 : gap));
            fire(b, sl, t, k, damage(b, k.shot), color, n % 4 == 0);
        }
    }

    /** One melee blow. */
    private static void swing(SupremeEntity b, ServerLevel sl, LivingEntity t, CharacterRelics.Kind k, boolean awake, int color, CompoundTag d, long now) {
        int n = d.getInt("ororSwings") + 1;
        d.putInt("ororSwings", n);
        // the kind's attack speed (player swings a second), a little slower for a character
        double perSecond = Math.max(0.8, 4.0 + k.speed);
        int gap = (int) Math.max(5L, Math.round(20.0 / perSecond * (awake ? 1.2 : 1.6)));
        d.putLong("ororSwingAt", now + gap);
        boolean fist = k.id.equals("fist");
        boolean heavy = fist ? n % 3 == 0 : n % 4 == 0;
        int motion = switch (k.id) {
            case "fist" -> heavy ? 3 : 2;
            case "rapier", "polearm", "shield" -> 2;
            case "heavy", "greatsword", "toyhammer" -> n % 2 == 0 ? 7 : 3;
            default -> n % 2 == 0 ? 5 : 1;
        };
        b.motion(motion, (int) Math.min(14L, Math.max(6L, gap)));
        b.swing(InteractionHand.MAIN_HAND);
        float dmg = damage(b, k.mul) * (heavy ? 1.6F : 1.0F);
        BossPowers.hit(b, t, dmg);
        Vec3 at = t.position().add(0.0, t.getBbHeight() * 0.5, 0.0);
        DustParticleOptions dust = RelicEffects.dust(color, 1.2F);
        sl.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, heavy ? 12 : 5, 0.25, 0.3, 0.25, 0.3);
        sl.sendParticles(dust, at.x, at.y, at.z, 6, 0.3, 0.3, 0.3, 0.0);
        switch (k.id) {
            case "fist", "rapier", "polearm", "shield" -> RelicEffects.line(sl, b.getEyePosition().add(0.0, -0.4, 0.0), at, dust, 0.25);
            case "heavy", "greatsword", "toyhammer" -> RelicEffects.circle(sl, t.position().add(0.0, 0.1, 0.0), heavy ? 2.5 : 1.5, dust);
            default -> RelicEffects.arc(sl, b, 2.2, n % 2 == 0 ? -0.4 : 0.4, dust, ParticleTypes.CRIT);
        }
        if (heavy) {
            if (!(t instanceof SupremeEntity)) {
                BossPowers.push(t, BossPowers.flat(t.position().subtract(b.position())).scale(0.9).add(0.0, 0.3, 0.0));
            }
            sl.sendParticles(ParticleTypes.POOF, at.x, at.y, at.z, 10, 0.3, 0.3, 0.3, 0.08);
            RelicEffects.sound(sl, t.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.0F, fist ? 0.8F : 0.6F);
        } else {
            RelicEffects.sound(sl, t.blockPosition(), fist ? SoundEvents.PLAYER_ATTACK_CRIT : SoundEvents.PLAYER_ATTACK_SWEEP, 0.8F, fist ? 1.3F : 1.0F);
        }
    }

    /**
     * One shot of a shooting kind: a bolt (a great bolt bursts around the target), a round, a light shot or an exploding
     * shell. Also used by AdaptiveCombat for characters in lore mode.
     */
    static void fire(SupremeEntity b, ServerLevel sl, LivingEntity t, CharacterRelics.Kind k, float dmg, int color, boolean great) {
        DustParticleOptions dust = RelicEffects.dust(color, k.mode.equals("shell") ? 2.0F : 1.2F);
        switch (k.mode) {
            case "gatling" -> {
                if (b.motion() == 0) {
                    b.motion(8, 12);
                }
                BossPowers.bolt(b, sl, t, dmg, dust, true);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, 0.5F, 1.7F);
            }
            case "shell" -> {
                b.motion(8, 14);
                shell(b, sl, t, dmg, dust);
            }
            case "bow" -> {
                b.motion(8, 12);
                BossPowers.bolt(b, sl, t, dmg, dust, false);
                t.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.GLOWING, 80, 0));
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ARROW_SHOOT, 1.0F, 1.2F);
            }
            default -> {
                b.motion(8, 10);
                BossPowers.bolt(b, sl, t, great ? dmg * 2.5F : dmg, dust, false);
                if (great) {
                    Vec3 at = t.position().add(0.0, t.getBbHeight() * 0.5, 0.0);
                    for (LivingEntity e : BossPowers.enemies(b, at, 3.0)) {
                        if (e != t) {
                            BossPowers.hit(b, e, dmg);
                        }
                    }
                    RelicEffects.burst(sl, at, dust, 30, 0.9, 0.0);
                    RelicEffects.shock(sl, at, 20, ParticleTypes.END_ROD, 0.3);
                    RelicEffects.sound(sl, t.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, 1.0F, 1.5F);
                } else {
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F, 1.4F);
                }
            }
        }
    }

    /** A shell: flies straight from the eyes, bursts on the target or the first wall, hitting everything within 3 blocks. */
    private static void shell(SupremeEntity b, ServerLevel sl, LivingEntity t, float dmg, DustParticleOptions dust) {
        Vec3 a = b.getEyePosition();
        Vec3 end = t.position().add(0.0, t.getBbHeight() * 0.5, 0.0);
        var wall = sl.clip(new ClipContext(a, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, b));
        if (wall.getType() != HitResult.Type.MISS) {
            end = wall.getLocation();
        }
        RelicEffects.line(sl, a, end, ParticleTypes.LARGE_SMOKE, 0.6);
        RelicEffects.line(sl, a, end, dust, 0.4);
        for (LivingEntity e : BossPowers.enemies(b, end, 3.0)) {
            BossPowers.hit(b, e, dmg);
            if (!(e instanceof SupremeEntity)) {
                BossPowers.push(e, BossPowers.flat(e.position().subtract(end)).scale(0.7).add(0.0, 0.5, 0.0));
            }
        }
        sl.sendParticles(ParticleTypes.EXPLOSION, end.x, end.y, end.z, 3, 0.6, 0.6, 0.6, 0.0);
        RelicEffects.burst(sl, end, dust, 24, 1.0, 0.0);
        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.WITHER_SHOOT, 0.6F, 1.4F);
        RelicEffects.sound(sl, BlockPos.containing(end), SoundEvents.FIREWORK_ROCKET_BLAST, 1.6F, 0.6F);
    }

    /** The pose a melee character's ability wind-up takes. */
    private static int power(CharacterRelics.Kind k) {
        return switch (k.id) {
            case "fist", "heavy", "greatsword", "toyhammer" -> 3;
            case "rapier", "polearm", "shield" -> 2;
            case "scythe" -> 5;
            default -> 1;
        };
    }

    /** Basic attacks hit for a share of the character's attack (abilities and moves stay the big hits). */
    private static float damage(SupremeEntity b, float mul) {
        return (float) (b.getAttributeValue(Attributes.ATTACK_DAMAGE) * mul * 0.45 * (Double) RebornConfig.DAMAGE.get());
    }
}
