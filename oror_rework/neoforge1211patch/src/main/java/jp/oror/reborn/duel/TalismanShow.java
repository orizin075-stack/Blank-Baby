package jp.oror.reborn.duel;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ItemParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * (r71, the user: "お札MODに動作の画像とかそこら辺のデバッグ") Duel Dominion's talismans worked (CI's duel check) but showed
 * almost nothing when cast: a few faint motes, the chat line, an effect icon. Seen in the real client (the look run's
 * frames d30-d39), a cast could not be told from nothing. Now each cast is seen: torn paper of its own talisman flies up
 * from the caster's hands, two rings of its colour turn about the caster, and a talisman cast on a foe draws a line of
 * its colour to the foe and bursts about it; a bell rings, deeper for the forbidden Calamity. Only the look: what each
 * talisman does is Duel Dominion's own.
 */
public final class TalismanShow {
    private static final Map<UUID, Long> LAST = new HashMap<>();
    public static int shown;

    private TalismanShow() {
    }

    /** The talisman's colour, after its paper's colour band (tools/dueldominion/textures.py). */
    static Vector3f colour(String talisman) {
        int rgb = switch (talisman) {
            case "HEALING" -> 0x47c46a;
            case "RETRIBUTION" -> 0xe0503a;
            case "GUARDIAN" -> 0xe2b54a;
            case "BINDING" -> 0x5a6ee0;
            case "MALICE_TRANSFER" -> 0xd45a9a;
            case "SOUL_SEEKER" -> 0x3fc8e8;
            case "EXORCISM" -> 0xf08a2a;
            case "NIGHT_PARADE" -> 0x4a4fa8;
            case "REVIVAL" -> 0x3fbfa0;
            case "CALAMITY" -> 0x7a0f12;
            default -> 0xffffff;
        };
        return new Vector3f(((rgb >> 16) & 255) / 255F, ((rgb >> 8) & 255) / 255F, (rgb & 255) / 255F);
    }

    public static void cast(ServerPlayer p, String talisman, LivingEntity target) {
        ServerLevel level = p.serverLevel();
        long now = level.getGameTime();
        Long last = LAST.put(p.getUUID(), now);
        if (last != null && last == now) {
            return;
        }
        shown++;
        DustParticleOptions dust = new DustParticleOptions(colour(talisman), 1.4F);
        Vec3 at = p.position();
        // two rings turning about the caster, at the waist and the shoulders
        for (int ring = 0; ring < 2; ring++) {
            double y = at.y + 0.5 + ring * 0.8, r = 1.1 + ring * 0.25;
            for (int i = 0; i < 28; i++) {
                double a = Math.PI * 2 * i / 28 + ring * 0.11;
                level.sendParticles(dust, at.x + Math.cos(a) * r, y, at.z + Math.sin(a) * r, 1, 0, 0.02, 0, 0);
            }
        }
        // the talisman's paper torn and flying up from the hands
        ItemStack paper = new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath("dueldominion", "ofuda_" + talisman.toLowerCase(java.util.Locale.ROOT))));
        if (!paper.isEmpty()) {
            Vec3 hand = p.getEyePosition().add(p.getLookAngle().scale(0.6)).add(0, -0.4, 0);
            level.sendParticles(new ItemParticleOption(ParticleTypes.ITEM, paper), hand.x, hand.y, hand.z, 18, 0.15, 0.15, 0.15, 0.12);
        }
        level.sendParticles(talisman.equals("CALAMITY") ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.ENCHANT, at.x, at.y + 1.1, at.z, 40, 0.6, 0.8, 0.6, 0.6);
        if (target != null && target.isAlive()) {
            Vec3 from = p.getEyePosition().add(0, -0.3, 0), to = target.position().add(0, target.getBbHeight() * 0.6, 0);
            double d = from.distanceTo(to);
            for (int i = 0; i <= (int) (d * 4); i++) {
                Vec3 q = from.lerp(to, i / Math.max(1.0, d * 4));
                level.sendParticles(dust, q.x, q.y, q.z, 1, 0, 0, 0, 0);
            }
            level.sendParticles(dust, to.x, to.y, to.z, 30, 0.4, 0.5, 0.4, 0);
            level.sendParticles(ParticleTypes.WITCH, to.x, to.y, to.z, 12, 0.3, 0.4, 0.3, 0.05);
        }
        level.playSound(null, at.x, at.y, at.z, SoundEvents.BELL_RESONATE, SoundSource.PLAYERS, 0.5F, talisman.equals("CALAMITY") ? 0.5F : 1.4F);
        level.playSound(null, at.x, at.y, at.z, SoundEvents.EVOKER_CAST_SPELL, SoundSource.PLAYERS, 0.6F, 1.3F);
    }

    // --------------------------------------------------------------------------------- the blow an effigy shouldered

    private record Shouldered(long tick, float amount) {
    }

    private static final Map<UUID, Shouldered> SHOULDERED = new HashMap<>();

    /** (DuelRetributionMixin) A blow at the player an effigy is about to take on itself, before it does. */
    public static void shouldering(ServerPlayer p, float amount) {
        long now = p.serverLevel().getGameTime();
        Shouldered was = SHOULDERED.get(p.getUUID());
        SHOULDERED.put(p.getUUID(), new Shouldered(now, was != null && was.tick() == now ? Math.max(was.amount(), amount) : amount));
    }

    /** The blow an effigy took this tick for the player (0 if none): what Retribution answers when nothing got through. */
    public static float shouldered(net.minecraft.world.entity.LivingEntity e) {
        Shouldered rec = SHOULDERED.get(e.getUUID());
        return rec == null || rec.tick() != e.level().getGameTime() ? 0F : rec.amount();
    }
}
