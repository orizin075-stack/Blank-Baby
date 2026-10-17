package jp.oror.reborn;

import com.google.gson.JsonObject;
import java.lang.reflect.Method;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.GameRules.BooleanValue;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class MindGameTests {
    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void epic_fight_reads_83_weapon_capabilities(GameTestHelper h) {
        try {
            Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
            Method get = caps.getMethod("getItemStackCapability", ItemStack.class);
            int count = 0;

            for (RelicSpec s : RelicSpec.ALL.values()) {
                if (s.slot.equals("weapon") || s.slot.equals("legend")) {
                    Object cap = get.invoke(null, ((Item)CharacterRelics.ITEMS.get(s.id).get()).getDefaultInstance());
                    h.assertTrue(cap != null && !(Boolean)cap.getClass().getMethod("isEmpty").invoke(cap), "EpicFight loaded " + s.id);
                    String var8 = s.character;

                    String expected = switch (var8) {
                        case "kokuhaku" -> "TACHI";
                        case "mels" -> "FIST";
                        case "taika", "brutality" -> "GREATSWORD";
                        case "huang_linghua" -> "SPEAR";
                        default -> "SWORD";
                    };
                    h.assertTrue(cap.getClass().getMethod("getWeaponCategory").invoke(cap).toString().equals(expected), "Custom category " + s.id);
                    count++;
                }
            }

            Object cap = get.invoke(null, ((SwordItem)AdventureContent.BLADE.get()).getDefaultInstance());
            h.assertTrue(cap != null && cap.getClass().getMethod("getWeaponCategory").invoke(cap).toString().equals("LONGSWORD"), "Adventure custom longsword");
            System.out.println("[OROR_MIND] epicFightWeapons=" + (count + 1) + " PASS");
            h.succeed();
        } catch (ReflectiveOperationException var10) {
            throw new IllegalStateException(var10);
        }
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void guard_villager_accepts_mind_and_arsenal(GameTestHelper h) {
        EntityType<?> type = (EntityType<?>)BuiltInRegistries.ENTITY_TYPE.get(ResourceLocation.fromNamespaceAndPath("guardvillagers", "guard"));
        h.assertTrue(type != EntityType.PIG, "Guard type exists");
        Entity entity = type.create(h.getLevel());
        h.assertTrue(entity instanceof Mob, "Guard native Mob");
        Mob guard = (Mob)entity;
        BlockPos pos = h.absolutePos(new BlockPos(8, 2, 8));
        guard.moveTo((double)pos.getX(), (double)pos.getY(), (double)pos.getZ());
        h.getLevel().addFreshEntity(guard);
        AdaptiveCombat.arm(guard);
        MobMind.practice(guard, "bow", 10);
        h.assertTrue(AdaptiveCombat.guardian(guard) && guard.getMaxHealth() >= 256.0F && MobMind.skill(guard, "bow") == 10, "Guard shares persistent mind");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void mace_fall_attack_and_player_style_learning(GameTestHelper h) {
        Villager v = (Villager)mob(h, EntityType.VILLAGER, 8, 8);
        v.setNoAi(true);
        AdaptiveCombat.arm(v);
        Husk t = (Husk)mob(h, EntityType.HUSK, 10, 8);
        t.setNoAi(true);
        t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        t.setHealth(1024.0F);
        v.fallDistance = 5.0F;
        v.setOnGround(false);
        AdaptiveCombat.strike(v, t, "mace", h.getLevel());
        h.assertTrue(t.getHealth() < 920.0F && MobMind.data(v).getInt("SuccessfulStrikes") == 1, "Mace fall damage is actually dealt");
        v.setNoAi(false);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.setItemInHand(InteractionHand.MAIN_HAND, Items.MACE.getDefaultInstance());
        p.moveTo(v.getX() + 1.0, v.getY(), v.getZ());
        v.hurt(p.damageSources().playerAttack(p), 1.0F);
        h.assertTrue(
            MobMind.data(v).getString("ObservedPlayerStyle").equals("mace") && MobMind.skill(v, "mace") >= 3, "Observed player weapon trains matching skill"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "mind"
    )
    public static void low_health_mob_retreats_during_healing(GameTestHelper h) {
        Villager v = guard((Villager)mob(h, EntityType.VILLAGER, 8, 8));
        AdaptiveCombat.arm(v);
        v.setHealth(40.0F);
        Husk t = (Husk)mob(h, EntityType.HUSK, 10, 8);
        t.setNoAi(true);
        v.setTarget(t);
        double start = (double)v.distanceTo(t);
        h.runAfterDelay(
            12L,
            () -> {
                h.assertTrue(
                    v.getHealth() > 40.0F && (double)v.distanceTo(t) > start && MobMind.skill(v, "healing") > 0, "Actual movement retreats while recovering"
                );
                h.succeed();
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 400,
        batch = "tukuyo"
    )
    public static void tukuyo_signed_decision_controls_native_stance(GameTestHelper h) {
        SupremeEntity b = mob(h, (EntityType<SupremeEntity>)OrorReborn.TYPES.get("riha").get(), 8, 8);
        b.setNoAi(true);
        b.setHealth(b.getMaxHealth() * 0.2F);
        h.succeedWhen(
            () -> {
                if (MobMind.data(b).getInt("TukuyoDecisions") == 0) {
                    TukuyoBridge.request(b, null, "");
                }

                h.assertTrue(MobMind.data(b).getInt("TukuyoDecisions") > 0, "Real local TUKUYO HTTP callback");
                h.assertTrue(
                    MobMind.stance(b).equals("defensive") && MobMind.data(b).getString("TukuyoDecision").matches("[0-9a-f]{64}"),
                    "Signed original runtime decision applied on server thread"
                );
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 500,
        batch = "tukuyo"
    )
    public static void tukuyo_teaching_and_entity_identity_stay_separate(GameTestHelper h) {
        SupremeEntity a = mob(h, (EntityType<SupremeEntity>)OrorReborn.TYPES.get("kokuhaku").get(), 8, 8);
        SupremeEntity b = mob(h, (EntityType<SupremeEntity>)OrorReborn.TYPES.get("riha").get(), 12, 8);
        a.setNoAi(true);
        b.setNoAi(true);
        h.succeedWhen(
            () -> {
                if (MobMind.data(a).getInt("TukuyoDecisions") == 0) {
                    TukuyoBridge.request(a, null, "空手を鍛えて");
                }

                if (MobMind.data(b).getInt("TukuyoDecisions") == 0) {
                    TukuyoBridge.request(b, null, "弓を鍛えて");
                }

                h.assertTrue(MobMind.data(a).getInt("TukuyoDecisions") > 0 && MobMind.data(b).getInt("TukuyoDecisions") > 0, "Two real TUKUYO individuals");
                h.assertTrue(
                    !MobMind.data(a).getString("TukuyoDecision").equals(MobMind.data(b).getString("TukuyoDecision"))
                        && MobMind.preferred(a).equals("unarmed")
                        && MobMind.preferred(b).equals("bow")
                        && MobMind.data(a).getString("TukuyoSource").equals("teacher"),
                    "Private identity and teacher provenance maintained"
                );
            }
        );
    }

    /** An armorer: one of the village's guards (VillageAI.fighter). */
    private static Villager guard(Villager v) {
        v.setVillagerData(v.getVillagerData().setProfession(VillagerProfession.ARMORER));
        return v;
    }

    private static <T extends Mob> T mob(GameTestHelper h, EntityType<T> type, int x, int z) {
        T m = (T)type.create(h.getLevel());
        BlockPos pos = h.absolutePos(new BlockPos(x, 2, z));
        m.moveTo((double)pos.getX() + 0.5, (double)pos.getY(), (double)pos.getZ() + 0.5, 0.0F, 0.0F);
        m.setPersistenceRequired();
        h.getLevel().addFreshEntity(m);
        if (m instanceof Villager) {
            MobLevels.set(m, 1);
        }

        return m;
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void conversation_changes_weapon_strength_and_persists(GameTestHelper h) {
        SupremeEntity b = mob(h, (EntityType<SupremeEntity>)OrorReborn.TYPES.get("kokuhaku").get(), 8, 8);
        b.setNoAi(true);
        UUID human = UUID.randomUUID();
        double before = MobMind.strength(b);
        MobConversation.apply(b, human, "空手を鍛えて", MobConversation.local(b, "空手を鍛えて", false, "試験"));
        h.assertTrue(
            MobMind.stance(b).equals("unarmed") && MobMind.skill(b, "unarmed") > 0 && MobMind.strength(b) > before,
            "Conversation changes executable skill and strength"
        );
        CompoundTag saved = new CompoundTag();
        b.saveWithoutId(saved);
        SupremeEntity restored = (SupremeEntity)((EntityType)OrorReborn.TYPES.get("kokuhaku").get()).create(h.getLevel());
        restored.load(saved);
        h.assertTrue(
            MobMind.skill(restored, "unarmed") == MobMind.skill(b, "unarmed") && MobMind.data(restored).getList("Conversations", 10).size() == 1,
            "Mind survives native entity save/load"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void dialogue_memory_and_practice_are_bounded(GameTestHelper h) {
        Villager b = (Villager)mob(h, EntityType.VILLAGER, 8, 8);

        for (int i = 0; i < 100; i++) {
            MobConversation.apply(b, UUID.randomUUID(), "弓の訓練", MobConversation.local(b, "弓の訓練", false, "試験"));
            MobMind.remember(b, "test:" + i, "shield");
        }

        CompoundTag n = MobMind.data(b);
        h.assertTrue(
            n.getList("Conversations", 10).size() == 12 && n.getCompound("Relations").size() == 16 && n.getCompound("Opponents").size() == 32,
            "Per-mob bounded memory"
        );
        h.assertTrue(MobMind.skill(b, "bow") == 12, "Dialogue spam cannot bypass training cooldown");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void older_mobs_gain_power_and_clock_survives_reload(GameTestHelper h) {
        Zombie b = (Zombie)mob(h, EntityType.ZOMBIE, 8, 8);
        b.setNoAi(true);
        CompoundTag n = MobMind.data(b);
        n.putLong("LastClock", h.getLevel().getGameTime() - 240000L);
        MobMind.clock(b);
        h.assertTrue(MobMind.age(b) >= 240000L && MobMind.strength(b) > 1.5, "Ten days lived makes stronger cognition");
        long age = MobMind.age(b);
        CompoundTag save = new CompoundTag();
        b.saveWithoutId(save);
        Zombie copy = (Zombie)EntityType.ZOMBIE.create(h.getLevel());
        copy.load(save);
        MobMind.clock(copy);
        h.assertTrue(MobMind.age(copy) == age, "Reload does not double-count age");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void villager_arms_and_defeats_survival_player(GameTestHelper h) {
        Villager v = (Villager)mob(h, EntityType.VILLAGER, 8, 8);
        AdaptiveCombat.arm(v);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.moveTo(v.getX() + 1.0, v.getY(), v.getZ());
        v.setTarget(p);
        AdaptiveCombat.strike(v, p, "sword", h.getLevel());
        h.assertTrue(
            v.getMainHandItem().is(Items.IRON_SWORD) && v.getOffhandItem().is(Items.SHIELD) && v.getMaxHealth() >= 256.0F && !p.isAlive(),
            "Trade level one villager kills ordinary survival player"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void villagers_alert_allies_after_player_attack(GameTestHelper h) {
        // v0.17.9: the guards (fighting professions) take up the fight; an ordinary villager hears the alarm instead
        Villager a = guard((Villager)mob(h, EntityType.VILLAGER, 8, 8));
        Villager b = guard((Villager)mob(h, EntityType.VILLAGER, 11, 8));
        Villager c = (Villager)mob(h, EntityType.VILLAGER, 9, 11);
        Player p = h.makeMockPlayer(GameType.SURVIVAL);
        p.moveTo(a.getX() + 1.0, a.getY(), a.getZ());
        a.hurt(p.damageSources().playerAttack(p), 2.0F);
        h.assertTrue(a.getTarget() == p && b.getTarget() == p && MobMind.skill(b, "teamwork") > 0, "Nearby guards share an aggressor");
        h.assertTrue(
            !VillageAI.fighter(c) && c.getTarget() == null && MobMind.data(c).getLong("VillageAlarm") > h.getLevel().getGameTime(),
            "An ordinary villager is warned, not sent in"
        );
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 160,
        batch = "mind"
    )
    public static void real_arrow_and_trident_hit_targets(GameTestHelper h) {
        Villager v = (Villager)mob(h, EntityType.VILLAGER, 8, 8);
        v.setNoAi(true);
        Husk a = (Husk)mob(h, EntityType.HUSK, 18, 8);
        a.setNoAi(true);
        a.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        a.setHealth(1024.0F);
        Husk b = (Husk)mob(h, EntityType.HUSK, 18, 16);
        b.setNoAi(true);
        b.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        b.setHealth(1024.0F);
        AdaptiveCombat.shoot(v, a, "bow", h.getLevel());
        AdaptiveCombat.shoot(v, b, "trident", h.getLevel());
        h.assertTrue(h.getLevel().getEntitiesOfClass(AbstractArrow.class, v.getBoundingBox().inflate(2.0)).size() >= 2, "Real native projectiles spawned");
        h.runAfterDelay(30L, () -> {
            h.assertTrue(a.getHealth() < 1024.0F && b.getHealth() < 1024.0F, "Both real projectile collision paths damage targets");
            h.succeed();
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void ranged_attacks_do_not_shoot_through_ally_or_wall(GameTestHelper h) {
        Villager v = (Villager)mob(h, EntityType.VILLAGER, 8, 8);
        Villager friend = (Villager)mob(h, EntityType.VILLAGER, 12, 8);
        Zombie target = (Zombie)mob(h, EntityType.ZOMBIE, 18, 8);
        h.assertTrue(!AdaptiveCombat.clearShot(v, target, h.getLevel()), "Ally blocks firing lane");
        friend.discard();
        h.assertTrue(AdaptiveCombat.clearShot(v, target, h.getLevel()), "Open firing lane accepted");

        for (int y = 2; y < 5; y++) {
            h.setBlock(12, y, 8, Blocks.STONE);
        }

        h.assertTrue(!AdaptiveCombat.clearShot(v, target, h.getLevel()), "Opaque wall blocks projectile decision");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 140,
        batch = "mind"
    )
    public static void axe_breaks_actual_shield_and_imposes_cooldown(GameTestHelper h) {
        Villager v = (Villager)mob(h, EntityType.VILLAGER, 8, 8);
        v.setNoAi(true);
        Zombie t = (Zombie)mob(h, EntityType.ZOMBIE, 10, 8);
        t.setNoAi(true);
        t.setItemInHand(InteractionHand.OFF_HAND, Items.SHIELD.getDefaultInstance());
        t.startUsingItem(InteractionHand.OFF_HAND);
        h.runAfterDelay(8L, () -> {
            h.assertTrue(t.isBlocking(), "Shield is actually raised");
            h.assertTrue(AdaptiveCombat.select(v, t, 2.0).equals("axe"), "Select axe against blocking target");
            AdaptiveCombat.strike(v, t, "axe", h.getLevel());
            h.assertTrue(!t.isBlocking() && MobMind.data(t).getLong("ShieldBroken") > h.getLevel().getGameTime(), "Actual shield released for 100 ticks");
            h.succeed();
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void every_supreme_has_overpowered_unarmed_damage(GameTestHelper h) {
        int total = 0;

        for (String id : CharacterSpec.ALL.keySet()) {
            SupremeEntity b = mob(h, (EntityType<SupremeEntity>)OrorReborn.TYPES.get(id).get(), 8, 8);
            Zombie target = (Zombie)mob(h, EntityType.ZOMBIE, 10, 8);
            target.setNoAi(true);
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
            target.setHealth(1024.0F);
            b.setTarget(target);
            AdaptiveCombat.strike(b, target, "unarmed", h.getLevel());
            h.assertTrue(!target.isAlive(), "Lore bare hand kills 1024 HP target: " + id);
            b.discard();
            target.discard();
            total++;
        }

        System.out.println("[OROR_MIND] unarmedSupreme=" + total + " PASS");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void terrain_pillar_and_protected_chest_rules(GameTestHelper h) {
        Villager v = (Villager)mob(h, EntityType.VILLAGER, 8, 8);
        v.setNoAi(true);
        v.setOnGround(true);
        Zombie t = (Zombie)mob(h, EntityType.ZOMBIE, 12, 8);
        t.setNoAi(true);
        t.teleportTo(t.getX(), v.getY() + 5.0, t.getZ());
        boolean grief = h.getLevel().getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING);
        ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(true, h.getLevel().getServer());
        BlockPos pos = v.blockPosition();
        h.assertTrue(AdaptiveCombat.terrain(v, t, h.getLevel()), "Mob builds upward toward elevated enemy");
        h.assertTrue(
            h.getLevel().getBlockState(pos).is(Blocks.COBBLESTONE) && v.getY() > (double)(pos.getY() + 1), "Real cobblestone pillar and collision-safe ascent"
        );
        MobMind.data(v).putLong("NextTerrain", 0L);
        v.setOnGround(true);
        t.teleportTo(t.getX(), v.getY(), t.getZ());
        BlockPos front = v.blockPosition().east();
        h.getLevel().setBlock(front, Blocks.CHEST.defaultBlockState(), 3);
        h.assertTrue(!AdaptiveCombat.terrain(v, t, h.getLevel()) && h.getLevel().getBlockState(front).is(Blocks.CHEST), "Chest cannot be destroyed for pathing");
        ((BooleanValue)h.getLevel().getGameRules().getRule(GameRules.RULE_MOBGRIEFING)).set(grief, h.getLevel().getServer());
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 100,
        batch = "mind"
    )
    public static void responses_search_schema_and_citation_parsing(GameTestHelper h) {
        JsonObject body = MobConversation.body("gpt-5.4-mini", "弓の間合いを調べて", true);
        h.assertTrue(
            body.getAsJsonArray("tools").get(0).getAsJsonObject().get("type").getAsString().equals("web_search")
                && body.get("tool_choice").getAsString().equals("required")
                && !body.get("store").getAsBoolean(),
            "Real Responses web search request shape"
        );
        String raw = "{\"status\":\"completed\",\"output\":[{\"content\":[{\"type\":\"output_text\",\"text\":\"{\\\"reply\\\":\\\"盾には斧だ\\\",\\\"stance\\\":\\\"aggressive\\\",\\\"skill\\\":\\\"axe\\\",\\\"lesson\\\":\\\"盾を崩す\\\"}\",\"annotations\":[{\"url\":\"https://minecraft.net/\"},{\"url\":\"file:///secret\"}]}]}]}";
        MobConversation.Answer a = MobConversation.parse(raw);
        h.assertTrue(
            a.remote() && a.skill().equals("axe") && a.sources().equals(List.of("https://minecraft.net/")),
            "Remote reply and real annotations parse; unsafe schemes rejected"
        );
        boolean invalid = false;

        try {
            MobConversation.parse(raw.replace("aggressive", "operator"));
        } catch (RuntimeException var6) {
            invalid = true;
        }

        h.assertTrue(invalid, "Model cannot invent arbitrary executable actions");
        h.succeed();
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 120,
        batch = "mind"
    )
    public static void native_combat_tick_uses_cooldowns_and_gains_experience(GameTestHelper h) {
        Villager v = guard((Villager)mob(h, EntityType.VILLAGER, 8, 8));
        AdaptiveCombat.arm(v);
        Zombie t = (Zombie)mob(h, EntityType.ZOMBIE, 10, 8);
        t.setNoAi(true);
        t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        t.setHealth(1024.0F);
        v.setTarget(t);
        h.runAfterDelay(
            48L,
            () -> {
                h.assertTrue(
                    t.getHealth() < 1024.0F && MobMind.data(v).getInt("Strikes") > 1 && MobMind.data(v).getInt("Strikes") < 10,
                    "Native tick attacks with bounded cooldown"
                );
                h.assertTrue(MobMind.skill(v, "sword") > 0 && MobMind.data(v).getLong("Experience") > 20L, "Successful combat updates skill library");
                h.succeed();
            }
        );
    }
}
