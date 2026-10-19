package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.StructureTags;
import net.minecraft.world.Container;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.Heightmap.Types;
import net.minecraft.world.phys.Vec3;

/**
 * How villages grow and go out into the world (v0.17.15).
 * - Development (発展): 開拓地 → 村 (3 villagers) → 町 (6 villagers, a communal chest, a campfire and two strong villagers)
 *   → 城下町 (8 villagers after a dungeon expedition) → 辺境の都 (two trips to the Nether) → 天空の都 (back from the End).
 *   The village announces each step to the players near it.
 * - Expeditions (遠征): up to four strong villagers, the strongest that are healthy and not miners, take the best armour
 *   and weapons from the communal chests, gather, set out, and come back after a while with what they found; the stronger
 *   the party the better the haul and the fewer the losses, and survivors come back tougher.
 *   - A town sends parties to dungeons (and ruined portals, for obsidian). A monster spawner found in the loaded ground
 *     around the village is the first target: when the party comes back it really is broken and its chests emptied.
 *   - A 城下町 gathers ten obsidian (from the chests, or by pouring water on a lava pool and digging the obsidian out),
 *     builds a nether gate near the centre and sends parties through it for nether wart, blaze rods, ghast tears, magma
 *     cream, quartz, ender pearls (bartered), ancient debris and netherite. The gate is lit only while a party goes or
 *     comes back, so nothing wanders through it.
 *   - The village makes eyes of ender from blaze powder and ender pearls; with twelve and a party strong enough (about
 *     diamond gear on seasoned villagers) it sets out toward the stronghold and comes back from the End with shulker shells,
 *     chorus fruit, purpur, dragon's breath and now and then elytra.
 * Away, the party is not in the world (unloaded ground does not move, so a journey there could not happen anyway): its
 * villagers are kept as saved data in VillageProgress and come back as themselves.
 * - Wandering parties (流れの遠征隊): now and then a party of some village's veterans is met in the wild - netherite gear,
 *   the highest level, guns where Superb Warfare is installed. They fight what they meet, camp at night and move on.
 * v0.17.16:
 * - A 辺境の都 also raids other mods' dungeons: a structure of a mod with chest loot of its own, whose chests (that mod's
 *   own loot tables, rolled for real) the party brings back.
 * - The great wish (悲願): the dragon egg, and the dragon head from an end ship. Until both are home a 辺境の都 puts the
 *   End first; either one in the communal chests (brought back, or put there by a player) is set on an altar by the
 *   centre for the whole world to hear of, and with both the village becomes a 竜の都.
 * - Two parties from different villages sometimes meet on the road and fight (VillageFeuds), and parties hunt players
 *   known to have attacked one.
 */
public final class VillageExpeditions {
    private static final String[] STAGES = {"開拓地", "村", "町", "城下町", "辺境の都", "天空の都", "竜の都"};
    private static final ResourceLocation VETERAN = new ResourceLocation("oror_supreme_bosses", "expedition_veteran");
    private static final List<String> STRONG = List.of("armorer", "weaponsmith", "toolsmith", "fletcher", "butcher", "leatherworker", "mason");

    private VillageExpeditions() {
    }

    // ------------------------------------------------------------------------------------- the review (every 30 s)
    /** Called by VillageWork.survey when it refreshes: deliveries, development, unlocks, the expedition under way. */
    static void review(ServerLevel sl, VillageWork.Survey s) {
        VillageProgress db = VillageProgress.get(sl);
        VillageProgress.Record r = db.of(s.village);
        long now = sl.getGameTime();
        db.unload(r, chests(sl, s), sl.registryAccess());
        int stage = Math.max(r.stage, stage(s, r));
        if (stage > r.stage) {
            r.stage = stage;
            db.setDirty();
            VillageProgress.announce(sl, s.village, "村が「" + STAGES[stage] + "」に発展しました（村人" + s.population + "人）"
                + (stage == 4 && (!r.egg || !r.head) ? "　村の悲願：エンダードラゴンの卵と、エンドシップのドラゴンの頭" : ""), stage >= 4);
        }
        VillageFeuds.enforce(sl, s.village);
        wish(sl, s, r);
        if (now - s.spawnersAt > 12000L || s.spawnersAt == 0L) {
            s.spawnersAt = now;
            spawners(sl, s);
        }
        smith(sl, s);
        VillageArms.review(sl, s, r);
        VillageFlights.review(sl, s, r);
        VillageVehicles.review(sl, s, r);
        if (r.trip != null) {
            advance(sl, s, r, now);
        } else if (sl.isDay() && now >= r.nextTrip && !s.night) {
            plan(sl, s, r, now);
        }
    }

    /**
     * The village smithy: with a netherite upgrade template and a netherite ingot in the chests, a diamond helmet,
     * chestplate, leggings, boots, sword or axe there becomes netherite, keeping its enchantments (as a smithing table does).
     */
    private static void smith(ServerLevel sl, VillageWork.Survey s) {
        if (s.stock("netherite_upgrade_smithing_template") < 1 || s.stock("netherite_ingot") < 1) {
            return;
        }
        for (Container box : chests(sl, s)) {
            for (int i = 0; i < box.getContainerSize(); i++) {
                ItemStack st = box.getItem(i);
                String id = st.isEmpty() ? "" : BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
                if (!id.startsWith("diamond_") || tier(st) < 0) {
                    continue;
                }
                Item better = item(id.replace("diamond_", "netherite_"));
                if (better == null || better == net.minecraft.world.item.Items.AIR) {
                    continue;
                }
                if (take(sl, s, "netherite_upgrade_smithing_template", 1) < 1) {
                    return;
                }
                if (take(sl, s, "netherite_ingot", 1) < 1) {
                    return;
                }
                box.setItem(i, st.transmuteCopy(better, 1));
                box.setChanged();
                VillageProgress.announce(sl, s.village, "村の鍛冶場で「" + st.getHoverName().getString() + "」をネザライトに強化しました", false);
                return;
            }
        }
    }

    static int stage(VillageWork.Survey s, VillageProgress.Record r) {
        if (r.egg && r.head) {
            return 6;
        }
        if (r.ends > 0) {
            return 5;
        }
        int stage = s.population >= 3 ? 1 : 0;
        if (stage == 1 && s.population >= 6 && !s.chests.isEmpty() && s.campfire != null && s.strong >= 2) {
            stage = 2;
        }
        if (stage == 2 && r.dungeons >= 1 && s.population >= 8) {
            stage = 3;
        }
        if (stage == 3 && r.nethers >= 2) {
            stage = 4;
        }
        return stage;
    }

    /**
     * v0.17.17: villagers of a kingdom (村人の王国) or a villager fortress (村人の要塞) found in the world bring their village
     * up to what such a place already is: a kingdom is a 辺境の都 with guns, a fortress a 城下町.
     */
    static void settle(Villager v, ServerLevel sl) {
        CompoundTag root = v.getPersistentData();
        String kind = root.getString("OrorSettlement");
        if (kind.isEmpty() || root.getBoolean("OrorSettled")) {
            return;
        }
        VillageLedger.Village village = VillageLedger.of(v);
        if (village == null) {
            return;
        }
        root.putBoolean("OrorSettled", true);
        VillageProgress db = VillageProgress.get(sl);
        VillageProgress.Record r = db.of(village);
        boolean kingdom = kind.equals("kingdom");
        if (kingdom && !r.kingdom) {
            r.kingdom = true;
            r.guns = r.guns || VillageArms.present();
            VillageProgress.announce(sl, village, "この地は村人の王国です", false);
        }
        r.stage = Math.max(r.stage, kingdom ? 4 : 3);
        db.setDirty();
    }

    static String stageName(int stage) {
        return STAGES[Math.max(0, Math.min(STAGES.length - 1, stage))];
    }

    static List<Container> chests(ServerLevel sl, VillageWork.Survey s) {
        List<Container> out = new ArrayList<>();
        for (BlockPos p : s.chests) {
            Container box = VillageReputation.communalChest(sl, s.village, p);
            if (box != null) {
                out.add(box);
            }
        }
        return out;
    }

    /** Monster spawners in the loaded ground within 96 blocks of the centre (real dungeons to clear). */
    private static void spawners(ServerLevel sl, VillageWork.Survey s) {
        s.spawners.clear();
        int cx = s.village.center.getX() >> 4;
        int cz = s.village.center.getZ() >> 4;
        for (int x = cx - 6; x <= cx + 6; x++) {
            for (int z = cz - 6; z <= cz + 6; z++) {
                LevelChunk chunk = sl.getChunkSource().getChunkNow(x, z);
                if (chunk == null) {
                    continue;
                }
                for (BlockEntity be : chunk.getBlockEntities().values()) {
                    if (be.getBlockState().is(spawner())) {
                        s.spawners.add(be.getBlockPos().immutable());
                    }
                }
            }
        }
        s.spawners.sort(Comparator.comparingDouble(p -> p.distSqr(s.village.center)));
    }

    // ------------------------------------------------------------------------------------- planning
    private static void plan(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, long now) {
        if (r.stage < 2) {
            return;
        }
        List<Villager> party = party(sl, s);
        if (party.size() < 2) {
            return;
        }
        int power = 0;
        for (Villager v : party) {
            power += power(v);
        }
        String kind = "dungeon";
        ResourceLocation target = null;
        // the great wish puts the End first until the egg and the head are home
        boolean wish = !r.egg || !r.head;
        if (r.stage >= 4 && s.stock("ender_eye") >= 12 && power >= 260 && (wish || sl.random.nextInt(3) == 0)) {
            kind = "end";
        } else if (r.stage >= 4 && power >= 200 && sl.random.nextInt(2) == 0 && (target = ruin(sl)) != null) {
            kind = "ruin";
        } else if (r.stage >= 3 && gateIntact(sl, r.gate)) {
            kind = "nether";
        }
        BlockPos gate = kind.equals("nether") ? front(r.gate) : rally(sl, s);
        if (gate == null) {
            return;
        }
        if (kind.equals("end") && take(sl, s, "ender_eye", 12) < 12) {
            return;
        }
        CompoundTag trip = new CompoundTag();
        trip.putString("Kind", kind);
        trip.putString("Phase", "muster");
        trip.putLong("Until", now + 1200L);
        trip.putLong("Gate", gate.asLong());
        ListTag members = new ListTag();
        for (Villager v : party) {
            members.add(VillageProgress.uuid(v.getUUID()));
            kit(sl, s, v);
            CompoundTag n = VillagerLife.data(v);
            n.putUUID("TripVillage", s.village.id);
            n.putString("Trip", kind);
            n.putString("Task", "遠征の準備");
        }
        trip.put("Members", members);
        trip.putInt("Power", power);
        if (kind.equals("dungeon") && !s.spawners.isEmpty()) {
            trip.putLong("Spawner", s.spawners.get(0).asLong());
        }
        if (target != null) {
            trip.putString("TargetNs", target.getNamespace());
            trip.putString("TargetPath", target.getPath());
        }
        r.trip = trip;
        VillageProgress.get(sl).setDirty();
        VillageProgress.announce(sl, s.village, "遠征隊（" + party.size() + "名・戦力" + power + "）が" + place(trip) + "への遠征の準備を始めました", false);
    }

    private static String place(String kind) {
        return switch (kind) {
            case "nether" -> "ネザー";
            case "end" -> "ジ・エンド";
            case "ruin" -> "他のMODのダンジョン";
            default -> "ダンジョン";
        };
    }

    /** The trip's destination by name: a modded dungeon's structure and mod. */
    private static String place(CompoundTag trip) {
        if (trip.getString("Kind").equals("ruin") && trip.contains("TargetPath")) {
            return "「" + trip.getString("TargetPath").replace('_', ' ') + "」（" + trip.getString("TargetNs") + "）";
        }
        return place(trip.getString("Kind"));
    }

    /** The strongest healthy strong villagers who are not miners, up to four. */
    private static List<Villager> party(ServerLevel sl, VillageWork.Survey s) {
        return sl.getEntitiesOfClass(Villager.class, new net.minecraft.world.phys.AABB(s.village.center).inflate(64.0, 24.0, 64.0),
                v -> v.isAlive() && VillageAI.strong(v) && !VillagerIndustry.miner(v) && !v.isSleeping() && v.getHealth() >= v.getMaxHealth() * 0.8F
                    && !VillagerLife.data(v).contains("Trip") && !v.getPersistentData().getBoolean("OrorWanderer") && VillageLedger.of(v) == s.village)
            .stream()
            .sorted(Comparator.comparingInt(VillageExpeditions::power).reversed())
            .limit(4L)
            .toList();
    }

    /** A villager's fighting strength: level, armour, weapon and expeditions survived. */
    static int power(Villager v) {
        return MobLevels.level(v) * 10 + v.getArmorValue() * 2 + (int)Math.round(v.getAttributeValue(Attributes.ATTACK_DAMAGE) * 2.0)
            + VillagerLife.data(v).getInt("Veteran") * 10;
    }

    /** Where a party gathers for a walk out: open ground near the centre. */
    private static BlockPos rally(ServerLevel sl, VillageWork.Survey s) {
        BlockPos c = s.village.center;
        for (int i = 0; i < 8; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            BlockPos p = top(sl, c.offset((int)Math.round(Math.cos(a) * 6.0), 0, (int)Math.round(Math.sin(a) * 6.0)));
            if (p != null && Math.abs(p.getY() - c.getY()) <= 4 && sl.getBlockState(p).canBeReplaced() && sl.getFluidState(p).isEmpty()) {
                return p;
            }
        }
        return c;
    }

    static BlockPos top(ServerLevel sl, BlockPos p) {
        return sl.hasChunkAt(p) ? new BlockPos(p.getX(), sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, p.getX(), p.getZ()), p.getZ()) : null;
    }

    // ------------------------------------------------------------------------------------- the armoury
    private static final List<String> TIERS = List.of("leather", "golden", "chainmail", "iron", "diamond", "netherite");

    /** A gear tier from an item id (netherite best), -1 for what is not armour or a sword or axe. */
    private static int tier(ItemStack st) {
        String id = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
        if (!(id.endsWith("_helmet") || id.endsWith("_chestplate") || id.endsWith("_leggings") || id.endsWith("_boots") || id.endsWith("_sword")
            || id.endsWith("_axe"))) {
            return -1;
        }
        String material = id.substring(0, id.lastIndexOf('_'));
        return TIERS.indexOf(material);
    }

    private static EquipmentSlot slot(ItemStack st) {
        String id = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
        if (id.endsWith("_helmet")) {
            return EquipmentSlot.HEAD;
        } else if (id.endsWith("_chestplate")) {
            return EquipmentSlot.CHEST;
        } else if (id.endsWith("_leggings")) {
            return EquipmentSlot.LEGS;
        } else if (id.endsWith("_boots")) {
            return EquipmentSlot.FEET;
        }
        return EquipmentSlot.MAINHAND;
    }

    /** Fit a party member with the best armour and blade the communal chests hold (better than what it wears). */
    private static void kit(ServerLevel sl, VillageWork.Survey s, Villager v) {
        CompoundTag mind = MobMind.data(v);
        for (Container box : chests(sl, s)) {
            for (int i = 0; i < box.getContainerSize(); i++) {
                ItemStack st = box.getItem(i);
                int t = st.isEmpty() ? -1 : tier(st);
                if (t < 0) {
                    continue;
                }
                EquipmentSlot slot = slot(st);
                ItemStack worn = v.getItemBySlot(slot);
                if (slot == EquipmentSlot.MAINHAND && AdaptiveCombat.foreign(worn) && !worn.isEmpty()) {
                    continue;
                }
                if (!worn.isEmpty() && tier(worn) >= t) {
                    continue;
                }
                ItemStack issued = box.removeItem(i, 1);
                box.setChanged();
                if (!worn.isEmpty() && !mind.contains("Managed_" + slot.getName())) {
                    box.setItem(i, worn.copy());
                }
                mind.remove("Managed_" + slot.getName());
                v.setItemSlot(slot, issued);
                v.setDropChance(slot, 0.0F);
                VillagerLife.data(v).putBoolean("Kit", true);
                if (slot == EquipmentSlot.MAINHAND) {
                    mind.putBoolean("OriginalAuto", false);
                    mind.remove("Selected");
                }
            }
        }
    }

    /** Back home: the armoury's gear goes back to the chests. */
    private static void unkit(ServerLevel sl, Villager v, VillageProgress.Record r) {
        if (!VillagerLife.data(v).getBoolean("Kit")) {
            return;
        }
        CompoundTag mind = MobMind.data(v);
        if (mind.contains("OriginalWeapon") && !mind.getBoolean("OriginalAuto")) {
            // the issued weapon, not one the combat AI made for a fight, is what goes back
            v.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.parseOptional(v.registryAccess(), mind.getCompound("OriginalWeapon")));
            mind.remove("OriginalWeapon");
            mind.remove("Selected");
        }
        List<ItemStack> back = new ArrayList<>();
        for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.MAINHAND)) {
            ItemStack worn = v.getItemBySlot(slot);
            if (!worn.isEmpty() && tier(worn) >= 0 && !mind.contains("Managed_" + slot.getName())) {
                back.add(worn.copy());
                v.setItemSlot(slot, ItemStack.EMPTY);
            }
        }
        VillagerLife.data(v).remove("Kit");
        VillageProgress.get(sl).deliver(r, back, sl.registryAccess());
    }

    // ------------------------------------------------------------------------------------- under way
    private static void advance(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, long now) {
        CompoundTag trip = r.trip;
        String phase = trip.getString("Phase");
        String kind = trip.getString("Kind");
        if (phase.equals("muster")) {
            BlockPos gate = BlockPos.of(trip.getLong("Gate"));
            List<Villager> members = members(sl, trip);
            if (members.isEmpty()) {
                r.trip = null;
                r.nextTrip = now + 6000L;
                return;
            }
            long there = members.stream().filter(v -> v.blockPosition().distSqr(gate) < 25.0).count();
            if (there < members.size() && now < trip.getLong("Until")) {
                return;
            }
            if (there < 2) {
                // not enough came: call it off
                for (Villager v : members) {
                    VillagerLife.data(v).remove("Trip");
                    unkit(sl, v, r);
                }
                if (kind.equals("end")) {
                    // v0.17.17: the twelve eyes of ender go back to the chests
                    List<ItemStack> eyes = new ArrayList<>();
                    add(eyes, sl, "ender_eye", 12, 12);
                    VillageProgress.get(sl).deliver(r, eyes, sl.registryAccess());
                }
                r.trip = null;
                r.nextTrip = now + 6000L;
                VillageProgress.announce(sl, s.village, "遠征隊が集まらず、遠征を見送りました", false);
                return;
            }
            trip.putString("Phase", "depart");
            trip.putLong("Until", now + 600L);
            if (kind.equals("nether")) {
                light(sl, r.gate);
            } else {
                trip.putLong("Out", out(sl, s, kind, trip).asLong());
            }
            for (Villager v : members) {
                VillagerLife.data(v).putString("Trip", kind + ":depart");
            }
            VillageProgress.announce(sl, s.village, "遠征隊が" + place(trip) + "へ出発しました", kind.equals("end"));
        } else if (phase.equals("depart")) {
            List<Villager> members = members(sl, trip);
            if (members.isEmpty() || now >= trip.getLong("Until")) {
                for (Villager v : members) {
                    leave(sl, v, r);
                }
                if (kind.equals("nether")) {
                    douse(sl, r.gate);
                }
                long away = switch (kind) {
                    case "nether" -> 24000L;
                    case "end" -> 36000L;
                    case "ruin" -> 30000L;
                    default -> 12000L;
                };
                trip.putString("Phase", "away");
                trip.putLong("Back", now + away);
                VillageProgress.get(sl).setDirty();
            }
        } else if (now >= trip.getLong("Back")) {
            // a gate broken while they were away: back() brings them home the long way
            back(sl, s, r, now);
        }
    }

    private static List<Villager> members(ServerLevel sl, CompoundTag trip) {
        List<Villager> out = new ArrayList<>();
        for (Tag t : trip.getList("Members", 10)) {
            Entity e = sl.getEntity(((CompoundTag)t).getUUID("Id"));
            if (e instanceof Villager v && v.isAlive()) {
                out.add(v);
            }
        }
        return out;
    }

    /** Where a walking party heads: toward the nearest real dungeon, the stronghold for the End, or anywhere. */
    private static BlockPos out(ServerLevel sl, VillageWork.Survey s, String kind, CompoundTag trip) {
        BlockPos c = s.village.center;
        Vec3 dir = null;
        if (trip.contains("Spawner")) {
            BlockPos sp = BlockPos.of(trip.getLong("Spawner"));
            dir = new Vec3(sp.getX() - c.getX(), 0.0, sp.getZ() - c.getZ());
        } else if (kind.equals("end")) {
            BlockPos hold = sl.findNearestMapStructure(StructureTags.EYE_OF_ENDER_LOCATED, c, 100, false);
            if (hold != null) {
                dir = new Vec3(hold.getX() - c.getX(), 0.0, hold.getZ() - c.getZ());
                trip.putLong("Stronghold", hold.asLong());
            }
        }
        if (dir == null || dir.lengthSqr() < 1.0) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            dir = new Vec3(Math.cos(a), 0.0, Math.sin(a));
        }
        dir = dir.normalize().scale(48.0);
        BlockPos p = top(sl, c.offset((int)dir.x, 0, (int)dir.z));
        return p != null ? p : c.offset((int)dir.x, 0, (int)dir.z);
    }

    /**
     * Every tick for a villager on an expedition (VillagerLife.tick): walking to the gathering point, then out of the
     * village or into the gate. True while the expedition keeps the villager from its day.
     */
    static boolean member(Villager v, ServerLevel sl) {
        CompoundTag n = VillagerLife.data(v);
        String trip = n.getString("Trip");
        if (trip.isEmpty()) {
            return false;
        }
        VillageProgress.Record r = n.hasUUID("TripVillage") ? VillageProgress.get(sl).villages.get(n.getUUID("TripVillage")) : null;
        // v0.17.17: only a member of the trip under way (a tag left from a called-off trip is not)
        if (r == null || r.trip == null || !r.trip.getString("Phase").equals("muster") && !r.trip.getString("Phase").equals("depart")
            || r.trip.getList("Members", 10).stream().noneMatch(t -> ((CompoundTag)t).getUUID("Id").equals(v.getUUID()))) {
            n.remove("Trip");
            // v0.17.17: the trip is off (or gone): the armoury's kit goes back now, not never
            VillageLedger.Village home = VillageLedger.of(v);
            if (home != null) {
                unkit(sl, v, VillageProgress.get(sl).of(home));
            }
            return false;
        }
        boolean depart = r.trip.getString("Phase").equals("depart");
        String kind = r.trip.getString("Kind");
        BlockPos to = BlockPos.of(r.trip.getLong(depart && !kind.equals("nether") ? "Out" : "Gate"));
        if (depart && kind.equals("nether")) {
            to = interior(r.gate);
            if (v.distanceToSqr(Vec3.atBottomCenterOf(to)) < 4.0) {
                // stepping through, before the portal itself takes them
                leave(sl, v, r);
                return true;
            }
        } else if (depart && (v.blockPosition().distSqr(to) < 16.0 || v.blockPosition().distSqr(BlockPos.of(r.trip.getLong("Gate"))) > 1600.0)) {
            leave(sl, v, r);
            return true;
        }
        if ((v.tickCount + v.getId()) % 20 == 0) {
            VillageAI.walk(v, to, VillageAI.pace(v, depart ? VillageAI.FLEE : VillageAI.WORK), depart && kind.equals("nether") ? 0 : 2);
            n.putString("Task", depart ? place(kind) + "へ出発" : "遠征隊の集合");
        }
        return true;
    }

    /** A member steps out of the world: kept as saved data with the expedition. */
    private static void leave(ServerLevel sl, Villager v, VillageProgress.Record r) {
        if (r.trip == null) {
            return;
        }
        boolean gate = r.trip.getString("Kind").equals("nether");
        sl.sendParticles(gate ? ParticleTypes.PORTAL : ParticleTypes.POOF, v.getX(), v.getY() + 1.0, v.getZ(), 30, 0.4, 0.8, 0.4, 0.4);
        if (gate) {
            RelicEffects.sound(sl, v.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, 0.8F, 0.7F);
        }
        VillagerLife.data(v).remove("Trip");
        CompoundTag saved = new CompoundTag();
        v.saveWithoutId(saved);
        ListTag gone = r.trip.getList("Gone", 10);
        gone.add(saved);
        r.trip.put("Gone", gone);
        ListTag members = r.trip.getList("Members", 10);
        members.removeIf(t -> ((CompoundTag)t).getUUID("Id").equals(v.getUUID()));
        r.trip.put("Members", members);
        v.stopRiding();
        v.discard();
        if (gate && members.isEmpty()) {
            later(sl, r.gate, 40L);
        }
        VillageProgress.get(sl).setDirty();
    }

    // ------------------------------------------------------------------------------------- gates to put out
    private static final Map<ServerLevel, List<long[]>> DOUSE = new java.util.WeakHashMap<>();

    /** Put the gate out a little later (once the party has gone through or stepped out). */
    private static void later(ServerLevel sl, BlockPos gate, long ticks) {
        if (gate != null) {
            DOUSE.computeIfAbsent(sl, k -> new ArrayList<>()).add(new long[]{gate.asLong(), sl.getGameTime() + ticks});
        }
    }

    /** Every level tick (WorldEvents.levelTick). */
    public static void timers(ServerLevel sl) {
        List<long[]> jobs = DOUSE.get(sl);
        if (jobs == null || jobs.isEmpty()) {
            return;
        }
        long now = sl.getGameTime();
        jobs.removeIf(j -> {
            if (now < j[1]) {
                return false;
            }
            douse(sl, BlockPos.of(j[0]));
            return true;
        });
    }

    // ------------------------------------------------------------------------------------- coming back
    private static void back(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r, long now) {
        CompoundTag trip = r.trip;
        String kind = trip.getString("Kind");
        int power = trip.getInt("Power");
        ListTag gone = trip.getList("Gone", 10);
        int party = Math.max(1, gone.size());
        double danger = switch (kind) {
            case "nether" -> 0.12;
            case "end" -> 0.18;
            case "ruin" -> 0.16;
            default -> 0.05;
        };
        double need = switch (kind) {
            case "nether" -> 160.0;
            case "end" -> 260.0;
            case "ruin" -> 220.0;
            default -> 80.0;
        };
        double edge = Math.max(0.25, Math.min(2.5, power / need));
        double loss = Math.max(0.0, Math.min(0.6, danger / edge));
        boolean gateOk = kind.equals("nether") && gateIntact(sl, r.gate);
        BlockPos at;
        if (gateOk) {
            light(sl, r.gate);
            at = front(r.gate);
        } else {
            BlockPos out = trip.contains("Out") ? BlockPos.of(trip.getLong("Out")) : rally(sl, s);
            Vec3 d = Vec3.atCenterOf(out).subtract(Vec3.atCenterOf(s.village.center));
            d = d.lengthSqr() < 1.0 ? new Vec3(1.0, 0.0, 0.0) : d.normalize();
            at = top(sl, s.village.center.offset((int)(d.x * 20.0), 0, (int)(d.z * 20.0)));
            if (at == null) {
                at = s.village.center;
            }
        }
        int lost = 0;
        List<String> names = new ArrayList<>();
        for (Tag t : gone) {
            if (sl.random.nextDouble() < loss) {
                lost++;
                continue;
            }
            Villager v = (Villager)EntityType.VILLAGER.create(sl);
            if (v == null) {
                continue;
            }
            v.load((CompoundTag)t);
            v.moveTo(at.getX() + 0.5 + (sl.random.nextDouble() - 0.5) * 1.6, at.getY(), at.getZ() + 0.5 + (sl.random.nextDouble() - 0.5) * 1.6, v.getYRot(), 0.0F);
            v.setHealth(Math.max(1.0F, v.getMaxHealth() * (0.5F + sl.random.nextFloat() * 0.5F)));
            if (!sl.addFreshEntity(v)) {
                continue;
            }
            CompoundTag n = VillagerLife.data(v);
            n.remove("Trip");
            int veteran = n.getInt("Veteran") + 1;
            n.putInt("Veteran", veteran);
            n.putLong("KitUntil", now + 1200L);
            veteran(v, veteran);
            if (MobLevels.level(v) < 5) {
                MobLevels.set(v, MobLevels.level(v) + 1);
            }
            sl.sendParticles(gateOk ? ParticleTypes.PORTAL : ParticleTypes.HAPPY_VILLAGER, v.getX(), v.getY() + 1.0, v.getZ(), 20, 0.4, 0.6, 0.4, 0.2);
            names.add(v.getName().getString());
        }
        List<ItemStack> loot = loot(sl, kind, power, party - lost);
        if (kind.equals("ruin") && lost < party && trip.contains("TargetNs")) {
            loot.addAll(ruinLoot(sl, new ResourceLocation(trip.getString("TargetNs"), trip.getString("TargetPath")),
                Math.min(6, 2 + power / 100), s.village.center));
        }
        if (kind.equals("end") && lost < party) {
            // the great wish: an end ship's dragon head, and (with the dragon beaten) its egg
            if (!r.head && chance(sl, Math.min(0.55, 0.15 + power / 1000.0))) {
                add(loot, sl, "dragon_head", 1, 1);
            }
            if (!r.egg && chance(sl, Math.min(0.35, 0.05 + power / 1500.0))) {
                add(loot, sl, "dragon_egg", 1, 1);
            }
        }
        String cleared = "";
        if (kind.equals("dungeon") && trip.contains("Spawner") && lost < party) {
            cleared = clear(sl, BlockPos.of(trip.getLong("Spawner")), loot);
        }
        VillageProgress db = VillageProgress.get(sl);
        db.deliver(r, loot, sl.registryAccess());
        db.unload(r, chests(sl, s), sl.registryAccess());
        switch (kind) {
            case "nether" -> r.nethers++;
            case "end" -> r.ends++;
            case "ruin" -> r.ruins++;
            default -> r.dungeons++;
        }
        r.trip = null;
        r.nextTrip = now + (kind.equals("end") ? 48000L : 24000L);
        if (gateOk) {
            later(sl, r.gate, 60L);
        }
        db.setDirty();
        StringBuilder text = new StringBuilder("遠征隊が" + place(trip) + "から帰還しました");
        text.append(lost > 0 ? "（" + lost + "名が戻らず）" : "（全員無事）");
        text.append(cleared);
        text.append("　持ち帰り：").append(summary(loot));
        VillageProgress.announce(sl, s.village, text.toString(), kind.equals("end"));
    }

    /** A survivor's lasting toughness: +15% health and +10% attack per expedition. */
    static void veteran(Villager v, int rank) {
        AttributeInstance hp = v.getAttribute(Attributes.MAX_HEALTH);
        if (hp != null) {
            hp.removeModifier(VETERAN);
            hp.addPermanentModifier(new AttributeModifier(VETERAN, 0.15 * rank, AttributeModifier.Operation.MULTIPLY_BASE));
        }
        AttributeInstance atk = v.getAttribute(Attributes.ATTACK_DAMAGE);
        if (atk != null) {
            atk.removeModifier(VETERAN);
            atk.addPermanentModifier(new AttributeModifier(VETERAN, 0.1 * rank, AttributeModifier.Operation.MULTIPLY_BASE));
        }
    }

    /** Called from VillagerLife.tick: a member back from an expedition hands the armoury's gear in after a minute. */
    static void stow(Villager v, ServerLevel sl) {
        CompoundTag n = VillagerLife.data(v);
        if (n.contains("KitUntil") && sl.getGameTime() >= n.getLong("KitUntil") && !AdaptiveCombat.enemy(v, v.getTarget())) {
            n.remove("KitUntil");
            VillageLedger.Village village = VillageLedger.of(v);
            if (village != null) {
                unkit(sl, v, VillageProgress.get(sl).of(village));
            }
        }
    }

    /** A real dungeon near the village: its spawner broken and its chests emptied into the haul. */
    private static String clear(ServerLevel sl, BlockPos spawner, List<ItemStack> loot) {
        if (!sl.hasChunkAt(spawner) || !sl.getBlockState(spawner).is(spawner())) {
            return "";
        }
        int chests = 0;
        for (BlockPos p : BlockPos.betweenClosed(spawner.offset(-5, -2, -5), spawner.offset(5, 2, 5))) {
            if (sl.getBlockEntity(p) instanceof ChestBlockEntity box) {
                for (int i = 0; i < box.getContainerSize(); i++) {
                    if (!box.getItem(i).isEmpty()) {
                        loot.add(box.removeItem(i, box.getItem(i).getCount()));
                    }
                }
                box.setChanged();
                chests++;
            }
        }
        sl.setBlock(spawner, Blocks.AIR.defaultBlockState(), 3);
        sl.sendParticles(ParticleTypes.EXPLOSION, spawner.getX() + 0.5, spawner.getY() + 0.5, spawner.getZ() + 0.5, 1, 0.0, 0.0, 0.0, 0.0);
        return "　近くのダンジョン（" + spawner.getX() + ", " + spawner.getY() + ", " + spawner.getZ() + "）を攻略してスポナーを破壊"
            + (chests > 0 ? "、宝箱" + chests + "個を回収" : "");
    }

    // ------------------------------------------------------------------------------------- other mods' dungeons
    private static Map<String, List<ResourceLocation>> chestTables;

    /** Other mods' chest loot tables by mod, read once. */
    private static Map<String, List<ResourceLocation>> tables(ServerLevel sl) {
        if (chestTables == null) {
            Map<String, List<ResourceLocation>> m = new java.util.HashMap<>();
            for (ResourceLocation id : sl.getServer().reloadableRegistries().getKeys(net.minecraft.core.registries.Registries.LOOT_TABLE)) {
                String ns = id.getNamespace();
                if (!ns.equals("minecraft") && !ns.equals("oror_supreme_bosses") && id.getPath().contains("chest")) {
                    m.computeIfAbsent(ns, k -> new ArrayList<>()).add(id);
                }
            }
            chestTables = m;
        }
        return chestTables;
    }

    /** A modded dungeon to raid: a structure of another mod that has chest loot of its own; null when there is none. */
    private static ResourceLocation ruin(ServerLevel sl) {
        Map<String, List<ResourceLocation>> t = tables(sl);
        List<ResourceLocation> found = new ArrayList<>();
        for (ResourceLocation id : sl.registryAccess().registryOrThrow(net.minecraft.core.registries.Registries.STRUCTURE).keySet()) {
            if (t.containsKey(id.getNamespace())) {
                found.add(id);
            }
        }
        return found.isEmpty() ? null : found.get(sl.random.nextInt(found.size()));
    }

    /** A modded dungeon's chests: that mod's own loot tables rolled for real, those named like the place first. */
    private static List<ItemStack> ruinLoot(ServerLevel sl, ResourceLocation target, int rolls, BlockPos at) {
        List<ResourceLocation> all = tables(sl).getOrDefault(target.getNamespace(), List.of());
        List<ItemStack> out = new ArrayList<>();
        if (all.isEmpty()) {
            return out;
        }
        String[] words = target.getPath().replace('/', '_').split("_");
        List<ResourceLocation> like = new ArrayList<>();
        for (ResourceLocation id : all) {
            for (String w : words) {
                if (w.length() > 3 && id.getPath().contains(w)) {
                    like.add(id);
                    break;
                }
            }
        }
        List<ResourceLocation> pool = like.isEmpty() ? all : like;
        net.minecraft.world.level.storage.loot.LootParams params = new net.minecraft.world.level.storage.loot.LootParams.Builder(sl)
            .withParameter(net.minecraft.world.level.storage.loot.parameters.LootContextParams.ORIGIN, Vec3.atCenterOf(at))
            .create(net.minecraft.world.level.storage.loot.parameters.LootContextParamSets.CHEST);
        for (int i = 0; i < rolls; i++) {
            ResourceLocation id = pool.get(sl.random.nextInt(pool.size()));
            try {
                out.addAll(sl.getServer().reloadableRegistries()
                    .getLootTable(net.minecraft.resources.ResourceKey.create(net.minecraft.core.registries.Registries.LOOT_TABLE, id))
                    .getRandomItems(params, sl.random.nextLong()));
            } catch (RuntimeException ex) {
                // a table that wants more than a chest gives it: left out
            }
        }
        return out;
    }

    // ------------------------------------------------------------------------------------- the great wish
    /**
     * The great wish (悲願): the dragon egg and an end ship's dragon head. Either one in the communal chests - brought back
     * from the End, or put there by a player - is set on an altar by the centre, and the whole world hears of it.
     */
    private static void wish(ServerLevel sl, VillageWork.Survey s, VillageProgress.Record r) {
        for (int i = 0; i < 2; i++) {
            boolean egg = i == 0;
            String id = egg ? "dragon_egg" : "dragon_head";
            if ((egg ? r.egg : r.head) || s.stock(id) < 1 || take(sl, s, id, 1) < 1) {
                continue;
            }
            if (egg) {
                r.egg = true;
            } else {
                r.head = true;
            }
            VillageProgress.get(sl).setDirty();
            Block block = item(id) instanceof BlockItem b ? b.getBlock() : null;
            BlockPos altar = block == null ? null : enshrine(sl, s, block, egg ? 2 : -2);
            if (altar == null) {
                VillageProgress.get(sl).deliver(r, List.of(item(id).getDefaultInstance()), sl.registryAccess());
            }
            celebrate(sl, s, altar != null ? altar : s.village.center);
            VillageProgress.announce(sl, s.village, "村の悲願「" + (egg ? "エンダードラゴンの卵" : "エンドシップのドラゴンの頭") + "」が叶い、"
                + (altar != null ? "村の中心の祭壇に祀られました！" : "村の宝になりました！")
                + (r.egg && r.head ? "　二つの悲願を果たし、村は「竜の都」となりました" : ""), true);
        }
    }

    /** An obsidian pedestal by the centre with the treasure on it; null when there is no room. */
    private static BlockPos enshrine(ServerLevel sl, VillageWork.Survey s, Block treasure, int side) {
        BlockPos c = s.village.center;
        for (int i = 0; i < 8; i++) {
            BlockPos p = top(sl, c.offset(side + (i % 3) - 1, 0, 3 + i / 3));
            if (p == null || !sl.getBlockState(p).canBeReplaced() || !sl.getBlockState(p.above()).canBeReplaced() || !sl.getFluidState(p).isEmpty()) {
                continue;
            }
            sl.setBlock(p, Blocks.OBSIDIAN.defaultBlockState(), 3);
            sl.setBlock(p.above(), treasure.defaultBlockState(), 3);
            return p.above();
        }
        return null;
    }

    /** Fireworks over the altar; players near the village are the village's heroes for a day. */
    private static void celebrate(ServerLevel sl, VillageWork.Survey s, BlockPos at) {
        sl.sendParticles(ParticleTypes.FIREWORK, at.getX() + 0.5, at.getY() + 3.0, at.getZ() + 0.5, 120, 2.5, 2.5, 2.5, 0.15);
        sl.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, at.getX() + 0.5, at.getY() + 1.0, at.getZ() + 0.5, 80, 1.5, 1.5, 1.5, 0.4);
        RelicEffects.sound(sl, at, SoundEvents.TOTEM_USE, 1.5F, 1.0F);
        for (net.minecraft.world.entity.player.Player p : sl.getEntitiesOfClass(net.minecraft.world.entity.player.Player.class,
                new net.minecraft.world.phys.AABB(s.village.center).inflate(64.0))) {
            p.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.HERO_OF_THE_VILLAGE, 24000, 2));
            VillageReputation.change(sl, s.village, p, 200, "村の悲願の成就");
        }
    }

    // ------------------------------------------------------------------------------------- the haul
    private static void add(List<ItemStack> loot, ServerLevel sl, String id, int min, int max) {
        Item item = (Item)BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id));
        int n = min + (max > min ? sl.random.nextInt(max - min + 1) : 0);
        while (n > 0 && item != null && item != net.minecraft.world.item.Items.AIR) {
            int part = Math.min(n, item.getDefaultInstance().getMaxStackSize());
            loot.add(item.getDefaultInstance().copyWithCount(part));
            n -= part;
        }
    }

    private static boolean chance(ServerLevel sl, double p) {
        return sl.random.nextDouble() < p;
    }

    /** What a party brings back: more and rarer for a stronger party, nothing when nobody returns. */
    static List<ItemStack> loot(ServerLevel sl, String kind, int power, int survivors) {
        List<ItemStack> loot = new ArrayList<>();
        if (survivors <= 0) {
            return loot;
        }
        double f = Math.max(0.5, Math.min(3.0, power / 120.0)) * Math.min(1.0, survivors / 3.0 + 0.34);
        int k = (int)Math.round(f * 2.0);
        switch (kind) {
            case "nether" -> {
                add(loot, sl, "nether_wart", 4 * k, 10 * k);
                add(loot, sl, "blaze_rod", k, 4 * k);
                add(loot, sl, "ghast_tear", 0, k);
                add(loot, sl, "magma_cream", k, 3 * k);
                add(loot, sl, "glowstone_dust", 4 * k, 10 * k);
                add(loot, sl, "quartz", 6 * k, 16 * k);
                add(loot, sl, "gold_ingot", 2 * k, 6 * k);
                add(loot, sl, "ender_pearl", k, 3 * k);
                add(loot, sl, "obsidian", 0, 2 * k);
                add(loot, sl, "crying_obsidian", 0, k);
                add(loot, sl, "soul_sand", 0, 4 * k);
                add(loot, sl, "ancient_debris", chance(sl, 0.3 * f) ? 1 : 0, k);
                if (chance(sl, 0.1 * f)) {
                    add(loot, sl, "netherite_scrap", 1, 2);
                }
                if (chance(sl, 0.12 * f)) {
                    add(loot, sl, "netherite_upgrade_smithing_template", 1, 1);
                }
            }
            case "end" -> {
                add(loot, sl, "shulker_shell", 2 * k, 4 * k);
                add(loot, sl, "chorus_fruit", 4 * k, 12 * k);
                add(loot, sl, "ender_pearl", 2 * k, 6 * k);
                add(loot, sl, "purpur_block", 8, 16 * k);
                add(loot, sl, "end_stone", 8, 24);
                add(loot, sl, "dragon_breath", 0, k);
                add(loot, sl, "diamond", k, 3 * k);
                add(loot, sl, "emerald", 2 * k, 6 * k);
                if (chance(sl, 0.25 * f)) {
                    add(loot, sl, "elytra", 1, 1);
                }
            }
            default -> {
                add(loot, sl, "bone", 2 * k, 6 * k);
                add(loot, sl, "string", k, 4 * k);
                add(loot, sl, "gunpowder", k, 4 * k);
                add(loot, sl, "iron_ingot", k, 4 * k);
                add(loot, sl, "gold_ingot", 0, 2 * k);
                add(loot, sl, "coal", 2 * k, 6 * k);
                add(loot, sl, "redstone", 0, 4 * k);
                add(loot, sl, "emerald", k, 4 * k);
                add(loot, sl, "ender_pearl", 0, k);
                add(loot, sl, "obsidian", 2, 3 + 2 * k);
                add(loot, sl, "flint", 0, 3);
                add(loot, sl, "paper", 0, 3);
                if (chance(sl, 0.25 * f)) {
                    add(loot, sl, "diamond", 1, k);
                }
                if (chance(sl, 0.15 * f)) {
                    add(loot, sl, "golden_apple", 1, 1);
                }
            }
        }
        return loot;
    }

    static String summary(List<ItemStack> loot) {
        Map<String, Integer> sum = new LinkedHashMap<>();
        for (ItemStack st : loot) {
            sum.merge(st.getHoverName().getString(), st.getCount(), Integer::sum);
        }
        if (sum.isEmpty()) {
            return "なし";
        }
        StringBuilder b = new StringBuilder();
        int i = 0;
        for (Map.Entry<String, Integer> e : sum.entrySet()) {
            if (i++ >= 10) {
                b.append(" ほか");
                break;
            }
            if (b.length() > 0) {
                b.append("、");
            }
            b.append(e.getKey()).append("×").append(e.getValue());
        }
        return b.toString();
    }

    /** Take up to n of an item (by vanilla id) out of the communal chests; how many were taken. */
    static int take(ServerLevel sl, VillageWork.Survey s, String id, int n) {
        Item item = (Item)BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id));
        return take(sl, s, st -> st.is(item), n);
    }

    static int take(ServerLevel sl, VillageWork.Survey s, java.util.function.Predicate<ItemStack> is, int n) {
        int got = 0;
        for (Container box : chests(sl, s)) {
            for (int i = 0; i < box.getContainerSize() && got < n; i++) {
                ItemStack st = box.getItem(i);
                if (!st.isEmpty() && is.test(st)) {
                    got += box.removeItem(i, Math.min(n - got, st.getCount())).getCount();
                    box.setChanged();
                }
            }
        }
        return got;
    }

    // ------------------------------------------------------------------------------------- the nether gate
    /*
     * The gate is a 4x5 obsidian frame along x without corners: bottom (1,0) (2,0), top (1,4) (2,4), sides (0,1..3) and
     * (3,1..3); the opening (1..2, 1..3). r.gate is the frame's (0,0).
     */
    static List<BlockPos> frame(BlockPos o) {
        List<BlockPos> out = new ArrayList<>();
        out.add(o.offset(1, 0, 0));
        out.add(o.offset(2, 0, 0));
        for (int y = 1; y <= 3; y++) {
            out.add(o.offset(0, y, 0));
            out.add(o.offset(3, y, 0));
        }
        out.add(o.offset(1, 4, 0));
        out.add(o.offset(2, 4, 0));
        return out;
    }

    static BlockPos interior(BlockPos o) {
        return o.offset(1, 1, 0);
    }

    /** Where a party stands before the gate (two blocks in front of its opening). */
    static BlockPos front(BlockPos o) {
        return o == null ? null : o.offset(1, 0, -2);
    }

    static boolean gateIntact(ServerLevel sl, BlockPos o) {
        if (o == null || !sl.hasChunkAt(o)) {
            return false;
        }
        for (BlockPos p : frame(o)) {
            if (!sl.getBlockState(p).is(Blocks.OBSIDIAN)) {
                return false;
            }
        }
        return true;
    }

    /** Light the gate: fire in the opening makes the portal (as flint and steel does). */
    static void light(ServerLevel sl, BlockPos o) {
        if (!gateIntact(sl, o)) {
            return;
        }
        BlockPos p = interior(o);
        if (sl.getBlockState(p).isAir()) {
            sl.setBlock(p, Blocks.FIRE.defaultBlockState(), 11);
            RelicEffects.sound(sl, p, SoundEvents.FIRECHARGE_USE, 1.0F, 1.0F);
        }
    }

    /** Put the portal out again. */
    static void douse(ServerLevel sl, BlockPos o) {
        if (o == null || !sl.hasChunkAt(o)) {
            return;
        }
        for (int x = 1; x <= 2; x++) {
            for (int y = 1; y <= 3; y++) {
                BlockPos p = o.offset(x, y, 0);
                BlockState st = sl.getBlockState(p);
                if (!st.isAir() && !st.is(Blocks.OBSIDIAN)) {
                    sl.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                }
            }
        }
    }

    private static Item item(String id) {
        return (Item)BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id));
    }

    private static Block spawner() {
        return item("spawner") instanceof BlockItem b ? b.getBlock() : Blocks.AIR;
    }

    /** A spot for the gate: 4 wide and 5 high of open air on natural ground near the centre, room before and behind. */
    static BlockPos gateSpot(Villager v, ServerLevel sl, VillageWork.Survey s) {
        BlockPos c = s.village.center;
        for (int i = 0; i < 12; i++) {
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            double d = 8.0 + sl.random.nextDouble() * 8.0;
            BlockPos o = top(sl, c.offset((int)Math.round(Math.cos(a) * d), 0, (int)Math.round(Math.sin(a) * d)));
            if (o == null || Math.abs(o.getY() - c.getY()) > 4) {
                continue;
            }
            boolean ok = true;
            for (int x = -1; x <= 4 && ok; x++) {
                for (int z = -2; z <= 2 && ok; z++) {
                    for (int y = 0; y <= 4 && ok; y++) {
                        BlockPos p = o.offset(x, y, z);
                        ok = sl.getBlockState(p).canBeReplaced() && sl.getFluidState(p).isEmpty() && VillagerLife.editable(v, sl, p);
                    }
                    BlockPos ground = o.offset(x, -1, z);
                    ok = ok && !sl.getBlockState(ground).canBeReplaced();
                }
            }
            if (ok) {
                return o;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------------------------- wandering parties
    /**
     * Now and then (about once in two days per player) a party of some village's veterans is met in the wild; sometimes
     * a rival party comes the other way and they fight. A player every village knows as an attacker of a party is hunted:
     * parties come for them far more often, wherever they are.
     */
    public static void wanderers(ServerLevel sl) {
        if (!sl.dimension().location().getPath().equals("overworld") || sl.getGameTime() % 2400L != 1200L) {
            return;
        }
        for (net.minecraft.server.level.ServerPlayer p : sl.players()) {
            boolean hunted = !p.isCreative() && VillageFeuds.outlaw(sl, p.getUUID());
            if (p.isSpectator() || sl.random.nextDouble() > (hunted ? 0.2 : 0.06)) {
                continue;
            }
            if (!sl.getEntitiesOfClass(Villager.class, p.getBoundingBox().inflate(160.0), v -> v.getPersistentData().getBoolean("OrorWanderer")).isEmpty()) {
                continue;
            }
            VillageLedger ledger = VillageLedger.get(sl);
            if (!hunted && ledger.nearest(p.blockPosition()) != null) {
                // inside a village they would be at home, not passing through
                continue;
            }
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            BlockPos at = open(sl, p.blockPosition().offset((int)(Math.cos(a) * 40.0), 0, (int)(Math.sin(a) * 40.0)));
            if (at == null) {
                continue;
            }
            // hunters make for the outlaw; others are only passing
            double heading = hunted ? Math.atan2(p.getZ() - at.getZ(), p.getX() - at.getX()) : sl.random.nextDouble() * Math.PI * 2.0;
            List<Villager> one = party(sl, at, heading, null, hunted ? "の追っ手" : "の遠征隊", 3 + sl.random.nextInt(3), hunted);
            if (one.isEmpty() || hunted || sl.random.nextDouble() >= 0.25) {
                continue;
            }
            // a rival party on the same road, coming the other way
            BlockPos far = open(sl, at.offset((int)(Math.cos(heading) * 36.0), 0, (int)(Math.sin(heading) * 36.0)));
            if (far == null) {
                continue;
            }
            CompoundTag first = one.get(0).getPersistentData();
            List<Villager> two = party(sl, far, heading + Math.PI, first.getUUID("OrorVillage"), "の遠征隊", 3 + sl.random.nextInt(3), false);
            if (!two.isEmpty()) {
                UUID a1 = first.getUUID("OrorParty");
                UUID b1 = two.get(0).getPersistentData().getUUID("OrorParty");
                for (Villager v : one) {
                    v.getPersistentData().putUUID("OrorRival", b1);
                }
                for (Villager v : two) {
                    v.getPersistentData().putUUID("OrorRival", a1);
                }
            }
        }
    }

    /** Dry open ground at the surface there, or null. */
    private static BlockPos open(ServerLevel sl, BlockPos p) {
        BlockPos at = top(sl, p);
        return at == null || !sl.getFluidState(at.below()).isEmpty() || !sl.getBlockState(at).canBeReplaced() ? null : at;
    }

    /** A party of some village (not notFrom) in the wild: netherite, the highest level, veterans; the first is the leader. */
    static List<Villager> party(ServerLevel sl, BlockPos at, double heading, UUID notFrom, String title, int size, boolean hunters) {
        VillageLedger ledger = VillageLedger.get(sl);
        List<VillageLedger.Village> known = new ArrayList<>(ledger.villages.values());
        known.removeIf(x -> x.id.equals(notFrom));
        VillageLedger.Village home = known.isEmpty() ? null : known.get(sl.random.nextInt(known.size()));
        for (int i = 0; home == null && i < 8; i++) {
            // a far village nobody has seen; v0.17.17: never the rival's own (they would count as allies and not fight)
            VillageLedger.Village far = ledger.register(at.offset((sl.random.nextInt(2) == 0 ? 1 : -1) * (3000 + i * 700), 0,
                (sl.random.nextInt(2) == 0 ? 1 : -1) * (3000 + i * 700)));
            home = far.id.equals(notFrom) ? null : far;
        }
        if (home == null) {
            return new ArrayList<>();
        }
        String name = VillageProgress.get(sl).of(home).name();
        UUID id = UUID.randomUUID();
        List<Villager> out = new ArrayList<>();
        for (int i = 0; i < size; i++) {
            Villager v = (Villager)EntityType.VILLAGER.create(sl);
            if (v == null) {
                break;
            }
            String job = STRONG.get(sl.random.nextInt(STRONG.size()));
            net.minecraft.world.entity.npc.VillagerProfession prof = (net.minecraft.world.entity.npc.VillagerProfession)BuiltInRegistries.VILLAGER_PROFESSION
                .get(ResourceLocation.withDefaultNamespace(job));
            v.setVillagerData(v.getVillagerData().setProfession(prof).setLevel(5));
            v.moveTo(at.getX() + 0.5 + i % 2, at.getY(), at.getZ() + 0.5 + i / 2, (float)Math.toDegrees(heading), 0.0F);
            CompoundTag root = v.getPersistentData();
            root.putBoolean("OrorWanderer", true);
            root.putUUID("OrorVillage", home.id);
            root.putUUID("OrorParty", id);
            root.putBoolean("OrorLeader", i == 0);
            root.putBoolean("OrorHunter", hunters);
            root.putLong("OrorWanderUntil", sl.getGameTime() + 24000L);
            root.putDouble("OrorWanderHeading", heading);
            v.setCustomName(net.minecraft.network.chat.Component.literal(name + title));
            v.setCustomNameVisible(true);
            v.setPersistenceRequired();
            MobLevels.set(v, 6);
            veteran(v, hunters ? 8 : 6);
            dress(sl, v, i == 0);
            v.setHealth(v.getMaxHealth());
            if (sl.addFreshEntity(v)) {
                out.add(v);
            }
        }
        return out;
    }

    /** Netherite, enchanted; the leader carries a Superb Warfare gun where the mod is installed, the rest a blade or a bow. */
    static void dress(ServerLevel sl, Villager v, boolean leader) {
        String[] armour = {"netherite_helmet", "netherite_chestplate", "netherite_leggings", "netherite_boots"};
        EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};
        var enchants = sl.registryAccess().registryOrThrow(net.minecraft.core.registries.Registries.ENCHANTMENT);
        for (int i = 0; i < 4; i++) {
            ItemStack st = item(armour[i]).getDefaultInstance();
            st.enchant(enchants.getHolderOrThrow(net.minecraft.world.item.enchantment.Enchantments.PROTECTION), 4);
            st.enchant(enchants.getHolderOrThrow(net.minecraft.world.item.enchantment.Enchantments.UNBREAKING), 3);
            v.setItemSlot(slots[i], st);
            v.setDropChance(slots[i], 0.0F);
        }
        ItemStack weapon = leader ? VillageArms.gun(sl, sl.random.nextInt(3) + 2) : ItemStack.EMPTY;
        if (weapon.isEmpty()) {
            weapon = item(VillagerRoles.profession(v).equals("fletcher") ? "bow" : (sl.random.nextInt(2) == 0 ? "netherite_sword" : "netherite_axe"))
                .getDefaultInstance();
            weapon.enchant(enchants.getHolderOrThrow(VillagerRoles.profession(v).equals("fletcher")
                ? net.minecraft.world.item.enchantment.Enchantments.POWER : net.minecraft.world.item.enchantment.Enchantments.SHARPNESS), 5);
        }
        v.setItemSlot(EquipmentSlot.MAINHAND, weapon);
        v.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
        CompoundTag mind = MobMind.data(v);
        mind.putBoolean("Armed", true);
        mind.putBoolean("VillageGeared", true);
        mind.putBoolean("OriginalAuto", false);
        mind.putLong("VillageGearUntil", Long.MAX_VALUE);
    }

    /**
     * A wandering party's day (VillagerLife.tick, once a second): on along its heading by day, round a campfire by night,
     * gone once its journey is over and no player is near.
     */
    static void wander(Villager v, ServerLevel sl) {
        CompoundTag root = v.getPersistentData();
        long now = sl.getGameTime();
        // v0.17.16: at war with a player, at feud with another party, or after an outlaw
        if (VillageFeuds.wander(v, sl)) {
            return;
        }
        if (root.hasUUID("OrorCaravan") && !AdaptiveCombat.enemy(v, v.getTarget()) && WanderingTraders.escort(v, sl)) {
            return;
        }
        if (now >= root.getLong("OrorWanderUntil") && sl.getNearestPlayer(v, 64.0) == null) {
            unCamp(sl, root);
            v.discard();
            return;
        }
        if (AdaptiveCombat.enemy(v, v.getTarget())) {
            VillagerLife.data(v).putString("Task", "交戦中");
            return;
        }
        if (!sl.isDay()) {
            BlockPos camp = root.contains("OrorCamp") ? BlockPos.of(root.getLong("OrorCamp")) : null;
            if (camp == null) {
                camp = v.blockPosition();
                root.putLong("OrorCamp", camp.asLong());
                Block fire = item("campfire") instanceof BlockItem b ? b.getBlock() : null;
                if (fire != null && sl.getGameRules().getBoolean(net.minecraft.world.level.GameRules.RULE_MOBGRIEFING) && sl.getBlockState(camp).canBeReplaced()
                    && !sl.getBlockState(camp.below()).canBeReplaced() && sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(6.0),
                        x -> x != v && x.getPersistentData().contains("OrorCampFire")).isEmpty()) {
                    BlockPos spot = camp.offset(sl.random.nextInt(2) == 0 ? 2 : -2, 0, sl.random.nextInt(2) == 0 ? 1 : -1);
                    if (sl.getBlockState(spot).canBeReplaced() && !sl.getBlockState(spot.below()).canBeReplaced()) {
                        sl.setBlock(spot, fire.defaultBlockState(), 3);
                        root.putLong("OrorCampFire", spot.asLong());
                    }
                }
            }
            if (v.blockPosition().distSqr(camp) > 16.0) {
                VillageAI.walk(v, camp, VillageAI.pace(v, VillageAI.WORK), 2);
            }
            VillagerLife.data(v).putString("Task", "野営");
            return;
        }
        unCamp(sl, root);
        double heading = root.getDouble("OrorWanderHeading") + (sl.random.nextDouble() - 0.5) * 0.2;
        root.putDouble("OrorWanderHeading", heading);
        BlockPos to = top(sl, v.blockPosition().offset((int)(Math.cos(heading) * 12.0), 0, (int)(Math.sin(heading) * 12.0)));
        if (to != null && (v.tickCount + v.getId()) % 100 < 20) {
            VillageAI.walk(v, to, VillageAI.pace(v, VillageAI.WORK), 2);
        }
        VillagerLife.data(v).putString("Task", "遠征の旅");
    }

    private static void unCamp(ServerLevel sl, CompoundTag root) {
        if (root.contains("OrorCampFire")) {
            BlockPos fire = BlockPos.of(root.getLong("OrorCampFire"));
            if (sl.hasChunkAt(fire) && sl.getBlockState(fire).is(VillageWork.campfire())) {
                sl.setBlock(fire, Blocks.AIR.defaultBlockState(), 3);
            }
            root.remove("OrorCampFire");
        }
        root.remove("OrorCamp");
    }
}
