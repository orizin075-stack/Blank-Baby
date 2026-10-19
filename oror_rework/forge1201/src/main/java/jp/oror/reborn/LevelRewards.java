package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.Level;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.event.entity.living.LivingExperienceDropEvent;

public final class LevelRewards {
    public static List<ItemStack> rewards(int level, Random random, boolean miracles) {
        ArrayList<ItemStack> out = new ArrayList<>();
        out.add(new ItemStack(Items.EMERALD, new int[]{0, 1, 3, 6, 12, 24, 48}[Math.clamp((long)level, 1, 6)]));
        if (level >= 3) {
            out.add(new ItemStack(Items.DIAMOND, level - 2));
        }

        if (level >= 4) {
            out.add(new ItemStack(Items.NETHERITE_SCRAP, level - 3));
        }

        if (level >= 5) {
            out.add(new ItemStack((ItemLike)AdventureContent.STAR.get(), level));
        }

        if (level == 6) {
            out.add(new ItemStack(Items.NETHERITE_INGOT, 2));
        }

        if (level >= 4 && random.nextDouble() < 0.01 * (double)level) {
            String[] ids = new String[]{"agony", "herrscher", "ruine", "moonless", "solar", "antitheus"};
            Item item = miracles ? (Item)BuiltInRegistries.ITEM.get(new ResourceLocation("wom", ids[random.nextInt(ids.length)])) : Items.AIR;
            if (item == Items.AIR) {
                item = (Item)CharacterRelics.ITEMS.get("kokuhaku_weapon").get();
            }

            out.add(item.getDefaultInstance());
        }

        return out;
    }

    public static void drops(LivingDropsEvent e) {
        if (e.getEntity() instanceof Mob mob
            && (Boolean)RebornConfig.LEVEL_REWARDS.get()
            && e.getSource().getEntity() instanceof Player
            && !(mob instanceof SupremeEntity)
            && !(mob instanceof FamiliarEntity)
            && !mob.getPersistentData().hasUUID("ororRelicOwner")
            && !MobMind.data(mob).getBoolean("RankRewardPaid")) {
            MobMind.data(mob).putBoolean("RankRewardPaid", true);
            Level level = mob.level();

            for (ItemStack stack : rewards(
                MobLevels.level(mob), new Random(level.getGameTime() ^ mob.getUUID().getLeastSignificantBits()), ModList.get().isLoaded("wom")
            )) {
                e.getDrops().add(new ItemEntity(level, mob.getX(), mob.getY(), mob.getZ(), stack));
            }

            return;
        }
    }

    public static void xp(LivingExperienceDropEvent e) {
        if (e.getEntity() instanceof Mob mob
            && (Boolean)RebornConfig.LEVEL_REWARDS.get()
            && e.getAttackingPlayer() != null
            && !mob.getPersistentData().hasUUID("ororRelicOwner")) {
            e.setDroppedExperience(Math.min(4096, Math.max(e.getDroppedExperience(), 5) * MobLevels.level(mob) * MobLevels.level(mob)));
        }
    }

    private LevelRewards() {
    }
}
