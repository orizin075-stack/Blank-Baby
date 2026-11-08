package jp.oror.reborn.king;

import com.mojang.datafixers.util.Pair;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.gossip.GossipType;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.WanderingTrader;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.MapItem;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.saveddata.maps.MapDecorationTypes;
import net.minecraft.world.level.saveddata.maps.MapItemSavedData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.registries.RegisterEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (056) 反逆証明書, the certificate of rebellion (the user: to win the illagers' trust, a recipe for a certificate of
 * rebellion made by using villagers; held and shown to a wandering trader, it gets a map to where the rebels are).
 * <ul>
 * <li>村人の血判 (a villager's blood seal): paper held, crouching, used on a villager: the villager is made to cut a
 * finger and press his seal on it (half a heart). He thinks the less of one for it (his gossip), and gives it once.</li>
 * <li>反逆証明書: three blood seals, a sheet of paper, an ink sac and an emerald (shapeless).</li>
 * <li>Carried, the rebels (the illagers and witches, the piglins, the endermen) take its bearer for a friend, as they
 * take the king's enemy (RebelPact.friend). Shown to one of them, they trade with its bearer (their favour made 5).</li>
 * <li>Shown to a wandering trader: he gives a map to the nearest illager city or fortress (Azazel's court), once to
 * each bearer.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RebelCertificate {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Rebels");
    public static Item SEAL;
    public static Item CERTIFICATE;
    static final String SEALED = "OrorBloodSealTaken", MAPS = "OrorRebelMapsGiven", SHOWN = "OrorCertificateShown";
    static final String MAP_NAME = "叛逆者の都への地図";

    private RebelCertificate() {
    }

    /** The items, with their words. */
    static final class Paper extends Item {
        private final String key;

        Paper(Properties p, String key) {
            super(p);
            this.key = key;
        }

        @Override
        public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> lines, TooltipFlag flag) {
            for (int i = 1; i <= 3; i++) {
                lines.add(Component.translatable("item.oror_supreme_bosses." + this.key + ".desc" + i).withStyle(i == 3 ? ChatFormatting.DARK_RED
                    : ChatFormatting.GRAY));
            }
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    public static final class Registry {
        private Registry() {
        }

        @SubscribeEvent
        public static void register(RegisterEvent event) {
            event.register(Registries.ITEM, helper -> {
                SEAL = new Paper(new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON), "villager_blood_seal");
                helper.register(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "villager_blood_seal"), SEAL);
                CERTIFICATE = new Paper(new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).component(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true),
                    "rebel_certificate");
                helper.register(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "rebel_certificate"), CERTIFICATE);
            });
        }

        @SubscribeEvent
        public static void tab(BuildCreativeModeTabContentsEvent event) {
            if (event.getTabKey().location().equals(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "supreme_entities"))) {
                event.accept(SEAL);
                event.accept(CERTIFICATE);
            }
        }
    }

    public static boolean isCertificate(ItemStack s) {
        return CERTIFICATE != null && s.is(CERTIFICATE);
    }

    /** Whether the player carries a certificate (anywhere in the inventory). */
    public static boolean carries(Player p) {
        if (p == null || CERTIFICATE == null) {
            return false;
        }
        for (ItemStack s : p.getInventory().items) {
            if (s.is(CERTIFICATE)) {
                return true;
            }
        }
        return p.getOffhandItem().is(CERTIFICATE);
    }

    // ------------------------------------------------------------------------------------------------ in use

    @SubscribeEvent
    public static void used(PlayerInteractEvent.EntityInteract e) {
        if (e.getHand() != InteractionHand.MAIN_HAND || !(e.getEntity() instanceof ServerPlayer p) || !(p.level() instanceof ServerLevel sl)) {
            return;
        }
        ItemStack held = p.getMainHandItem();
        Entity t = e.getTarget();
        boolean done = false;
        if (t instanceof Villager v && p.isShiftKeyDown() && held.is(Items.PAPER)) {
            done = takeSeal(p, v, sl);
        } else if (t instanceof WanderingTrader w && isCertificate(held)) {
            done = showTrader(p, w, sl);
        } else if (RebelPact.member(t) && isCertificate(held)) {
            done = showRebel(p, (LivingEntity) t);
        }
        if (done) {
            e.setCanceled(true);
            e.setCancellationResult(InteractionResult.SUCCESS);
        }
    }

    /** A villager made to press his blood seal on the paper. */
    public static boolean takeSeal(ServerPlayer p, Villager v, ServerLevel sl) {
        if (SEAL == null) {
            return false;
        }
        if (v.isBaby()) {
            p.displayClientMessage(Component.literal("子供の血判では役に立たない。").withStyle(ChatFormatting.GRAY), true);
            return true;
        }
        if (v.getPersistentData().getBoolean(SEALED)) {
            p.displayClientMessage(Component.literal("この村人は、もう血判を押している。").withStyle(ChatFormatting.GRAY), true);
            return true;
        }
        ItemStack paper = p.getMainHandItem();
        if (!p.isCreative()) {
            paper.shrink(1);
        }
        v.getPersistentData().putBoolean(SEALED, true);
        v.hurt(sl.damageSources().generic(), 1.0F);
        v.getGossips().add(p.getUUID(), GossipType.MINOR_NEGATIVE, 25);
        v.setUnhappyCounter(40);
        ItemStack seal = new ItemStack(SEAL);
        if (!p.getInventory().add(seal)) {
            p.drop(seal, false);
        }
        sl.sendParticles(ParticleTypes.ANGRY_VILLAGER, v.getX(), v.getY() + v.getBbHeight() + 0.2, v.getZ(), 4, 0.3, 0.2, 0.3, 0);
        sl.sendParticles(ParticleTypes.DAMAGE_INDICATOR, v.getX(), v.getY() + 1.0, v.getZ(), 3, 0.2, 0.2, 0.2, 0);
        sl.playSound(null, v.blockPosition(), SoundEvents.VILLAGER_NO, v.getSoundSource(), 1.0F, 0.9F);
        p.displayClientMessage(Component.literal("村人の血判を手に入れた（この村人はあなたを信用しなくなった）").withStyle(ChatFormatting.DARK_RED), true);
        LOG.info("BLOOD-SEAL {}", p.getGameProfile().getName());
        return true;
    }

    /** Shown to a rebel: they trust the bearer and trade. */
    public static boolean showRebel(ServerPlayer p, LivingEntity rebel) {
        CompoundTag k = KingCourt.kept(p);
        if (RebelPact.favour(p) < 5) {
            RebelPact.addFavour(p, 5 - RebelPact.favour(p));
        }
        if (!k.getBoolean(SHOWN)) {
            k.putBoolean(SHOWN, true);
            KingCourt.keep(p, k);
            p.sendSystemMessage(Component.literal("叛逆者たち：……村人どもの血判か。王に叛く者の証、確かに見た。信じよう。").withStyle(ChatFormatting.DARK_GREEN));
            LOG.info("CERTIFICATE-SHOWN {}", p.getGameProfile().getName());
            return true;
        }
        return false;
    }

    /** Shown to a wandering trader: a map to the rebels' city, once to each bearer. */
    public static boolean showTrader(ServerPlayer p, WanderingTrader w, ServerLevel sl) {
        ListTag given = w.getPersistentData().getList(MAPS, Tag.TAG_STRING);
        String who = p.getUUID().toString();
        for (int i = 0; i < given.size(); i++) {
            if (given.getString(i).equals(who)) {
                p.sendSystemMessage(Component.literal("行商人：地図はもう渡したはずだ。……早く行け。").withStyle(ChatFormatting.GRAY));
                return true;
            }
        }
        BlockPos at = rebelsCity(sl, w.blockPosition());
        if (at == null) {
            p.sendSystemMessage(Component.literal("行商人：……悪いが、この辺りで奴らの都の噂は聞かない。").withStyle(ChatFormatting.GRAY));
            return true;
        }
        ItemStack map = MapItem.create(sl, at.getX(), at.getZ(), (byte) 2, true, true);
        MapItem.renderBiomePreviewMap(sl, map);
        MapItemSavedData.addTargetDecoration(map, at, "+", MapDecorationTypes.RED_X);
        map.set(DataComponents.CUSTOM_NAME, Component.literal(MAP_NAME).withStyle(ChatFormatting.DARK_PURPLE));
        if (!p.getInventory().add(map)) {
            p.drop(map, false);
        }
        given.add(StringTag.valueOf(who));
        w.getPersistentData().put(MAPS, given);
        sl.playSound(null, w.blockPosition(), SoundEvents.WANDERING_TRADER_YES, w.getSoundSource(), 1.0F, 0.8F);
        p.sendSystemMessage(Component.literal("行商人：……その証文、本物だな。奴らの都はここだ。王国には黙っておく。").withStyle(ChatFormatting.DARK_GREEN));
        LOG.info("REBEL-MAP {} {} {}", p.getGameProfile().getName(), at.getX(), at.getZ());
        return true;
    }

    /** The nearest illager city or fortress (Azazel's court) from a place, or null. */
    public static BlockPos rebelsCity(ServerLevel sl, BlockPos from) {
        var reg = sl.registryAccess().registryOrThrow(Registries.STRUCTURE);
        List<Holder<Structure>> holders = new ArrayList<>();
        for (ResourceLocation id : new ResourceLocation[]{RebelLord.CITY, RebelLord.FORTRESS}) {
            reg.getHolder(ResourceKey.create(Registries.STRUCTURE, id)).ifPresent(holders::add);
        }
        if (holders.isEmpty()) {
            return null;
        }
        Pair<BlockPos, Holder<Structure>> found = sl.getChunkSource().getGenerator().findNearestMapStructure(sl, HolderSet.direct(holders), from, 100,
            false);
        return found == null ? null : found.getFirst();
    }
}
