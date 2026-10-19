package jp.oror.reborn;

import java.util.Map;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation;
import net.minecraft.world.entity.npc.Villager;

public final class VillagerRoles {
    private static final Map<String, VillagerRoles.Role> ROLES = Map.ofEntries(
        Map.entry("armorer", new VillagerRoles.Role("sword", "shield", 1.5, 1.0, 0.85, 8821419)),
        Map.entry("weaponsmith", new VillagerRoles.Role("axe", "axe", 1.15, 1.5, 1.0, 15097676)),
        Map.entry("toolsmith", new VillagerRoles.Role("mace", "terrain", 1.2, 1.15, 1.0, 15054693)),
        Map.entry("fletcher", new VillagerRoles.Role("bow", "bow", 0.95, 1.15, 1.15, 6868624)),
        Map.entry("cleric", new VillagerRoles.Role("sword", "healing", 1.2, 0.9, 1.0, 13011962)),
        Map.entry("librarian", new VillagerRoles.Role("crossbow", "tactics", 1.0, 1.1, 1.05, 7914751)),
        Map.entry("fisherman", new VillagerRoles.Role("trident", "trident", 1.15, 1.15, 1.1, 5294302)),
        Map.entry("farmer", new VillagerRoles.Role("sword", "healing", 1.25, 1.0, 1.0, 9426275)),
        Map.entry("butcher", new VillagerRoles.Role("axe", "axe", 1.1, 1.35, 1.1, 14452091)),
        Map.entry("cartographer", new VillagerRoles.Role("bow", "terrain", 1.0, 1.0, 1.25, 14863730)),
        Map.entry("leatherworker", new VillagerRoles.Role("sword", "shield", 1.15, 1.0, 1.2, 13015666)),
        Map.entry("mason", new VillagerRoles.Role("mace", "terrain", 1.4, 1.2, 0.95, 12238798)),
        Map.entry("shepherd", new VillagerRoles.Role("sword", "teamwork", 1.2, 1.0, 1.05, 15384285)),
        Map.entry("miner", new VillagerRoles.Role("axe", "terrain", 1.25, 1.15, 1.0, 16766051))
    );
    private static final ResourceLocation HP = new ResourceLocation("oror_supreme_bosses", "profession_health");
    private static final ResourceLocation ATK = new ResourceLocation("oror_supreme_bosses", "profession_attack");
    private static final ResourceLocation SPEED = new ResourceLocation("oror_supreme_bosses", "profession_speed");

    public static String profession(Villager v) {
        return BuiltInRegistries.VILLAGER_PROFESSION.getKey(v.getVillagerData().getProfession()).getPath();
    }

    public static VillagerRoles.Role role(Villager v) {
        return ROLES.getOrDefault(profession(v), new VillagerRoles.Role("sword", "tactics", 1.0, 1.0, 1.0, 11911373));
    }

    public static String preferred(Mob m) {
        return RebornConfig.ROLES.get() && m instanceof Villager v ? role(v).weapon() : "";
    }

    public static void refresh(Mob m) {
        if (m instanceof Villager v && (Boolean)RebornConfig.ROLES.get() && !v.isBaby()) {
            CompoundTag n = MobMind.data(m);
            String key = profession(v) + ":" + MobLevels.level(v);
            if (key.equals(n.getString("ProfessionApplied"))) {
                return;
            }

            VillagerRoles.Role r = role(v);
            modifier(v, Attributes.MAX_HEALTH, HP, r.health() - 1.0);
            modifier(v, Attributes.ATTACK_DAMAGE, ATK, r.attack() - 1.0);
            modifier(v, Attributes.MOVEMENT_SPEED, SPEED, r.speed() - 1.0);
            n.putString("ProfessionApplied", key);
            n.putString("ProfessionRole", r.weapon());
            MobMind.practice(v, r.skill(), 8);
            n.remove("Selected");
            return;
        }
    }

    private static void modifier(Villager v, Attribute attribute, ResourceLocation id, double amount) {
        AttributeInstance a = v.getAttribute(attribute);
        if (a != null) {
            Mods.remove(a, id);
            if (amount != 0.0) {
                a.addPermanentModifier(Mods.make(id, amount, Operation.MULTIPLY_BASE));
            }
        }
    }

    public static void ability(Villager v, ServerLevel sl) {
        if ((Boolean)RebornConfig.ROLES.get() && v.tickCount % 100 == Math.floorMod(v.getId(), 100) && AdaptiveCombat.active(v)) {
            String role = profession(v);
            int rank = MobLevels.level(v);
            if (role.equals("cleric") || role.equals("farmer")) {
                for (Villager friend : sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(8.0), a -> a.isAlive() && AdaptiveCombat.allied(v, a))) {
                    friend.heal(role.equals("cleric") ? (float)(3 + rank) : 1.0F + (float)rank * 0.5F);
                    if (role.equals("cleric")) {
                        RelicPowers.cleanse(friend);
                    }
                }

                MobMind.practice(v, "healing", 1);
            }

            if (role.equals("armorer")) {
                v.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 120, rank >= 4 ? 1 : 0));
            }

            if (role.equals("cartographer")) {
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 120, rank >= 4 ? 1 : 0));
            }

            if (role.equals("fisherman")) {
                v.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 120, 0));
            }

            if (role.equals("shepherd")) {
                for (Villager friendx : sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(8.0), a -> a.isAlive())) {
                    friendx.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 120, rank >= 5 ? 1 : 0));
                }
            }
        }
    }

    public static int color(Villager v) {
        return role(v).color();
    }

    private VillagerRoles() {
    }

    public static record Role(String weapon, String skill, double health, double attack, double speed, int color) {
    }
}
