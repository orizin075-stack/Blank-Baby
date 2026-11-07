package jp.oror.reborn.king;

import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import org.joml.Vector3f;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The villager king's returns from death, each its own film (the user: every return's effects and film all
 * different; first a hero's form; then as if his texture had come off, glitched all over; last that falls away and he
 * is born again in a holy form). While one plays he is still (no mind of his own: his AI off) and nothing can hurt
 * him; its climax is a blow on all his foes about him, never weaker than his old returns'. Driven from his entity tick,
 * which goes on with his AI off. The players' screens get their part from TechniqueShow "move:king_revive_*"
 * (KingScreen, KingRig, KingLook).
 * <ul>
 * <li>The hero (5 s): golden motes drawn in while he kneels, a heartbeat; a pillar of light comes down on him and he
 * rises out of the old king's shape; the horn of a raid; three imperial guards kneel to him; a ring of golden light
 * bursts from him (12 blocks, 24).</li>
 * <li>The broken one (6 s): his shape jerks from place to place, magenta, cyan and black pixels and blocks of the
 * missing texture spill off him, the note of a broken chip at random pitches; those near him are thrown a block
 * aside twice, darkness falls; the bursting of hellfire and the missing texture (12 blocks, 30, burning) and two
 * archmages.</li>
 * <li>The god (8 s): the broken shell falls from him in pieces; a beam comes down from the heavens; he rises three
 * blocks with his halo and wings of light gathering; his true name; eight bolts round him, every foe within 24 blocks
 * struck (24) and thrown up, the flies loosed, the storm; he comes down.</li>
 * </ul>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingCinema {
    private static final Logger LOG = LoggerFactory.getLogger("OROR King");
    public static final String CINE = "OrorKingCine", AT = "OrorKingCineAt";
    private static final String NOAI = "OrorKingCineNoAi", INV = "OrorKingCineInv", AX = "OrorKingCineX", AY = "OrorKingCineY",
        AZ = "OrorKingCineZ";
    public static final int[] LENGTH = {0, 100, 120, 160};
    private static final String[] ID = {"", "hero", "glitch", "divine"};

    private KingCinema() {
    }

    public static boolean playing(LivingEntity e) {
        return e.getPersistentData().getInt(CINE) > 0;
    }

    /** Starts the film of his return into the given form (KingForms.reborn). */
    public static void start(RoyalMob king, ServerLevel sl, int phase) {
        phase = Mth.clamp(phase, 1, 3);
        CompoundTag d = king.getPersistentData();
        if (d.getInt(CINE) > 0) {
            finish(king, sl, false);
        }
        d.putInt(CINE, phase);
        d.putLong(AT, sl.getGameTime());
        d.putBoolean(NOAI, king.isNoAi());
        d.putBoolean(INV, king.isInvulnerable());
        d.putDouble(AX, king.getX());
        d.putDouble(AY, king.getY());
        d.putDouble(AZ, king.getZ());
        king.getNavigation().stop();
        king.setDeltaMovement(Vec3.ZERO);
        king.setNoAi(true);
        king.setInvulnerable(true);
        TechniqueShow.send(king, "move:king_revive_" + ID[phase], 0, LENGTH[phase] * 85 / 100, LENGTH[phase], -1);
        LOG.info("KING-CINEMA {\"phase\":{},\"film\":\"{}\",\"ticks\":{}}", phase, ID[phase], LENGTH[phase]);
    }

    private static void finish(RoyalMob king, ServerLevel sl, boolean whole) {
        CompoundTag d = king.getPersistentData();
        int phase = d.getInt(CINE);
        d.remove(CINE);
        king.setNoAi(d.getBoolean(NOAI));
        king.setInvulnerable(d.getBoolean(INV));
        if (d.contains(AX)) {
            king.teleportTo(d.getDouble(AX), d.getDouble(AY), d.getDouble(AZ));
        }
        king.fallDistance = 0F;
        d.putInt("OrorKingCinemas", d.getInt("OrorKingCinemas") + (whole ? 1 : 0));
        LOG.info("KING-CINEMA-END {\"phase\":{},\"whole\":{}}", phase, whole);
    }

    /** Nothing hurts him while his film plays (but the void and /kill). */
    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void untouchable(LivingIncomingDamageEvent e) {
        if (e.getEntity() instanceof RoyalMob m && playing(m) && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            e.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof RoyalMob king) || !(king.level() instanceof ServerLevel sl)) {
            return;
        }
        CompoundTag d = king.getPersistentData();
        int phase = d.getInt(CINE);
        if (phase <= 0) {
            return;
        }
        long t = sl.getGameTime() - d.getLong(AT);
        if (t < 0 || t >= LENGTH[Mth.clamp(phase, 1, 3)]) {
            finish(king, sl, t >= 0);
            return;
        }
        Vec3 home = new Vec3(d.getDouble(AX), d.getDouble(AY), d.getDouble(AZ));
        switch (phase) {
            case 1 -> hero(king, sl, (int) t, home);
            case 2 -> glitch(king, sl, (int) t, home);
            default -> divine(king, sl, (int) t, home);
        }
    }

    // ------------------------------------------------------------------------------------------------- helpers

    private static final DustParticleOptions GOLD = new DustParticleOptions(new Vector3f(1.0F, 0.82F, 0.25F), 1.6F);
    private static final DustParticleOptions WHITE = new DustParticleOptions(new Vector3f(1.0F, 0.98F, 0.9F), 1.8F);
    private static final DustParticleOptions MAGENTA = new DustParticleOptions(new Vector3f(1.0F, 0.0F, 1.0F), 1.4F);
    private static final DustParticleOptions CYAN = new DustParticleOptions(new Vector3f(0.0F, 1.0F, 1.0F), 1.4F);
    private static final DustParticleOptions BLACK = new DustParticleOptions(new Vector3f(0.02F, 0.02F, 0.02F), 1.6F);

    private static void sound(ServerLevel sl, Vec3 at, SoundEvent s, float vol, float pitch) {
        sl.playSound(null, at.x, at.y, at.z, s, SoundSource.HOSTILE, vol, pitch);
    }

    private static void title(ServerLevel sl, Vec3 at, Component title, Component sub, int stay) {
        for (ServerPlayer p : sl.players()) {
            if (p.distanceToSqr(at) < 96 * 96) {
                p.connection.send(new ClientboundSetTitlesAnimationPacket(8, stay, 16));
                p.connection.send(new ClientboundSetSubtitleTextPacket(sub));
                p.connection.send(new ClientboundSetTitleTextPacket(title));
            }
        }
    }

    private static void say(ServerLevel sl, Vec3 at, String line, ChatFormatting style) {
        for (ServerPlayer p : sl.players()) {
            if (p.distanceToSqr(at) < 256 * 256) {
                p.sendSystemMessage(Component.literal(line).withStyle(style));
            }
        }
    }

    private static void column(ServerLevel sl, ParticleOptions o, Vec3 at, double from, double to, double step) {
        for (double y = from; y < to; y += step) {
            sl.sendParticles(o, at.x, at.y + y, at.z, 1, 0.12, 0.05, 0.12, 0.0);
        }
    }

    private static void ring(ServerLevel sl, ParticleOptions o, Vec3 at, double r, double y, int n) {
        for (int i = 0; i < n; i++) {
            double a = 2 * Math.PI * i / n;
            sl.sendParticles(o, at.x + Math.cos(a) * r, at.y + y, at.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
        }
    }

    // ------------------------------------------------------------------------------------------------- the films

    private static void hero(RoyalMob king, ServerLevel sl, int t, Vec3 home) {
        king.teleportTo(home.x, home.y, home.z);
        double h = king.getBbHeight();
        if (t == 0) {
            say(sl, home, "村人王：……まだだ。王は、斃れぬ。", ChatFormatting.GOLD);
            sound(sl, home, SoundEvents.BEACON_ACTIVATE, 3F, 0.6F);
        }
        if (t < 40) {
            if (t % 10 == 0) {
                sound(sl, home, SoundEvents.WARDEN_HEARTBEAT, 2F, 1.3F);
            }
            if (t % 2 == 0) {
                double r = 7.0 * (1.0 - t / 40.0) + 0.5;
                for (int i = 0; i < 14; i++) {
                    double a = 2 * Math.PI * i / 14 + t * 0.15;
                    sl.sendParticles(GOLD, home.x + Math.cos(a) * r, home.y + 0.3 + (i % 4) * 0.7, home.z + Math.sin(a) * r, 1, 0, 0, 0, 0);
                }
                sl.sendParticles(ParticleTypes.WAX_ON, home.x, home.y + h * 0.5, home.z, 4, 0.4, h * 0.3, 0.4, 0.02);
            }
        }
        if (t == 20) {
            title(sl, home, Component.literal("英雄王、再臨").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD),
                Component.literal("「民よ、見よ。王はここに立つ！」").withStyle(ChatFormatting.YELLOW), 60);
        }
        if (t >= 40 && t < 62 && t % 2 == 0) {
            column(sl, ParticleTypes.END_ROD, home, 0, 34, 0.8);
            column(sl, GOLD, home, 0, 34, 1.4);
        }
        if (t == 45) {
            sound(sl, home, SoundEvents.TOTEM_USE, 3F, 0.9F);
            sl.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, home.x, home.y + h * 0.5, home.z, 120, 0.8, h * 0.4, 0.8, 0.6);
        }
        if (t == 60) {
            sound(sl, home, SoundEvents.RAID_HORN.value(), 4F, 1.2F);
            say(sl, home, "英雄王：我が剣は民のために。我が盾は王国のために。", ChatFormatting.GOLD);
        }
        if (t == 75) {
            KingForms.call(king, sl, RoyalRole.IMPERIAL, 3);
        }
        if (t >= 85 && t <= 95) {
            ring(sl, GOLD, home, 2.0 + (t - 85) * 1.0, 0.3, 48);
            ring(sl, ParticleTypes.END_ROD, home, 2.0 + (t - 85) * 1.0, 0.6, 24);
        }
        if (t == 85) {
            KingForms.burst(king, sl, 12.0, 24F, 1.8, false);
            KingForms.rally(king, sl);
            sl.sendParticles(ParticleTypes.EXPLOSION, home.x, home.y + 1, home.z, 8, 2, 0.5, 2, 0);
            sound(sl, home, SoundEvents.WARDEN_SONIC_BOOM, 3F, 1.2F);
            sound(sl, home, SoundEvents.PLAYER_LEVELUP, 2F, 0.6F);
        }
    }

    private static void glitch(RoyalMob king, ServerLevel sl, int t, Vec3 home) {
        double h = king.getBbHeight();
        var rnd = sl.random;
        if (t < 100 && t % 2 == 0) {
            king.teleportTo(home.x + (rnd.nextDouble() - 0.5) * 1.6, home.y + rnd.nextDouble() * 0.5, home.z + (rnd.nextDouble() - 0.5) * 1.6);
        } else if (t % 6 == 3 || t >= 100) {
            king.teleportTo(home.x, home.y, home.z);
        }
        if (t == 0) {
            say(sl, home, "村人王：ア、ア……王ハ……王ハ、" + KingForms.GARBLED_NAME.substring(0, 4) + "……", ChatFormatting.DARK_PURPLE);
            say(sl, home, "§k####§r " + KingForms.GARBLED_KING + " 0x0000F00D §k####", ChatFormatting.LIGHT_PURPLE);
            sound(sl, home, SoundEvents.GLASS_BREAK, 3F, 0.5F);
        }
        if (t == 10) {
            sound(sl, home, SoundEvents.ELDER_GUARDIAN_CURSE, 2F, 1.6F);
        }
        if (t < 100) {
            if (t % 3 == 0) {
                sound(sl, home, SoundEvents.NOTE_BLOCK_BIT.value(), 2F, 0.5F + rnd.nextFloat() * 1.5F);
            }
            for (DustParticleOptions o : new DustParticleOptions[]{MAGENTA, CYAN, BLACK}) {
                sl.sendParticles(o, home.x, home.y + h * 0.5, home.z, 8, 0.6, h * 0.4, 0.6, 0.05);
            }
            if (t % 6 == 0) {
                sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, (rnd.nextBoolean() ? Blocks.MAGENTA_CONCRETE : Blocks.BLACK_CONCRETE)
                    .defaultBlockState()), home.x, home.y + h * 0.6, home.z, 30, 0.7, h * 0.3, 0.7, 0.15);
            }
        }
        if (t == 20) {
            title(sl, home, Component.literal("譚台ｺｺ邇").withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.OBFUSCATED),
                Component.literal("ERROR 0x0000F00D: 王ハ 斃レ ヌ").withStyle(ChatFormatting.LIGHT_PURPLE), 70);
            for (LivingEntity f : KingForms.foes(king, sl, 32.0)) {
                f.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
            }
        }
        if (t == 40 || t == 70) {
            for (LivingEntity f : KingForms.foes(king, sl, 16.0)) {
                Vec3 to = f.position().add((rnd.nextDouble() - 0.5) * 2.4, 0, (rnd.nextDouble() - 0.5) * 2.4);
                if (sl.noCollision(f, f.getBoundingBox().move(to.subtract(f.position())))) {
                    f.teleportTo(to.x, to.y, to.z);
                }
            }
            sound(sl, home, SoundEvents.ENDERMAN_TELEPORT, 2F, 0.4F);
        }
        if (t == 100) {
            KingForms.burst(king, sl, 12.0, 30F, 1.2, true);
            sl.sendParticles(ParticleTypes.FLAME, home.x, home.y + 1, home.z, 300, 6, 1, 6, 0.08);
            for (DustParticleOptions o : new DustParticleOptions[]{MAGENTA, CYAN, BLACK}) {
                sl.sendParticles(o, home.x, home.y + 1, home.z, 200, 6, 1.2, 6, 0.1);
            }
            sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, home.x, home.y + 1, home.z, 1, 0, 0, 0, 0);
            sound(sl, home, SoundEvents.ENDERMAN_SCREAM, 3F, 0.5F);
            sound(sl, home, SoundEvents.DRAGON_FIREBALL_EXPLODE, 3F, 0.6F);
            KingForms.call(king, sl, RoyalRole.ARCHMAGE, 2);
        }
    }

    private static void divine(RoyalMob king, ServerLevel sl, int t, Vec3 home) {
        double h = king.getBbHeight();
        double lift = t < 50 ? 0 : t <= 120 ? 3.0 * smooth((t - 50) / 70.0) : t < 130 ? 3.0 : 3.0 * (1 - smooth((t - 130) / 30.0));
        king.teleportTo(home.x, home.y + lift, home.z);
        var rnd = sl.random;
        if (t == 0) {
            say(sl, home, "……壊れた殻が、剥がれ落ちていく。", ChatFormatting.GRAY);
            sound(sl, home, SoundEvents.AMETHYST_BLOCK_BREAK, 3F, 0.5F);
        }
        if (t < 40 && t % 2 == 0) {
            var block = switch (rnd.nextInt(5)) {
                case 0 -> Blocks.MAGENTA_CONCRETE;
                case 1 -> Blocks.BLACK_CONCRETE;
                case 2 -> Blocks.GOLD_BLOCK;
                case 3 -> Blocks.IRON_BLOCK;
                default -> Blocks.BLUE_WOOL;
            };
            sl.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, block.defaultBlockState()), home.x, home.y + h * 0.6, home.z, 14,
                0.7, h * 0.35, 0.7, 0.0);
            if (t % 4 == 0) {
                sound(sl, home, SoundEvents.GLASS_BREAK, 1.6F, 0.6F + rnd.nextFloat() * 0.8F);
            }
        }
        if (t == 40) {
            sl.setWeatherParameters(0, 6000, true, true);
            sound(sl, home, SoundEvents.BEACON_POWER_SELECT, 3F, 0.5F);
        }
        if (t >= 40 && t < 72 && t % 2 == 0) {
            double bottom = 44.0 - (t - 40) / 32.0 * 44.0;
            column(sl, ParticleTypes.END_ROD, home, bottom, 44, 0.7);
            column(sl, WHITE, home, bottom, 44, 1.2);
        }
        if (t >= 60 && t % 3 == 0) {
            Vec3 at = king.position();
            ring(sl, ParticleTypes.END_ROD, at, 1.2 + king.getScale() * 0.3, h + 0.6, 18);
            for (int s = -1; s <= 1; s += 2) {
                for (int i = 0; i < 10; i++) {
                    double u = i / 9.0;
                    sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, at.x + s * (1.0 + u * 5.0), at.y + h * 0.7 + Math.sin(u * Math.PI) * 2.2,
                        at.z + 0.8, 1, 0, 0, 0, 0);
                }
            }
        }
        if (t == 70 || t == 100) {
            sound(sl, home, SoundEvents.BELL_RESONATE, 3F, 1.5F);
            sound(sl, home, SoundEvents.AMETHYST_BLOCK_RESONATE, 3F, 0.8F);
        }
        if (t == 110) {
            title(sl, home, Component.literal(KingForms.TRUE_NAME).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD),
                Component.literal(KingForms.TRUE_TITLE).withStyle(ChatFormatting.YELLOW), 80);
            say(sl, home, "――我が真名を知れ。", ChatFormatting.DARK_PURPLE);
            say(sl, home, KingForms.TRUE_NAME + "：我は" + KingForms.TRUE_NAME + "。" + KingForms.TRUE_TITLE + "なり。", ChatFormatting.DARK_PURPLE);
            say(sl, home, KingForms.TRUE_NAME + "：雷よ、ヤグルシよ、アイムールよ。蝿どもよ。この者らを喰らえ。", ChatFormatting.DARK_PURPLE);
        }
        if (t == 130) {
            for (int i = 0; i < 8; i++) {
                double a = i * Math.PI / 4;
                KingForms.bolt(sl, home.add(Math.cos(a) * 7, 0, Math.sin(a) * 7));
            }
            for (LivingEntity f : KingForms.foes(king, sl, 24.0)) {
                f.hurt(king.damageSources().indirectMagic(king, king), 24F);
                KingForms.swarm(king, f, sl.getGameTime() + 100);
                f.setDeltaMovement(f.getDeltaMovement().add(0, 1.2, 0));
                f.hurtMarked = true;
            }
            KingForms.arm(king, 3);
            sl.sendParticles(ParticleTypes.END_ROD, home.x, home.y + 2, home.z, 240, 1.5, 2.0, 1.5, 0.5);
            sound(sl, home, SoundEvents.TOTEM_USE, 3F, 0.6F);
            sound(sl, home, SoundEvents.LIGHTNING_BOLT_THUNDER, 4F, 0.5F);
        }
    }

    private static double smooth(double t) {
        t = Math.max(0, Math.min(1, t));
        return t * t * (3 - 2 * t);
    }

    /** Whether a film is under way on this king (the CI's check). */
    public static int cinemas(RoyalMob king) {
        return king.getPersistentData().getInt("OrorKingCinemas");
    }

    static BlockPos at(RoyalMob king) {
        return king.blockPosition();
    }
}
