package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.animal.Wolf;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent.Pre;

public final class RelicPowers {
    private static final Set<String> HEALERS = Set.of("savior", "arcana", "magna_mater", "yggdrasil", "bahamut", "mary_sue", "relentless_research", "innocence");
    private static final Set<String> MAKERS = Set.of("berit", "valeria", "ferdinand", "hephaistos");

    public static boolean shielded(LivingEntity e) {
        if (!(e instanceof Player p)) {
            return false;
        } else {
            RelicSpec a = CharacterRelics.of(p.getMainHandItem());
            RelicSpec b = CharacterRelics.of(p.getOffhandItem());
            return a != null && a.rank == 3 || b != null && b.rank == 3;
        }
    }

    public static boolean enemy(Player p, LivingEntity e) {
        if (e == p
            || !e.isAlive()
            || e.isSpectator()
            || e.isAlliedTo(p)
            || e instanceof Player q && q.isCreative()
            || e.getPersistentData().hasUUID("ororRelicOwner") && p.getUUID().equals(e.getPersistentData().getUUID("ororRelicOwner"))) {
            return false;
        } else {
            if (e instanceof SupremeEntity b) {
                return !p.getUUID().equals(b.owner) && (b.arena || b.getTarget() == p);
            }

            if (e instanceof Enemy) {
                return true;
            } else {
                if (e instanceof Mob m && m.getTarget() == p) {
                    return true;
                }

                return false;
            }
        }
    }

    private static List<LivingEntity> targets(Player p, int rank) {
        return p.level()
            .getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate((double)(8 + rank * 4)), e -> enemy(p, e))
            .stream()
            .sorted(Comparator.comparingDouble(p::distanceToSqr))
            .limit(24L)
            .toList();
    }

    private static void effect(LivingEntity e, Holder<MobEffect> type, int time, int amp) {
        e.addEffect(new MobEffectInstance(type, time, amp));
    }

    public static void cleanse(LivingEntity e) {
        for (MobEffectInstance v : new ArrayList<MobEffectInstance>(e.getActiveEffects())) {
            if (!((MobEffect)v.getEffect().value()).isBeneficial()) {
                e.removeEffect(v.getEffect());
            }
        }
    }

    private static void healFriends(Player p, float amount) {
        p.heal(amount);

        for (LivingEntity e : p.level()
            .getEntitiesOfClass(
                LivingEntity.class,
                p.getBoundingBox().inflate(14.0),
                v -> v instanceof Player q && !enemy(p, q)
                        || v instanceof SupremeEntity b && p.getUUID().equals(b.owner)
                        || v.getPersistentData().hasUUID("ororRelicOwner") && p.getUUID().equals(v.getPersistentData().getUUID("ororRelicOwner"))
            )) {
            e.heal(amount);
            cleanse(e);
        }
    }

    private static void hit(RelicSpec s, Player p, LivingEntity e) {
        float damage = s.rank == 3 ? 1000000.0F : (float)(2000 * s.rank);
        if (e instanceof SupremeEntity b) {
            RelicDrops.fracture(b, p, damage);
        }

        e.hurt(p.damageSources().playerAttack(p), damage);
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

    private static void blink(Player p, Vec3 at) {
        Level l = p.level();
        if (l.hasChunkAt(BlockPos.containing(at))
            && l.getWorldBorder().isWithinBounds(BlockPos.containing(at))
            && l.noCollision(p, p.getBoundingBox().move(at.subtract(p.position())))) {
            p.teleportTo(at.x, at.y, at.z);
        }
    }

    public static void cast(RelicSpec s, Player p) {
        if (p.level() instanceof ServerLevel sl) {
            RelicEffects.show(sl, p, s.color, s.rank);
            List<LivingEntity> var12 = targets(p, s.rank);
            int r = s.rank;
            int time = 60 + r * 40;
            String var6 = s.character;
            switch (var6) {
                case "kokuhaku":
                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                        Abilities.stun(e, 20 * r);
                    }

                    if (!var12.isEmpty()) {
                        blink(p, ((LivingEntity)var12.getFirst()).position().add(-2.0, 0.0, 0.0));
                    }

                    eraseProjectiles(p);
                    break;
                case "riha":
                    CompoundTag n = p.getPersistentData();
                    int word = n.getInt("ororRelicWord") % 4;
                    n.putInt("ororRelicWord", word + 1);
                    p.displayClientMessage(Component.literal(s.name + "：「" + new String[]{"止まれ", "治れ", "退け", "死んで"}[word] + "」"), true);

                    for (LivingEntity e : var12) {
                        if (word == 0) {
                            Abilities.stun(e, time);
                        }

                        if (word == 2) {
                            knock(p, e, 2.0);
                        }

                        if (word == 3) {
                            hit(s, p, e);
                        }
                    }

                    if (word == 1) {
                        healFriends(p, (float)(20 * r));
                    }
                    break;
                case "tenki":
                    cleanse(p);
                    eraseProjectiles(p);

                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.WEAKNESS, time, 4);
                        hit(s, p, e);
                    }

                    effect(p, MobEffects.ABSORPTION, time, 4 * r);
                    break;
                case "chaos":
                    for (LivingEntity e : var12) {
                        switch (sl.random.nextInt(4)) {
                            case 0:
                                effect(e, MobEffects.LEVITATION, time, r);
                                break;
                            case 1:
                                effect(e, MobEffects.CONFUSION, time, 0);
                                break;
                            case 2:
                                Abilities.stun(e, time);
                                break;
                            default:
                                hit(s, p, e);
                        }
                    }

                    effect(p, MobEffects.LUCK, time, r);
                    break;
                case "berit":
                    repair(p, 64 * r);
                    p.getInventory().add(new ItemStack(r == 3 ? Items.DIAMOND : Items.GOLD_INGOT, r * 2));

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        hit(s, p, e);
                    }
                    break;
                case "elseria":
                    healFriends(p, (float)(10 * r));

                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.MOVEMENT_SLOWDOWN, time, r);
                        hit(s, p, e);
                        sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, e.getX(), e.getY() + 1.0, e.getZ(), 20, 1.0, 1.0, 1.0, 0.1);
                    }
                    break;
                case "valeria":
                    repair(p, 128 * r);
                    summon(p, r, false);
                    effect(p, MobEffects.ABSORPTION, time, 3 * r);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "huang_linghua":
                    healFriends(p, (float)(20 * r));

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        effect(e, MobEffects.WEAKNESS, time, r);
                        hit(s, p, e);
                    }
                    break;
                case "ferdinand":
                    repair(p, 64 * r);
                    summon(p, r, false);
                    p.getInventory().add(new ItemStack(Items.REDSTONE, r * 4));

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "mels":
                    for (LivingEntity e : var12) {
                        Abilities.stun(e, 30 * r);
                        hit(s, p, e);
                        knock(p, e, (double)(1 + r));
                    }

                    effect(p, MobEffects.DAMAGE_RESISTANCE, time, 3);
                    break;
                case "hephaistos":
                    repair(p, 256 * r);
                    summon(p, r + 1, false);
                    effect(p, MobEffects.ABSORPTION, time, 5 * r);
                    break;
                case "nortia":
                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        effect(e, MobEffects.LEVITATION, 40, 0);
                        hit(s, p, e);
                    }

                    healFriends(p, (float)(12 * r));
                    p.displayClientMessage(Component.literal("ノルティア：罰ゲーム！もう一回遊ぼう！"), true);
                    break;
                case "lucifara":
                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.CONFUSION, time, 0);
                        effect(e, MobEffects.WEAKNESS, time, 3);
                        hit(s, p, e);
                    }

                    healFriends(p, (float)(15 * r));
                    break;
                case "taika":
                    effect(p, MobEffects.DAMAGE_BOOST, time, 5 * r);
                    effect(p, MobEffects.MOVEMENT_SPEED, time, r);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                        knock(p, e, (double)(2 * r));
                    }
                    break;
                case "mary_sue":
                    cleanse(p);
                    p.heal(p.getMaxHealth());
                    effect(p, MobEffects.ABSORPTION, time, 5 * r);
                    effect(p, MobEffects.DAMAGE_BOOST, time, 3 * r);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "savior":
                    healFriends(p, (float)(40 * r));
                    cleanse(p);
                    effect(p, MobEffects.DAMAGE_RESISTANCE, time, 4);

                    for (LivingEntity e : var12) {
                        knock(p, e, 3.0);
                    }
                    break;
                case "gokuka":
                    summon(p, 1, true);

                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.WITHER, time, 3 * r);
                        effect(e, MobEffects.POISON, time, 3 * r);
                        effect(e, MobEffects.WEAKNESS, time, 3);
                        hit(s, p, e);
                    }
                    break;
                case "merlinus":
                    eraseProjectiles(p);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        hit(s, p, e);
                    }

                    blink(p, p.position().add(p.getLookAngle().scale(-5.0)));
                    break;
                case "enkou":
                    effect(p, MobEffects.WATER_BREATHING, time, 0);

                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.DARKNESS, time, 0);
                        effect(e, MobEffects.POISON, time, r * 2);
                        hit(s, p, e);
                        knock(p, e, (double)r);
                    }
                    break;
                case "kurma":
                    healFriends(p, (float)(20 * r));
                    effect(p, MobEffects.DAMAGE_RESISTANCE, time, 4);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                        knock(p, e, (double)(r * 2));
                    }
                    break;
                case "teia":
                    eraseProjectiles(p);
                    blink(p, p.position().add(p.getLookAngle().scale((double)(8 + r * 3))));
                    effect(p, MobEffects.MOVEMENT_SPEED, time, 4 * r);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "bahamut":
                    healFriends(p, (float)(30 * r));
                    effect(p, MobEffects.WATER_BREATHING, time, 0);
                    effect(p, MobEffects.DOLPHINS_GRACE, time, r);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                        knock(p, e, 3.0);
                    }
                    break;
                case "nun":
                    effect(p, MobEffects.DAMAGE_BOOST, time, r * 3);
                    effect(p, MobEffects.MOVEMENT_SPEED, time, r);
                    effect(p, MobEffects.DAMAGE_RESISTANCE, time, 3);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "arcana":
                    healFriends(p, (float)(20 * r));
                    eraseProjectiles(p);
                    effect(p, MobEffects.LUCK, time, 5 * r);
                    effect(p, MobEffects.ABSORPTION, time, 4 * r);
                    break;
                case "eomaia":
                    summon(p, r, true);
                    effect(p, MobEffects.DAMAGE_BOOST, time, 4 * r);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, 30);
                        hit(s, p, e);
                    }
                    break;
                case "demiurgos":
                    summon(p, r, false);
                    effect(p, MobEffects.ABSORPTION, time, r * 5);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "hakyoku":
                    p.getPersistentData().putLong("ororRelicAdaptUntil", sl.getGameTime() + (long)time);
                    healFriends(p, (float)(20 * r));

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "shinra":
                    p.getPersistentData().putLong("ororRelicAdaptUntil", sl.getGameTime() + (long)time);

                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.WEAKNESS, time, 5);
                        hit(s, p, e);
                    }
                    break;
                case "ain_sof_aur":
                    summon(p, r, false);
                    effect(p, MobEffects.LUCK, time, 5);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, 40);
                        hit(s, p, e);
                    }

                    blink(p, p.position().add(p.getLookAngle().scale(6.0)));
                    break;
                case "angra_mainyu":
                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.WITHER, time, r * 4);
                        effect(e, MobEffects.WEAKNESS, time, 4);
                        hit(s, p, e);
                    }

                    healFriends(p, (float)(20 * r));
                    break;
                case "magna_mater":
                    healFriends(p, (float)(40 * r));
                    summon(p, r + 1, true);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                    }
                    break;
                case "ouroboros":
                    CompoundTag n2 = p.getPersistentData();
                    if (n2.contains("ororRelicPrevHP")) {
                        p.heal(Math.max(0.0F, n2.getFloat("ororRelicPrevHP") - p.getHealth()));
                    }

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        hit(s, p, e);
                    }

                    p.heal((float)(20 * r));
                    break;
                case "yggdrasil":
                    healFriends(p, (float)(40 * r));
                    summon(p, r, true);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        hit(s, p, e);
                    }
                    break;
                case "miyohime":
                    cleanse(p);

                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.LEVITATION, time, r * 2);
                        Abilities.stun(e, time);
                        hit(s, p, e);
                    }

                    effect(p, MobEffects.DAMAGE_RESISTANCE, time, 4);
                    break;
                case "innocence":
                    p.heal(p.getMaxHealth());
                    cleanse(p);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        effect(e, MobEffects.LEVITATION, time, r);
                        hit(s, p, e);
                    }
                    break;
                case "brutality":
                    cleanse(p);
                    effect(p, MobEffects.DAMAGE_BOOST, time, 8 * r);

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                        knock(p, e, (double)(r * 3));
                    }
                    break;
                case "cursed_love":
                    for (LivingEntity e : var12) {
                        effect(e, MobEffects.WITHER, time, 5 * r);
                        effect(e, MobEffects.CONFUSION, time, 0);
                        hit(s, p, e);
                    }

                    healFriends(p, (float)(20 * r));
                    break;
                case "relentless_research":
                    healFriends(p, (float)(40 * r));
                    summon(p, r, true);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        effect(e, MobEffects.POISON, time, 5 * r);
                        hit(s, p, e);
                    }
                    break;
                case "forbidden_arcana":
                    eraseProjectiles(p);
                    p.getPersistentData().putLong("ororRelicAdaptUntil", sl.getGameTime() + (long)time);

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                        hit(s, p, e);
                    }
                    break;
                case "fallen_savior":
                    cleanse(p);
                    p.heal(p.getMaxHealth());

                    for (LivingEntity e : var12) {
                        hit(s, p, e);
                    }
                    break;
                case "sweet_pact":
                    p.heal(p.getMaxHealth());
                    p.getFoodData().setFoodLevel(20);
                    p.getInventory().add(new ItemStack(Items.EMERALD, 4 * r));
                    CompoundTag n3 = p.getPersistentData();
                    if (n3.getInt("ororPactDebt") < Integer.MAX_VALUE) {
                        n3.putInt("ororPactDebt", n3.getInt("ororPactDebt") + 1);
                    }

                    for (LivingEntity e : var12) {
                        Abilities.stun(e, time);
                    }

                    p.displayClientMessage(Component.literal("未来の富を得た。契約の負債が1件増えた。"), true);
                    break;
                default:
                    throw new IllegalStateException("No relic power " + s.character);
            }

            p.getPersistentData().putInt("ororRelicCasts", p.getPersistentData().getInt("ororRelicCasts") + 1);
        }
    }

    public static void passive(RelicSpec s, Player p) {
        int r = s.rank;
        effect(p, MobEffects.DAMAGE_RESISTANCE, 40, r == 3 ? 4 : 2);
        effect(p, MobEffects.DAMAGE_BOOST, 40, r == 3 ? 10 : 2);
        if (r == 3) {
            p.heal(10.0F);
            cleanse(p);
        }

        if (HEALERS.contains(s.character)) {
            healFriends(p, (float)(r * 3));
            effect(p, MobEffects.REGENERATION, 40, r);
        }

        if (MAKERS.contains(s.character)) {
            repair(p, 8 * r);
        }

        String var3 = s.character;
        switch (var3) {
            case "teia":
            case "taika":
            case "mels":
            case "brutality":
                effect(p, MobEffects.MOVEMENT_SPEED, 40, r * 2);
                break;
            case "enkou":
            case "bahamut":
                effect(p, MobEffects.WATER_BREATHING, 40, 0);
                effect(p, MobEffects.DOLPHINS_GRACE, 40, r);
                break;
            case "hakyoku":
            case "shinra":
            case "forbidden_arcana":
                p.getPersistentData().putLong("ororRelicAdaptUntil", p.level().getGameTime() + 40L);
                break;
            case "arcana":
            case "ain_sof_aur":
            case "riha":
                effect(p, MobEffects.LUCK, 40, 5 * r);
                break;
            case "huang_linghua":
            case "kurma":
            case "tenki":
                effect(p, MobEffects.ABSORPTION, 40, 3 * r);
                break;
            case "ouroboros":
                p.getPersistentData().putFloat("ororRelicPrevHP", p.getHealth());
        }
    }

    private static void knock(Player p, LivingEntity e, double strength) {
        e.setDeltaMovement(e.position().subtract(p.position()).normalize().scale(strength).add(0.0, 0.4, 0.0));
        e.hurtMarked = true;
    }

    private static void eraseProjectiles(Player p) {
        for (Projectile e : p.level()
            .getEntitiesOfClass(
                Projectile.class,
                p.getBoundingBox().inflate(12.0),
                ex -> ex.getOwner() != p && (!(ex.getOwner() instanceof LivingEntity owner) || enemy(p, owner))
            )) {
            e.discard();
        }
    }

    private static void summon(Player p, int count, boolean beast) {
        if (p.level() instanceof ServerLevel sl) {
            int var9 = SummonBudget.remaining(sl, p.getUUID(), 4, count);

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

    public static void summonedTick(Pre e) {
        Entity v = e.getEntity();
        if (v instanceof SupremeEntity boss && v.tickCount % 40 == 7 && !v.level().isClientSide) {
            RelicArts.equip(boss);
        }
        if (!(v.level() instanceof ServerLevel sl) || !v.getPersistentData().hasUUID("ororRelicOwner")) {
            return;
        }

        if (sl.getGameTime() >= v.getPersistentData().getLong("ororRelicExpire")) {
            v.discard();
        } else {
            if (v instanceof Mob m && v.tickCount % 20 == 0 && sl.getEntity(v.getPersistentData().getUUID("ororRelicOwner")) instanceof Player p) {
                m.setTarget(targets(p, 3).stream().findFirst().orElse(null));
            }
        }
    }

    public static void damage(LivingIncomingDamageEvent e) {
        if (!e.getEntity().level().isClientSide && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            if (RelicArts.incoming(e)) {
                return;
            }
            Entity attacker = e.getSource().getEntity();
            if (attacker != null
                && attacker.getPersistentData().hasUUID("ororRelicOwner")
                && attacker.getPersistentData().getUUID("ororRelicOwner").equals(e.getEntity().getUUID())) {
                e.setCanceled(true);
            } else if (shielded(e.getEntity())) {
                e.setCanceled(true);
            } else {
                if (e.getEntity() instanceof Player p && p.getPersistentData().getLong("ororRelicAdaptUntil") > p.level().getGameTime()) {
                    String kind = e.getSource().getMsgId();
                    CompoundTag n = p.getPersistentData().getCompound("ororRelicAdaptation");
                    if (n.getBoolean(kind)) {
                        e.setCanceled(true);
                    } else {
                        n.putBoolean(kind, true);
                        p.getPersistentData().put("ororRelicAdaptation", n);
                    }
                }
            }
        }
    }
}
