package jp.oror.reborn.show;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import jp.oror.reborn.Abilities;
import jp.oror.reborn.CharacterArsenal;
import jp.oror.reborn.RebornConfig;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/**
 * (052) What a character is doing, told to the players who can see it, so that each of its techniques and big moves has
 * its own motion and its own magic (TechniquePoses, TechniqueEffects) instead of the sixteen shared motions and the same
 * few sparks. The server watches each character: when a new motion begins with a windup (the ability is ready and it
 * starts to cast), the technique is the one its cast sequence points at (the base ability, or one of its three arsenal
 * techniques); when it starts one of its big moves (BossMoves), the move. Its windup, the moment it goes off, its length
 * and its target are sent. A guard's moments (a parry, a block, a broken guard, being parried: MobGuard) are sent the
 * same way, for the characters' and the royals' rigs to show, and are kept apart so that they play over a technique
 * without ending it.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
public final class TechniqueShow {
    /** What the client knows of a technique, a move or a guard's moment under way. */
    public record Active(int entity, String character, String mechanic, int seq, int windup, int length, int target, long start) {
    }

    /** kind: "tech", "move:<id>", "end" (a move ended early), or a guard's "parry", "block", "break", "parried". */
    public record Payload(int entity, String kind, int seq, int windup, int length, int target, long start) implements CustomPacketPayload {
        public static final Type<Payload> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "technique_show"));
        public static final StreamCodec<RegistryFriendlyByteBuf, Payload> CODEC = StreamCodec.ofMember(Payload::write, Payload::read);

        private void write(RegistryFriendlyByteBuf buf) {
            buf.writeVarInt(this.entity);
            buf.writeUtf(this.kind, 64);
            buf.writeVarInt(this.seq);
            buf.writeVarInt(this.windup);
            buf.writeVarInt(this.length);
            buf.writeVarInt(this.target);
            buf.writeVarLong(this.start);
        }

        private static Payload read(RegistryFriendlyByteBuf buf) {
            return new Payload(buf.readVarInt(), buf.readUtf(64), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(),
                buf.readVarLong());
        }

        @Override
        public Type<? extends CustomPacketPayload> type() {
            return TYPE;
        }
    }

    /** The client's techniques and moves under way, by entity id (written by the network thread's queued work). */
    public static final Map<Integer, Active> ACTIVE = new ConcurrentHashMap<>();
    /** The client's guard moments under way (parry, block, broken guard, parried), by entity id. */
    public static final Map<Integer, Active> REACT = new ConcurrentHashMap<>();

    private TechniqueShow() {
    }

    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent e) {
        e.registrar("2").optional().playToClient(Payload.TYPE, Payload.CODEC, (p, ctx) -> ctx.enqueueWork(() -> received(ctx.player().level(), p)));
    }

    private static void received(net.minecraft.world.level.Level level, Payload p) {
        Entity e = level.getEntity(p.entity());
        String character;
        if (e instanceof SupremeEntity b && b.spec != null) {
            character = b.spec.id;
        } else if (e instanceof RoyalMob) {
            character = "";
        } else {
            return;
        }
        String kind = p.kind();
        if (kind.equals("end")) {
            Active was = ACTIVE.get(p.entity());
            if (was != null && was.mechanic().startsWith("MOVE_")) {
                ACTIVE.remove(p.entity());
            }
            return;
        }
        if (kind.equals("tech")) {
            if (e instanceof SupremeEntity b) {
                ACTIVE.put(p.entity(), new Active(p.entity(), character, mechanic(b, p.seq()), p.seq(), p.windup(), p.length(), p.target(), p.start()));
            }
        } else if (kind.startsWith("move:")) {
            ACTIVE.put(p.entity(), new Active(p.entity(), character, "MOVE_" + kind.substring(5).toUpperCase(Locale.ROOT), 0, p.windup(), p.length(),
                p.target(), p.start()));
        } else {
            REACT.put(p.entity(), new Active(p.entity(), character, kind.toUpperCase(Locale.ROOT), 0, p.windup(), p.length(), p.target(), p.start()));
        }
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

    /** Tells the players who see it what the entity is doing (on the server; nothing happens on a client). */
    public static void send(Entity e, String kind, int seq, int windup, int length, int target) {
        if (e.level().isClientSide) {
            return;
        }
        PacketDistributor.sendToPlayersTrackingEntity(e, new Payload(e.getId(), kind, seq, windup, length, target, e.level().getGameTime()));
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

    /** The big moves' windups and lengths (BossMoves' table). */
    private static final Map<String, int[]> MOVES = Map.ofEntries(Map.entry("dash_slash", new int[]{10, 14}), Map.entry("blink_strike", new int[]{8, 14}),
        Map.entry("combo_rush", new int[]{6, 30}), Map.entry("spin_slash", new int[]{8, 32}), Map.entry("blade_wave", new int[]{10, 14}),
        Map.entry("leap_slam", new int[]{8, 40}), Map.entry("uppercut", new int[]{8, 26}), Map.entry("ground_spikes", new int[]{10, 36}),
        Map.entry("nova", new int[]{12, 34}), Map.entry("vortex", new int[]{10, 44}), Map.entry("meteor", new int[]{12, 48}),
        Map.entry("beam", new int[]{14, 46}), Map.entry("homing_orbs", new int[]{10, 70}), Map.entry("arrow_rain", new int[]{10, 44}),
        Map.entry("bolt_barrage", new int[]{6, 28}), Map.entry("bullet_storm", new int[]{8, 40}), Map.entry("shell_barrage", new int[]{10, 34}),
        Map.entry("barrier", new int[]{6, 24}), Map.entry("chain_pull", new int[]{8, 24}), Map.entry("reap", new int[]{8, 30}),
        Map.entry("ricochet", new int[]{8, 20}), Map.entry("afterimage", new int[]{6, 36}), Map.entry("charge", new int[]{10, 30}),
        Map.entry("breath", new int[]{12, 44}));

    @EventBusSubscriber(modid = "oror_supreme_bosses")
    public static final class Watch {
        private Watch() {
        }

        @SubscribeEvent
        public static void tick(EntityTickEvent.Post e) {
            if (!(e.getEntity() instanceof SupremeEntity b) || b.level().isClientSide || b.spec == null) {
                return;
            }
            CompoundTag data = b.getPersistentData();
            LivingEntity target = b.getTarget();
            int targetId = target == null ? -1 : target.getId();
            // a big move begins (BossMoves keeps it by name and start; a leap that lands early moves its start back,
            // which ends it, and is not a new move)
            String move = data.getString("ororMove");
            long moveAt = data.getLong("ororMoveAt");
            if (!move.isEmpty() && moveAt > data.getLong("OrorShowMoveAt")) {
                data.putLong("OrorShowMoveAt", moveAt);
                data.putBoolean("OrorShowMoving", true);
                int[] m = MOVES.getOrDefault(move, new int[]{8, 30});
                PacketDistributor.sendToPlayersTrackingEntity(b, new Payload(b.getId(), "move:" + move, 0, m[0], m[1], targetId, moveAt));
            } else if (move.isEmpty() && data.getBoolean("OrorShowMoving")) {
                data.putBoolean("OrorShowMoving", false);
                PacketDistributor.sendToPlayersTrackingEntity(b, new Payload(b.getId(), "end", 0, 0, 0, -1, b.level().getGameTime()));
            }
            long[] state = motionState(b);
            if (state == null) {
                return;
            }
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
            PacketDistributor.sendToPlayersTrackingEntity(b, new Payload(b.getId(), "tech", seq, (int) state[1] - 24, (int) state[1], targetId,
                state[0]));
        }
    }
}
