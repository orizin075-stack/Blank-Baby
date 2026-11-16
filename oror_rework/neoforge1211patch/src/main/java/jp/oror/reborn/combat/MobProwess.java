package jp.oror.reborn.combat;

import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.neoforged.neoforge.common.Tags;

/**
 * (059h) The user: "強くてレベル高いモブ程経験積んでるからうまいし　スタミナも多めで　一定にしないで". How good a mob is at
 * dodging, and how deep its stamina, is not fixed by what kind of mob it is: it is its prowess, from 0 (a fresh zombie)
 * to 1 (a god), made of
 * <ul>
 * <li>its level (MobLevels: 1 to 5 by the experience it has fought for and how long it has lived, an elite above), 30%;</li>
 * <li>the experience itself (MobMind's, up to 16,000), 15%;</li>
 * <li>how strong it is: its health (20 to 20,000, by halvings) 20%, its blow (3 to 190) 10%;</li>
 * <li>its tactics (MobMind's skill) 10%, and what it has learnt dodging: every blow or shot it has met, dodged or not,
 * up to 500, 10%;</li>
 * <li>and what it is: a god +0.4, the King +0.4, a general +0.3, the bodyguards and the imperial guard +0.2, the sages and
 * archmages +0.15, the guards and mages +0.1, a boss +0.25.</li>
 * </ul>
 * And each mob is born with its own gift (from its UUID, for good): its dodging from 0.8 to 1.25 times as good, its
 * stamina from 0.85 to 1.2 times as deep. Two zombies of a level are not alike.
 */
public final class MobProwess {
    private MobProwess() {
    }

    private record Known(float prowess, long at) {
    }

    private static final Map<Mob, Known> KNOWN = new WeakHashMap<>();

    /** Its prowess, 0 to 1 (worked out again every five seconds). */
    public static float of(Mob m) {
        long now = m.level().getGameTime();
        Known k = KNOWN.get(m);
        if (k != null && now - k.at() < 100) {
            return k.prowess();
        }
        float p = work(m);
        KNOWN.put(m, new Known(p, now));
        return p;
    }

    private static float work(Mob m) {
        float level = 0F, experience = 0F, tactics = 0F;
        try {
            level = Mth.clamp((jp.oror.reborn.MobLevels.level(m) - 1) / 5F, 0F, 1F);
            CompoundTag mind = jp.oror.reborn.MobMind.data(m);
            experience = (float) Mth.clamp(Math.log1p(Math.max(0L, mind.getLong("Experience")) / 40.0) / Math.log1p(16000 / 40.0), 0, 1);
            tactics = (float) Mth.clamp(Math.log1p(jp.oror.reborn.MobMind.skill(m, "tactics") / 10.0) / Math.log1p(1000 / 10.0), 0, 1);
        } catch (RuntimeException | LinkageError ex) {
            // the mod's levels and minds are off or out of reach: by its strength and what it is alone
        }
        double hp = m.getAttribute(Attributes.MAX_HEALTH) == null ? 20 : m.getMaxHealth();
        float health = (float) Mth.clamp(Math.log(Math.max(1, hp) / 20.0) / Math.log(2) / 10.0, 0, 1);
        double atk = m.getAttributes().hasAttribute(Attributes.ATTACK_DAMAGE) ? m.getAttributeValue(Attributes.ATTACK_DAMAGE) : 2;
        float blow = (float) Mth.clamp(Math.log(Math.max(0.5, atk) / 3.0) / Math.log(2) / 6.0, 0, 1);
        float learnt = (float) Mth.clamp(Math.log1p(m.getPersistentData().getInt("OrorDodgeXp") / 20.0) / Math.log1p(500 / 20.0), 0, 1);
        float bonus = 0F;
        if (m instanceof SupremeEntity) {
            bonus = 0.4F;
        } else if (m instanceof RoyalMob r && r.role() != null) {
            RoyalRole role = r.role();
            bonus = switch (role) {
                case KING -> 0.4F;
                case GENERAL -> 0.3F;
                case BODYGUARD, IMPERIAL -> 0.2F;
                case SAGE, ARCHMAGE -> 0.15F;
                default -> 0.1F;
            };
        } else if (m.getType().is(Tags.EntityTypes.BOSSES)) {
            bonus = 0.25F;
        }
        return Mth.clamp(0.30F * level + 0.15F * experience + 0.20F * health + 0.10F * blow + 0.10F * tactics + 0.10F * learnt + bonus, 0F, 1F);
    }

    /** Its gift at dodging, 0.8 to 1.25, its own for good. */
    public static float gift(Mob m) {
        long bits = m.getUUID().getLeastSignificantBits() ^ m.getUUID().getMostSignificantBits() * 31;
        return 0.8F + 0.45F * ((bits & 0xFFFF) / 65535F);
    }

    /** Its gift of stamina, 0.85 to 1.2, its own for good. */
    public static float wind(Mob m) {
        long bits = m.getUUID().getMostSignificantBits() ^ m.getUUID().getLeastSignificantBits() * 17;
        return 0.85F + 0.35F * (((bits >>> 20) & 0xFFFF) / 65535F);
    }

    /** Something learnt: a blow or a shot met (dodged or not). */
    static void learn(Mob m) {
        CompoundTag d = m.getPersistentData();
        d.putInt("OrorDodgeXp", Math.min(100000, d.getInt("OrorDodgeXp") + 1));
    }

    static float lerp(float p, float a, float b) {
        return a + (b - a) * p;
    }

    /** For the checks: its prowess and gifts. */
    public static String describe(Mob m) {
        return String.format(java.util.Locale.ROOT, "prowess %.2f gift %.2f wind %.2f", of(m), gift(m), wind(m));
    }
}
