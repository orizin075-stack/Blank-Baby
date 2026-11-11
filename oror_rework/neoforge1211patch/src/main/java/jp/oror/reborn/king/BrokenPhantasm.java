package jp.oror.reborn.king;

import java.util.List;
import jp.oror.reborn.royal.RoyalGuns;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.DiggerItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ProjectileWeaponItem;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ShearsItem;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingEntityUseItemEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import org.joml.Vector3f;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The rebels' hidden grand magic, 「壊れた幻想」 (Broken Phantasm). Cast (used), for thirty seconds every thing
 * its caster uses breaks with that one use, and gives in its breaking a power like a bug's (the user: normal 10-20
 * times, rare 25-50, epic 75-100, legendary 1000 and more, mythic arms ?????????).
 * <ul>
 * <li>Its tiers: normal (an item of common rarity), rare (uncommon, rare), epic (epic), legendary (OROR's own epic arms
 * and the legendary guns the king sells), mythic (the relics of OROR's beings: their weapons, foci, charms and
 * legends): 10-20, 25-50, 75-100, 1000-9999, and beyond counting.</li>
 * <li>A weapon's blow is multiplied and the weapon shatters; a bow's, a crossbow's or a gun's shot is (the weapon
 * shatters as it fires); a tool tears out a sphere of the world round the block it breaks (its radius by the tier) and
 * shatters; food and potions are drunk to a bug's strength (their effects many times as strong and long, the whole
 * stack gone); anything else used shatters into a surge of strength, speed, haste and healing.</li>
 * </ul>
 * The magic is a scroll of amethyst the rebels keep hidden: at 60 favour their shops sell it, and Azazel's body
 * yields it one time in four.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class BrokenPhantasm {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Rebels");
    static final String TAG = "OrorBrokenPhantasm", UNTIL = "OrorPhantasmUntil", SHOT = "OrorPhantasmMult";
    public static final int SECONDS = 30;
    private static final DustParticleOptions MAGENTA = new DustParticleOptions(new Vector3f(1.0F, 0.0F, 1.0F), 1.2F);
    private static final DustParticleOptions CYAN = new DustParticleOptions(new Vector3f(0.0F, 1.0F, 1.0F), 1.2F);

    private BrokenPhantasm() {
    }

    /** The scroll. */
    public static ItemStack scroll() {
        ItemStack s = new ItemStack(Items.AMETHYST_SHARD);
        s.set(DataComponents.CUSTOM_NAME, Component.literal("大魔法『壊れた幻想』").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD));
        s.set(DataComponents.LORE, new ItemLore(List.of(
            Component.literal("叛逆者たちが秘匿する大魔法。").withStyle(ChatFormatting.GRAY),
            Component.literal("唱えてから30秒、使ったものはすべて一度で砕け散り、").withStyle(ChatFormatting.GRAY),
            Component.literal("砕けるとき、壊れた力（バグのような強化）を放つ。").withStyle(ChatFormatting.GRAY),
            Component.literal("ノーマル 10～20倍／レア 25～50倍／エピック 75～100倍").withStyle(ChatFormatting.DARK_PURPLE),
            Component.literal("レジェンダリー 1000倍～／神話級武具 ？？？？？？？？？").withStyle(ChatFormatting.DARK_PURPLE))));
        s.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        s.set(DataComponents.RARITY, Rarity.EPIC);
        CompoundTag t = new CompoundTag();
        t.putBoolean(TAG, true);
        s.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
        return s;
    }

    public static boolean isScroll(ItemStack s) {
        CustomData d = s.get(DataComponents.CUSTOM_DATA);
        return d != null && d.copyTag().getBoolean(TAG);
    }

    public static boolean active(Player p) {
        return p.getPersistentData().getLong(UNTIL) > p.level().getGameTime();
    }

    // ------------------------------------------------------------------------------------------ the tiers

    /** 0 normal, 1 rare, 2 epic, 3 legendary, 4 mythic. */
    public static int tier(ItemStack s) {
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(s.getItem());
        if (id.getNamespace().equals("oror_supreme_bosses")) {
            String p = id.getPath();
            if (p.endsWith("_weapon") || p.endsWith("_legend") || p.endsWith("_focus") || p.endsWith("_charm")) {
                return 4;
            }
            if (s.getRarity() == Rarity.EPIC) {
                return 3;
            }
        }
        try {
            if (RoyalGuns.legendary().contains(s.getItem())) {
                return 3;
            }
        } catch (RuntimeException ex) {
            // the gun mods' items not there
        }
        return switch (s.getRarity()) {
            case EPIC -> 2;
            case RARE, UNCOMMON -> 1;
            default -> 0;
        };
    }

    static final String[] TIER_NAME = {"ノーマル", "レア", "エピック", "レジェンダリー", "神話級武具"};

    /** The multiplier for a tier (mythic: beyond counting, shown as ?????????). */
    public static double multiplier(int tier, net.minecraft.util.RandomSource r) {
        return switch (tier) {
            case 0 -> 10 + r.nextInt(11);
            case 1 -> 25 + r.nextInt(26);
            case 2 -> 75 + r.nextInt(26);
            case 3 -> 1000 + r.nextInt(9000);
            default -> 1.0E9;
        };
    }

    static String shown(int tier, double mult) {
        return tier >= 4 ? "×？？？？？？？？？" : "×" + (long) mult;
    }

    /** The thing breaks, telling what it gave. */
    static void shatter(ServerPlayer p, ItemStack s, int tier, double mult, String what) {
        Component name = s.getHoverName();
        s.setCount(0);
        ServerLevel sl = (ServerLevel) p.level();
        sl.playSound(null, p.blockPosition(), SoundEvents.ITEM_BREAK, SoundSource.PLAYERS, 1.2F, 0.5F);
        sl.playSound(null, p.blockPosition(), SoundEvents.NOTE_BLOCK_BIT.value(), SoundSource.PLAYERS, 1.2F, 0.5F + p.getRandom().nextFloat());
        sl.sendParticles(MAGENTA, p.getX(), p.getY() + 1.2, p.getZ(), 30, 0.5, 0.5, 0.5, 0.05);
        sl.sendParticles(CYAN, p.getX(), p.getY() + 1.2, p.getZ(), 30, 0.5, 0.5, 0.5, 0.05);
        p.displayClientMessage(Component.literal("§k||§r 壊れた幻想：").withStyle(ChatFormatting.LIGHT_PURPLE)
            .append(name.copy().withStyle(ChatFormatting.WHITE)).append(Component.literal(" は砕け散った（" + TIER_NAME[tier] + "）" + what + " "
                + shown(tier, mult) + " §k||").withStyle(ChatFormatting.LIGHT_PURPLE)), true);
        LOG.info("BROKEN-PHANTASM {\"player\":\"{}\",\"item\":\"{}\",\"tier\":{},\"mult\":{},\"use\":\"{}\"}", p.getGameProfile().getName(),
            BuiltInRegistries.ITEM.getKey(s.getItem()), tier, mult, what);
    }

    // ------------------------------------------------------------------------------------------ the casting

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void used(PlayerInteractEvent.RightClickItem e) {
        if (!(e.getEntity() instanceof ServerPlayer p) || !(p.level() instanceof ServerLevel sl)) {
            return;
        }
        ItemStack s = e.getItemStack();
        if (isScroll(s)) {
            e.setCanceled(true);
            e.setCancellationResult(InteractionResult.SUCCESS);
            s.shrink(1);
            cast(p, sl);
            return;
        }
        if (!active(p) || s.isEmpty()) {
            return;
        }
        // things that are drawn, eaten, drunk, blocked with or swung are handled where they act
        UseAnim anim = s.getUseAnimation();
        Item it = s.getItem();
        if (anim != UseAnim.NONE || it instanceof ProjectileWeaponItem || it instanceof DiggerItem || it instanceof ShearsItem
            || it.getClass().getName().contains("Gun") || s.has(DataComponents.FOOD)) {
            return;
        }
        int tier = tier(s);
        double mult = multiplier(tier, p.getRandom());
        surge(p, tier, mult);
        shatter(p, s, tier, mult, "力の奔流");
        e.setCanceled(true);
        e.setCancellationResult(InteractionResult.SUCCESS);
    }

    public static void cast(ServerPlayer p, ServerLevel sl) {
        p.getPersistentData().putLong(UNTIL, sl.getGameTime() + SECONDS * 20L);
        p.connection.send(new ClientboundSetTitlesAnimationPacket(5, 40, 15));
        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("30秒間、使ったものは砕け、壊れた力を放つ").withStyle(ChatFormatting.LIGHT_PURPLE)));
        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal("壊れた幻想").withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD)));
        sl.playSound(null, p.blockPosition(), SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.PLAYERS, 1F, 1.6F);
        sl.playSound(null, p.blockPosition(), SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 1F, 0.5F);
        sl.sendParticles(MAGENTA, p.getX(), p.getY() + 1, p.getZ(), 120, 1.2, 1.2, 1.2, 0.1);
        sl.sendParticles(CYAN, p.getX(), p.getY() + 1, p.getZ(), 120, 1.2, 1.2, 1.2, 0.1);
        LOG.info("BROKEN-PHANTASM-CAST {}", p.getGameProfile().getName());
    }

    // ------------------------------------------------------------------------------------------ blows

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void blow(LivingIncomingDamageEvent e) {
        Entity direct = e.getSource().getDirectEntity();
        if (direct instanceof Projectile pr && pr.getPersistentData().contains(SHOT)) {
            double mult = pr.getPersistentData().getDouble(SHOT);
            e.setAmount(scaled(e.getAmount(), mult, e.getEntity()));
            return;
        }
        if (!(e.getSource().getEntity() instanceof ServerPlayer p) || direct != p || !active(p)) {
            return;
        }
        ItemStack s = p.getMainHandItem();
        if (s.isEmpty()) {
            return;
        }
        int tier = tier(s);
        double mult = multiplier(tier, p.getRandom());
        e.setAmount(scaled(e.getAmount(), mult, e.getEntity()));
        ServerLevel sl = (ServerLevel) p.level();
        sl.sendParticles(ParticleTypes.EXPLOSION, e.getEntity().getX(), e.getEntity().getY() + 1, e.getEntity().getZ(), 1, 0, 0, 0, 0);
        shatter(p, s, tier, mult, "一撃");
    }

    /** A blow multiplied, kept finite (the gods refuse an infinite one): the mythic one strikes for a hundred times
     * its mark's life at the least. */
    static float scaled(float amount, double mult, LivingEntity target) {
        double v = Math.max(amount, 1.0) * mult;
        if (mult >= 1.0E9) {
            v = Math.max(v, target.getMaxHealth() * 100.0);
        }
        return (float) Math.min(v, 1.0E20);
    }

    @SubscribeEvent
    public static void shot(EntityJoinLevelEvent e) {
        if (e.getLevel().isClientSide() || !(e.getEntity() instanceof Projectile pr) || !(pr.getOwner() instanceof ServerPlayer p)
            || !active(p) || pr.getPersistentData().contains(SHOT)) {
            return;
        }
        ItemStack s = p.getMainHandItem();
        if (!(s.getItem() instanceof ProjectileWeaponItem) && !s.getItem().getClass().getName().contains("Gun") && !s.is(Items.TRIDENT)) {
            s = p.getOffhandItem();
            if (!(s.getItem() instanceof ProjectileWeaponItem) && !s.getItem().getClass().getName().contains("Gun")) {
                s = ItemStack.EMPTY;
            }
        }
        int tier = s.isEmpty() ? 0 : tier(s);
        double mult = multiplier(tier, p.getRandom());
        pr.getPersistentData().putDouble(SHOT, mult);
        if (!s.isEmpty()) {
            shatter(p, s, tier, mult, "射撃");
        }
    }

    // ------------------------------------------------------------------------------------------ tools

    @SubscribeEvent
    public static void dug(BlockEvent.BreakEvent e) {
        if (!(e.getPlayer() instanceof ServerPlayer p) || !active(p) || !(e.getLevel() instanceof ServerLevel sl)) {
            return;
        }
        ItemStack s = p.getMainHandItem();
        if (!(s.getItem() instanceof DiggerItem) && !(s.getItem() instanceof ShearsItem)) {
            return;
        }
        int tier = tier(s);
        double mult = multiplier(tier, p.getRandom());
        int r = (int) Math.min(10, Math.max(2, Math.round(Math.cbrt(mult))));
        BlockPos c = e.getPos();
        int broke = 0;
        // (058) never the capital's or a village's blocks: the burst took whole houses with it (the user's broken buildings)
        jp.oror.reborn.VillageLedger.Village village = jp.oror.reborn.VillageLedger.get(sl).nearest(c);
        for (BlockPos q : BlockPos.betweenClosed(c.offset(-r, -r, -r), c.offset(r, r, r))) {
            if (q.distSqr(c) > r * r || q.equals(c)) {
                continue;
            }
            if (jp.oror.reborn.village.BuildingGuard.inCapital(q, 64) || village != null && village.contains(q)) {
                continue;
            }
            BlockState st = sl.getBlockState(q);
            if (st.isAir() || st.getDestroySpeed(sl, q) < 0 || sl.getBlockEntity(q) != null) {
                continue;
            }
            sl.destroyBlock(q, true, p);
            if (++broke >= 4500) {
                break;
            }
        }
        shatter(p, s, tier, mult, "採掘（半径" + r + "・" + broke + "ブロック）");
    }

    // ------------------------------------------------------------------------------------------ food and drink

    @SubscribeEvent
    public static void eaten(LivingEntityUseItemEvent.Finish e) {
        if (!(e.getEntity() instanceof ServerPlayer p) || !active(p)) {
            return;
        }
        ItemStack s = e.getItem();
        int tier = tier(s);
        double mult = multiplier(tier, p.getRandom());
        int boost = (int) Math.min(9, Math.floor(Math.log10(mult) * 2));
        int ticks = (int) Math.min(20 * 60 * 20, 20 * 30 * Math.min(40, Math.log10(mult) * 4));
        PotionContents pc = s.get(DataComponents.POTION_CONTENTS);
        if (pc != null) {
            for (MobEffectInstance m : pc.getAllEffects()) {
                p.addEffect(new MobEffectInstance(m.getEffect(), Math.max(ticks, m.getDuration()), safe(m.getEffect(), m.getAmplifier() + boost)));
            }
        }
        if (s.has(DataComponents.FOOD)) {
            p.getFoodData().eat(20, 20F);
            p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, ticks, Math.min(24, boost * 3)));
            p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, ticks, Math.min(5, boost)));
            p.addEffect(new MobEffectInstance(MobEffects.SATURATION, 100, 0));
        }
        ItemStack rest = e.getResultStack();
        String what = pc != null ? "飲用" : "食事";
        shatter(p, rest.isEmpty() ? s.copy() : rest, tier, mult, what);
        e.setResultStack(ItemStack.EMPTY);
    }

    /** Resistance above III would make one untouchable: it is held at III. */
    static int safe(Holder<MobEffect> effect, int amp) {
        return effect.is(MobEffects.DAMAGE_RESISTANCE.unwrapKey().orElseThrow()) ? Math.min(3, amp) : Math.min(amp, 30);
    }

    /** Anything else used: a surge of strength, speed, haste, healing and the like, by the tier. */
    static void surge(ServerPlayer p, int tier, double mult) {
        int amp = (int) Math.min(9, Math.floor(Math.log10(mult) * 2));
        int ticks = 20 * 30 * (1 + tier);
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, ticks, amp));
        p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, ticks, Math.min(5, amp)));
        p.addEffect(new MobEffectInstance(MobEffects.DIG_SPEED, ticks, amp));
        p.addEffect(new MobEffectInstance(MobEffects.JUMP, ticks, Math.min(4, amp / 2)));
        p.addEffect(new MobEffectInstance(MobEffects.REGENERATION, ticks, Math.min(5, amp)));
        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, ticks, Math.min(3, amp / 2)));
        if (tier >= 4) {
            p.setHealth(p.getMaxHealth());
            p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, ticks, 49));
        }
    }

    /** The unused slot of an item (the CI): the scroll's tier table as it stands. */
    public static String table() {
        return "normal 10-20, rare 25-50, epic 75-100, legendary 1000-9999, mythic 1e9";
    }

    static EquipmentSlot hand(boolean main) {
        return main ? EquipmentSlot.MAINHAND : EquipmentSlot.OFFHAND;
    }
}
