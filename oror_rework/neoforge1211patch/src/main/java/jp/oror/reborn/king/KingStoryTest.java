package jp.oror.reborn.king;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.royal.RoyalThreats;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.LecternBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) /oror story test: the villager king at peace and at war, his forms, the rebels and their lord, the crown, and
 * the summoning chamber, each as a player meets them (stand-in players). KING-STORY {...} with a pass for each part.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingStoryTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Story");
    public static volatile boolean resultLogged;

    static final class Tester extends FakePlayer {
        Tester(ServerLevel level, int n) {
            super(level, new GameProfile(UUID.fromString("0f0e0d0c-0b0a-4908-8706-0504030203" + String.format("%02x", n)), "[OROR Story " + n + "]"));
            unshield();
        }

        /** A fake player never ticks, so its sixty ticks of spawn protection never run out and every blow on it is
         * refused before any handler sees it; take them away. */
        boolean unshield() {
            this.invulnerableTime = 0;
            try {
                java.lang.reflect.Field f = net.minecraft.server.level.ServerPlayer.class.getDeclaredField("spawnInvulnerableTime");
                f.setAccessible(true);
                f.setInt(this, 0);
                return true;
            } catch (ReflectiveOperationException | RuntimeException ex) {
                LOG.warn("KING-STORY-UNSHIELD {}", ex.toString());
                return false;
            }
        }

        void ready() {
            this.attackStrengthTicker = 200;
        }

        @Override
        public boolean isInvulnerableTo(net.minecraft.world.damagesource.DamageSource source) {
            return false;
        }
    }

    private static final class Run {
        ServerLevel level;
        BlockPos at;
        RoyalMob king;
        Tester friend, rebel, keeper;
        final Map<String, Object> r = new LinkedHashMap<>();
        final List<Entity> made = new ArrayList<>();
        final List<int[]> chunks = new ArrayList<>();
        long started;
        int stage;
        int trial = -1;
        boolean movesDone;
        String lastId;
        Mob lastDummy;
        final StringBuilder notes = new StringBuilder();
        long nextTrial = -1, after = -1;
        final Map<String, Integer> hitsBefore = new LinkedHashMap<>();
    }

    private static Run run;

    private KingStoryTest() {
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("story").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> start(c.getSource())))));
    }

    private static int start(CommandSourceStack src) {
        if (run != null) {
            return 0;
        }
        Run r = new Run();
        r.level = src.getServer().overworld();
        BlockPos o = BlockPos.containing(src.getPosition()).offset(-4000, 0, 4000);
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = -3; dz <= 3; dz++) {
                int cx = (o.getX() >> 4) + dx, cz = (o.getZ() >> 4) + dz;
                r.level.setChunkForced(cx, cz, true);
                r.chunks.add(new int[]{cx, cz});
            }
        }
        int y = Math.max(r.level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, o.getX(), o.getZ()), r.level.getSeaLevel() + 1) + 6;
        r.at = new BlockPos(o.getX(), y, o.getZ());
        for (int dx = -30; dx <= 30; dx++) {
            for (int dz = -30; dz <= 30; dz++) {
                r.level.setBlock(r.at.offset(dx, -1, dz), Blocks.STONE.defaultBlockState(), 2);
                for (int h = 0; h < 8; h++) {
                    r.level.setBlock(r.at.offset(dx, h, dz), Blocks.AIR.defaultBlockState(), 2);
                }
            }
        }
        r.king = RoyalRegistry.TYPES.get(RoyalRole.KING).create(r.level);
        r.king.moveTo(r.at.getX() + 0.5, r.at.getY(), r.at.getZ() + 0.5, 0F, 0F);
        r.king.setPersistenceRequired();
        r.level.addFreshEntity(r.king);
        r.made.add(r.king);
        r.friend = new Tester(r.level, 1);
        r.rebel = new Tester(r.level, 2);
        r.keeper = new Tester(r.level, 3);
        for (Tester t : List.of(r.friend, r.rebel, r.keeper)) {
            t.moveTo(r.at.getX() + 3.5, r.at.getY(), r.at.getZ() + 0.5, 90F, 0F);
        }
        r.started = r.level.getGameTime();
        run = r;
        LOG.info("KING-STORY-START {}", r.at);
        return 1;
    }

    private static Mob spawn(Run r, EntityType<? extends Mob> type, double dx, double dz) {
        Mob m = type.create(r.level);
        m.moveTo(r.at.getX() + 0.5 + dx, r.at.getY(), r.at.getZ() + 0.5 + dz, 0F, 0F);
        m.finalizeSpawn(r.level, r.level.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.COMMAND, null);
        m.setPersistenceRequired();
        r.level.addFreshEntity(m);
        r.made.add(m);
        return m;
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        Run r = run;
        if (r == null) {
            return;
        }
        long age = r.level.getGameTime() - r.started;
        try {
            step(r, age);
        } catch (RuntimeException ex) {
            r.r.put("error", ex.toString());
            LOG.error("KING-STORY-ERROR", ex);
            finish(r);
        }
    }

    private static void step(Run r, long age) {
        ServerLevel sl = r.level;
        Map<String, Object> out = r.r;
        if (age == 40) {
            // peace: no target, the trades, the blessing, the grace as favour grows
            out.put("peaceTarget", r.king.getTarget() == null);
            out.put("peaceHostile", RoyalThreats.hostilePlayer(r.friend));
            MerchantOffers offers = KingCourt.offers(r.friend, sl);
            out.put("kingOffers", offers.size());
            KingCourt.bless(r.friend, sl);
            out.put("blessed", r.friend.hasEffect(MobEffects.HERO_OF_THE_VILLAGE) && r.friend.hasEffect(MobEffects.REGENERATION));
            for (int i = 0; i < 60; i++) {
                KingCourt.traded(r.friend, offers.get(0));
            }
            out.put("grace", KingCourt.kept(r.friend).getInt(KingCourt.GRACE));
            out.put("graceHealth", r.friend.getAttribute(Attributes.MAX_HEALTH).getModifier(KingCourt.GRACE_HEALTH) != null);
            int gifts = 0;
            for (ItemStack s : r.friend.getInventory().items) {
                gifts += s.isEmpty() ? 0 : 1;
            }
            out.put("graceGifts", gifts);
        }
        if (age == 60) {
            // war: the rebel strikes the king; the king's enemy for good, the kingdom's enemy, the boss bar's
            r.rebel.ready();
            r.rebel.attack(r.king);
            out.put("enemy", KingCourt.enemy(r.rebel));
            out.put("enemyHostile", RoyalThreats.hostilePlayer(r.rebel));
            out.put("friendStillPeace", !RoyalThreats.hostilePlayer(r.friend));
            // the rebels: a vindicator takes no friend for a target
            Mob v = spawn(r, EntityType.VINDICATOR, -6, 0);
            v.setTarget(r.rebel);
            out.put("vindicatorSpares", v.getTarget() != r.rebel);
            Mob p = spawn(r, EntityType.PIGLIN, -6, 3);
            p.setTarget(r.rebel);
            out.put("piglinSpares", p.getTarget() != r.rebel);
            // their favour: two of the kingdom's expeditioners
            for (int i = 0; i < 2; i++) {
                Villager ex = (Villager) spawn(r, EntityType.VILLAGER, 8, i * 2);
                ex.getPersistentData().putBoolean("OrorWanderer", true);
                ex.hurt(r.rebel.damageSources().playerAttack(r.rebel), 10000F);
            }
            out.put("rebelFavour", RebelPact.favour(r.rebel));
            out.put("rebelOffers", RebelPact.offers(r.rebel, sl, "illager").size());
            int came = RebelPact.summon(r.rebel, sl, "illager");
            out.put("allies", came);
            List<Mob> allies = sl.getEntitiesOfClass(Mob.class, new AABB(r.at).inflate(20), m -> m.getPersistentData().getBoolean(RebelPact.ALLY));
            r.made.addAll(allies);
            boolean spare = true;
            for (Mob a : allies) {
                a.setTarget(r.rebel);
                spare &= a.getTarget() != r.rebel;
            }
            out.put("alliesSpare", spare);
        }
        if (age == 80) {
            // the field gives way to Azazel's likeness; the king dies for real and comes back as the hero, in his film
            int came = RebelPact.summon(r.rebel, sl, "azazel");
            List<Mob> lord = sl.getEntitiesOfClass(Mob.class, new AABB(r.at).inflate(20), m -> m.getPersistentData().getBoolean(RebelLord.LORD));
            r.made.addAll(lord);
            out.put("likeness", came);
            out.put("breachedBefore", r.king.atBreached());
            kingState(r, "k0");
            PROBE = new StringBuilder();
            if (!lord.isEmpty()) {
                out.put("lordHit", r.king.hurt(r.king.damageSources().mobAttack(lord.get(0)), 10F));
            }
            out.put("probeLord", PROBE.toString().trim());
            out.put("breachedByLord", r.king.atBreached());
            kingState(r, "k1");
            int before = r.king.lifePhase();
            r.king.sovereign().healTo(4F);
            r.king.invulnerableTime = 0;
            PROBE = new StringBuilder();
            out.put("deathHit", r.king.hurt(r.king.damageSources().mobAttack(lord.isEmpty() ? r.king : lord.get(0)), 500F));
            out.put("probeDeath", PROBE.toString().trim());
            kingState(r, "k2");
            out.put("revive", before + "->" + r.king.lifePhase());
            if (r.king.lifePhase() == before) {
                // the likeness's blow did not land (probeLord/probeDeath say where it was undone): the rebel's own
                // killing blow through the broken field, as a player gives it
                PROBE = new StringBuilder();
                r.rebel.ready();
                r.king.sovereign().healTo(4F);
                r.king.sovereign().incoming(1.0E30F);
                r.king.invulnerableTime = 0;
                out.put("playerDeathHit", r.king.hurt(r.rebel.damageSources().playerAttack(r.rebel), 500F));
                out.put("probePlayer", PROBE.toString().trim());
                kingState(r, "k3");
                out.put("reviveByPlayer", before + "->" + r.king.lifePhase());
            }
            PROBE = null;
            out.put("reviveAlive", r.king.isAlive());
            out.put("film1", KingCinema.playing(r.king));
            out.put("name1", KingForms.name(r.king, 1, 0).getString());
            for (Mob m : lord) {
                m.discard();
            }
        }
        if (age == 90) {
            float h = r.king.getHealth();
            Mob z = spawn(r, EntityType.ZOMBIE, 3, 3);
            r.king.hurt(r.king.damageSources().mobAttack(z), 50F);
            out.put("filmUntouchable", r.king.getHealth() >= h);
            z.discard();
        }
        if (age == 190) {
            out.put("film1Done", !KingCinema.playing(r.king) && KingCinema.cinemas(r.king) >= 1 && !r.king.isNoAi());
            out.put("scale1", Math.round(r.king.getScale() * 100) / 100.0);
            out.put("armour1", r.king.getAttribute(Attributes.ARMOR).getModifier(KingForms.FORM_MOD) != null);
            out.put("heroSword", r.king.getMainHandItem().is(Items.NETHERITE_SWORD));
        }
        if (age == 200) {
            stage(r, 2);
        }
        if (age == 330) {
            out.put("film2Done", KingCinema.cinemas(r.king) >= 2 && !r.king.isNoAi());
            out.put("scale2", Math.round(r.king.getScale() * 100) / 100.0);
            for (int i = 0; i < 3; i++) {
                sturdy(spawn(r, EntityType.ZOMBIE, 3 + i, -3));
            }
        }
        if (age > 330 && age < 530) {
            // the broken king fights: his broken hits, his phantoms, his error arm; the zombies strike at him too
            List<Zombie> zs = sl.getEntitiesOfClass(Zombie.class, new AABB(r.at).inflate(30), Zombie::isAlive);
            if (!zs.isEmpty() && (r.king.getTarget() == null || !r.king.getTarget().isAlive())) {
                r.king.setTarget(zs.get(0));
            }
            if (age % 10 == 0 && !zs.isEmpty()) {
                r.king.doHurtTarget(zs.get(0));
                Zombie z = zs.get(zs.size() - 1);
                r.king.hurt(r.king.damageSources().mobAttack(z), 4F);
            }
            if (zs.size() < 3 && age % 20 == 0) {
                sturdy(spawn(r, EntityType.ZOMBIE, 3, -3));
            }
        }
        if (age == 530) {
            CompoundTag c = r.king.getPersistentData().getCompound(KingDeeds.COUNT);
            CompoundTag h = r.king.getPersistentData().getCompound(KingDeeds.HITS);
            out.put("missOut", c.getInt("miss_out"));
            out.put("missIn", c.getInt("miss_in"));
            out.put("lagHits", h.getInt("lag_hit"));
            out.put("phantoms", h.getInt("phantom"));
            out.put("errorArm", h.getInt("error_arm"));
            stage(r, 3);
        }
        if (age == 700) {
            out.put("film3Done", KingCinema.cinemas(r.king) >= 3 && !r.king.isNoAi());
            out.put("scale3", Math.round(r.king.getScale() * 100) / 100.0);
            out.put("bossName3", KingForms.bossName(3).getString());
            out.put("name3", KingForms.name(r.king, 3, 0).getString());
            out.put("phase", r.king.lifePhase());
            out.put("called", r.king.getPersistentData().getInt("OrorKingCalled"));
            out.put("mainhand", net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(r.king.getMainHandItem().getItem()).toString());
            r.trial = 0;
            r.nextTrial = age;
            // while the deeds are tried one by one he does nothing of his own, and the players stand well away
            r.king.getPersistentData().putBoolean(KingForms.QUIET, true);
            for (Tester t : List.of(r.friend, r.rebel, r.keeper)) {
                t.moveTo(r.at.getX() + 0.5, r.at.getY() + 40, r.at.getZ() - 60.5, 0F, 0F);
            }
        }
        int deeds = KingDeeds.DEEDS.size(), total = deeds + KingArsenal.MOVES.size();
        if (!r.movesDone && r.trial >= deeds && r.trial < total && age >= r.nextTrial) {
            // then every one of his weapons' seventy motions, the same way
            KingArsenal.Move m = KingArsenal.MOVES.get(r.trial - deeds);
            note(r, sl);
            for (Zombie z : sl.getEntitiesOfClass(Zombie.class, new AABB(r.at).inflate(40), Zombie::isAlive)) {
                z.discard();
            }
            double dist = Math.max(2.5, Math.min(14.0, (m.min() + Math.min(m.max(), 16)) / 2.0));
            r.king.teleportTo(r.at.getX() + 0.5, r.at.getY(), r.at.getZ() + 0.5);
            Mob a = sturdy(spawn(r, EntityType.ZOMBIE, dist, 0));
            sturdy(spawn(r, EntityType.ZOMBIE, dist, 1.5));
            r.king.setTarget(a);
            KingArsenal.perform(r.king, sl, m, a);
            r.lastId = m.id();
            r.lastDummy = a;
            if ((r.trial - deeds) % 10 == 0) {
                LOG.info("KING-TRIAL {\"move\":\"{}\",\"n\":{}}", m.id(), r.trial - deeds);
            }
            r.nextTrial = age + m.windup() + 22 + switch (m.shape()) {
                case LEAP, THROW -> 30;
                case LOB -> m.count() * 8 + 20;
                case SHOT, MULTI -> m.count() * 6 + 5;
                case ERUPT, WAVE, RING -> 25;
                case DASH, PULL, BACKSTEP, CROSS -> 12;
                default -> 0;
            };
            r.trial++;
            if (r.trial == total) {
                r.trial = deeds;
                r.nextTrial = age + 200;
                r.movesDone = true;
            }
        }
        if (r.trial >= 0 && r.trial <= deeds && age >= r.nextTrial && (r.trial < deeds || r.movesDone)) {
            // every deed, done on sturdy zombies set at its range
            if (r.trial == deeds) {
                CompoundTag h = r.king.getPersistentData().getCompound(KingDeeds.HITS);
                CompoundTag c = r.king.getPersistentData().getCompound(KingDeeds.COUNT);
                StringBuilder missed = new StringBuilder();
                int landed = 0;
                for (KingDeeds.Deed d : KingDeeds.DEEDS) {
                    int n = h.getInt(d.id());
                    out.put("deed_" + d.id(), n);
                    if (n > 0) {
                        landed++;
                    } else {
                        missed.append(d.id()).append(' ');
                    }
                }
                out.put("deedsLanded", landed);
                out.put("deedsMissed", missed.toString().trim());
                int moves = 0;
                StringBuilder mm = new StringBuilder();
                for (KingArsenal.Move m : KingArsenal.MOVES) {
                    if (h.getInt(m.id()) > 0) {
                        moves++;
                    } else {
                        mm.append(m.id()).append(' ');
                    }
                }
                out.put("movesLanded", moves + "/" + KingArsenal.MOVES.size());
                out.put("movesLandedN", moves);
                out.put("movesMissed", mm.toString().trim());
                note(r, sl);
                out.put("trialNotes", r.notes.toString().trim());
                out.put("echoes", c.getInt("echo"));
                out.put("moveMisses", c.getInt("move_miss"));
                out.put("stances", "clubs " + c.getInt("stance_clubs") + " scythe " + c.getInt("stance_scythe") + " twin " + c.getInt("stance_twin")
                    + " spear " + c.getInt("stance_spear") + " bow " + c.getInt("stance_bow"));
                out.put("deleted", r.king.getPersistentData().getInt("OrorKingDeleted"));
                out.put("bolts", r.king.getPersistentData().getInt("OrorKingBolts"));
                out.put("swarms", r.king.getPersistentData().getInt("OrorKingSwarms"));
                r.trial = -1;
                r.after = age + 10;
                r.king.getPersistentData().remove(KingForms.QUIET);
                for (Tester t : List.of(r.friend, r.rebel, r.keeper)) {
                    t.moveTo(r.at.getX() + 3.5, r.at.getY(), r.at.getZ() + 0.5, 90F, 0F);
                }
            } else {
                note(r, sl);
                KingDeeds.Deed d = KingDeeds.DEEDS.get(r.trial);
                r.lastId = d.id();
                for (Zombie z : sl.getEntitiesOfClass(Zombie.class, new AABB(r.at).inflate(40), Zombie::isAlive)) {
                    z.discard();
                }
                double dist = Math.max(3.0, Math.min(14.0, (d.min() + Math.min(d.max(), 16)) / 2.0));
                r.king.teleportTo(r.at.getX() + 0.5, r.at.getY(), r.at.getZ() + 0.5);
                Mob a = sturdy(spawn(r, EntityType.ZOMBIE, dist, 0));
                r.lastDummy = a;
                sturdy(spawn(r, EntityType.ZOMBIE, dist, 1.5));
                r.king.setTarget(a);
                if (d.stance() != 0) {
                    KingDeeds.switchStance(r.king, sl, d.stance());
                }
                KingDeeds.perform(r.king, sl, d.id(), a);
                r.nextTrial = age + d.windup() + switch (d.id()) {
                    case "rollback", "brand", "feast" -> 75;
                    case "gaze", "void", "rain", "doomsday" -> 50;
                    case "ghosts", "judgment", "driver", "execution", "javelin" -> 45;
                    default -> 30;
                };
                r.trial++;
            }
        }
        if (r.after > 0 && age == r.after) {
            // the rebel lord, his crown; kept, presented
            Mob lord = RebelLord.court(sl, r.at.offset(-15, 0, 12), true);
            out.put("lord", lord != null && lord.getPersistentData().getBoolean(RebelLord.LORD));
            if (lord != null) {
                r.made.addAll(sl.getEntitiesOfClass(Mob.class, new AABB(lord.blockPosition()).inflate(8), m -> m != lord));
                lord.hurt(r.keeper.damageSources().playerAttack(r.keeper), 100000F);
            }
        }
        if (r.after > 0 && age == r.after + 10) {
            List<ItemEntity> crowns = sl.getEntitiesOfClass(ItemEntity.class, new AABB(r.at).inflate(40), i -> RebelLord.isCrown(i.getItem()));
            out.put("crownDropped", crowns.size());
            r.keeper.getInventory().add(RebelLord.crown());
            RebelLord.setHeld(r.keeper, 5980);
            RebelLord.keep(r.keeper);
            out.put("keeperEnemy", KingCourt.enemy(r.keeper));
            r.friend.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, RebelLord.crown());
            int favour = KingCourt.kept(r.friend).getInt(KingCourt.FAVOUR);
            boolean presented = RebelLord.present(r.friend, r.king, sl);
            out.put("presented", presented);
            out.put("festival", RebelLord.festivals());
            out.put("favourRise", KingCourt.kept(r.friend).getInt(KingCourt.FAVOUR) - favour);
            for (ItemEntity c : crowns) {
                c.discard();
            }
        }
        if (r.after > 0 && age >= r.after + 20 && age < r.after + 30 && !Boolean.TRUE.equals(out.get("godSlayer"))) {
            // Baal Zebul's last death at the rebel's hand: the rebel and those who fought him become god-slayers
            for (Zombie z : sl.getEntitiesOfClass(Zombie.class, new AABB(r.at).inflate(40), Zombie::isAlive)) {
                z.discard();
            }
            if (r.king.isAlive()) {
                r.rebel.ready();
                r.king.sovereign().healTo(1F);
                r.king.sovereign().incoming(1.0E30F);
                r.king.hurt(r.rebel.damageSources().playerAttack(r.rebel), 1000F);
            }
            out.put("kingDead", !r.king.isAlive());
            out.put("godSlayer", GodSlayer.has(r.rebel));
        }
        if (r.after > 0 && age == r.after + 30) {
            out.put("godSlayerHealth", r.rebel.getAttribute(Attributes.MAX_HEALTH).getValue());
            GodSlayer.give(r.rebel, sl);
            // its field takes a small blow whole; a great blow breaks it and the ceiling holds what goes through
            r.rebel.setHealth(r.rebel.getMaxHealth());
            out.put("testerUnshielded", r.rebel.unshield());
            Mob z = spawn(r, EntityType.ZOMBIE, 2, 2);
            float h0 = r.rebel.getHealth();
            r.rebel.hurt(r.rebel.damageSources().mobAttack(z), 20F);
            out.put("fieldTook", r.rebel.getHealth() >= h0 && GodSlayer.fieldOf(r.rebel) < GodSlayer.CAPACITY);
            r.rebel.invulnerableTime = 0;
            float h1 = r.rebel.getHealth();
            r.rebel.hurt(r.rebel.damageSources().mobAttack(z), 400F);
            out.put("ceilingHeld", h1 - r.rebel.getHealth() <= r.rebel.getMaxHealth() * 0.25F + 0.01F && r.rebel.isAlive());
            z.discard();
            // a god struck by a god-slayer: a new king is weakened and his field breaks
            RoyalMob god = RoyalRegistry.TYPES.get(RoyalRole.KING).create(sl);
            god.moveTo(r.at.getX() + 6.5, r.at.getY(), r.at.getZ() + 6.5, 0F, 0F);
            sl.addFreshEntity(god);
            r.made.add(god);
            r.rebel.ready();
            god.hurt(r.rebel.damageSources().playerAttack(r.rebel), 10F);
            out.put("godWeakenedEffect", god.hasEffect(MobEffects.WEAKNESS));
            // the King throws off harmful effects; the curse on his armour and strength holds
            out.put("godWeakened", god.hasEffect(MobEffects.WEAKNESS)
                || god.getAttribute(Attributes.ARMOR).getModifier(GodSlayer.CURSE) != null);
            out.put("godBreached", god.atBreached());
            god.discard();
        }
        if (r.after > 0 && age == r.after + 40) {
            // the broken phantasm: a sword shatters into a blow many times over; a pickaxe tears out a sphere
            r.keeper.getInventory().clearContent();
            // the sword's own blow first (a fake player never ticks, so its weapon's modifiers are put on by hand)
            float base = swordBlow(r);
            BrokenPhantasm.cast(r.keeper, sl);
            out.put("phantasmActive", BrokenPhantasm.active(r.keeper));
            float blow = swordBlow(r);
            out.put("phantasmBase", Math.round(base * 10) / 10.0);
            out.put("phantasmBlow", Math.round(blow));
            out.put("phantasmRatio", base > 0 ? Math.round(blow / base * 10) / 10.0 : -1.0);
            out.put("phantasmSwordGone", r.keeper.getMainHandItem().isEmpty());
            BlockPos c = r.at.offset(8, 3, -8);
            for (BlockPos q : BlockPos.betweenClosed(c.offset(-3, -3, -3), c.offset(3, 3, 3))) {
                sl.setBlock(q, Blocks.STONE.defaultBlockState(), 2);
            }
            r.keeper.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND_PICKAXE));
            r.keeper.gameMode.destroyBlock(c);
            int air = 0;
            for (BlockPos q : BlockPos.betweenClosed(c.offset(-3, -3, -3), c.offset(3, 3, 3))) {
                air += sl.getBlockState(q).isAir() ? 1 : 0;
            }
            out.put("phantasmDug", air);
            out.put("phantasmPickGone", r.keeper.getMainHandItem().isEmpty());
            out.put("tiers", BrokenPhantasm.tier(new ItemStack(Items.IRON_SWORD)) + "/" + BrokenPhantasm.tier(new ItemStack(Items.TRIDENT)) + "/"
                + BrokenPhantasm.tier(new ItemStack(Items.ENCHANTED_GOLDEN_APPLE)) + "/"
                + net.minecraft.core.registries.BuiltInRegistries.ITEM.getOptional(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "kokuhaku_weapon"))
                .map(i -> BrokenPhantasm.tier(new ItemStack(i))).orElse(-1));
            CompoundTag kept = KingCourt.kept(r.rebel);
            kept.putInt(RebelPact.FAVOUR, 70);
            KingCourt.keep(r.rebel, kept);
            out.put("phantasmOffered", RebelPact.offers(r.rebel, sl, "illager").stream().anyMatch(o -> BrokenPhantasm.isScroll(o.getResult())));
        }
        if (r.after > 0 && age == r.after + 50) {
            // the summoning chamber, dug under the nearest forest; one comes into the world on its circle
            BlockPos circle = SummoningChamber.build(sl, r.at);
            out.put("chamber", circle.toShortString());
            BlockPos o = circle.below();
            out.put("circleStone", sl.getBlockState(o).is(Blocks.CHISELED_DEEPSLATE));
            int containers = 0, filled = 0, workshops = 0, ladders = 0, iss = 0;
            boolean journal = false;
            java.util.Set<String> kinds = new java.util.TreeSet<>();
            for (BlockPos p : BlockPos.betweenClosed(o.offset(-10, 0, -10), o.offset(10, 7, 10))) {
                BlockEntity be = sl.getBlockEntity(p);
                if (be instanceof Container c) {
                    containers++;
                    filled += c.isEmpty() ? 0 : 1;
                }
                if (be instanceof LecternBlockEntity le && le.hasBook()) {
                    journal = true;
                }
                var st = sl.getBlockState(p);
                if (st.is(Blocks.CRAFTING_TABLE) || st.is(Blocks.FURNACE) || st.is(Blocks.ANVIL) || st.is(Blocks.ENCHANTING_TABLE) || st.is(Blocks.BREWING_STAND)
                    || st.is(Blocks.SMITHING_TABLE)) {
                    workshops++;
                    kinds.add(net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(st.getBlock()).getPath());
                }
                if (net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(st.getBlock()).getNamespace().equals("irons_spellbooks")) {
                    iss++;
                }
            }
            for (int y = o.getY(); y < o.getY() + 40; y++) {
                if (sl.getBlockState(new BlockPos(o.getX(), y, o.getZ() + SummoningChamber.HALF + 1)).is(Blocks.LADDER)) {
                    ladders++;
                }
            }
            int lying = sl.getEntitiesOfClass(ItemEntity.class, new AABB(o).inflate(12, 4, 12)).size();
            out.put("containers", containers);
            out.put("filled", filled);
            out.put("workshops", workshops);
            out.put("workshopKinds", String.join(" ", kinds));
            out.put("issBlocks", iss);
            out.put("journal", journal);
            out.put("ladders", ladders);
            out.put("lying", lying);
            Tester comer = new Tester(sl, 4);
            SummoningChamber.arrive(comer, sl, circle);
            out.put("arrived", comer.blockPosition().distManhattan(circle) <= 1);
            out.put("respawn", circle.equals(comer.getRespawnPosition()));
            for (ItemEntity it : sl.getEntitiesOfClass(ItemEntity.class, new AABB(o).inflate(12, 4, 12))) {
                it.discard();
            }
            finish(r);
        }
    }

    /** After a trial: if what was tried hit nothing, where the King had got to and where its dummy stood. */
    private static void note(Run r, ServerLevel sl) {
        if (r.lastId == null) {
            return;
        }
        CompoundTag h = r.king.getPersistentData().getCompound(KingDeeds.HITS);
        if (h.getInt(r.lastId) == 0) {
            double moved = r.king.position().distanceTo(net.minecraft.world.phys.Vec3.atBottomCenterOf(r.at));
            double zd = r.lastDummy != null ? r.lastDummy.distanceTo(r.king) : -1;
            r.notes.append(String.format(java.util.Locale.ROOT, "%s(k%.1f,z%.1f,%s) ", r.lastId, moved, zd,
                r.lastDummy == null ? "-" : r.lastDummy.isAlive() ? "a" : "d"));
        }
        r.lastId = null;
    }

    /** One blow of an iron sword by the keeper on a fresh dummy; the health it took. */
    private static float swordBlow(Run r) {
        ItemStack sword = new ItemStack(Items.IRON_SWORD);
        r.keeper.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, sword);
        List<net.minecraft.resources.ResourceLocation> put = new ArrayList<>();
        sword.forEachModifier(net.minecraft.world.entity.EquipmentSlot.MAINHAND, (a, m) -> {
            var in = r.keeper.getAttribute(a);
            if (in != null && in.getModifier(m.id()) == null) {
                in.addTransientModifier(m);
                put.add(m.id());
            }
        });
        Mob z = sturdy(spawn(r, EntityType.ZOMBIE, 1.5, -1.5));
        float zh = z.getHealth();
        r.keeper.ready();
        r.keeper.attack(z);
        float took = zh - z.getHealth();
        z.discard();
        for (var a : List.of(Attributes.ATTACK_DAMAGE, Attributes.ATTACK_SPEED)) {
            var in = r.keeper.getAttribute(a);
            if (in != null) {
                for (var id : put) {
                    in.removeModifier(id);
                }
            }
        }
        return took;
    }

    /** The King's state for the record: his health, field, phase, and the counts his sovereign keeps. */
    private static void kingState(Run r, String tag) {
        RoyalMob k = r.king;
        CompoundTag d = k.getPersistentData();
        StringBuilder b = new StringBuilder();
        b.append("hp=").append(Math.round(k.getHealth() * 10) / 10.0).append('/').append(Math.round(k.getMaxHealth()))
            .append(" field=").append(Math.round(k.sovereign().field())).append(" breached=").append(k.sovereign().breached())
            .append(" phase=").append(k.lifePhase()).append(" inv=").append(k.isInvulnerable()).append(" noai=").append(k.isNoAi())
            .append(" itime=").append(k.invulnerableTime).append(" alive=").append(k.isAlive());
        for (String c : new String[]{"RoyalFieldBreaks", "RoyalFieldAbsorptions", "RoyalParries", "RoyalBlocks", "RoyalResurrections",
            "RoyalDirectDeathBlocks", "RoyalInstantKillBlocks", "RoyalFatalNegations"}) {
            if (d.getInt(c) > 0) {
                b.append(' ').append(c.substring(5)).append('=').append(d.getInt(c));
            }
        }
        r.r.put(tag, b.toString());
    }

    private static void stage(Run r, int phase) {
        CompoundTag t = new CompoundTag();
        t.putInt("Phase", phase);
        r.king.sovereign().load(t);
        KingForms.reborn(r.king, phase);
        r.r.put("name" + phase, KingForms.name(r.king, phase, 0).getString());
    }

    /** The test's dummies are not let die (the King's own blows, his storms and his offense would kill them before the
     * deed on trial lands): their death is refused and their health made whole. */
    @SubscribeEvent
    public static void dummy(net.neoforged.neoforge.event.entity.living.LivingDeathEvent e) {
        if (e.getEntity().getPersistentData().getBoolean(DUMMY) && run != null) {
            e.setCanceled(true);
            e.getEntity().setHealth(e.getEntity().getMaxHealth());
        }
    }

    static final String DUMMY = "OrorStoryDummy";

    /** Where a blow on the King is undone: the cancel state seen at each priority (for the record). */
    static StringBuilder PROBE;

    private static void probe(LivingIncomingDamageEvent e, String at) {
        if (PROBE != null && KingCourt.isKing(e.getEntity())) {
            PROBE.append(at).append(e.isCanceled() ? 'x' : 'o').append(Math.round(e.getAmount())).append(' ');
        }
    }

    @SubscribeEvent(priority = EventPriority.HIGHEST, receiveCanceled = true)
    public static void probe1(LivingIncomingDamageEvent e) {
        probe(e, "HIGHEST:");
    }

    @SubscribeEvent(priority = EventPriority.HIGH, receiveCanceled = true)
    public static void probe2(LivingIncomingDamageEvent e) {
        probe(e, "HIGH:");
    }

    @SubscribeEvent(priority = EventPriority.NORMAL, receiveCanceled = true)
    public static void probe3(LivingIncomingDamageEvent e) {
        probe(e, "NORMAL:");
    }

    @SubscribeEvent(priority = EventPriority.LOW, receiveCanceled = true)
    public static void probe4(LivingIncomingDamageEvent e) {
        probe(e, "LOW:");
    }

    @SubscribeEvent(priority = EventPriority.LOWEST, receiveCanceled = true)
    public static void probe5(LivingIncomingDamageEvent e) {
        probe(e, "LOWEST:");
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void probePre(net.neoforged.neoforge.event.entity.living.LivingDamageEvent.Pre e) {
        if (PROBE != null && KingCourt.isKing(e.getEntity())) {
            PROBE.append("PRE:").append(Math.round(e.getNewDamage())).append(' ');
        }
    }

    /** While his deeds are tried, the King takes no target of his own (his blows would knock the dummies about). */
    @SubscribeEvent
    public static void quietTarget(net.neoforged.neoforge.event.entity.living.LivingChangeTargetEvent e) {
        if (run != null && e.getNewAboutToBeSetTarget() != null && KingCourt.isKing(e.getEntity())
            && e.getEntity().getPersistentData().getBoolean(KingForms.QUIET)) {
            e.setCanceled(true);
        }
    }

    /** A zombie that lives through many blows and does not burn. */
    private static Mob sturdy(Mob m) {
        m.getPersistentData().putBoolean(DUMMY, true);
        // standing still: what a deed does to it is what the deed does, not where the dummy walked or was knocked
        m.setNoAi(true);
        var a = m.getAttribute(Attributes.MAX_HEALTH);
        if (a != null) {
            a.setBaseValue(1000);
        }
        m.setHealth(m.getMaxHealth());
        m.setItemSlot(net.minecraft.world.entity.EquipmentSlot.HEAD, new ItemStack(Items.LEATHER_HELMET));
        return m;
    }

    private static void finish(Run r) {
        run = null;
        Map<String, Object> o = r.r;
        boolean peace = Boolean.TRUE.equals(o.get("peaceTarget")) && Boolean.FALSE.equals(o.get("peaceHostile")) && num(o, "kingOffers") >= 10
            && Boolean.TRUE.equals(o.get("blessed")) && num(o, "grace") == 3 && Boolean.TRUE.equals(o.get("graceHealth"));
        boolean war = Boolean.TRUE.equals(o.get("enemy")) && Boolean.TRUE.equals(o.get("enemyHostile")) && Boolean.TRUE.equals(o.get("friendStillPeace"));
        boolean rebels = Boolean.TRUE.equals(o.get("vindicatorSpares")) && num(o, "rebelFavour") >= 5 && num(o, "allies") == 3
            && Boolean.TRUE.equals(o.get("alliesSpare"));
        boolean forms = Boolean.TRUE.equals(o.get("breachedByLord")) && ("0->1".equals(o.get("revive")) || "0->1".equals(o.get("reviveByPlayer"))) && Boolean.TRUE.equals(o.get("film1"))
            && Boolean.TRUE.equals(o.get("filmUntouchable")) && Boolean.TRUE.equals(o.get("film1Done")) && Boolean.TRUE.equals(o.get("film2Done"))
            && Boolean.TRUE.equals(o.get("film3Done")) && num(o, "phase") == 3 && Boolean.TRUE.equals(o.get("armour1")) && Boolean.TRUE.equals(o.get("heroSword"))
            && o.get("scale1") instanceof Double s1 && o.get("scale2") instanceof Double s2 && o.get("scale3") instanceof Double s3 && s1 > 1.0 && s2 > s1 && s3 > s2;
        boolean deeds = num(o, "deedsLanded") >= KingDeeds.DEEDS.size() - 1;
        boolean moves = num(o, "movesLandedN") >= KingArsenal.MOVES.size() - 3;
        boolean broken = num(o, "missOut") + num(o, "lagHits") + num(o, "missIn") + num(o, "phantoms") + num(o, "errorArm") > 0;
        boolean slayer = Boolean.TRUE.equals(o.get("godSlayer")) && Boolean.TRUE.equals(o.get("fieldTook")) && Boolean.TRUE.equals(o.get("ceilingHeld"))
            && Boolean.TRUE.equals(o.get("godWeakened"));
        boolean phantasm = Boolean.TRUE.equals(o.get("phantasmActive")) && o.get("phantasmRatio") instanceof Double pr && pr >= 9.5
            && Boolean.TRUE.equals(o.get("phantasmSwordGone"))
            && num(o, "phantasmDug") >= 10 && Boolean.TRUE.equals(o.get("phantasmPickGone"));
        boolean crown = num(o, "crownDropped") >= 1 && Boolean.TRUE.equals(o.get("keeperEnemy")) && Boolean.TRUE.equals(o.get("presented"))
            && num(o, "festival") >= 1;
        boolean chamber = Boolean.TRUE.equals(o.get("circleStone")) && num(o, "filled") >= 8 && num(o, "workshops") >= 5 && num(o, "ladders") >= 8
            && num(o, "lying") >= 5 && Boolean.TRUE.equals(o.get("journal")) && Boolean.TRUE.equals(o.get("arrived"));
        o.put("passPeace", peace);
        o.put("passWar", war);
        o.put("passRebels", rebels);
        o.put("passForms", forms);
        o.put("passCrown", crown);
        o.put("passChamber", chamber);
        o.put("passDeeds", deeds);
        o.put("passMoves", moves);
        o.put("passBroken", broken);
        o.put("passGodSlayer", slayer);
        o.put("passPhantasm", phantasm);
        o.put("pass", peace && war && rebels && forms && crown && chamber && deeds && moves && broken && slayer && phantasm);
        StringBuilder b = new StringBuilder("{");
        o.forEach((k, v) -> b.append(b.length() > 1 ? "," : "").append('"').append(k).append("\":")
            .append(v instanceof String s ? "\"" + s.replace("\"", "'") + "\"" : String.valueOf(v)));
        LOG.info("KING-STORY {}}", b);
        for (Entity e : r.made) {
            if (e.isAlive()) {
                e.discard();
            }
        }
        for (Entity e : r.level.getEntities((Entity) null, new AABB(r.at).inflate(40, 20, 40), x -> !(x instanceof Player))) {
            e.discard();
        }
        for (int[] c : r.chunks) {
            r.level.setChunkForced(c[0], c[1], false);
        }
        resultLogged = true;
    }

    private static int num(Map<String, Object> o, String k) {
        return o.get(k) instanceof Number n ? n.intValue() : -1;
    }
}
