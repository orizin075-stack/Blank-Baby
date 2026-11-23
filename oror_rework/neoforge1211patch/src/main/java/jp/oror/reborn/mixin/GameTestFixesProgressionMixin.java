package jp.oror.reborn.mixin;

import jp.oror.reborn.VillagerIndustry;
import jp.oror.reborn.ci.GameTestFixes;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.Container;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.ArrayList;
import java.util.List;

/** (r66) ProgressionGameTests: the miners' ore under a roof, as a miner digs only underground since 053 (GameTestFixes.roof). */
@Mixin(targets = "jp.oror.reborn.ProgressionGameTests", remap = false)
public abstract class GameTestFixesProgressionMixin {
    @Shadow(remap = false)
    private static Villager worker(GameTestHelper h, int x, int z, int rank) {
        throw new AssertionError();
    }

    @Shadow(remap = false)
    private static ChestBlockEntity box(GameTestHelper h, Villager v) {
        throw new AssertionError();
    }

    @Shadow(remap = false)
    private static int count(Container c, Item item) {
        throw new AssertionError();
    }

    @Inject(method = "critical_attack_waits_for_actual_descending_jump", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$critical(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.criticalJump(h);
        ci.cancel();
    }

    /**
     * The master villager's duel with the netherite player: as one of the village's fighters (an armorer). Without a
     * trade it is a civilian, which fights back only while cornered and walks off once a dodge takes it out of reach
     * (passing some runs and not others since 052).
     */
    @org.spongepowered.asm.mixin.injection.Redirect(method = "master_villager_defeats_fully_enchanted_netherite_player",
        at = @At(value = "INVOKE", target = "Ljp/oror/reborn/AdaptiveCombat;arm(Lnet/minecraft/world/entity/Mob;)V", remap = false), remap = false)
    private static void oror$masterFighter(net.minecraft.world.entity.Mob m) {
        if (m instanceof Villager v) {
            v.setVillagerData(v.getVillagerData().setProfession(net.minecraft.world.entity.npc.VillagerProfession.ARMORER));
        }
        jp.oror.reborn.AdaptiveCombat.arm(m);
    }

    /** (r68: failed in 2 of the last 4 full runs) each strike of the master on the netherite player, told (GameTestFixes.masterTrace). */
    @Inject(method = "lambda$master_villager_defeats_fully_enchanted_netherite_player$1", at = @At("HEAD"), require = 1, remap = false)
    private static void oror$masterTrace(GameTestHelper h, net.minecraft.world.entity.player.Player p, Villager v, CallbackInfo ci) {
        GameTestFixes.masterTrace(p, v);
    }

    @Inject(method = "buried_ore_is_excavated_smelted_and_collected", at = @At("RETURN"), remap = false)
    private static void oror$buried(GameTestHelper h, CallbackInfo ci) {
        GameTestFixes.roof(h, 3, 17, 3, 13);
    }

    /**
     * Three miners at once, each its own furnace, chest and ore. The old test set them 37 blocks apart (x 8, 45 and 82),
     * out of its own 32-block ground into its neighbours' (which other tests clear and build on); here side by side in its
     * own, 11 blocks apart, at trade level two (a search ten blocks round its furnace: none sees another's ore), the ore
     * under a roof.
     */
    @Inject(method = "three_miners_work_simultaneously_without_material_duplication", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$three(GameTestHelper h, CallbackInfo ci) {
        List<Villager> workers = new ArrayList<>();
        for (int z : new int[]{5, 16, 27}) {
            Villager v = worker(h, 8, z, 2);
            workers.add(v);
            h.setBlock(11, 2, z, Blocks.IRON_ORE);
        }
        GameTestFixes.roof(h, 3, 17, 0, 31);
        h.succeedWhen(() -> {
            int products = 0;
            StringBuilder seen = new StringBuilder();
            for (Villager v : workers) {
                int mined = VillagerIndustry.data(v).getInt("OresMined"), made = count(box(h, v), Items.IRON_INGOT);
                seen.append(" [").append(mined).append(" mined, ").append(made).append(" made: ").append(VillagerIndustry.status(v)).append(']');
                products += made;
            }
            for (Villager v : workers) {
                h.assertTrue(VillagerIndustry.data(v).getInt("OresMined") == 1 && count(box(h, v), Items.IRON_INGOT) == 1,
                    "Each independent furnace produced exactly one ingot:" + seen);
            }
            h.assertTrue(products == 3, "Three ore blocks produced three products:" + seen);
        });
        ci.cancel();
    }
}
