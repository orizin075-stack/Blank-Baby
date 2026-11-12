package jp.oror.reborn.duel;

import java.lang.reflect.Method;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLEnvironment;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059e) The user's Duel Dominion grimoire (支配の魔導書) opened as a book (the user: "本は実際に開いてみれるように 専用の
 * モーション付きで"). Right-click opens it (DuelGrimoireMixin): the reader raises it in both hands and reads (the item is in
 * use while the book is open, so everyone sees the pose and the open book in his hands, GrimoireClient), and the book
 * lies open on the screen (GrimoireScreen): its cover swings open, its pages turn, each page shows four of the sealed
 * mobs (their likeness, name and state), and from the page the reader chooses one and calls it out or back. Storing a
 * bound hair (one in the other hand) is as before. The book's choices reach the server here ({@link Act}): the server
 * does what Duel Dominion's own right-click did (its Selected, its SealSummoning.toggle), on the book in that hand.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class GrimoireBook {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Duel");
    public static final ResourceLocation GRIMOIRE = ResourceLocation.fromNamespaceAndPath("dueldominion", "dominion_grimoire");
    public static final ResourceLocation HAIR = ResourceLocation.fromNamespaceAndPath("dueldominion", "bound_hair");
    public static final int SELECT = 0, TOGGLE = 1;
    private static Method toggle;
    private static boolean broken;

    private GrimoireBook() {
    }

    public static boolean isGrimoire(ItemStack s) {
        return !s.isEmpty() && GRIMOIRE.equals(BuiltInRegistries.ITEM.getKey(s.getItem()));
    }

    public static boolean isHair(ItemStack s) {
        return !s.isEmpty() && HAIR.equals(BuiltInRegistries.ITEM.getKey(s.getItem()));
    }

    /** The book's own data (Duel Dominion keeps it in the item's custom data). */
    public static CompoundTag data(ItemStack book) {
        CustomData c = book.get(DataComponents.CUSTOM_DATA);
        return c == null ? new CompoundTag() : c.copyTag();
    }

    /** On the client: the book opens on the screen. */
    public static void openClient(InteractionHand hand) {
        if (FMLEnvironment.dist.isClient()) {
            jp.oror.reborn.duel.client.GrimoireScreen.open(hand);
        }
    }

    /** What the reader chose on a page: which entry, and to choose it or to call it out (or back). */
    public record Act(boolean offhand, int index, int action) implements CustomPacketPayload {
        public static final Type<Act> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "grimoire_act"));
        public static final StreamCodec<FriendlyByteBuf, Act> CODEC = StreamCodec.of(
            (buf, p) -> {
                buf.writeBoolean(p.offhand);
                buf.writeVarInt(p.index);
                buf.writeVarInt(p.action);
            },
            buf -> new Act(buf.readBoolean(), buf.readVarInt(), buf.readVarInt()));

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent e) {
        e.registrar("1").optional().playToServer(Act.TYPE, Act.CODEC, (p, ctx) -> ctx.enqueueWork(() -> {
            if (ctx.player() instanceof ServerPlayer sp) {
                act(sp, p);
            }
        }));
    }

    static void act(ServerPlayer sp, Act p) {
        InteractionHand hand = p.offhand() ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
        ItemStack book = sp.getItemInHand(hand);
        if (!isGrimoire(book)) {
            return;
        }
        CompoundTag data = data(book);
        ListTag entries = data.getList("Entries", 10);
        if (p.index() < 0 || p.index() >= entries.size()) {
            return;
        }
        data.putInt("Selected", p.index());
        if (p.action() == TOGGLE) {
            CompoundTag chosen = entries.getCompound(p.index()).copy();
            boolean done = toggle(sp, chosen);
            entries.set(p.index(), chosen);
            data.put("Entries", entries);
            if (!done) {
                sp.sendSystemMessage(Component.literal("召喚・回収できませんでした。"));
            } else {
                sp.level().playSound(null, sp.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS, 0.6F, 1.4F);
            }
        }
        book.set(DataComponents.CUSTOM_DATA, CustomData.of(data));
    }

    /** Duel Dominion's own call out / call back (SealSummoning.toggle), on the chosen entry. */
    private static boolean toggle(ServerPlayer sp, CompoundTag entry) {
        if (broken) {
            return false;
        }
        try {
            if (toggle == null) {
                toggle = Class.forName("jp.oror.dueldominion.SealSummoning").getMethod("toggle", ServerPlayer.class, CompoundTag.class);
            }
            return (Boolean) toggle.invoke(null, sp, entry);
        } catch (ReflectiveOperationException | RuntimeException | LinkageError ex) {
            broken = true;
            LOG.warn("GRIMOIRE cannot call Duel Dominion's SealSummoning.toggle: {}", ex.toString());
            return false;
        }
    }
}
