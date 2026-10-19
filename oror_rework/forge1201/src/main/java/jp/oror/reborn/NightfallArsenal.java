package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.Item.Properties;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ClipContext.Block;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.registries.RegistryObject;

public final class NightfallArsenal {
    public static final List<RegistryObject<?>> CONTENT = new ArrayList<>();
    public static final RegistryObject<Item> RAPIER = add(OrorReborn.ITEMS.register("reverie_rapier", () -> new NightfallArsenal.Blade()));
    public static final RegistryObject<Item> PARRY = gear("parry_emblem", 0);
    public static final RegistryObject<Item> DODGE = gear("dodge_talon", 1);
    public static final RegistryObject<Item> BANNER = gear("squad_banner", 2);
    public static final RegistryObject<Item> BLOOM = gear("last_bloom", 3);

    private static <T extends Item> RegistryObject<T> add(RegistryObject<T> item) {
        CONTENT.add(item);
        return item;
    }

    private static RegistryObject<Item> gear(String id, int kind) {
        return add(OrorReborn.ITEMS.register(id, () -> new NightfallArsenal.Gear(kind)));
    }

    private static boolean enemy(Player p, LivingEntity e) {
        return e != p
            && e.isAlive()
            && !e.isAlliedTo(p)
            && !e.isSpectator()
            && (!(e instanceof Player q) || !q.isCreative())
            && (e instanceof Enemy || e instanceof Mob m && m.getTarget() == p);
    }

    private static void particles(ServerLevel sl, Player p) {
        sl.sendParticles(ParticleTypes.END_ROD, p.getX(), p.getY() + 1.0, p.getZ(), 20, 0.5, 0.5, 0.5, 0.02);
    }

    public static void damage(LivingHurtEvent e) {
        if (e.getEntity() instanceof Player p && p.level() instanceof ServerLevel sl && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            if (p.getPersistentData().getLong("OrorParryUntil") > sl.getGameTime()) {
                e.setCanceled(true);
                p.getPersistentData().remove("OrorParryUntil");
                if (e.getSource().getEntity() instanceof LivingEntity attacker && enemy(p, attacker)) {
                    attacker.hurt(p.damageSources().playerAttack(p), 256.0F);
                }

                particles(sl, p);
            } else if (p.getOffhandItem().is((Item)BLOOM.get()) && !p.getCooldowns().isOnCooldown((Item)BLOOM.get()) && e.getAmount() >= p.getHealth()) {
                e.setCanceled(true);
                p.setHealth(Math.min(p.getMaxHealth(), 12.0F));
                p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 300, 4));
                p.getCooldowns().addCooldown((Item)BLOOM.get(), 3600);
                particles(sl, p);
            }

            return;
        }
    }

    private NightfallArsenal() {
    }

    public static final class Blade extends SwordItem {
        Blade() {
            super(
                Tiers.NETHERITE, 72, -1.8F,
                new Properties().durability(6144).fireResistant().rarity(Rarity.EPIC)
            );
        }

        public InteractionResultHolder<ItemStack> use(Level world, Player p, InteractionHand hand) {
            ItemStack stack = p.getItemInHand(hand);
            if (p.getCooldowns().isOnCooldown(this)) {
                return InteractionResultHolder.fail(stack);
            } else {
                if (world instanceof ServerLevel sl) {
                    for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(4.0), ex -> NightfallArsenal.enemy(p, ex))) {
                        if (p.hasLineOfSight(e)) {
                            e.hurt(
                                p.damageSources().playerAttack(p),
                                (double)e.getHealth() < (double)e.getMaxHealth() * 0.35 ? Math.min(1000000.0F, e.getMaxHealth() * 3.0F) : 192.0F
                            );
                        }
                    }

                    stack.hurtAndBreak(3, p, x -> x.broadcastBreakEvent(hand));
                    p.getCooldowns().addCooldown(this, 50);
                    NightfallArsenal.particles(sl, p);
                }

                return InteractionResultHolder.sidedSuccess(stack, world.isClientSide);
            }
        }
    }

    public static final class Gear extends Item {
        private final int kind;

        Gear(int kind) {
            super(new Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant());
            this.kind = kind;
        }

        public InteractionResultHolder<ItemStack> use(Level world, Player p, InteractionHand hand) {
            ItemStack stack = p.getItemInHand(hand);
            if (p.getCooldowns().isOnCooldown(this)) {
                return InteractionResultHolder.fail(stack);
            } else {
                if (world instanceof ServerLevel sl) {
                    if (this.kind == 0) {
                        p.getPersistentData().putLong("OrorParryUntil", sl.getGameTime() + 20L);
                        p.getCooldowns().addCooldown(this, 100);
                    } else if (this.kind == 1) {
                        Vec3 direction = p.getLookAngle().multiply(1.0, 0.0, 1.0).normalize();
                        Vec3 end = p.position().add(direction.scale(4.0));
                        BlockHitResult hit = sl.clip(
                            new ClipContext(p.getEyePosition(), p.getEyePosition().add(direction.scale(4.0)), Block.COLLIDER, Fluid.NONE, p)
                        );
                        double distance = Math.max(0.0, Math.min(4.0, p.getEyePosition().distanceTo(hit.getLocation()) - 0.65));

                        for (double d = distance; d > 0.25; d -= 0.25) {
                            if (sl.noCollision(p, p.getBoundingBox().move(direction.scale(d)))) {
                                Vec3 at = p.position().add(direction.scale(d));
                                p.teleportTo(at.x, at.y, at.z);
                                break;
                            }
                        }

                        p.getCooldowns().addCooldown(this, 60);
                    } else if (this.kind != 2) {
                        p.heal(24.0F);
                        p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 3));
                        p.getCooldowns().addCooldown(this, 300);
                    } else {
                        for (LivingEntity e : sl.getEntitiesOfClass(
                            LivingEntity.class,
                            p.getBoundingBox().inflate(12.0),
                            ex -> ex == p
                                    || ex.isAlliedTo(p)
                                    || ex.getPersistentData().hasUUID("ororRelicOwner") && ex.getPersistentData().getUUID("ororRelicOwner").equals(p.getUUID())
                        )) {
                            e.heal(20.0F);
                            e.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 400, 3));
                            e.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 400, 2));
                        }

                        p.getCooldowns().addCooldown(this, 600);
                    }

                    NightfallArsenal.particles(sl, p);
                }

                return InteractionResultHolder.sidedSuccess(stack, world.isClientSide);
            }
        }
    }
}
