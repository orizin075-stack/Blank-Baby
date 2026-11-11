package jp.oror.reborn.safety;

import it.unimi.dsi.fastutil.longs.LongSet;
import java.util.function.LongPredicate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (058) The server no longer dies when something changes the list of chunks whose entities are leaving while that
 * list is being walked.
 *
 * <p>Vanilla walks the set of chunks to unload with {@code removeIf}, and for each takes its entities out of the world.
 * Taking an entity out tells every mod that listens (its vehicle lets its riders go, its owner's things are cleared,
 * whatever a mod does when its mob leaves), and if any of that loads a chunk or lets one go, the set being walked
 * changes under the walk. fastutil's iterator then reads past its end: "Exception ticking world", a
 * NullPointerException or IndexOutOfBoundsException in LongOpenHashSet$SetIterator.nextLong under
 * PersistentEntitySectionManager.processUnloads. The look runs met it three times while the capital's mobs unloaded
 * (Nov 1, Nov 2, Nov 11), with OROR's own unload handler doing nothing of the kind: whichever mod does it, the walk is
 * now over a copy, and each chunk is looked at again before it is handled.</p>
 */
public final class EntityUnloads {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Safety");
    private static boolean walking, said;
    /** How many walks, how many times the set changed under one, how many re-entries were caught in the act. */
    public static long walks, changed, reentries;

    private EntityUnloads() {
    }

    /** {@code set.removeIf(each)}, safe against the set changing while {@code each} runs. */
    public static boolean safely(LongSet set, LongPredicate each) {
        if (!said) {
            said = true;
            LOG.info("OROR SAFE-UNLOAD active: entity chunks unload from a copy of their list");
        }
        if (set.isEmpty()) {
            return false;
        }
        walks++;
        long[] copy = set.toLongArray();
        boolean any = false;
        boolean was = walking;
        walking = true;
        try {
            for (long pos : copy) {
                int before = set.size();
                // gone from the set meanwhile (its chunk came back): nothing to do for it now
                if (!set.contains(pos)) {
                    continue;
                }
                boolean done = each.test(pos);
                if (set.size() != before) {
                    changed++;
                }
                if (done) {
                    set.remove(pos);
                    any = true;
                }
            }
        } finally {
            walking = was;
        }
        return any;
    }

    /** Called when a chunk's entity status changes: inside a walk, this is what used to kill the server. */
    public static void statusChanged() {
        if (walking) {
            reentries++;
            if (reentries <= 3) {
                LOG.warn("OROR SAFE-UNLOAD: a chunk's status changed while entities were unloading (this crashed the server before); "
                    + "who did it:", new Throwable("re-entry " + reentries));
            }
        }
    }

    public static String report() {
        return "walks=" + walks + " changedUnderWalk=" + changed + " reentries=" + reentries + " active=" + said;
    }
}
