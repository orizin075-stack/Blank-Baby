package jp.oror.reborn.raid;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * (059e) The raid health of the 41 gods: the user's V20 table (design/v20/hp_41.csv, "レイド戦用目標実効HP"), the god's
 * own health times 10 to 100. Generated from the table; a god not in it has no raid.
 */
public final class RaidTable {
    public record Entry(String id, float health, int times) {
    }

    public static final Map<String, Entry> ALL = new LinkedHashMap<>();

    static {
        put("kokuhaku", 30720F, 30);
        put("riha", 16000F, 20);
        put("tenki", 30720F, 30);
        put("chaos", 51200F, 50);
        put("berit", 18750F, 25);
        put("elseria", 21000F, 30);
        put("valeria", 14300F, 22);
        put("huang_linghua", 46080F, 45);
        put("ferdinand", 9000F, 15);
        put("mels", 12000F, 12);
        put("hephaistos", 46080F, 45);
        put("nortia", 16000F, 20);
        put("lucifara", 28500F, 30);
        put("taika", 51200F, 50);
        put("mary_sue", 38250F, 45);
        put("savior", 32000F, 40);
        put("gokuka", 29250F, 30);
        put("merlinus", 22500F, 30);
        put("enkou", 51200F, 50);
        put("kurma", 10240F, 10);
        put("teia", 26250F, 35);
        put("bahamut", 61440F, 60);
        put("nun", 24750F, 30);
        put("arcana", 18750F, 25);
        put("eomaia", 51200F, 50);
        put("demiurgos", 81920F, 80);
        put("hakyoku", 61440F, 60);
        put("shinra", 30720F, 30);
        put("ain_sof_aur", 81920F, 80);
        put("angra_mainyu", 60000F, 60);
        put("magna_mater", 51200F, 50);
        put("ouroboros", 14250F, 15);
        put("yggdrasil", 61440F, 60);
        put("miyohime", 102400F, 100);
        put("innocence", 102400F, 100);
        put("brutality", 66560F, 65);
        put("cursed_love", 46080F, 45);
        put("relentless_research", 51200F, 50);
        put("forbidden_arcana", 61440F, 60);
        put("fallen_savior", 71680F, 70);
        put("sweet_pact", 30720F, 30);
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
