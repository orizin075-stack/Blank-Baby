package jp.oror.reborn;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.living.MobSpawnEvent.PositionCheck;

/**
 * v0.17.18: the parts of NightfallCraft 2.2.8.6 that its authors wrote as config files rather than mods, carried into
 * this mod so they work without InControl or Multiplayer Boss Fight (neither has a 1.21.1 NeoForge build).
 *
 * <ul>
 *   <li>config/multiplayer_boss_fight: a boss grows with every extra player near it, +40% toughness and +10% attack
 *       each (the Ender Dragon +25% toughness). Nightfall counted every player; here the first one is free, so a boss
 *       fought alone keeps the strength it was tuned for.</li>
 *   <li>config/incontrol/spawn.json: natural spawn caps. At most 700 of one kind per dimension in the Overworld, the
 *       Nether and the End; creepers, stonelings, toretoises and flies 3 per player, Endermapteras 7 per player, the
 *       Weapons of Miracles elites one per player, bats 3; the Cataclysm dungeon dimensions spawn only their own
 *       creatures. Spawners are never limited.</li>
 * </ul>
 */
public final class NightfallRules {
    static final TagKey<EntityType<?>> BOSSES = TagKey.create(Registries.ENTITY_TYPE, ResourceLocation.fromNamespaceAndPath("c", "bosses"));
    static final double RANGE = 64.0;
    static final int MAX_EXTRA = 10;

    static final Map<String, Integer> PER_PLAYER = Map.of(
        "wom:saulomonk", 1, "wom:hollow", 1, "wom:evil_skeleton", 1, "wom:lycanth", 1,
        "cataclysm:endermaptera", 7,
        "minecraft:creeper", 3, "quark:stoneling", 3, "quark:toretoise", 3, "alexsmobs:fly", 3
    );
    static final Map<String, Integer> FLAT = Map.of("minecraft:bat", 3);
    static final Set<String> CAPPED_DIMENSIONS = Set.of("minecraft:overworld", "minecraft:the_nether", "minecraft:the_end");
    static final int KIND_CAP = 700;
    static final Map<String, Set<String>> DIMENSION_MOBS = Map.of(
        "cataclysm_dimension:cataclysm_forge_of_aeons", Set.of("cataclysm:the_watcher", "cataclysm:the_prowler", "cataclysm:the_harbinger"),
        "cataclysm_dimension:cataclysm_abyssal_depths", Set.of(
            "cataclysm:deepling", "cataclysm:deepling_angler", "cataclysm:deepling_priest", "cataclysm:deepling_warlock",
            "cataclysm:deepling_brute", "cataclysm:coralssus", "cataclysm:coral_golem", "cataclysm:the_leviathan"),
        "cataclysm_dimension:cataclysm_pharaohs_bane", Set.of("cataclysm:koboleton", "cataclysm:wadjet", "cataclysm:kobolediator", "cataclysm:ancient_remnant"),
        "cataclysm_dimension:cataclysm_eternal_frosthold", Set.of(
            "cataclysm:draugr", "cataclysm:royal_draugr", "cataclysm:elite_draugr", "cataclysm:aptrgangr", "cataclysm:maledictus"),
        "cataclysm_dimension:cataclysm_sanctum_fallen", Set.of(
            "cataclysm:urchinkin", "cataclysm:octohost", "cataclysm:symbiocto", "cataclysm:cindaria", "cataclysm:hippocamtus",
            "cataclysm:clawdian", "cataclysm:scylla"),
        "cataclysm_dimension:cataclysm_souls_anvil", Set.of(
            "cataclysm:piglin", "cataclysm:piglin_brute", "cataclysm:netherite_ministrosity", "cataclysm:netherite_monstrosity"),
        "cataclysm_dimension:cataclysm_infernos_maw", Set.of("cataclysm:ignited_revenant", "cataclysm:ignited_berserker", "cataclysm:ignis"),
        "cataclysm_dimension:cataclysm_bastion_lost", Set.of("minecraft:shulker", "cataclysm:endermaptera", "cataclysm:ender_golem", "cataclysm:ender_guardian")
    );

    /** Entities per kind in each dimension, counted once a second; capped kinds let through since then are added on. */
    private static final Map<ServerLevel, Census> CENSUS = new WeakHashMap<>();
    private static boolean hooked;

    private static final class Census {
        long at = Long.MIN_VALUE;
        final Map<EntityType<?>, Integer> kinds = new HashMap<>();
    }

    /**
     * Called from WorldEvents.levelTick. OrorReborn registers no spawn listener, and the server classes of this
     * build leave the mod class as it was, so the spawn check joins the event bus the first time a world ticks.
     */
    static void hook() {
        if (!hooked) {
            hooked = true;
            NeoForge.EVENT_BUS.addListener(NightfallRules::spawn);
        }
    }

    private static Census census(ServerLevel sl) {
        Census c = CENSUS.computeIfAbsent(sl, k -> new Census());
        long now = sl.getGameTime();
        if (c.at == Long.MIN_VALUE || now - c.at >= 20L || now < c.at) {
            c.at = now;
            c.kinds.clear();
            for (Entity e : sl.getAllEntities()) {
                if (e.isAlive()) {
                    c.kinds.merge(e.getType(), 1, Integer::sum);
                }
            }
        }

        return c;
    }

    static void spawn(PositionCheck e) {
        // natural spawns only: spawners, eggs, commands, raids and this mod's own patrols are never limited
        if (e.getSpawnType() != MobSpawnType.NATURAL || !(e.getLevel() instanceof ServerLevel sl)) {
            return;
        }

        Mob mob = e.getEntity();
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(mob.getType()).toString();
        String dimension = sl.dimension().location().toString();
        Set<String> natives = DIMENSION_MOBS.get(dimension);
        if (natives != null) {
            if (!natives.contains(id)) {
                e.setResult(PositionCheck.Result.FAIL);
            }

            return;
        }

        Census c = census(sl);
        int have = c.kinds.getOrDefault(mob.getType(), 0);
        int players = Math.max(1, sl.players().size());
        boolean deny = CAPPED_DIMENSIONS.contains(dimension) && have >= KIND_CAP
            || PER_PLAYER.containsKey(id) && have >= PER_PLAYER.get(id) * players
            || FLAT.containsKey(id) && have >= FLAT.get(id);
        if (deny) {
            e.setResult(PositionCheck.Result.FAIL);
        } else if ((PER_PLAYER.containsKey(id) || FLAT.containsKey(id)) && mob.checkSpawnRules(sl, MobSpawnType.NATURAL) && mob.checkSpawnObstruction(sl)) {
            // a pack spawns in one tick, before the next count: add the ones that will really appear (the same two
            // checks the event falls back to), so a refused attempt does not use up the allowance
            c.kinds.merge(mob.getType(), 1, Integer::sum);
        }
    }

    static boolean boss(LivingEntity e) {
        if (e instanceof SupremeEntity s) {
            // a character that walks with a player is a companion, not a boss to share
            return s.owner == null;
        } else {
            return e instanceof EnderDragon || e instanceof WitherBoss || e.getType().is(BOSSES);
        }
    }

    /** Toughness per extra player: the share of health Nightfall added (the Ender Dragon's is smaller). */
    static float toughness(LivingEntity e) {
        return e instanceof EnderDragon ? 0.25F : 0.4F;
    }

    /**
     * Called every two seconds for each living entity from WorldEvents.livingTick: counts the players near a boss and
     * keeps the number of extra ones on it for damage(). Nightfall raised the health attribute instead, but that stops
     * at 1024 (a third of this mod's characters already stand there), leaves the Wither short after its spawn heal and
     * does nothing for the Wither and the Dragon's attacks, which have no attack attribute.
     */
    static void party(LivingEntity e, ServerLevel sl) {
        if (!e.isAlive() || !boss(e)) {
            return;
        }

        int near = 0;
        for (ServerPlayer p : sl.players()) {
            if (p.isAlive() && !p.isSpectator() && p.distanceToSqr(e) < RANGE * RANGE) {
                near++;
            }
        }

        // nobody around: keep what it had, so walking off and coming back alone does not reset the fight
        if (near == 0) {
            return;
        }

        int extra = Math.min(MAX_EXTRA, near - 1);
        int before = e.getPersistentData().getInt("OrorParty");
        if (extra == before) {
            return;
        }

        if (extra > 0) {
            e.getPersistentData().putInt("OrorParty", extra);
        } else {
            e.getPersistentData().remove("OrorParty");
        }

        Component text = extra > 0
            ? Component.empty().append(e.getDisplayName()).append("：挑戦者" + near + "人に合わせて耐久+" + Math.round(toughness(e) * extra * 100.0F) + "%・攻撃+" + extra * 10 + "%")
            : Component.empty().append(e.getDisplayName()).append("：挑戦者が一人になり、本来の強さに戻った");
        for (ServerPlayer p : sl.players()) {
            if (p.distanceToSqr(e) < RANGE * RANGE) {
                p.displayClientMessage(text, true);
            }
        }
    }

    /**
     * Called from WorldEvents.damage. A boss facing extra players takes 1/(1 + 0.4 per player) of each hit, the same as
     * 40% more health, and its own hits, projectiles and breath included, deal 10% more per player.
     */
    static void damage(LivingIncomingDamageEvent e) {
        LivingEntity target = e.getEntity();
        int guarded = target.getPersistentData().getInt("OrorParty");
        if (guarded > 0 && boss(target)) {
            e.setAmount(e.getAmount() / (1.0F + toughness(target) * guarded));
        }

        if (e.getSource().getEntity() instanceof LivingEntity attacker && attacker != target) {
            int fierce = attacker.getPersistentData().getInt("OrorParty");
            if (fierce > 0 && boss(attacker)) {
                e.setAmount(e.getAmount() * (1.0F + 0.1F * fierce));
            }
        }
    }

    private NightfallRules() {
    }
}
