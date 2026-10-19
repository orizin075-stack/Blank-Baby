package jp.oror.reborn;

import java.util.List;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;

public final class MobLevels {
    private MobLevels() {
    }

    public static int lottery(UUID id, double chance) {
        long v = id.getLeastSignificantBits() ^ Long.rotateLeft(id.getMostSignificantBits(), 23);
        v ^= v >>> 33;
        v *= -49064778989728563L;
        v ^= v >>> 33;
        return Long.remainderUnsigned(v, 1000000L) < Math.round(chance * 1000000.0) ? 6 : 0;
    }

    public static int initial(UUID id, double chance) {
        if (lottery(id, chance) == 6) {
            return 6;
        } else {
            int r = Math.floorMod(id.hashCode(), 100);
            return r < 35 ? 1 : (r < 63 ? 2 : (r < 83 ? 3 : (r < 95 ? 4 : 5)));
        }
    }

    public static void initialize(Mob m) {
        CompoundTag n = MobMind.data(m);
        if (!n.getBoolean("LevelInitialized")) {
            int rank = initial(m.getUUID(), (Double)RebornConfig.ELITE_CHANCE.get());
            n.putInt("BaseLevel", m instanceof SupremeEntity && rank != 6 ? 5 : rank);
            n.putBoolean("Elite", rank == 6);
            n.putBoolean("LevelInitialized", true);
        }
    }

    public static int level(Mob m) {
        if (!(Boolean)RebornConfig.MOB_LEVELS.get()) {
            return 1;
        } else {
            initialize(m);
            CompoundTag n = MobMind.data(m);
            if (n.getBoolean("Elite")) {
                return 6;
            } else if (m instanceof Villager v) {
                return net.minecraft.util.Mth.clamp((int)v.getVillagerData().getLevel(), 1, 5);
            } else {
                long xp = Math.max(0L, n.getLong("Experience"));
                long age = MobMind.age(m);
                int trained = 1;
                long[] x = new long[]{250L, 1000L, 4000L, 16000L};
                long[] a = new long[]{48000L, 168000L, 480000L, 1440000L};

                for (int i = 0; i < 4; i++) {
                    if (xp >= x[i] || age >= a[i]) {
                        trained = i + 2;
                    }
                }

                return net.minecraft.util.Mth.clamp((int)Math.max(n.getInt("BaseLevel"), trained), 1, 5);
            }
        }
    }

    public static void set(Mob m, int rank) {
        CompoundTag n = MobMind.data(m);
        n.putBoolean("LevelInitialized", true);
        n.putBoolean("Elite", rank == 6);
        n.putInt("BaseLevel", net.minecraft.util.Mth.clamp((int)rank, 1, 6));
        if (m instanceof Villager v) {
            v.setVillagerData(v.getVillagerData().setLevel(Math.min(5, rank)));
        }

        n.putInt("LoadoutLevel", 0);
        n.remove("Selected");
    }

    public static double power(Mob m) {
        return switch (level(m)) {
            case 2 -> 1.4;
            case 3 -> 2.0;
            case 4 -> 3.0;
            case 5 -> 4.0;
            case 6 -> 8.0;
            default -> 1.0;
        };
    }

    public static int decisionTicks(Mob m) {
        return level(m) >= 5 ? 2 : 4;
    }

    public static int cooldown(Mob m, int base) {
        return Math.max(4, base - (level(m) - 1) * 2);
    }

    public static float accuracy(Mob m, String weapon) {
        double wisdom = Math.log1p((double)MobMind.age(m) / 24000.0) + Math.log1p((double)MobMind.skill(m, weapon));
        return (float)Math.max(0.02, 0.7 - (double)level(m) * 0.1 - wisdom * 0.04);
    }

    public static boolean armored(Mob m) {
        return AdaptiveCombat.guardian(m) || level(m) == 6 && !(m instanceof SupremeEntity) && !(m instanceof FamiliarEntity);
    }

    public static void refresh(Mob m) {
        int rank = level(m);
        CompoundTag n = MobMind.data(m);
        if (m.getCustomName() == null || m.getCustomName().getString().equals(n.getString("RankName"))) {
            Component title = Component.literal("Lv." + rank + " ")
                .withStyle(rank == 6 ? ChatFormatting.GOLD : ChatFormatting.WHITE)
                .append(m.getType().getDescription());
            m.setCustomName(title);
            m.setCustomNameVisible(rank == 6);
            n.putString("RankName", title.getString());
        }

        if (armored(m) && !m.isBaby() && (Boolean)RebornConfig.ARMED_VILLAGERS.get() && n.getInt("LoadoutLevel") != rank) {
            arm(m);
        }

        VillagerRoles.refresh(m);
        TierSignals.refresh(m);
        if (rank == 6) {
            for (MobEffectInstance effect : List.of(
                new MobEffectInstance(MobEffects.DAMAGE_BOOST, 220, 3),
                new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 220, 2),
                new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 220, 1),
                new MobEffectInstance(MobEffects.REGENERATION, 220, 1),
                new MobEffectInstance(MobEffects.ABSORPTION, 220, 3)
            )) {
                m.addEffect(effect);
            }

            if (!m.hasEffect(MobEffects.REGENERATION)) {
                m.heal(8.0F);
            }

            n.putBoolean("LevelBuffs", true);
        } else if (n.getBoolean("LevelBuffs")) {
            for (MobEffect effect : List.of(
                MobEffects.DAMAGE_BOOST, MobEffects.DAMAGE_RESISTANCE, MobEffects.MOVEMENT_SPEED, MobEffects.REGENERATION, MobEffects.ABSORPTION
            )) {
                MobEffectInstance e = m.getEffect(effect);
                if (e != null && e.getDuration() <= 220) {
                    m.removeEffect(effect);
                }
            }

            n.putBoolean("LevelBuffs", false);
        }
    }

    public static void arm(Mob m) {
        int rank = level(m);
        CompoundTag n = MobMind.data(m);
        boolean legacy = n.getBoolean("Armed") && !n.contains("LoadoutLevel");

        for (EquipmentSlot slot : List.of(
            EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.OFFHAND, EquipmentSlot.MAINHAND
        )) {
            String key = "Managed_" + slot.getName();
            ItemStack current = m.getItemBySlot(slot);
            boolean managed = current.isEmpty()
                || legacy
                || n.contains(key) && ItemStack.isSameItemSameTags(current, ItemStack.of(n.getCompound(key)));
            if (managed) {
                ItemStack stack = slot == EquipmentSlot.MAINHAND
                    ? weapon(m, "sword")
                    : (slot == EquipmentSlot.OFFHAND ? Items.SHIELD.getDefaultInstance() : armor(rank, slot).getDefaultInstance());
                if (rank >= 3 && slot != EquipmentSlot.MAINHAND) {
                    ench(m, stack, slot == EquipmentSlot.OFFHAND ? Enchantments.UNBREAKING : Enchantments.ALL_DAMAGE_PROTECTION, rank == 3 ? 2 : 4);
                }

                if (rank >= 5) {
                    ench(m, stack, Enchantments.UNBREAKING, 3);
                }

                m.setItemSlot(slot, stack);
                m.setDropChance(slot, 0.0F);
                n.put(key, stack.save(new CompoundTag()));
                if (slot == EquipmentSlot.MAINHAND) {
                    n.putBoolean("OriginalAuto", true);
                }
            }
        }

        n.putBoolean("Armed", true);
        n.putInt("LoadoutLevel", rank);
        n.remove("Selected");
        AttributeInstance hp = m.getAttribute(Attributes.MAX_HEALTH);
        if (hp != null) {
            if (!n.contains("BeforeArmingHealth")) {
                n.putDouble("BeforeArmingHealth", hp.getBaseValue());
            }

            double base = Math.max(n.getDouble("BeforeArmingHealth"), (double)(256 + 128 * (rank - 1)));
            double ratio = (double)(m.getHealth() / Math.max(1.0F, m.getMaxHealth()));
            hp.setBaseValue(base);
            m.setHealth((float)((double)m.getMaxHealth() * Math.max(ratio, 0.5)));
        }

        if (!n.getBoolean("ArmingTrained")) {
            MobMind.practice(m, "tactics", 20);
            n.putBoolean("ArmingTrained", true);
        }
    }

    private static Item armor(int rank, EquipmentSlot slot) {
        boolean diamond = rank == 2 || rank == 3;
        boolean netherite = rank >= 4;

        return switch (slot) {
            case HEAD -> netherite ? Items.NETHERITE_HELMET : (diamond ? Items.DIAMOND_HELMET : Items.IRON_HELMET);
            case CHEST -> netherite ? Items.NETHERITE_CHESTPLATE : (diamond ? Items.DIAMOND_CHESTPLATE : Items.IRON_CHESTPLATE);
            case LEGS -> netherite ? Items.NETHERITE_LEGGINGS : (diamond ? Items.DIAMOND_LEGGINGS : Items.IRON_LEGGINGS);
            default -> netherite ? Items.NETHERITE_BOOTS : (diamond ? Items.DIAMOND_BOOTS : Items.IRON_BOOTS);
        };
    }

    public static ItemStack weapon(Mob m, String kind) {
        int rank = level(m);

        Item item = switch (kind) {
            case "bow" -> Items.BOW;
            case "crossbow" -> Items.CROSSBOW;
            case "trident" -> Items.TRIDENT;
            case "mace" -> Items.IRON_AXE;
            case "axe" -> rank >= 4 ? Items.NETHERITE_AXE : (rank >= 2 ? Items.DIAMOND_AXE : Items.IRON_AXE);
            case "pickaxe" -> rank >= 4 ? Items.NETHERITE_PICKAXE : (rank >= 2 ? Items.DIAMOND_PICKAXE : Items.IRON_PICKAXE);
            default -> rank == 6
            ? (Item)CharacterRelics.ITEMS.get("kokuhaku_legend").get()
            : (rank >= 4 ? Items.NETHERITE_SWORD : (rank >= 2 ? Items.DIAMOND_SWORD : Items.IRON_SWORD));
        };
        ItemStack stack = item.getDefaultInstance();
        if (rank >= 3) {
            Enchantment enchant = switch (kind) {
                case "bow" -> Enchantments.POWER_ARROWS;
                case "crossbow" -> Enchantments.QUICK_CHARGE;
                case "pickaxe" -> Enchantments.BLOCK_EFFICIENCY;
                case "sword", "axe" -> Enchantments.SHARPNESS;
                default -> Enchantments.UNBREAKING;
            };
            ench(m, stack, enchant, kind.equals("crossbow") ? Math.min(3, rank - 2) : Math.min(5, rank));
        }

        if (rank >= 5) {
            ench(m, stack, Enchantments.UNBREAKING, 3);
        }

        return stack;
    }

    private static void ench(Mob m, ItemStack stack, Enchantment key, int level) {
        stack.enchant(key, level);
    }
}
