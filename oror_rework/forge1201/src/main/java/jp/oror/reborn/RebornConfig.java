package jp.oror.reborn;

import net.minecraftforge.common.ForgeConfigSpec;
import net.minecraftforge.common.ForgeConfigSpec.BooleanValue;
import net.minecraftforge.common.ForgeConfigSpec.Builder;
import net.minecraftforge.common.ForgeConfigSpec.ConfigValue;
import net.minecraftforge.common.ForgeConfigSpec.DoubleValue;
import net.minecraftforge.common.ForgeConfigSpec.IntValue;

public final class RebornConfig {
    private static final Builder B = new Builder();
    public static final BooleanValue LORE = B.comment("Unlimited thematic revivals, with engine ceilings.").define("loreMode", true);
    public static final BooleanValue TERRAIN = B.comment("Bounded alchemy, also requires mobGriefing.").define("terrainChanges", false);
    public static final BooleanValue NATURAL = B.define("naturalEncounters", true);
    public static final IntValue MAX_SUMMONS = B.defineInRange("summonsPerCreator", 6, 0, 16);
    public static final IntValue LEVEL_SUMMONS = B.defineInRange("summonsPerLevel", 96, 0, 256);
    public static final IntValue REVIVALS = B.defineInRange("balancedRevivalLimit", 2, 0, 16);
    public static final IntValue BLOCK_BUDGET = B.defineInRange("blocksPerAbility", 24, 0, 128);
    public static final IntValue ENCOUNTER_INTERVAL = B.defineInRange("encounterIntervalTicks", 12000, 1200, 72000);
    public static final DoubleValue DAMAGE = B.defineInRange("damageMultiplier", 1.0, 0.05, 100.0);
    public static final BooleanValue SMART_MOBS = B.comment("Persistent combat, memory and growth for all mobs.").define("smartMobs", true);
    public static final BooleanValue ARMED_VILLAGERS = B.define("armedVillagers", true);
    public static final BooleanValue AI_TERRAIN = B.comment("One safe terrain action per mob per 40 ticks; respects mobGriefing.").define("aiTerrain", true);
    public static final BooleanValue ONLINE_AI = B.comment("Server-only API; no key means local dialogue.").define("onlineAi", true);
    public static final IntValue AI_REQUESTS = B.defineInRange("aiRequestsPerHour", 16, 0, 1000);
    public static final IntValue CHAT_COOLDOWN = B.defineInRange("chatCooldownSeconds", 3, 1, 3600);
    public static final ConfigValue<String> AI_MODEL = B.define("aiModel", "gpt-5.4-mini");
    public static final BooleanValue TUKUYO = B.define("tukuyo", true);
    public static final ConfigValue<String> TUKUYO_ENDPOINT = B.define("tukuyoEndpoint", "http://127.0.0.1:8022/v1/mind");
    public static final BooleanValue MOB_LEVELS = B.define("mobLevels", true);
    public static final BooleanValue MINERS = B.define("miningVillagers", true);
    public static final BooleanValue AUTO_RESEARCH = B.comment("Nearby NPCs may research combat once per Minecraft day, within the shared API budget.")
        .define("autonomousResearch", true);
    public static final DoubleValue ELITE_CHANCE = B.comment("One persistent level-6 lottery per individual, default one in 2000.")
        .defineInRange("level6Chance", 5.0E-4, 0.0, 1.0);
    public static final IntValue MINER_RANGE = B.defineInRange("minerRange", 16, 4, 24);
    public static final IntValue MINER_DEPTH = B.defineInRange("minerDepth", 16, 2, 32);
    public static final BooleanValue ROLES = B.define("villagerRoles", true);
    public static final BooleanValue LEVEL_REWARDS = B.define("levelRewards", true);
    public static final BooleanValue AURAS = B.define("levelAuras", true);
    public static final BooleanValue DIVINE_DOMAINS = B.define("divineDomains", true);
    public static final BooleanValue DIALOGUE_ARCHIVE = B.define("dialogueArchive", true);
    public static final BooleanValue LOCAL_AI = B.define("localGenerativeAi", true);
    public static final IntValue CHAT_CHARS = B.defineInRange("chatCharacters", 2048, 500, 8192);
    public static final IntValue REPLY_CHARS = B.defineInRange("replyCharacters", 1024, 240, 4096);
    public static final IntValue COMBAT_BUDGET = B.defineInRange("combatDecisionsPerTick", 256, 32, 4096);
    public static final IntValue LOCAL_REQUESTS = B.defineInRange("localAiRequestsPerHour", 600, 0, 10000);
    public static final ConfigValue<String> LOCAL_AI_ENDPOINT = B.define("localAiEndpoint", "http://127.0.0.1:8023/v1/responses");
    public static final BooleanValue VILLAGE_SCORE = B.define("villageReputation", true);
    public static final BooleanValue VILLAGE_LIFE = B.define("villagerCivilization", true);
    public static final BooleanValue HUMAN_VILLAGERS = B.define("humanVillagerModels", true);
    public static final BooleanValue COOPERATION = B.define("mobCooperation", true);
    public static final BooleanValue EXTRA_ABILITIES = B.define("extraCharacterAbilities", true);
    public static final BooleanValue MOD_EQUIPMENT = B.define("modEquipmentUse", true);
    public static final IntValue VILLAGE_BUDGET = B.defineInRange("villageActionsPerTick", 16, 1, 128);
    public static final ForgeConfigSpec SPEC = B.build();
}
