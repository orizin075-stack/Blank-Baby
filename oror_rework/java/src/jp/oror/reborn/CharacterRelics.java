package jp.oror.reborn;

import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.Item.Properties;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.registries.DeferredItem;

public final class CharacterRelics {
    public static final Map<String, DeferredItem<Item>> ITEMS = new LinkedHashMap<>();

    public static RelicSpec of(ItemStack stack) {
        return stack.getItem() instanceof CharacterRelics.Relic r ? r.spec() : null;
    }

    private static InteractionResultHolder<ItemStack> activate(RelicSpec s, Level l, Player p, InteractionHand hand) {
        ItemStack stack = p.getItemInHand(hand);
        if (p.getCooldowns().isOnCooldown(stack.getItem())) {
            return InteractionResultHolder.fail(stack);
        } else {
            if (!l.isClientSide) {
                if (RelicArts.of(s.id) != null) {
                    if (p.level() instanceof net.minecraft.server.level.ServerLevel sl) {
                        RelicEffects.show(sl, p, s.color, s.rank);
                    }
                    RelicArts.cast(s.id, p);
                } else {
                    RelicPowers.cast(s, p);
                }
                p.getCooldowns().addCooldown(stack.getItem(), RelicArts.cooldown(s.id, s.cooldown));
                if (stack.isDamageableItem()) {
                    stack.hurtAndBreak(1, p, LivingEntity.getSlotForHand(hand));
                }
            }

            return InteractionResultHolder.sidedSuccess(stack, l.isClientSide);
        }
    }

    static {
        for (RelicSpec s : RelicSpec.ALL.values()) {
            ITEMS.put(
                s.id,
                OrorReborn.ITEMS
                    .register(
                        s.id,
                        () -> (Item)(!s.slot.equals("weapon") && !s.slot.equals("legend") ? new CharacterRelics.Artifact(s) : new CharacterRelics.Blade(s))
                    )
            );
        }
    }

    public static final class Artifact extends Item implements CharacterRelics.Relic {
        private final RelicSpec spec;

        Artifact(RelicSpec s) {
            super(new Properties().stacksTo(1).fireResistant().rarity(Rarity.RARE));
            this.spec = s;
        }

        @Override
        public RelicSpec spec() {
            return this.spec;
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            return CharacterRelics.activate(this.spec, l, p, h);
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            CharacterRelics.held(this.spec, stack, l, e);
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, java.util.List<net.minecraft.network.chat.Component> lines, net.minecraft.world.item.TooltipFlag flag) {
            RelicArts.tooltip(this.spec.id, lines);
        }
    }

    public static final class Blade extends SwordItem implements CharacterRelics.Relic {
        private final RelicSpec spec;

        Blade(RelicSpec s) {
            super(
                Tiers.NETHERITE,
                new Properties()
                    .durability(s.rank == 3 ? '\uffff' : 8192)
                    .fireResistant()
                    .rarity(s.rank == 3 ? Rarity.EPIC : Rarity.RARE)
                    .attributes(SwordItem.createAttributes(Tiers.NETHERITE, s.damage, -1.6F))
            );
            this.spec = s;
        }

        @Override
        public RelicSpec spec() {
            return this.spec;
        }

        public boolean isFoil(ItemStack s) {
            return this.spec.rank == 3 || super.isFoil(s);
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            return CharacterRelics.activate(this.spec, l, p, h);
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            CharacterRelics.held(this.spec, stack, l, e);
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, java.util.List<net.minecraft.network.chat.Component> lines, net.minecraft.world.item.TooltipFlag flag) {
            RelicArts.tooltip(this.spec.id, lines);
        }
    }

    /** Passive arts run once a second while the relic is in either hand. */
    static void held(RelicSpec s, ItemStack stack, Level l, Entity e) {
        if (l.isClientSide || !(e instanceof Player p) || p.tickCount % 20 != 0) {
            return;
        }
        if (p.getMainHandItem() != stack && p.getOffhandItem() != stack) {
            return;
        }
        if (RelicArts.of(s.id) != null) {
            RelicArts.passive(s.id, p);
        } else if (s.rank == 3 || s.slot.equals("charm")) {
            RelicPowers.passive(s, p);
        }
    }

    public interface Relic {
        RelicSpec spec();
    }
}
