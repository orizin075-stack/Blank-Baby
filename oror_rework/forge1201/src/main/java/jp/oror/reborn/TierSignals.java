package jp.oror.reborn;

import jp.oror.reborn.client.LevelAuras;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload.Type;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber.Bus;
import net.minecraftforge.event.entity.player.PlayerEvent.StartTracking;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.event.RegisterPayloadHandlersEvent;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    bus = Bus.MOD
)
public final class TierSignals {
    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent e) {
        e.registrar("1")
            .optional()
            .playToClient(TierSignals.Rank.TYPE, TierSignals.Rank.CODEC, (payload, context) -> context.enqueueWork(() -> LevelAuras.accept(payload)));
    }

    public static int color(Mob m) {
        return m instanceof SupremeEntity b
            ? b.spec.accent
            : (
                m instanceof CitadelGuard g
                    ? CharacterSpec.ALL.get(g.theme()).accent
                    : (
                        m instanceof Villager v
                            ? VillagerRoles.color(v)
                            : new int[]{0, 11184810, 7716333, 9071586, 14240903, 15223875, 12189683}[MobLevels.level(m)]
                    )
            );
    }

    public static void refresh(Mob m) {
        CompoundTag n = MobMind.data(m);
        int rank = MobLevels.level(m);
        int color = color(m);
        if (n.getInt("SentRank") != rank || n.getInt("SentRankColor") != color) {
            n.putInt("SentRank", rank);
            n.putInt("SentRankColor", color);
            PacketDistributor.sendToPlayersTrackingEntity(m, new TierSignals.Rank(m.getId(), rank, color), new CustomPacketPayload[0]);
        }
    }

    public static void track(StartTracking e) {
        if (e.getTarget() instanceof Mob m && e.getEntity() instanceof ServerPlayer p) {
            PacketDistributor.sendToPlayer(p, new TierSignals.Rank(m.getId(), MobLevels.level(m), color(m)), new CustomPacketPayload[0]);
        }
    }

    private TierSignals() {
    }

    public static record Rank(int entity, int rank, int color) implements CustomPacketPayload {
        public static final Type<TierSignals.Rank> TYPE = new Type(new ResourceLocation("oror_supreme_bosses", "rank"));
        public static final StreamCodec<RegistryFriendlyByteBuf, TierSignals.Rank> CODEC = StreamCodec.composite(
            ByteBufCodecs.VAR_INT,
            TierSignals.Rank::entity,
            ByteBufCodecs.VAR_INT,
            TierSignals.Rank::rank,
            ByteBufCodecs.INT,
            TierSignals.Rank::color,
            TierSignals.Rank::new
        );

        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }
}
