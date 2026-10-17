package jp.oror.reborn;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ShieldItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.Item.Properties;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import jp.oror.reborn.RelicArts.Art;
import net.neoforged.neoforge.common.ItemAbilities;
import net.neoforged.neoforge.common.ItemAbility;
import net.neoforged.neoforge.registries.DeferredItem;

/**
 * The 164 character relics. Weapons and legends are wielded according to their kind (weapon_kinds.json, written by
 * tools/mc/weapon_kinds.py): melee kinds differ in speed, reach, knockback and sweep and use their art on right-click;
 * catalysts, guns and cannons shoot, bows draw and shields block on right-click, with the art on sneak + right-click.
 */
public final class CharacterRelics {
    public static final Map<String, DeferredItem<Item>> ITEMS = new LinkedHashMap<>();
    public static final Map<String, Kind> KINDS = new HashMap<>();
    private static final Map<String, String> BY_CHARACTER = new HashMap<>();
    /** Damage multiplier of relic weapons by rank (weapon_kinds.json "power"). */
    private static final Map<Integer, Float> POWER = new HashMap<>();
    private static final ResourceLocation REACH_ID = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "weapon_kind_reach");
    private static final ResourceLocation KNOCK_ID = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "weapon_kind_knockback");
    /** The netherite tier bonus SwordItem.createAttributes added to every relic's damage. */
    private static final float TIER_BONUS = 4.0F;

    public static final class Kind {
        public String id = "sword";
        public float speed = -1.8F;
        public float mul = 1.0F;
        public float reach;
        public float knock;
        public float shot;
        public boolean sweep = true;
        public String mode = "melee";
        public int gap;

        /** Shooting and guarding kinds keep right-click for the weapon itself. */
        public boolean ranged() {
            return !this.mode.equals("melee");
        }
    }

    static {
        try (InputStream in = CharacterRelics.class.getResourceAsStream("/assets/oror_supreme_bosses/weapon_kinds.json")) {
            if (in == null) {
                throw new IllegalStateException("Missing weapon_kinds.json");
            }
            JsonObject top = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
            JsonObject kinds = top.getAsJsonObject("kinds");
            for (String id : kinds.keySet()) {
                JsonObject o = kinds.getAsJsonObject(id);
                Kind k = new Kind();
                k.id = id;
                k.speed = o.get("speed").getAsFloat();
                k.mul = o.get("mul").getAsFloat();
                k.reach = o.get("reach").getAsFloat();
                k.knock = o.get("knock").getAsFloat();
                k.shot = o.get("shot").getAsFloat();
                k.sweep = o.get("sweep").getAsBoolean();
                k.mode = o.get("mode").getAsString();
                k.gap = o.get("gap").getAsInt();
                KINDS.put(id, k);
            }
            JsonObject power = top.getAsJsonObject("power");
            for (String r : power.keySet()) {
                POWER.put(Integer.parseInt(r), power.get(r).getAsFloat());
            }
            JsonObject chars = top.getAsJsonObject("characters");
            for (String c : chars.keySet()) {
                BY_CHARACTER.put(c, chars.get(c).getAsString());
            }
        } catch (Exception e) {
            throw new IllegalStateException("Invalid weapon_kinds.json", e);
        }
    }

    private static Kind kind(String id) {
        Kind k = id == null ? null : KINDS.get(id);
        return k != null ? k : new Kind();
    }

    public static Kind kindOf(String character) {
        return kind(BY_CHARACTER.get(character));
    }

    public static RelicSpec of(ItemStack stack) {
        return stack.getItem() instanceof CharacterRelics.Relic r ? r.spec() : null;
    }

    /** A wielded relic: its spec, the art it casts, its kind and its attack damage before the kind multiplier. */
    public static final class Wield {
        public final RelicSpec spec;
        public final String art;
        public final Kind kind;
        public final float damage;
        public final int rank;
        final int cooldown;

        Wield(RelicSpec spec, String art, Kind kind, float damage, int rank, int cooldown) {
            this.spec = spec;
            this.art = art;
            this.kind = kind;
            this.damage = damage;
            this.rank = rank;
            this.cooldown = cooldown;
        }
    }

    // ------------------------------------------------------------------------------------- factories
    private static Item relic(RelicSpec s) {
        if (!s.slot.equals("weapon") && !s.slot.equals("legend")) {
            return new CharacterRelics.Artifact(s);
        }
        Wield w = new Wield(s, s.id, kindOf(s.character), (s.damage + TIER_BONUS) * POWER.getOrDefault(s.rank, 1.0F), s.rank, s.cooldown);
        return make(w, s.rank == 3 ? 65535 : 8192, s.rank == 3 ? Rarity.EPIC : Rarity.RARE);
    }

    private static Item make(Wield w, int durability, Rarity rarity) {
        Properties props = new Properties().fireResistant().rarity(rarity);
        return switch (w.kind.mode) {
            case "bow" -> new CharacterRelics.Bow(w, props.durability(durability));
            // A blocked lore-mode hit (1e6 damage) would wear any durability away at once, so relic shields do not wear.
            case "guard" -> new CharacterRelics.Shield(w, props.stacksTo(1));
            default -> new CharacterRelics.Blade(w, props.durability(durability));
        };
    }

    // ------------------------------------------------------------------------------------- right-click
    private static InteractionResultHolder<ItemStack> art(Wield w, Level l, Player p, InteractionHand hand) {
        ItemStack stack = p.getItemInHand(hand);
        if (p.getCooldowns().isOnCooldown(stack.getItem())) {
            return InteractionResultHolder.fail(stack);
        }
        if (l.isClientSide) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        // Item cooldowns block every right-click, so kinds that shoot or guard keep their art on a clock of their own.
        boolean clock = w.kind != null && w.kind.ranged();
        long now = l.getGameTime();
        CompoundTag clocks = p.getPersistentData().getCompound("ororArtClock");
        if (clock && now < clocks.getLong(w.art)) {
            long sec = (clocks.getLong(w.art) - now + 19L) / 20L;
            p.displayClientMessage(
                Component.translatable("weapon_kind.oror_supreme_bosses.cooldown")
                    .append(Component.literal(" " + sec))
                    .append(Component.translatable("weapon_kind.oror_supreme_bosses.seconds")),
                true
            );
            return InteractionResultHolder.fail(stack);
        }
        boolean cast = false;
        if (RelicArts.of(w.art) != null) {
            if (w.spec != null && l instanceof ServerLevel sl) {
                RelicEffects.show(sl, p, w.spec.color, w.spec.rank);
            }
            cast = RelicArts.cast(w.art, p);
        } else if (w.spec != null) {
            RelicPowers.cast(w.spec, p);
            cast = true;
        }
        if (cast) {
            // the art's name flashes over the hotbar; v0.17.4 also shortened every art cooldown by a quarter
            Art banner = RelicArts.of(w.art);
            if (banner != null) {
                p.displayClientMessage(
                    Component.translatable("relic_art.oror_supreme_bosses." + w.art + ".title").withStyle(w.rank >= 3 ? ChatFormatting.GOLD : ChatFormatting.AQUA), true
                );
            }
            int cd = Math.max(20, RelicArts.cooldown(w.art, w.cooldown) * 3 / 4);
            if (clock) {
                clocks.putLong(w.art, now + cd);
                p.getPersistentData().put("ororArtClock", clocks);
            } else {
                p.getCooldowns().addCooldown(stack.getItem(), cd);
            }
            if (w.spec != null && stack.isDamageableItem()) {
                stack.hurtAndBreak(1, p, LivingEntity.getSlotForHand(hand));
            }
        }
        return InteractionResultHolder.sidedSuccess(stack, false);
    }

    /** True while the art of the relic in this stack recharges. */
    public static boolean artCooling(Player p, ItemStack stack) {
        if (p.getCooldowns().isOnCooldown(stack.getItem())) {
            return true;
        }
        return stack.getItem() instanceof CharacterRelics.Wielded x
            && x.wield().art != null
            && p.level().getGameTime() < p.getPersistentData().getCompound("ororArtClock").getLong(x.wield().art);
    }

    /** Catalysts, guns and cannons: one shot per right-click, at most one per kind.gap ticks (held right-click repeats every 4). */
    private static InteractionResultHolder<ItemStack> fire(Wield w, Level l, Player p, InteractionHand hand) {
        ItemStack stack = p.getItemInHand(hand);
        long now = l.getGameTime();
        CompoundTag data = p.getPersistentData();
        if (now < data.getLong("ororShotAt")) {
            // reloading: consume the click so held right-click does not fall through to the off-hand item (food, a shield)
            return InteractionResultHolder.consume(stack);
        }
        data.putLong("ororShotAt", now + Math.max(1, w.kind.gap));
        if (!l.isClientSide) {
            RelicArts.shot(p, w);
        }
        return w.kind.mode.equals("bolt") ? InteractionResultHolder.sidedSuccess(stack, l.isClientSide) : InteractionResultHolder.consume(stack);
    }

    private static InteractionResultHolder<ItemStack> use(Wield w, Level l, Player p, InteractionHand hand) {
        if (w.art != null && (!w.kind.ranged() || p.isShiftKeyDown())) {
            return art(w, l, p, hand);
        }
        return fire(w, l, p, hand);
    }

    /** Bows: arrows need no ammunition; a rank 3 bow looses three in a fan. */
    private static void loose(Wield w, ItemStack stack, Level l, LivingEntity who, int left) {
        if (!(who instanceof Player p) || !(l instanceof ServerLevel sl)) {
            return;
        }
        float t = (72000 - left) / 20.0F;
        float power = Math.min(1.0F, (t * t + t * 2.0F) / 3.0F);
        if (power < 0.1F) {
            return;
        }
        int n = w.rank >= 3 ? 3 : 1;
        Vec3 look = p.getLookAngle();
        for (int i = 0; i < n; i++) {
            double yaw = Math.toRadians((i - (n - 1) * 0.5) * 6.0);
            double c = Math.cos(yaw);
            double s = Math.sin(yaw);
            Arrow a = new Arrow(sl, p, new ItemStack(Items.ARROW), stack);
            a.shoot(look.x * c - look.z * s, look.y, look.x * s + look.z * c, power * 3.0F, 1.0F);
            a.setBaseDamage(w.damage * w.kind.shot / 3.0);
            a.pickup = AbstractArrow.Pickup.DISALLOWED;
            // read back by WeaponSkills.arrow when it lands
            CompoundTag tag = a.getPersistentData();
            tag.putInt("ororRelicArrow", w.spec != null ? w.spec.color : 0xFFFFFF);
            tag.putFloat("ororArrowPow", power);
            tag.putInt("ororArrowRank", w.rank);
            sl.addFreshEntity(a);
        }
        sl.playSound(null, p.blockPosition(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS, 1.0F, 0.7F + power * 0.5F);
        if (power >= 1.0F) {
            RelicEffects.burst(sl, p.getEyePosition().add(look.scale(1.2)), RelicEffects.dust(w.spec != null ? w.spec.color : 0xFFFFFF, 1.4F), 16, 0.25, 0.0);
            RelicEffects.sound(sl, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 0.8F, 1.7F);
        }
        if (stack.isDamageableItem()) {
            stack.hurtAndBreak(1, p, LivingEntity.getSlotForHand(who.getUsedItemHand()));
        }
    }

    /** Passive arts run once a second while the item is in either hand; a raised relic shield also guards nearby players. */
    static void held(Wield w, ItemStack stack, Level l, Entity e) {
        if (w.art == null || l.isClientSide || !(e instanceof Player p) || p.tickCount % 20 != 0) {
            return;
        }
        if (p.getMainHandItem() != stack && p.getOffhandItem() != stack) {
            return;
        }
        if (w.kind != null && w.kind.mode.equals("guard") && p.isBlocking() && p.getUseItem() == stack && l instanceof ServerLevel sl) {
            WeaponSkills.sanctuary(p, w, sl);
        }
        if (RelicArts.of(w.art) != null) {
            RelicArts.passive(w.art, p);
        } else if (w.spec != null && (w.spec.rank == 3 || w.spec.slot.equals("charm"))) {
            RelicPowers.passive(w.spec, p);
        }
    }

    static void describe(Wield w, List<Component> lines) {
        String k = "weapon_kind.oror_supreme_bosses.";
        lines.add(Component.translatable(k + w.kind.id).withStyle(ChatFormatting.GRAY));
        lines.add(Component.translatable("weapon_skill.oror_supreme_bosses." + w.kind.id + ".desc").withStyle(ChatFormatting.YELLOW));
        if (w.art != null || w.kind.ranged()) {
            lines.add(Component.translatable(k + "how." + w.kind.mode).withStyle(ChatFormatting.WHITE));
        }
        if (w.art != null) {
            RelicArts.tooltip(w.art, lines);
        }
    }

    /** The fighting style a mob learns from seeing a player wield this item, or null for other items. */
    public static String style(ItemStack stack) {
        if (!(stack.getItem() instanceof CharacterRelics.Wielded x) || x.wield().kind == null) {
            return null;
        }
        Kind k = x.wield().kind;
        if (k.ranged()) {
            return k.mode.equals("guard") ? "sword" : "bow";
        }
        return switch (k.id) {
            case "heavy", "toyhammer" -> "mace";
            case "greatsword" -> "axe";
            case "fist" -> "unarmed";
            default -> "sword";
        };
    }

    static {
        for (RelicSpec s : RelicSpec.ALL.values()) {
            ITEMS.put(s.id, OrorReborn.ITEMS.register(s.id, () -> relic(s)));
        }
        // the swap-hands key casts the art too: Epic Fight's battle mode turns right-click into guard for its
        // sword-type weapons and cancels the item use, so right-click alone cannot be relied on
        net.neoforged.neoforge.common.NeoForge.EVENT_BUS.addListener(CharacterRelics::swapHands);
    }

    /** F (swap hands) with a relic in the main hand casts its art; sneak + F swaps hands as usual. Server side. */
    static void swapHands(net.neoforged.neoforge.event.entity.living.LivingSwapItemsEvent.Hands e) {
        if (!(e.getEntity() instanceof Player p) || p.level().isClientSide || p.isShiftKeyDown()) {
            return;
        }
        if (p.getMainHandItem().getItem() instanceof CharacterRelics.Wielded x && x.wield().art != null) {
            e.setCanceled(true);
            CharacterRelics.art(x.wield(), p.level(), p, InteractionHand.MAIN_HAND);
        }
    }

    // ------------------------------------------------------------------------------------- items
    public static final class Artifact extends Item implements CharacterRelics.Relic, CharacterRelics.Wielded {
        private final Wield w;

        Artifact(RelicSpec s) {
            super(new Properties().stacksTo(1).fireResistant().rarity(Rarity.RARE).attributes(attributes(s)));
            this.w = new Wield(s, s.id, null, 0.0F, s.rank, s.cooldown);
        }

        /** Held in either hand: a focus sharpens the wielder's attacks, a charm hardens and quickens them (v0.17.6). */
        static ItemAttributeModifiers attributes(RelicSpec s) {
            ItemAttributeModifiers.Builder b = ItemAttributeModifiers.builder();
            if (s.slot.equals("focus")) {
                b.add(Attributes.ATTACK_DAMAGE, modifier("focus_attack", 0.4, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL), EquipmentSlotGroup.ANY)
                    .add(Attributes.ATTACK_SPEED, modifier("focus_speed", 0.2, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL), EquipmentSlotGroup.ANY);
            } else {
                b.add(Attributes.MAX_HEALTH, modifier("charm_health", 20.0, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.ANY)
                    .add(Attributes.ARMOR, modifier("charm_armor", 10.0, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.ANY)
                    .add(Attributes.ARMOR_TOUGHNESS, modifier("charm_toughness", 6.0, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.ANY)
                    .add(Attributes.MOVEMENT_SPEED, modifier("charm_speed", 0.2, AttributeModifier.Operation.ADD_MULTIPLIED_BASE), EquipmentSlotGroup.ANY)
                    .add(Attributes.KNOCKBACK_RESISTANCE, modifier("charm_steady", 0.5, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.ANY);
            }
            return b.build();
        }

        private static AttributeModifier modifier(String id, double amount, AttributeModifier.Operation op) {
            return new AttributeModifier(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", id), amount, op);
        }

        @Override
        public RelicSpec spec() {
            return this.w.spec;
        }

        @Override
        public Wield wield() {
            return this.w;
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            return CharacterRelics.art(this.w, l, p, h);
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            CharacterRelics.held(this.w, stack, l, e);
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, java.util.List<Component> lines, net.minecraft.world.item.TooltipFlag flag) {
            RelicArts.tooltip(this.w.art, lines);
        }
    }

    /** Melee kinds, catalysts, guns and cannons. */
    public static final class Blade extends SwordItem implements CharacterRelics.Relic, CharacterRelics.Wielded {
        private final Wield w;

        Blade(Wield w, Properties props) {
            super(Tiers.NETHERITE, props.attributes(attributes(w.kind, w.damage)));
            this.w = w;
        }

        /** Damage and speed replace the base modifiers like SwordItem.createAttributes; reach and knockback are added on top. */
        static ItemAttributeModifiers attributes(Kind k, float damage) {
            ItemAttributeModifiers.Builder b = ItemAttributeModifiers.builder()
                .add(Attributes.ATTACK_DAMAGE, new AttributeModifier(BASE_ATTACK_DAMAGE_ID, damage * k.mul, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND)
                .add(Attributes.ATTACK_SPEED, new AttributeModifier(BASE_ATTACK_SPEED_ID, k.speed, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
            if (k.reach != 0.0F) {
                b.add(Attributes.ENTITY_INTERACTION_RANGE, new AttributeModifier(REACH_ID, k.reach, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
            }
            if (k.knock != 0.0F) {
                b.add(Attributes.ATTACK_KNOCKBACK, new AttributeModifier(KNOCK_ID, k.knock, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
            }
            return b.build();
        }

        @Override
        public RelicSpec spec() {
            return this.w.spec;
        }

        @Override
        public Wield wield() {
            return this.w;
        }

        /** Relic weapons never wear out (NeoForge IItemExtension.damageItem; same erased descriptor as its generic form). */
        @Override
        @SuppressWarnings("rawtypes")
        public int damageItem(ItemStack stack, int amount, LivingEntity entity, java.util.function.Consumer onBroken) {
            return 0;
        }

        public boolean isFoil(ItemStack s) {
            return this.w.rank == 3 || super.isFoil(s);
        }

        @Override
        public boolean canPerformAction(ItemStack stack, ItemAbility ability) {
            return (this.w.kind.sweep || ability != ItemAbilities.SWORD_SWEEP) && super.canPerformAction(stack, ability);
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            if (this.w.art == null && !this.w.kind.ranged()) {
                return super.use(l, p, h);
            }
            return CharacterRelics.use(this.w, l, p, h);
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            CharacterRelics.held(this.w, stack, l, e);
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, java.util.List<Component> lines, net.minecraft.world.item.TooltipFlag flag) {
            CharacterRelics.describe(this.w, lines);
        }
    }

    public static final class Bow extends BowItem implements CharacterRelics.Relic, CharacterRelics.Wielded {
        private final Wield w;

        Bow(Wield w, Properties props) {
            super(props.attributes(Blade.attributes(w.kind, w.damage)));
            this.w = w;
        }

        @Override
        public RelicSpec spec() {
            return this.w.spec;
        }

        @Override
        public Wield wield() {
            return this.w;
        }

        /** Relic weapons never wear out (NeoForge IItemExtension.damageItem; same erased descriptor as its generic form). */
        @Override
        @SuppressWarnings("rawtypes")
        public int damageItem(ItemStack stack, int amount, LivingEntity entity, java.util.function.Consumer onBroken) {
            return 0;
        }

        public boolean isFoil(ItemStack s) {
            return this.w.rank == 3 || super.isFoil(s);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            if (this.w.art != null && p.isShiftKeyDown()) {
                return CharacterRelics.art(this.w, l, p, h);
            }
            p.startUsingItem(h);
            return InteractionResultHolder.consume(p.getItemInHand(h));
        }

        @Override
        public void releaseUsing(ItemStack stack, Level l, LivingEntity who, int left) {
            CharacterRelics.loose(this.w, stack, l, who, left);
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            CharacterRelics.held(this.w, stack, l, e);
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, java.util.List<Component> lines, net.minecraft.world.item.TooltipFlag flag) {
            CharacterRelics.describe(this.w, lines);
        }
    }

    public static final class Shield extends ShieldItem implements CharacterRelics.Relic, CharacterRelics.Wielded {
        private final Wield w;

        Shield(Wield w, Properties props) {
            super(props.attributes(Blade.attributes(w.kind, w.damage)));
            this.w = w;
        }

        @Override
        public RelicSpec spec() {
            return this.w.spec;
        }

        @Override
        public Wield wield() {
            return this.w;
        }

        public boolean isFoil(ItemStack s) {
            return this.w.rank == 3 || super.isFoil(s);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            if (this.w.art != null && p.isShiftKeyDown()) {
                return CharacterRelics.art(this.w, l, p, h);
            }
            // the perfect-guard window (WeaponSkills.guard) opens when the shield is raised
            p.getPersistentData().putLong("ororGuardAt", l.getGameTime());
            return super.use(l, p, h);
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            CharacterRelics.held(this.w, stack, l, e);
        }

        @Override
        public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, java.util.List<Component> lines, net.minecraft.world.item.TooltipFlag flag) {
            CharacterRelics.describe(this.w, lines);
        }
    }

    /** A character relic. */
    public interface Relic {
        RelicSpec spec();
    }

    public interface Wielded {
        Wield wield();
    }
}
