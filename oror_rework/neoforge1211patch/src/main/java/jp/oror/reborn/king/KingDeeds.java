package jp.oror.reborn.king;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.function.IntConsumer;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.core.component.DataComponents;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.joml.Vector3f;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The villager king's deeds in his later forms (the user: more varied and more vicious attacks, never weaker;
 * the broken form's attacks broken too, sometimes with no hit at all, sometimes hitting from somewhere strange; Baal
 * Zebul switching between demonic and divine arms). Every form keeps every deed of the forms before it.
 * <ul>
 * <li>The hero: the hero's charge (a dash through his foes), the great cleave (a wide arc before him), the spear of
 * light (thrown, bursting on its mark).</li>
 * <li>The broken one: desync (he is suddenly beside his foe and strikes three times from three sides; some strikes do
 * nothing, some land from the other side), rollback (his foes are snapped back to where they were three seconds
 * before), corruption (their hotbars shuffled, frozen in place), ghost mines (squares of the missing texture that burst
 * after a breath). And his hits are broken: one in three goes through his foe without a hit, one in four lands a
 * moment late or on someone else; a third of the blows on him go through him (MISS); phantom blows from nowhere; the
 * error arm's reach of seven blocks.</li>
 * <li>Baal Zebul, his divine arms (神器: Yagrush and Aymur): pillars of judgment under his foes, the Chaser thrown to
 * hunt its mark, the Driver's leap and fall, the gaze of heaven (a beam).</li>
 * <li>Baal Zebul, his demon's arm (魔器: the fly lord's scythe): the reaping (a three-quarter arc that drinks), the
 * vortex of flies (drawing his foes in), the brand (marks that burst), the plague (flies on all about him, their
 * healing stopped). One blow in eight on him is turned aside by his majesty.</li>
 * <li>Baal Zebul's other arms (the user: twin swords, a spear, a bow, taken up in turn): the twin swords' flurry (six
 * strikes from six sides in two seconds) and cross (two blades thrown crossed on his foe); the spear's lunge (twelve
 * blocks, all in the way run through and pinned) and javelin (the lightning on its mark, the thunder on to three more,
 * a field of sparks where it stands); the bow's rain of light and three arrows that pass through everything. He changes
 * arms every fifteen seconds, sooner when the one in hand is wrong for the distance: the bow or the spear for a far
 * foe, the swords or the scythe for a near one.</li>
 * <li>Nastier deeds (the user: guns only in the first form, nastier things instead): the execution (from the hero on:
 * the foe held up by the throat and driven into the ground, executed outright under a third of its health), the
 * sundering (armour cracked: a quarter of every piece's life, its protection halved ten seconds), the deletion (the
 * broken one: a sphere of the world round the foe deleted, back ten seconds later), the feast (Baal Zebul drinks the
 * life and the food of all about him) and the day of judgment (under a third of his life: the fire of heaven on every
 * foe in his sight; only the hidden are spared).</li>
 * </ul>
 * Deeds are counted on him (OrorKingDeeds, OrorKingDeedHits) for the CI.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingDeeds {
    private static final Logger LOG = LoggerFactory.getLogger("OROR King");
    static final String COUNT = "OrorKingDeeds", HITS = "OrorKingDeedHits", BUSY = "OrorKingBusyUntil", STANCE = "OrorKingStanceAt";

    /** A deed: its name, the least form it needs, its stance (0 any; 1 clubs, 2 scythe, 3 twin swords, 4 spear, 5 bow),
     * its range, how often, its windup and length (ticks). */
    record Deed(String id, int phase, int stance, double min, double max, int every, int windup, int length) {
    }

    static final List<Deed> DEEDS = List.of(
        new Deed("charge", 1, 0, 6, 24, 160, 10, 26),
        new Deed("cleave", 1, 0, 0, 6, 120, 12, 26),
        new Deed("spear", 1, 0, 8, 40, 200, 14, 26),
        new Deed("execution", 1, 0, 0, 5, 300, 10, 50),
        new Deed("sunder", 1, 0, 0, 6, 240, 8, 24),
        new Deed("desync", 2, 0, 0, 16, 140, 4, 34),
        new Deed("rollback", 2, 0, 0, 24, 300, 10, 30),
        new Deed("corrupt", 2, 0, 0, 16, 360, 8, 24),
        new Deed("ghosts", 2, 0, 0, 32, 220, 10, 28),
        new Deed("void", 2, 0, 0, 24, 360, 30, 40),
        new Deed("judgment", 3, 1, 0, 32, 160, 12, 30),
        new Deed("chaser", 3, 1, 6, 48, 180, 10, 22),
        new Deed("driver", 3, 1, 6, 30, 220, 8, 34),
        new Deed("gaze", 3, 1, 0, 40, 260, 20, 60),
        new Deed("reap", 3, 2, 0, 8, 120, 12, 26),
        new Deed("vortex", 3, 2, 0, 20, 240, 10, 40),
        new Deed("brand", 3, 2, 0, 24, 200, 10, 24),
        new Deed("plague", 3, 2, 0, 16, 400, 12, 30),
        new Deed("flurry", 3, 3, 0, 10, 140, 6, 30),
        new Deed("crossslash", 3, 3, 0, 16, 160, 12, 24),
        new Deed("lunge", 3, 4, 3, 16, 140, 12, 20),
        new Deed("javelin", 3, 4, 8, 48, 200, 14, 30),
        new Deed("rain", 3, 5, 6, 48, 220, 14, 50),
        new Deed("triple", 3, 5, 3, 48, 100, 10, 20),
        new Deed("feast", 3, 0, 0, 16, 400, 10, 60),
        new Deed("doomsday", 3, 0, 0, 48, 1200, 60, 100));

    private KingDeeds() {
    }

    // -------------------------------------------------------------------------------------------- the scheduler

    private record Later(ServerLevel level, long due, Runnable run) {
    }

    private static final List<Later> LATER = new ArrayList<>();

    static void later(ServerLevel sl, int ticks, Runnable run) {
        LATER.add(new Later(sl, sl.getGameTime() + Math.max(1, ticks), run));
    }

    /** Runs each tick from `from` to `from + count - 1` (its index given). */
    static void each(ServerLevel sl, int from, int count, int step, IntConsumer run) {
        for (int i = 0; i < count; i++) {
            final int k = i;
            later(sl, from + i * step, () -> run.accept(k));
        }
    }

    @SubscribeEvent
    public static void run(ServerTickEvent.Post e) {
        if (LATER.isEmpty()) {
            return;
        }
        List<Later> due = new ArrayList<>();
        for (Iterator<Later> it = LATER.iterator(); it.hasNext(); ) {
            Later l = it.next();
            if (l.level.getGameTime() >= l.due) {
                due.add(l);
                it.remove();
            }
        }
        for (Later l : due) {
            try {
                l.run.run();
            } catch (RuntimeException ex) {
                LOG.warn("KING-DEED-ERROR {}", ex.toString());
            }
        }
    }

    @SubscribeEvent
    public static void stopped(ServerStoppedEvent e) {
        LATER.clear();
        RESTORE.clear();
    }

    /** The world deleted by the broken king, to be put back (on time, or at once when the server stops). */
    private static final List<Runnable> RESTORE = new ArrayList<>();

    @SubscribeEvent
    public static void stopping(ServerStoppingEvent e) {
        for (Runnable r : new ArrayList<>(RESTORE)) {
            try {
                r.run();
            } catch (RuntimeException ex) {
                LOG.warn("KING-RESTORE-ERROR {}", ex.toString());
            }
        }
        RESTORE.clear();
    }

    // -------------------------------------------------------------------------------------------- choosing

    /** His stance in his last form, by what is in his main hand: 1 the thunder clubs (a mace), 2 the fly lord's scythe
     * (a netherite hoe), 3 the twin swords (a netherite sword), 4 the thunder spear (a trident), 5 the rainbow bow. */
    public static int stance(RoyalMob king) {
        ItemStack m = king.getMainHandItem();
        if (m.is(Items.NETHERITE_HOE)) {
            return 2;
        }
        if (m.is(Items.NETHERITE_SWORD)) {
            return 3;
        }
        if (m.is(Items.TRIDENT)) {
            return 4;
        }
        if (m.is(Items.BOW)) {
            return 5;
        }
        return 1;
    }

    /** He holds one of his five arms (KingForms.tick re-arms him otherwise). */
    public static boolean armed(RoyalMob king) {
        ItemStack m = king.getMainHandItem();
        return m.is(Items.MACE) || m.is(Items.NETHERITE_HOE) || m.is(Items.NETHERITE_SWORD) || m.is(Items.TRIDENT) || m.is(Items.BOW);
    }

    /** The next arm for the distance: the bow or the spear for a far foe, the twin swords or the scythe for a near one,
     * any between; never the one in hand. */
    static int nextStance(int cur, double dist, long seed) {
        int[] pick = dist > 16 ? new int[]{5, 4, 1} : dist < 6 ? new int[]{3, 2, 1} : new int[]{1, 2, 3, 4, 5};
        int i = new java.util.Random(seed).nextInt(pick.length);
        return pick[i] != cur ? pick[i] : pick[(i + 1) % pick.length];
    }

    /** From KingForms.tick, while he fights: the stance, his broken form's passive glitches, and the next deed. */
    static void tick(RoyalMob king, ServerLevel sl, int phase, LivingEntity t) {
        CompoundTag d = king.getPersistentData();
        long now = sl.getGameTime();
        if (phase >= 3) {
            long at = d.getLong(STANCE);
            int cur = stance(king);
            double far = king.distanceTo(t);
            boolean wrong = (far > 20 && (cur == 2 || cur == 3)) || (far < 4 && cur == 5);
            if (now >= at || (wrong && now >= at - 200)) {
                d.putLong(STANCE, now + 300);
                switchStance(king, sl, nextStance(cur, far, now ^ king.getId()));
            }
        }
        if (phase == 2) {
            brokenPassives(king, sl, t, now);
        }
        if (now < d.getLong(BUSY)) {
            return;
        }
        double dist = king.distanceTo(t);
        int st = phase >= 3 ? stance(king) : 0;
        List<Deed> order = new ArrayList<>(DEEDS);
        Collections.shuffle(order, new java.util.Random(now ^ king.getId()));
        for (Deed deed : order) {
            if (deed.phase > phase || (deed.stance != 0 && deed.stance != st) || dist < deed.min || dist > deed.max) {
                continue;
            }
            if (now < d.getLong("OrorKingDeed_" + deed.id)) {
                continue;
            }
            if (deed.max > 8 && !king.hasLineOfSight(t)) {
                continue;
            }
            if (deed.id.equals("doomsday") && king.getHealth() >= king.getMaxHealth() * 0.35F) {
                continue;
            }
            d.putLong("OrorKingDeed_" + deed.id, now + deed.every);
            perform(king, sl, deed.id, t);
            return;
        }
    }

    static Deed deed(String id) {
        for (Deed d : DEEDS) {
            if (d.id.equals(id)) {
                return d;
            }
        }
        return null;
    }

    /** Does one deed on the target now (the CI calls it directly). */
    public static void perform(RoyalMob king, ServerLevel sl, String id, LivingEntity t) {
        Deed deed = deed(id);
        if (deed == null || t == null) {
            return;
        }
        CompoundTag d = king.getPersistentData();
        d.putLong(BUSY, sl.getGameTime() + deed.length);
        count(king, COUNT, id);
        TechniqueShow.send(king, "move:king_" + id, 0, deed.windup, deed.length, t.getId());
        int w = deed.windup;
        switch (id) {
            case "charge" -> charge(king, sl, t, w);
            case "cleave" -> later(sl, w, () -> cleave(king, sl, t));
            case "spear" -> spear(king, sl, t, w);
            case "desync" -> desync(king, sl, t, w);
            case "rollback" -> rollback(king, sl, w);
            case "corrupt" -> later(sl, w, () -> corrupt(king, sl));
            case "ghosts" -> ghosts(king, sl, t, w);
            case "judgment" -> judgment(king, sl, w);
            case "chaser" -> chaser(king, sl, t, w);
            case "driver" -> driver(king, sl, t, w);
            case "gaze" -> gaze(king, sl, t, w);
            case "reap" -> later(sl, w, () -> reap(king, sl, t));
            case "vortex" -> vortex(king, sl, w);
            case "brand" -> brand(king, sl, w);
            case "plague" -> later(sl, w, () -> plague(king, sl));
            case "execution" -> execution(king, sl, t, w);
            case "sunder" -> sunder(king, sl, t, w);
            case "void" -> deletion(king, sl, t, w);
            case "flurry" -> flurry(king, sl, t, w);
            case "crossslash" -> crossslash(king, sl, t, w);
            case "lunge" -> lunge(king, sl, t, w);
            case "javelin" -> javelin(king, sl, t, w);
            case "rain" -> rain(king, sl, t, w);
            case "triple" -> triple(king, sl, t, w);
            case "feast" -> feast(king, sl, w);
            case "doomsday" -> doomsday(king, sl, w);
            default -> {
            }
        }
    }

    // -------------------------------------------------------------------------------------------- helpers

    static void count(RoyalMob king, String key, String id) {
        CompoundTag d = king.getPersistentData();
        CompoundTag c = d.getCompound(key);
        c.putInt(id, c.getInt(id) + 1);
        d.put(key, c);
    }

    /** A blow of a deed: counted when it lands. */
    static boolean hit(RoyalMob king, String id, LivingEntity v, float amount, boolean magic) {
        if (!v.isAlive() || !king.isAlive()) {
            return false;
        }
        DamageSource src = magic ? king.damageSources().indirectMagic(king, king) : king.damageSources().mobAttack(king);
        boolean landed = v.hurt(src, amount);
        if (landed) {
            count(king, HITS, id);
        }
        return landed;
    }

    static final DustParticleOptions GOLD = new DustParticleOptions(new Vector3f(1.0F, 0.82F, 0.25F), 1.5F);
    static final DustParticleOptions WHITE = new DustParticleOptions(new Vector3f(1.0F, 0.98F, 0.9F), 1.6F);
    static final DustParticleOptions MAGENTA = new DustParticleOptions(new Vector3f(1.0F, 0.0F, 1.0F), 1.4F);
    static final DustParticleOptions CYAN = new DustParticleOptions(new Vector3f(0.0F, 1.0F, 1.0F), 1.4F);
    static final DustParticleOptions BLACK = new DustParticleOptions(new Vector3f(0.02F, 0.02F, 0.02F), 1.5F);
    static final DustParticleOptions CRIMSON = new DustParticleOptions(new Vector3f(0.75F, 0.05F, 0.08F), 1.6F);
    static final DustParticleOptions RED = new DustParticleOptions(new Vector3f(1.0F, 0.15F, 0.05F), 1.3F);

    static void sound(ServerLevel sl, Vec3 at, SoundEvent s, float vol, float pitch) {
        sl.playSound(null, at.x, at.y, at.z, s, SoundSource.HOSTILE, vol, pitch);
    }

    static void ring(ServerLevel sl, ParticleOptions o, Vec3 at, double r, double y, int n) {
        for (int i = 0; i < n; i++) {
            double a = 2 * Math.PI * i / n;
            sl.sendParticles(o, at.x + Math.cos(a) * r, at.y + y, at.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
        }
    }

    static void line(ServerLevel sl, ParticleOptions o, Vec3 a, Vec3 b, double step) {
        Vec3 d = b.subtract(a);
        double L = d.length();
        for (double s = 0; s < L; s += step) {
            Vec3 p = a.add(d.scale(s / L));
            sl.sendParticles(o, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
    }

    static Vec3 flat(Vec3 v) {
        Vec3 f = new Vec3(v.x, 0, v.z);
        return f.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : f.normalize();
    }

    static void throwFrom(LivingEntity v, Vec3 from, double strength, double up) {
        Vec3 away = flat(v.position().subtract(from));
        v.setDeltaMovement(v.getDeltaMovement().add(away.x * strength, up, away.z * strength));
        v.hurtMarked = true;
    }

    // -------------------------------------------------------------------------------------------- the hero

    private static void charge(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        sound(sl, king.position(), SoundEvents.RAVAGER_ROAR, 3F, 0.8F);
        Set<LivingEntity> struck = new HashSet<>();
        later(sl, w, () -> {
            Vec3 dir = flat(t.position().subtract(king.position()));
            each(sl, 0, 10, 1, k -> {
                king.getNavigation().stop();
                king.setDeltaMovement(dir.x * 1.5, king.getDeltaMovement().y, dir.z * 1.5);
                king.hurtMarked = true;
                sl.sendParticles(ParticleTypes.CLOUD, king.getX(), king.getY() + 0.3, king.getZ(), 4, 0.4, 0.1, 0.4, 0.02);
                sl.sendParticles(GOLD, king.getX(), king.getY() + king.getBbHeight() * 0.5, king.getZ(), 6, 0.6, 0.6, 0.6, 0);
                for (LivingEntity v : KingForms.foes(king, sl, 2.6 + king.getBbWidth() * 0.5)) {
                    if (struck.add(v) && hit(king, "charge", v, 18F, false)) {
                        throwFrom(v, king.position(), 1.2, 0.6);
                        sound(sl, v.position(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2F, 0.7F);
                    }
                }
            });
        });
    }

    private static void cleave(RoyalMob king, ServerLevel sl, LivingEntity t) {
        Vec3 fwd = flat(t.position().subtract(king.position()));
        for (LivingEntity v : KingForms.foes(king, sl, 7.0 + king.getBbWidth() * 0.5)) {
            Vec3 to = flat(v.position().subtract(king.position()));
            if (to.dot(fwd) > Math.cos(Math.toRadians(85)) && hit(king, "cleave", v, 26F, false)) {
                throwFrom(v, king.position(), 2.0, 0.4);
                v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
            }
        }
        double base = Math.atan2(fwd.z, fwd.x);
        for (int i = -8; i <= 8; i++) {
            double a = base + i * Math.toRadians(10);
            for (double r = 3.0; r <= 6.5; r += 1.75) {
                sl.sendParticles(ParticleTypes.SWEEP_ATTACK, king.getX() + Math.cos(a) * r, king.getY() + 1.2, king.getZ() + Math.sin(a) * r, 1, 0, 0, 0, 0);
            }
        }
        sound(sl, king.position(), SoundEvents.PLAYER_ATTACK_SWEEP, 3F, 0.6F);
        sound(sl, king.position(), SoundEvents.ANVIL_LAND, 1F, 1.6F);
    }

    private static void spear(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3 start = king.getEyePosition();
            sound(sl, start, SoundEvents.ARROW_SHOOT, 3F, 0.5F);
            each(sl, 0, 6, 1, k -> {
                Vec3 end = t.getEyePosition();
                Vec3 p = start.add(end.subtract(start).scale((k + 1) / 6.0));
                sl.sendParticles(ParticleTypes.END_ROD, p.x, p.y, p.z, 8, 0.15, 0.15, 0.15, 0.02);
                sl.sendParticles(GOLD, p.x, p.y, p.z, 6, 0.2, 0.2, 0.2, 0);
                if (k == 5) {
                    for (LivingEntity v : KingForms.foes(king, sl, 48)) {
                        double dd = v.distanceTo(t);
                        if (dd <= 3.0 && hit(king, "spear", v, v == t ? 20F : 12F, true)) {
                            v.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0));
                            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1));
                        }
                    }
                    sl.sendParticles(ParticleTypes.EXPLOSION, end.x, end.y, end.z, 2, 0.3, 0.3, 0.3, 0);
                    sl.sendParticles(ParticleTypes.END_ROD, end.x, end.y, end.z, 60, 0.6, 0.6, 0.6, 0.25);
                    sound(sl, end, SoundEvents.LIGHTNING_BOLT_IMPACT, 2F, 1.4F);
                }
            });
        });
    }

    // -------------------------------------------------------------------------------------------- the broken one

    private static void glitchAt(ServerLevel sl, Vec3 p) {
        for (DustParticleOptions o : new DustParticleOptions[]{MAGENTA, CYAN, BLACK}) {
            sl.sendParticles(o, p.x, p.y, p.z, 10, 0.4, 0.5, 0.4, 0.02);
        }
    }

    private static void desync(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        for (int s = 0; s < 3; s++) {
            final int strike = s;
            later(sl, w + s * 10, () -> {
                if (!t.isAlive()) {
                    return;
                }
                double a = sl.random.nextDouble() * Math.PI * 2;
                Vec3 from = king.position();
                Vec3 to = t.position().add(Math.cos(a) * 1.8, 0, Math.sin(a) * 1.8);
                glitchAt(sl, from.add(0, 1, 0));
                king.teleportTo(to.x, t.getY(), to.z);
                king.getLookControl().setLookAt(t);
                glitchAt(sl, king.position().add(0, 1, 0));
                sound(sl, to, SoundEvents.ENDERMAN_TELEPORT, 2F, 1.7F);
                sound(sl, to, SoundEvents.NOTE_BLOCK_BIT.value(), 2F, 0.5F + sl.random.nextFloat());
                int roll = sl.random.nextInt(3);
                if (roll == 0 && strike < 2) {
                    // a strike with no hit: it goes through
                    glitchAt(sl, t.position().add(0, 1, 0));
                } else if (hit(king, "desync", t, 14F, false)) {
                    // the others land, one of them from the wrong side: it draws the foe in
                    if (roll == 1) {
                        throwFrom(t, t.position().add(t.position().subtract(king.position())), 1.0, 0.2);
                    } else {
                        throwFrom(t, king.position(), 0.8, 0.3);
                    }
                    t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 20, 2));
                }
            });
        }
    }

    private static void rollback(RoyalMob king, ServerLevel sl, int w) {
        later(sl, w, () -> {
            List<LivingEntity> marked = new ArrayList<>(KingForms.foes(king, sl, 24.0));
            if (marked.size() > 8) {
                marked = marked.subList(0, 8);
            }
            List<Vec3> saved = new ArrayList<>();
            for (LivingEntity v : marked) {
                saved.add(v.position());
            }
            final List<LivingEntity> ms = marked;
            each(sl, 0, 12, 5, k -> {
                for (Vec3 p : saved) {
                    sl.sendParticles(k % 2 == 0 ? MAGENTA : CYAN, p.x, p.y + 1.0, p.z, 12, 0.3, 0.9, 0.3, 0);
                }
            });
            later(sl, 60, () -> {
                for (int i = 0; i < ms.size(); i++) {
                    LivingEntity v = ms.get(i);
                    Vec3 p = saved.get(i);
                    if (!v.isAlive() || v.level() != sl) {
                        continue;
                    }
                    if (v instanceof ServerPlayer sp) {
                        sp.teleportTo(sl, p.x, p.y, p.z, sp.getYRot(), sp.getXRot());
                        sp.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 100, 0));
                    } else {
                        v.teleportTo(p.x, p.y, p.z);
                    }
                    v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2));
                    hit(king, "rollback", v, 12F, true);
                    glitchAt(sl, p.add(0, 1, 0));
                }
                sound(sl, king.position(), SoundEvents.ENDERMAN_TELEPORT, 3F, 0.5F);
                sound(sl, king.position(), SoundEvents.NOTE_BLOCK_BIT.value(), 3F, 0.5F);
            });
        });
    }

    private static void corrupt(RoyalMob king, ServerLevel sl) {
        for (LivingEntity v : KingForms.foes(king, sl, 16.0)) {
            if (v instanceof Player p) {
                List<ItemStack> bar = new ArrayList<>();
                for (int i = 0; i < 9; i++) {
                    bar.add(p.getInventory().getItem(i));
                }
                Collections.shuffle(bar, new java.util.Random(sl.getGameTime() ^ p.getId()));
                for (int i = 0; i < 9; i++) {
                    p.getInventory().setItem(i, bar.get(i));
                }
                p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 6));
                p.addEffect(new MobEffectInstance(MobEffects.DIG_SLOWDOWN, 100, 1));
                p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 20, 0));
                p.displayClientMessage(Component.literal("§kXX§r データ破損：ホットバーが壊れた §kXX").withStyle(ChatFormatting.LIGHT_PURPLE), true);
                hit(king, "corrupt", v, 8F, true);
            } else {
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 6));
                hit(king, "corrupt", v, 12F, true);
            }
            sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MAGENTA_CONCRETE.defaultBlockState()), v.getX(), v.getY() + 1,
                v.getZ(), 30, 0.4, 0.6, 0.4, 0.1);
        }
        sound(sl, king.position(), SoundEvents.ITEM_BREAK, 3F, 0.5F);
        sound(sl, king.position(), SoundEvents.NOTE_BLOCK_BIT.value(), 3F, 1.9F);
    }

    private static void ghosts(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        List<Vec3> pts = new ArrayList<>();
        pts.add(t.position());
        for (int i = 0; i < 4; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2, r = 3 + sl.random.nextDouble() * 2.5;
            pts.add(t.position().add(Math.cos(a) * r, 0, Math.sin(a) * r));
        }
        each(sl, 0, (w + 30) / 3, 3, k -> {
            for (Vec3 p : pts) {
                for (int j = 0; j < 8; j++) {
                    double x = (j % 3 - 1) * 1.25, z = (j / 3 - 1) * 1.25;
                    sl.sendParticles((j + k) % 2 == 0 ? MAGENTA : BLACK, p.x + x, p.y + 0.1, p.z + z, 1, 0, 0, 0, 0);
                }
            }
        });
        later(sl, w + 30, () -> {
            for (Vec3 p : pts) {
                for (LivingEntity v : KingForms.foes(king, sl, 48)) {
                    if (v.position().distanceTo(p) <= 2.8 && hit(king, "ghosts", v, 22F, true)) {
                        v.setDeltaMovement(v.getDeltaMovement().add(0, 0.9, 0));
                        v.hurtMarked = true;
                        v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0));
                    }
                }
                sl.sendParticles(ParticleTypes.EXPLOSION, p.x, p.y + 0.5, p.z, 1, 0, 0, 0, 0);
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.MAGENTA_CONCRETE.defaultBlockState()), p.x, p.y + 0.5, p.z, 40,
                    0.8, 0.5, 0.8, 0.2);
            }
            sound(sl, t.position(), SoundEvents.DRAGON_FIREBALL_EXPLODE, 3F, 1.5F);
            sound(sl, t.position(), SoundEvents.GLASS_BREAK, 3F, 0.6F);
        });
    }

    /** The broken king's hits are broken: phantom blows from nowhere, the error arm's long reach. */
    private static void brokenPassives(RoyalMob king, ServerLevel sl, LivingEntity t, long now) {
        if (now % 80 == king.getId() % 80) {
            List<LivingEntity> fs = KingForms.foes(king, sl, 20.0);
            if (!fs.isEmpty()) {
                LivingEntity v = fs.get(sl.random.nextInt(fs.size()));
                Vec3 from = v.position().add((sl.random.nextDouble() - 0.5) * 6, sl.random.nextDouble() * 2, (sl.random.nextDouble() - 0.5) * 6);
                glitchAt(sl, from.add(0, 1, 0));
                if (hit(king, "phantom", v, 10F, true)) {
                    throwFrom(v, from, 0.8, 0.3);
                }
            }
        }
        if (now % 60 == (king.getId() + 30) % 60 && king.distanceTo(t) <= 7.0 + king.getBbWidth() * 0.5) {
            line(sl, MAGENTA, king.position().add(0, king.getBbHeight() * 0.5, 0), t.position().add(0, 1, 0), 0.4);
            if (hit(king, "error_arm", t, 14F, false)) {
                Vec3 in = flat(king.position().subtract(t.position()));
                t.setDeltaMovement(t.getDeltaMovement().add(in.x * 0.9, 0.2, in.z * 0.9));
                t.hurtMarked = true;
            }
            sound(sl, t.position(), SoundEvents.NOTE_BLOCK_BIT.value(), 2F, 0.3F);
        }
    }

    // -------------------------------------------------------------------------------------------- the divine arms

    private static void judgment(RoyalMob king, ServerLevel sl, int w) {
        later(sl, w, () -> {
            List<LivingEntity> fs = new ArrayList<>(KingForms.foes(king, sl, 32.0));
            if (fs.size() > 6) {
                fs = fs.subList(0, 6);
            }
            for (LivingEntity f : fs) {
                Vec3 c = f.position();
                each(sl, 0, 9, 3, k -> {
                    ring(sl, GOLD, c, 2.2, 0.1, 22);
                    sl.sendParticles(ParticleTypes.END_ROD, c.x, c.y + 6 + k, c.z, 2, 0.2, 0.5, 0.2, 0);
                });
                later(sl, 25, () -> {
                    for (LivingEntity v : KingForms.foes(king, sl, 48)) {
                        if (v.position().distanceTo(c) <= 2.4 && hit(king, "judgment", v, 30F, true)) {
                            v.igniteForSeconds(6);
                            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1));
                        }
                    }
                    KingForms.bolt(sl, c);
                    for (double y = 0; y < 18; y += 0.6) {
                        sl.sendParticles(ParticleTypes.END_ROD, c.x, c.y + y, c.z, 2, 0.4, 0.1, 0.4, 0);
                    }
                    sound(sl, c, SoundEvents.AMETHYST_BLOCK_CHIME, 3F, 0.6F);
                });
            }
        });
    }

    private static void chaser(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3[] orb = {king.getEyePosition()};
            boolean[] done = {false};
            sound(sl, orb[0], SoundEvents.LIGHTNING_BOLT_IMPACT, 2F, 1.8F);
            each(sl, 0, 40, 1, k -> {
                if (done[0] || !t.isAlive()) {
                    return;
                }
                Vec3 to = t.getEyePosition().subtract(orb[0]);
                double L = to.length();
                orb[0] = orb[0].add(to.scale(Math.min(1.0, 1.4 / Math.max(0.01, L))));
                sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, orb[0].x, orb[0].y, orb[0].z, 10, 0.3, 0.3, 0.3, 0.05);
                sl.sendParticles(GOLD, orb[0].x, orb[0].y, orb[0].z, 4, 0.2, 0.2, 0.2, 0);
                if (L < 1.4) {
                    done[0] = true;
                    if (hit(king, "chaser", t, 28F, false)) {
                        throwFrom(t, king.position(), 2.5, 0.5);
                    }
                    int chained = 0;
                    for (LivingEntity v : KingForms.foes(king, sl, 48)) {
                        if (v != t && v.distanceTo(t) <= 8 && chained < 2) {
                            chained++;
                            line(sl, ParticleTypes.ELECTRIC_SPARK, t.getEyePosition(), v.getEyePosition(), 0.5);
                            hit(king, "chaser", v, 12F, true);
                        }
                    }
                    sound(sl, t.position(), SoundEvents.LIGHTNING_BOLT_THUNDER, 2F, 1.5F);
                }
            });
        });
    }

    private static void driver(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        Vec3 c = t.position();
        each(sl, 0, 14, 2, k -> {
            ring(sl, RED, c, 5.0, 0.1, 40);
            ring(sl, GOLD, c, 2.5, 0.1, 20);
        });
        later(sl, w, () -> {
            king.setDeltaMovement(0, 1.6, 0);
            king.hurtMarked = true;
            sound(sl, king.position(), SoundEvents.WIND_CHARGE_BURST.value(), 3F, 0.6F);
        });
        later(sl, w + 12, () -> king.teleportTo(c.x, c.y + 7, c.z));
        later(sl, w + 20, () -> {
            king.teleportTo(c.x, c.y, c.z);
            king.fallDistance = 0F;
            for (LivingEntity v : KingForms.foes(king, sl, 5.0 + king.getBbWidth() * 0.5)) {
                if (hit(king, "driver", v, 40F, false)) {
                    throwFrom(v, c, 1.5, 1.0);
                }
            }
            sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y, c.z, 1, 0, 0, 0, 0);
            sl.sendParticles(ParticleTypes.GUST_EMITTER_LARGE, c.x, c.y + 0.5, c.z, 1, 0, 0, 0, 0);
            sound(sl, c, SoundEvents.MACE_SMASH_GROUND_HEAVY, 3F, 0.6F);
            sound(sl, c, SoundEvents.DRAGON_FIREBALL_EXPLODE, 3F, 0.6F);
        });
    }

    private static void gaze(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        each(sl, 0, w / 2, 2, k -> line(sl, RED, king.getEyePosition(), t.getEyePosition(), 0.8));
        sound(sl, king.position(), SoundEvents.GUARDIAN_ATTACK, 3F, 0.5F);
        each(sl, w, 20, 2, k -> {
            if (!t.isAlive()) {
                return;
            }
            Vec3 a = king.getEyePosition(), b = t.getEyePosition();
            line(sl, ParticleTypes.END_ROD, a, b, 0.5);
            line(sl, WHITE, a, b, 0.7);
            if (k % 5 == 0 && king.hasLineOfSight(t)) {
                if (hit(king, "gaze", t, 10F, true)) {
                    t.igniteForSeconds(3);
                    t.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100, 0));
                }
                sound(sl, b, SoundEvents.BEACON_AMBIENT, 2F, 1.6F);
            }
        });
    }

    // -------------------------------------------------------------------------------------------- the demon's arm

    private static void reap(RoyalMob king, ServerLevel sl, LivingEntity t) {
        Vec3 fwd = flat(t.position().subtract(king.position()));
        float drunk = 0F;
        for (LivingEntity v : KingForms.foes(king, sl, 8.0 + king.getBbWidth() * 0.5)) {
            Vec3 to = flat(v.position().subtract(king.position()));
            if (to.dot(fwd) > Math.cos(Math.toRadians(135))) {
                float before = v.getHealth();
                if (hit(king, "reap", v, 34F, false)) {
                    v.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
                    drunk += Math.max(0F, before - v.getHealth());
                }
            }
        }
        if (drunk > 0F) {
            king.heal(drunk * 0.3F);
        }
        double base = Math.atan2(fwd.z, fwd.x);
        for (int i = -13; i <= 13; i++) {
            double a = base + i * Math.toRadians(10);
            for (double r = 3.0; r <= 8.0; r += 1.6) {
                sl.sendParticles(CRIMSON, king.getX() + Math.cos(a) * r, king.getY() + 1.4, king.getZ() + Math.sin(a) * r, 2, 0.1, 0.1, 0.1, 0);
            }
            sl.sendParticles(ParticleTypes.SWEEP_ATTACK, king.getX() + Math.cos(a) * 5, king.getY() + 1.4, king.getZ() + Math.sin(a) * 5, 1, 0, 0, 0, 0);
        }
        sound(sl, king.position(), SoundEvents.PLAYER_ATTACK_SWEEP, 3F, 0.45F);
        sound(sl, king.position(), SoundEvents.WITHER_SHOOT, 2F, 0.6F);
    }

    private static void vortex(RoyalMob king, ServerLevel sl, int w) {
        sound(sl, king.position(), SoundEvents.BEE_LOOP_AGGRESSIVE, 4F, 0.5F);
        each(sl, w, 15, 2, k -> {
            Vec3 c = king.position();
            for (int i = 0; i < 24; i++) {
                double a = i * Math.PI / 12 + k * 0.4, r = 2 + (i % 6) * 2;
                sl.sendParticles(ParticleTypes.SQUID_INK, c.x + Math.cos(a) * r, c.y + 0.5 + (i % 4), c.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
            }
            for (LivingEntity v : KingForms.foes(king, sl, 14.0)) {
                Vec3 in = flat(c.subtract(v.position()));
                v.setDeltaMovement(v.getDeltaMovement().add(in.x * 0.35, 0.05, in.z * 0.35));
                v.hurtMarked = true;
                if (k % 5 == 0 && hit(king, "vortex", v, 6F, true)) {
                    v.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 1));
                }
            }
        });
    }

    private static void brand(RoyalMob king, ServerLevel sl, int w) {
        later(sl, w, () -> {
            List<LivingEntity> fs = new ArrayList<>(KingForms.foes(king, sl, 24.0));
            if (fs.size() > 4) {
                fs = fs.subList(0, 4);
            }
            for (LivingEntity v : fs) {
                each(sl, 0, 12, 5, k -> {
                    if (v.isAlive()) {
                        ring(sl, CRIMSON, v.position(), 0.8, v.getBbHeight() + 0.5, 10);
                        sl.sendParticles(RED, v.getX(), v.getY() + v.getBbHeight() + 0.5, v.getZ(), 3, 0.1, 0.1, 0.1, 0);
                    }
                });
                later(sl, 60, () -> {
                    if (!v.isAlive()) {
                        return;
                    }
                    Vec3 c = v.position();
                    for (LivingEntity u : KingForms.foes(king, sl, 48)) {
                        if (u.position().distanceTo(c) <= 3.0 && hit(king, "brand", u, 26F, true)) {
                            u.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
                            u.setDeltaMovement(u.getDeltaMovement().add(0, 0.8, 0));
                            u.hurtMarked = true;
                        }
                    }
                    sl.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 1, c.z, 2, 0.3, 0.3, 0.3, 0);
                    sl.sendParticles(CRIMSON, c.x, c.y + 1, c.z, 60, 1.0, 1.0, 1.0, 0.1);
                    sound(sl, c, SoundEvents.DRAGON_FIREBALL_EXPLODE, 2F, 0.8F);
                });
            }
        });
    }

    private static void plague(RoyalMob king, ServerLevel sl) {
        long now = sl.getGameTime();
        for (LivingEntity v : KingForms.foes(king, sl, 16.0)) {
            KingForms.swarm(king, v, now + 160);
            v.removeEffect(MobEffects.REGENERATION);
            v.addEffect(new MobEffectInstance(MobEffects.HUNGER, 160, 2));
            count(king, HITS, "plague");
        }
        sl.sendParticles(ParticleTypes.SQUID_INK, king.getX(), king.getY() + 1, king.getZ(), 200, 8, 1.5, 8, 0.05);
        sound(sl, king.position(), SoundEvents.BEE_LOOP_AGGRESSIVE, 4F, 0.6F);
        sound(sl, king.position(), SoundEvents.WITHER_AMBIENT, 2F, 1.5F);
    }

    // -------------------------------------------------------------------------------------------- the nastier deeds

    static final ResourceLocation SUNDERED = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "king_sundered");
    static final ResourceLocation SUNDERED_T = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "king_sundered_toughness");

    /** Who speaks: the hero, the broken one, Baal Zebul. */
    static String who(RoyalMob king) {
        int ph = king.lifePhase();
        return ph >= 3 ? "バアル＝ゼブル" : ph == 2 ? "崩壊王" : "英雄王";
    }

    static double toSegment(Vec3 p, Vec3 a, Vec3 b) {
        Vec3 ab = b.subtract(a);
        double L2 = ab.lengthSqr();
        double u = L2 < 1.0E-9 ? 0 : Math.max(0, Math.min(1, p.subtract(a).dot(ab) / L2));
        return p.distanceTo(a.add(ab.scale(u)));
    }

    /** 処刑: he takes his foe by the throat, holds it up for a breath and drives it into the ground; a foe under a third
     * of its health is executed outright (a god-slayer's ceiling still holds). */
    private static void execution(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            if (!t.isAlive() || !king.isAlive() || king.distanceTo(t) > 6 + king.getBbWidth()) {
                return;
            }
            sound(sl, t.position(), SoundEvents.IRON_GOLEM_ATTACK, 3F, 0.5F);
            Vec3 fwd = flat(t.position().subtract(king.position()));
            each(sl, 0, 30, 1, k -> {
                if (!t.isAlive() || !king.isAlive()) {
                    return;
                }
                Vec3 grip = king.position().add(fwd.scale(0.9 + king.getBbWidth() * 0.5));
                double y = king.getY() + king.getBbHeight() * (0.5 + 0.4 * Math.min(1.0, k / 8.0));
                t.teleportTo(grip.x, y, grip.z);
                t.setDeltaMovement(Vec3.ZERO);
                t.hurtMarked = true;
                t.fallDistance = 0F;
                if (k % 6 == 0) {
                    t.invulnerableTime = 0;
                    hit(king, "execution", t, 4F, false);
                    sl.sendParticles(CRIMSON, t.getX(), t.getY() + t.getBbHeight() * 0.8, t.getZ(), 10, 0.2, 0.2, 0.2, 0);
                }
            });
            later(sl, 31, () -> {
                if (!t.isAlive() || !king.isAlive()) {
                    return;
                }
                Vec3 at = king.position().add(fwd.scale(1.2 + king.getBbWidth() * 0.5));
                t.teleportTo(at.x, king.getY(), at.z);
                boolean low = t.getHealth() < t.getMaxHealth() * 0.34F;
                t.invulnerableTime = 0;
                hit(king, "execution", t, low ? t.getHealth() * 4F + t.getAbsorptionAmount() + 40F : 36F, low);
                t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 3));
                t.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 100, 0));
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.STONE.defaultBlockState()), at.x, king.getY() + 0.1, at.z,
                    80, 1.2, 0.1, 1.2, 0.2);
                sound(sl, at, SoundEvents.MACE_SMASH_GROUND_HEAVY, 3F, 0.5F);
                if (low) {
                    sound(sl, at, SoundEvents.WITHER_BREAK_BLOCK, 2F, 0.6F);
                    KingCinemaSay.near(sl, king, who(king) + "：――処刑する。", ChatFormatting.DARK_RED);
                }
            });
        });
    }

    /** 破甲: a blow that cracks his foes' armour: a quarter of every piece's life gone at once, its protection halved for
     * ten seconds. */
    private static void sunder(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3 fwd = flat(t.position().subtract(king.position()));
            for (LivingEntity v : KingForms.foes(king, sl, 6.0 + king.getBbWidth() * 0.5)) {
                Vec3 to = flat(v.position().subtract(king.position()));
                if (v != t && to.dot(fwd) < 0.3) {
                    continue;
                }
                if (!hit(king, "sunder", v, 16F, false)) {
                    continue;
                }
                for (EquipmentSlot slot : new EquipmentSlot[]{EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
                    ItemStack a = v.getItemBySlot(slot);
                    if (!a.isEmpty() && a.isDamageableItem()) {
                        a.hurtAndBreak(Math.max(1, a.getMaxDamage() / 4), v, slot);
                    }
                }
                AttributeInstance armor = v.getAttribute(Attributes.ARMOR), tough = v.getAttribute(Attributes.ARMOR_TOUGHNESS);
                if (armor != null) {
                    armor.removeModifier(SUNDERED);
                    armor.addTransientModifier(new AttributeModifier(SUNDERED, -0.5, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
                }
                if (tough != null) {
                    tough.removeModifier(SUNDERED_T);
                    tough.addTransientModifier(new AttributeModifier(SUNDERED_T, -0.5, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
                }
                later(sl, 200, () -> {
                    AttributeInstance a1 = v.getAttribute(Attributes.ARMOR), a2 = v.getAttribute(Attributes.ARMOR_TOUGHNESS);
                    if (a1 != null) {
                        a1.removeModifier(SUNDERED);
                    }
                    if (a2 != null) {
                        a2.removeModifier(SUNDERED_T);
                    }
                });
                throwFrom(v, king.position(), 1.4, 0.3);
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, Blocks.IRON_BLOCK.defaultBlockState()), v.getX(),
                    v.getY() + v.getBbHeight() * 0.6, v.getZ(), 40, 0.4, 0.5, 0.4, 0.15);
                sound(sl, v.position(), SoundEvents.SHIELD_BREAK, 2F, 0.6F);
                sound(sl, v.position(), SoundEvents.ANVIL_DESTROY, 1.5F, 0.8F);
            }
        });
    }

    /** 削除 (the broken one): a sphere of the world round his foe is deleted and everything in it struck by nothing; the
     * blocks come back ten seconds later wherever nothing stands in their place (at once if the server stops). */
    private static void deletion(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        Vec3 c = t.position().add(0, 0.5, 0);
        int R = 4;
        each(sl, 0, Math.max(1, w / 3), 3, k -> {
            for (int i = 0; i < 48; i++) {
                double a = sl.random.nextDouble() * Math.PI * 2, z = sl.random.nextDouble() * 2 - 1, q = Math.sqrt(1 - z * z);
                sl.sendParticles(i % 3 == 0 ? CYAN : i % 2 == 0 ? MAGENTA : BLACK, c.x + q * Math.cos(a) * R, c.y + z * R, c.z + q * Math.sin(a) * R,
                    1, 0, 0, 0, 0);
            }
        });
        sound(sl, c, SoundEvents.BEACON_DEACTIVATE, 3F, 0.5F);
        later(sl, w, () -> {
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                if (v.position().distanceTo(c) <= R + 0.5 && hit(king, "void", v, 28F, true)) {
                    v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 120, 0));
                    v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 120, 1));
                }
            }
            List<BlockPos> gone = new ArrayList<>();
            List<BlockState> was = new ArrayList<>();
            BlockPos o = BlockPos.containing(c);
            for (BlockPos p : BlockPos.betweenClosed(o.offset(-R, -R, -R), o.offset(R, R, R))) {
                if (p.distSqr(o) > R * R + 0.5) {
                    continue;
                }
                BlockState st = sl.getBlockState(p);
                if (st.isAir() || st.hasBlockEntity() || !st.getFluidState().isEmpty() || st.getDestroySpeed(sl, p) < 0) {
                    continue;
                }
                gone.add(p.immutable());
                was.add(st);
                sl.setBlock(p, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
            }
            for (int i = 0; i < 6; i++) {
                glitchAt(sl, c.add(sl.random.nextGaussian() * 2, sl.random.nextGaussian() * 2, sl.random.nextGaussian() * 2));
            }
            sound(sl, c, SoundEvents.GLASS_BREAK, 3F, 0.4F);
            sound(sl, c, SoundEvents.ENDERMAN_TELEPORT, 3F, 0.3F);
            CompoundTag d = king.getPersistentData();
            d.putInt("OrorKingDeleted", d.getInt("OrorKingDeleted") + gone.size());
            Runnable back = new Runnable() {
                @Override
                public void run() {
                    if (!RESTORE.remove(this)) {
                        return;
                    }
                    for (int i = 0; i < gone.size(); i++) {
                        BlockPos p = gone.get(i);
                        if (!sl.getBlockState(p).isAir() || !sl.getEntitiesOfClass(Entity.class, new AABB(p)).isEmpty()) {
                            continue;
                        }
                        sl.setBlock(p, was.get(i), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
                    }
                }
            };
            RESTORE.add(back);
            later(sl, 200, back);
        });
    }

    /** 饗宴 (Baal Zebul): threads of crimson from him to every foe within sixteen blocks for three seconds; each is drained
     * of its life and its food, its regeneration and absorption torn away, and he drinks what he takes. */
    private static void feast(RoyalMob king, ServerLevel sl, int w) {
        sound(sl, king.position(), SoundEvents.WARDEN_HEARTBEAT, 4F, 0.5F);
        KingCinemaSay.near(sl, king, "バアル＝ゼブル：汝らの血と肉、我が饗宴に供えよ。", ChatFormatting.DARK_RED);
        each(sl, w, 6, 10, k -> {
            float drunk = 0F;
            for (LivingEntity v : KingForms.foes(king, sl, 16.0)) {
                line(sl, CRIMSON, v.getEyePosition(), king.getEyePosition(), 0.6);
                v.removeEffect(MobEffects.REGENERATION);
                v.removeEffect(MobEffects.ABSORPTION);
                v.setAbsorptionAmount(0F);
                float before = v.getHealth();
                v.invulnerableTime = 0;
                if (hit(king, "feast", v, 5F, true)) {
                    drunk += Math.max(0F, before - v.getHealth());
                }
                if (v instanceof Player p) {
                    p.causeFoodExhaustion(12F);
                }
            }
            if (drunk > 0F) {
                king.heal(drunk);
                sl.sendParticles(CRIMSON, king.getX(), king.getY() + king.getBbHeight() * 0.6, king.getZ(), 30, 0.6, 0.8, 0.6, 0.05);
            }
            sound(sl, king.position(), SoundEvents.GENERIC_DRINK, 2F, 0.5F);
        });
    }

    /** 審判の日 (Baal Zebul, under a third of his life): the sky goes dark and the heavens open for three seconds of
     * warning; then every foe within forty-eight blocks in his sight is struck by the fire of heaven. Only those hidden
     * from him (behind walls, under the earth) are spared. */
    private static void doomsday(RoyalMob king, ServerLevel sl, int w) {
        KingCinemaSay.near(sl, king, "バアル＝ゼブル：見よ、審判の日は来たれり。――我が目より隠れ得ぬ者に、災いあれ。", ChatFormatting.GOLD);
        for (LivingEntity v : KingForms.foes(king, sl, 48)) {
            v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, w + 40, 0));
        }
        sound(sl, king.position(), SoundEvents.END_PORTAL_SPAWN, 4F, 0.6F);
        each(sl, 0, Math.max(1, w / 4), 4, k -> {
            ring(sl, GOLD, king.position(), 4 + k * 2.5, 0.2, 48);
            sl.sendParticles(ParticleTypes.END_ROD, king.getX(), king.getY() + king.getBbHeight() + 2, king.getZ(), 20, 1, 3, 1, 0.1);
            if (k % 3 == 0) {
                sound(sl, king.position(), SoundEvents.LIGHTNING_BOLT_THUNDER, 3F, 0.5F);
            }
        });
        later(sl, w, () -> {
            for (LivingEntity v : KingForms.foes(king, sl, 48)) {
                if (!king.hasLineOfSight(v)) {
                    sl.sendParticles(WHITE, v.getX(), v.getY() + v.getBbHeight() + 0.5, v.getZ(), 6, 0.3, 0.2, 0.3, 0);
                    continue;
                }
                line(sl, ParticleTypes.END_ROD, v.position().add(0, 30, 0), v.position(), 0.8);
                KingForms.bolt(sl, v.position());
                v.invulnerableTime = 0;
                if (hit(king, "doomsday", v, 60F, true)) {
                    v.igniteForSeconds(10);
                    v.addEffect(new MobEffectInstance(MobEffects.WITHER, 200, 2));
                    v.addEffect(new MobEffectInstance(MobEffects.GLOWING, 400, 0));
                }
            }
            for (int i = 0; i < 8; i++) {
                double a = sl.random.nextDouble() * Math.PI * 2, r = 6 + sl.random.nextDouble() * 14;
                KingForms.bolt(sl, king.position().add(Math.cos(a) * r, 0, Math.sin(a) * r));
            }
            sound(sl, king.position(), SoundEvents.GENERIC_EXPLODE.value(), 4F, 0.5F);
        });
    }

    // -------------------------------------------------------------------------------------------- the twin swords

    /** 乱舞: he is gone and back six times in two seconds, each time from another side, the white blade burning and the
     * black one rotting. */
    private static void flurry(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> each(sl, 0, 6, 4, k -> {
            if (!t.isAlive() || !king.isAlive()) {
                return;
            }
            double a = k * 2.4 + t.getId();
            double r = 1.4 + t.getBbWidth() * 0.5 + king.getBbWidth() * 0.5;
            Vec3 from = king.position();
            Vec3 to = t.position().add(Math.cos(a) * r, 0, Math.sin(a) * r);
            if (sl.noCollision(king, king.getBoundingBox().move(to.subtract(from)))) {
                line(sl, k % 2 == 0 ? WHITE : CRIMSON, from.add(0, 1, 0), to.add(0, 1, 0), 0.6);
                king.teleportTo(to.x, to.y, to.z);
            }
            king.getLookControl().setLookAt(t);
            t.invulnerableTime = 0;
            if (hit(king, "flurry", t, 12F, false)) {
                if (k % 2 == 0) {
                    t.igniteForSeconds(4);
                } else {
                    t.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1));
                }
            }
            sl.sendParticles(ParticleTypes.SWEEP_ATTACK, t.getX(), t.getY() + 1, t.getZ(), 2, 0.3, 0.3, 0.3, 0);
            sl.sendParticles(k % 2 == 0 ? WHITE : CRIMSON, t.getX(), t.getY() + 1, t.getZ(), 12, 0.4, 0.4, 0.4, 0);
            sound(sl, t.position(), SoundEvents.PLAYER_ATTACK_SWEEP, 2F, 1.2F + k * 0.08F);
        }));
    }

    /** 十字斬: two blades of light and rot thrown crossed, the cross on his foe; whatever an arm of the cross passes
     * through is cut, at the crossing twice. */
    private static void crossslash(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3 c = t.position().add(0, t.getBbHeight() * 0.5, 0);
            Vec3 f = flat(c.subtract(king.position()));
            Vec3 side = new Vec3(-f.z, 0, f.x);
            Vec3[] dirs = {f.add(side).normalize(), f.subtract(side).normalize()};
            for (int i = 0; i < 2; i++) {
                Vec3 a = c.subtract(dirs[i].scale(7)), b = c.add(dirs[i].scale(7));
                line(sl, i == 0 ? WHITE : CRIMSON, a, b, 0.3);
                line(sl, i == 0 ? ParticleTypes.END_ROD : ParticleTypes.SQUID_INK, a, b, 0.8);
                for (LivingEntity v : KingForms.foes(king, sl, 48)) {
                    if (toSegment(v.position().add(0, v.getBbHeight() * 0.5, 0), a, b) <= 1.4 + v.getBbWidth() * 0.5) {
                        v.invulnerableTime = 0;
                        if (hit(king, "crossslash", v, 22F, false)) {
                            if (i == 0) {
                                v.igniteForSeconds(5);
                            } else {
                                v.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 2));
                            }
                        }
                    }
                }
            }
            sound(sl, c, SoundEvents.PLAYER_ATTACK_SWEEP, 3F, 0.5F);
            sound(sl, c, SoundEvents.PLAYER_ATTACK_CRIT, 3F, 0.6F);
        });
    }

    // -------------------------------------------------------------------------------------------- the spear

    /** 迅雷突: a lunge of twelve blocks at his foe faster than the eye; all in its way are run through, carried along and
     * pinned (slowed to a stop), and the lightning falls on his foe where he stops. */
    private static void lunge(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3 dir = flat(t.position().subtract(king.position()));
            Set<LivingEntity> struck = new HashSet<>();
            sound(sl, king.position(), SoundEvents.LIGHTNING_BOLT_IMPACT, 2F, 1.6F);
            each(sl, 0, 6, 1, k -> {
                king.getNavigation().stop();
                king.setDeltaMovement(dir.x * 2.2, king.getDeltaMovement().y, dir.z * 2.2);
                king.hurtMarked = true;
                sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, king.getX(), king.getY() + king.getBbHeight() * 0.5, king.getZ(), 14, 0.6, 0.6, 0.6, 0.05);
                for (LivingEntity v : KingForms.foes(king, sl, 2.2 + king.getBbWidth() * 0.5)) {
                    if (struck.add(v) && hit(king, "lunge", v, 26F, false)) {
                        v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 50, 5));
                        v.setDeltaMovement(dir.x * 1.6, 0.2, dir.z * 1.6);
                        v.hurtMarked = true;
                    }
                }
                if (k == 5 && t.isAlive() && t.distanceTo(king) < 8) {
                    KingForms.bolt(sl, t.position());
                }
            });
        });
    }

    /** 雷槍投擲: the spear thrown; it falls on its mark with the lightning, the thunder runs on to three more, and for
     * three seconds the spear stands where it fell in a field of sparks that burns all near it. */
    private static void javelin(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3 start = king.getEyePosition();
            sound(sl, start, SoundEvents.ARROW_SHOOT, 3F, 0.4F);
            each(sl, 0, 8, 1, k -> {
                Vec3 end = t.getEyePosition();
                Vec3 p = start.add(end.subtract(start).scale((k + 1) / 8.0));
                sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 10, 0.2, 0.2, 0.2, 0.05);
                sl.sendParticles(GOLD, p.x, p.y, p.z, 6, 0.15, 0.15, 0.15, 0);
                if (k != 7) {
                    return;
                }
                Vec3 c = t.position();
                KingForms.bolt(sl, c);
                t.invulnerableTime = 0;
                if (hit(king, "javelin", t, 30F, true)) {
                    t.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 3));
                }
                int chained = 0;
                for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                    if (v != t && v.distanceTo(t) <= 10 && chained < 3) {
                        chained++;
                        line(sl, ParticleTypes.ELECTRIC_SPARK, t.getEyePosition(), v.getEyePosition(), 0.4);
                        v.invulnerableTime = 0;
                        hit(king, "javelin", v, 14F, true);
                    }
                }
                sound(sl, c, SoundEvents.LIGHTNING_BOLT_THUNDER, 3F, 1.2F);
                each(sl, 2, 6, 10, j -> {
                    ring(sl, ParticleTypes.ELECTRIC_SPARK, c, 3.0, 0.2, 30);
                    sl.sendParticles(GOLD, c.x, c.y + 1.5, c.z, 8, 0.1, 1.2, 0.1, 0);
                    for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                        if (v.position().distanceTo(c) <= 3.2) {
                            v.invulnerableTime = 0;
                            hit(king, "javelin", v, 5F, true);
                        }
                    }
                });
            });
        });
    }

    // -------------------------------------------------------------------------------------------- the bow

    /** 光の雨: an arrow loosed into the sky comes down as a rain of light for two seconds where his foe stood: shafts on
     * where his foes stand now and all about. */
    private static void rain(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        Vec3 c0 = t.position();
        sound(sl, king.position(), SoundEvents.ARROW_SHOOT, 3F, 0.4F);
        line(sl, ParticleTypes.END_ROD, king.getEyePosition(), king.getEyePosition().add(0, 20, 0), 0.6);
        later(sl, w, () -> each(sl, 0, 20, 2, k -> {
            List<LivingEntity> fs = new ArrayList<>();
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                if (v.position().distanceTo(c0) <= 10) {
                    fs.add(v);
                }
            }
            List<Vec3> spots = new ArrayList<>();
            for (LivingEntity v : fs) {
                if (sl.random.nextFloat() < 0.6F) {
                    spots.add(v.position().add(sl.random.nextGaussian() * 0.9, 0, sl.random.nextGaussian() * 0.9));
                }
            }
            for (int i = 0; i < 4; i++) {
                spots.add(c0.add((sl.random.nextDouble() - 0.5) * 12, 0, (sl.random.nextDouble() - 0.5) * 12));
            }
            for (Vec3 s : spots) {
                line(sl, ParticleTypes.END_ROD, s.add(0, 8, 0), s, 1.0);
                sl.sendParticles(GOLD, s.x, s.y + 0.1, s.z, 4, 0.2, 0.05, 0.2, 0);
                for (LivingEntity v : fs) {
                    double dx = v.getX() - s.x, dz = v.getZ() - s.z;
                    if (Math.sqrt(dx * dx + dz * dz) <= 0.8 + v.getBbWidth() * 0.5 && Math.abs(v.getY() - s.y) < 3) {
                        v.invulnerableTime = 0;
                        hit(king, "rain", v, 4F, true);
                    }
                }
            }
            if (k % 3 == 0) {
                sound(sl, c0, SoundEvents.ARROW_HIT, 2F, 1.3F);
            }
        }));
    }

    /** 三連光矢: three arrows of light loosed at once in a narrow fan; each runs through everything in its line out to
     * forty-eight blocks or the first wall, stopped by no armour. */
    private static void triple(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        later(sl, w, () -> {
            Vec3 a = king.getEyePosition();
            Vec3 aim = t.getEyePosition().subtract(a).normalize();
            sound(sl, a, SoundEvents.ARROW_SHOOT, 3F, 1.4F);
            DustParticleOptions[] tint = {RED, GOLD, CYAN};
            for (int i = -1; i <= 1; i++) {
                double ang = i * Math.toRadians(7);
                Vec3 d = new Vec3(aim.x * Math.cos(ang) - aim.z * Math.sin(ang), aim.y, aim.x * Math.sin(ang) + aim.z * Math.cos(ang)).normalize();
                Vec3 b = sl.clip(new ClipContext(a, a.add(d.scale(48)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, king)).getLocation();
                line(sl, ParticleTypes.END_ROD, a, b, 0.5);
                line(sl, tint[i + 1], a, b, 0.7);
                for (LivingEntity v : KingForms.foes(king, sl, 50)) {
                    if (toSegment(v.getBoundingBox().getCenter(), a, b) <= 0.9 + v.getBbWidth() * 0.5) {
                        v.invulnerableTime = 0;
                        if (hit(king, "triple", v, 16F, true)) {
                            v.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0));
                        }
                    }
                }
            }
        });
    }

    // -------------------------------------------------------------------------------------------- the stances

    static ItemStack named(Item item, String name, ChatFormatting style) {
        ItemStack it = new ItemStack(item);
        it.set(DataComponents.CUSTOM_NAME, Component.literal(name).withStyle(style));
        it.set(DataComponents.RARITY, Rarity.EPIC);
        return it;
    }

    /** Baal Zebul takes up one of his arms: 1 the thunder clubs, 2 the fly lord's scythe, 3 the twin swords, 4 the thunder
     * spear, 5 the rainbow bow (KingRig shows the arm and brings his hands into its hold). */
    public static void switchStance(RoyalMob king, ServerLevel sl, int stance) {
        var ench = king.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        Vec3 c = king.position().add(0, king.getBbHeight() * 0.6, 0);
        String[] names = {"", "clubs", "scythe", "twin", "spear", "bow"};
        stance = Math.max(1, Math.min(5, stance));
        switch (stance) {
            case 2 -> {
                ItemStack scythe = named(Items.NETHERITE_HOE, "魔器・蝿王の大鎌《ベルゼブブ》", ChatFormatting.DARK_RED);
                scythe.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 10);
                scythe.enchant(ench.getHolderOrThrow(Enchantments.SWEEPING_EDGE), 5);
                king.setItemSlot(EquipmentSlot.MAINHAND, scythe);
                king.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
                sl.sendParticles(CRIMSON, c.x, c.y, c.z, 160, 1.2, 1.5, 1.2, 0.1);
                sl.sendParticles(ParticleTypes.SQUID_INK, king.getX(), king.getY() + 1, king.getZ(), 80, 1.5, 1, 1.5, 0.05);
                sound(sl, king.position(), SoundEvents.WITHER_SPAWN, 1.5F, 1.4F);
                KingCinemaSay.near(sl, king, "バアル＝ゼブル：蝿どもよ、我が手に来れ。――魔器、解放。", ChatFormatting.DARK_RED);
            }
            case 3 -> {
                ItemStack seraph = named(Items.NETHERITE_SWORD, "熾天の剣《セラフ》", ChatFormatting.GOLD);
                seraph.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 8);
                seraph.enchant(ench.getHolderOrThrow(Enchantments.FIRE_ASPECT), 2);
                ItemStack fly = named(Items.NETHERITE_SWORD, "蝿王の剣《ベルゼブブ》", ChatFormatting.DARK_RED);
                fly.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 8);
                king.setItemSlot(EquipmentSlot.MAINHAND, seraph);
                king.setItemSlot(EquipmentSlot.OFFHAND, fly);
                sl.sendParticles(WHITE, c.x, c.y, c.z, 100, 1.2, 1.5, 1.2, 0.1);
                sl.sendParticles(CRIMSON, c.x, c.y, c.z, 100, 1.2, 1.5, 1.2, 0.1);
                sound(sl, king.position(), SoundEvents.ANVIL_USE, 2F, 1.6F);
                KingCinemaSay.near(sl, king, "バアル＝ゼブル：光と蝿、ふたつの刃にて汝を刻まん。――双剣、解放。", ChatFormatting.LIGHT_PURPLE);
            }
            case 4 -> {
                ItemStack spear = named(Items.TRIDENT, "雷槍《バアルの稲妻》", ChatFormatting.YELLOW);
                spear.enchant(ench.getHolderOrThrow(Enchantments.IMPALING), 5);
                spear.enchant(ench.getHolderOrThrow(Enchantments.CHANNELING), 1);
                king.setItemSlot(EquipmentSlot.MAINHAND, spear);
                king.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
                sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, c.x, c.y, c.z, 160, 1.2, 1.5, 1.2, 0.2);
                sound(sl, king.position(), SoundEvents.LIGHTNING_BOLT_THUNDER, 2F, 1.4F);
                KingCinemaSay.near(sl, king, "バアル＝ゼブル：天の雷を、ひと振りの槍に。――雷槍、解放。", ChatFormatting.YELLOW);
            }
            case 5 -> {
                ItemStack bow = named(Items.BOW, "虹の大弓《契約の虹》", ChatFormatting.AQUA);
                bow.enchant(ench.getHolderOrThrow(Enchantments.POWER), 10);
                bow.enchant(ench.getHolderOrThrow(Enchantments.FLAME), 1);
                king.setItemSlot(EquipmentSlot.MAINHAND, bow);
                king.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
                for (DustParticleOptions o : new DustParticleOptions[]{RED, GOLD, CYAN, WHITE}) {
                    sl.sendParticles(o, c.x, c.y, c.z, 40, 1.2, 1.5, 1.2, 0.05);
                }
                sound(sl, king.position(), SoundEvents.AMETHYST_BLOCK_CHIME, 3F, 0.8F);
                // Genesis 9:13: I do set my bow in the cloud
                KingCinemaSay.near(sl, king, "バアル＝ゼブル：雲間に掛けし我が弓よ。――虹弓、解放。", ChatFormatting.AQUA);
            }
            default -> {
                KingForms.arm(king, 3);
                sl.sendParticles(ParticleTypes.END_ROD, c.x, c.y, c.z, 160, 1.2, 1.5, 1.2, 0.2);
                sl.sendParticles(GOLD, c.x, c.y, c.z, 120, 1.2, 1.5, 1.2, 0.05);
                sound(sl, king.position(), SoundEvents.BEACON_ACTIVATE, 3F, 1.3F);
                KingCinemaSay.near(sl, king, "バアル＝ゼブル：雷霆よ、我が手に還れ。――神器、解放。", ChatFormatting.GOLD);
            }
        }
        king.setDropChance(EquipmentSlot.MAINHAND, 0F);
        king.setDropChance(EquipmentSlot.OFFHAND, 0F);
        LivingEntity t = king.getTarget();
        TechniqueShow.send(king, "move:king_stance", 0, 10, 24, t == null ? -1 : t.getId());
        count(king, COUNT, "stance_" + names[stance]);
    }

    // -------------------------------------------------------------------------------------------- broken hits

    /**
     * The broken king's blows are broken: a third pass through with no hit; a quarter land a moment late, or on
     * someone else near. A third of the blows on him go through him (MISS). Baal Zebul turns aside one blow in eight
     * by his majesty. The rebel lord's blade and the void are never turned aside.
     */
    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void brokenHits(LivingIncomingDamageEvent e) {
        if (!(e.getEntity().level() instanceof ServerLevel sl)) {
            return;
        }
        // his blows
        if (e.getSource().getEntity() instanceof RoyalMob king && KingCourt.isKing(king) && king.lifePhase() == 2
            && e.getSource().getDirectEntity() == king && !KingCinema.playing(king)) {
            LivingEntity v = e.getEntity();
            int roll = sl.random.nextInt(12);
            if (roll < 4) {
                e.setCanceled(true);
                glitchAt(sl, v.position().add(0, 1, 0));
                count(king, COUNT, "miss_out");
            } else if (roll < 7) {
                e.setCanceled(true);
                float amount = e.getAmount() * 1.5F;
                Vec3 was = v.position();
                later(sl, 10 + sl.random.nextInt(16), () -> {
                    LivingEntity to = v;
                    if (!v.isAlive() || v.position().distanceTo(was) > 4) {
                        List<LivingEntity> fs = KingForms.foes(king, sl, 10.0);
                        if (fs.isEmpty()) {
                            return;
                        }
                        to = fs.get(sl.random.nextInt(fs.size()));
                    }
                    glitchAt(sl, to.position().add(0, 1, 0));
                    hit(king, "lag_hit", to, amount, false);
                });
            }
            return;
        }
        // blows on him
        if (e.getEntity() instanceof RoyalMob king && KingCourt.isKing(king) && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)
            && !RebelLord.slayer(e.getSource().getEntity())) {
            int phase = king.lifePhase();
            if (phase == 2 && sl.random.nextInt(3) == 0) {
                e.setCanceled(true);
                glitchAt(sl, king.position().add(0, king.getBbHeight() * 0.5, 0));
                if (e.getSource().getEntity() instanceof Player p) {
                    p.displayClientMessage(Component.literal("MISS").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD), true);
                }
                count(king, COUNT, "miss_in");
            } else if (phase >= 3 && sl.random.nextInt(8) == 0 && !GodSlayer.has(e.getSource().getEntity())) {
                e.setCanceled(true);
                sl.sendParticles(GOLD, king.getX(), king.getY() + king.getBbHeight() * 0.5, king.getZ(), 30, 0.8, 1.0, 0.8, 0.1);
                sound(sl, king.position(), SoundEvents.SHIELD_BLOCK, 2F, 0.6F);
                count(king, COUNT, "majesty");
            }
        }
    }

    /** A line said to those near (shared with the stances). */
    static final class KingCinemaSay {
        private KingCinemaSay() {
        }

        static void near(ServerLevel sl, LivingEntity at, String line, ChatFormatting style) {
            for (ServerPlayer p : sl.players()) {
                if (p.distanceToSqr(at) < 128 * 128) {
                    p.sendSystemMessage(Component.literal(line).withStyle(style));
                }
            }
        }
    }
}
