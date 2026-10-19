package jp.oror.reborn;

import java.util.Comparator;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Holder.Reference;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.ClipContext.Block;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

public final class Abilities {
    public static boolean melee(String id) {
        return Set.of("kokuhaku", "taika", "mels", "hakyoku", "shinra", "eomaia", "brutality", "fallen_savior").contains(id);
    }

    public static void burst(SupremeEntity b, SimpleParticleType p, int n) {
        if (b.level() instanceof ServerLevel sl) {
            sl.sendParticles(p, b.getX(), b.getY() + (double)b.getBbHeight() * 0.6, b.getZ(), n, 0.8, 0.8, 0.8, 0.02);
        }
    }

    public static List<LivingEntity> enemies(SupremeEntity b, double r) {
        return b.level()
            .getEntitiesOfClass(LivingEntity.class, b.getBoundingBox().inflate(r), b::validEnemy)
            .stream()
            .sorted(Comparator.comparingDouble(b::distanceToSqr))
            .limit(24L)
            .toList();
    }

    private static void hit(SupremeEntity b, LivingEntity t, float f) {
        if (b.validEnemy(t)) {
            LorePowers.strike(b, t, (float)(b.getAttributeValue(Attributes.ATTACK_DAMAGE) * (double)f * (Double)RebornConfig.DAMAGE.get()), false);
        }
    }

    private static void concept(SupremeEntity b, LivingEntity t, float f) {
        if (b.validEnemy(t)) {
            if (b.lore()) {
                LorePowers.strike(b, t, 1.0F, true);
            } else {
                ResourceKey<DamageType> key = ResourceKey.create(
                    Registries.DAMAGE_TYPE, new ResourceLocation("oror_supreme_bosses", "concept")
                );
                Reference<DamageType> holder = b.level().registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(key);
                t.hurt(new DamageSource(holder, b), (float)(b.getAttributeValue(Attributes.ATTACK_DAMAGE) * (double)f * (Double)RebornConfig.DAMAGE.get()));
            }
        }
    }

    public static void stun(LivingEntity t, int ticks) {
        if (t instanceof Player) {
            t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, ticks, 4));
            t.addEffect(new MobEffectInstance(MobEffects.DIG_SLOWDOWN, ticks, 2));
        } else {
            t.getPersistentData().putLong("ororFreezeUntil", t.level().getGameTime() + (long)ticks);
        }
    }

    private static void effect(LivingEntity t, Holder<MobEffect> e, int ticks, int amp) {
        t.addEffect(new MobEffectInstance(e, ticks, amp));
    }

    private static void knock(SupremeEntity b, LivingEntity t, double s) {
        Vec3 d = t.position().subtract(b.position()).normalize();
        t.setDeltaMovement(d.scale(s).add(0.0, 0.25, 0.0));
        t.hurtMarked = true;
    }

    private static void area(SupremeEntity b, double r, float f) {
        for (LivingEntity e : enemies(b, r)) {
            hit(b, e, f);
            knock(b, e, 0.8);
        }

        burst(b, ParticleTypes.EXPLOSION, 8);
    }

    private static void line(SupremeEntity b, ServerLevel sl, LivingEntity t, float f, SimpleParticleType p) {
        Vec3 start = b.getEyePosition();
        Vec3 delta = t.getEyePosition().subtract(start);
        double len = Math.min(32.0, delta.length());
        Vec3 dir = delta.normalize();
        BlockHitResult ray = sl.clip(new ClipContext(start, start.add(dir.scale(len)), Block.COLLIDER, Fluid.NONE, b));
        len = Math.min(len, ray.getLocation().distanceTo(start));

        for (double n = 0.0; n < len; n += 0.8) {
            Vec3 v = start.add(dir.scale(n));
            sl.sendParticles(p, v.x, v.y, v.z, 1, 0.0, 0.0, 0.0, 0.0);
        }

        double reach = len;

        for (LivingEntity e : enemies(b, 34.0)) {
            Vec3 d = e.getBoundingBox().getCenter().subtract(start);
            double along = d.dot(dir);
            if (along >= 0.0 && along <= reach + 1.0 && d.subtract(dir.scale(along)).length() < (double)e.getBbWidth() * 0.5 + 1.0) {
                hit(b, e, f);
            }
        }
    }

    public static boolean blink(SupremeEntity b, Vec3 v) {
        BlockPos p = BlockPos.containing(v);
        if (b.level().hasChunkAt(p)
            && !(v.y < (double)(b.level().getMinBuildHeight() + 1))
            && !(v.y > (double)((float)b.level().getMaxBuildHeight() - b.getBbHeight()))
            && b.level().getWorldBorder().isWithinBounds(p)
            && b.level().noCollision(b, b.getBoundingBox().move(v.subtract(b.position())))) {
            b.teleportTo(v.x, v.y, v.z);
            burst(b, ParticleTypes.PORTAL, 12);
            return true;
        } else {
            return false;
        }
    }

    private static void repair(SupremeEntity b) {
        if (b.owner != null && b.level() instanceof ServerLevel sl && sl.getEntity(b.owner) instanceof Player p && b.distanceTo(p) < 8.0F) {
            for (ItemStack i : p.getAllSlots()) {
                if (i.isDamageableItem()) {
                    i.setDamageValue(Math.max(0, i.getDamageValue() - 8));
                }
            }
        }
    }

    private static void reflect(SupremeEntity b, boolean erase) {
        for (Projectile p : b.level()
            .getEntitiesOfClass(
                Projectile.class,
                b.getBoundingBox().inflate(8.0),
                px -> px.getOwner() != b && (!(px.getOwner() instanceof LivingEntity owner) || !b.ally(owner))
            )) {
            if (erase) {
                p.discard();
            } else {
                p.setDeltaMovement(p.getDeltaMovement().scale(-1.0));
                p.setOwner(b);
                p.hasImpulse = true;
            }
        }
    }

    private static void say(SupremeEntity b, ServerLevel sl, String w) {
        for (ServerPlayer p : sl.players()) {
            if (b.distanceToSqr(p) < 1024.0) {
                p.displayClientMessage(Component.literal(b.spec.name + "：「" + w + "」"), true);
            }
        }
    }

    public static void telegraph(SupremeEntity b, ServerLevel sl, LivingEntity t) {
        if (b.windup % 4 == 0) {
            sl.sendParticles(ParticleTypes.END_ROD, t.getX(), t.getY() + 0.1, t.getZ(), 3, 0.9, 0.1, 0.9, 0.0);
            burst(b, ParticleTypes.ENCHANT, 3);
        }
    }

    public static void passive(SupremeEntity b, ServerLevel sl) {
        String var2 = b.spec.id;
        switch (var2) {
            case "elseria":
            case "savior":
            case "bahamut":
            case "magna_mater":
            case "yggdrasil":
                b.healAllies(2.0F);
                burst(b, ParticleTypes.HAPPY_VILLAGER, 5);
                break;
            case "huang_linghua":
            case "kurma":
                b.heal(6.0F);
                break;
            case "valeria":
            case "ferdinand":
                repair(b);
                break;
            case "hakyoku":
            case "miyohime":
                if (b.tickCount % 400 == 0) {
                    b.evolution = CombatMemory.boundedEvolution(b.evolution + 1);
                }
                break;
            case "angra_mainyu":
                b.mana(b.mana() + (float)(enemies(b, 12.0).stream().filter(e -> {
                    if (e instanceof Enemy) {
                        return true;
                    } else {
                        if (e instanceof Mob m && m.getTarget() != null) {
                            return true;
                        }

                        return false;
                    }
                }).count() * 2L));
                break;
            case "chaos":
                b.setForm(b.form() + 1);
                b.coreOpen = 30;
                burst(b, ParticleTypes.WITCH, 18);
        }
    }

    public static void cast(SupremeEntity b, ServerLevel sl, LivingEntity t) {
        if (b.lore() && b.mana() < 20.0F) {
            b.mana(20.0F);
        }

        if (b.validEnemy(t) && b.spend(20.0F)) {
            b.motion(CharacterArsenal.baseMotion(b), 24);
            OperatorPowers.cast(b, sl, t);
            String var3 = b.spec.id;
            label358:
            switch (var3) {
                case "kokuhaku":
                    reflect(b, false);
                    blink(b, t.position().add(t.position().subtract(b.position()).normalize().scale(-2.0)));
                    line(b, sl, t, 1.8F, ParticleTypes.SOUL_FIRE_FLAME);
                    break;
                case "riha":
                    int w = b.tickCount / b.spec.cooldown % 4;
                    switch (w) {
                        case 0:
                            say(b, sl, "止まれ");
                            stun(t, 55);
                            break label358;
                        case 1:
                            say(b, sl, "治れ");
                            b.heal(30.0F);
                            b.healAllies(15.0F);
                            break label358;
                        case 2:
                            say(b, sl, "退け");
                            hit(b, t, 1.0F);
                            knock(b, t, 2.0);
                            break label358;
                        default:
                            say(b, sl, "死んで");
                            concept(b, t, 3.0F);
                            break label358;
                    }
                case "tenki":
                    reflect(b, true);
                    b.removeAllEffects();
                    b.shield = 80.0F;
                    effect(t, MobEffects.WEAKNESS, 100, 2);
                    concept(b, t, 1.8F);
                    break;
                case "chaos":
                    b.setForm(b.form() + 1);
                    b.coreOpen = 50;

                    for (LivingEntity e : enemies(b, 12.0)) {
                        int n = b.getRandom().nextInt(4);
                        if (n == 0) {
                            effect(e, MobEffects.LEVITATION, 55, 0);
                        }

                        if (n == 1) {
                            effect(e, MobEffects.CONFUSION, 100, 0);
                        }

                        if (n == 2) {
                            stun(e, 35);
                        }

                        if (n == 3) {
                            hit(b, e, 1.4F);
                            knock(b, e, 1.5);
                        }
                    }

                    terrain(b, sl, t.blockPosition(), Blocks.AMETHYST_BLOCK);
                    burst(b, ParticleTypes.WITCH, 36);
                    break;
                case "berit":
                    reflect(b, true);
                    stun(t, 50);
                    terrain(b, sl, t.blockPosition(), Blocks.COPPER_BLOCK);
                    FamiliarEntity.create(b, sl, 0, 1);
                    burst(b, ParticleTypes.WAX_ON, 24);
                    hit(b, t, 1.2F);
                    break;
                case "elseria":
                    line(b, sl, t, 1.5F, ParticleTypes.FLAME);
                    effect(t, MobEffects.MOVEMENT_SLOWDOWN, 80, 2);
                    b.healAllies(12.0F);

                    for (LivingEntity e : enemies(b, 8.0)) {
                        hit(b, e, 1.0F);
                    }
                    break;
                case "valeria":
                    b.shield = (float)Math.min(160, 60 + b.memory.entries().size() * 8);
                    FamiliarEntity.create(b, sl, 0, 2);
                    repair(b);
                    line(b, sl, t, 1.3F, ParticleTypes.CRIT);
                    break;
                case "huang_linghua":
                    b.heal(35.0F);
                    stun(t, 60);
                    area(b, 8.0, 1.5F);
                    effect(t, MobEffects.WEAKNESS, 100, 1);
                    burst(b, ParticleTypes.ELECTRIC_SPARK, 32);
                    break;
                case "ferdinand":
                    FamiliarEntity.create(b, sl, b.tickCount % 3, 2);
                    repair(b);
                    b.shield = 35.0F;
                    line(b, sl, t, 1.0F, ParticleTypes.SMOKE);
                    break;
                case "mels":
                    blink(b, t.position().add(2.0, 0.0, 0.0));
                    stun(t, 20);
                    hit(b, t, 2.0F);
                    area(b, 4.0, 0.8F);
                    b.setForm(b.form() + 1);
                    break;
                case "hephaistos":
                    FamiliarEntity.create(b, sl, 0, 3);
                    b.shield = 100.0F;
                    reflect(b, false);
                    burst(b, ParticleTypes.ELECTRIC_SPARK, 24);
                    break;
                case "nortia":
                    int r = b.tickCount / b.spec.cooldown % 3;

                    say(b, sl, switch (r) {
                        case 0 -> "赤信号！動いたら負け！";
                        case 1 -> "跳べ！床は溶岩だよ！";
                        default -> "鬼ごっこ、追いかけるよ！";
                    });

                    for (LivingEntity e : enemies(b, 14.0)) {
                        CompoundTag n = e.getPersistentData();
                        n.putLong("ororGameUntil", sl.getGameTime() + 60L);
                        n.putInt("ororGameRule", r);
                        n.putDouble("ororGameX", e.getX());
                        n.putDouble("ororGameZ", e.getZ());
                        n.putUUID("ororGameCreator", b.getUUID());
                    }

                    b.shield = 40.0F;
                    break;
                case "lucifara":
                    for (LivingEntity e : enemies(b, 10.0)) {
                        effect(e, MobEffects.CONFUSION, 140, 0);
                        effect(e, MobEffects.WEAKNESS, 120, 1);
                        hit(b, e, 0.8F);
                    }

                    b.heal(15.0F);
                    burst(b, ParticleTypes.DRAGON_BREATH, 28);
                    break;
                case "taika":
                    float s = t.getAttribute(Attributes.ATTACK_DAMAGE) == null ? b.spec.damage : (float)t.getAttributeValue(Attributes.ATTACK_DAMAGE);
                    b.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(Math.min(120.0, Math.max((double)b.spec.damage, (double)s * 1.15)));
                    hit(b, t, 1.8F + Math.min(2.0F, s / 40.0F));
                    area(b, 5.0, 1.0F);
                    break;
                case "mary_sue":
                    b.evolution = CombatMemory.boundedEvolution(b.evolution + 1);
                    b.heal((float)(12 + b.evolution));
                    b.shield = 30.0F;
                    b.setForm(b.form() + 1);
                    blink(b, t.position().add(-3.0, 0.0, 0.0));
                    hit(b, t, 1.3F + Math.min(2.0F, (float)b.evolution * 0.1F));
                    break;
                case "savior":
                    b.healAllies(35.0F);
                    b.shield = 120.0F;

                    for (LivingEntity e : enemies(b, 10.0)) {
                        knock(b, e, 1.3);
                        hit(b, e, 0.7F);
                    }

                    burst(b, ParticleTypes.END_ROD, 28);
                    break;
                case "gokuka":
                    for (LivingEntity e : enemies(b, 12.0)) {
                        effect(e, MobEffects.WITHER, 100, 1);
                        effect(e, MobEffects.POISON, 140, 1);
                        effect(e, MobEffects.WEAKNESS, 100, 1);
                    }

                    FamiliarEntity.create(b, sl, 3, 1);
                    burst(b, ParticleTypes.WITCH, 32);
                    break;
                case "merlinus":
                    reflect(b, false);
                    stun(t, 65);
                    blink(b, b.position().add(b.position().subtract(t.position()).normalize().scale(5.0)));
                    line(b, sl, t, 2.0F, ParticleTypes.PORTAL);
                    break;
                case "enkou":
                    effect(t, MobEffects.DARKNESS, 100, 0);
                    effect(t, MobEffects.POISON, 80, 1);
                    stun(t, 35);
                    area(b, 12.0, b.isInWater() ? 2.2F : 1.2F);
                    burst(b, ParticleTypes.BUBBLE, 24);
                    break;
                case "kurma":
                    b.heal(30.0F);
                    area(b, 14.0, 1.5F);
                    b.shield = 90.0F;
                    terrain(b, sl, t.blockPosition(), Blocks.MOSS_BLOCK);
                    burst(b, ParticleTypes.COMPOSTER, 25);
                    break;
                case "teia":
                    Vec3 d = t.position().add(0.0, 1.0, 0.0);
                    blink(b, d.add(3.0, 1.0, 0.0));
                    line(b, sl, t, 2.0F, ParticleTypes.ELECTRIC_SPARK);
                    blink(b, d.add(-3.0, 2.0, 0.0));
                    break;
                case "bahamut":
                    b.healAllies(30.0F);

                    for (LivingEntity e : enemies(b, 15.0)) {
                        knock(b, e, 1.8);
                        effect(e, MobEffects.MOVEMENT_SLOWDOWN, 80, 2);
                    }

                    line(b, sl, t, 2.0F, ParticleTypes.SPLASH);
                    b.shield = 80.0F;
                    break;
                case "nun":
                    String m = t instanceof SupremeEntity s ? s.spec.model : (t instanceof Animal ? "beast" : "human");

                    b.setForm(switch (m) {
                        case "beast", "sea", "whale" -> 1;
                        case "dragon" -> 2;
                        default -> 3;
                    });
                    b.shield = 50.0F;
                    hit(b, t, 1.5F);
                    reflect(b, false);
                    break;
                case "arcana":
                    b.healAllies(20.0F);
                    reflect(b, false);
                    effect(b, MobEffects.LUCK, 200, 2);
                    b.shield = 60.0F;
                    hit(b, t, 0.9F);
                    break;
                case "eomaia":
                    b.setForm(b.form() + 1);
                    FamiliarEntity.create(b, sl, 1, 3);
                    area(b, 9.0, 1.3F);
                    b.healAllies(10.0F);
                    break;
                case "demiurgos":
                    b.shield = 100.0F;
                    FamiliarEntity.create(b, sl, 2, 2);
                    blink(b, b.position().add(0.0, 2.0, 0.0));
                    line(b, sl, t, 2.2F, ParticleTypes.DRAGON_BREATH);
                    break;
                case "hakyoku":
                    hit(b, t, 1.3F + Math.min(2.0F, (float)b.evolution * 0.04F));
                    b.heal(10.0F);
                    effect(t, MobEffects.WITHER, 60, 0);
                    burst(b, ParticleTypes.SOUL, 25);
                    break;
                case "shinra":
                    b.targetSpecies = BuiltInRegistries.ENTITY_TYPE.getKey(t.getType()).toString();
                    effect(t, MobEffects.WEAKNESS, 100, 2);
                    concept(b, t, 2.5F);
                    b.shield = 50.0F;
                    break;
                case "ain_sof_aur":
                    blink(b, t.position().add(4.0, 0.0, 0.0));
                    b.shield = 80.0F;
                    FamiliarEntity.create(b, sl, 2, 2);
                    concept(b, t, 1.5F);
                    break;
                case "angra_mainyu":
                    for (LivingEntity e : enemies(b, 12.0)) {
                        effect(e, MobEffects.WITHER, 120, 1);
                        effect(e, MobEffects.WEAKNESS, 100, 1);
                        hit(b, e, 1.0F);
                    }

                    b.heal(12.0F);
                    burst(b, ParticleTypes.SOUL, 24);
                    break;
                case "magna_mater":
                    FamiliarEntity.create(b, sl, 1, 3);
                    b.healAllies(30.0F);
                    stun(t, 40);
                    burst(b, ParticleTypes.HAPPY_VILLAGER, 30);
                    break;
                case "ouroboros":
                    b.rewind();
                    stun(t, 70);
                    hit(b, t, 1.4F);
                    burst(b, ParticleTypes.REVERSE_PORTAL, 30);
                    break;
                case "yggdrasil":
                    b.heal(30.0F);
                    b.healAllies(25.0F);

                    for (LivingEntity e : enemies(b, 14.0)) {
                        stun(e, 60);
                        hit(b, e, 1.3F);
                    }

                    FamiliarEntity.create(b, sl, 2, 2);
                    burst(b, ParticleTypes.HAPPY_VILLAGER, 32);
                    break;
                case "miyohime":
                    int l = b.tickCount / b.spec.cooldown % 3;

                    for (LivingEntity e : enemies(b, 14.0)) {
                        if (l == 0) {
                            effect(e, MobEffects.LEVITATION, 70, 1);
                        }

                        if (l == 1) {
                            stun(e, 70);
                        }

                        if (l == 2) {
                            e.removeAllEffects();
                            concept(b, e, 1.7F);
                        }
                    }

                    b.evolution = CombatMemory.boundedEvolution(b.evolution + 1);
                    b.shield = 90.0F;
                    burst(b, ParticleTypes.REVERSE_PORTAL, 32);
                    break;
                case "innocence":
                    say(b, sl, "遊ぶ？");
                    b.shield = 500.0F;
                    b.setForm(b.form() + 1);
                    stun(t, 100);
                    effect(t, MobEffects.LEVITATION, 80, 1);
                    b.rewind();
                    burst(b, ParticleTypes.PORTAL, 36);
                    break;
                case "brutality":
                    b.removeAllEffects();
                    area(b, 12.0, 3.0F);
                    stun(t, 30);
                    hit(b, t, 4.0F);
                    burst(b, ParticleTypes.CRIT, 35);
                    break;
                case "cursed_love":
                    for (LivingEntity v : enemies(b, 18.0)) {
                        CompoundTag n = v.getPersistentData();
                        n.putLong("ororTragedyUntil", sl.getGameTime() + 400L);
                        n.putUUID("ororTragedyCreator", b.getUUID());
                        n.putFloat("ororTragedyHealth", v.getHealth());
                        effect(v, MobEffects.WITHER, 240, 2);
                        effect(v, MobEffects.CONFUSION, 200, 0);
                    }

                    b.heal(30.0F);
                    burst(b, ParticleTypes.WITCH, 32);
                    break;
                case "relentless_research":
                    b.healAllies(80.0F);
                    b.heal(80.0F);
                    FamiliarEntity.create(b, sl, 1, 4);
                    stun(t, 80);
                    effect(t, MobEffects.POISON, 120, 2);
                    burst(b, ParticleTypes.HAPPY_VILLAGER, 25);
                    break;
                case "forbidden_arcana":
                    reflect(b, false);
                    b.setForm(b.form() + 1);
                    stun(t, 100);
                    line(b, sl, t, 4.0F, ParticleTypes.PORTAL);
                    b.shield = 200.0F;
                    break;
                case "fallen_savior":
                    b.heal(b.getMaxHealth());
                    b.removeAllEffects();
                    line(b, sl, t, 4.0F, ParticleTypes.END_ROD);
                    concept(b, t, 5.0F);
                    break;
                case "sweet_pact":
                    b.shield = 300.0F;
                    stun(t, 80);
                    effect(t, MobEffects.WEAKNESS, 240, 3);
                    blink(b, b.position().add(b.position().subtract(t.position()).normalize().scale(8.0)));
                    burst(b, ParticleTypes.ENCHANT, 24);
                    break;
                default:
                    throw new IllegalStateException("Unimplemented " + b.spec.id);
            }

            LorePowers.cast(b, t);
        } else {
            b.cooldown = 30;
        }
    }

    private static void terrain(SupremeEntity b, ServerLevel sl, BlockPos p, net.minecraft.world.level.block.Block r) {
        if ((Boolean)RebornConfig.TERRAIN.get() && sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
            int n = 0;

            for (int x = -2; x <= 2; x++) {
                for (int z = -2; z <= 2; z++) {
                    BlockPos q = p.offset(x, -1, z);
                    if (n < (Integer)RebornConfig.BLOCK_BUDGET.get() && sl.hasChunkAt(q) && sl.getWorldBorder().isWithinBounds(q)) {
                        BlockState s = sl.getBlockState(q);
                        if (!s.hasBlockEntity() && (s.is(Blocks.STONE) || s.is(Blocks.DIRT) || s.is(Blocks.GRASS_BLOCK) || s.is(Blocks.DEEPSLATE))) {
                            sl.setBlock(q, r.defaultBlockState(), 3);
                            n++;
                        }
                    }
                }
            }
        }
    }
}
