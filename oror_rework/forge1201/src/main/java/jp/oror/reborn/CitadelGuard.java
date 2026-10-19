package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.network.syncher.SynchedEntityData.Builder;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.DyedItemColor;
import net.minecraft.world.level.Level;

public final class CitadelGuard extends Zombie {
    private static final EntityDataAccessor<Integer> THEME = SynchedEntityData.defineId(CitadelGuard.class, EntityDataSerializers.INT);

    public CitadelGuard(EntityType<? extends Zombie> type, Level world) {
        super(type, world);
    }

    protected void defineSynchedData(Builder builder) {
        super.defineSynchedData(builder);
        builder.define(THEME, 0);
    }

    public String theme() {
        return new ArrayList<>(CharacterSpec.ALL.keySet())
            .get(Math.clamp((long)((Integer)this.entityData.get(THEME)).intValue(), 0, CharacterSpec.ALL.size() - 1));
    }

    public void readAdditionalSaveData(CompoundTag n) {
        super.readAdditionalSaveData(n);
        String kind = n.getString("DungeonKind");
        int index = new ArrayList<>(CharacterSpec.ALL.keySet()).indexOf(kind);
        this.entityData.set(THEME, Math.max(0, index));
        this.getPersistentData().putString("DungeonKind", this.theme());
        int role = n.getInt("DungeonRole");
        this.getPersistentData().putInt("DungeonRole", role);
        int rank = n.contains("DungeonLevel") ? Math.clamp((long)n.getInt("DungeonLevel"), 1, 6) : 3;
        MobLevels.set(this, rank);
        MobMind.data(this).putString("Weapon", role % 2 == 1 ? "bow" : "sword");
        MobMind.practice(this, role % 2 == 1 ? "bow" : "sword", 20);

        for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET)) {
            Item item = switch (slot) {
                case HEAD -> Items.LEATHER_HELMET;
                case CHEST -> Items.LEATHER_CHESTPLATE;
                case LEGS -> Items.LEATHER_LEGGINGS;
                default -> Items.LEATHER_BOOTS;
            };
            ItemStack stack = item.getDefaultInstance();
            stack.set(DataComponents.DYED_COLOR, new DyedItemColor(CharacterSpec.ALL.get(this.theme()).accent, false));
            this.setItemSlot(slot, stack);
        }

        this.setItemSlot(EquipmentSlot.MAINHAND, (role % 2 == 1 ? Items.BOW : Items.DIAMOND_SWORD).getDefaultInstance());
        this.setPersistenceRequired();
    }

    public void addAdditionalSaveData(CompoundTag n) {
        super.addAdditionalSaveData(n);
        n.putString("DungeonKind", this.theme());
        n.putInt("DungeonRole", this.getPersistentData().getInt("DungeonRole"));
        n.putInt("DungeonLevel", MobLevels.level(this));
    }
}
