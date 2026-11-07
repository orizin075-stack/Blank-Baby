package jp.oror.reborn.royal;

import jp.oror.reborn.show.TechniqueShow;

/**
 * (054) Which of the villager king's four looks is on him this frame (client side): his form (RoyalMob.lifePhase:
 * 0 the regal villager king, 1 the hero, 2 the broken one, 3 Baal Zebul), but during a return from death the look
 * changes in the course of its show (KingCinema, TechniqueShow "move:king_revive_*"): the hero rises out of the old
 * king when the light comes down on him; the broken one flickers between the hero and his ruin; the god is first
 * the broken shell, then flickers through as the shell falls away.
 */
public final class KingLook {
    public static final String[] RIGS = {"villager_king_regal", "villager_king_hero", "villager_king_broken", "villager_king_divine"};

    private KingLook() {
    }

    /** The revival show under way on him, or null. */
    public static TechniqueShow.Active revive(RoyalMob mob) {
        TechniqueShow.Active a = TechniqueShow.ACTIVE.get(mob.getId());
        return a != null && a.mechanic().startsWith("MOVE_KING_REVIVE_") ? a : null;
    }

    /** How far through a show it is, 0..1 (may run past either end). */
    public static float progress(RoyalMob mob, TechniqueShow.Active a, float partial) {
        return (mob.level().getGameTime() - a.start() + partial) / Math.max(1, a.length());
    }

    public static int hash(int a, int b) {
        int h = a * 0x27d4eb2d ^ b * 0x165667b1;
        h ^= h >>> 15;
        h *= 0x2c1b3c6d;
        h ^= h >>> 12;
        return h & 0x7fffffff;
    }

    /** His look this frame: 0 regal, 1 hero, 2 broken, 3 divine. */
    public static int form(RoyalMob mob, float partial) {
        int phase = Math.max(0, Math.min(3, mob.lifePhase()));
        TechniqueShow.Active a = revive(mob);
        if (a == null) {
            return phase;
        }
        float u = progress(mob, a, partial);
        if (u < 0F || u > 1F) {
            return phase;
        }
        int flick = hash(mob.getId(), (int) (mob.level().getGameTime() / 2));
        return switch (a.mechanic()) {
            case "MOVE_KING_REVIVE_HERO" -> u < 0.45F ? 0 : u < 0.5F ? (flick % 2 == 0 ? 0 : 1) : 1;
            case "MOVE_KING_REVIVE_GLITCH" -> u < 0.85F ? (flick % 3 == 0 ? 1 : 2) : 2;
            case "MOVE_KING_REVIVE_DIVINE" -> u < 0.3F ? 2 : u < 0.42F ? (flick % 2 == 0 ? 2 : 3) : 3;
            default -> phase;
        };
    }

    /** How broken the broken king is, 0 (whole) to 1 (nearly dead): the stages of his ruin follow it. */
    public static float ruin(RoyalMob mob) {
        float hp = mob.getHealth() / Math.max(1F, mob.getMaxHealth());
        return Math.max(0F, Math.min(1F, 1F - hp));
    }
}
