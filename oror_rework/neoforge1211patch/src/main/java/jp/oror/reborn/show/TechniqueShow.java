package jp.oror.reborn.show;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import jp.oror.reborn.Abilities;
import jp.oror.reborn.CharacterArsenal;
import jp.oror.reborn.RebornConfig;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/**
 * (052) Which technique a character is about to use, told to the players who can see it, so that each of the techniques
 * has its own motion and its own magic (TechniquePoses, TechniqueEffects) instead of the sixteen shared motions and the
 * same few sparks. The server watches each character's motion: when a new one begins with a windup (the character's
 * ability is ready and it starts to cast), the technique is the one its cast sequence points at (the base ability, or
 * one of its three arsenal techniques), and its windup, the moment the technique goes off, and its target are sent.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class TechniqueShow {
    /** What the client knows of a technique under way. */
    public record Active(int entity, String character, String mechanic, int seq, int windup, int target, long start) {
        public int length() {
            return this.windup + 24;
        }
    }

    public record Payload(int entity, int seq, int windup, int target, long start) implements CustomPacketPayload {
        public static final Type<Payload> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "technique_show"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Payload> CODEC = StreamCodec.composite(ByteBufCodecs.VAR_INT, Payload::entity,
            ByteBufCodecs.VAR_INT, Payload::seq, ByteBufCodecs.VAR_INT, Payload::windup, ByteBufCodecs.VAR_INT, Payload::target, ByteBufCodecs.VAR_LONG,
            Payload::start, Payload::new);

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** The client's techniques under way, by entity id (written by the network thread's queued work, read by rendering). */
    public static final Map<Integer, Active> ACTIVE = new ConcurrentHashMap<>();

    private TechniqueShow() {
    }

    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent e) {
        e.registrar("1").optional().playToClient(Payload.TYPE, Payload.CODEC, (p, ctx) -> ctx.enqueueWork(() -> received(ctx.player().level(), p)));
    }

    private static void received(net.minecraft.world.level.Level level, Payload p) {
        if (!(level.getEntity(p.entity()) instanceof SupremeEntity b) || b.spec == null) {
            return;
        }
        ACTIVE.put(p.entity(), new Active(p.entity(), b.spec.id, mechanic(b, p.seq()), p.seq(), p.windup(), p.target(), p.start()));
    }

    /** The technique's kind: an arsenal technique's mechanic, or the base ability's style. */
    public static String mechanic(SupremeEntity b, int seq) {
        if (seq > 0) {
            List<CharacterArsenal.Skill> skills = CharacterArsenal.ALL.get(b.spec.id);
            if (skills != null && !skills.isEmpty()) {
                return skills.get(Math.floorMod(seq - 1, skills.size())).mechanic();
            }
        }
        if (Abilities.melee(b.spec.id)) {
            return "COMBO";
        }
        return b.spec.airborne() || b.spec.aquatic() ? "SWOOP" : "BOLT";
    }

    // ------------------------------------------------------------------------------------------------- the server side

    private static Field startField, durationField;
    private static boolean looked;

    @SuppressWarnings("unchecked")
    private static long[] motionState(SupremeEntity b) {
        try {
            if (!looked) {
                looked = true;
                startField = SupremeEntity.class.getDeclaredField("MOTION_START");
                durationField = SupremeEntity.class.getDeclaredField("MOTION_DURATION");
                startField.setAccessible(true);
                durationField.setAccessible(true);
            }
            if (startField == null || durationField == null) {
                return null;
            }
            long start = b.getEntityData().get((EntityDataAccessor<Long>) startField.get(null));
            int duration = b.getEntityData().get((EntityDataAccessor<Integer>) durationField.get(null));
            return new long[]{start, duration};
        } catch (ReflectiveOperationException | RuntimeException ex) {
            startField = durationField = null;
            return null;
        }
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses")
    public static final class Watch {
        private Watch() {
        }

        @SubscribeEvent
        public static void tick(EntityTickEvent.Post e) {
            if (!(e.getEntity() instanceof SupremeEntity b) || b.level().isClientSide || b.spec == null) {
                return;
            }
            long[] state = motionState(b);
            if (state == null) {
                return;
            }
            CompoundTag data = b.getPersistentData();
            if (data.getLong("OrorShowStart") == state[0]) {
                return;
            }
            data.putLong("OrorShowStart", state[0]);
            // a windup begins: the ability is ready and the character starts to cast (a technique's own motion at the
            // moment it goes off, 24 ticks long, and the moves' short motions are not shows)
            if (state[1] <= 24 || b.action() != 1) {
                return;
            }
            int seq = Math.floorMod(data.getInt("OrorCastSequence"), 4);
            if (!RebornConfig.EXTRA_ABILITIES.get()) {
                seq = 0;
            }
            LivingEntity target = b.getTarget();
            PacketDistributor.sendToPlayersTrackingEntity(b, new Payload(b.getId(), seq, (int) state[1] - 24, target == null ? -1 : target.getId(),
                state[0]));
        }
    }
}
