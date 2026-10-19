package jp.oror.reborn;

import jp.oror.reborn.client.LevelAuras;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.minecraftforge.event.entity.player.PlayerEvent.StartTracking;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.network.simple.SimpleChannel;

public final class TierSignals {
    private static final String VERSION = "1";
    /** Forge 1.20.1: a SimpleChannel (NeoForge's payload registrar in 1.21.1); optional, so vanilla clients still join. */
    static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(
        new ResourceLocation("oror_supreme_bosses", "rank"), () -> VERSION, NetworkRegistry.acceptMissingOr(VERSION), NetworkRegistry.acceptMissingOr(VERSION)
    );

    /** Called from the mod constructor: the channel and its message are registered before the network starts. */
    public static void init() {
        CHANNEL.messageBuilder(TierSignals.Rank.class, 0, NetworkDirection.PLAY_TO_CLIENT)
            .encoder(TierSignals.Rank::write)
            .decoder(TierSignals.Rank::read)
            .consumerMainThread((payload, context) -> LevelAuras.accept(payload))
            .add();
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
            CHANNEL.send(PacketDistributor.TRACKING_ENTITY.with(() -> m), new TierSignals.Rank(m.getId(), rank, color));
        }
    }

    public static void track(StartTracking e) {
        if (e.getTarget() instanceof Mob m && e.getEntity() instanceof ServerPlayer p) {
            CHANNEL.send(PacketDistributor.PLAYER.with(() -> p), new TierSignals.Rank(m.getId(), MobLevels.level(m), color(m)));
        }
    }

    private TierSignals() {
    }

    public static record Rank(int entity, int rank, int color) {
        void write(FriendlyByteBuf buf) {
            buf.writeVarInt(this.entity);
            buf.writeVarInt(this.rank);
            buf.writeInt(this.color);
        }

        static TierSignals.Rank read(FriendlyByteBuf buf) {
            return new TierSignals.Rank(buf.readVarInt(), buf.readVarInt(), buf.readInt());
        }
    }
}
