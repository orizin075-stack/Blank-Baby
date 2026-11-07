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
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.LecternBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
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
        }

        void ready() {
            this.attackStrengthTicker = 200;
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
            // the field gives way to Azazel's likeness; the king dies for real and comes back in his first form
            int came = RebelPact.summon(r.rebel, sl, "azazel");
            List<Mob> lord = sl.getEntitiesOfClass(Mob.class, new AABB(r.at).inflate(20), m -> m.getPersistentData().getBoolean(RebelLord.LORD));
            r.made.addAll(lord);
            out.put("likeness", came);
            out.put("breachedBefore", r.king.atBreached());
            if (!lord.isEmpty()) {
                r.king.hurt(r.king.damageSources().mobAttack(lord.get(0)), 10F);
            }
            out.put("breachedByLord", r.king.atBreached());
            int before = r.king.lifePhase();
            r.king.sovereign().healTo(4F);
            r.king.hurt(r.king.damageSources().mobAttack(lord.isEmpty() ? r.king : lord.get(0)), 500F);
            out.put("revive", before + "->" + r.king.lifePhase());
            out.put("reviveAlive", r.king.isAlive());
            out.put("name1", KingForms.name(r.king, 1, 0).getString());
        }
        if (age == 100) {
            // the later forms, called directly; the third's arms and deeds against monsters
            for (int phase = 2; phase <= 3; phase++) {
                CompoundTag t = new CompoundTag();
                t.putInt("Phase", phase);
                r.king.sovereign().load(t);
                KingForms.reborn(r.king, phase);
                out.put("name" + phase, KingForms.name(r.king, phase, 0).getString());
            }
            out.put("bossName3", KingForms.bossName(3).getString());
            out.put("phase", r.king.lifePhase());
            out.put("called", r.king.getPersistentData().getInt("OrorKingCalled"));
            for (int i = 0; i < 3; i++) {
                spawn(r, EntityType.ZOMBIE, 4 + i, -4);
            }
        }
        if (age > 100 && age < 400) {
            List<Zombie> zs = sl.getEntitiesOfClass(Zombie.class, new AABB(r.at).inflate(30), Zombie::isAlive);
            if (!zs.isEmpty() && (r.king.getTarget() == null || !r.king.getTarget().isAlive())) {
                r.king.setTarget(zs.get(0));
            }
            if (zs.isEmpty() && age % 40 == 0) {
                spawn(r, EntityType.ZOMBIE, 3, -3);
            }
        }
        if (age == 400) {
            CompoundTag d = r.king.getPersistentData();
            out.put("mainhand", net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(r.king.getMainHandItem().getItem()).toString());
            out.put("offhand", net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(r.king.getOffhandItem().getItem()).toString());
            out.put("bolts", d.getInt("OrorKingBolts"));
            out.put("swarms", d.getInt("OrorKingSwarms"));
            out.put("slams", d.getInt("OrorKingSlams"));
            // the rebel lord, his crown; kept, presented
            Mob lord = RebelLord.court(sl, r.at.offset(-15, 0, 12), true);
            out.put("lord", lord != null && lord.getPersistentData().getBoolean(RebelLord.LORD));
            if (lord != null) {
                r.made.addAll(sl.getEntitiesOfClass(Mob.class, new AABB(lord.blockPosition()).inflate(8), m -> m != lord));
                lord.hurt(r.keeper.damageSources().playerAttack(r.keeper), 100000F);
            }
        }
        if (age == 410) {
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
        if (age == 420) {
            // the summoning chamber, dug under the nearest forest; one comes into the world on its circle
            BlockPos circle = SummoningChamber.build(sl, r.at);
            out.put("chamber", circle.toShortString());
            BlockPos o = circle.below();
            out.put("circleStone", sl.getBlockState(o).is(Blocks.CHISELED_DEEPSLATE));
            int containers = 0, filled = 0, workshops = 0, ladders = 0, iss = 0;
            boolean journal = false;
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

    private static void finish(Run r) {
        run = null;
        Map<String, Object> o = r.r;
        boolean peace = Boolean.TRUE.equals(o.get("peaceTarget")) && Boolean.FALSE.equals(o.get("peaceHostile")) && num(o, "kingOffers") >= 10
            && Boolean.TRUE.equals(o.get("blessed")) && num(o, "grace") == 3 && Boolean.TRUE.equals(o.get("graceHealth"));
        boolean war = Boolean.TRUE.equals(o.get("enemy")) && Boolean.TRUE.equals(o.get("enemyHostile")) && Boolean.TRUE.equals(o.get("friendStillPeace"));
        boolean rebels = Boolean.TRUE.equals(o.get("vindicatorSpares")) && num(o, "rebelFavour") >= 5 && num(o, "allies") == 3
            && Boolean.TRUE.equals(o.get("alliesSpare"));
        boolean forms = Boolean.TRUE.equals(o.get("breachedByLord")) && "0->1".equals(o.get("revive")) && num(o, "phase") == 3
            && "minecraft:mace".equals(o.get("mainhand")) && num(o, "bolts") > 0 && num(o, "swarms") > 0;
        boolean crown = num(o, "crownDropped") >= 1 && Boolean.TRUE.equals(o.get("keeperEnemy")) && Boolean.TRUE.equals(o.get("presented"))
            && num(o, "festival") >= 1;
        boolean chamber = Boolean.TRUE.equals(o.get("circleStone")) && num(o, "filled") >= 8 && num(o, "workshops") >= 6 && num(o, "ladders") >= 8
            && num(o, "lying") >= 5 && Boolean.TRUE.equals(o.get("journal")) && Boolean.TRUE.equals(o.get("arrived"));
        o.put("passPeace", peace);
        o.put("passWar", war);
        o.put("passRebels", rebels);
        o.put("passForms", forms);
        o.put("passCrown", crown);
        o.put("passChamber", chamber);
        o.put("pass", peace && war && rebels && forms && crown && chamber);
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
