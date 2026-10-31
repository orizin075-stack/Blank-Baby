package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.Level;
import net.neoforged.fml.ModList;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.living.LivingExperienceDropEvent;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * What a ranked enemy leaves besides its own loot. Every kill used to pay emeralds, diamonds, netherite scrap and
 * ingots by the stack (a level-6 zombie: 48 emeralds, 4 diamonds, 3 scrap, 2 ingots), animals and villagers included.
 * Now only enemies pay, mostly in more of what they carry anyway (a ranked skeleton drops more bones and arrows), with a
 * few emeralds, and a gem or a scrap of netherite only now and then from the strongest.
 */
public final class LevelRewards {
    private LevelRewards() {
    }

    /** The coin and the rare finds for a rank (1-6): a few emeralds always, the rest by chance. */
    public static List<ItemStack> rewards(int level, Random random, boolean miracles) {
        List<ItemStack> out = new ArrayList<>();
        int rank = Math.clamp(level, 1, 6);
        out.add(new ItemStack(Items.EMERALD, rank));
        if (rank >= 4 && random.nextDouble() < 0.08 * (rank - 3)) {
            out.add(new ItemStack(Items.DIAMOND));
        }
        if (rank >= 5 && random.nextDouble() < 0.2) {
            out.add(new ItemStack((ItemLike) AdventureContent.STAR.get()));
        }
        if (rank == 6 && random.nextDouble() < 0.12) {
            out.add(new ItemStack(Items.NETHERITE_SCRAP));
        }
        if (rank >= 4 && random.nextDouble() < 0.005 * rank) {
            String[] ids = {"agony", "herrscher", "ruine", "moonless", "solar", "antitheus"};
            Item item = miracles ? BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("wom", ids[random.nextInt(ids.length)])) : Items.AIR;
            if (item == Items.AIR) {
                item = (Item) ((DeferredItem<?>) CharacterRelics.ITEMS.get("kokuhaku_weapon")).get();
            }
            out.add(item.getDefaultInstance());
        }
        return out;
    }

    public static void drops(LivingDropsEvent e) {
        if (!(e.getEntity() instanceof Mob mob) || !(mob instanceof Enemy) || !RebornConfig.LEVEL_REWARDS.get()
            || !(e.getSource().getEntity() instanceof Player) || mob instanceof SupremeEntity || mob instanceof FamiliarEntity
            || mob.getPersistentData().hasUUID("ororRelicOwner") || MobMind.data(mob).getBoolean("RankRewardPaid")) {
            return;
        }
        MobMind.data(mob).putBoolean("RankRewardPaid", true);
        Level level = mob.level();
        int rank = MobLevels.level(mob);
        if (rank <= 1) {
            return;
        }
        Random random = new Random(level.getGameTime() ^ mob.getUUID().getLeastSignificantBits());
        // more of its own loot: one more of a random drop for every rank above the first (equipment excluded)
        List<ItemStack> own = new ArrayList<>();
        for (ItemEntity drop : e.getDrops()) {
            ItemStack s = drop.getItem();
            if (!s.isEmpty() && s.isStackable()) {
                own.add(s);
            }
        }
        for (int i = 1; i < rank && !own.isEmpty(); i++) {
            ItemStack pick = own.get(random.nextInt(own.size()));
            e.getDrops().add(new ItemEntity(level, mob.getX(), mob.getY(), mob.getZ(), pick.copyWithCount(1 + random.nextInt(2))));
        }
        for (ItemStack stack : rewards(rank - 1, random, ModList.get().isLoaded("wom"))) {
            e.getDrops().add(new ItemEntity(level, mob.getX(), mob.getY(), mob.getZ(), stack));
        }
    }

    public static void xp(LivingExperienceDropEvent e) {
        if (e.getEntity() instanceof Mob mob && RebornConfig.LEVEL_REWARDS.get() && e.getAttackingPlayer() != null
            && !mob.getPersistentData().hasUUID("ororRelicOwner")) {
            e.setDroppedExperience(Math.min(4096, Math.max(e.getDroppedExperience(), 5) * MobLevels.level(mob) * MobLevels.level(mob)));
        }
    }
}
