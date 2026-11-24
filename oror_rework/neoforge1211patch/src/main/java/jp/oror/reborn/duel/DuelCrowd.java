package jp.oror.reborn.duel;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.raid.Raider;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r71, the user: "決闘の際は周囲のモブが周りで円になって応援したり手を叩いて囃し立てたりするように") While a duel of Duel Dominion
 * goes on, the mobs about it (twenty blocks, the twenty nearest that walk on the ground: villagers, the kingdom's people,
 * monsters, beasts; not a boss, not the duellists) leave what they were doing, walk to a ring about the duel, face it and
 * cheer: they jump, clap (both hands in turn, a clap's sound), raiders throw up their arms as they do after a raid, the
 * villagers celebrate, notes rise. Now and then one of them shouts (いけー！ そこだ！ ...), one shout at a time above its
 * head. A monster in the ring is a spectator: it lets the duellists be. When the duel ends the ring cheers once more and
 * goes back to its business.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class DuelCrowd {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Duel Crowd");
    private static final String HECKLE = "oror_duel_heckle";
    private static final String[] SHOUTS = {"いけー！", "そこだ！", "やれやれー！", "負けるなー！", "いいぞー！", "おおーっ！", "決めろー！", "まだまだー！"};
    private static final int REACH = 20, MOST = 20, FINALE = 50;

    private static final class Ring {
        final ServerLevel level;
        final LivingEntity a, b;
        final List<Mob> crowd = new ArrayList<>();
        final Map<Mob, Vec3> slot = new HashMap<>();
        Display.TextDisplay shout;
        Mob shouter;
        int shoutLeft, age, finale = -1;

        Ring(ServerLevel level, LivingEntity a, LivingEntity b) {
            this.level = level;
            this.a = a;
            this.b = b;
        }

        Vec3 centre() {
            return a.position().add(b.position()).scale(0.5);
        }
    }

    private static final List<Ring> RINGS = new ArrayList<>();
    public static int recruited, cheers, shouts;

    private DuelCrowd() {
    }

    /** (DuelCrowdMixin) A duel has begun between these two. */
    public static void begun(LivingEntity a, LivingEntity b) {
        if (!(a.level() instanceof ServerLevel sl) || b == null) {
            return;
        }
        for (Ring r : RINGS) {
            if (r.finale < 0 && (r.a == a || r.b == a) && (r.a == b || r.b == b)) {
                return;
            }
        }
        RINGS.add(new Ring(sl, a, b));
        LOG.info("DUEL-CROWD start {} vs {}", a.getType().toShortString(), b.getType().toShortString());
    }

    /** (DuelCrowdMixin) The duel between these two is over: a last cheer, then the ring breaks up. */
    public static void ended(LivingEntity a, LivingEntity b) {
        for (Ring r : RINGS) {
            if (r.finale < 0 && (r.a == a || r.b == a || r.a == b || r.b == b)) {
                r.finale = FINALE;
                LOG.info("DUEL-CROWD end, {} watching, {} cheers, {} shouts", r.crowd.size(), cheers, shouts);
            }
        }
    }

    /** How many watch the duel this one fights in (for the CI check), or -1. */
    public static int watching(LivingEntity duellist) {
        // the duel still on, not one ending (a duellist's earlier duels linger for their last cheer)
        int most = -1;
        for (Ring r : RINGS) {
            if (r.a == duellist || r.b == duellist) {
                most = Math.max(most, r.finale < 0 ? r.crowd.size() : 0);
            }
        }
        return most;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        if (RINGS.isEmpty()) {
            return;
        }
        for (Ring r : new ArrayList<>(RINGS)) {
            try {
                if (!step(r)) {
                    release(r);
                    RINGS.remove(r);
                }
            } catch (RuntimeException ex) {
                LOG.warn("DUEL-CROWD stopped: {}", ex.toString());
                release(r);
                RINGS.remove(r);
            }
        }
    }

    /** One tick of a ring; false when it is over. */
    private static boolean step(Ring r) {
        r.age++;
        if (r.finale >= 0 && r.finale-- == 0) {
            return false;
        }
        if (r.finale < 0 && (!r.a.isAlive() && !r.b.isAlive() || r.a.isRemoved() && r.b.isRemoved() || r.age > 20 * 60 * 10
            || r.a.level() != r.level)) {
            return false;
        }
        Vec3 c = r.centre();
        double radius = Math.max(7.0, Math.min(13.0, r.a.distanceTo(r.b) / 2 + 5.5));
        if (r.finale < 0 && r.age % 20 == 1) {
            recruit(r, c);
            place(r, c, radius);
        }
        RandomSource rnd = r.level.random;
        for (Mob m : new ArrayList<>(r.crowd)) {
            if (!m.isAlive() || m.level() != r.level) {
                r.crowd.remove(m);
                r.slot.remove(m);
                continue;
            }
            // a spectator lets the duellists (and everyone) be
            if (m.getTarget() != null) {
                m.setTarget(null);
            }
            Vec3 s = r.slot.get(m);
            boolean there = s == null || m.position().distanceToSqr(s.x, m.getY(), s.z) < 2.2;
            if (!there && r.age % 10 == 0 && s != null) {
                m.getNavigation().moveTo(s.x, s.y, s.z, 1.1);
            }
            if (there) {
                if (!m.getNavigation().isDone()) {
                    m.getNavigation().stop();
                }
                m.getLookControl().setLookAt(c.x, c.y + 1.0, c.z, 30F, 30F);
                if (m instanceof Raider raider) {
                    raider.setCelebrating(true);
                }
                int every = r.finale >= 0 ? 8 : 26;
                if ((r.age + m.getId() * 7) % every == 0 && rnd.nextFloat() < 0.8F) {
                    cheer(r, m, rnd);
                }
            }
        }
        // one shout at a time
        if (r.shout != null) {
            if (--r.shoutLeft <= 0 || r.shouter == null || !r.shouter.isAlive()) {
                r.shout.discard();
                r.shout = null;
                r.shouter = null;
            } else {
                r.shout.setPos(r.shouter.getX(), r.shouter.getY() + r.shouter.getBbHeight() + 0.55, r.shouter.getZ());
            }
        } else if (!r.crowd.isEmpty() && r.age % (r.finale >= 0 ? 15 : 45) == 0) {
            Mob who = r.crowd.get(rnd.nextInt(r.crowd.size()));
            Vec3 s = r.slot.get(who);
            if (s == null || who.position().distanceToSqr(s.x, who.getY(), s.z) < 4.0) {
                shout(r, who, r.finale >= 0 ? "おおーっ！" : SHOUTS[rnd.nextInt(SHOUTS.length)]);
            }
        }
        return true;
    }

    private static void recruit(Ring r, Vec3 c) {
        if (r.crowd.size() >= MOST) {
            return;
        }
        List<PathfinderMob> near = r.level.getEntitiesOfClass(PathfinderMob.class, new AABB(c, c).inflate(REACH, 6, REACH), m -> m.isAlive() && m != r.a && m != r.b
            && !m.isNoAi() && !m.isPassenger() && !m.isVehicle() && m.getNavigation() instanceof GroundPathNavigation
            && !m.getType().is(Tags.EntityTypes.BOSSES) && !(m instanceof jp.oror.reborn.SupremeEntity) && !m.getTags().contains(HECKLE) && !r.crowd.contains(m));
        near.sort(Comparator.comparingDouble(m -> m.distanceToSqr(c)));
        for (PathfinderMob m : near) {
            if (r.crowd.size() >= MOST) {
                break;
            }
            r.crowd.add(m);
            recruited++;
        }
    }

    /** Each spectator its place on the ring, in the order they stand about it (so that none crosses the duel). */
    private static void place(Ring r, Vec3 c, double radius) {
        if (r.crowd.isEmpty()) {
            return;
        }
        List<Mob> order = new ArrayList<>(r.crowd);
        order.sort(Comparator.comparingDouble(m -> Math.atan2(m.getZ() - c.z, m.getX() - c.x)));
        double start = Math.atan2(order.get(0).getZ() - c.z, order.get(0).getX() - c.x);
        for (int i = 0; i < order.size(); i++) {
            double ang = start + Math.PI * 2 * i / order.size();
            double x = c.x + Math.cos(ang) * radius, z = c.z + Math.sin(ang) * radius;
            int y = r.level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, (int) Math.floor(x), (int) Math.floor(z));
            double yy = Math.abs(y - c.y) < 4 ? y : c.y;
            r.slot.put(order.get(i), new Vec3(x, yy, z));
        }
    }

    private static void cheer(Ring r, Mob m, RandomSource rnd) {
        cheers++;
        int kind = rnd.nextInt(3);
        if (kind == 0 && m.onGround()) {
            m.getJumpControl().jump();
        }
        // a clap: both hands in turn
        m.swing(InteractionHand.MAIN_HAND, true);
        m.swing(InteractionHand.OFF_HAND, true);
        r.level.playSound(null, m.getX(), m.getY() + 1, m.getZ(), SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.NEUTRAL, 0.35F, 1.6F + rnd.nextFloat() * 0.3F);
        if (kind == 1) {
            r.level.playSound(null, m.getX(), m.getY() + 1, m.getZ(), SoundEvents.NOTE_BLOCK_HAT.value(), SoundSource.NEUTRAL, 0.3F, 1.8F);
        }
        if (m instanceof AbstractVillager v) {
            if (kind == 2) {
                r.level.playSound(null, v.getX(), v.getY() + 1, v.getZ(), SoundEvents.VILLAGER_CELEBRATE, SoundSource.NEUTRAL, 0.6F, 1.0F);
            }
            r.level.sendParticles(ParticleTypes.HAPPY_VILLAGER, v.getX(), v.getY() + v.getBbHeight() + 0.2, v.getZ(), 3, 0.25, 0.1, 0.25, 0);
        } else if (m instanceof Raider raider && kind == 2) {
            r.level.playSound(null, raider.getX(), raider.getY() + 1, raider.getZ(), raider.getCelebrateSound(), SoundSource.HOSTILE, 0.6F, 1.0F);
        }
        r.level.sendParticles(ParticleTypes.NOTE, m.getX(), m.getY() + m.getBbHeight() + 0.4, m.getZ(), 1, 0.2, 0.1, 0.2, rnd.nextFloat());
    }

    private static void shout(Ring r, Mob who, String text) {
        Display.TextDisplay d = EntityType.TEXT_DISPLAY.create(r.level);
        if (d == null) {
            return;
        }
        shouts++;
        d.setPos(who.getX(), who.getY() + who.getBbHeight() + 0.55, who.getZ());
        d.addTag(HECKLE);
        net.minecraft.nbt.CompoundTag tag = new net.minecraft.nbt.CompoundTag();
        tag.putString("text", Component.Serializer.toJson(Component.literal(text).withStyle(net.minecraft.ChatFormatting.GOLD), r.level.registryAccess()));
        tag.putString("billboard", "center");
        tag.putInt("background", 0x60000000);
        d.load(tagged(d, tag));
        r.level.addFreshEntity(d);
        r.shout = d;
        r.shouter = who;
        r.shoutLeft = 32;
    }

    /** The display's own save with these fields laid over it (its text, its facing, its background). */
    private static net.minecraft.nbt.CompoundTag tagged(Entity d, net.minecraft.nbt.CompoundTag over) {
        net.minecraft.nbt.CompoundTag all = d.saveWithoutId(new net.minecraft.nbt.CompoundTag());
        all.merge(over);
        return all;
    }

    private static void release(Ring r) {
        for (Mob m : r.crowd) {
            if (m instanceof Raider raider && raider.getCurrentRaid() == null) {
                raider.setCelebrating(false);
            }
            if (m.isAlive()) {
                m.getNavigation().stop();
            }
        }
        r.crowd.clear();
        if (r.shout != null) {
            r.shout.discard();
        }
    }

    /** A shout left in the world (the game saved or stopped mid-duel) goes when it is loaded again. */
    @SubscribeEvent
    public static void stray(EntityJoinLevelEvent e) {
        if (!e.getLevel().isClientSide() && e.getEntity() instanceof Display.TextDisplay d && d.getTags().contains(HECKLE)) {
            boolean ours = false;
            for (Ring r : RINGS) {
                ours |= r.shout == d;
            }
            if (!ours && e.loadedFromDisk()) {
                e.setCanceled(true);
            }
        }
    }
}
