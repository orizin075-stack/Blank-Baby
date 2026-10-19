package jp.oror.reborn;

import java.util.ArrayDeque;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.BossEvent.BossBarColor;
import net.minecraft.world.BossEvent.BossBarOverlay;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.Entity.RemovalReason;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier.Builder;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ProjectileWeaponItem;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.fluids.FluidType;

public final class SupremeEntity extends PathfinderMob {
    private static final EntityDataAccessor<Integer> PHASE = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> ACTION = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> FORM = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> OPERATOR = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Float> MANA = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.FLOAT);
    private static final EntityDataAccessor<Integer> MOTION = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> MOTION_DURATION = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Long> MOTION_START = SynchedEntityData.defineId(SupremeEntity.class, EntityDataSerializers.LONG);
    private long clientMotionStartTime;
    public final CharacterSpec spec;
    public final CombatMemory memory = new CombatMemory();
    private final ServerBossEvent bar;
    public long nextRelicDrop;
    public float avatarFracture;
    public boolean balanced;
    public long loreEvolution;
    public final Set<String> loreAdaptation = new HashSet<>();
    public float soulHealth;
    public float shield;
    public int evolution;
    public int revivals;
    public int cooldown = 50;
    public int windup;
    public int coreOpen;
    public String targetSpecies = "";
    public UUID owner;
    public boolean arena;
    private final ArrayDeque<SupremeEntity.Snapshot> history = new ArrayDeque<>();

    public boolean lore() {
        return (Boolean)RebornConfig.LORE.get() && !this.balanced;
    }

    public float manaCap() {
        return this.lore() && this.spec.loreMana > 0.0F ? this.spec.loreMana : this.spec.mana;
    }

    public SupremeEntity(EntityType<? extends SupremeEntity> type, Level level, CharacterSpec spec) {
        super(type, level);
        this.spec = spec;
        this.setPersistenceRequired();
        this.setNoGravity(spec.airborne());
        this.bar = new ServerBossEvent(Component.literal(spec.name), BossBarColor.PURPLE, BossBarOverlay.PROGRESS);
        this.soulHealth = spec.loreHealth > 0.0F ? spec.loreHealth : spec.health;
        this.entityData.set(MANA, this.manaCap());
    }

    public static Builder attributes(CharacterSpec s) {
        return Mob.createMobAttributes()
            .add(Attributes.MAX_HEALTH, (double)s.health)
            .add(Attributes.ARMOR, 12.0)
            .add(Attributes.ARMOR_TOUGHNESS, 6.0)
            .add(Attributes.ATTACK_DAMAGE, (double)s.damage)
            .add(Attributes.MOVEMENT_SPEED, (double)s.speed)
            .add(Attributes.FLYING_SPEED, 0.5)
            .add(Attributes.FOLLOW_RANGE, 40.0)
            .add(Attributes.KNOCKBACK_RESISTANCE, 0.8)
            .add(net.minecraftforge.common.ForgeMod.STEP_HEIGHT_ADDITION.get(), 0.6);
    }

    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(PHASE, 0);
        this.entityData.define(ACTION, 0);
        this.entityData.define(FORM, 0);
        this.entityData.define(MANA, 0.0F);
        this.entityData.define(OPERATOR, 0);
        this.entityData.define(MOTION, 0);
        this.entityData.define(MOTION_DURATION, 1);
        this.entityData.define(MOTION_START, 0L);
    }

    public void motion(int id, int duration) {
        this.entityData.set(MOTION, net.minecraft.util.Mth.clamp((int)id, 0, 16));
        this.entityData.set(MOTION_DURATION, Math.max(1, duration));
        this.entityData.set(MOTION_START, this.level().getGameTime());
    }

    private long motionElapsed() {
        return Math.max(0L, this.level().getGameTime() - (this.level().isClientSide ? this.clientMotionStartTime : (Long)this.entityData.get(MOTION_START)));
    }

    public int motion() {
        return this.motionElapsed() < (long)((Integer)this.entityData.get(MOTION_DURATION)).intValue() ? (Integer)this.entityData.get(MOTION) : 0;
    }

    public float motionProgress(float partial) {
        return net.minecraft.util.Mth.clamp(((float)this.motionElapsed() + partial) / (float)((Integer)this.entityData.get(MOTION_DURATION)).intValue(), 0.0F, 1.0F);
    }

    protected void registerGoals() {
        this.goalSelector.addGoal(0, new FloatGoal(this));
        this.goalSelector
            .addGoal(
                6,
                new WaterAvoidingRandomStrollGoal(this, 0.65) {
                    public boolean canUse() {
                        return SupremeEntity.this.spec != null
                            && !SupremeEntity.this.spec.airborne()
                            && !SupremeEntity.this.spec.aquatic()
                            && !SupremeEntity.this.spec.model.equals("tree")
                            && SupremeEntity.this.getTarget() == null
                            && SupremeEntity.this.owner == null
                            && super.canUse();
                    }
                }
            );
        this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
    }

    public int operatorLevel() {
        return this.level().isClientSide ? (Integer)this.entityData.get(OPERATOR) : OperatorPowers.level(this);
    }

    protected int getPermissionLevel() {
        return this.spec == null ? 0 : this.operatorLevel();
    }

    public boolean canBeAffected(MobEffectInstance e) {
        return (this.spec == null || this.operatorLevel() != 4 || e.getEffect().isBeneficial()) && super.canBeAffected(e);
    }

    public int phase() {
        return (Integer)this.entityData.get(PHASE);
    }

    public int action() {
        return (Integer)this.entityData.get(ACTION);
    }

    public int form() {
        return (Integer)this.entityData.get(FORM);
    }

    public void setForm(int f) {
        int next = Math.floorMod(f, 4);
        if (this.form() == next) {
            this.refreshDimensions();
        } else {
            this.entityData.set(FORM, next);
        }
    }

    public void onSyncedDataUpdated(EntityDataAccessor<?> data) {
        super.onSyncedDataUpdated(data);
        if (this.level().isClientSide && (MOTION_START.equals(data) || MOTION.equals(data))) {
            this.clientMotionStartTime = this.level().getGameTime();
        }

        if (FORM.equals(data) && this.spec != null) {
            this.refreshDimensions();
        }
    }

    public EntityDimensions getDimensions(Pose p) {
        return this.spec != null && this.spec.id.equals("yggdrasil") && this.form() == 1
            ? EntityDimensions.scalable(0.6F, 1.7F)
            : super.getDimensions(p);
    }

    public float mana() {
        return (Float)this.entityData.get(MANA);
    }

    public void mana(float v) {
        this.entityData.set(MANA, Float.isFinite(v) ? Math.max(0.0F, Math.min(this.manaCap(), v)) : 0.0F);
    }

    public boolean spend(float v) {
        if (this.mana() < v) {
            return false;
        } else {
            this.mana(this.mana() - v);
            return true;
        }
    }

    public boolean ally(LivingEntity e) {
        if (e != this && !this.isAlliedTo(e)) {
            if (e.getPersistentData().hasUUID("ororRelicOwner") && this.owner != null && this.owner.equals(e.getPersistentData().getUUID("ororRelicOwner"))) {
                return true;
            } else if (e == this.getTarget()) {
                return false;
            } else if (this.owner != null && this.owner.equals(e.getUUID())) {
                return true;
            } else {
                if (e instanceof FamiliarEntity f) {
                    if (this.getUUID().equals(f.creator)) {
                        return true;
                    }

                    if (f.creator != null && this.level() instanceof ServerLevel sl && sl.getEntity(f.creator) instanceof SupremeEntity maker) {
                        return this.ally(maker);
                    }
                }

                return e instanceof SupremeEntity s
                    ? !this.arena && !s.arena && (this.owner == null || s.owner == null || this.owner.equals(s.owner))
                    : !this.arena && this.spec.behavior.equals("guardian") && (e instanceof Player || e instanceof Animal || e instanceof Villager);
            }
        } else {
            return true;
        }
    }

    public boolean validEnemy(LivingEntity e) {
        if (!e.isAlive() || e.isSpectator() || this.ally(e)) {
            return false;
        } else {
            if (e instanceof Player p && p.isCreative()) {
                return false;
            }

            if (e instanceof FamiliarEntity f
                && f.creator != null
                && this.level() instanceof ServerLevel sl
                && sl.getEntity(f.creator) instanceof SupremeEntity s
                && this.ally(s)) {
                return false;
            }

            return true;
        }
    }

    public boolean canDrownInFluidType(FluidType type) {
        return false;
    }

    public ItemStack getProjectile(ItemStack weapon) {
        ItemStack ammunition = super.getProjectile(weapon);
        if (!ammunition.isEmpty()) {
            return ammunition;
        } else {
            return weapon.getItem() instanceof ProjectileWeaponItem ? Items.ARROW.getDefaultInstance() : ammunition;
        }
    }

    public boolean removeWhenFarAway(double d) {
        return false;
    }

    public boolean causeFallDamage(float d, float m, DamageSource s) {
        return false;
    }

    public void startSeenByPlayer(ServerPlayer p) {
        super.startSeenByPlayer(p);
        this.bar.addPlayer(p);
    }

    public void stopSeenByPlayer(ServerPlayer p) {
        super.stopSeenByPlayer(p);
        this.bar.removePlayer(p);
    }

    public void tick() {
        super.tick();
        if (!this.level().isClientSide && this.isAlive() && this.level() instanceof ServerLevel sl) {
            this.entityData.set(OPERATOR, OperatorPowers.level(this));
            this.bar.setName(Component.literal(this.spec.name + (this.operatorLevel() == 4 ? " [創世管理者 Lv.4]" : "")));
            this.bar.setVisible(this.getTarget() != null || this.arena);
            this.bar.setProgress(Math.max(0.0F, Math.min(1.0F, this.getHealth() / this.getMaxHealth())));
            if ((Integer)this.entityData.get(MOTION) != 0 && this.motionElapsed() >= (long)((Integer)this.entityData.get(MOTION_DURATION)).intValue()) {
                this.entityData.set(MOTION, 0);
            }

            if (this.isNoAi()) {
                this.windup = 0;
                this.entityData.set(ACTION, 0);
                this.navigation.stop();
            } else {
                if (this.tickCount % 10 == 0) {
                    this.mana(this.mana() + this.spec.regen * 0.5F);
                    if (this.history.size() == 12) {
                        this.history.removeFirst();
                    }

                    this.history.addLast(new SupremeEntity.Snapshot(this.position(), this.getHealth()));
                }

                if (this.lore()
                    && this.tickCount % 100 == 0
                    && Set.of("hakyoku", "miyohime", "shinra", "mary_sue", "forbidden_arcana", "relentless_research").contains(this.spec.id)) {
                    LorePowers.grow(this);
                }

                if (this.coreOpen > 0) {
                    this.coreOpen--;
                }

                if (this.shield > 0.0F) {
                    this.shield = Math.max(0.0F, this.shield - 0.04F);
                }

                if (this.tickCount % 40 == 0) {
                    Abilities.passive(this, sl);
                }

                LivingEntity target = this.getTarget();
                if (target != null && (!this.validEnemy(target) || this.distanceToSqr(target) > 16384.0)) {
                    this.setTarget(null);
                    target = null;
                    this.windup = 0;
                    this.entityData.set(ACTION, 0);
                }

                if (target == null && this.tickCount % 20 == 0 && (this.spec.behavior.equals("guardian") || this.spec.behavior.equals("violent"))) {
                    target = sl.getEntitiesOfClass(
                            LivingEntity.class,
                            this.getBoundingBox().inflate(12.0),
                            e -> (e instanceof Enemy || this.spec.behavior.equals("violent") && e instanceof Player) && this.validEnemy(e)
                        )
                        .stream()
                        .min(Comparator.comparingDouble(this::distanceToSqr))
                        .orElse(null);
                    this.setTarget(target);
                }

                if (target == null && this.lore() && this.getPersistentData().getLong("OrorDomainCasts") > 0L && this.tickCount % 20 == 0) {
                    target = sl.getEntitiesOfClass(
                            Mob.class, this.getBoundingBox().inflate(128.0), m -> this.validEnemy(m) && (m.getTarget() == this || m.getLastHurtByMob() == this)
                        )
                        .stream()
                        .min(Comparator.comparingDouble(this::distanceToSqr))
                        .orElse(null);
                    this.setTarget(target);
                }

                if (target == null) {
                    this.followOwner(sl);
                    if (this.spec.airborne()) {
                        this.setDeltaMovement(this.getDeltaMovement().scale(0.8));
                    }

                    if (this.spec.aquatic()) {
                        this.swim(null);
                    }
                } else {
                    this.lookAt(target, 30.0F, 30.0F);
                    if (this.spec.airborne()) {
                        this.fly(target);
                    } else if (this.spec.aquatic()) {
                        this.swim(target);
                    } else if (!this.spec.model.equals("tree")) {
                        double range = Abilities.melee(this.spec.id) ? 2.5 : 9.0;
                        if ((double)this.distanceTo(target) > range) {
                            this.navigation.moveTo(target, 1.05);
                        } else {
                            this.navigation.stop();
                        }
                    }

                    if (this.windup > 0) {
                        this.windup--;
                        Abilities.telegraph(this, sl, target);
                        if (this.windup == 0) {
                            int next = this.getPersistentData().getInt("OrorCastSequence");
                            if (next % 4 != 0 && (Boolean)RebornConfig.EXTRA_ABILITIES.get()) {
                                CharacterArsenal.cast(this, sl, target, next % 4 - 1);
                            } else {
                                Abilities.cast(this, sl, target);
                            }

                            this.getPersistentData().putInt("OrorCastSequence", next == Integer.MAX_VALUE ? 0 : next + 1);
                            this.cooldown = this.lore()
                                ? Math.max(1, this.spec.cooldown / 12)
                                : Math.max(20, this.spec.cooldown - Math.min(30, this.evolution));
                            this.entityData.set(ACTION, 0);
                        }
                    } else if (--this.cooldown <= 0 && this.distanceToSqr(target) < 1600.0) {
                        this.windup = this.lore() ? (Set.of("kokuhaku", "teia").contains(this.spec.id) ? 1 : 3) : 16;
                        int seq = this.getPersistentData().getInt("OrorCastSequence") % 4;
                        this.motion(
                            seq == 0 ? CharacterArsenal.baseMotion(this) : CharacterArsenal.ALL.get(this.spec.id).get(seq - 1).motion(), this.windup + 24
                        );
                        this.entityData.set(ACTION, 1);
                        this.coreOpen = 36;
                    }
                }
            }
        }
    }

    private void followOwner(ServerLevel sl) {
        if (this.owner != null && sl.getEntity(this.owner) instanceof LivingEntity p && this.distanceTo(p) > 4.0F && this.distanceTo(p) < 40.0F) {
            if (this.spec.airborne()) {
                this.fly(p);
            } else if (this.spec.aquatic()) {
                this.swim(p);
            } else {
                this.navigation.moveTo(p, 0.9);
            }
        }
    }

    private void fly(LivingEntity t) {
        this.setNoGravity(true);
        Vec3 v = t.position().add(0.0, 3.0, 0.0).subtract(this.position());
        if (v.lengthSqr() > 4.0) {
            Vec3 next = this.getDeltaMovement().scale(0.7).add(v.normalize().scale(this.spec.id.equals("teia") ? 0.3 : 0.12));
            this.setDeltaMovement(next.length() > 1.0 ? next.normalize() : next);
        }
    }

    private void swim(LivingEntity t) {
        if (this.isInWater()) {
            Vec3 v = t == null
                ? new Vec3(Math.sin((double)this.tickCount * 0.03), 0.01, Math.cos((double)this.tickCount * 0.03))
                : t.position().subtract(this.position()).normalize();
            this.setDeltaMovement(this.getDeltaMovement().scale(0.8).add(v.scale(0.08)));
        }
    }

    public void rewind() {
        SupremeEntity.Snapshot s = this.history.peekFirst();
        if (s != null) {
            Abilities.blink(this, s.pos());
            this.setHealth(Math.max(this.getHealth(), s.hp()));
        }
    }

    public void healAllies(float a) {
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(12.0), this::ally)) {
            e.heal(a);
            e.removeEffect(MobEffects.POISON);
            e.removeEffect(MobEffects.WITHER);
            e.removeEffect(MobEffects.WEAKNESS);
        }
    }

    public boolean hurt(DamageSource source, float amount) {
        if (this.level().isClientSide || !Float.isFinite(amount) || amount <= 0.0F) {
            return false;
        } else if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return super.hurt(source, amount);
        } else {
            Entity attacker = source.getEntity();
            if ((
                    attacker instanceof SupremeEntity
                        || attacker instanceof FamiliarEntity
                        || attacker != null && attacker.getPersistentData().hasUUID("ororRelicOwner")
                )
                && attacker instanceof LivingEntity friendly
                && this.ally(friendly)) {
                return false;
            }

            if (attacker instanceof LivingEntity e && e != this && !this.isAlliedTo(e) && (this.owner == null || !this.owner.equals(e.getUUID()))) {
                this.setTarget(e);
            }

            String type = source.typeHolder().unwrapKey().map(k -> k.location().toString()).orElse("unknown");
            int previous = this.memory.count(type);
            amount = LorePowers.incoming(this, source, amount, type);
            if (Set.of("hakyoku", "shinra", "miyohime", "valeria").contains(this.spec.id)) {
                amount *= CombatMemory.resistance(previous);
            }

            if (this.spec.id.equals("mels")) {
                amount *= 0.35F;
            }

            if (this.spec.id.equals("chaos") && this.coreOpen <= 0) {
                amount *= 0.1F;
            }

            if (this.spec.id.equals("tenki") && source.getDirectEntity() instanceof Projectile) {
                source.getDirectEntity().discard();
                return false;
            } else {
                if (this.spec.id.equals("riha") && this.spend(8.0F)) {
                    amount *= 0.25F;
                }

                if (this.shield > 0.0F) {
                    float absorb = Math.min(amount, this.shield);
                    this.shield -= absorb;
                    amount -= absorb;
                }

                if (this.spec.id.equals("shinra") && attacker instanceof LivingEntity e) {
                    if (BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString().equals(this.targetSpecies)) {
                        amount *= 0.25F;
                    }

                    this.targetSpecies = BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();
                }

                this.memory.observe(type);
                if (this.spec.id.equals("hakyoku") || this.spec.id.equals("miyohime")) {
                    this.evolution = CombatMemory.boundedEvolution(this.evolution + 1);
                }

                if (amount <= 0.0F) {
                    return false;
                } else if (this.lore() && this.spec.loreHealth > 0.0F) {
                    this.soulHealth = Math.max(0.0F, this.soulHealth - amount);
                    this.setHealth(this.getMaxHealth() * this.soulHealth / this.spec.loreHealth);
                    if (this.soulHealth <= 0.0F) {
                        this.die(source);
                    }

                    this.level().broadcastEntityEvent(this, (byte)2);
                    return true;
                } else {
                    boolean result = super.hurt(source, amount);
                    this.entityData.set(PHASE, Math.max(this.phase(), (int)((1.0F - this.getHealth() / this.getMaxHealth()) * 3.0F)));
                    return result;
                }
            }
        }
    }

    public void heal(float amount) {
        if (this.spec != null && this.lore() && this.spec.loreHealth > 0.0F) {
            this.soulHealth = Math.min(this.spec.loreHealth, this.soulHealth + Math.max(0.0F, amount) * 10000.0F);
            this.setHealth(this.getMaxHealth() * this.soulHealth / this.spec.loreHealth);
        } else {
            super.heal(amount);
        }
    }

    private boolean immortal() {
        return LorePowers.IMMORTAL.contains(this.spec.id);
    }

    public void die(DamageSource s) {
        if (Boolean.getBoolean("oror.smoke")) {
            System.out
                .println(
                    "[OROR_LORE_DEATH] id="
                        + this.spec.id
                        + " source="
                        + s.getMsgId()
                        + " attacker="
                        + (s.getEntity() == null ? "none" : BuiltInRegistries.ENTITY_TYPE.getKey(s.getEntity().getType()))
                        + " at="
                        + this.position()
                        + " hp="
                        + this.getHealth()
                );
        }

        if (!s.is(DamageTypeTags.BYPASSES_INVULNERABILITY) && this.immortal() && (this.lore() || this.revivals < (Integer)RebornConfig.REVIVALS.get())) {
            RelicDrops.defeat(this, s);
            if (this.revivals < Integer.MAX_VALUE) {
                this.revivals++;
            }

            if (this.lore()) {
                LorePowers.grow(this);
            }

            this.soulHealth = this.spec.loreHealth > 0.0F ? this.spec.loreHealth : this.spec.health;
            this.evolution = CombatMemory.boundedEvolution(this.evolution + 3);
            this.entityData.set(PHASE, Math.min(10, this.phase() + 1));
            this.setHealth(this.getMaxHealth());
            this.shield = 60.0F;
            this.cooldown = 40;
            Abilities.burst(this, ParticleTypes.END_ROD, 32);
        } else {
            RelicDrops.defeat(this, s);
            this.bar.removeAllPlayers();
            super.die(s);
        }
    }

    protected InteractionResult mobInteract(Player p, InteractionHand hand) {
        if (hand != InteractionHand.MAIN_HAND) {
            return InteractionResult.PASS;
        } else {
            if (!this.level().isClientSide) {
                if (p.getMainHandItem().is((Item)AdventureContent.MANA.get())) {
                    this.mana(this.mana() + 100.0F);
                    if (!p.isCreative()) {
                        p.getMainHandItem().shrink(1);
                    }

                    return InteractionResult.SUCCESS;
                }

                if (this.spec.id.equals("sweet_pact")) {
                    PactSystem.interact(this, p);
                    return InteractionResult.SUCCESS;
                }

                if (p.isShiftKeyDown() && p.getMainHandItem().isEmpty() && (this.owner == null || this.owner.equals(p.getUUID()))) {
                    this.owner = this.owner == null ? p.getUUID() : null;
                    p.displayClientMessage(Component.literal(this.spec.name + (this.owner == null ? "：ここで過ごします。" : "：一緒に行こう。")), false);
                } else {
                    p.displayClientMessage(Component.literal(this.spec.name + " — " + this.spec.ability), false);
                    if (this.spec.id.equals("yggdrasil")) {
                        this.setForm(this.form() == 0 ? 1 : 0);
                    }
                }
            }

            return InteractionResult.sidedSuccess(this.level().isClientSide);
        }
    }

    public void addAdditionalSaveData(CompoundTag n) {
        super.addAdditionalSaveData(n);
        n.putLong("NextRelicDrop", this.nextRelicDrop);
        n.putFloat("AvatarFracture", this.avatarFracture);
        n.putInt("DivineOperatorLevel", this.operatorLevel());
        n.putBoolean("Balanced", this.balanced);
        n.putLong("LoreEvolution", this.loreEvolution);
        n.putFloat("SoulHealth", this.soulHealth);
        n.putBoolean("LoreManaSchema", true);
        ListTag la = new ListTag();
        this.loreAdaptation.stream().sorted().forEach(k -> la.add(StringTag.valueOf(k)));
        n.put("LoreAdaptation", la);
        n.putInt("Evolution", this.evolution);
        n.putInt("Revivals", this.revivals);
        n.putFloat("Mana", this.mana());
        n.putFloat("Shield", this.shield);
        n.putInt("Phase", this.phase());
        n.putInt("Form", this.form());
        n.putBoolean("Arena", this.arena);
        n.putString("TargetSpecies", this.targetSpecies);
        if (this.owner != null) {
            n.putUUID("Owner", this.owner);
        }

        CompoundTag m = new CompoundTag();
        this.memory.entries().forEach(m::putInt);
        n.put("Adaptation", m);
    }

    public void readAdditionalSaveData(CompoundTag n) {
        super.readAdditionalSaveData(n);
        this.nextRelicDrop = Math.max(0L, n.getLong("NextRelicDrop"));
        this.avatarFracture = Float.isFinite(n.getFloat("AvatarFracture")) ? Math.max(0.0F, Math.min(100000.0F, n.getFloat("AvatarFracture"))) : 0.0F;
        this.balanced = n.getBoolean("Balanced");
        this.entityData.set(OPERATOR, OperatorPowers.level(this));
        this.loreEvolution = Math.max(0L, n.getLong("LoreEvolution"));
        this.loreAdaptation.clear();
        n.getList("LoreAdaptation", 8).forEach(k -> this.loreAdaptation.add(k.getAsString()));
        this.soulHealth = n.contains("SoulHealth")
            ? Math.max(0.0F, Math.min(this.spec.loreHealth > 0.0F ? this.spec.loreHealth : this.spec.health, n.getFloat("SoulHealth")))
            : (this.spec.loreHealth > 0.0F ? this.spec.loreHealth : this.spec.health);
        this.evolution = CombatMemory.boundedEvolution(n.getInt("Evolution"));
        this.revivals = Math.max(0, n.getInt("Revivals"));
        this.mana(
            this.lore() && this.spec.loreMana > 0.0F && !n.getBoolean("LoreManaSchema")
                ? this.manaCap()
                : (n.contains("Mana") ? n.getFloat("Mana") : this.manaCap())
        );
        this.shield = Float.isFinite(n.getFloat("Shield")) ? Math.max(0.0F, Math.min(500.0F, n.getFloat("Shield"))) : 0.0F;
        this.entityData.set(PHASE, Math.max(0, Math.min(10, n.getInt("Phase"))));
        this.setForm(n.getInt("Form"));
        this.arena = n.getBoolean("Arena");
        this.targetSpecies = n.getString("TargetSpecies");
        this.owner = n.hasUUID("Owner") ? n.getUUID("Owner") : null;
        CompoundTag m = n.getCompound("Adaptation");
        m.getAllKeys().stream().sorted().limit(128L).forEach(k -> this.memory.restore(k, m.getInt(k)));
    }

    public void remove(RemovalReason reason) {
        if (Boolean.getBoolean("oror.smoke") && this.spec.id.equals("ferdinand") && reason.shouldDestroy()) {
            System.out.println("[OROR_REMOVAL] ferdinand reason=" + reason + " hp=" + this.getHealth() + " uuid=" + this.getUUID());
            new Exception("Developer removal trace").printStackTrace();
        }

        this.bar.removeAllPlayers();
        super.remove(reason);
    }

    private static record Snapshot(Vec3 pos, float hp) {
    }
}
