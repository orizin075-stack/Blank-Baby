package jp.oror.reborn.king;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.Vec3;

/**
 * (054) The villager king's arsenal: ten motions for each of his weapons (the user: about eighty motions and techniques,
 * ten for each weapon), seventy in all, each with its own windup and strike pose (KingRig), its own reach and shape of
 * blow, its own effects. The hero fights as a true knight of the sword and the shield; the broken one's blows are a box
 * of tricks (struck from somewhere else, a second later, by an echo, or not at all); Baal Zebul's five arms each fight
 * their own way. His great deeds (KingDeeds) come between them.
 * <p>
 * A move is data: its shape (an arc before him, a line, a spin, a slam, a leap, a dash, a travelling wave, a run of
 * strikes, shots, a fan of shots, a lobbed shot, a thrown weapon that comes back, a pull, a strike from behind, a
 * backstep and a shot, a cross on the foe, spikes erupting in a line, a thrust that throws the foe into the sky, a ring
 * running out from him, a chain of lightning), its two sizes, its damage and its effects.
 */
public final class KingArsenal {
    public static final int SWORD = 0, BROKEN = 1, CLUBS = 2, SCYTHE = 3, TWIN = 4, SPEAR = 5, BOW = 6;
    public static final String[] WEAPON_NAMES = {"聖剣《黎明》と塔盾", "壊れた聖剣とエラーの腕", "雷霆棍ヤグルシとアイムール", "蝿王の大鎌", "双剣セラフとベルゼブブ", "雷槍", "虹の大弓"};

    public enum Shape { ARC, LINE, SPIN, SLAM, LEAP, DASH, WAVE, MULTI, SHOT, FAN, LOB, THROW, PULL, BEHIND, BACKSTEP, CROSS, ERUPT, UPTHRUST, RING, CHAIN }

    static final int FIRE = 1, WITHER = 2, SLOW = 4, LAUNCH = 8, KNOCK = 16, MAGIC = 32, STUN = 64, LIGHTNING = 128, POISON = 256, PIN = 512,
        SOUL = 1024, RAINBOW = 2048, DRAIN = 4096, LAG = 8192, OFFSET = 16384, ECHO = 32768, EXECUTE = 65536, STRIP = 131072, BLIND = 262144,
        BACK = 524288, MISSY = 1048576;

    /** One motion: its weapon, name, pose style and side (1 right-handed, -1 mirrored), windup, length and how often (ticks),
     * its range, its shape and sizes, its damage (before his offense), effects and count. */
    public record Move(String id, int weapon, String name, String style, int side, int windup, int length, int every, double min, double max,
                       Shape shape, double a, double b, float dmg, int fx, int count) {
    }

    private static Move m(String id, int weapon, String name, String style, int side, int windup, int length, int every, double min, double max,
                          Shape shape, double a, double b, float dmg, int fx, int count) {
        return new Move(id, weapon, name, style, side, windup, length, every, min, max, shape, a, b, dmg, fx, count);
    }

    public static final List<Move> MOVES = List.of(
        // ---- the hero: a true knight of the sword and the shield
        m("sword_sweep", SWORD, "横薙ぎ", "slash_h", 1, 8, 16, 40, 0, 6, Shape.ARC, 5.5, 60, 16, KNOCK, 1),
        m("sword_return", SWORD, "返し斬り", "slash_h", -1, 6, 14, 40, 0, 6, Shape.ARC, 5.5, 60, 16, 0, 1),
        m("sword_cleave", SWORD, "袈裟斬り", "slash_d", 1, 10, 18, 60, 0, 6, Shape.ARC, 6, 35, 22, STUN, 1),
        m("sword_rising", SWORD, "斬り上げ", "slash_up", 1, 8, 16, 60, 0, 5, Shape.ARC, 5, 35, 16, LAUNCH, 1),
        m("sword_thrust", SWORD, "刺突", "thrust", 1, 10, 16, 60, 2, 8, Shape.LINE, 8, 1.3, 22, MAGIC, 1),
        m("sword_bash", SWORD, "盾打ち", "bash", 1, 6, 14, 80, 0, 4, Shape.ARC, 4, 50, 12, STUN | KNOCK, 1),
        m("sword_spin", SWORD, "回転斬り", "spin", 1, 12, 20, 100, 0, 6, Shape.SPIN, 6, 180, 18, KNOCK, 1),
        m("sword_leap", SWORD, "跳躍斬り", "leap", 1, 12, 30, 120, 6, 18, Shape.LEAP, 4, 0, 26, STUN, 1),
        m("sword_dash", SWORD, "突進斬り", "dash", 1, 10, 22, 100, 5, 14, Shape.DASH, 10, 2.2, 20, KNOCK, 1),
        m("sword_wave", SWORD, "聖光剣波", "slash_d", 1, 14, 22, 120, 4, 20, Shape.WAVE, 16, 1.8, 18, FIRE, 1),
        // ---- the broken one: a box of tricks
        m("broken_shard", BROKEN, "断片斬り", "glitch", 1, 6, 14, 40, 0, 7, Shape.ARC, 6, 70, 14, OFFSET | MISSY, 1),
        m("broken_lag", BROKEN, "ラグ斬り", "slash_h", 1, 8, 16, 60, 0, 6, Shape.ARC, 5.5, 60, 12, LAG, 1),
        m("broken_blink", BROKEN, "座標飛び突き", "thrust", 1, 6, 18, 80, 2, 16, Shape.BEHIND, 5, 30, 18, MAGIC | ECHO, 1),
        m("broken_multi", BROKEN, "多重斬り", "glitch", -1, 6, 36, 80, 0, 6, Shape.MULTI, 5.5, 70, 8, MISSY | OFFSET, 5),
        m("broken_rewind", BROKEN, "逆再生", "cast", 1, 10, 22, 120, 0, 16, Shape.PULL, 16, 0, 14, ECHO, 1),
        m("broken_blocks", BROKEN, "欠損ブロック投げ", "throw", 1, 10, 36, 100, 4, 24, Shape.LOB, 3, 0, 16, OFFSET, 3),
        m("broken_grab", BROKEN, "エラー腕の掴み", "bash", -1, 8, 24, 100, 0, 8, Shape.PULL, 8, 0, 20, STUN | LAG, 1),
        m("broken_echo", BROKEN, "分身斬り", "glitch", 1, 8, 24, 120, 0, 10, Shape.CROSS, 7, 1.5, 14, ECHO, 1),
        m("broken_hitbox", BROKEN, "当たり判定膨張", "spin", 1, 10, 20, 120, 0, 9, Shape.SPIN, 9, 180, 16, MISSY | KNOCK, 1),
        m("broken_nan", BROKEN, "NaN落下", "cast", -1, 8, 20, 160, 0, 12, Shape.UPTHRUST, 12, 0, 12, LAUNCH | OFFSET, 1),
        // ---- the thunder clubs
        m("clubs_smite", CLUBS, "雷槌振り", "slash_d", 1, 8, 16, 40, 0, 6, Shape.ARC, 6, 40, 18, LIGHTNING, 1),
        m("clubs_flurry", CLUBS, "双棍連打", "double", 1, 6, 30, 80, 0, 5, Shape.MULTI, 5, 60, 10, KNOCK, 4),
        m("clubs_rise", CLUBS, "振り上げ", "slash_up", -1, 8, 16, 60, 0, 5, Shape.ARC, 5, 45, 16, LAUNCH, 1),
        m("clubs_quake", CLUBS, "大地叩き", "slam", 1, 12, 22, 100, 0, 7, Shape.SLAM, 5, 5, 26, STUN, 1),
        m("clubs_spin", CLUBS, "雷鳴の回転", "spin", 1, 10, 22, 100, 0, 6, Shape.SPIN, 6.5, 180, 18, LIGHTNING, 1),
        m("clubs_throw", CLUBS, "投擲雷霆", "throw", 1, 10, 30, 120, 6, 24, Shape.THROW, 24, 1.6, 20, LIGHTNING, 1),
        m("clubs_cross", CLUBS, "交差打ち", "cross", 1, 8, 18, 80, 0, 5, Shape.ARC, 5, 50, 22, KNOCK, 1),
        m("clubs_leap", CLUBS, "跳び叩き", "leap", 1, 12, 30, 120, 6, 20, Shape.LEAP, 5, 0, 30, LIGHTNING | STUN, 1),
        m("clubs_chain", CLUBS, "連鎖雷", "cast", -1, 10, 20, 120, 0, 24, Shape.CHAIN, 24, 0, 14, LIGHTNING, 5),
        m("clubs_shock", CLUBS, "雷の衝撃波", "slam", -1, 12, 24, 120, 0, 12, Shape.RING, 12, 0, 16, LIGHTNING | KNOCK, 1),
        // ---- the fly lord's scythe
        m("scythe_reap", SCYTHE, "刈り払い", "slash_h", 1, 10, 18, 40, 0, 8, Shape.ARC, 8, 75, 18, WITHER, 1),
        m("scythe_return", SCYTHE, "逆刈り", "slash_h", -1, 8, 16, 40, 0, 8, Shape.ARC, 8, 75, 18, WITHER, 1),
        m("scythe_neck", SCYTHE, "首刈り", "slash_d", 1, 12, 20, 100, 0, 7, Shape.ARC, 7, 25, 24, EXECUTE, 1),
        m("scythe_hook", SCYTHE, "引き寄せ刈り", "hook", 1, 10, 24, 100, 4, 12, Shape.PULL, 12, 0, 20, WITHER, 1),
        m("scythe_spin", SCYTHE, "大回転刈り", "spin", 1, 12, 24, 100, 0, 8, Shape.SPIN, 8.5, 180, 20, WITHER | DRAIN, 1),
        m("scythe_throw", SCYTHE, "鎌投げ", "throw", 1, 12, 32, 140, 5, 22, Shape.THROW, 20, 2.4, 22, WITHER, 1),
        m("scythe_wave", SCYTHE, "蝿の斬撃波", "slash_h", -1, 12, 22, 120, 4, 22, Shape.WAVE, 20, 3.0, 16, POISON | BLIND, 1),
        m("scythe_soul", SCYTHE, "魂刈り", "slash_up", 1, 10, 18, 100, 0, 7, Shape.ARC, 7, 40, 18, STRIP | SOUL, 1),
        m("scythe_low", SCYTHE, "地這い刈り", "sweep_low", 1, 8, 16, 80, 0, 8, Shape.ARC, 8, 70, 14, SLOW | PIN, 1),
        m("scythe_leap", SCYTHE, "死神の跳躍", "leap", 1, 14, 32, 140, 6, 22, Shape.LEAP, 6, 0, 28, WITHER | DRAIN, 1),
        // ---- the twin swords
        m("twin_double", TWIN, "二連斬", "slash_h", 1, 5, 20, 40, 0, 5, Shape.MULTI, 5, 60, 12, FIRE, 2),
        m("twin_cross", TWIN, "交差斬", "cross", 1, 7, 16, 60, 0, 5, Shape.ARC, 5, 45, 20, WITHER, 1),
        m("twin_stabs", TWIN, "四連突き", "thrust", 1, 6, 30, 80, 0, 6, Shape.MULTI, 6, 12, 9, MAGIC, 4),
        m("twin_whirl", TWIN, "旋風", "spin", 1, 8, 22, 80, 0, 5.5, Shape.MULTI, 5.5, 180, 10, FIRE | WITHER, 2),
        m("twin_leap", TWIN, "跳び交差", "leap", 1, 10, 26, 120, 5, 16, Shape.LEAP, 4, 0, 24, FIRE | WITHER, 1),
        m("twin_slide", TWIN, "滑り斬り", "dash", 1, 8, 18, 80, 4, 12, Shape.DASH, 9, 2.0, 16, FIRE, 1),
        m("twin_rise", TWIN, "逆手斬り上げ", "slash_up", -1, 6, 14, 60, 0, 5, Shape.ARC, 5, 40, 16, LAUNCH, 1),
        m("twin_xwave", TWIN, "光蝿交差波", "cross", 1, 12, 22, 120, 5, 20, Shape.CROSS, 10, 1.4, 18, FIRE | WITHER, 1),
        m("twin_behind", TWIN, "回り込み", "dash", 1, 6, 18, 100, 0, 10, Shape.BEHIND, 5, 50, 18, WITHER, 1),
        m("twin_hundred", TWIN, "百裂", "double", 1, 8, 62, 160, 0, 5, Shape.MULTI, 5, 60, 4, MAGIC, 10),
        // ---- the thunder spear
        m("spear_thrust", SPEAR, "突き", "thrust", 1, 8, 14, 30, 2, 9, Shape.LINE, 9, 1.2, 20, MAGIC, 1),
        m("spear_double", SPEAR, "二段突き", "thrust", 1, 6, 20, 60, 2, 9, Shape.MULTI, 9, 12, 14, MAGIC, 2),
        m("spear_sweep", SPEAR, "薙ぎ払い", "slash_h", 1, 10, 18, 60, 0, 8, Shape.ARC, 8, 70, 16, KNOCK, 1),
        m("spear_butt", SPEAR, "石突き打ち", "butt", 1, 6, 14, 80, 0, 4, Shape.ARC, 4, 60, 12, STUN | BACK, 1),
        m("spear_twirl", SPEAR, "回転槍", "twirl", 1, 10, 22, 100, 0, 7, Shape.SPIN, 7, 180, 16, LIGHTNING, 1),
        m("spear_dive", SPEAR, "跳躍突き", "leap", 1, 12, 30, 120, 6, 20, Shape.LEAP, 3.5, 0, 30, MAGIC | PIN, 1),
        m("spear_rush", SPEAR, "雷槍突進", "dash", 1, 10, 22, 100, 6, 16, Shape.DASH, 12, 1.8, 22, LIGHTNING, 1),
        m("spear_throw", SPEAR, "投げ槍", "throw", 1, 12, 26, 120, 8, 30, Shape.SHOT, 30, 0, 24, LIGHTNING, 1),
        m("spear_bristle", SPEAR, "槍衾", "cast", 1, 12, 26, 140, 0, 16, Shape.ERUPT, 16, 1.6, 18, PIN, 1),
        m("spear_heaven", SPEAR, "天突き", "thrust_up", 1, 10, 22, 120, 0, 8, Shape.UPTHRUST, 8, 0, 18, LAUNCH | LIGHTNING, 1),
        // ---- the rainbow bow
        m("bow_quick", BOW, "速射", "draw", 1, 8, 14, 30, 4, 40, Shape.SHOT, 40, 0, 18, MAGIC, 1),
        m("bow_double", BOW, "二連射", "draw", 1, 8, 22, 60, 4, 40, Shape.SHOT, 40, 0, 14, MAGIC, 2),
        m("bow_fan", BOW, "拡散射", "draw", 1, 10, 18, 80, 3, 30, Shape.FAN, 30, 40, 12, 0, 5),
        m("bow_lob", BOW, "曲射", "lob", 1, 10, 30, 80, 8, 40, Shape.LOB, 3, 0, 18, FIRE, 1),
        m("bow_pierce", BOW, "貫通射", "draw", 1, 14, 20, 100, 6, 48, Shape.LINE, 48, 1.0, 22, MAGIC, 1),
        m("bow_retreat", BOW, "後退射", "backstep", 1, 4, 22, 100, 0, 6, Shape.BACKSTEP, 6, 0, 18, MAGIC, 1),
        m("bow_rainbow", BOW, "虹の矢", "draw", 1, 10, 18, 100, 4, 40, Shape.SHOT, 40, 0, 16, RAINBOW, 1),
        m("bow_pin", BOW, "足止め矢", "draw", -1, 8, 16, 100, 4, 36, Shape.SHOT, 36, 0, 10, PIN, 1),
        m("bow_burst", BOW, "爆裂矢", "draw", 1, 12, 22, 120, 6, 40, Shape.LOB, 4, 0, 22, KNOCK | FIRE, 1),
        m("bow_strike", BOW, "弓打ち", "bash", 1, 6, 14, 60, 0, 4, Shape.ARC, 4, 60, 12, KNOCK, 1));

    private KingArsenal() {
    }

    /** The weapon in his hands: the hero's sword, the broken sword, or Baal Zebul's arm of the stance. */
    public static int weapon(RoyalMob king, int phase) {
        if (phase <= 1) {
            return SWORD;
        }
        if (phase == 2) {
            return BROKEN;
        }
        return CLUBS + KingDeeds.stance(king) - 1;
    }

    public static Move move(String id) {
        for (Move m : MOVES) {
            if (m.id.equals(id)) {
                return m;
            }
        }
        return null;
    }

    /** One of the weapon's motions that fits the distance and is ready; null if none. */
    public static Move pick(RoyalMob king, int weapon, double dist, long now, RandomSource rnd) {
        CompoundTag d = king.getPersistentData();
        List<Move> ok = new ArrayList<>();
        for (Move m : MOVES) {
            if (m.weapon == weapon && dist >= m.min && dist <= m.max && now >= d.getLong("OrorKingMove_" + m.id)) {
                ok.add(m);
            }
        }
        if (ok.isEmpty()) {
            return null;
        }
        Move m = ok.get(rnd.nextInt(ok.size()));
        d.putLong("OrorKingMove_" + m.id, now + m.every);
        return m;
    }

    /** Does the motion on his foe now: its pose shown, its blow after the windup. */
    public static void perform(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        if (m == null || t == null) {
            return;
        }
        king.getPersistentData().putLong(KingDeeds.BUSY, sl.getGameTime() + m.length);
        KingDeeds.count(king, KingDeeds.COUNT, m.id);
        TechniqueShow.send(king, "move:king_" + m.id, 0, m.windup, m.length, t.getId());
        king.getLookControl().setLookAt(t, 60F, 60F);
        windupSigns(king, sl, m);
        KingDeeds.later(sl, m.windup, () -> strike(king, sl, m, t, false));
    }

    // ------------------------------------------------------------------------------------------------ the blows

    private static final ParticleOptions[][] TINT = {
        {KingDeeds.GOLD, ParticleTypes.END_ROD}, {KingDeeds.MAGENTA, KingDeeds.CYAN}, {ParticleTypes.ELECTRIC_SPARK, KingDeeds.GOLD},
        {KingDeeds.CRIMSON, ParticleTypes.SOUL_FIRE_FLAME}, {KingDeeds.WHITE, KingDeeds.CRIMSON}, {ParticleTypes.ELECTRIC_SPARK, KingDeeds.WHITE},
        {KingDeeds.RED, KingDeeds.CYAN}};

    private static ParticleOptions tint(Move m, int i) {
        return TINT[m.weapon][i & 1];
    }

    private static SoundEvent swing(Move m) {
        return switch (m.weapon) {
            case BOW -> SoundEvents.ARROW_SHOOT;
            case BROKEN -> SoundEvents.GLASS_BREAK;
            case CLUBS -> SoundEvents.LIGHTNING_BOLT_IMPACT;
            default -> SoundEvents.PLAYER_ATTACK_SWEEP;
        };
    }

    private static void windupSigns(RoyalMob king, ServerLevel sl, Move m) {
        Vec3 c = king.position().add(0, king.getBbHeight() * 0.6, 0);
        sl.sendParticles(tint(m, 0), c.x, c.y, c.z, 12, 0.5, 0.6, 0.5, 0.02);
        if (m.weapon == BROKEN) {
            sl.sendParticles(KingDeeds.BLACK, c.x, c.y, c.z, 10, 0.8, 0.8, 0.8, 0);
        }
    }

    /** The blow itself; an echo is the same blow again from a ghost a moment later (the broken one). */
    static void strike(RoyalMob king, ServerLevel sl, Move m, LivingEntity t, boolean echo) {
        if (!king.isAlive() || !t.isAlive()) {
            return;
        }
        Vec3 from = king.position();
        Vec3 fwd = KingDeeds.flat(t.position().subtract(from));
        if ((m.fx & BACK) != 0) {
            fwd = fwd.scale(-1);
        }
        if ((m.fx & OFFSET) != 0) {
            // the blow comes from somewhere else
            RandomSource r = sl.random;
            from = from.add((r.nextDouble() - 0.5) * 6, 0, (r.nextDouble() - 0.5) * 6);
            KingDeeds.glitchAt(sl, from.add(0, 1, 0));
        }
        KingDeeds.sound(sl, king.position(), swing(m), 2F, m.weapon == BROKEN ? 0.4F + sl.random.nextFloat() : 0.7F);
        double reach = king.getBbWidth() * 0.5;
        switch (m.shape) {
            case ARC -> arc(king, sl, m, from, fwd, m.a + reach, m.b, 1F);
            case SPIN -> arc(king, sl, m, from, fwd, m.a + reach, 180, 1F);
            case LINE -> line(king, sl, m, king.getEyePosition().add(0, -0.4, 0), aim(king, t), m.a + reach, m.b, 1F);
            case SLAM -> {
                Vec3 at = from.add(fwd.scale(Math.min(m.a, from.distanceTo(t.position()))));
                circle(king, sl, m, at, m.b, 1F);
                KingDeeds.sound(sl, at, SoundEvents.MACE_SMASH_GROUND_HEAVY, 3F, 0.6F);
            }
            case LEAP -> leap(king, sl, m, t);
            case DASH -> dash(king, sl, m, fwd);
            case WAVE -> wave(king, sl, m, from, fwd);
            case MULTI -> {
                Vec3 f0 = fwd;
                Vec3 o0 = from;
                KingDeeds.each(sl, 0, m.count, 5, k -> {
                    if (!king.isAlive()) {
                        return;
                    }
                    Vec3 o = (m.fx & OFFSET) != 0 ? o0 : king.position();
                    Vec3 f = t.isAlive() ? KingDeeds.flat(t.position().subtract(king.position())) : f0;
                    if (m.b <= 15) {
                        line(king, sl, m, king.getEyePosition().add(0, -0.4, 0), aim(king, t), m.a + reach, 1.2, 1F);
                    } else {
                        arc(king, sl, m, o, rotate(f, (k % 2 == 0 ? -1 : 1) * 0.3), m.a + reach, m.b, 1F);
                    }
                    KingDeeds.sound(sl, king.position(), swing(m), 1.5F, 0.9F + k * 0.07F);
                });
            }
            case SHOT -> KingDeeds.each(sl, 0, m.count, 6, k -> {
                if (king.isAlive() && t.isAlive()) {
                    ray(king, sl, m, aim(king, t), m.a);
                    KingDeeds.sound(sl, king.position(), SoundEvents.ARROW_SHOOT, 2F, 1.2F + k * 0.1F);
                }
            });
            case FAN -> {
                Vec3 aim = aim(king, t);
                for (int i = 0; i < m.count; i++) {
                    double ang = Math.toRadians(-m.b / 2 + m.b * i / Math.max(1, m.count - 1));
                    ray(king, sl, m, rotate(aim, ang), m.a);
                }
            }
            case LOB -> KingDeeds.each(sl, 0, m.count, 8, k -> lob(king, sl, m, t, k));
            case THROW -> thrown(king, sl, m, t);
            case PULL -> pull(king, sl, m, t);
            case BEHIND -> behind(king, sl, m, t);
            case BACKSTEP -> {
                Vec3 away = fwd.scale(-1);
                king.setDeltaMovement(away.x * 1.4, 0.45, away.z * 1.4);
                king.hurtMarked = true;
                sl.sendParticles(ParticleTypes.CLOUD, king.getX(), king.getY() + 0.2, king.getZ(), 10, 0.4, 0.1, 0.4, 0.02);
                KingDeeds.later(sl, 8, () -> {
                    if (king.isAlive() && t.isAlive()) {
                        ray(king, sl, m, aim(king, t), 40);
                    }
                });
            }
            case CROSS -> cross(king, sl, m, t);
            case ERUPT -> erupt(king, sl, m, from, fwd);
            case UPTHRUST -> upthrust(king, sl, m, t);
            case RING -> ring(king, sl, m);
            case CHAIN -> chain(king, sl, m, t);
        }
        if ((m.fx & ECHO) != 0 && !echo) {
            // a ghost of him does it again a moment later, from the other side
            KingDeeds.later(sl, 12, () -> {
                if (king.isAlive() && t.isAlive()) {
                    Vec3 g = t.position().add(t.position().subtract(king.position()).normalize().scale(2.5));
                    KingDeeds.glitchAt(sl, g.add(0, 1, 0));
                    for (int i = 0; i < 3; i++) {
                        sl.sendParticles(KingDeeds.MAGENTA, g.x, g.y + 0.5 + i * 0.6, g.z, 6, 0.3, 0.2, 0.3, 0);
                    }
                    land(king, sl, m, t, 0.7F);
                    KingDeeds.count(king, KingDeeds.COUNT, "echo");
                }
            });
        }
    }

    private static Vec3 aim(RoyalMob king, LivingEntity t) {
        Vec3 d = t.getBoundingBox().getCenter().subtract(king.getEyePosition().add(0, -0.4, 0));
        return d.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : d.normalize();
    }

    private static Vec3 rotate(Vec3 v, double ang) {
        double c = Math.cos(ang), s = Math.sin(ang);
        return new Vec3(v.x * c - v.z * s, v.y, v.x * s + v.z * c);
    }

    // ------------------------------------------------------------------------------------------------ landing

    /** Lands one blow of the move on one foe, with its effects; the broken one's may miss or come again later. */
    static boolean land(RoyalMob king, ServerLevel sl, Move m, LivingEntity v, float scale) {
        if (!v.isAlive()) {
            return false;
        }
        if ((m.fx & MISSY) != 0 && sl.random.nextInt(10) < 3) {
            // the blow goes through: nothing
            sl.sendParticles(KingDeeds.CYAN, v.getX(), v.getY() + v.getBbHeight() + 0.3, v.getZ(), 8, 0.3, 0.1, 0.3, 0);
            KingDeeds.count(king, KingDeeds.COUNT, "move_miss");
            return false;
        }
        float before = v.getHealth();
        v.invulnerableTime = 0;
        boolean magic = (m.fx & (MAGIC | SOUL)) != 0;
        if (!KingDeeds.hit(king, m.id, v, m.dmg * scale, magic)) {
            return false;
        }
        int fx = m.fx;
        if ((fx & FIRE) != 0) {
            v.igniteForSeconds(4);
        }
        if ((fx & WITHER) != 0) {
            v.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1));
        }
        if ((fx & SLOW) != 0) {
            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2));
        }
        if ((fx & PIN) != 0) {
            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 9));
            v.addEffect(new MobEffectInstance(MobEffects.JUMP, 40, 128));
        }
        if ((fx & STUN) != 0) {
            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 5));
            v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 1));
            v.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 60, 0));
        }
        if ((fx & POISON) != 0) {
            v.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1));
        }
        if ((fx & BLIND) != 0) {
            v.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 50, 0));
        }
        if ((fx & LAUNCH) != 0) {
            v.setDeltaMovement(v.getDeltaMovement().add(0, 1.0, 0));
            v.hurtMarked = true;
        }
        if ((fx & KNOCK) != 0) {
            KingDeeds.throwFrom(v, king.position(), 1.3, 0.35);
        }
        if ((fx & LIGHTNING) != 0) {
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, v.getX(), v.getY() + v.getBbHeight() * 0.5, v.getZ(), 20, 0.4, 0.6, 0.4, 0.1);
            if (sl.random.nextInt(4) == 0) {
                KingForms.bolt(sl, v.position());
            }
        }
        if ((fx & EXECUTE) != 0 && v.isAlive() && v.getHealth() < v.getMaxHealth() * 0.3F) {
            v.invulnerableTime = 0;
            KingDeeds.hit(king, m.id, v, v.getHealth() * 4F + 20F, true);
        }
        if ((fx & STRIP) != 0) {
            for (MobEffectInstance e : List.copyOf(v.getActiveEffects())) {
                if (e.getEffect().value().isBeneficial()) {
                    v.removeEffect(e.getEffect());
                    king.addEffect(new MobEffectInstance(e.getEffect(), Math.min(600, e.getDuration()), e.getAmplifier()));
                }
            }
        }
        if ((fx & SOUL) != 0) {
            KingSouls.feed(king, v, 40);
        }
        if ((fx & RAINBOW) != 0) {
            var all = List.of(MobEffects.POISON, MobEffects.WITHER, MobEffects.MOVEMENT_SLOWDOWN, MobEffects.WEAKNESS, MobEffects.BLINDNESS,
                MobEffects.LEVITATION, MobEffects.CONFUSION);
            v.addEffect(new MobEffectInstance(all.get(sl.random.nextInt(all.size())), 100, 1));
        }
        if ((fx & DRAIN) != 0) {
            king.heal(Math.max(0F, before - v.getHealth()) * 0.5F);
        }
        if ((fx & LAG) != 0) {
            // the same blow lands again a second later, wherever the foe has got to
            KingDeeds.later(sl, 20, () -> {
                if (v.isAlive() && king.isAlive() && v.distanceTo(king) < 16) {
                    KingDeeds.glitchAt(sl, v.position().add(0, 1, 0));
                    v.invulnerableTime = 0;
                    KingDeeds.hit(king, m.id, v, m.dmg * scale * 0.8F, false);
                    KingDeeds.count(king, KingDeeds.HITS, "lag_hit");
                }
            });
        }
        return true;
    }

    // ------------------------------------------------------------------------------------------------ shapes

    static void arc(RoyalMob king, ServerLevel sl, Move m, Vec3 from, Vec3 fwd, double r, double half, float scale) {
        double cos = Math.cos(Math.toRadians(Math.min(180, half)));
        for (LivingEntity v : KingForms.foes(king, sl, r + 16)) {
            Vec3 to = v.position().subtract(from);
            if (to.horizontalDistance() > r + v.getBbWidth() * 0.5 || Math.abs(to.y) > 4) {
                continue;
            }
            if (half >= 180 || KingDeeds.flat(to).dot(fwd) >= cos) {
                land(king, sl, m, v, scale);
            }
        }
        double base = Math.atan2(fwd.z, fwd.x);
        int n = (int) Math.max(6, Math.min(36, half / 6));
        for (int i = -n; i <= n; i++) {
            double a = base + Math.toRadians(half) * i / n;
            for (double rr = Math.max(1.5, r * 0.45); rr <= r; rr += Math.max(1.2, r / 3)) {
                double x = from.x + Math.cos(a) * rr, z = from.z + Math.sin(a) * rr;
                sl.sendParticles(tint(m, i), x, from.y + 1.2, z, 1, 0, 0, 0, 0);
            }
            if (i % 3 == 0) {
                sl.sendParticles(ParticleTypes.SWEEP_ATTACK, from.x + Math.cos(a) * r * 0.7, from.y + 1.2, from.z + Math.sin(a) * r * 0.7, 1, 0, 0, 0, 0);
            }
        }
    }

    static void line(RoyalMob king, ServerLevel sl, Move m, Vec3 a, Vec3 dir, double len, double width, float scale) {
        Vec3 b = sl.clip(new ClipContext(a, a.add(dir.scale(len)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, king)).getLocation();
        KingDeeds.line(sl, tint(m, 0), a, b, 0.35);
        KingDeeds.line(sl, tint(m, 1), a, b, 0.9);
        for (LivingEntity v : KingForms.foes(king, sl, len + 4)) {
            if (KingDeeds.toSegment(v.getBoundingBox().getCenter(), a, b) <= width + v.getBbWidth() * 0.5) {
                land(king, sl, m, v, scale);
            }
        }
    }

    static void circle(RoyalMob king, ServerLevel sl, Move m, Vec3 c, double r, float scale) {
        for (LivingEntity v : KingForms.foes(king, sl, 64)) {
            if (v.position().distanceTo(c) <= r + v.getBbWidth() * 0.5) {
                land(king, sl, m, v, scale);
            }
        }
        KingDeeds.ring(sl, tint(m, 0), c, r, 0.2, (int) (r * 8));
        KingDeeds.ring(sl, tint(m, 1), c, r * 0.5, 0.3, (int) (r * 5));
        sl.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.5, c.z, 1, 0, 0, 0, 0);
    }

    private static void ray(RoyalMob king, ServerLevel sl, Move m, Vec3 dir, double len) {
        Vec3 a = king.getEyePosition().add(0, -0.3, 0);
        Vec3 b = sl.clip(new ClipContext(a, a.add(dir.scale(len)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, king)).getLocation();
        KingDeeds.line(sl, ParticleTypes.END_ROD, a, b, 0.6);
        KingDeeds.line(sl, m.weapon == BOW ? new ParticleOptions[]{KingDeeds.RED, KingDeeds.GOLD, KingDeeds.CYAN, KingDeeds.WHITE}[sl.random.nextInt(4)] : tint(m, 0),
            a, b, 0.8);
        for (LivingEntity v : KingForms.foes(king, sl, len + 2)) {
            if (KingDeeds.toSegment(v.getBoundingBox().getCenter(), a, b) <= 0.8 + v.getBbWidth() * 0.5) {
                land(king, sl, m, v, 1F);
            }
        }
        sl.sendParticles(ParticleTypes.CRIT, b.x, b.y, b.z, 8, 0.2, 0.2, 0.2, 0.2);
    }

    private static void leap(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        Vec3 dir = t.position().subtract(king.position());
        king.setDeltaMovement(dir.x * 0.12, 1.2, dir.z * 0.12);
        king.hurtMarked = true;
        KingDeeds.sound(sl, king.position(), SoundEvents.WIND_CHARGE_BURST.value(), 2F, 0.7F);
        Vec3[] spot = {t.position()};
        KingDeeds.each(sl, 0, 8, 1, k -> {
            if (t.isAlive()) {
                spot[0] = t.position();
            }
            KingDeeds.ring(sl, tint(m, 0), spot[0], m.a, 0.1, 20);
        });
        KingDeeds.later(sl, 12, () -> {
            if (!king.isAlive()) {
                return;
            }
            Vec3 c = spot[0];
            if (sl.noCollision(king, king.getBoundingBox().move(c.subtract(king.position())))) {
                king.teleportTo(c.x, c.y, c.z);
            }
            king.fallDistance = 0F;
            circle(king, sl, m, c, m.a + king.getBbWidth() * 0.5, 1F);
            KingDeeds.sound(sl, c, SoundEvents.MACE_SMASH_GROUND_HEAVY, 3F, 0.7F);
        });
    }

    private static void dash(RoyalMob king, ServerLevel sl, Move m, Vec3 fwd) {
        Set<LivingEntity> struck = new HashSet<>();
        double speed = m.a / 6.0;
        KingDeeds.each(sl, 0, 6, 1, k -> {
            if (!king.isAlive()) {
                return;
            }
            king.getNavigation().stop();
            // stepped, not pushed: a push can be lost (a big body, a leap's leftover fall), a step cannot
            Vec3 step = fwd.scale(speed);
            if (sl.noCollision(king, king.getBoundingBox().move(step))) {
                king.teleportTo(king.getX() + step.x, king.getY(), king.getZ() + step.z);
            } else {
                king.setDeltaMovement(step.x, king.getDeltaMovement().y, step.z);
                king.hurtMarked = true;
            }
            sl.sendParticles(tint(m, k), king.getX(), king.getY() + king.getBbHeight() * 0.5, king.getZ(), 8, 0.5, 0.6, 0.5, 0);
            for (LivingEntity v : KingForms.foes(king, sl, m.b + king.getBbWidth() * 0.5)) {
                if (struck.add(v)) {
                    land(king, sl, m, v, 1F);
                }
            }
        });
    }

    private static void wave(RoyalMob king, ServerLevel sl, Move m, Vec3 from, Vec3 fwd) {
        Set<LivingEntity> struck = new HashSet<>();
        int steps = (int) Math.ceil(m.a / 1.6);
        KingDeeds.each(sl, 0, steps, 1, k -> {
            Vec3 p = from.add(fwd.scale(1.5 + k * 1.6)).add(0, 1, 0);
            Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
            for (double s = -m.b; s <= m.b; s += 0.6) {
                Vec3 q = p.add(side.scale(s));
                sl.sendParticles(tint(m, (int) (s * 3)), q.x, q.y, q.z, 1, 0, 0.3, 0, 0);
            }
            if (m.weapon == SCYTHE) {
                sl.sendParticles(ParticleTypes.SQUID_INK, p.x, p.y, p.z, 6, m.b * 0.4, 0.4, m.b * 0.4, 0.02);
            }
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                if (v.position().add(0, 1, 0).distanceTo(p) <= m.b + v.getBbWidth() * 0.5 && struck.add(v)) {
                    land(king, sl, m, v, 1F);
                }
            }
        });
    }

    private static void lob(RoyalMob king, ServerLevel sl, Move m, LivingEntity t, int k) {
        Vec3 target = t.position().add((m.fx & OFFSET) != 0 ? new Vec3(sl.random.nextGaussian() * 2, 0, sl.random.nextGaussian() * 2) : Vec3.ZERO);
        Vec3 start = king.getEyePosition();
        KingDeeds.each(sl, 0, 15, 1, j -> {
            double u = (j + 1) / 15.0;
            Vec3 p = start.lerp(target, u).add(0, Math.sin(Math.PI * u) * 6, 0);
            sl.sendParticles(m.weapon == BROKEN ? KingDeeds.MAGENTA : tint(m, j), p.x, p.y, p.z, 3, 0.1, 0.1, 0.1, 0);
            if (m.weapon == BROKEN) {
                sl.sendParticles(KingDeeds.BLACK, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0);
            }
        });
        KingDeeds.later(sl, 16, () -> {
            if (king.isAlive()) {
                circle(king, sl, m, target, m.a, 1F);
                KingDeeds.sound(sl, target, SoundEvents.GENERIC_EXPLODE.value(), 1.5F, 1.2F);
            }
        });
    }

    private static void thrown(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        Vec3 start = king.getEyePosition().add(0, -0.3, 0);
        Vec3 dir = aim(king, t);
        double far = Math.min(m.a, start.distanceTo(t.getEyePosition()) + 4);
        Set<LivingEntity> out = new HashSet<>(), back = new HashSet<>();
        int n = (int) Math.ceil(far / 1.5);
        KingDeeds.each(sl, 0, n * 2, 1, k -> {
            boolean going = k < n;
            double s = going ? (k + 1) * 1.5 : (2 * n - k - 1) * 1.5;
            Vec3 p = (going ? start : king.getEyePosition().add(0, -0.3, 0)).add(dir.scale(s));
            for (int i = 0; i < 6; i++) {
                double a = k * 0.9 + i * Math.PI / 3;
                sl.sendParticles(tint(m, i), p.x + Math.cos(a) * 0.8, p.y + Math.sin(a) * 0.8, p.z, 1, 0, 0, 0, 0);
            }
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                if (v.getBoundingBox().getCenter().distanceTo(p) <= m.b + v.getBbWidth() * 0.5 && (going ? out : back).add(v)) {
                    land(king, sl, m, v, going ? 1F : 0.7F);
                }
            }
        });
    }

    private static void pull(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        Vec3 front = king.position().add(KingDeeds.flat(t.position().subtract(king.position())).scale(1.6 + king.getBbWidth() * 0.5));
        List<LivingEntity> caught = new ArrayList<>();
        for (LivingEntity v : KingForms.foes(king, sl, m.a)) {
            if (v == t || v.distanceTo(t) < 3) {
                caught.add(v);
            }
        }
        for (LivingEntity v : caught) {
            KingDeeds.line(sl, m.weapon == BROKEN ? KingDeeds.MAGENTA : KingDeeds.CRIMSON, v.getEyePosition(), king.getEyePosition(), 0.5);
            if (m.weapon == BROKEN || !(v instanceof net.minecraft.world.entity.player.Player)) {
                // the broken one's pull is a jump in place; a creature (not a player, who is drawn smoothly) is
                // snatched to him outright
                v.teleportTo(front.x, front.y, front.z);
            } else {
                Vec3 in = front.subtract(v.position());
                v.setDeltaMovement(in.x * 0.35, 0.3, in.z * 0.35);
                v.hurtMarked = true;
            }
        }
        KingDeeds.later(sl, 8, () -> {
            if (king.isAlive()) {
                arc(king, sl, m, king.position(), KingDeeds.flat(t.position().subtract(king.position())), 4.5 + king.getBbWidth() * 0.5, 70, 1F);
            }
        });
    }

    private static void behind(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        Vec3 look = KingDeeds.flat(t.getLookAngle());
        Vec3 to = t.position().subtract(look.scale(1.6 + king.getBbWidth() * 0.5));
        Vec3 from = king.position();
        if (sl.noCollision(king, king.getBoundingBox().move(to.subtract(from)))) {
            sl.sendParticles(m.weapon == BROKEN ? KingDeeds.MAGENTA : ParticleTypes.PORTAL, from.x, from.y + 1, from.z, 30, 0.5, 1, 0.5, 0.1);
            king.teleportTo(to.x, to.y, to.z);
        }
        Vec3 fwd = KingDeeds.flat(t.position().subtract(king.position()));
        arc(king, sl, m, king.position(), fwd, m.a + king.getBbWidth() * 0.5, m.b, 1F);
    }

    private static void cross(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        Vec3 c = t.position().add(0, t.getBbHeight() * 0.5, 0);
        Vec3 f = KingDeeds.flat(c.subtract(king.position()));
        Vec3 side = new Vec3(-f.z, 0, f.x);
        Vec3[] dirs = {f.add(side).normalize(), f.subtract(side).normalize()};
        for (int i = 0; i < 2; i++) {
            Vec3 a = c.subtract(dirs[i].scale(m.a / 2)), b = c.add(dirs[i].scale(m.a / 2));
            KingDeeds.line(sl, tint(m, i), a, b, 0.3);
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                if (KingDeeds.toSegment(v.getBoundingBox().getCenter(), a, b) <= m.b + v.getBbWidth() * 0.5) {
                    land(king, sl, m, v, 1F);
                }
            }
        }
    }

    private static void erupt(RoyalMob king, ServerLevel sl, Move m, Vec3 from, Vec3 fwd) {
        Set<LivingEntity> struck = new HashSet<>();
        int n = (int) Math.ceil(m.a / 1.5);
        KingDeeds.each(sl, 0, n, 2, k -> {
            Vec3 p = from.add(fwd.scale(2 + k * 1.5));
            for (double y = 0; y < 3; y += 0.4) {
                sl.sendParticles(tint(m, k), p.x, p.y + y, p.z, 1, 0.05, 0, 0.05, 0);
            }
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y + 1.5, p.z, 6, 0.2, 0.8, 0.2, 0.05);
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                if (v.position().distanceTo(p) <= m.b + v.getBbWidth() * 0.5 && struck.add(v)) {
                    land(king, sl, m, v, 1F);
                    v.setDeltaMovement(v.getDeltaMovement().add(0, 0.6, 0));
                    v.hurtMarked = true;
                }
            }
            if (k % 2 == 0) {
                KingDeeds.sound(sl, p, SoundEvents.ANVIL_LAND, 1.0F, 1.8F);
            }
        });
    }

    private static void upthrust(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        if (king.distanceTo(t) > m.a + king.getBbWidth()) {
            return;
        }
        Vec3 c = t.position();
        if ((m.fx & OFFSET) != 0) {
            // NaN: thrown high, put down somewhere else
            t.teleportTo(c.x + sl.random.nextGaussian() * 3, c.y + 10, c.z + sl.random.nextGaussian() * 3);
            KingDeeds.glitchAt(sl, c.add(0, 1, 0));
        }
        land(king, sl, m, t, 1F);
        t.setDeltaMovement(t.getDeltaMovement().add(0, 1.4, 0));
        t.hurtMarked = true;
        KingDeeds.line(sl, tint(m, 0), c, c.add(0, 8, 0), 0.4);
        if ((m.fx & LIGHTNING) != 0) {
            KingDeeds.later(sl, 10, () -> KingForms.bolt(sl, t.isAlive() ? t.position() : c));
        }
    }

    private static void ring(RoyalMob king, ServerLevel sl, Move m) {
        Vec3 c = king.position();
        Set<LivingEntity> struck = new HashSet<>();
        int n = (int) Math.ceil(m.a / 1.5);
        KingDeeds.each(sl, 0, n, 1, k -> {
            double r = 1.5 + k * 1.5;
            KingDeeds.ring(sl, tint(m, k), c, r, 0.2, (int) (r * 6));
            for (LivingEntity v : KingForms.foes(king, sl, m.a + 2)) {
                double d = v.position().distanceTo(c);
                if (Math.abs(d - r) <= 1.2 && struck.add(v)) {
                    land(king, sl, m, v, 1F);
                }
            }
        });
    }

    private static void chain(RoyalMob king, ServerLevel sl, Move m, LivingEntity t) {
        List<LivingEntity> done = new ArrayList<>();
        LivingEntity cur = t;
        Vec3 from = king.getEyePosition();
        for (int i = 0; i < m.count && cur != null; i++) {
            KingDeeds.line(sl, ParticleTypes.ELECTRIC_SPARK, from, cur.getEyePosition(), 0.4);
            land(king, sl, m, cur, i == 0 ? 1F : 0.7F);
            done.add(cur);
            from = cur.getEyePosition();
            LivingEntity next = null;
            double best = 8 * 8;
            for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                double dd = v.distanceToSqr(cur);
                if (!done.contains(v) && dd < best) {
                    best = dd;
                    next = v;
                }
            }
            cur = next;
        }
        KingDeeds.sound(sl, t.position(), SoundEvents.LIGHTNING_BOLT_THUNDER, 2F, 1.6F);
    }

    // ------------------------------------------------------------------------------------------------ poses

    /**
     * Each style's windup and strike: right upper arm x y z, left upper arm x y z, body x y, head x, height (+ lower),
     * right forearm x, left forearm x, the right-hand weapon x, the left-hand weapon x. Offsets on the stance's hold.
     */
    private static final Map<String, float[][]> STYLES = new HashMap<>();

    private static void style(String id, float[] w, float[] s) {
        STYLES.put(id, new float[][]{w, s});
    }

    static {
        style("slash_h", new float[]{-1.3F, -1.0F, 0.3F, -0.4F, 0, -0.2F, 0, -0.6F, 0, 0, 0.2F, 0, -0.6F, 0},
            new float[]{-1.4F, 1.1F, 0, -0.3F, 0, -0.2F, 0.1F, 0.7F, 0, 0.5F, 0, 0, -0.6F, 0});
        style("slash_d", new float[]{-2.9F, -0.2F, 0.5F, -0.6F, 0, -0.2F, -0.2F, -0.3F, -0.2F, 0, 0.3F, 0, 0.4F, 0},
            new float[]{-0.5F, 0.5F, -0.1F, -0.4F, 0, -0.2F, 0.4F, 0.3F, 0.2F, 1F, 0, 0, -0.3F, 0});
        style("slash_up", new float[]{0.5F, -0.4F, 0.2F, -0.2F, 0, 0, 0.3F, -0.3F, 0, 1.5F, 0, 0, 0.3F, 0},
            new float[]{-2.7F, 0.3F, 0, -0.4F, 0, -0.2F, -0.25F, 0.3F, -0.3F, 0, 0, 0, 0.6F, 0});
        style("thrust", new float[]{-0.9F, -0.3F, 0, -0.5F, 0, -0.2F, 0, -0.5F, 0, 0.5F, 0.9F, 0, 1.0F, 0},
            new float[]{-1.6F, 0.1F, 0, -0.6F, 0, -0.2F, 0.2F, 0.35F, 0, 1F, -0.2F, 0, 1.0F, 0});
        style("thrust_up", new float[]{-0.4F, 0, 0, -0.3F, 0, 0, 0.3F, 0, 0.2F, 2F, 0.6F, 0, 0.6F, 0},
            new float[]{-3.0F, 0, 0.1F, -0.4F, 0, -0.2F, -0.3F, 0, -0.6F, 0, 0, 0, -1.0F, 0});
        style("spin", new float[]{-1.4F, -0.9F, 0.4F, -1.4F, 0.9F, -0.4F, 0, -1.0F, 0, 0.5F, 0, 0, -0.5F, -0.5F},
            new float[]{-1.5F, 0.6F, 1.2F, -1.5F, -0.6F, -1.2F, 0, 6.28F, 0, 0.5F, 0, 0, -0.5F, -0.5F});
        style("slam", new float[]{-3.0F, 0, 0.3F, -3.0F, 0, -0.3F, -0.3F, 0, -0.4F, 0, 0, 0, 0.3F, 0.3F},
            new float[]{-0.4F, 0, 0, -0.4F, 0, 0, 0.6F, 0, 0.3F, 3F, 0, 0, -0.3F, -0.3F});
        style("bash", new float[]{-0.4F, 0, 0.2F, -0.8F, 0.6F, -0.2F, 0, 0.4F, 0, 0, 0, 0.4F, 0, 0},
            new float[]{-0.3F, 0, 0.2F, -1.6F, -0.4F, -0.1F, 0.2F, -0.5F, 0, 1F, 0, -0.3F, 0, 0});
        style("butt", new float[]{-1.2F, 0.4F, 0, -0.3F, 0, 0, 0, 0.6F, 0, 0, 0.4F, 0, 0, 0},
            new float[]{0.6F, -0.6F, 0, -0.3F, 0, 0, -0.2F, -0.8F, 0, 0, 0, 0, 0, 0});
        style("leap", new float[]{0.6F, 0, 0.3F, 0.6F, 0, -0.3F, 0.4F, 0, 0.2F, 3F, 0, 0, 0, 0},
            new float[]{-3.0F, 0, 0.2F, -3.0F, 0, -0.2F, -0.3F, 0, -0.4F, 0, 0, 0, 0.5F, 0.5F});
        style("dash", new float[]{0.6F, 0, 0.2F, -0.4F, 0, 0, 0.5F, 0, 0.2F, 1.5F, 0, 0, 0, 0},
            new float[]{-1.6F, 0.5F, 0, -0.8F, 0, 0, 0.4F, 0.5F, 0, 1F, 0, 0, -0.4F, 0});
        style("double", new float[]{-2.4F, -0.3F, 0.3F, -2.4F, 0.3F, -0.3F, -0.2F, 0, -0.2F, 0, 0, 0, 0.3F, 0.3F},
            new float[]{-0.9F, 0.4F, 0, -0.9F, -0.4F, 0, 0.3F, 0, 0.1F, 1F, 0, 0, -0.3F, -0.3F});
        style("cross", new float[]{-2.6F, 0.6F, 0.4F, -2.6F, -0.6F, -0.4F, -0.2F, 0, -0.3F, 0, 0, 0, 0.3F, 0.3F},
            new float[]{-0.6F, -0.8F, -0.3F, -0.6F, 0.8F, 0.3F, 0.4F, 0, 0.2F, 1F, 0, 0, -0.4F, -0.4F});
        style("cast", new float[]{-3.0F, 0, 0.5F, -3.0F, 0, -0.5F, -0.3F, 0, -0.8F, 0, 0, 0, 0, 0},
            new float[]{-1.6F, 0, 0.2F, -1.6F, 0, -0.2F, 0.2F, 0, 0, 0, 0, 0, 0, 0});
        style("throw", new float[]{-3.0F, -0.3F, 0.4F, -0.8F, 0, -0.3F, -0.2F, -0.6F, 0, 0, 0.5F, 0, 0.5F, 0},
            new float[]{-1.0F, 0.4F, 0, -0.6F, 0, 0, 0.3F, 0.5F, 0, 0, 0, 0, -0.8F, 0});
        style("hook", new float[]{-2.6F, 0.2F, 0.3F, -1.2F, 0, -0.2F, -0.1F, 0.3F, 0, 0, 0, 0, 0.6F, 0},
            new float[]{-0.4F, -0.6F, 0, -0.8F, 0, 0, 0.3F, -0.6F, 0, 1F, 0.4F, 0, -0.4F, 0});
        style("sweep_low", new float[]{-0.5F, -1.0F, 0.4F, -0.3F, 0, -0.2F, 0.5F, -0.6F, 0.3F, 3F, 0, 0, -0.9F, 0},
            new float[]{-0.6F, 1.2F, 0, -0.3F, 0, -0.2F, 0.6F, 0.7F, 0.3F, 3F, 0, 0, -0.9F, 0});
        style("twirl", new float[]{-1.5F, 0, 0.2F, -1.5F, 0, -0.2F, 0, 0, 0, 0, -0.2F, -0.4F, 0, 0},
            new float[]{-1.5F, 0, 0.2F, -1.5F, 0, -0.2F, 0, 0, 0, 0, -0.2F, -0.4F, 12.57F, 0});
        style("draw", new float[]{-1.55F, 0.4F, 0, -1.55F, 0, 0, 0, -0.4F, 0, 0, -0.9F, 1.25F, 0, 0},
            new float[]{-1.4F, -0.2F, 0.3F, -1.55F, 0, 0, 0, -0.4F, 0, 0, 0, 1.25F, 0, 0});
        style("lob", new float[]{-2.4F, 0.4F, 0, -2.4F, 0, 0, -0.4F, -0.3F, -0.6F, 0, -0.9F, 1.25F, 0, 0},
            new float[]{-2.2F, -0.2F, 0.3F, -2.4F, 0, 0, -0.4F, -0.3F, -0.6F, 0, 0, 1.25F, 0, 0});
        style("backstep", new float[]{0.3F, 0, 0.2F, 0.3F, 0, -0.2F, -0.3F, 0, 0, 1.5F, 0, 0, 0, 0},
            new float[]{-1.55F, 0.4F, 0, -1.55F, 0, 0, -0.2F, -0.4F, 0, 0, -0.9F, 1.25F, 0, 0});
        style("glitch", new float[]{-0.6F, 1.8F, 2.4F, -2.8F, -1.6F, -1.2F, 0.5F, 2.4F, 0.9F, 1F, 1.2F, -1.4F, 2.0F, 0},
            new float[]{-2.9F, -2.2F, -0.8F, 0.4F, 1.9F, 2.6F, -0.4F, -1.8F, -1.1F, 0, -1.3F, 1.1F, -2.6F, 0});
        style("guard", new float[]{-0.4F, 0, 0, -1.4F, 0.5F, 0, 0.1F, 0, 0, 0.5F, 0, 0, 0, 0},
            new float[]{-0.4F, 0, 0, -1.4F, 0.5F, 0, 0.1F, 0, 0, 0.5F, 0, 0, 0, 0});
    }

    /** Deeds of KingDeeds that have no pose of their own there, given a style. */
    private static final Map<String, String> DEED_STYLE = Map.ofEntries(
        Map.entry("execution", "hook"), Map.entry("sunder", "bash"), Map.entry("void", "cast"), Map.entry("feast", "cast"),
        Map.entry("doomsday", "cast"), Map.entry("flurry", "double"), Map.entry("crossslash", "cross"), Map.entry("lunge", "dash"),
        Map.entry("javelin", "throw"), Map.entry("rain", "lob"), Map.entry("triple", "draw"), Map.entry("backstep", "backstep"),
        Map.entry("sidestep", "dash"), Map.entry("guard", "guard"), Map.entry("summon", "cast"), Map.entry("chains", "hook"),
        Map.entry("wormwood", "cast"), Map.entry("bowls", "cast"), Map.entry("veil", "cast"), Map.entry("soul", "cast"),
        Map.entry("halo", "throw"), Map.entry("feathers", "cast"), Map.entry("crucify", "hook"), Map.entry("creation", "cast"),
        Map.entry("dawn", "slash_d"), Map.entry("swords", "cast"), Map.entry("overflow", "glitch"), Map.entry("panic", "glitch"),
        Map.entry("leapin", "leap"));

    private static final Map<String, float[][]> POSE_CACHE = new HashMap<>();

    /** The pose of a technique by its mechanic name (MOVE_KING_...), or null. */
    public static float[][] poseFor(String mechanic) {
        if (POSE_CACHE.containsKey(mechanic)) {
            return POSE_CACHE.get(mechanic);
        }
        float[][] p = null;
        String id = mechanic.startsWith("MOVE_KING_") ? mechanic.substring(10).toLowerCase(Locale.ROOT) : mechanic.toLowerCase(Locale.ROOT);
        Move m = move(id);
        if (m != null) {
            p = mirrored(STYLES.get(m.style), m.side);
        } else if (DEED_STYLE.containsKey(id)) {
            p = STYLES.get(DEED_STYLE.get(id));
        }
        POSE_CACHE.put(mechanic, p);
        return p;
    }

    /** A pose done with the other hand: the arms, forearms and weapons swapped, the turns about y and z reversed. */
    static float[][] mirrored(float[][] p, int side) {
        if (p == null || side >= 0) {
            return p;
        }
        float[][] o = new float[2][];
        for (int k = 0; k < 2; k++) {
            float[] a = p[k], b = a.clone();
            b[0] = a[3];
            b[1] = -a[4];
            b[2] = -a[5];
            b[3] = a[0];
            b[4] = -a[1];
            b[5] = -a[2];
            b[7] = -a[7];
            b[10] = a[11];
            b[11] = a[10];
            b[12] = a[13];
            b[13] = a[12];
            o[k] = b;
        }
        return o;
    }
}
