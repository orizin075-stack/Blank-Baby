package jp.oror.reborn;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

public final class CombatMemory {
    private final LinkedHashMap<String, Integer> data = new LinkedHashMap<>();

    public int count(String s) {
        return this.data.getOrDefault(s, 0);
    }

    public void observe(String s) {
        this.restore(s, this.count(s) + 1);
    }

    public void restore(String s, int n) {
        if (!this.data.containsKey(s) && this.data.size() >= 128) {
            this.data.remove(this.data.keySet().iterator().next());
        }

        this.data.put(s, Integer.valueOf(Math.max(0, Math.min(64, n))));
    }

    public Map<String, Integer> entries() {
        return Collections.unmodifiableMap(this.data);
    }

    public static float resistance(int n) {
        return Math.max(0.08F, (float)Math.pow(0.68, (double)Math.max(0, n)));
    }

    public static int boundedEvolution(int n) {
        return Math.max(0, Math.min(1000, n));
    }
}
