package jp.oror.reborn.relic;

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
 * (058) The relic techniques' traffic. The one thing a player sends is which of the three keys was pressed; the server
 * decides everything (whether the weapon is held, the cooldown, the moment of release, every hit) and tells the
 * watchers only what to show: a technique readied or ended (Show), a 3D shape at a place (Cue), a unit or field set
 * down, moved or gone (Thing), and its owner when each technique is ready again (Ready).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class RelicNet {
    private RelicNet() {
    }

    private static ResourceLocation rl(String path) {
        return ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", path);
    }

    /** The player pressed technique key 0, 1 or 2 (特殊技Ⅰ, 特殊技Ⅱ, 必殺技). */
    public record Key(int slot) implements CustomPacketPayload {
        public static final Type<Key> TYPE = new Type<>(rl("relic_key"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Key> CODEC = StreamCodec.ofMember(Key::write, Key::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeByte(this.slot);
        }

        private static Key read(RegistryFriendlyByteBuf b) {
            return new Key(b.readByte());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** A technique readied by a player (start and release in game time), or ended (index -1, reason 0 done, 1 cut off). */
    public record Show(int entity, int index, long start, long release, int reason) implements CustomPacketPayload {
        public static final Type<Show> TYPE = new Type<>(rl("relic_show"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Show> CODEC = StreamCodec.ofMember(Show::write, Show::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeVarInt(this.entity);
            b.writeVarInt(this.index + 1);
            b.writeVarLong(this.start);
            b.writeVarLong(this.release);
            b.writeByte(this.reason);
        }

        private static Show read(RegistryFriendlyByteBuf b) {
            return new Show(b.readVarInt(), b.readVarInt() - 1, b.readVarLong(), b.readVarLong(), b.readByte());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** A shape to draw: its kind, colour, place and direction, size, life, a second measure (a tilt, a height) and a word. */
    public record Cue(int kind, int colour, double x, double y, double z, float dx, float dy, float dz, float size, int life, float a, float h,
                      int owner, String text) implements CustomPacketPayload {
        public static final Type<Cue> TYPE = new Type<>(rl("relic_cue"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Cue> CODEC = StreamCodec.ofMember(Cue::write, Cue::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeByte(this.kind);
            b.writeInt(this.colour);
            b.writeDouble(this.x);
            b.writeDouble(this.y);
            b.writeDouble(this.z);
            b.writeFloat(this.dx);
            b.writeFloat(this.dy);
            b.writeFloat(this.dz);
            b.writeFloat(this.size);
            b.writeVarInt(this.life);
            b.writeFloat(this.a);
            b.writeFloat(this.h);
            b.writeVarInt(this.owner + 1);
            b.writeUtf(this.text, 64);
        }

        private static Cue read(RegistryFriendlyByteBuf b) {
            return new Cue(b.readByte(), b.readInt(), b.readDouble(), b.readDouble(), b.readDouble(), b.readFloat(), b.readFloat(), b.readFloat(),
                b.readFloat(), b.readVarInt(), b.readFloat(), b.readFloat(), b.readVarInt() - 1, b.readUtf(64));
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** A unit or a field a technique set down (op 0), where it is or how hurt (op 1), or gone (op 2). */
    public record Thing(int op, int id, String kind, int colour, double x, double y, double z, float radius, int life, int owner, float hp)
        implements CustomPacketPayload {
        public static final Type<Thing> TYPE = new Type<>(rl("relic_thing"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Thing> CODEC = StreamCodec.ofMember(Thing::write, Thing::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeByte(this.op);
            b.writeVarInt(this.id);
            b.writeUtf(this.kind, 32);
            b.writeInt(this.colour);
            b.writeDouble(this.x);
            b.writeDouble(this.y);
            b.writeDouble(this.z);
            b.writeFloat(this.radius);
            b.writeVarInt(Math.max(0, this.life));
            b.writeVarInt(this.owner + 1);
            b.writeFloat(this.hp);
        }

        private static Thing read(RegistryFriendlyByteBuf b) {
            return new Thing(b.readByte(), b.readVarInt(), b.readUtf(32), b.readInt(), b.readDouble(), b.readDouble(), b.readDouble(), b.readFloat(),
                b.readVarInt(), b.readVarInt() - 1, b.readFloat());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** When the owner's technique (by index) is ready again, in game time. */
    public record Ready(int index, long at) implements CustomPacketPayload {
        public static final Type<Ready> TYPE = new Type<>(rl("relic_ready"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Ready> CODEC = StreamCodec.ofMember(Ready::write, Ready::read);

        private void write(RegistryFriendlyByteBuf b) {
            b.writeVarInt(this.index);
            b.writeVarLong(this.at);
        }

        private static Ready read(RegistryFriendlyByteBuf b) {
            return new Ready(b.readVarInt(), b.readVarLong());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent e) {
        var r = e.registrar("1").optional();
        r.playToServer(Key.TYPE, Key.CODEC, (p, ctx) -> ctx.enqueueWork(() -> {
            if (ctx.player() instanceof ServerPlayer sp) {
                RelicTech.press(sp, p.slot());
            }
        }));
        r.playToClient(Show.TYPE, Show.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client(p)));
        r.playToClient(Cue.TYPE, Cue.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client(p)));
        r.playToClient(Thing.TYPE, Thing.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client(p)));
        r.playToClient(Ready.TYPE, Ready.CODEC, (p, ctx) -> ctx.enqueueWork(() -> client(p)));
    }

    private static void client(Object p) {
        if (FMLEnvironment.dist.isClient()) {
            jp.oror.reborn.relic.client.RelicClient.receive(p);
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
