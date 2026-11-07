package jp.oror.reborn.village;

import jp.oror.reborn.MobLevels;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;

/**
 * (053) A villager's health when it takes up arms. It went from 20 to 256 + 128 per level (MobLevels.arm: 768 at level
 * 5, and more with its trade's share, over a thousand for a level-5 armourer), and stayed there: far too much for a
 * villager (the user). Now 40 at level 1, fifteen more a level (100 at level 5), 140 for an elite (first 30-70, then
 * "a little more" (the user)); its trade's share (a
 * mason's +40%...) and a veteran's are still added on top. Villagers armed before 053 are brought down to it when they
 * are next loaded. Only villagers and wandering traders: the kingdom's people, the guards of Guard Villagers and the
 * other armed mobs keep theirs.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class VillagerHealth {
    private VillagerHealth() {
    }

    public static double armed(int level) {
        return level >= 6 ? 140.0 : 40.0 + 15.0 * (Math.max(1, Math.min(5, level)) - 1);
    }

    /** After MobLevels.arm (and on loading): a villager's base health no more than its level's. */
    public static void cap(Mob m) {
        if (!(m instanceof AbstractVillager)) {
            return;
        }
        AttributeInstance hp = m.getAttribute(Attributes.MAX_HEALTH);
        CompoundTag mind = m.getPersistentData().getCompound("OrorMind");
        if (hp == null || !mind.contains("BeforeArmingHealth")) {
            return;
        }
        double target = Math.max(mind.getDouble("BeforeArmingHealth"), armed(MobLevels.level(m)));
        if (hp.getBaseValue() <= target + 0.01) {
            return;
        }
        float ratio = m.getHealth() / Math.max(1F, m.getMaxHealth());
        hp.setBaseValue(target);
        m.setHealth(Math.max(1F, Math.min(m.getMaxHealth(), ratio * m.getMaxHealth())));
    }

    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        if (!e.getLevel().isClientSide() && e.getEntity() instanceof AbstractVillager v) {
            cap(v);
        }
    }
}
