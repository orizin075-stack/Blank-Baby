package jp.oror.reborn.royal;

import io.redspace.ironsspellbooks.api.spells.SpellData;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * (053) The spells the kingdom's people cast. They had every spell of every school registered (RoyalSpells.catalog):
 * the add-on's too (Geomancy Plus) and Iron's own that are made for a player's hand (a portal, recall, telekinesis, a
 * spectral hammer...), and a guard casting one crashed the game (the user). Now only Iron's own spells for a fight,
 * of the kind Iron's own spellcasters use, are theirs. The list is checked in the CI by casting each of the old
 * catalogue's spells in turn (/oror spells test); a royal that still fails in its tick is taken away rather than the
 * game stopping (CrashNet). Not Arrow Volley: a dozen arrows a cast, left lying where they fell (346 of them on the
 * field of the third 053 CI's hundred-man battle, a load of their own).
 */
public final class RoyalSpellSafety {
    /** Iron's Spells' fighting spells (their ids' paths), as its own spellcasting mobs use such spells. */
    public static final Set<String> FIGHTING = Set.of(
        // fire
        "firebolt", "fireball", "fire_breath", "blaze_storm", "magma_bomb", "scorch", "wall_of_fire", "heat_surge", "flaming_strike",
        "flaming_barrage",
        // ice
        "icicle", "frostbolt", "cone_of_cold", "ray_of_frost", "ice_block", "frostwave", "ice_spikes", "summon_polar_bear",
        // lightning
        "lightning_bolt", "chain_lightning", "lightning_lance", "electrocute", "ball_lightning", "shockwave", "charge",
        // holy
        "heal", "greater_heal", "healing_circle", "fortify", "blessing_of_life", "guiding_bolt", "wisp", "sunbeam", "cloud_of_regeneration",
        "haste",
        // ender
        "magic_missile", "magic_arrow", "starfall", "dragon_breath", "counterspell",
        // blood
        "blood_slash", "wither_skull", "ray_of_siphoning", "devour", "blood_needles", "acupuncture", "raise_dead", "heartstop",
        // evocation
        "fang_strike", "fang_ward", "summon_vex", "shield", "firecracker", "lob_creeper", "chain_creeper", "gust", "slow",
        // nature
        "poison_arrow", "poison_splash", "poison_breath", "acid_orb", "root", "stomp", "blight", "oakskin", "firefly_swarm",
        // eldritch
        "sculk_tentacles", "sonic_boom", "eldritch_blast", "abyssal_shroud");

    private static final ThreadLocal<Boolean> WHOLE = ThreadLocal.withInitial(() -> Boolean.FALSE);
    private static final Map<List<SpellData>, List<SpellData>> FILTERED = new IdentityHashMap<>();

    private RoyalSpellSafety() {
    }

    public static boolean allowed(SpellData d) {
        String id = d.getSpell().getSpellId();
        return id.startsWith("irons_spellbooks:") && FIGHTING.contains(d.getSpell().getSpellResource().getPath());
    }

    /** The catalogue as the royals now have it (the whole one while the CI's sweep asks for it). */
    public static synchronized List<SpellData> filter(List<SpellData> whole) {
        if (whole == null || WHOLE.get()) {
            return whole;
        }
        List<SpellData> kept = FILTERED.get(whole);
        if (kept == null) {
            List<SpellData> k = new ArrayList<>();
            for (SpellData d : whole) {
                if (allowed(d)) {
                    k.add(d);
                }
            }
            kept = List.copyOf(k);
            FILTERED.put(whole, kept);
        }
        return kept;
    }

    /** Runs with the whole old catalogue in place (the CI's sweep). */
    public static <T> T whole(java.util.function.Supplier<T> body) {
        WHOLE.set(Boolean.TRUE);
        try {
            return body.get();
        } finally {
            WHOLE.set(Boolean.FALSE);
        }
    }
}
