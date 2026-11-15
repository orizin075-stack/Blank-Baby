package jp.oror.reborn.raid;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * (059e) The raid health of the 41 gods: the user's V20 table (design/v20/hp_41.csv, "レイド戦用目標実効HP"), the god's
 * own health times 10 to 100. Generated from the table; a god not in it has no raid.
 * (059g, the user: "それぞれ１０００００ぐらいにして") every god's 100,000, as its health now is (GodStrength); the times are
 * kept: they rank the gods, and what their blows are multiplied by (ten to fifty) is read from them.
 */
public final class RaidTable {
    public record Entry(String id, float health, int times) {
    }

    public static final Map<String, Entry> ALL = new LinkedHashMap<>();

    static {
        put("kokuhaku", 100000F, 30);
        put("riha", 100000F, 20);
        put("tenki", 100000F, 30);
        put("chaos", 100000F, 50);
        put("berit", 100000F, 25);
        put("elseria", 100000F, 30);
        put("valeria", 100000F, 22);
        put("huang_linghua", 100000F, 45);
        put("ferdinand", 100000F, 15);
        put("mels", 100000F, 12);
        put("hephaistos", 100000F, 45);
        put("nortia", 100000F, 20);
        put("lucifara", 100000F, 30);
        put("taika", 100000F, 50);
        put("mary_sue", 100000F, 45);
        put("savior", 100000F, 40);
        put("gokuka", 100000F, 30);
        put("merlinus", 100000F, 30);
        put("enkou", 100000F, 50);
        put("kurma", 100000F, 10);
        put("teia", 100000F, 35);
        put("bahamut", 100000F, 60);
        put("nun", 100000F, 30);
        put("arcana", 100000F, 25);
        put("eomaia", 100000F, 50);
        put("demiurgos", 100000F, 80);
        put("hakyoku", 100000F, 60);
        put("shinra", 100000F, 30);
        put("ain_sof_aur", 100000F, 80);
        put("angra_mainyu", 100000F, 60);
        put("magna_mater", 100000F, 50);
        put("ouroboros", 100000F, 15);
        put("yggdrasil", 100000F, 60);
        put("miyohime", 100000F, 100);
        put("innocence", 100000F, 100);
        put("brutality", 100000F, 65);
        put("cursed_love", 100000F, 45);
        put("relentless_research", 100000F, 50);
        put("forbidden_arcana", 100000F, 60);
        put("fallen_savior", 100000F, 70);
        put("sweet_pact", 100000F, 30);
    }

    private RaidTable() {
    }

    private static void put(String id, float health, int times) {
        ALL.put(id, new Entry(id, health, times));
    }

    public static Entry of(String id) {
        return id == null ? null : ALL.get(id);
    }
}
