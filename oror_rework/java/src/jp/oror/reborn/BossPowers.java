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
 * - five named moves each and a movement style (BossMoves.java, boss_moves.json);
 * - awakening at half health: the legend weapon in hand, a barrier of half its health, a damaging aura and
 *   moves twice as often;
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
        // older worlds (and AdaptiveCombat before v0.17.8) could have swapped the relic for a vanilla weapon
        if (now % 20L == 0L) {
            hold(b, awake ? "_legend" : "_weapon");
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
        BossMoves.tick(b, sl, t, awake, color);
        BossArms.tick(b, sl, t, awake, color);
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

    /** A hitscan shot from the eyes to a target; walls stop it. Gatling rounds spread a little. */
    static void bolt(SupremeEntity b, ServerLevel sl, LivingEntity t, float dmg, DustParticleOptions dust, boolean round) {
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
    static int color(SupremeEntity b) {
        RelicSpec s = RelicSpec.ALL.get(b.spec.id + "_weapon");
        return s != null ? s.color : b.spec.accent;
    }

    static List<LivingEntity> enemies(SupremeEntity b, Vec3 at, double r) {
        return new ArrayList<>(b.level().getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(r),
            e -> e != b && b.validEnemy(e) && e.position().distanceTo(at) <= r));
    }

    /** Enemies within width of the segment a-c: horizontally around its closest point, vertically anywhere on the body. */
    static List<LivingEntity> strip(SupremeEntity b, Vec3 a, Vec3 c, double width) {
        Vec3 d = c.subtract(a);
        double len = d.length();
        Vec3 u = len < 1.0E-4 ? new Vec3(1.0, 0.0, 0.0) : d.scale(1.0 / len);
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity e : b.level().getEntitiesOfClass(LivingEntity.class, new AABB(a, c).inflate(width + 3.0), e -> e != b && b.validEnemy(e))) {
            Vec3 mid = e.position().add(0.0, e.getBbHeight() * 0.5, 0.0);
            double s = Math.max(0.0, Math.min(len, mid.subtract(a).dot(u)));
            Vec3 q = a.add(u.scale(s));
            double dx = q.x - e.getX();
            double dz = q.z - e.getZ();
            boolean level = q.y >= e.getY() - width && q.y <= e.getY() + e.getBbHeight() + width;
            if (level && Math.sqrt(dx * dx + dz * dz) <= width + e.getBbWidth() * 0.5) {
                out.add(e);
            }
        }
        return out;
    }

    static void hit(SupremeEntity b, LivingEntity e, float amount) {
        e.invulnerableTime = 0;
        e.hurt(b.damageSources().mobAttack(b), amount);
    }

    static Vec3 flat(Vec3 v) {
        Vec3 f = new Vec3(v.x, 0.0, v.z);
        return f.lengthSqr() < 1.0E-6 ? new Vec3(1.0, 0.0, 0.0) : f.normalize();
    }

    static void push(LivingEntity e, Vec3 v) {
        e.setDeltaMovement(e.getDeltaMovement().add(v));
        e.hurtMarked = true;
    }

    static void lift(LivingEntity e, double up) {
        if (!(e instanceof SupremeEntity)) {
            push(e, new Vec3(0.0, up, 0.0));
        }
    }
}
