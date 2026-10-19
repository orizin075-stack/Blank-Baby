package jp.oror.reborn;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.raid.Raid;
import net.minecraft.world.entity.raid.Raider;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.living.LivingHurtEvent;

/**
 * Raids as the vanguard of something bigger (v0.17.16).
 * - Every raid on a village brings a messenger (伝令兵): a glowing pillager that keeps to the back and does not fight.
 *   When the raid is beaten (or going badly, or after two minutes) it starts a ten-second ritual to teleport home to its
 *   headquarters; every blow sets it back. Kill it before it finishes.
 * - The raid can be won either way, but a messenger that gets home reports the village, and some nights later the
 *   headquarters sends a horde: a hundred and more (more for a bigger, grander village, and half as many again for every
 *   report since), arriving in waves around the village. Its soldiers are strong on their own - higher levels, double
 *   health, iron, diamond then netherite armour as the reports pile up - and come with monstrous weapons (netherite axes
 *   past sharpness V with fire aspect, piercing multishot crossbows, and in the elites' hands relic weapons). The horde has
 *   a messenger of its own.
 * - Beating a horde makes the players there heroes of the village.
 */
public final class VillageRaids {
    private static final ResourceLocation MIGHT = new ResourceLocation("oror_supreme_bosses", "horde_might");
    private static final java.util.Map<ServerLevel, Set<Integer>> SEEN = new java.util.WeakHashMap<>();
    private static final int CAP = 48;
    private static final String[][] SOLDIERS = {
        {"pillager", "38"}, {"vindicator", "38"}, {"witch", "8"}, {"evoker", "7"}, {"ravager", "5"}, {"illusioner", "4"}
    };

    private VillageRaids() {
    }

    /** AdaptiveCombat leaves messengers alone: they do not fight. */
    static boolean driven(Mob m) {
        return m.getPersistentData().contains("OrorMessenger", 10);
    }

    // ------------------------------------------------------------------------------------- every tick
    /** VillagerLife.tick hands every other entity here: raiders, messengers and horde soldiers. */
    static void tick(Entity e) {
        if (!(e instanceof Mob m) || !(m.level() instanceof ServerLevel sl) || !m.isAlive()) {
            return;
        }
        CompoundTag root = m.getPersistentData();
        if (root.contains("OrorMessenger", 10)) {
            messenger(sl, m, root.getCompound("OrorMessenger"));
            return;
        }
        if (root.hasUUID("OrorHorde")) {
            if (m.tickCount % 40 == Math.floorMod(m.getId(), 40)) {
                march(sl, m, root.getUUID("OrorHorde"));
            }
            return;
        }
        if (e instanceof Raider r && r.tickCount % 40 == Math.floorMod(r.getId(), 40) && (Boolean)RebornConfig.VILLAGE_LIFE.get()) {
            Raid raid = r.getCurrentRaid();
            if (raid != null && !raid.isOver() && SEEN.computeIfAbsent(sl, k -> new HashSet<>()).add(raid.getId())) {
                vanguard(sl, raid, r);
            }
        }
    }

    /** A new raid: its messenger joins it (unless one is already there from before a restart). */
    private static void vanguard(ServerLevel sl, Raid raid, Raider r) {
        BlockPos c = raid.getCenter();
        int id = raid.getId();
        if (!sl.getEntitiesOfClass(Mob.class, new AABB(c).inflate(160.0, 64.0, 160.0),
                x -> x.getPersistentData().contains("OrorMessenger", 10) && x.getPersistentData().getCompound("OrorMessenger").getInt("Raid") == id).isEmpty()) {
            return;
        }
        VillageLedger.Village village = VillageLedger.get(sl).register(c);
        VillageProgress db = VillageProgress.get(sl);
        VillageProgress.Record rec = db.of(village);
        if (rec.raidMessenger == id) {
            // this raid already had its messenger (before a restart)
            return;
        }
        rec.raidMessenger = id;
        db.setDirty();
        CompoundTag tag = new CompoundTag();
        tag.putString("From", "raid");
        tag.putInt("Raid", id);
        if (spawnMessenger(sl, village, r.blockPosition(), tag)) {
            for (Player p : sl.getEntitiesOfClass(Player.class, new AABB(c).inflate(128.0))) {
                p.displayClientMessage(Component.literal("§e襲撃隊（先鋒隊）の中に、光る伝令兵がいる。本部へ逃げ帰られる前に倒せ"), false);
            }
        }
    }

    private static boolean spawnMessenger(ServerLevel sl, VillageLedger.Village village, BlockPos at, CompoundTag tag) {
        Mob m = (Mob)EntityType.PILLAGER.create(sl);
        if (m == null) {
            return false;
        }
        m.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, sl.random.nextFloat() * 360.0F, 0.0F);
        m.setCustomName(Component.literal("§e伝令兵"));
        m.setCustomNameVisible(true);
        m.setPersistenceRequired();
        // a runner, not a fighter: never one of the elites (whose health is in the hundreds)
        MobLevels.set(m, 3);
        m.addEffect(new MobEffectInstance(MobEffects.GLOWING, 72000, 0));
        m.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 72000, 0));
        if (m instanceof Raider r) {
            r.setCanJoinRaid(false);
        }
        tag.putUUID("Village", village.id);
        tag.putLong("Since", sl.getGameTime());
        tag.putString("Phase", "watch");
        tag.putInt("Progress", 0);
        m.getPersistentData().put("OrorMessenger", tag);
        return sl.addFreshEntity(m);
    }

    // ------------------------------------------------------------------------------------- the messenger
    private static void messenger(ServerLevel sl, Mob m, CompoundTag tag) {
        long now = sl.getGameTime();
        m.setTarget(null);
        VillageLedger.Village village = tag.hasUUID("Village") ? VillageLedger.get(sl).villages.get(tag.getUUID("Village")) : null;
        BlockPos c = village != null ? village.center : m.blockPosition();
        String phase = tag.getString("Phase");
        if (phase.equals("watch")) {
            boolean over;
            if (tag.getString("From").equals("raid")) {
                Raid raid = sl.getRaids().get(tag.getInt("Raid"));
                over = raid == null || raid.isOver();
            } else {
                VillageProgress.Record r = village != null ? VillageProgress.get(sl).villages.get(village.id) : null;
                over = r == null || r.horde == null;
            }
            if (over || now - tag.getLong("Since") > 2400L || m.getHealth() < m.getMaxHealth() * 0.6F) {
                tag.putString("Phase", "ritual");
                tag.putInt("Progress", 0);
                warn(sl, m, 10);
                return;
            }
            if (m.tickCount % 10 == 0) {
                // at the back: away from whoever comes near, otherwise some 28 blocks out from the centre
                Player near = sl.getNearestPlayer(m, 14.0);
                Vec3 to;
                if (near != null) {
                    Vec3 away = m.position().subtract(near.position()).multiply(1.0, 0.0, 1.0);
                    to = m.position().add(away.lengthSqr() < 1.0E-4 ? new Vec3(8.0, 0.0, 0.0) : away.normalize().scale(10.0));
                } else {
                    Vec3 out = m.position().subtract(Vec3.atCenterOf(c)).multiply(1.0, 0.0, 1.0);
                    out = out.lengthSqr() < 1.0E-4 ? new Vec3(1.0, 0.0, 0.0) : out.normalize();
                    to = Vec3.atCenterOf(c).add(out.scale(28.0));
                }
                m.getNavigation().moveTo(to.x, m.getY(), to.z, near != null ? 0.95 : 0.7);
            }
            return;
        }
        // the ritual: rooted, ten seconds, set back by every blow
        m.getNavigation().stop();
        m.setDeltaMovement(0.0, m.getDeltaMovement().y, 0.0);
        int progress = tag.getInt("Progress") + 1;
        tag.putInt("Progress", progress);
        if (m.tickCount % 4 == 0) {
            sl.sendParticles(ParticleTypes.PORTAL, m.getX(), m.getY() + 1.0, m.getZ(), 20, 0.6, 1.0, 0.6, 0.6);
            sl.sendParticles(ParticleTypes.REVERSE_PORTAL, m.getX(), m.getY() + 0.2, m.getZ(), 6, 0.4, 0.1, 0.4, 0.05);
            sl.sendParticles(ParticleTypes.ENCHANT, m.getX(), m.getY() + 2.2, m.getZ(), 10, 0.5, 0.3, 0.5, 0.5);
        }
        if (progress % 40 == 1) {
            RelicEffects.sound(sl, m.blockPosition(), SoundEvents.EVOKER_PREPARE_SUMMON, 1.5F, 0.6F);
        }
        if (progress % 20 == 0) {
            warn(sl, m, (200 - progress) / 20);
        }
        if (progress >= 200) {
            escape(sl, m, tag, village);
        }
    }

    private static void warn(ServerLevel sl, Mob m, int seconds) {
        Component line = Component.literal("§e伝令兵が本部へ転移しようとしている！ あと" + Math.max(0, seconds) + "秒　（倒さないと本部に報告される）");
        for (Player p : sl.getEntitiesOfClass(Player.class, m.getBoundingBox().inflate(96.0))) {
            p.displayClientMessage(line, true);
        }
    }

    /** Home with the report: the village is marked, and a horde will come (bigger with every report). */
    private static void escape(ServerLevel sl, Mob m, CompoundTag tag, VillageLedger.Village village) {
        sl.sendParticles(ParticleTypes.PORTAL, m.getX(), m.getY() + 1.0, m.getZ(), 80, 0.5, 1.0, 0.5, 1.0);
        RelicEffects.sound(sl, m.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, 1.5F, 0.6F);
        m.discard();
        if (village == null) {
            return;
        }
        VillageProgress db = VillageProgress.get(sl);
        VillageProgress.Record r = db.of(village);
        r.reports++;
        if (r.hordeAt <= 0L) {
            r.hordeAt = sl.getGameTime() + 6000L + sl.random.nextInt(18000);
        }
        db.setDirty();
        VillageProgress.announce(sl, village, "伝令兵が本部へ逃げ帰った……村は本部に目を付けられた。近いうちに大軍（" + size(sl, village, r) + "人規模）が押し寄せる", false);
    }

    /** VillageRaids.hurt (WorldEvents.damage): a blow sets a ritual back by two and a half seconds. */
    static void hurt(LivingHurtEvent e) {
        CompoundTag root = e.getEntity().getPersistentData();
        if (root.contains("OrorMessenger", 10)) {
            CompoundTag tag = root.getCompound("OrorMessenger");
            if (tag.getString("Phase").equals("ritual")) {
                tag.putInt("Progress", Math.max(0, tag.getInt("Progress") - 50));
            }
        }
    }

    /** VillageReputation.death: a messenger cut down, a horde soldier fallen. */
    static void died(LivingDeathEvent e) {
        if (!(e.getEntity().level() instanceof ServerLevel sl)) {
            return;
        }
        CompoundTag root = e.getEntity().getPersistentData();
        if (root.contains("OrorMessenger", 10)) {
            for (Player p : sl.getEntitiesOfClass(Player.class, e.getEntity().getBoundingBox().inflate(96.0))) {
                p.displayClientMessage(Component.literal("§a伝令兵を討ち取った。本部に知られずに済んだ"), false);
            }
        } else if (root.hasUUID("OrorHorde")) {
            VillageProgress.Record r = VillageProgress.get(sl).villages.get(root.getUUID("OrorHorde"));
            if (r != null && r.horde != null) {
                r.horde.putInt("Killed", r.horde.getInt("Killed") + 1);
                VillageProgress.get(sl).setDirty();
            }
        }
        if (root.getBoolean("OrorWarlord")) {
            warlordFallen(sl, e.getEntity().blockPosition());
        }
    }

    /**
     * v0.17.17: the commander of an illager city or fortress (the headquarters) is killed: the villages around (within
     * 2500 blocks) are no longer marked, and a horde on its way turns back.
     */
    private static void warlordFallen(ServerLevel sl, BlockPos at) {
        VillageProgress db = VillageProgress.get(sl);
        VillageLedger ledger = VillageLedger.get(sl);
        int freed = 0;
        for (VillageProgress.Record r : new ArrayList<>(db.villages.values())) {
            VillageLedger.Village v = ledger.villages.get(r.id);
            if (v == null || v.center.distSqr(at) > 2500.0 * 2500.0 || r.reports <= 0 && r.hordeAt <= 0L && r.horde == null) {
                continue;
            }
            r.reports = 0;
            r.hordeAt = 0L;
            if (r.horde != null) {
                // the soldiers still out go home (VillageRaids.run sends them off)
                r.horde.putInt("Elapsed", 40000);
            }
            freed++;
        }
        db.setDirty();
        Component line = Component.literal("【朗報】邪悪な村人の本部の将が討たれた" + (freed > 0 ? "。周りの村々（" + freed + "）への大軍の侵攻は止まった" : ""));
        for (Object o : sl.getServer().getPlayerList().getPlayers()) {
            if (o instanceof net.minecraft.server.level.ServerPlayer p) {
                p.sendSystemMessage(line);
            }
        }
    }

    private static final net.minecraft.tags.TagKey<net.minecraft.world.level.levelgen.structure.Structure> HEADQUARTERS =
        net.minecraft.tags.TagKey.create(Registries.STRUCTURE, new ResourceLocation("oror_supreme_bosses", "illager_headquarters"));

    /** The nearest illager city or fortress (the horde's headquarters), or null. */
    private static BlockPos headquarters(ServerLevel sl, BlockPos from) {
        try {
            return sl.findNearestMapStructure(HEADQUARTERS, from, 64, false);
        } catch (RuntimeException ex) {
            return null;
        }
    }

    private static String bearing(double dx, double dz) {
        String[] names = {"東", "南東", "南", "南西", "西", "北西", "北", "北東"};
        double a = Math.toDegrees(Math.atan2(dz, dx));
        return names[Math.floorMod((int)Math.round(a / 45.0), 8)];
    }

    // ------------------------------------------------------------------------------------- the horde
    private static int size(ServerLevel sl, VillageLedger.Village village, VillageProgress.Record r) {
        VillageWork.Survey s = VillageWork.cached(village.id);
        int population = s != null ? s.population : 8;
        double base = 100.0 + population * 6.0 + r.stage * 20.0;
        return (int)Math.min(600.0, base * (1.0 + 0.5 * Math.max(0, r.reports - 1)));
    }

    /** WorldEvents.levelTick (once a second): hordes coming at night, and the ones under way while players are there. */
    static void levelTick(ServerLevel sl) {
        if (sl.getGameTime() % 20L != 7L) {
            return;
        }
        VillageProgress db = VillageProgress.get(sl);
        VillageLedger ledger = VillageLedger.get(sl);
        for (VillageProgress.Record r : new ArrayList<>(db.villages.values())) {
            if (r.hordeAt <= 0L && r.horde == null) {
                continue;
            }
            VillageLedger.Village v = ledger.villages.get(r.id);
            if (v == null || !sl.hasChunkAt(v.center)) {
                continue;
            }
            boolean watched = !sl.getEntitiesOfClass(Player.class, new AABB(v.center).inflate(160.0, 96.0, 160.0), p -> !p.isSpectator()).isEmpty();
            if (!watched) {
                continue;
            }
            if (r.horde == null) {
                if (sl.getGameTime() >= r.hordeAt && !sl.isDay()) {
                    start(sl, db, r, v);
                }
            } else {
                run(sl, db, r, v);
            }
        }
    }

    private static void start(ServerLevel sl, VillageProgress db, VillageProgress.Record r, VillageLedger.Village v) {
        CompoundTag h = new CompoundTag();
        h.putInt("Total", size(sl, v, r));
        h.putInt("Spawned", 0);
        h.putInt("Killed", 0);
        h.putInt("Elapsed", 0);
        h.putInt("Reports", Math.max(1, r.reports));
        // v0.17.17: from the nearest illager city or fortress, if there is one
        BlockPos hq = headquarters(sl, v.center);
        String from = "";
        if (hq != null && hq.distSqr(v.center) > 64.0) {
            double dx = hq.getX() - v.center.getX();
            double dz = hq.getZ() - v.center.getZ();
            h.putDouble("Angle", Math.atan2(dz, dx));
            h.putLong("Hq", hq.asLong());
            from = "　本部は" + bearing(dx, dz) + "に約" + (int)Math.sqrt(dx * dx + dz * dz) + "ブロック（その将を討てば侵攻は止まる）";
        } else {
            h.putDouble("Angle", sl.random.nextDouble() * Math.PI * 2.0);
        }
        r.horde = h;
        r.hordeAt = 0L;
        db.setDirty();
        RelicEffects.sound(sl, v.center, SoundEvents.ENDER_DRAGON_GROWL, 3.0F, 0.5F);
        VillageProgress.announce(sl, v, "【急報】本部の大軍（" + h.getInt("Total") + "人）が攻めてきた！" + from, true);
    }

    private static void run(ServerLevel sl, VillageProgress db, VillageProgress.Record r, VillageLedger.Village v) {
        CompoundTag h = r.horde;
        int elapsed = h.getInt("Elapsed") + 20;
        h.putInt("Elapsed", elapsed);
        List<Mob> alive = sl.getEntitiesOfClass(Mob.class, new AABB(v.center).inflate(192.0, 96.0, 192.0),
            m -> m.isAlive() && m.getPersistentData().hasUUID("OrorHorde") && v.id.equals(m.getPersistentData().getUUID("OrorHorde")));
        int total = h.getInt("Total");
        int spawned = h.getInt("Spawned");
        if (elapsed > 36000) {
            for (Mob m : alive) {
                sl.sendParticles(ParticleTypes.POOF, m.getX(), m.getY() + 1.0, m.getZ(), 10, 0.3, 0.6, 0.3, 0.02);
                m.discard();
            }
            r.horde = null;
            db.setDirty();
            VillageProgress.announce(sl, v, "本部の大軍は引き上げていった", false);
            return;
        }
        if (spawned >= total && alive.isEmpty()) {
            r.horde = null;
            r.hordesBeaten++;
            db.setDirty();
            for (Player p : sl.getEntitiesOfClass(Player.class, new AABB(v.center).inflate(128.0))) {
                p.addEffect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, 48000, 4));
                VillageReputation.change(sl, v, p, 300, "本部の大軍の撃退");
            }
            VillageProgress.announce(sl, v, "本部の大軍（" + total + "人）を撃退した！", true);
            return;
        }
        if (elapsed % 40 == 0 && spawned < total && alive.size() < CAP) {
            int n = Math.min(8, Math.min(total - spawned, CAP - alive.size()));
            int arrived = 0;
            for (int i = 0; i < n; i++) {
                arrived += soldier(sl, v, h) ? 1 : 0;
            }
            if (arrived == 0) {
                // v0.17.17: that side is water or not loaded: the horde comes round another way
                h.putDouble("Angle", sl.random.nextDouble() * Math.PI * 2.0);
            }
            n = arrived;
            h.putInt("Spawned", spawned + n);
            db.setDirty();
            if (!h.getBoolean("Messenger") && spawned + n >= 16) {
                h.putBoolean("Messenger", true);
                CompoundTag tag = new CompoundTag();
                tag.putString("From", "horde");
                BlockPos at = edge(sl, v, h);
                if (at != null && spawnMessenger(sl, v, at, tag)) {
                    VillageProgress.announce(sl, v, "大軍の中に、光る伝令兵がいる。逃がせば次の大軍はさらに大きくなる", false);
                }
            }
        }
        if (elapsed % 200 == 0) {
            Component line = Component.literal("§c本部の大軍：残り" + Math.max(0, total - h.getInt("Killed")) + "人（全" + total + "人）");
            for (Player p : sl.getEntitiesOfClass(Player.class, new AABB(v.center).inflate(160.0))) {
                p.displayClientMessage(line, true);
            }
        }
    }

    /** Where soldiers arrive: 48-64 blocks out, from the horde's side of the village. */
    private static BlockPos edge(ServerLevel sl, VillageLedger.Village v, CompoundTag h) {
        for (int i = 0; i < 6; i++) {
            double a = h.getDouble("Angle") + (sl.random.nextDouble() - 0.5) * 1.4;
            double d = 48.0 + sl.random.nextDouble() * 16.0;
            BlockPos p = VillageExpeditions.top(sl, v.center.offset((int)(Math.cos(a) * d), 0, (int)(Math.sin(a) * d)));
            if (p != null && sl.getFluidState(p.below()).isEmpty() && sl.getBlockState(p).canBeReplaced()) {
                return p;
            }
        }
        return null;
    }

    private static String pick(ServerLevel sl) {
        int sum = 0;
        for (String[] s : SOLDIERS) {
            sum += Integer.parseInt(s[1]);
        }
        int roll = sl.random.nextInt(sum);
        for (String[] s : SOLDIERS) {
            roll -= Integer.parseInt(s[1]);
            if (roll < 0) {
                return s[0];
            }
        }
        return "pillager";
    }

    /** One soldier of the horde: strong on its own, armoured by the reports, with a monstrous weapon. */
    private static boolean soldier(ServerLevel sl, VillageLedger.Village v, CompoundTag h) {
        BlockPos at = edge(sl, v, h);
        if (at == null) {
            return false;
        }
        String id = pick(sl);
        EntityType<?> type = (EntityType<?>)BuiltInRegistries.ENTITY_TYPE.get(new ResourceLocation(id));
        if (!(type.create(sl) instanceof Mob m)) {
            return false;
        }
        int reports = h.getInt("Reports");
        m.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, sl.random.nextFloat() * 360.0F, 0.0F);
        double roll = sl.random.nextDouble();
        boolean elite = roll < 0.08 + 0.04 * reports;
        // level 5 at most: level 6 makes any mob an elite of several hundred health, a whole horde of those is too much
        MobLevels.set(m, elite || roll < 0.45 ? 5 : 4);
        AttributeInstance hp = m.getAttribute(Attributes.MAX_HEALTH);
        if (hp != null) {
            hp.addPermanentModifier(Mods.make(MIGHT, 1.0 + 0.5 * (reports - 1), AttributeModifier.Operation.MULTIPLY_BASE));
        }
        AttributeInstance atk = m.getAttribute(Attributes.ATTACK_DAMAGE);
        if (atk != null) {
            atk.addPermanentModifier(Mods.make(MIGHT, 0.5, AttributeModifier.Operation.MULTIPLY_BASE));
        }
        m.setHealth(m.getMaxHealth());
        arm(sl, m, id, reports, elite);
        m.setPersistenceRequired();
        if (m instanceof Raider r) {
            r.setCanJoinRaid(false);
        }
        m.getPersistentData().putUUID("OrorHorde", v.id);
        if (elite) {
            m.setCustomName(Component.literal("§c本部の精鋭"));
            m.setCustomNameVisible(true);
        }
        if (!sl.addFreshEntity(m)) {
            return false;
        }
        sl.sendParticles(ParticleTypes.LARGE_SMOKE, m.getX(), m.getY() + 1.0, m.getZ(), 6, 0.3, 0.6, 0.3, 0.02);
        return true;
    }

    private static void enchant(ServerLevel sl, ItemStack st, net.minecraft.world.item.enchantment.Enchantment key, int level) {
        st.enchant(key, level);
    }

    private static void arm(ServerLevel sl, Mob m, String id, int reports, boolean elite) {
        String metal = reports >= 3 ? "netherite" : (reports == 2 ? "diamond" : "iron");
        String[] parts = {"_helmet", "_chestplate", "_leggings", "_boots"};
        EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};
        if (!id.equals("ravager")) {
            for (int i = 0; i < 4; i++) {
                ItemStack st = ((Item)BuiltInRegistries.ITEM.get(new ResourceLocation(metal + parts[i]))).getDefaultInstance();
                enchant(sl, st, Enchantments.ALL_DAMAGE_PROTECTION, Math.min(4, 1 + reports));
                m.setItemSlot(slots[i], st);
                m.setDropChance(slots[i], 0.0F);
            }
        }
        ItemStack weapon = ItemStack.EMPTY;
        if (id.equals("illusioner")) {
            weapon = Items.BOW.getDefaultInstance();
            enchant(sl, weapon, Enchantments.POWER_ARROWS, Math.min(5, 2 + reports));
        } else if (id.equals("vindicator")) {
            weapon = Items.NETHERITE_AXE.getDefaultInstance();
            enchant(sl, weapon, Enchantments.SHARPNESS, Math.min(10, 5 + reports));
            enchant(sl, weapon, Enchantments.FIRE_ASPECT, 2);
            enchant(sl, weapon, Enchantments.KNOCKBACK, 2);
        } else if (id.equals("pillager")) {
            weapon = Items.CROSSBOW.getDefaultInstance();
            enchant(sl, weapon, Enchantments.QUICK_CHARGE, 3);
            enchant(sl, weapon, Enchantments.MULTISHOT, 1);
            enchant(sl, weapon, Enchantments.PIERCING, 4);
        }
        float drop = 0.0F;
        if (elite && !id.equals("pillager") && !id.equals("ravager")) {
            // a relic weapon in an elite's hands
            List<String> relics = new ArrayList<>();
            for (String k : CharacterRelics.ITEMS.keySet()) {
                if (k.endsWith("_weapon")) {
                    relics.add(k);
                }
            }
            if (!relics.isEmpty()) {
                weapon = ((Item)CharacterRelics.ITEMS.get(relics.get(sl.random.nextInt(relics.size()))).get()).getDefaultInstance();
                drop = 0.05F;
            }
        }
        if (!weapon.isEmpty()) {
            m.setItemSlot(EquipmentSlot.MAINHAND, weapon);
            m.setDropChance(EquipmentSlot.MAINHAND, drop);
            CompoundTag mind = MobMind.data(m);
            mind.putBoolean("OriginalAuto", false);
        }
    }

    /** A soldier without a target marches on the village centre. */
    private static void march(ServerLevel sl, Mob m, UUID village) {
        if (m.getTarget() != null && m.getTarget().isAlive()) {
            return;
        }
        VillageLedger.Village v = VillageLedger.get(sl).villages.get(village);
        if (v == null) {
            return;
        }
        if (m.blockPosition().distSqr(v.center) > 36.0) {
            m.getNavigation().moveTo(v.center.getX() + 0.5 + (sl.random.nextDouble() - 0.5) * 12.0, v.center.getY(),
                v.center.getZ() + 0.5 + (sl.random.nextDouble() - 0.5) * 12.0, 1.0);
        }
    }
}
