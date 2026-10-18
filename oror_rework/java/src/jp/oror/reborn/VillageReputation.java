package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import jp.oror.reborn.mixin.CompoundContainerAccess;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.CompoundContainer;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.village.poi.PoiTypes;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Post;
import net.neoforged.neoforge.event.entity.player.TradeWithVillagerEvent;
import net.neoforged.neoforge.event.entity.player.PlayerContainerEvent.Close;
import net.neoforged.neoforge.event.entity.player.PlayerContainerEvent.Open;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract;
import net.neoforged.neoforge.event.level.BlockEvent.BreakEvent;
import net.neoforged.neoforge.event.level.BlockEvent.EntityPlaceEvent;

public final class VillageReputation {
    private static final Map<Player, VillageReputation.Theft> OPEN = new WeakHashMap<>();

    public static int score(Mob v, UUID player) {
        VillageLedger.Village village = VillageLedger.of(v);
        return village == null ? 0 : village.score(player);
    }

    public static boolean sameVillage(Mob a, Mob b) {
        VillageLedger.Village av = VillageLedger.of(a);
        VillageLedger.Village bv = VillageLedger.of(b);
        return av != null && bv != null && av.id.equals(bv.id);
    }

    public static int change(ServerLevel sl, VillageLedger.Village village, Player player, int delta, String reason) {
        if (player != null && (Boolean)RebornConfig.VILLAGE_SCORE.get() && village != null) {
            int result = VillageLedger.get(sl).change(village, player.getUUID(), delta, sl.getGameTime(), reason);
            if (delta < 0 || player.isShiftKeyDown()) {
                player.displayClientMessage(Component.literal("村人スコア " + result + "（" + reason + "）"), true);
            }

            return result;
        } else {
            return 0;
        }
    }

    public static void trade(TradeWithVillagerEvent e) {
        if (e.getAbstractVillager() instanceof Villager v && v.level() instanceof ServerLevel sl) {
            change(sl, VillageLedger.of(v), e.getEntity(), 3, "取引");
            // v0.17.15: the emeralds a player pays stay in the village (the villager carries them to the communal chests)
            int paid = 0;
            for (ItemStack cost : List.of(e.getMerchantOffer().getCostA(), e.getMerchantOffer().getCostB())) {
                if (cost.is(net.minecraft.world.item.Items.EMERALD)) {
                    paid += cost.getCount();
                }
            }
            if (paid > 0) {
                ItemStack rest = v.getInventory().addItem(new ItemStack(net.minecraft.world.item.Items.EMERALD, paid));
                if (!rest.isEmpty() && VillageLedger.of(v) != null) {
                    VillageProgress db = VillageProgress.get(sl);
                    db.deliver(db.of(VillageLedger.of(v)), List.of(rest), sl.registryAccess());
                }
            }
        }
    }

    public static void interact(EntityInteract e) {
        // v0.17.16: a trader in its true colours does not trade
        if (WanderingTraders.refuse(e)) {
            return;
        }
        if (e.getHand() == InteractionHand.MAIN_HAND
            && e.getTarget() instanceof Villager v
            && v.level() instanceof ServerLevel sl
            && (Boolean)RebornConfig.VILLAGE_SCORE.get()) {
            Player p = e.getEntity();
            VillageLedger.Village village = VillageLedger.of(v);
            ItemStack stack = p.getMainHandItem();
            if (village.score(p.getUUID()) <= -80) {
                p.displayClientMessage(Component.literal("この村から敵と見なされています。村人スコア " + village.score(p.getUUID())), true);
                e.setCancellationResult(InteractionResult.FAIL);
                e.setCanceled(true);
            } else if (p.isShiftKeyDown() && stack.isEmpty()) {
                // This handler cancels the event, so later listeners never see it: select the
                // conversation partner here, and leave miners to VillagerIndustry (cargo hand-over).
                if (p instanceof ServerPlayer sp) {
                    MobConversation.focus(v, sp);
                }

                if (VillagerIndustry.miner(v)) {
                    return;
                }

                p.displayClientMessage(
                    Component.literal("村人スコア " + village.score(p.getUUID()) + " / 村 " + village.center.toShortString() + " / " + VillagerLife.status(v)), false
                );
                e.setCancellationResult(InteractionResult.SUCCESS);
                e.setCanceled(true);
            } else if (p.isShiftKeyDown() && stack.has(DataComponents.FOOD) && v.getInventory().canAddItem(stack.copyWithCount(1))) {
                v.getInventory().addItem(stack.copyWithCount(1));
                if (!p.isCreative()) {
                    stack.shrink(1);
                }

                v.heal(2.0F);
                change(sl, village, p, 2, "食事の差し入れ");
                e.setCancellationResult(InteractionResult.SUCCESS);
                e.setCanceled(true);
            } else {
                if (p.isShiftKeyDown() && !stack.isEmpty() && MobEquipmentUse.supported(stack)) {
                    v.setItemSlot(EquipmentSlot.MAINHAND, stack.copyWithCount(1));
                    if (!p.isCreative()) {
                        stack.shrink(1);
                    }

                    CompoundTag n = MobMind.data(v);
                    n.remove("OriginalWeapon");
                    n.remove("Selected");
                    // v0.17.17: a player's gift is the villager's own, never put away as issued gear
                    n.remove("Managed_mainhand");
                    n.putBoolean("OriginalAuto", false);
                    n.putString("Weapon", MobEquipmentUse.kind(v.getMainHandItem()));
                    change(sl, village, p, 4, "装備の提供");
                    e.setCancellationResult(InteractionResult.SUCCESS);
                    e.setCanceled(true);
                }
            }
        }
    }

    public static boolean job(BlockState s) {
        return PoiTypes.forState(s).isPresent();
    }

    public static void placed(EntityPlaceEvent e) {
        if (e.getEntity() instanceof Player p
            && !(p instanceof FakePlayer)
            && p.level() instanceof ServerLevel sl
            && !e.isCanceled()
            && (Boolean)RebornConfig.VILLAGE_SCORE.get()) {
            VillageLedger db = VillageLedger.get(sl);
            VillageLedger.Village village = db.nearest(e.getPos());
            if (village == null) {
                return;
            }

            boolean fresh = !village.property.containsKey(e.getPos().asLong());
            village.property.put(e.getPos().asLong(), p.getUUID());
            db.setDirty();
            if (!fresh) {
                return;
            }

            int points = e.getPlacedBlock().getBlock() instanceof BedBlock
                ? 6
                : (job(e.getPlacedBlock()) ? 4 : (e.getPlacedBlock().is(Blocks.FARMLAND) ? 2 : 0));
            if (points > 0) {
                change(sl, village, p, points, "村の設備建設");
            }

            return;
        }
    }

    public static void broken(BreakEvent e) {
        if (!(e.getPlayer() instanceof FakePlayer) && e.getLevel() instanceof ServerLevel sl && !e.isCanceled() && (Boolean)RebornConfig.VILLAGE_SCORE.get()) {
            VillageLedger db = VillageLedger.get(sl);
            VillageLedger.Village village = db.nearest(e.getPos());
            if (village != null) {
                BlockState state = e.getState();
                int penalty = state.getBlock() instanceof BedBlock ? -60 : (job(state) ? -35 : (state.getBlock() instanceof ChestBlock ? -45 : 0));
                if (e.getPlayer().getUUID().equals(village.property.get(e.getPos().asLong()))) {
                    penalty = 0;
                }

                village.property.remove(e.getPos().asLong());
                village.communal.remove(e.getPos().asLong());
                db.setDirty();
                if (penalty != 0) {
                    change(sl, village, e.getPlayer(), penalty, "村の設備破壊");
                }
            }
        }
    }

    public static void damaged(Post e) {
        if (e.getEntity() instanceof Villager v
            && e.getSource().getEntity() instanceof Player p
            && e.getOriginalDamage() > 0.0F
            && v.level() instanceof ServerLevel sl) {
            change(sl, VillageLedger.of(v), p, -120, "村人への攻撃");
        }
    }

    public static void death(LivingDeathEvent e) {
        // v0.17.16: the last of a party, a trader's or a raid's end
        VillageFeuds.died(e);
        WanderingTraders.died(e);
        VillageRaids.died(e);
        if (e.getEntity() instanceof Villager v && e.getSource().getEntity() instanceof Player p && v.level() instanceof ServerLevel sl) {
            change(sl, VillageLedger.of(v), p, -400, "村人の殺害");
        }
    }

    public static boolean villageOwned(ServerLevel sl, BlockPos pos) {
        VillageLedger.Village village = VillageLedger.get(sl).nearest(pos);
        return village != null && (village.property.containsKey(pos.asLong()) || village.communal.contains(pos.asLong()));
    }

    public static Container communalChest(ServerLevel sl, VillageLedger.Village village, BlockPos pos) {
        if (sl.hasChunkAt(pos) && village.contains(pos) && !village.property.containsKey(pos.asLong()) && sl.getBlockEntity(pos) instanceof ChestBlockEntity c) {
            village.communal.add(pos.asLong());
            VillageLedger.get(sl).setDirty();
            return c;
        } else {
            return null;
        }
    }

    private static BlockPos chestPos(Container c) {
        if (c instanceof ChestBlockEntity box) {
            return box.getBlockPos();
        } else if (c instanceof CompoundContainer both) {
            BlockPos a = chestPos(((CompoundContainerAccess)both).oror$getFirst());
            return a != null ? a : chestPos(((CompoundContainerAccess)both).oror$getSecond());
        } else {
            return null;
        }
    }

    private static boolean privateChest(Container c, VillageLedger.Village village) {
        if (c instanceof CompoundContainer both) {
            return privateChest(((CompoundContainerAccess)both).oror$getFirst(), village)
                || privateChest(((CompoundContainerAccess)both).oror$getSecond(), village);
        } else {
            BlockPos pos = chestPos(c);
            return pos == null || village.property.containsKey(pos.asLong());
        }
    }

    public static List<ItemStack> snapshot(Container c) {
        ArrayList<ItemStack> stacks = new ArrayList<>();

        for (int i = 0; i < c.getContainerSize(); i++) {
            stacks.add(c.getItem(i).copy());
        }

        return stacks;
    }

    public static int removed(List<ItemStack> before, Container after) {
        List<ItemStack> remaining = snapshot(after);
        int missing = 0;

        for (ItemStack old : before) {
            int needed = old.getCount();

            for (ItemStack current : remaining) {
                if (ItemStack.isSameItemSameComponents(old, current)) {
                    int use = Math.min(needed, current.getCount());
                    needed -= use;
                    current.shrink(use);
                }
            }

            missing += needed;
        }

        return missing;
    }

    public static void open(Open e) {
        if (e.getEntity().level() instanceof ServerLevel sl && e.getContainer() instanceof ChestMenu menu && (Boolean)RebornConfig.VILLAGE_SCORE.get()) {
            Container c = menu.getContainer();
            BlockPos at = chestPos(c);
            if (at == null) {
                return;
            }

            VillageLedger.Village village = VillageLedger.get(sl).nearest(at);
            if (village != null && !privateChest(c, village)) {
                OPEN.put(e.getEntity(), new VillageReputation.Theft(c, village, snapshot(c)));
                if (village.score(e.getEntity().getUUID()) < 200) {
                    change(sl, village, e.getEntity(), -3, "村の収納を無断で開く");
                }

                return;
            }

            return;
        }
    }

    public static void close(Close e) {
        VillageReputation.Theft theft = OPEN.remove(e.getEntity());
        if (theft != null && e.getEntity().level() instanceof ServerLevel sl && theft.village.score(e.getEntity().getUUID()) < 200) {
            int stolen = removed(theft.before, theft.container);
            if (stolen > 0) {
                change(sl, theft.village, e.getEntity(), -Math.min(300, 10 + stolen * 2), "村の物資の持ち去り");
            }
        }
    }

    public static void tick(net.neoforged.neoforge.event.tick.EntityTickEvent.Post e) {
        if (e.getEntity() instanceof Villager v
            && v.level() instanceof ServerLevel sl
            && !v.isBaby()
            && v.isAlive()
            && !v.isNoAi()
            && (Boolean)RebornConfig.VILLAGE_SCORE.get()
            && v.tickCount % 40 == Math.floorMod(v.getId(), 40)) {
            VillageLedger.Village village = VillageLedger.of(v);

            for (ServerPlayer p : sl.players()) {
                if (village.contains(p.blockPosition()) && !(v.distanceToSqr(p) > 1600.0)) {
                    int score = village.score(p.getUUID());
                    if (score <= -80 && !p.isCreative() && !p.isSpectator()) {
                        VillageFeuds.gossip(v, p);
                        v.setTarget(p);
                        MobMind.data(v).putBoolean("VillageRetaliation", true);
                        break;
                    }

                    if (score >= 100 && v.distanceToSqr(p) < 64.0 && sl.getGameTime() >= v.getPersistentData().getLong("OrorNextService")) {
                        p.heal(score >= 500 ? 6.0F : 2.0F);
                        RelicPowers.cleanse(p);
                        v.getPersistentData().putLong("OrorNextService", sl.getGameTime() + 600L);
                        VillagerLife.count(v, "Services");
                    }
                }
            }

            if (v.getTarget() instanceof Player px
                && MobMind.data(v).getBoolean("VillageRetaliation")
                && (village.score(px.getUUID()) > -80 || !village.contains(px.blockPosition()))) {
                v.setTarget(null);
                v.setLastHurtByMob(null);
                MobMind.data(v).remove("VillageRetaliation");
            }

            return;
        }
    }

    public static void prices(Villager v, Player p) {
        if (p != null && (Boolean)RebornConfig.VILLAGE_SCORE.get()) {
            int score = score(v, p.getUUID());
            double fraction = score >= 500 ? -0.5 : (score >= 200 ? -0.3 : (score >= 50 ? -0.15 : (score < 0 ? 0.25 : 0.0)));
            if (fraction != 0.0) {
                for (MerchantOffer offer : v.getOffers()) {
                    offer.addToSpecialPriceDiff((int)Math.floor((double)offer.getBaseCostA().getCount() * fraction));
                }
            }
        }
    }

    private VillageReputation() {
    }

    private static record Theft(Container container, VillageLedger.Village village, List<ItemStack> before) {
    }
}
