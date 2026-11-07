package jp.oror.reborn.king;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Endermite;
import net.minecraft.world.entity.monster.Phantom;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;

/**
 * (054) The villager king's great works beyond his weapons' motions (the user: ten super-powerful specials, five special
 * attacks, three attacks of a god, the backstep and the rest, summonings, the feast):
 * <ul>
 * <li>Specials: 聖剣解放《黎明》 and 王の剣陣 (the hero), スタックオーバーフロー and カーネルパニック (the broken one), 蝿の帳, 魂喰らい,
 * 堕ちた光輪, 黒き翼の嵐, 逆さ十字の磔 and 偽りの創世 (Baal Zebul).</li>
 * <li>Special attacks: the execution, the sundering, the deletion, the feast (KingDeeds) and 鎖縛, the binding.</li>
 * <li>The wrath of a god: 審判の日 (KingDeeds.doomsday: pillars of light, a thousand ten times over on any in one at its
 * moment), 星墜とし (Wormwood: stars falling, the waters made bitter), 七つの鉢 (the seven bowls of wrath, one after
 * another).</li>
 * <li>The rest: the backstep, the sidestep and the hero's shield (when he is struck), the leap at a far foe, the
 * summoning (his guard, the broken one's errors, Baal Zebul's flies).</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingWrath {
    private KingWrath() {
    }

    // ------------------------------------------------------------------------------------------------ the hero

    /** 聖剣解放《黎明》: a sword of light many times his height rises over him and falls along a line of twenty-two blocks. */
    static void dawn(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, KingDeeds.who(king) + "：聖剣、解放――《黎明》！", ChatFormatting.GOLD);
        Vec3 fwd = KingDeeds.flat(t.position().subtract(king.position()));
        KingDeeds.each(sl, 0, Math.max(1, w / 3), 3, k -> {
            Vec3 c = king.position();
            for (double y = 0; y < 14; y += 0.7) {
                sl.sendParticles(ParticleTypes.END_ROD, c.x, c.y + king.getBbHeight() + y, c.z, 1, 0.15, 0, 0.15, 0);
            }
            sl.sendParticles(KingDeeds.GOLD, c.x, c.y + king.getBbHeight() + 7, c.z, 10, 1.2, 4, 1.2, 0);
        });
        KingDeeds.sound(sl, king.position(), SoundEvents.BEACON_POWER_SELECT, 3F, 0.6F);
        KingDeeds.later(sl, w, () -> {
            if (!king.isAlive()) {
                return;
            }
            Vec3 a = king.position().add(0, 1, 0), b = a.add(fwd.scale(22));
            for (int i = 0; i < 3; i++) {
                KingDeeds.line(sl, i == 1 ? ParticleTypes.END_ROD : KingDeeds.GOLD, a.add(0, i * 1.2, 0), b.add(0, i * 1.2, 0), 0.3);
            }
            KingDeeds.line(sl, ParticleTypes.FLAME, a, b, 0.5);
            for (LivingEntity v : KingForms.foes(king, sl, 26)) {
                if (KingDeeds.toSegment(v.getBoundingBox().getCenter(), a, b) <= 3.0 + v.getBbWidth() * 0.5) {
                    v.invulnerableTime = 0;
                    if (KingDeeds.hit(king, "dawn", v, 60F, true)) {
                        v.igniteForSeconds(8);
                        KingDeeds.throwFrom(v, king.position(), 2.0, 0.6);
                    }
                }
            }
            sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, b.x, b.y, b.z, 1, 0, 0, 0, 0);
            KingDeeds.sound(sl, a, SoundEvents.LIGHTNING_BOLT_THUNDER, 4F, 0.6F);
            KingDeeds.sound(sl, b, SoundEvents.GENERIC_EXPLODE.value(), 3F, 0.7F);
        });
    }

    /** 王の剣陣: twelve swords of light fall one after another on his foes and about them. */
    static void swords(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, KingDeeds.who(king) + "：剣よ、降れ。", ChatFormatting.GOLD);
        KingDeeds.later(sl, w, () -> {
            List<Vec3> spots = new ArrayList<>();
            for (LivingEntity v : KingForms.foes(king, sl, 32)) {
                for (int i = 0; i < 3; i++) {
                    spots.add(v.position().add(sl.random.nextGaussian() * 1.2, 0, sl.random.nextGaussian() * 1.2));
                }
            }
            while (spots.size() < 12) {
                double a = sl.random.nextDouble() * Math.PI * 2, r = 3 + sl.random.nextDouble() * 12;
                spots.add(king.position().add(Math.cos(a) * r, 0, Math.sin(a) * r));
            }
            for (int i = 0; i < spots.size(); i++) {
                Vec3 s = spots.get(i);
                KingDeeds.later(sl, 1 + i * 3, () -> {
                    KingDeeds.line(sl, ParticleTypes.END_ROD, s.add(0, 12, 0), s, 0.5);
                    KingDeeds.ring(sl, KingDeeds.GOLD, s, 1.5, 0.1, 12);
                    for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                        if (v.position().distanceTo(s) <= 1.6 + v.getBbWidth() * 0.5) {
                            v.invulnerableTime = 0;
                            if (KingDeeds.hit(king, "swords", v, 14F, true)) {
                                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 3));
                            }
                        }
                    }
                    KingDeeds.sound(sl, s, SoundEvents.ANVIL_LAND, 1.2F, 1.7F);
                });
            }
        });
    }

    // ------------------------------------------------------------------------------------------------ the broken one

    /** スタックオーバーフロー: a blow that calls itself: one, two, four, eight, sixteen ghost strikes about the foe. */
    static void overflow(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        for (int depth = 0; depth < 5; depth++) {
            int n = 1 << depth;
            KingDeeds.later(sl, w + depth * 6, () -> {
                if (!t.isAlive() || !king.isAlive()) {
                    return;
                }
                for (int i = 0; i < n; i++) {
                    Vec3 s = t.position().add(sl.random.nextGaussian() * 2.2, 0, sl.random.nextGaussian() * 2.2);
                    KingDeeds.glitchAt(sl, s.add(0, 1, 0));
                    for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                        if (v.position().distanceTo(s) <= 1.8 + v.getBbWidth() * 0.5) {
                            v.invulnerableTime = 0;
                            KingDeeds.hit(king, "overflow", v, 6F, false);
                        }
                    }
                }
                KingDeeds.sound(sl, t.position(), SoundEvents.NOTE_BLOCK_BIT.value(), 2F, 0.5F + n * 0.1F);
            });
        }
        KingDeeds.later(sl, w + 32, () -> KingDeeds.KingCinemaSay.near(sl, king, "崩壊王：Exception in thread \"main\" java.lang.StackOverflowError",
            ChatFormatting.LIGHT_PURPLE));
    }

    /** カーネルパニック: everything about him stops dead for two seconds, then breaks apart. */
    static void panic(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, "*** KERNEL PANIC *** 崩壊王：――――――――", ChatFormatting.DARK_PURPLE);
        for (LivingEntity v : KingForms.foes(king, sl, 16)) {
            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, w + 5, 255));
            v.addEffect(new MobEffectInstance(MobEffects.JUMP, w + 5, 128));
            v.addEffect(new MobEffectInstance(MobEffects.DIG_SLOWDOWN, w + 5, 9));
            v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, w + 20, 0));
        }
        KingDeeds.each(sl, 0, Math.max(1, w / 4), 4, k -> {
            Vec3 c = king.position();
            for (int i = 0; i < 6; i++) {
                KingDeeds.glitchAt(sl, c.add(sl.random.nextGaussian() * 6, 1 + sl.random.nextDouble() * 3, sl.random.nextGaussian() * 6));
            }
        });
        KingDeeds.later(sl, w, () -> {
            Vec3 c = king.position();
            for (LivingEntity v : KingForms.foes(king, sl, 12)) {
                v.invulnerableTime = 0;
                if (KingDeeds.hit(king, "panic", v, 40F, true)) {
                    KingDeeds.throwFrom(v, c, 2.2, 0.8);
                }
            }
            sl.sendParticles(KingDeeds.MAGENTA, c.x, c.y + 1, c.z, 300, 6, 2, 6, 0.2);
            sl.sendParticles(KingDeeds.CYAN, c.x, c.y + 1, c.z, 200, 6, 2, 6, 0.2);
            sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, c.x, c.y + 1, c.z, 2, 2, 0.5, 2, 0);
            KingDeeds.sound(sl, c, SoundEvents.GENERIC_EXPLODE.value(), 4F, 0.4F);
        });
    }

    // ------------------------------------------------------------------------------------------------ Baal Zebul

    static void veil(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：地の面を覆え、我が蝿どもよ。", ChatFormatting.DARK_GRAY);
        KingDeeds.later(sl, w, () -> {
            if (king.isAlive()) {
                KingSouls.veil(king, sl, 240);
            }
        });
    }

    static void soul(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：青き炎よ、その魂を灼け。燃え尽きしとき、それは我がものとなる。", ChatFormatting.DARK_AQUA);
        KingDeeds.later(sl, w, () -> {
            for (LivingEntity v : KingForms.foes(king, sl, 24)) {
                KingSouls.mark(king, v);
                KingDeeds.line(sl, ParticleTypes.SOUL_FIRE_FLAME, king.getEyePosition(), v.getEyePosition(), 0.4);
                KingDeeds.count(king, KingDeeds.HITS, "soul");
            }
            KingDeeds.sound(sl, king.position(), SoundEvents.SOUL_ESCAPE.value(), 4F, 0.4F);
        });
    }

    /** 堕ちた光輪: his own cracked halo thrown, turning, out to his foe and back. */
    static void halo(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        KingDeeds.later(sl, w, () -> {
            Vec3 start = king.getEyePosition().add(0, 1.5, 0);
            Vec3 dir = t.getEyePosition().subtract(start).normalize();
            double far = Math.min(32, start.distanceTo(t.getEyePosition()) + 6);
            int n = (int) Math.ceil(far / 1.2);
            Set<LivingEntity> out = new HashSet<>(), back = new HashSet<>();
            KingDeeds.each(sl, 0, n * 2, 1, k -> {
                boolean going = k < n;
                double s = going ? (k + 1) * 1.2 : (2 * n - k - 1) * 1.2;
                Vec3 p = start.add(dir.scale(s));
                for (int i = 0; i < 16; i++) {
                    if (i % 5 == 0) {
                        continue;
                    }
                    double a = k * 0.7 + i * Math.PI / 8;
                    sl.sendParticles(i % 2 == 0 ? KingDeeds.GOLD : KingDeeds.CRIMSON, p.x + Math.cos(a) * 1.8, p.y + Math.sin(a) * 1.8 * 0.3, p.z + Math.sin(a) * 1.8,
                        1, 0, 0, 0, 0);
                }
                for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                    if (v.getBoundingBox().getCenter().distanceTo(p) <= 2.4 + v.getBbWidth() * 0.5 && (going ? out : back).add(v)) {
                        v.invulnerableTime = 0;
                        if (KingDeeds.hit(king, "halo", v, 30F, true)) {
                            v.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
                        }
                    }
                }
                if (k % 4 == 0) {
                    KingDeeds.sound(sl, p, SoundEvents.PLAYER_ATTACK_SWEEP, 1.5F, 0.5F);
                }
            });
        });
    }

    /** 黒き翼の嵐: black feathers like knives, six at every foe and many more everywhere. */
    static void feathers(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.later(sl, w, () -> {
            Vec3 c = king.position().add(0, king.getBbHeight() * 0.7, 0);
            for (int i = 0; i < 24; i++) {
                double a = i * Math.PI / 12;
                KingDeeds.line(sl, KingDeeds.BLACK, c, c.add(Math.cos(a) * 20, sl.random.nextDouble() * 3 - 1.5, Math.sin(a) * 20), 0.7);
            }
            for (LivingEntity v : KingForms.foes(king, sl, 24)) {
                for (int i = 0; i < 6; i++) {
                    int k = i;
                    KingDeeds.later(sl, 1 + i * 2, () -> {
                        if (!v.isAlive()) {
                            return;
                        }
                        Vec3 from = c.add(sl.random.nextGaussian() * 3, sl.random.nextDouble() * 3, sl.random.nextGaussian() * 3);
                        KingDeeds.line(sl, k % 2 == 0 ? KingDeeds.BLACK : KingDeeds.CRIMSON, from, v.getEyePosition(), 0.5);
                        v.invulnerableTime = 0;
                        if (KingDeeds.hit(king, "feathers", v, 5F, true)) {
                            v.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0));
                        }
                    });
                }
            }
            KingDeeds.sound(sl, c, SoundEvents.PHANTOM_FLAP, 4F, 0.4F);
        });
    }

    /** 逆さ十字の磔: up to four foes lifted by chains and held on inverted crosses for three seconds, burning, then let fall. */
    static void crucify(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：逆しまに架けられよ。", ChatFormatting.DARK_RED);
        KingDeeds.later(sl, w, () -> {
            List<LivingEntity> fs = new ArrayList<>(KingForms.foes(king, sl, 20));
            if (fs.size() > 4) {
                fs = fs.subList(0, 4);
            }
            for (LivingEntity v : fs) {
                Vec3 hold = v.position().add(0, 4, 0);
                KingDeeds.each(sl, 0, 60, 1, k -> {
                    if (!v.isAlive()) {
                        return;
                    }
                    v.teleportTo(hold.x, hold.y, hold.z);
                    v.setDeltaMovement(Vec3.ZERO);
                    v.hurtMarked = true;
                    v.fallDistance = 0F;
                    if (k % 4 == 0) {
                        // the inverted cross: the long arm above, the bar low
                        KingDeeds.line(sl, KingDeeds.CRIMSON, hold.add(0, 2.6, 0), hold.add(0, -1.2, 0), 0.3);
                        KingDeeds.line(sl, KingDeeds.CRIMSON, hold.add(-1.0, -0.4, 0), hold.add(1.0, -0.4, 0), 0.3);
                        for (int i = 0; i < 4; i++) {
                            double a = i * Math.PI / 2 + 0.6;
                            KingDeeds.line(sl, KingDeeds.BLACK, hold.add(0, 1, 0), hold.add(Math.cos(a) * 4, -4, Math.sin(a) * 4), 0.6);
                        }
                    }
                    if (k % 10 == 0) {
                        v.invulnerableTime = 0;
                        if (KingDeeds.hit(king, "crucify", v, 6F, true)) {
                            v.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 2));
                        }
                    }
                });
                KingDeeds.later(sl, 61, () -> v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2)));
            }
            KingDeeds.sound(sl, king.position(), SoundEvents.CHAIN_BREAK, 3F, 0.5F);
        });
    }

    /** 偽りの創世: he makes creatures in mockery of creation: three twisted angels and two black wings. */
    static void creation(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：光あれ――否。歪みあれ。", ChatFormatting.DARK_PURPLE);
        KingDeeds.later(sl, w, () -> {
            for (int i = 0; i < 3; i++) {
                Vex a = EntityType.VEX.create(sl);
                if (a != null) {
                    a.moveTo(king.getX() + sl.random.nextGaussian() * 2, king.getY() + 3, king.getZ() + sl.random.nextGaussian() * 2, 0F, 0F);
                    a.setOwner(king);
                    a.setLimitedLife(20 * 40);
                    a.addEffect(new MobEffectInstance(MobEffects.GLOWING, 20 * 40, 0));
                    a.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 20 * 40, 2));
                    KingSouls.spawned(a, "歪められた天使", ChatFormatting.WHITE);
                    sl.addFreshEntity(a);
                }
            }
            for (int i = 0; i < 2; i++) {
                Phantom p = EntityType.PHANTOM.create(sl);
                if (p != null) {
                    p.moveTo(king.getX() + sl.random.nextGaussian() * 3, king.getY() + 8, king.getZ() + sl.random.nextGaussian() * 3, 0F, 0F);
                    p.setPhantomSize(4);
                    KingSouls.spawned(p, "黒き翼", ChatFormatting.DARK_GRAY);
                    sl.addFreshEntity(p);
                    KingDeeds.later(sl, 20 * 40, p::discard);
                }
            }
            sl.sendParticles(ParticleTypes.END_ROD, king.getX(), king.getY() + 3, king.getZ(), 80, 2, 2, 2, 0.1);
            sl.sendParticles(KingDeeds.BLACK, king.getX(), king.getY() + 3, king.getZ(), 80, 2, 2, 2, 0.1);
            KingDeeds.count(king, KingDeeds.HITS, "creation");
            KingDeeds.sound(sl, king.position(), SoundEvents.EVOKER_PREPARE_SUMMON, 3F, 0.5F);
        });
    }

    // ------------------------------------------------------------------------------------------------ special attacks

    /** 鎖縛: chains from him to every foe within sixteen blocks; they are dragged to him and bound, and tugged thrice. */
    static void chains(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.later(sl, w, () -> {
            for (LivingEntity v : KingForms.foes(king, sl, 16)) {
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 6));
                for (int k = 0; k < 3; k++) {
                    KingDeeds.later(sl, k * 10, () -> {
                        if (!v.isAlive() || !king.isAlive()) {
                            return;
                        }
                        KingDeeds.line(sl, KingDeeds.BLACK, v.getEyePosition(), king.getEyePosition(), 0.4);
                        Vec3 in = king.position().subtract(v.position());
                        v.setDeltaMovement(in.x * 0.18, 0.2, in.z * 0.18);
                        v.hurtMarked = true;
                        v.invulnerableTime = 0;
                        KingDeeds.hit(king, "chains", v, 8F, false);
                    });
                }
            }
            KingDeeds.sound(sl, king.position(), SoundEvents.CHAIN_BREAK, 3F, 0.6F);
        });
    }

    // ------------------------------------------------------------------------------------------------ the wrath of a god

    /** 星墜とし (Revelation 8:10-11): a great star, burning as a lamp, falls on his foes again and again; the star is called
     * Wormwood, and the waters are made bitter (poison and sickness on all). */
    static void wormwood(RoyalMob king, ServerLevel sl, int w) {
        KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：大いなる星よ、燈火のごとく燃えて墜ちよ。その名は苦よもぎ。", ChatFormatting.GOLD);
        KingDeeds.later(sl, w, () -> {
            List<Vec3> spots = new ArrayList<>();
            for (LivingEntity v : KingForms.foes(king, sl, 40)) {
                spots.add(v.position());
                spots.add(v.position().add(sl.random.nextGaussian() * 4, 0, sl.random.nextGaussian() * 4));
            }
            while (spots.size() < 12) {
                double a = sl.random.nextDouble() * Math.PI * 2, r = 4 + sl.random.nextDouble() * 20;
                spots.add(king.position().add(Math.cos(a) * r, 0, Math.sin(a) * r));
            }
            for (int i = 0; i < spots.size(); i++) {
                Vec3 s = spots.get(i);
                int delay = i * 5;
                KingDeeds.each(sl, delay, 10, 1, k -> {
                    Vec3 p = s.add(6 - k * 0.6, 30 - k * 3, 0);
                    sl.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 10, 0.4, 0.4, 0.4, 0.02);
                    sl.sendParticles(ParticleTypes.LAVA, p.x, p.y, p.z, 2, 0.3, 0.3, 0.3, 0);
                });
                KingDeeds.later(sl, delay + 11, () -> {
                    for (LivingEntity v : KingForms.foes(king, sl, 64)) {
                        if (v.position().distanceTo(s) <= 3.5 + v.getBbWidth() * 0.5) {
                            v.invulnerableTime = 0;
                            if (KingDeeds.hit(king, "wormwood", v, 30F, true)) {
                                v.igniteForSeconds(6);
                            }
                        }
                    }
                    sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, s.x, s.y + 0.5, s.z, 1, 0, 0, 0, 0);
                    KingDeeds.sound(sl, s, SoundEvents.GENERIC_EXPLODE.value(), 3F, 0.6F);
                });
            }
            KingDeeds.later(sl, spots.size() * 5 + 14, () -> {
                for (LivingEntity v : KingForms.foes(king, sl, 40)) {
                    v.addEffect(new MobEffectInstance(MobEffects.POISON, 200, 1));
                    v.addEffect(new MobEffectInstance(MobEffects.CONFUSION, 200, 0));
                    sl.sendParticles(ParticleTypes.WITCH, v.getX(), v.getY() + 1, v.getZ(), 20, 0.5, 0.8, 0.5, 0.02);
                }
            });
        });
    }

    /** 七つの鉢 (Revelation 16): the seven bowls of the wrath of God poured out one after another on every foe within forty
     * blocks: sores, the sea as blood, the rivers as blood, the scorching sun, darkness, the Euphrates (all drawn to
     * him), and the great earthquake with hail. */
    static void bowls(RoyalMob king, ServerLevel sl, int w) {
        String[] says = {"第一の鉢――悪しき腫物", "第二の鉢――海は死人の血のごとく", "第三の鉢――川と泉は血となれり", "第四の鉢――日は人を火にて焼く",
            "第五の鉢――その国は暗くなれり", "第六の鉢――大いなる川ユーフラテス", "第七の鉢――事すでに成れり。大いなる地震と雹"};
        for (int i = 0; i < 7; i++) {
            int bowl = i;
            KingDeeds.later(sl, w + i * 20, () -> {
                if (!king.isAlive()) {
                    return;
                }
                KingDeeds.KingCinemaSay.near(sl, king, "バアル＝ゼブル：" + says[bowl], ChatFormatting.DARK_RED);
                for (LivingEntity v : KingForms.foes(king, sl, 40)) {
                    v.invulnerableTime = 0;
                    switch (bowl) {
                        case 0 -> {
                            v.addEffect(new MobEffectInstance(MobEffects.WITHER, 200, 1));
                            KingDeeds.hit(king, "bowls", v, 6F, true);
                        }
                        case 1 -> {
                            sl.sendParticles(KingDeeds.CRIMSON, v.getX(), v.getY() + 1, v.getZ(), 60, 1.2, 1, 1.2, 0.05);
                            KingDeeds.hit(king, "bowls", v, 20F, true);
                        }
                        case 2 -> {
                            v.addEffect(new MobEffectInstance(MobEffects.POISON, 200, 1));
                            v.addEffect(new MobEffectInstance(MobEffects.HUNGER, 200, 2));
                            KingDeeds.hit(king, "bowls", v, 6F, true);
                        }
                        case 3 -> {
                            KingDeeds.line(sl, ParticleTypes.END_ROD, v.position().add(0, 20, 0), v.position(), 0.6);
                            v.igniteForSeconds(10);
                            KingDeeds.hit(king, "bowls", v, 15F, true);
                        }
                        case 4 -> {
                            v.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 160, 0));
                            v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 160, 0));
                            KingDeeds.count(king, KingDeeds.HITS, "bowls");
                        }
                        case 5 -> {
                            Vec3 in = king.position().subtract(v.position());
                            v.setDeltaMovement(in.x * 0.2, 0.4, in.z * 0.2);
                            v.hurtMarked = true;
                            v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2));
                            KingDeeds.count(king, KingDeeds.HITS, "bowls");
                        }
                        default -> {
                            v.setDeltaMovement(v.getDeltaMovement().add(0, 1.2, 0));
                            v.hurtMarked = true;
                            sl.sendParticles(ParticleTypes.ITEM_SNOWBALL, v.getX(), v.getY() + 3, v.getZ(), 40, 1.5, 1, 1.5, 0.1);
                            KingDeeds.hit(king, "bowls", v, 40F, true);
                        }
                    }
                }
                KingDeeds.sound(sl, king.position(), bowl == 6 ? SoundEvents.GENERIC_EXPLODE.value() : SoundEvents.ELDER_GUARDIAN_CURSE, 3F, 0.6F);
            });
        }
    }

    // ------------------------------------------------------------------------------------------------ the rest

    /** The summoning: the hero's guard, the broken one's errors, Baal Zebul's flies. */
    static void summon(RoyalMob king, ServerLevel sl, int w) {
        int phase = king.lifePhase();
        KingDeeds.later(sl, w, () -> {
            if (!king.isAlive()) {
                return;
            }
            if (phase <= 1) {
                KingForms.call(king, sl, RoyalRole.IMPERIAL, 3);
                KingDeeds.KingCinemaSay.near(sl, king, KingDeeds.who(king) + "：近衛よ、王の傍らに。", ChatFormatting.GOLD);
            } else if (phase == 2) {
                for (int i = 0; i < 5; i++) {
                    Endermite e = EntityType.ENDERMITE.create(sl);
                    if (e != null) {
                        e.moveTo(king.getX() + sl.random.nextGaussian() * 3, king.getY(), king.getZ() + sl.random.nextGaussian() * 3, 0F, 0F);
                        e.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 20 * 30, 4));
                        e.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 20 * 30, 2));
                        KingSouls.spawned(e, "ERROR", ChatFormatting.LIGHT_PURPLE);
                        sl.addFreshEntity(e);
                        if (king.getTarget() != null) {
                            e.setTarget(king.getTarget());
                        }
                        KingDeeds.later(sl, 20 * 30, e::discard);
                    }
                }
            } else {
                KingSouls.veil(king, sl, 1);
            }
            KingDeeds.count(king, KingDeeds.HITS, "summon");
        });
    }

    /** A leap at a far foe: he comes down beside it. */
    static void leapIn(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        KingDeeds.later(sl, w, () -> {
            Vec3 d = t.position().subtract(king.position());
            king.setDeltaMovement(d.x * 0.09, 1.3, d.z * 0.09);
            king.hurtMarked = true;
            KingDeeds.sound(sl, king.position(), SoundEvents.WIND_CHARGE_BURST.value(), 2F, 0.6F);
            KingDeeds.later(sl, 14, () -> {
                Vec3 to = t.position().subtract(KingDeeds.flat(d).scale(2 + king.getBbWidth()));
                if (king.isAlive() && sl.noCollision(king, king.getBoundingBox().move(to.subtract(king.position())))) {
                    king.teleportTo(to.x, to.y, to.z);
                }
                king.fallDistance = 0F;
                for (LivingEntity v : KingForms.foes(king, sl, 4 + king.getBbWidth() * 0.5)) {
                    v.invulnerableTime = 0;
                    if (KingDeeds.hit(king, "leapin", v, 12F, false)) {
                        KingDeeds.throwFrom(v, king.position(), 1.0, 0.5);
                    }
                }
                sl.sendParticles(ParticleTypes.EXPLOSION, king.getX(), king.getY(), king.getZ(), 2, 0.5, 0.1, 0.5, 0);
            });
        });
    }

    /** A step back and away from a foe close upon him, and a blow straight after (the bow's, the spear's, or a thrust). */
    static void backstep(RoyalMob king, ServerLevel sl, LivingEntity t, int w) {
        Vec3 away = KingDeeds.flat(king.position().subtract(t.position()));
        king.setDeltaMovement(away.x * 1.5, 0.45, away.z * 1.5);
        king.hurtMarked = true;
        sl.sendParticles(ParticleTypes.CLOUD, king.getX(), king.getY() + 0.2, king.getZ(), 12, 0.5, 0.1, 0.5, 0.03);
        KingDeeds.count(king, KingDeeds.HITS, "backstep");
        KingDeeds.later(sl, 8 + w, () -> counter(king, sl, t));
    }

    /** His counter after a step: one of his weapon's motions straight away, ready or not. */
    private static void counter(RoyalMob king, ServerLevel sl, LivingEntity t) {
        if (!king.isAlive() || !t.isAlive()) {
            return;
        }
        int weapon = KingArsenal.weapon(king, king.lifePhase());
        String id = switch (weapon) {
            case KingArsenal.SWORD -> "sword_thrust";
            case KingArsenal.BROKEN -> "broken_blink";
            case KingArsenal.CLUBS -> "clubs_throw";
            case KingArsenal.SCYTHE -> "scythe_hook";
            case KingArsenal.TWIN -> "twin_slide";
            case KingArsenal.SPEAR -> "spear_thrust";
            default -> "bow_quick";
        };
        KingArsenal.perform(king, sl, KingArsenal.move(id), t);
    }

    /**
     * When he is struck: the hero turns a blow from the front aside on his shield (seven tenths of it) and bashes back; any
     * of his forms may step to the side, or back, and answer at once.
     */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void reflex(LivingIncomingDamageEvent e) {
        if (!KingCourt.isKing(e.getEntity()) || !(e.getEntity().level() instanceof ServerLevel sl) || !(e.getSource().getEntity() instanceof LivingEntity by)) {
            return;
        }
        RoyalMob king = (RoyalMob) e.getEntity();
        int phase = king.lifePhase();
        if (phase < 1 || KingCinema.playing(king) || king.getPersistentData().getBoolean(KingForms.QUIET) || by == king) {
            return;
        }
        long now = sl.getGameTime();
        var d = king.getPersistentData();
        if (now < d.getLong("OrorKingReflexAt")) {
            return;
        }
        Vec3 to = KingDeeds.flat(by.position().subtract(king.position()));
        boolean front = to.dot(KingDeeds.flat(king.getLookAngle())) > 0.2;
        if (phase <= 2 && front && king.getOffhandItem().is(net.minecraft.world.item.Items.SHIELD) && sl.random.nextInt(4) == 0) {
            d.putLong("OrorKingReflexAt", now + 40);
            e.setAmount(e.getAmount() * 0.3F);
            TechniqueShow.send(king, "move:king_guard", 0, 2, 14, by.getId());
            KingDeeds.sound(sl, king.position(), SoundEvents.SHIELD_BLOCK, 2F, 0.8F);
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, king.getX() + to.x, king.getEyeY(), king.getZ() + to.z, 12, 0.3, 0.3, 0.3, 0.05);
            KingDeeds.count(king, KingDeeds.COUNT, "guard");
            KingDeeds.later(sl, 6, () -> KingArsenal.perform(king, sl, KingArsenal.move("sword_bash"), by));
            return;
        }
        int roll = sl.random.nextInt(10);
        if (roll == 0) {
            d.putLong("OrorKingReflexAt", now + 60);
            TechniqueShow.send(king, "move:king_backstep", 0, 2, 16, by.getId());
            backstep(king, sl, by, 0);
        } else if (roll == 1) {
            d.putLong("OrorKingReflexAt", now + 60);
            Vec3 side = new Vec3(-to.z, 0, to.x).scale(sl.random.nextBoolean() ? 1 : -1);
            king.setDeltaMovement(side.x * 1.4, 0.3, side.z * 1.4);
            king.hurtMarked = true;
            TechniqueShow.send(king, "move:king_sidestep", 0, 2, 12, by.getId());
            sl.sendParticles(ParticleTypes.CLOUD, king.getX(), king.getY() + 0.2, king.getZ(), 10, 0.4, 0.1, 0.4, 0.02);
            KingDeeds.count(king, KingDeeds.COUNT, "sidestep");
            KingDeeds.later(sl, 8, () -> counter(king, sl, by));
        }
    }

    /** For the record: a line to all near (the speaker's name by his form). */
    static void say(ServerLevel sl, RoyalMob king, String line, ChatFormatting style) {
        KingDeeds.KingCinemaSay.near(sl, king, KingDeeds.who(king) + "：" + line, style);
    }

    static void tell(ServerPlayer p, String line) {
        p.displayClientMessage(Component.literal(line), true);
    }
}
