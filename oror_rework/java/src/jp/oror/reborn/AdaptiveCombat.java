package jp.oror.reborn;

import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ThrownTrident;
import net.minecraft.world.entity.projectile.AbstractArrow.Pickup;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ProjectileWeaponItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.ClipContext.Block;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.HitResult.Type;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent.Post;
import net.neoforged.neoforge.registries.DeferredItem;

public final class AdaptiveCombat {
    private static final ResourceLocation GROWTH = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "mind_growth");

    public static boolean active(Mob m) {
        return (Boolean)RebornConfig.SMART_MOBS.get()
            && !m.isNoAi()
            && m.isAlive()
            && (!(m instanceof SupremeEntity bx) || bx.lore())
            && (
                !(m instanceof FamiliarEntity f)
                    || !(m.level() instanceof ServerLevel sl)
                    || f.creator == null
                    || !(sl.getEntity(f.creator) instanceof SupremeEntity b)
                    || b.lore()
            );
    }

    public static boolean guardian(Mob m) {
        return m instanceof Villager || BuiltInRegistries.ENTITY_TYPE.getKey(m.getType()).getNamespace().equals("guardvillagers");
    }

    public static boolean allied(Mob m, LivingEntity other) {
        if (m != other && !m.isAlliedTo(other)) {
            if (m.getPersistentData().hasUUID("ororRelicOwner")) {
                UUID owner = m.getPersistentData().getUUID("ororRelicOwner");
                if (owner.equals(other.getUUID())
                    || other.getPersistentData().hasUUID("ororRelicOwner") && owner.equals(other.getPersistentData().getUUID("ororRelicOwner"))) {
                    return true;
                }
            }

            if (m instanceof FamiliarEntity f && f.creator != null && m.level() instanceof ServerLevel sl && sl.getEntity(f.creator) instanceof SupremeEntity b
                )
             {
                return b.ally(other);
            }

            if (m instanceof SupremeEntity b) {
                return b.ally(other);
            }

            if (guardian(m) && other instanceof Mob a && guardian(a)) {
                return VillageReputation.sameVillage(m, a);
            }

            if (other instanceof Mob a && m.getType() == a.getType() && m.getTarget() != null && m.getTarget() == a.getTarget()) {
                return true;
            }

            if (m instanceof TamableAnimal a && a.getOwnerUUID() != null && a.getOwnerUUID().equals(other.getUUID())) {
                return true;
            }

            return false;
        } else {
            return true;
        }
    }

    public static boolean enemy(Mob m, LivingEntity t) {
        return t != null && t.isAlive() && !t.isSpectator() && !allied(m, t) && (!(t instanceof Player p) || !p.isCreative());
    }

    public static void tick(Post event) {
        if (event.getEntity() instanceof Mob m && m.level() instanceof ServerLevel sl && (Boolean)RebornConfig.SMART_MOBS.get()) {
            if (m.tickCount % 20 == Math.floorMod(m.getId(), 20)) {
                MobMind.clock(m);
            }

            if (!active(m)) {
                return;
            }

            CompoundTag n = MobMind.data(m);
            if (nativeGunner(m, n)) {
                return;
            }

            MobEquipmentUse.clock(m);
            MobLevels.initialize(m);
            if (m instanceof SupremeEntity b && !n.contains("OriginalWeapon")) {
                DeferredItem<Item> relic = CharacterRelics.ITEMS.get(b.spec.id + "_weapon");
                if (relic != null) {
                    n.put("OriginalWeapon", ((Item)relic.get()).getDefaultInstance().save(m.registryAccess()));
                }
            }

            if (m.tickCount % 100 == Math.floorMod(m.getId(), 100)) {
                MobLevels.refresh(m);
                growth(m);
            }

            if (m instanceof Villager v) {
                VillagerRoles.ability(v, sl);
            }

            TerrainPlay.fallRescue(m, sl);
            if (guardian(m) && (Boolean)RebornConfig.ARMED_VILLAGERS.get() && !m.isBaby() && !n.getBoolean("Armed")) {
                arm(m);
            }

            // v0.17.9: guards hold their post, villagers run instead of charging (VillageAI)
            if (guardian(m) && VillageAI.tick(m, sl, n)) {
                return;
            }

            LivingEntity t = m.getTarget();
            if (t != null && !enemy(m, t)) {
                m.setTarget(null);
                t = null;
            }

            if (t == null && m.tickCount % 20 == Math.floorMod(m.getId(), 20)) {
                LivingEntity attacker = m.getLastHurtByMob();
                if (enemy(m, attacker) && m.distanceToSqr(attacker) < 4096.0 && (!guardian(m) || VillageAI.engage(m, attacker))) {
                    m.setTarget(attacker);
                } else if (guardian(m) && (Boolean)RebornConfig.ARMED_VILLAGERS.get()) {
                    m.setTarget(VillageAI.threat(m, sl));
                }

                t = m.getTarget();
            }

            if (!enemy(m, t)) {
                if (m.isSprinting()) {
                    m.setSprinting(false);
                }
                return;
            }

            if (m.distanceToSqr(t) > (double)(m instanceof SupremeEntity ? 16384 : 4096)) {
                m.setTarget(null);
                return;
            }

            long now = sl.getGameTime();
            footwork(m, n, now);
            int decision = MobLevels.decisionTicks(m);
            if (m.tickCount % decision == Math.floorMod(m.getId(), decision) && CombatBudget.take(m, sl)) {
                TacticalLearning.observe(m, t);
                Teamplay.coordinate(m, sl, t);
                if (MobEquipmentUse.nativeGoal(m)) {
                    return;
                }

                m.getLookControl().setLookAt(t, 40.0F, 40.0F);
                double distance = (double)m.distanceTo(t);
                String weapon = select(m, t, distance);
                boolean sight = m.getSensing().hasLineOfSight(t);
                if (n.getFloat("LastTargetHealth") > 0.0F && t.getHealth() > n.getFloat("LastTargetHealth")) {
                    MobMind.practice(m, "tactics", 1);
                }

                n.putFloat("LastTargetHealth", t.getHealth());
                if (weapon.equals("shield")) {
                    weapon = "sword";
                }

                if (n.getLong("NextHeal") <= sl.getGameTime()
                    && (double)m.getHealth() < (double)m.getMaxHealth() * (MobMind.stance(m).equals("defensive") ? 0.6 : 0.35)) {
                    m.heal((float)Math.min((double)m.getMaxHealth() * 0.2, 12.0 * MobMind.strength(m)));
                    MobMind.practice(m, "healing", 2);
                    n.putLong("NextHeal", sl.getGameTime() + 160L);
                    if (m.onGround()) {
                        Vec3 hop = BossPowers.flat(m.position().subtract(t.position())).scale(0.45);
                        m.setDeltaMovement(new Vec3(hop.x, 0.32, hop.z));
                    }
                    n.putLong("RetreatUntil", sl.getGameTime() + 32L);
                }

                List<Projectile> threats = sl.getEntitiesOfClass(
                    Projectile.class,
                    m.getBoundingBox().inflate(12.0),
                    p -> p.getOwner() != m
                            && (!(p.getOwner() instanceof LivingEntity a) || !allied(m, a))
                            && p.getDeltaMovement().lengthSqr() > 0.02
                            && p.getDeltaMovement().dot(m.position().subtract(p.position())) > 0.0
                            // v0.17.12: nobody sees a bullet coming; reacting to gun mods' bullets kept shields up for
                            // as long as a gun fired, so automatic fire never got through from the front
                            && !GUN_MODS.contains(BuiltInRegistries.ENTITY_TYPE.getKey(p.getType()).getNamespace())
                );
                if (!threats.isEmpty() && m.getOffhandItem().is(Items.SHIELD) && !m.isUsingItem() && n.getLong("ShieldBroken") <= sl.getGameTime()) {
                    m.startUsingItem(InteractionHand.OFF_HAND);
                    MobMind.practice(m, "shield", 1);
                    n.putLong("BlockUntil", sl.getGameTime() + 12L);
                }

                if (!threats.isEmpty() && MobLevels.level(m) >= 2) {
                    Vec3 approach = threats.getFirst().getDeltaMovement().normalize();
                    double sign = (double)((sl.getGameTime() / 20L + (long)m.getId()) % 2L == 0L ? 1 : -1);
                    Vec3 dodge = new Vec3(-approach.z * 0.28 * sign, 0.0, approach.x * 0.28 * sign);
                    if (sl.noCollision(m, m.getBoundingBox().move(dodge))
                        && !sl.getBlockState(BlockPos.containing(m.position().add(dodge).add(0.0, -0.2, 0.0))).isAir()) {
                        m.setDeltaMovement(new Vec3(dodge.x, m.getDeltaMovement().y, dodge.z));
                        n.putInt("Dodges", n.getInt("Dodges") + 1);
                        MobMind.practice(m, "tactics", 1);
                    }
                }

                if (distance < 4.0
                    && t.swinging
                    && n.getLong("NextAttack") > sl.getGameTime()
                    && m.getOffhandItem().is(Items.SHIELD)
                    && !m.isUsingItem()
                    && n.getLong("ShieldBroken") <= sl.getGameTime()) {
                    m.startUsingItem(InteractionHand.OFF_HAND);
                    n.putLong("BlockUntil", sl.getGameTime() + 6L);
                }

                if (m.isUsingItem() && n.getLong("BlockUntil") <= sl.getGameTime()) {
                    m.stopUsingItem();
                }

                // footwork side: flips every two seconds, per mob
                float sign = (now / 40L + (long)m.getId()) % 2L == 0L ? 1.0F : -1.0F;
                if (n.getLong("RetreatUntil") > now && distance < 8.0) {
                    step(n, now, decision + 2, -1.0F, 0.35F * sign);
                    m.setSprinting(false);
                    return;
                }

                boolean ranged = Set.of("bow", "crossbow", "trident", "gun", "magic").contains(weapon);
                // footwork keeps a melee fighter in its band until the target is clearly out of reach (no stop-start jitter)
                boolean stepping = n.getLong("FootUntil") > now;
                if (distance > (ranged ? 10.0 : (stepping ? 4.5 : 2.8))) {
                    Vec3 formation = Teamplay.formation(m, t, distance);
                    n.remove("FootUntil");
                    if (guardian(m)) {
                        VillageAI.walk(m, BlockPos.containing(formation), VillageAI.pace(m, VillageAI.CHARGE), 1);
                    } else {
                        m.getNavigation().moveTo(formation.x, formation.y, formation.z, 1.15);
                    }
                    m.setSprinting(distance > 8.0 && (guardian(m) || MobLevels.level(m) >= 3));
                } else if (distance < 3.0 && ranged) {
                    step(n, now, decision + 2, -0.8F, 0.3F * sign);
                    m.setSprinting(false);
                } else if (sight) {
                    m.setSprinting(false);
                    if (ranged) {
                        // archers circle at range like a skeleton
                        step(n, now, decision + 2, distance < 6.0 ? -0.35F : (distance > 9.0 ? 0.3F : 0.0F), 0.5F * sign);
                    } else {
                        // circle while the weapon recovers, step in when it is ready (after the step out that follows a blow)
                        long ready = n.getLong("NextAttack") - now;
                        float fwd = ready <= 4L || distance > 3.2 ? 0.6F : (distance < 1.6 ? -0.4F : 0.05F);
                        if (n.getLong("FootHold") <= now) {
                            step(n, now, decision + 2, fwd, (ready <= 4L ? 0.15F : 0.5F) * sign);
                        }
                    }
                }

                if (!sight || t.getY() > m.getY() + 2.0) {
                    terrain(m, t, sl);
                }

                TerrainPlay.bridge(m, t, sl);
                if (now >= n.getLong("NextAttack") && sight && !m.isUsingItem()) {
                    if (Set.of("gun", "magic").contains(weapon) && distance < 40.0) {
                        if (clearShot(m, t, sl)) {
                            MobEquipmentUse.use(m, t, sl, weapon);
                            n.putLong("NextAttack", now + (long)MobLevels.cooldown(m, weapon.equals("gun") ? 8 : 60));
                        }

                        return;
                    }

                    if (ranged && distance > 3.0 && distance < 32.0) {
                        if (!clearShot(m, t, sl)) {
                            return;
                        }

                        shoot(m, t, weapon, sl);
                        n.putLong("NextAttack", now + (long)MobLevels.cooldown(m, weapon.equals("crossbow") ? 28 : (weapon.equals("trident") ? 24 : 20)));
                    } else if (distance < Math.min(5.0, 2.5 + (double)(m.getBbWidth() + t.getBbWidth()) * 0.5)) {
                        long windup = n.getLong("CriticalUntil");
                        if (windup > now && !m.onGround() && m.getDeltaMovement().y >= 0.0) {
                            n.putLong("NextAttack", now + 2L);
                            return;
                        }

                        if (windup > now && m.onGround()) {
                            n.putLong("NextAttack", now + 2L);
                            return;
                        }

                        if (windup == 0L
                            && MobMind.stance(m).equals("aggressive")
                            && m.onGround()
                            && sl.noCollision(m, m.getBoundingBox().move(0.0, 0.65, 0.0))) {
                            m.getJumpControl().jump();
                            n.putLong("CriticalUntil", now + 14L);
                            n.putLong("NextAttack", now + 2L);
                            return;
                        }

                        if (windup > 0L && !m.onGround() && m.getDeltaMovement().y < 0.0) {
                            n.putInt("CriticalHits", n.getInt("CriticalHits") + 1);
                        }

                        n.remove("CriticalUntil");
                        strike(m, t, weapon, sl);
                        step(n, now, 6, -0.7F, 0.35F * sign);
                        n.putLong("FootHold", now + 6L);
                        n.putLong("NextAttack", now + (long)MobLevels.cooldown(m, weapon.equals("axe") ? 20 : (weapon.equals("unarmed") ? 8 : 12)));
                    }

                    return;
                }

                return;
            }

            return;
        }
    }

    public static void arm(Mob m) {
        MobLevels.arm(m);
    }

    private static final Set<String> GUN_MODS = Set.of("tacz", "jeg", "superbwarfare", "pillagers_gun", "pillagerguns", "tacz_bandits");

    /** An item from another mod (not vanilla, not this mod's). */
    static boolean foreign(ItemStack s) {
        if (s.isEmpty()) {
            return false;
        }
        String ns = BuiltInRegistries.ITEM.getKey(s.getItem()).getNamespace();
        return !ns.equals("minecraft") && !ns.equals("oror_supreme_bosses");
    }

    /** A gun from one of the pack's gun mods (or any other mod's gun or launcher). */
    static boolean gun(ItemStack s) {
        if (!foreign(s)) {
            return false;
        }
        String ns = BuiltInRegistries.ITEM.getKey(s.getItem()).getNamespace();
        return GUN_MODS.contains(ns) && !(s.getItem() instanceof SwordItem) || s.getItem() instanceof ProjectileWeaponItem || gunClass(s);
    }

    /** Another mod's gun item: its class or a superclass is a gun (TaCZ ModernKineticGunItem, JEG and Superb Warfare GunItem). */
    static boolean gunClass(ItemStack s) {
        if (!foreign(s)) {
            return false;
        }
        for (Class<?> c = s.getItem().getClass(); c != null && c != Item.class; c = c.getSuperclass()) {
            if (c.getSimpleName().toLowerCase(java.util.Locale.ROOT).contains("gun")) {
                return true;
            }
        }
        return false;
    }

    /**
     * v0.17.12: a mob that carries another mod's gun (pillagers from Pillager Guns and Pillagers Gun, TaCZ bandits, JEG and
     * Superb Warfare mobs) fights with that mod's own AI. Driving the same gun from here as well fired it twice, fought
     * its AI over aiming and reloads, ticked Superb Warfare guns twice and swapped guns this file did not know for vanilla
     * crossbows and swords. Villagers and the characters, which have no gun AI of their own, still shoot through
     * MobEquipmentUse. A gun swapped away by an older version is given back.
     */
    private static boolean nativeGunner(Mob m, CompoundTag n) {
        if (guardian(m) || m instanceof SupremeEntity) {
            return false;
        }
        if (!n.getBoolean("GunRestoreChecked") && !gun(m.getMainHandItem()) && n.contains("OriginalWeapon") && !n.getBoolean("OriginalAuto")) {
            // once per mob: parsing the saved weapon every tick would be wasted work
            n.putBoolean("GunRestoreChecked", true);
            ItemStack original = ItemStack.parseOptional(m.registryAccess(), n.getCompound("OriginalWeapon"));
            if (gun(original)) {
                m.setItemSlot(EquipmentSlot.MAINHAND, original);
                n.remove("OriginalWeapon");
                n.remove("Selected");
            }
        }
        return gun(m.getMainHandItem());
    }

    /** Queue footwork: forward/sideways input (as for a skeleton's strafing) for the next ticks. */
    private static void step(CompoundTag n, long now, int ticks, float forward, float side) {
        n.putLong("FootUntil", now + (long)ticks);
        n.putFloat("FootForward", forward);
        n.putFloat("FootSide", side);
    }

    /**
     * Per-tick footwork (v0.17.9): sidesteps, step-backs and closing steps go through the move control every tick, which
     * keeps the mob's footing (it will not strafe off a ledge) and looks like stepping; before, a velocity kick once every
     * few decision ticks made fighters twitch.
     */
    private static void footwork(Mob m, CompoundTag n, long now) {
        LivingEntity t = m.getTarget();
        if (t == null || n.getLong("FootUntil") <= now) {
            return;
        }
        m.getNavigation().stop();
        if (m instanceof Villager v) {
            v.getBrain().eraseMemory(MemoryModuleType.WALK_TARGET);
        }
        m.lookAt(t, 30.0F, 30.0F);
        m.getMoveControl().strafe(n.getFloat("FootForward"), n.getFloat("FootSide"));
    }

    private static void growth(Mob m) {
        double power = MobMind.strength(m);

        for (Holder<Attribute> attr : List.of(Attributes.ATTACK_DAMAGE, Attributes.MAX_HEALTH, Attributes.MOVEMENT_SPEED)) {
            AttributeInstance a = m.getAttribute(attr);
            if (a != null) {
                a.removeModifier(GROWTH);
                if (power > 1.0) {
                    // movement: at most +15% (+32% ground speed); the old +80% made veterans more than three times as fast
                    double amount = attr == Attributes.MOVEMENT_SPEED ? Math.min(0.15, (power - 1.0) * 0.06) : Math.min(31.0, power - 1.0);
                    a.addPermanentModifier(new AttributeModifier(GROWTH, amount, Operation.ADD_MULTIPLIED_BASE));
                }
            }
        }
    }

    public static String select(Mob m, LivingEntity t, double distance) {
        // characters fight with their own relic (BossPowers keeps it in hand): never trade it for a vanilla weapon
        String relic = m instanceof SupremeEntity ? CharacterRelics.style(m.getMainHandItem()) : null;
        if (relic != null) {
            MobMind.data(m).putString("Selected", relic);
            return relic;
        }
        String special = MobEquipmentUse.kind(m.getMainHandItem());
        if (!special.isEmpty()) {
            MobMind.data(m).putString("Selected", special);
            return special;
        } else if (foreign(m.getMainHandItem())) {
            // v0.17.12: another mod's weapon stays in hand (it used to be swapped for a vanilla one)
            String kept = gun(m.getMainHandItem()) ? "bow" : "sword";
            MobMind.data(m).putString("Selected", kept);
            return kept;
        } else {
            String wanted = MobMind.preferred(m);
            String stance = MobMind.stance(m);
            if (wanted.isEmpty()) {
                wanted = VillagerRoles.preferred(m);
            }

            boolean var10000;
            label108: {
                if (m instanceof SupremeEntity b && b.spec.id.equals("kokuhaku") && wanted.isEmpty() && !stance.equals("ranged")) {
                    var10000 = true;
                    break label108;
                }

                var10000 = false;
            }

            boolean swordsman = var10000;
            if (wanted.isEmpty() && m instanceof SupremeEntity b && b.spec.id.equals("mels")) {
                wanted = "unarmed";
            }

            if (stance.equals("unarmed")) {
                wanted = "unarmed";
            } else if (t.isBlocking()) {
                wanted = "axe";
            } else if (m.isInWater() && distance > 4.0) {
                wanted = "trident";
            } else if (!(distance > 8.0) || swordsman || wanted.equals("unarmed") && !stance.equals("ranged")) {
                if (wanted.isEmpty() || Set.of("tactics", "terrain", "teamwork", "healing", "shield").contains(wanted)) {
                    wanted = "sword";
                }
            } else {
                wanted = wanted.equals("crossbow") ? "crossbow" : "bow";
            }

            if (!Set.of("unarmed", "sword", "axe", "mace", "bow", "crossbow", "trident").contains(wanted)) {
                wanted = "sword";
            }

            wanted = TacticalLearning.choose(m, t, wanted);
            CompoundTag n = MobMind.data(m);
            String previous = n.getString("Selected");
            if (!previous.equals(wanted)) {
                ItemStack held = m.getMainHandItem();
                if (!held.isEmpty() && !n.getBoolean("OriginalAuto") && !n.contains("OriginalWeapon")) {
                    n.put("OriginalWeapon", held.save(m.registryAccess()));
                }

                ItemStack next = wanted.equals("unarmed")
                    ? ItemStack.EMPTY
                    : (
                        wanted.equals("sword") && n.contains("OriginalWeapon") && !n.getBoolean("OriginalAuto")
                            ? ItemStack.parseOptional(m.registryAccess(), n.getCompound("OriginalWeapon"))
                            : MobLevels.weapon(m, wanted)
                    );
                if (wanted.equals("sword")
                    && !(next.getItem() instanceof SwordItem)
                    && !Set.of("epicfight", "wom").contains(BuiltInRegistries.ITEM.getKey(next.getItem()).getNamespace())) {
                    next = MobLevels.weapon(m, "sword");
                }

                m.setItemSlot(EquipmentSlot.MAINHAND, next);
                m.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
                n.putString("Selected", wanted);
            }

            return wanted;
        }
    }

    public static boolean clearShot(Mob m, LivingEntity t, ServerLevel sl) {
        Vec3 start = m.getEyePosition();
        Vec3 end = t.getEyePosition();
        if (sl.clip(new ClipContext(start, end, Block.COLLIDER, Fluid.NONE, m)).getType() != Type.MISS) {
            return false;
        } else {
            Vec3 line = end.subtract(start);
            double len = line.lengthSqr();

            for (LivingEntity a : sl.getEntitiesOfClass(LivingEntity.class, new AABB(start, end).inflate(1.0), v -> v != m && v != t && allied(m, v))) {
                double f = a.getBoundingBox().getCenter().subtract(start).dot(line) / Math.max(0.001, len);
                if (f > 0.0 && f < 1.0 && a.getBoundingBox().inflate(0.35).clip(start, end).isPresent()) {
                    return false;
                }
            }

            return true;
        }
    }

    public static void shoot(Mob m, LivingEntity t, String weapon, ServerLevel sl) {
        // v0.17.10: characters with a catalyst, gun, cannon or bow relic fire its bolts and shells, not plain arrows
        if (m instanceof SupremeEntity b) {
            CharacterRelics.Kind kind = CharacterRelics.kindOf(b.spec.id);
            if (kind.ranged() && !kind.mode.equals("guard")) {
                float dmg = (float)((b.lore() ? 1000000.0 : b.spec.damage * kind.shot) * MobMind.strength(m));
                int n = MobMind.data(m).getInt("Shots") + 1;
                BossArms.fire(b, sl, t, kind, dmg, BossPowers.color(b), n % 4 == 0);
                m.swing(InteractionHand.MAIN_HAND);
                MobMind.practice(m, weapon, 1);
                MobMind.data(m).putInt("Shots", n);
                return;
            }
        }

        Projectile projectile;
        if (weapon.equals("trident")) {
            ThrownTrident p = new ThrownTrident(sl, m, Items.TRIDENT.getDefaultInstance());
            p.pickup = Pickup.DISALLOWED;
            projectile = p;
        } else {
            Arrow p;
            int var10001;
            label27: {
                ItemStack source = m.getMainHandItem().getItem() instanceof ProjectileWeaponItem
                    ? m.getMainHandItem()
                    : (weapon.equals("crossbow") ? Items.CROSSBOW : Items.BOW).getDefaultInstance();
                p = new Arrow(sl, m, Items.ARROW.getDefaultInstance(), source);
                if (m instanceof SupremeEntity b && b.lore()) {
                    var10001 = 1000000;
                    break label27;
                }

                var10001 = guardian(m) ? 16 : 4;
            }

            p.setBaseDamage((double)var10001 * MobMind.strength(m));
            p.pickup = Pickup.DISALLOWED;
            projectile = p;
        }

        double distance = (double)m.distanceTo(t);
        Vec3 lead = t.getDeltaMovement().scale(Math.min(10.0, distance / 2.4));
        Vec3 aim = t.getEyePosition().add(lead).subtract(projectile.position()).add(0.0, distance * 0.018, 0.0);
        projectile.shoot(aim.x, aim.y, aim.z, 2.6F, MobLevels.accuracy(m, weapon));
        sl.addFreshEntity(projectile);
        m.swing(InteractionHand.MAIN_HAND);
        MobMind.practice(m, weapon, 1);
        MobMind.data(m).putInt("Shots", MobMind.data(m).getInt("Shots") + 1);
    }

    public static void strike(Mob m, LivingEntity t, String weapon, ServerLevel sl) {
        if (enemy(m, t)) {
            String learningContext = TacticalLearning.context(m, t);
            CompoundTag n = MobMind.data(m);
            if (weapon.equals("axe") && t.isBlocking()) {
                t.stopUsingItem();
                if (t instanceof Player p) {
                    p.getCooldowns().addCooldown(Items.SHIELD, 100);
                }

                if (t instanceof Mob mob) {
                    MobMind.data(mob).putLong("ShieldBroken", sl.getGameTime() + 100L);
                }
            }

            float hpBefore = t.getHealth();
            m.swing(InteractionHand.MAIN_HAND);
            if (m instanceof SupremeEntity b) {
                LorePowers.strike(b, t, (float)((double)b.spec.damage * MobMind.strength(m)), false);
            } else {
                label81: {
                    if (m instanceof FamiliarEntity f && f.creator != null && sl.getEntity(f.creator) instanceof SupremeEntity b && b.lore()) {
                        LorePowers.strike(b, t, 5.0F, false);
                        break label81;
                    }

                    AttributeInstance attack = m.getAttribute(Attributes.ATTACK_DAMAGE);
                    double base = attack == null ? 4.0 + weaponBonus(m) : Math.max(4.0, attack.getValue());
                    if (guardian(m)) {
                        base = Math.max(48.0, base);
                    }

                    float amount = (float)Math.min(1000000.0, base * MobMind.strength(m) * (weapon.equals("axe") ? 1.2 : 1.0));
                    if (!m.onGround()) {
                        amount *= 1.5F;
                    }

                    if (weapon.equals("mace") && m.fallDistance > 1.5F) {
                        amount += Math.min(1024.0F, m.fallDistance * 12.0F);
                    }

                    t.hurt(m.damageSources().mobAttack(m), amount);
                }
            }

            boolean hit = t.getHealth() < hpBefore || !t.isAlive();
            TacticalLearning.outcome(m, learningContext, weapon, hit);
            if (hit) {
                n.putInt("SuccessfulStrikes", n.getInt("SuccessfulStrikes") + 1);
            } else {
                n.putInt("RejectedStrikes", n.getInt("RejectedStrikes") + 1);
            }

            MobMind.practice(m, weapon, 2);
            MobMind.practice(m, "tactics", 1);
            MobMind.remember(m, BuiltInRegistries.ENTITY_TYPE.getKey(t.getType()).toString(), t.isBlocking() ? "axe_vs_shield" : "spacing_and_cooldown");
            n.putInt("Strikes", n.getInt("Strikes") + 1);
            m.setSprinting(false);
        }
    }

    private static double weaponBonus(Mob m) {
        double[] amount = new double[]{0.0};
        m.getMainHandItem().forEachModifier(EquipmentSlot.MAINHAND, (attribute, modifier) -> {
            if (attribute.equals(Attributes.ATTACK_DAMAGE) && modifier.operation() == Operation.ADD_VALUE) {
                amount[0] += modifier.amount();
            }
        });
        MobEffectInstance effect = m.getEffect(MobEffects.DAMAGE_BOOST);
        if (effect != null) {
            amount[0] += (double)(3 * (effect.getAmplifier() + 1));
        }

        return amount[0];
    }

    public static boolean terrain(Mob m, LivingEntity t, ServerLevel sl) {
        if (!guardian(m)
            && (Boolean)RebornConfig.AI_TERRAIN.get()
            && sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)
            && sl.getWorldBorder().isWithinBounds(m.blockPosition())
            && m.onGround()) {
            CompoundTag n = MobMind.data(m);
            long now = sl.getGameTime();
            if (n.getLong("NextTerrain") > now) {
                return false;
            } else {
                n.putLong("NextTerrain", now + 40L);
                BlockPos pos = m.blockPosition();
                if (t.getY() > m.getY() + 2.0 && m.distanceToSqr(t) < 256.0) {
                    BlockState state = sl.getBlockState(pos);
                    if (!state.canBeReplaced()
                        || sl.getBlockEntity(pos) != null
                        || !sl.hasChunkAt(pos.above(2))
                        || !sl.noCollision(m, m.getBoundingBox().move(0.0, 1.0, 0.0))) {
                        return false;
                    } else if (!TerrainPlay.place(m, sl, pos, Blocks.COBBLESTONE.defaultBlockState())) {
                        return false;
                    } else {
                        m.teleportTo(m.getX(), m.getY() + 1.05, m.getZ());
                        n.putInt("PillarBlocks", n.getInt("PillarBlocks") + 1);
                        MobMind.practice(m, "terrain", 2);
                        return true;
                    }
                } else {
                    Vec3 dir = t.position().subtract(m.position()).normalize();
                    BlockPos front = BlockPos.containing(m.getX() + dir.x, m.getY(), m.getZ() + dir.z);
                    if (sl.hasChunkAt(front) && sl.getWorldBorder().isWithinBounds(front)) {
                        BlockState state = sl.getBlockState(front);
                        if (!state.isAir()
                            && !VillageReputation.villageOwned(sl, front)
                            && sl.getBlockEntity(front) == null
                            && !(state.getBlock() instanceof BedBlock)
                            && !(state.getBlock() instanceof BaseEntityBlock)
                            && !(state.getDestroySpeed(sl, front) < 0.0F)
                            && !(state.getDestroySpeed(sl, front) > 5.0F)) {
                            sl.destroyBlock(front, false, m);
                            MobMind.practice(m, "terrain", 2);
                            return true;
                        } else {
                            return false;
                        }
                    } else {
                        return false;
                    }
                }
            }
        } else {
            return false;
        }
    }

    public static void damage(LivingIncomingDamageEvent event) {
        if (event.getEntity().level() instanceof ServerLevel sl) {
            if (event.getSource().getEntity() instanceof LivingEntity attacker) {
                if (attacker instanceof Mob a && active(a) && allied(a, event.getEntity())) {
                    event.setCanceled(true);
                    return;
                }

                if (attacker instanceof Mob a && active(a) && event.getSource().getDirectEntity() instanceof ThrownTrident) {
                    event.setAmount((float)((double)event.getAmount() * MobMind.strength(a)));
                }

                if (event.getEntity() instanceof Mob m && active(m) && enemy(m, attacker)) {
                    if (attacker instanceof Player player) {
                        String observed = player.getMainHandItem().is(Items.MACE)
                            ? "mace"
                            : (
                                player.getMainHandItem().getItem() instanceof AxeItem
                                    ? "axe"
                                    : (
                                        player.getMainHandItem().getItem() instanceof SwordItem
                                            ? "sword"
                                            : (event.getSource().getDirectEntity() instanceof Projectile ? "bow" : "unarmed")
                                    )
                            );
                        String kind = CharacterRelics.style(player.getMainHandItem());
                        if (kind != null) {
                            observed = kind;
                        }
                        MobMind.practice(m, observed, 1);
                        MobMind.data(m).putString("ObservedPlayerStyle", observed);
                        MobMind.data(m).putString("PlayerEvidenceKind", "observed_attack_attempt");
                        if (player.fallDistance > 1.5F) {
                            MobMind.practice(m, "shield", 2);
                        }
                    }

                    MobMind.practice(m, "shield", 1);
                    MobMind.remember(m, BuiltInRegistries.ENTITY_TYPE.getKey(attacker.getType()).toString(), "observed_" + event.getSource().getMsgId());
                    if (guardian(m) && (Boolean)RebornConfig.ARMED_VILLAGERS.get()) {
                        // v0.17.9: guards take up the fight, villagers hear the alarm and run (VillageAI)
                        if (VillageAI.fighter(m)) {
                            m.setTarget(attacker);
                        }

                        for (Mob ally : sl.getEntitiesOfClass(Mob.class, m.getBoundingBox().inflate(24.0), AdaptiveCombat::guardian)) {
                            if (active(ally) && allied(m, ally) && enemy(ally, attacker) && VillageAI.engage(ally, attacker)) {
                                ally.setTarget(attacker);
                                MobMind.practice(ally, "teamwork", 1);
                            }
                        }

                        VillageAI.alarm(sl, m, attacker);
                    }
                }
            }
        }
    }
}
