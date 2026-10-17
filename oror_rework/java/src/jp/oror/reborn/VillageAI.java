package jp.oror.reborn;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.levelgen.Heightmap.Types;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * Village roles (v0.17.9; redrawn in v0.17.14), called from AdaptiveCombat.tick, AdaptiveCombat.damage and VillagerLife.tick.
 * - Guards (衛兵) are Guard Villagers' guards. They fight with their own AI (AdaptiveCombat leaves them alone); here they
 *   only answer a villager's cry for help.
 * - Strong villagers: armorers, weaponsmiths, toolsmiths, fletchers, butchers, leatherworkers, masons and miners. They are
 *   villagers like any other - they work by day, sleep at night and carry their gear only while danger is near - but they
 *   do not run: they take on what threatens them or the villagers around them, within 16 blocks of where they stood, and
 *   go back to work once it is beaten or gone. Creepers they leave to the archers.
 * - Every other villager, and every child, runs: home at night, behind a guard or a strong villager by day, or away, and
 *   strikes back only when cornered at arm's length.
 * Every walk here is given as a ground speed, so profession, growth and potion bonuses to movement speed no longer turn
 * villagers into a blur: a mob's ground speed grows with the square of its speed value, and the old 1.1-1.35 multipliers on
 * a boosted villager came to 20-80 blocks a second.
 */
public final class VillageAI {
    /** Ground speeds (movement speed value; about 44 x value^2 blocks a second). Vanilla villagers walk at 0.25. */
    static final double WORK = 0.3;
    static final double FLEE = 0.36;
    static final double CHARGE = 0.38;
    /** How far from where it stood a strong villager follows a fight. */
    private static final double REACH = 16.0;
    private static final Set<String> STRONG = Set.of("armorer", "weaponsmith", "toolsmith", "fletcher", "butcher", "leatherworker", "mason", "miner");
    private static final Set<String> SHOOTERS = Set.of("bow", "crossbow", "trident");

    private VillageAI() {
    }

    /** Guards: other mods' village guards. A villager is never one. */
    public static boolean fighter(Mob m) {
        return !(m instanceof Villager) && AdaptiveCombat.guardian(m);
    }

    /** A grown villager of one of the strong trades (with armed villagers on). */
    public static boolean strong(Mob m) {
        return m instanceof Villager v && (Boolean) RebornConfig.ARMED_VILLAGERS.get() && !v.isBaby() && STRONG.contains(VillagerRoles.profession(v));
    }

    public static boolean fleeing(Mob m) {
        return MobMind.data(m).getLong("VillageFlee") > m.level().getGameTime();
    }

    /** True when the combat AI should sit this tick out (a villager that is asleep, fleeing or simply living its day). */
    static boolean tick(Mob m, ServerLevel sl, CompoundTag n) {
        if (!(m instanceof Villager v)) {
            return false;
        }
        if (v.isSleeping()) {
            // asleep: nothing until something wakes them (being hurt does)
            return true;
        }
        long now = sl.getGameTime();
        return strong(v) ? stand(v, sl, n, now) : civilian(v, sl, n, now);
    }

    /** May m take e on? A guard always; a strong villager that is awake when e is within reach of where it stood. */
    static boolean engage(Mob m, LivingEntity e) {
        if (fighter(m)) {
            return true;
        }
        return e != null && strong(m) && !((Villager) m).isSleeping() && !far(e, spot(m, MobMind.data(m)), REACH);
    }

    // ------------------------------------------------------------------------------------- strong villagers
    /** A strong villager's turn: fight what is near, let it go once it is beaten or far, otherwise live like the rest. */
    private static boolean stand(Villager v, ServerLevel sl, CompoundTag n, long now) {
        LivingEntity t = v.getTarget();
        if (t != null && (!AdaptiveCombat.enemy(v, t) || far(t, spot(v, n), REACH + 4.0))) {
            // beaten or run off: back to the day's work
            v.setTarget(null);
            v.setLastHurtByMob(null);
            t = null;
        }
        if (t == null && (now + v.getId()) % 10L == 0L) {
            t = foe(v, sl, n);
            if (t != null) {
                v.setTarget(t);
                alarm(sl, v, t);
            }
        }
        if (t == null) {
            // creepers and what is out of reach: step away like anyone else
            return civilian(v, sl, n, now);
        }
        n.putLong("VillageStand", spot(v, n).asLong());
        n.putLong("VillageStandUntil", now + 200L);
        gear(v, n, now, true);
        label(v, "応戦中");
        return false;
    }

    /** Where the fight began (for ten seconds after it ends), or where the villager stands now. */
    private static BlockPos spot(Mob m, CompoundTag n) {
        return n.getLong("VillageStandUntil") > m.level().getGameTime() ? BlockPos.of(n.getLong("VillageStand")) : m.blockPosition();
    }

    /** Whoever hurt it, or the hostile nearby that hunts someone (or is at arm's length) and is in sight; menaces first. */
    private static LivingEntity foe(Villager v, ServerLevel sl, CompoundTag n) {
        BlockPos at = spot(v, n);
        LivingEntity hurt = v.getLastHurtByMob();
        if (AdaptiveCombat.enemy(v, hurt) && !far(hurt, at, REACH)) {
            return hurt;
        }
        boolean shooter = SHOOTERS.contains(VillagerRoles.preferred(v));
        LivingEntity best = null;
        double score = Double.MAX_VALUE;
        for (Mob e : sl.getEntitiesOfClass(Mob.class, v.getBoundingBox().inflate(REACH, 6.0, REACH), x -> x instanceof Enemy && AdaptiveCombat.enemy(v, x))) {
            if (!shooter && BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).getPath().equals("creeper") || far(e, at, REACH)) {
                continue;
            }
            LivingEntity aim = e.getTarget();
            boolean menace = aim != null && (aim instanceof Player || aim instanceof Mob a && AdaptiveCombat.allied(v, a));
            double d = Math.sqrt(v.distanceToSqr(e));
            if (!menace && d > 6.0 || d > 4.0 && !v.getSensing().hasLineOfSight(e)) {
                continue;
            }
            double s = d - (menace ? 8.0 : 0.0);
            if (s < score) {
                score = s;
                best = e;
            }
        }
        return best;
    }

    /** A cry for help: guards and strong villagers near the threat answer (three at most), the rest within earshot run. */
    static void alarm(ServerLevel sl, Mob caller, LivingEntity threat) {
        CompoundTag n = MobMind.data(caller);
        long now = sl.getGameTime();
        if (n.getLong("VillageAlarmAt") > now) {
            return;
        }
        n.putLong("VillageAlarmAt", now + 100L);
        RelicEffects.sound(sl, caller.blockPosition(), SoundEvents.VILLAGER_NO, 1.3F, 0.7F);
        sl.sendParticles(ParticleTypes.ANGRY_VILLAGER, caller.getX(), caller.getEyeY() + 0.6, caller.getZ(), 1, 0.0, 0.0, 0.0, 0.0);
        List<Mob> near = sl.getEntitiesOfClass(Mob.class, caller.getBoundingBox().inflate(32.0, 8.0, 32.0),
                x -> x != caller && AdaptiveCombat.guardian(x) && AdaptiveCombat.active(x) && AdaptiveCombat.allied(caller, x))
            .stream()
            .sorted(Comparator.comparingDouble(caller::distanceToSqr))
            .toList();
        int answered = 0;
        for (Mob a : near) {
            if (fighter(a) || strong(a)) {
                if (answered < 3 && a.getTarget() == null && a.distanceToSqr(threat) < 576.0 && engage(a, threat)) {
                    a.setTarget(threat);
                    answered++;
                }
            } else {
                CompoundTag d = MobMind.data(a);
                d.putLong("VillageAlarm", now + 160L);
                d.putDouble("VillageAlarmX", threat.getX());
                d.putDouble("VillageAlarmZ", threat.getZ());
            }
        }
    }

    // ------------------------------------------------------------------------------------- villagers
    private static boolean civilian(Mob m, ServerLevel sl, CompoundTag n, long now) {
        LivingEntity t = m.getTarget();
        LivingEntity threat = null;
        if (t != null) {
            if (AdaptiveCombat.enemy(m, t) && cornered(m, t)) {
                gear(m, n, now, true);
                return false;
            }
            // shared targets and grudges are for the guards and the strong; a villager steps back from them
            m.setTarget(null);
            if (AdaptiveCombat.enemy(m, t) && m.distanceToSqr(t) < 400.0) {
                threat = t;
            }
        }
        if (threat == null && (now + m.getId()) % 10L != 0L) {
            return true;
        }
        if (threat == null) {
            threat = danger(m, sl);
        }
        Vec3 from = threat != null ? threat.position() : null;
        if (from == null && n.getLong("VillageAlarm") > now) {
            Vec3 alarm = new Vec3(n.getDouble("VillageAlarmX"), m.getY(), n.getDouble("VillageAlarmZ"));
            from = alarm.distanceToSqr(m.position()) < 576.0 ? alarm : null;
        }
        if (from == null) {
            gear(m, n, now, false);
            return true;
        }
        gear(m, n, now, true);
        if (threat != null && cornered(m, threat)) {
            m.setTarget(threat);
            return false;
        }
        flee(m, sl, n, from, now);
        return true;
    }

    /**
     * v0.17.13: a villager, strong or not, wears armor and carries a weapon only while danger is near, and puts them away
     * ten seconds after it passes, so the profession's clothes show the rest of the time. Only the gear MobLevels.arm
     * gave is taken off; anything a player handed over stays.
     */
    private static void gear(Mob m, CompoundTag n, long now, boolean danger) {
        if (!(Boolean) RebornConfig.ARMED_VILLAGERS.get() || m.isBaby()) {
            return;
        }
        if (danger) {
            n.putLong("VillageGearUntil", now + 200L);
            if (!n.contains("VillageGeared") || !n.getBoolean("VillageGeared")) {
                // arming also sets the armed health; keep the wounds the villager already has
                float health = m.getHealth();
                MobLevels.arm(m);
                m.setHealth(Math.min(health, m.getMaxHealth()));
                n.putBoolean("VillageGeared", true);
            }
        } else if (now >= n.getLong("VillageGearUntil") && (!n.contains("VillageGeared") || n.getBoolean("VillageGeared"))) {
            for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.OFFHAND, EquipmentSlot.MAINHAND)) {
                String key = "Managed_" + slot.getName();
                ItemStack worn = m.getItemBySlot(slot);
                if (!worn.isEmpty() && n.contains(key) && ItemStack.isSameItemSameComponents(worn, ItemStack.parseOptional(m.registryAccess(), n.getCompound(key)))) {
                    m.setItemSlot(slot, ItemStack.EMPTY);
                }
            }
            // the role weapon the combat AI switched to (a bow, an axe...) is this mod's vanilla weapon too
            ItemStack hand = m.getMainHandItem();
            if (n.getBoolean("OriginalAuto") && !AdaptiveCombat.foreign(hand) && (hand.getItem() instanceof net.minecraft.world.item.SwordItem
                || hand.getItem() instanceof net.minecraft.world.item.AxeItem || hand.getItem() instanceof net.minecraft.world.item.ProjectileWeaponItem
                || hand.is(net.minecraft.world.item.Items.TRIDENT) || hand.is(net.minecraft.world.item.Items.MACE))) {
                m.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
            }
            n.remove("Selected");
            n.putBoolean("VillageGeared", false);
        }
    }

    /**
     * v0.17.13: at night every villager goes home to bed (the brain takes it the last steps and to sleep);
     * from far away it is walked home first. Returns the status line.
     */
    static String bedtime(Villager v, ServerLevel sl) {
        if (v.isSleeping()) {
            return "就寝";
        }
        BlockPos home = home(v, sl);
        if (home != null && home.distSqr(v.blockPosition()) > 36.0) {
            walk(v, home, pace(v, WORK), 1);
            return "帰宅中";
        }
        return "就寝準備";
    }

    private static boolean cornered(Mob m, LivingEntity t) {
        return m.distanceToSqr(t) < 6.25 && (t instanceof Mob h && h.getTarget() == m || m.getLastHurtByMob() == t);
    }

    /** Whoever hurt the villager, or the nearest hostile that is close or hunting someone, and in sight. */
    private static LivingEntity danger(Mob m, ServerLevel sl) {
        LivingEntity hurt = m.getLastHurtByMob();
        if (AdaptiveCombat.enemy(m, hurt) && m.distanceToSqr(hurt) < 400.0) {
            return hurt;
        }
        return sl.getEntitiesOfClass(Mob.class, m.getBoundingBox().inflate(14.0, 6.0, 14.0), e -> e instanceof Enemy && AdaptiveCombat.enemy(m, e) && menacing(m, e))
            .stream()
            .min(Comparator.comparingDouble(m::distanceToSqr))
            .orElse(null);
    }

    private static boolean menacing(Mob m, Mob e) {
        double d = m.distanceToSqr(e);
        LivingEntity aim = e.getTarget();
        boolean hunting = aim != null && (aim == m || aim instanceof Player || aim instanceof Mob a && AdaptiveCombat.guardian(a));
        return (d < 9.0 || m.getSensing().hasLineOfSight(e)) && (d < 64.0 || hunting);
    }

    private static void flee(Mob m, ServerLevel sl, CompoundTag n, Vec3 from, long now) {
        Vec3 me = m.position();
        Vec3 away = BossPowers.flat(me.subtract(from));
        double danger = me.distanceToSqr(from);
        BlockPos home = home(m, sl);
        boolean homeSafe = home != null && home.distSqr(m.blockPosition()) < 2304.0 && safe(me, Vec3.atCenterOf(home), from, danger);
        BlockPos to = !sl.isDay() && homeSafe ? home : null;
        if (to == null) {
            // run behind the nearest guard or strong villager that is not in the threat's direction
            for (Mob g : sl.getEntitiesOfClass(Mob.class, m.getBoundingBox().inflate(24.0, 6.0, 24.0), x -> x != m && AdaptiveCombat.active(x) && (fighter(x) || strong(x)) && AdaptiveCombat.allied(m, x))
                .stream()
                .sorted(Comparator.comparingDouble(m::distanceToSqr))
                .toList()) {
                Vec3 behind = g.position().add(BossPowers.flat(g.position().subtract(from)).scale(3.0));
                if (safe(me, behind, from, danger)) {
                    to = BlockPos.containing(behind);
                    break;
                }
            }
        }
        if (to == null && homeSafe) {
            to = home;
        }
        if (to == null) {
            to = BlockPos.containing(me.add(away.scale(12.0)));
        }
        BlockPos dest = ground(sl, to, m.blockPosition().getY(), 6);
        walk(m, dest != null ? dest : to, pace(m, FLEE), 1);
        n.putLong("VillageFlee", now + 40L);
        label(m, "避難中");
        sl.sendParticles(ParticleTypes.SPLASH, m.getX(), m.getEyeY() + 0.35, m.getZ(), 3, 0.15, 0.05, 0.15, 0.0);
    }

    /** A refuge must lie farther from the threat than we stand, and not past it. */
    private static boolean safe(Vec3 me, Vec3 refuge, Vec3 from, double danger) {
        Vec3 go = refuge.subtract(me);
        Vec3 toward = from.subtract(me);
        double len = Math.sqrt(go.x * go.x + go.z * go.z) * Math.sqrt(toward.x * toward.x + toward.z * toward.z);
        boolean pastIt = len > 1.0E-4 && (go.x * toward.x + go.z * toward.z) / len > 0.4;
        return refuge.distanceToSqr(from) > danger + 9.0 && !pastIt;
    }

    private static BlockPos home(Mob m, ServerLevel sl) {
        if (m instanceof Villager v) {
            Optional<?> o = v.getBrain().getMemory(MemoryModuleType.HOME);
            if (o.isPresent() && o.get() instanceof GlobalPos g && g.dimension().equals(sl.dimension())) {
                return g.pos();
            }
        }
        return null;
    }

    // ------------------------------------------------------------------------------------- shared
    /** Movement speed multiplier that makes this mob move at the given ground speed, whatever its bonuses. */
    static float pace(Mob m, double speed) {
        return (float) Math.max(0.2, Math.min(1.6, speed / Math.max(0.05, m.getAttributeValue(Attributes.MOVEMENT_SPEED))));
    }

    /** Walk somewhere; villagers through their brain, so their own panic and schedule do not pull them elsewhere. */
    static void walk(Mob m, BlockPos p, float mod, int close) {
        if (m instanceof Villager v) {
            // the brain's walk sink only re-paths when the target moves, so setting it again is cheap
            v.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(p, mod, close));
            return;
        }
        CompoundTag n = MobMind.data(m);
        if (n.contains("VillageWalk") && !m.getNavigation().isDone() && BlockPos.of(n.getLong("VillageWalk")).distSqr(p) <= 2.0) {
            return;
        }
        n.putLong("VillageWalk", p.asLong());
        m.getNavigation().moveTo(p.getX() + 0.5, p.getY(), p.getZ() + 0.5, mod);
    }

    private static boolean far(LivingEntity e, BlockPos post, double r) {
        if (post == null) {
            return false;
        }
        double dx = e.getX() - (post.getX() + 0.5);
        double dz = e.getZ() - (post.getZ() + 0.5);
        return dx * dx + dz * dz > r * r;
    }

    /** The ground at p's column, if the chunk is loaded and it is within reach of the given height. */
    private static BlockPos ground(ServerLevel sl, BlockPos p, int y, int reach) {
        if (!sl.hasChunkAt(p)) {
            return null;
        }
        int top = sl.getHeight(Types.MOTION_BLOCKING_NO_LEAVES, p.getX(), p.getZ());
        return Math.abs(top - y) <= reach ? new BlockPos(p.getX(), top, p.getZ()) : null;
    }

    private static void label(Mob m, String task) {
        if (m instanceof Villager v) {
            VillagerLife.data(v).putString("Task", task);
        }
    }
}
