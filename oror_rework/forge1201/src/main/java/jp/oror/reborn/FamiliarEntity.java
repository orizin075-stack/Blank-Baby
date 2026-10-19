package jp.oror.reborn;

import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier.Builder;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ProjectileWeaponItem;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

public final class FamiliarEntity extends PathfinderMob {
    private static final EntityDataAccessor<Integer> STYLE = SynchedEntityData.defineId(FamiliarEntity.class, EntityDataSerializers.INT);
    public UUID creator;
    private long expires;
    private int attack;

    public FamiliarEntity(EntityType<? extends FamiliarEntity> type, Level l) {
        super(type, l);
    }

    public static Builder attributes() {
        return Mob.createMobAttributes()
            .add(Attributes.MAX_HEALTH, 40.0)
            .add(Attributes.ATTACK_DAMAGE, 5.0)
            .add(Attributes.MOVEMENT_SPEED, 0.3)
            .add(Attributes.FOLLOW_RANGE, 24.0);
    }

    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(STYLE, 0);
    }

    public int style() {
        return (Integer)this.entityData.get(STYLE);
    }

    public void tick() {
        super.tick();
        if (!this.level().isClientSide && this.level() instanceof ServerLevel sl) {
            if (sl.getGameTime() <= this.expires && this.creator != null && sl.getEntity(this.creator) instanceof SupremeEntity b && b.isAlive()) {
                LivingEntity t = b.getTarget();
                this.setTarget(t);
                LivingEntity aim = (LivingEntity)(t == null ? b : t);
                Vec3 d = aim.position().subtract(this.position());
                if (this.style() == 0) {
                    this.setNoGravity(true);
                    this.setDeltaMovement(
                        this.getDeltaMovement().scale(0.7).add(d.normalize().scale(0.1)).add(0.0, Math.sin((double)this.tickCount * 0.1) * 0.02, 0.0)
                    );
                } else if (d.length() > 2.0) {
                    this.navigation.moveTo(aim, 1.1);
                }

                if (t != null && b.validEnemy(t) && --this.attack <= 0 && this.distanceTo(t) < 5.0F) {
                    if (b.lore()) {
                        LorePowers.strike(b, t, 5.0F, false);
                    } else {
                        t.hurt(this.damageSources().mobAttack(this), 5.0F);
                    }

                    this.attack = 25;
                }
            } else {
                this.discard();
            }
        }
    }

    public static void create(SupremeEntity b, ServerLevel sl, int style, int number) {
        int n = SummonBudget.remaining(sl, b.getUUID(), (Integer)RebornConfig.MAX_SUMMONS.get(), number);

        for (int i = 0; i < n; i++) {
            FamiliarEntity f = (FamiliarEntity)((EntityType)OrorReborn.FAMILIAR.get()).create(sl);
            if (f != null) {
                boolean placed = false;
                double radius = Math.max(2.0, (double)b.getBbWidth() * 0.5 + 1.1);
                double start = b.getRandom().nextDouble() * Math.PI * 2.0;

                for (int attempt = 0; attempt < 12; attempt++) {
                    double angle = start + (double)attempt * 2.399963229728653;
                    Vec3 p = b.position().add(Math.cos(angle) * radius, (double)(1 + attempt % 3), Math.sin(angle) * radius);
                    f.moveTo(p.x, p.y, p.z, 0.0F, 0.0F);
                    if (sl.hasChunkAt(f.blockPosition()) && sl.getWorldBorder().isWithinBounds(f.blockPosition()) && sl.noCollision(f)) {
                        placed = true;
                        break;
                    }
                }

                if (placed) {
                    f.creator = b.getUUID();
                    f.expires = sl.getGameTime() + 1200L;
                    f.entityData.set(STYLE, Math.floorMod(style, 4));
                    f.setCustomName(Component.literal(b.spec.name + "の眷属"));
                    sl.addFreshEntity(f);
                }
            }
        }
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

    public void addAdditionalSaveData(CompoundTag n) {
        super.addAdditionalSaveData(n);
        if (this.creator != null) {
            n.putUUID("Creator", this.creator);
        }

        n.putLong("Expires", this.expires);
        n.putInt("Style", this.style());
    }

    public void readAdditionalSaveData(CompoundTag n) {
        super.readAdditionalSaveData(n);
        this.creator = n.hasUUID("Creator") ? n.getUUID("Creator") : null;
        this.expires = n.getLong("Expires");
        this.entityData.set(STYLE, Math.floorMod(n.getInt("Style"), 4));
    }
}
