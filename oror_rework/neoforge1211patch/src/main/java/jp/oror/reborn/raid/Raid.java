package jp.oror.reborn.raid;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.saveddata.SavedData;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059e) Raid health for the 41 gods (the user's V20 hp_raid.md: "撃破可能なレイド戦モード").
 * <p>
 * In lore mode a god cannot be beaten: several take no damage at all (ABSOLUTE), others a thousandth or less, and the
 * undying ones rise again without end. A raid is a separate state that begins when a player strikes a god (the
 * player's own blow, arrow, pet or summon) and ends a minute after the last player blow with no player near. In a raid:
 * <ul>
 * <li>the god has its raid health from the user's table ({@link RaidTable}, 9,000 to 102,400), kept in its save
 * (restart, unload, dimension change); its shown health is the same share of its own (at most 1,024);</li>
 * <li>the lore's outright defences (no damage, a thousandth, rewinding, healing to full when struck) give way to a
 * guard: a share of the raid health (8% for the gods whose lore makes them untouchable, 7% for those with conditional
 * immunity, 5% for the rest) that takes half of every blow until it breaks; then the god is broken for ten seconds
 * (damage x1.5, caps x2.5); thirty seconds later the guard comes back, with a warning three seconds before (the
 * "予兆");</li>
 * <li>no blow takes more than 5% of the raid health (15% while broken), and no second more than 0.33 to 0.65% of it
 * (the bigger the god, the smaller the share), a quarter more for each other player who struck in the last ten seconds
 * (up to six): a million-damage weapon or a stack of them cannot end a raid in a few blows;</li>
 * <li>healing is a share of the raid health (at most 4% at once, then nothing for thirty seconds), not the lore's
 * x10,000;</li>
 * <li>the undying gods (LorePowers.IMMORTAL) rise once, with 35% and a whole guard, three seconds untouchable; the
 * second fall is death (no lore revival);</li>
 * <li>the raid uses the god's own boss bar, red and notched: the stage, the raid health, the guard left and BREAK.</li>
 * </ul>
 * Outside a raid nothing changes (the lore, its immunities and revivals, damage between gods and from mobs). Between
 * raids the raid health comes back at 1% a second. A raid needs lore mode (with lore mode off the gods have their own
 * balanced health). "/oror raid off" turns raids off for the world (kept in its save), "/oror raid on" back on.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class Raid {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Raid");
    static final String KEY = "ororRaid";
    /** The gods whose lore makes them untouchable. */
    static final Set<String> ABSOLUTE = jp.oror.reborn.LorePowers.ABSOLUTE;
    /** Conditional immunity or great damage reduction in the lore. */
    static final Set<String> GUARDED = Set.of("kokuhaku", "shinra", "hakyoku", "forbidden_arcana", "valeria", "relentless_research",
        "ouroboros", "mels", "kurma", "taika", "chaos");
    /** The undying. */
    static final Set<String> IMMORTAL = jp.oror.reborn.LorePowers.IMMORTAL;

    static final long END_AFTER = 1200;       // a minute without a player blow (and no player near)
    static final long BREAK_TICKS = 200;      // broken for ten seconds
    static final long GUARD_BACK = 600;       // the guard back thirty seconds after the break ends
    static final long HEAL_GAP = 600;         // one heal per thirty seconds
    static final float HEAL_MAX = 0.04F;
    static final float HIT_CAP = 0.05F, HIT_CAP_BROKEN = 0.15F;
    static final float BROKEN_DAMAGE = 1.5F, BROKEN_CAPS = 2.5F;
    static final float REVIVE = 0.35F;

    private static boolean enabled = true;
    /** The gods being struck right now (SupremeEntity.hurt), whose lore gives way to the raid (the server thread's own). */
    private static final ThreadLocal<ArrayDeque<Object>> STRUCK = ThreadLocal.withInitial(ArrayDeque::new);
    private static final Object NONE = new Object();
    private record Hit(long at, float damage) {
    }

    private static final Map<UUID, ArrayDeque<Hit>> RECENT = new HashMap<>();
    private static final Map<UUID, Map<UUID, Long>> STRIKERS = new HashMap<>();
    public static int started, ended, broken, revived, slain;

    private Raid() {
    }

    // ------------------------------------------------------------------------------------------------- the switch

    public static final class Mode extends SavedData {
        boolean off;

        static Mode load(CompoundTag t, HolderLookup.Provider p) {
            Mode m = new Mode();
            m.off = t.getBoolean("Off");
            return m;
        }

        @Override
        public CompoundTag save(CompoundTag t, HolderLookup.Provider p) {
            t.putBoolean("Off", off);
            return t;
        }

        static Mode of(MinecraftServer s) {
            return s.overworld().getDataStorage().computeIfAbsent(new SavedData.Factory<>(Mode::new, Mode::load, null), "oror_raid");
        }
    }

    public static boolean enabled() {
        return enabled;
    }

    public static void enable(MinecraftServer s, boolean on) {
        Mode m = Mode.of(s);
        m.off = !on;
        m.setDirty();
        enabled = on;
    }

    @SubscribeEvent
    public static void started(ServerStartedEvent e) {
        try {
            enabled = !Mode.of(e.getServer()).off;
        } catch (RuntimeException ex) {
            enabled = true;
        }
    }

    // ------------------------------------------------------------------------------------------------- state

    static CompoundTag state(SupremeEntity b) {
        return b.getPersistentData().getCompound(KEY);
    }

    static void keep(SupremeEntity b, CompoundTag t) {
        b.getPersistentData().put(KEY, t);
    }

    public static boolean active(Entity e) {
        return e instanceof SupremeEntity b && b.getPersistentData().getCompound(KEY).getBoolean("On");
    }

    public static float health(SupremeEntity b) {
        return state(b).getFloat("Hp");
    }

    public static float max(SupremeEntity b) {
        return state(b).getFloat("Max");
    }

    static float guardShare(String id) {
        return ABSOLUTE.contains(id) ? 0.08F : GUARDED.contains(id) ? 0.07F : 0.05F;
    }

    /** The share of the raid health one second may take: 0.65% for the smallest gods, 0.33% for the biggest. */
    static float secondShare(RaidTable.Entry t) {
        float s = (float) (0.0045 * Math.sqrt(30.0 / Math.max(1, t.times())));
        return Math.max(0.0033F, Math.min(0.0065F, s));
    }

    /** True when the blow is a player's: the player, an arrow or spell of theirs, their pet or summon. */
    static Player playerOf(DamageSource s) {
        Entity e = s.getEntity();
        if (e instanceof Player p) {
            return p;
        }
        if (e instanceof OwnableEntity o && o.getOwner() instanceof Player p) {
            return p;
        }
        if (e != null && e.getPersistentData().hasUUID("ororRelicOwner") && e.level() instanceof ServerLevel sl
            && sl.getEntity(e.getPersistentData().getUUID("ororRelicOwner")) instanceof Player p) {
            return p;
        }
        return null;
    }

    // ------------------------------------------------------------------------------------------------- SupremeEntity.hurt

    /** At the head of SupremeEntity.hurt: a player's blow starts a raid; while one is on, the god's lore gives way. */
    public static void enter(SupremeEntity b, DamageSource s) {
        boolean raid = false;
        if (!b.level().isClientSide && b.level() instanceof ServerLevel sl && !s.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            CompoundTag t = state(b);
            Player p = playerOf(s);
            if (t.getBoolean("On") && !enabled) {
                end(b, sl, "レイド戦は無効");
            } else if (t.getBoolean("On")) {
                raid = true;
            } else if (p != null && enabled && b.isAlive() && b.lore() && RaidTable.of(b.spec.id) != null) {
                begin(b, sl);
                raid = true;
            }
            if (raid && p != null) {
                CompoundTag u = state(b);
                u.putLong("Fight", sl.getGameTime());
                keep(b, u);
                STRIKERS.computeIfAbsent(b.getUUID(), k -> new HashMap<>()).put(p.getUUID(), sl.getGameTime());
            }
        }
        STRUCK.get().push(raid ? b : NONE);
    }

    public static void leave() {
        ArrayDeque<Object> s = STRUCK.get();
        if (!s.isEmpty()) {
            s.pop();
        }
    }

    /** SupremeEntity.lore() inside its own hurt during a raid. */
    public static boolean struck(Object b) {
        ArrayDeque<Object> s = STRUCK.get();
        return !s.isEmpty() && s.peek() == b;
    }

    /** Any god being struck in a raid right now (CombatMemory's resistance is bounded then). */
    public static boolean anyStruck() {
        ArrayDeque<Object> s = STRUCK.get();
        return !s.isEmpty() && s.peek() != NONE;
    }

    static void begin(SupremeEntity b, ServerLevel sl) {
        RaidTable.Entry e = RaidTable.of(b.spec.id);
        CompoundTag t = state(b);
        float max = e.health();
        float hp = t.contains("Hp") && t.getFloat("Max") == max && t.getFloat("Hp") > 0F ? t.getFloat("Hp") : max;
        long now = sl.getGameTime();
        t.putBoolean("On", true);
        t.putFloat("Max", max);
        t.putFloat("Hp", hp);
        t.putFloat("GuardMax", max * guardShare(b.spec.id));
        if (!t.contains("Guard") || hp >= max) {
            t.putFloat("Guard", max * guardShare(b.spec.id));
        }
        t.putLong("Start", now);
        t.putLong("Fight", now);
        t.remove("Final");
        keep(b, t);
        RECENT.remove(b.getUUID());
        STRIKERS.remove(b.getUUID());
        show(b);
        started++;
        tell(b, sl, Component.literal("【レイド戦開始】" + b.spec.name + "　レイド体力 " + whole(hp) + " / " + whole(max)).withStyle(ChatFormatting.RED));
        LOG.info("RAID begins: {} {} / {} at {}", b.spec.id, whole(hp), whole(max), b.blockPosition().toShortString());
    }

    static void end(SupremeEntity b, ServerLevel sl, String why) {
        CompoundTag t = state(b);
        t.putBoolean("On", false);
        keep(b, t);
        RECENT.remove(b.getUUID());
        STRIKERS.remove(b.getUUID());
        ended++;
        tell(b, sl, Component.literal("【レイド戦終了】" + b.spec.name + "（" + why + "）").withStyle(ChatFormatting.GRAY));
    }

    // ------------------------------------------------------------------------------------------------- damage

    /** The blow's damage, after armour and every other change, becomes raid damage; the shown health follows. */
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void damage(LivingDamageEvent.Pre e) {
        if (!(e.getEntity() instanceof SupremeEntity b) || !(b.level() instanceof ServerLevel sl) || !active(b)
            || e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            return;
        }
        CompoundTag t = state(b);
        RaidTable.Entry entry = RaidTable.of(b.spec.id);
        if (entry == null) {
            return;
        }
        long now = sl.getGameTime();
        float max = t.getFloat("Max");
        float hp = t.getFloat("Hp");
        b.setAbsorptionAmount(0F);
        if (now < t.getLong("Untouchable")) {
            e.setNewDamage(0F);
            return;
        }
        float dmg = e.getNewDamage();
        if (!(dmg > 0F)) {
            e.setNewDamage(0F);
            return;
        }
        if (!Float.isFinite(dmg)) {
            dmg = max;
        }
        boolean brk = now < t.getLong("BreakUntil");
        if (brk) {
            dmg *= BROKEN_DAMAGE;
        }
        dmg = Math.min(dmg, max * (brk ? HIT_CAP_BROKEN : HIT_CAP));
        // the second's room
        ArrayDeque<Hit> recent = RECENT.computeIfAbsent(b.getUUID(), k -> new ArrayDeque<>());
        float used = 0F;
        for (Iterator<Hit> it = recent.iterator(); it.hasNext(); ) {
            Hit h = it.next();
            if (now - h.at() >= 20) {
                it.remove();
            } else {
                used += h.damage();
            }
        }
        float room = max * secondShare(entry) * group(b, now) * (brk ? BROKEN_CAPS : 1F) - used;
        dmg = Math.max(0F, Math.min(dmg, room));
        if (dmg <= 0F) {
            e.setNewDamage(0F);
            return;
        }
        recent.add(new Hit(now, dmg));
        // the guard takes half until it breaks
        float guard = t.getFloat("Guard");
        if (guard > 0F && !brk) {
            float took = Math.min(guard, dmg * 0.5F);
            guard -= took;
            dmg -= took;
            t.putFloat("Guard", guard);
            if (guard <= 0F) {
                t.putLong("BreakUntil", now + BREAK_TICKS);
                t.putLong("GuardBack", now + BREAK_TICKS + GUARD_BACK);
                t.remove("Warned");
                broken++;
                sl.sendParticles(ParticleTypes.EXPLOSION, b.getX(), b.getY() + b.getBbHeight() * 0.6, b.getZ(), 3, 0.6, 0.6, 0.6, 0);
                tell(b, sl, Component.literal("【ブレイク】" + b.spec.name + "の防御が砕けた！ 10秒間 被ダメージ1.5倍").withStyle(ChatFormatting.GOLD));
            }
        }
        hp -= dmg;
        t.putFloat("Dealt", t.getFloat("Dealt") + dmg);
        if (hp <= 0F) {
            if (IMMORTAL.contains(b.spec.id) && t.getInt("Rose") < 1) {
                // the undying rise once in a raid
                t.putInt("Rose", t.getInt("Rose") + 1);
                hp = max * REVIVE;
                t.putFloat("Guard", t.getFloat("GuardMax"));
                t.putLong("BreakUntil", 0L);
                t.putLong("Untouchable", now + 60);
                t.putFloat("Hp", hp);
                keep(b, t);
                RECENT.remove(b.getUUID());
                revived++;
                e.setNewDamage(0F);
                b.setHealth(shown(b, hp, max));
                sl.sendParticles(ParticleTypes.END_ROD, b.getX(), b.getY() + b.getBbHeight() * 0.5, b.getZ(), 40, 0.8, 1.0, 0.8, 0.15);
                tell(b, sl, Component.literal("【第二段階】" + b.spec.name + "が再臨した（レイド体力 " + whole(hp) + "）").withStyle(ChatFormatting.LIGHT_PURPLE));
                return;
            }
            t.putFloat("Hp", 0F);
            t.putBoolean("Final", true);
            keep(b, t);
            RECENT.remove(b.getUUID());
            STRIKERS.remove(b.getUUID());
            slain++;
            e.setNewDamage(b.getHealth() + 1F);
            tell(b, sl, Component.literal("【討伐】" + b.spec.name + "を討ち果たした（"
                + String.format(Locale.ROOT, "%.0f", (now - t.getLong("Start")) / 20.0) + "秒）").withStyle(ChatFormatting.GOLD));
            return;
        }
        t.putFloat("Hp", hp);
        keep(b, t);
        float target = shown(b, hp, max);
        e.setNewDamage(Math.max(0F, b.getHealth() - target));
    }

    /** One for a single player, a quarter more for each other player who struck in the last ten seconds (up to six). */
    static float group(SupremeEntity b, long now) {
        Map<UUID, Long> m = STRIKERS.get(b.getUUID());
        int n = 0;
        if (m != null) {
            m.values().removeIf(at -> now - at > 200);
            n = m.size();
        }
        return 1F + 0.25F * (Math.max(1, Math.min(6, n)) - 1);
    }

    static float shown(SupremeEntity b, float hp, float max) {
        return Math.max(hp > 0F ? 0.01F : 0F, b.getMaxHealth() * hp / max);
    }

    /** SupremeEntity.heal during a raid: a share of the raid health, at most 4% at once, once per thirty seconds. */
    public static void heal(SupremeEntity b, float amount) {
        if (!(b.level() instanceof ServerLevel sl) || !(amount > 0F) || b.isDeadOrDying()) {
            return;
        }
        CompoundTag t = state(b);
        long now = sl.getGameTime();
        if (now < t.getLong("HealAt")) {
            return;
        }
        float max = t.getFloat("Max");
        float hp = t.getFloat("Hp");
        float add = Math.min(max * HEAL_MAX, Math.min(1F, amount / Math.max(1F, b.getMaxHealth())) * max);
        if (add <= 0F || hp >= max) {
            return;
        }
        hp = Math.min(max, hp + add);
        t.putFloat("Hp", hp);
        t.putLong("HealAt", now + HEAL_GAP);
        t.putFloat("Healed", t.getFloat("Healed") + add);
        keep(b, t);
        b.setHealth(shown(b, hp, max));
    }

    /** For the CI's checks: the raid health set outright (the raid must be on). */
    public static void testHealth(SupremeEntity b, float hp) {
        CompoundTag t = state(b);
        if (t.getBoolean("On")) {
            t.putFloat("Hp", Math.max(0F, Math.min(t.getFloat("Max"), hp)));
            t.putFloat("Guard", 0F);
            keep(b, t);
            RECENT.remove(b.getUUID());
        }
    }

    /** SupremeEntity.immortal(): the raid's last fall is death. */
    public static boolean slainInRaid(SupremeEntity b) {
        return b.getPersistentData().getCompound(KEY).getBoolean("Final");
    }

    // ------------------------------------------------------------------------------------------------- the boss bar

    /** The raid's line on the god's boss bar, or null outside a raid. */
    public static Component title(SupremeEntity b) {
        CompoundTag t = state(b);
        if (!t.getBoolean("On")) {
            return null;
        }
        long now = b.level().getGameTime();
        StringBuilder s = new StringBuilder("【レイド】").append(b.spec.name).append("　第").append(1 + t.getInt("Rose")).append("段階　")
            .append(whole(t.getFloat("Hp"))).append(" / ").append(whole(t.getFloat("Max")));
        if (now < t.getLong("BreakUntil")) {
            s.append("　ブレイク！");
        } else if (t.getFloat("GuardMax") > 0F) {
            s.append("　防御 ").append(Math.round(100F * t.getFloat("Guard") / t.getFloat("GuardMax"))).append("%");
        }
        return Component.literal(s.toString());
    }

    static void show(SupremeEntity b) {
        CompoundTag t = state(b);
        if (t.getFloat("Max") > 0F) {
            b.setHealth(shown(b, t.getFloat("Hp"), t.getFloat("Max")));
        }
    }

    // ------------------------------------------------------------------------------------------------- time

    @SubscribeEvent
    public static void serverTick(ServerTickEvent.Pre e) {
        // a hurt that threw leaves nothing behind
        STRUCK.get().clear();
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof SupremeEntity b) || !(b.level() instanceof ServerLevel sl) || !b.isAlive()) {
            return;
        }
        if (!b.getPersistentData().contains(KEY)) {
            return;
        }
        CompoundTag t = state(b);
        if (t.getBoolean("Final") && b.getHealth() > 0F) {
            // its last fall was turned away (Duel Dominion's duel seals the god it defeats; a totem): the raid is over.
            // Without this a god called back out of its seal would carry its raid's empty health and die at once.
            b.getPersistentData().remove(KEY);
            RECENT.remove(b.getUUID());
            STRIKERS.remove(b.getUUID());
            LOG.info("RAID cleared: {} lives on after its last fall (sealed or saved)", b.spec.id);
            return;
        }
        if (b.tickCount % 10 != 0) {
            return;
        }
        long now = sl.getGameTime();
        float max = t.getFloat("Max");
        if (max <= 0F) {
            return;
        }
        if (!t.getBoolean("On")) {
            // between raids the raid health comes back, 1% a second
            float hp = t.getFloat("Hp");
            if (hp < max && b.tickCount % 20 == 0) {
                t.putFloat("Hp", Math.min(max, hp + max * 0.01F));
                keep(b, t);
            }
            return;
        }
        float hp = t.getFloat("Hp");
        // the shown health follows the raid health
        float want = shown(b, hp, max);
        if (Math.abs(b.getHealth() - want) > 0.5F) {
            b.setHealth(want);
        }
        // the guard comes back, with a warning first
        long back = t.getLong("GuardBack");
        if (back > 0 && t.getFloat("Guard") <= 0F) {
            if (now >= back) {
                t.putFloat("Guard", t.getFloat("GuardMax"));
                t.putLong("GuardBack", 0L);
                keep(b, t);
                tell(b, sl, Component.literal("【防御再展開】" + b.spec.name + "の防御が戻った").withStyle(ChatFormatting.AQUA));
            } else if (now >= back - 60 && !t.getBoolean("Warned")) {
                t.putBoolean("Warned", true);
                keep(b, t);
                sl.sendParticles(ParticleTypes.ENCHANT, b.getX(), b.getY() + b.getBbHeight() * 0.5, b.getZ(), 60, 1.2, 1.2, 1.2, 0.6);
                tell(b, sl, Component.literal("【予兆】" + b.spec.name + "が防御を張り直そうとしている（3秒）").withStyle(ChatFormatting.YELLOW));
            }
        }
        // the end: a minute without a player's blow and no player near
        if (now - t.getLong("Fight") > END_AFTER && b.tickCount % 20 == 0
            && sl.getNearestPlayer(b.getX(), b.getY(), b.getZ(), 48, p -> p instanceof ServerPlayer sp && !sp.isSpectator() && !sp.isCreative()) == null) {
            end(b, sl, "戦闘から離れた");
        }
    }

    static void tell(SupremeEntity b, ServerLevel sl, Component c) {
        for (ServerPlayer p : sl.players()) {
            if (p.distanceToSqr(b) < 96 * 96) {
                p.displayClientMessage(c, false);
            }
        }
    }

    static String whole(float f) {
        return String.format(Locale.ROOT, "%,d", Math.round(f));
    }

    // ------------------------------------------------------------------------------------------------- commands

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("raid").requires(s -> s.hasPermission(2))
            .then(Commands.literal("on").executes(c -> {
                enable(c.getSource().getServer(), true);
                c.getSource().sendSuccess(() -> Component.literal("神格のレイド戦: 有効"), true);
                return 1;
            }))
            .then(Commands.literal("off").executes(c -> {
                enable(c.getSource().getServer(), false);
                c.getSource().sendSuccess(() -> Component.literal("神格のレイド戦: 無効（ロアの通常状態のみ）"), true);
                return 1;
            }))
            .then(Commands.literal("status").executes(c -> {
                c.getSource().sendSuccess(() -> Component.literal("神格のレイド戦: " + (enabled ? "有効" : "無効")
                    + String.format(Locale.ROOT, "（開始 %d / 終了 %d / ブレイク %d / 再臨 %d / 討伐 %d）", started, ended, broken, revived, slain)), false);
                return 1;
            }))));
    }
}
