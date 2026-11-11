package jp.oror.reborn.waza;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.loading.FMLEnvironment;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/**
 * (057) What the server tells the players who can see a technique, and the one thing a player tells the server (a
 * contract accepted or refused). The server owns the technique's id, its start, its target, its random seed and every
 * change of state; the client only plays the pose, the sound and the particles (the design's 実装順序と安全性).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class WazaNet {
    private WazaNet() {
    }

    private static ResourceLocation rl(String path) {
        return ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path);
    }

    /** A technique begins (phase TELEGRAPH at start), or ends: index -1 with reason (0 done, 1 cancelled, 2 death, 3 gone). */
    public record Show(int entity, int index, long seed, long start, int target, int reason) implements CustomPacketPayload {
        public static final Type<Show> TYPE = new Type<>(rl("waza_show"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Show> CODEC = StreamCodec.ofMember(Show::write, Show::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeVarInt(this.entity);
            b.writeVarInt(this.index + 1);
            b.writeLong(this.seed);
            b.writeVarLong(this.start);
            b.writeVarInt(this.target + 1);
            b.writeByte(this.reason);
        }

        private static Show read(RegistryFriendlyByteBuf b) {
            return new Show(b.readVarInt(), b.readVarInt() - 1, b.readLong(), b.readVarLong(), b.readVarInt() - 1, b.readByte());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /**
     * A thing a technique put into the world (a shot, a beam, a field, a ring of sound, a growth, a device, a guard, a
     * curse's mark, a summoning circle), made (op 0), changed (op 1: its stage or where it is) or gone (op 2).
     */
    public record Obj(int op, int id, int kind, int owner, int index, double x, double y, double z, float dx, float dy, float dz, float radius,
                      int life, int stage, long born) implements CustomPacketPayload {
        public static final Type<Obj> TYPE = new Type<>(rl("waza_obj"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Obj> CODEC = StreamCodec.ofMember(Obj::write, Obj::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeByte(this.op);
            b.writeVarInt(this.id);
            b.writeByte(this.kind);
            b.writeVarInt(this.owner);
            b.writeVarInt(this.index + 1);
            b.writeDouble(this.x);
            b.writeDouble(this.y);
            b.writeDouble(this.z);
            b.writeFloat(this.dx);
            b.writeFloat(this.dy);
            b.writeFloat(this.dz);
            b.writeFloat(this.radius);
            b.writeVarInt(Math.max(0, this.life));
            b.writeByte(this.stage);
            b.writeVarLong(this.born);
        }

        private static Obj read(RegistryFriendlyByteBuf b) {
            return new Obj(b.readByte(), b.readVarInt(), b.readByte(), b.readVarInt(), b.readVarInt() - 1, b.readDouble(), b.readDouble(), b.readDouble(),
                b.readFloat(), b.readFloat(), b.readFloat(), b.readFloat(), b.readVarInt(), b.readByte(), b.readVarLong());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** A moment: a hit landed, a guard cracked or broke, a rewind, a countermeasure learned, a contract sealed. */
    public record Fx(int kind, int index, int entity, double x, double y, double z, float a) implements CustomPacketPayload {
        public static final Type<Fx> TYPE = new Type<>(rl("waza_fx"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Fx> CODEC = StreamCodec.ofMember(Fx::write, Fx::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeByte(this.kind);
            b.writeVarInt(this.index + 1);
            b.writeVarInt(this.entity + 1);
            b.writeDouble(this.x);
            b.writeDouble(this.y);
            b.writeDouble(this.z);
            b.writeFloat(this.a);
        }

        private static Fx read(RegistryFriendlyByteBuf b) {
            return new Fx(b.readByte(), b.readVarInt() - 1, b.readVarInt() - 1, b.readDouble(), b.readDouble(), b.readDouble(), b.readFloat());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** (059) A blow the villager king's AT field met: from which way, and how hard against the field's whole
     * (ATFieldHits sends it, ATFieldRenderer draws where it struck). */
    public record AtHit(int entity, float dx, float dy, float dz, float strength) implements CustomPacketPayload {
        public static final Type<AtHit> TYPE = new Type<>(rl("at_field_hit"));
        public static final StreamCodec<RegistryFriendlyByteBuf, AtHit> CODEC = StreamCodec.ofMember(AtHit::write, AtHit::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeVarInt(this.entity);
            b.writeFloat(this.dx);
            b.writeFloat(this.dy);
            b.writeFloat(this.dz);
            b.writeFloat(this.strength);
        }

        private static AtHit read(RegistryFriendlyByteBuf b) {
            return new AtHit(b.readVarInt(), b.readFloat(), b.readFloat(), b.readFloat(), b.readFloat());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** A contract offered to this player: its terms, shown on screen, and nothing paid until the player agrees. */
    public record Offer(int contract, int index, int owner, String benefit, String cost, int seconds) implements CustomPacketPayload {
        public static final Type<Offer> TYPE = new Type<>(rl("waza_offer"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Offer> CODEC = StreamCodec.ofMember(Offer::write, Offer::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeVarInt(this.contract);
            b.writeVarInt(this.index);
            b.writeVarInt(this.owner);
            b.writeUtf(this.benefit, 256);
            b.writeUtf(this.cost, 256);
            b.writeVarInt(this.seconds);
        }

        private static Offer read(RegistryFriendlyByteBuf b) {
            return new Offer(b.readVarInt(), b.readVarInt(), b.readVarInt(), b.readUtf(256), b.readUtf(256), b.readVarInt());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** The player's answer to a contract (from the contract screen). */
    public record Answer(int contract, boolean accept) implements CustomPacketPayload {
        public static final Type<Answer> TYPE = new Type<>(rl("waza_answer"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Answer> CODEC = StreamCodec.ofMember(Answer::write, Answer::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeVarInt(this.contract);
            b.writeBoolean(this.accept);
        }

        private static Answer read(RegistryFriendlyByteBuf b) {
            return new Answer(b.readVarInt(), b.readBoolean());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent e) {
        var r = e.registrar("1").optional();
        r.playToClient(Show.TYPE, Show.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client("show", p)));
        r.playToClient(Obj.TYPE, Obj.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client("obj", p)));
        r.playToClient(Fx.TYPE, Fx.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client("fx", p)));
        r.playToClient(Offer.TYPE, Offer.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client("offer", p)));
        r.playToClient(AtHit.TYPE, AtHit.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client("athit", p)));
        r.playToServer(Answer.TYPE, Answer.CODEC, (p, ctx) -> ctx.enqueueWork(() -> {
            if (ctx.player() instanceof ServerPlayer sp) {
                WazaWorld.answer(sp, p.contract(), p.accept());
            }
        }));
    }

    /** Hands a payload to the client's side (only ever run on a client; the class is not touched on a server). */
    private static void client(String what, Object p) {
        if (FMLEnvironment.dist.isClient()) {
            jp.oror.reborn.waza.client.WazaClient.receive(what, p);
        }
    }

    static void toWatchers(Entity e, CustomPacketPayload p) {
        if (e != null && !e.level().isClientSide) {
            PacketDistributor.sendToPlayersTrackingEntityAndSelf(e, p);
        }
    }

    static void toPlayer(ServerPlayer sp, CustomPacketPayload p) {
        PacketDistributor.sendToPlayer(sp, p);
    }
}
