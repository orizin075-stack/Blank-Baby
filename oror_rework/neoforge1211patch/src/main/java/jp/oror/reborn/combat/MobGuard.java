package jp.oror.reborn.combat;

import java.util.HashMap;
import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.ItemAbilities;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (052) OROR's guard and parry, for every mob. The royals have always guarded so (RoyalMob.defend): when an enemy comes
 * within five blocks the guard goes up for half a second, every so often; a blow from the front in its first three
 * ticks is parried (the blow undone, a twentieth of its weight taken from the guard's stamina), later in the window it
 * is blocked (three tenths), and a guard without the stamina for a blow breaks, the mob staggering for a second. Mobs
 * of Epic Fight's Combat Evolution and Indestructible keep their own guard; every other mob (the vanilla ones, other
 * mods', OROR's characters) now guards by the royals' rules, scaled to what it is:
 * <ul>
 * <li>a boss (OROR's characters, the bosses' tag: not health, which the pack's mob levels raise) raises its guard every 1.8 seconds,
 * with a deeper stamina, and turns arrows aside as well;</li>
 * <li>an armed mob (a weapon or a shield in hand) every 2.5 seconds; it parries arrows with a blade, and blocks them
 * with a shield;</li>
 * <li>a bare-handed mob every 3.5 seconds, a shorter window, and only parries; its block halves a blow.</li>
 * </ul>
 * A mob struck while its guard is down raises it again in half the time, reading the rhythm of the blows. A parried attacker is
 * thrown back and staggered (Epic Fight's long stun where it has one), which is also what a player's own parry (Epic
 * Fight's) now does to any mob, not only to Indestructible's (NightfallNativeParryFeedbackMixin). The guard is seen:
 * an Epic Fight humanoid plays its guard and parry animations, OROR's characters and the royals their own poses
 * (TechniqueShow), every mob strikes sparks and rings.
 * <p>
 * (053) Mobs looked wrong with it (the user: wither skeletons and others): it worked between mobs too (a golem and a
 * zombie, the royals and the mobs, mobs in a brawl) and Epic Fight's long stun froze whoever was parried, every block
 * played Epic Fight's guard animation (a mob stands in it), a broken guard its two-second "neutralised" one, archers
 * raised a guard. Now a mob guards only against players' blows; a parried mob is stunned briefly (Epic Fight's short
 * stun); a block shows only the sparks and the pose on OROR's rigs, a parry and a broken guard Epic Fight's short guard
 * hit; a mob with a bow or a crossbow does not guard, nor one with a gun (the user: the mobs carry guns too); a block
 * without a shield halves a blow instead of undoing it.
 * <p>
 * (059e) The user: "敵も味方もパリイシステム使わない". Parries had become too rare to see: a guard parried only in its
 * first three ticks, and only players' blows were met. Now a mob guards against any foe in reach (the kingdom's soldiers
 * and the mobs they fight, a player or not), the first half of its guard parries, and the royals parry likewise
 * (RoyalGuardTimingMixin); the Indestructible mobs keep their own guard and parry whole again
 * (NightfallEnemyParryWindowMixin, which cut their parry to the guard's first six ticks, is no longer applied). On a
 * dedicated server Epic Fight is now read one method at a time, so its patches are found there too.
 * <p>
 * (059e, later) The user: "すべてのモブがパリイを使えるように あときちんとモーションを モブのモーションが機能してなかった".
 * Every mob that fights now guards: the monsters, the villagers and the golems, wolves and whatever else strikes (an
 * attack of its own); one with a bow, a crossbow or a gun raises its guard when its foe comes to arm's reach, and meets
 * blows only, not shots; a villager with no target guards against whoever struck it last. The mobs of Combat Evolution
 * and Indestructible guard by these rules too whenever their own guard is down (their own, when up, takes the blow as
 * before). The guard is seen on every mob: its raising is told to the players (TechniqueShow "guard") with each moment,
 * and GuardPoses draws them all on Minecraft's models (they were drawn only on OROR's characters and the royals); an
 * Epic Fight humanoid plays Epic Fight's guard hit on a block as on a parry. A mob without the AI (a statue, a test's
 * target) does not guard.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class MobGuard {
    private MobGuard() {
    }

    enum Tier {
        BOSS(36, 8, 160F), ARMED(50, 10, 80F), BARE(70, 6, 50F);

        final int cycle, window;
        final float stamina;

        Tier(int cycle, int window, float stamina) {
            this.cycle = cycle;
            this.window = window;
            this.stamina = stamina;
        }
    }

    /** A mob's guard: the window its guard is up in, its age, the wait before the next, its stamina and stagger. */
    static final class Guard {
        int remaining, age, delay = 20, stagger;
        float stamina = -1F;
    }

    private static final Map<LivingEntity, Guard> GUARDS = new WeakHashMap<>();
    /** Mob types whose Epic Fight patch guards on its own (Combat Evolution, Indestructible). */
    private static final Map<EntityType<?>, Boolean> NATIVE = new HashMap<>();

    /**
     * Whether a mob guards by these rules: (059e) every mob that fights (not players, nor the royals, who guard by
     * their own hand, nor a mob without its AI). The mobs of the guarding mods do too, while their own guard is down.
     */
    public static boolean guards(LivingEntity e) {
        return e instanceof Mob m && !(m instanceof RoyalMob) && m.isAlive() && !m.isNoAi() && fighter(m);
    }

    /** A mob that fights: a monster, a villager, a golem, a mob that turns on whoever wrongs it, or any with an attack. */
    static boolean fighter(Mob m) {
        return m instanceof net.minecraft.world.entity.monster.Enemy || m instanceof net.minecraft.world.entity.npc.AbstractVillager
            || m instanceof net.minecraft.world.entity.animal.AbstractGolem || m instanceof net.minecraft.world.entity.NeutralMob
            || m.getAttributes().hasAttribute(Attributes.ATTACK_DAMAGE);
    }

    /** A mob that shoots (a bow, a crossbow, a gun): it guards only at arm's reach, and only against blows. */
    static boolean ranged(Mob m) {
        ItemStack main = m.getMainHandItem();
        return main.getItem() instanceof net.minecraft.world.item.ProjectileWeaponItem || Guns.held(main);
    }

    /** Whether the mob's own mod (Combat Evolution, Indestructible) guards it: then its own guard, while up, takes the blow. */
    static boolean nativeMob(Mob m) {
        Boolean known = NATIVE.get(m.getType());
        if (known == null) {
            String patch = ModList.get().isLoaded("epicfight") ? Ef.patchClass(m) : "";
            if (patch == null) {
                return false;
            }
            known = patch.contains("combat_evolution") || patch.contains("indestructible") || patch.contains("combatevolution");
            NATIVE.put(m.getType(), known);
        }
        return known;
    }

    /** A guarding mod's own guard up now (its patch blocking, or a shield raised the vanilla way). */
    static boolean nativeGuardUp(Mob m) {
        return m.isBlocking() || nativeMob(m) && Ef.blocking(m);
    }

    /** The foe a mob guards against: its target, or (one with none, a villager) whoever struck it in the last five seconds. */
    static LivingEntity foe(Mob m) {
        LivingEntity t = m.getTarget();
        if (t == null || !t.isAlive()) {
            LivingEntity last = m.getLastHurtByMob();
            t = last != null && last.isAlive() && m.tickCount - m.getLastHurtByMobTimestamp() < 100 ? last : null;
        }
        return t;
    }

    static Tier tier(Mob m) {
        if (m instanceof SupremeEntity || m.getType().is(Tags.EntityTypes.BOSSES)) {
            return Tier.BOSS;
        }
        ItemStack main = m.getMainHandItem();
        if (shield(m) || !main.isEmpty() && (main.canPerformAction(ItemAbilities.SWORD_SWEEP) || main.canPerformAction(ItemAbilities.AXE_DIG)
            || armed(m, main))) {
            return Tier.ARMED;
        }
        return Tier.BARE;
    }

    private static boolean armed(Mob m, ItemStack main) {
        double[] dmg = {0};
        main.forEachModifier(EquipmentSlot.MAINHAND, (attribute, modifier) -> {
            if (attribute.value() == Attributes.ATTACK_DAMAGE.value()) {
                dmg[0] += modifier.amount();
            }
        });
        return dmg[0] >= 2;
    }

    static boolean shield(LivingEntity m) {
        return m.getOffhandItem().canPerformAction(ItemAbilities.SHIELD_BLOCK) || m.getMainHandItem().canPerformAction(ItemAbilities.SHIELD_BLOCK);
    }

    private static Guard guard(Mob m) {
        Guard g = GUARDS.get(m);
        if (g == null) {
            g = new Guard();
            GUARDS.put(m, g);
        }
        if (g.stamina < 0) {
            g.stamina = tier(m).stamina;
        }
        return g;
    }

    // ------------------------------------------------------------------------------------------------ raising the guard

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob m) || m.level().isClientSide) {
            return;
        }
        if (m instanceof RoyalMob r) {
            royalRaised(r);
            return;
        }
        Guard g = GUARDS.get(m);
        LivingEntity t = foe(m);
        if (g == null && t == null) {
            return;
        }
        if (!guards(m)) {
            return;
        }
        g = guard(m);
        if (g.stagger > 0) {
            // staggered: the guard stays down (the mob was stopped once, when it staggered)
            g.stagger--;
            g.remaining = 0;
            return;
        }
        if (g.remaining > 0) {
            g.remaining--;
            g.age++;
            g.stamina = Math.max(0F, g.stamina - 0.08F);
            return;
        }
        if (g.delay > 0) {
            g.delay--;
        }
        // (059e, the user: "敵も味方もパリイシステム使わない") against any foe in reach, a player or a mob: the kingdom's
        // soldiers and the mobs they fight guard and parry each other too (053 had it for players' blows only)
        // (059e) one that shoots raises it only when its foe is at arm's reach; one whose own mod's guard is up leaves it to that
        if (g.delay == 0 && t != null && t.isAlive() && m.distanceToSqr(t) < (ranged(m) ? 12.25 : 25.0) && m.getSensing().hasLineOfSight(t)
            && !nativeGuardUp(m)) {
            Tier tier = tier(m);
            g.stamina = Math.min(tier.stamina, g.stamina + 0.4F * tier.cycle);
            g.remaining = tier.window;
            g.age = 0;
            g.delay = tier.cycle;
            // (059e) the guard seen going up (GuardPoses; (059f) OROR's characters too, on their own rigs: CharacterModel
            // leaves it out while a technique of theirs is under way)
            TechniqueShow.send(m, "guard", 0, 1, tier.window + 2, t.getId());
            count(m, "OrorGuardShown");
        }
    }

    private static final Map<RoyalMob, Long> ROYAL_RAISED = new WeakHashMap<>();

    /** (059f) A royal's own guard (RoyalMob.defend's timer) just raised: shown on its rig, as every other mob's is. */
    private static void royalRaised(RoyalMob r) {
        if (!(((Object) r) instanceof jp.oror.reborn.mixin.RoyalGuardAccess a)) {
            return;
        }
        int remaining = a.oror$guardRemaining();
        if (remaining <= 0 || a.oror$guardAge() > 1) {
            return;
        }
        long now = r.level().getGameTime();
        Long last = ROYAL_RAISED.get(r);
        if (last != null && now - last < 5) {
            return;
        }
        ROYAL_RAISED.put(r, now);
        LivingEntity t = r.getTarget();
        TechniqueShow.send(r, "guard", 0, 1, remaining + 2, t == null ? -1 : t.getId());
        count(r, "OrorGuardShown");
    }

    // ---------------------------------------------------------------------------------------------- meeting the blow

    /** What a guard made of a blow: none (it lands), undone (parried or blocked whole), halved, or the guard broken. */
    public static final int NONE = 0, UNDONE = 1, HALVED = 2, BROKEN = 3;

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void hurt(LivingIncomingDamageEvent e) {
        LivingEntity self = e.getEntity();
        if (self.level().isClientSide || !(self instanceof Mob m) || self instanceof SupremeEntity) {
            // (059f) OROR's characters meet blows at the start of their own hurt (SupremeEntityGuardMixin): in their lore
            // their blows never reach this event (their soul's health takes them), so a god never parried (CI 27: 0/0)
            return;
        }
        int met = meet(m, e.getSource(), e.getAmount());
        if (met == UNDONE) {
            e.setCanceled(true);
        } else if (met == HALVED) {
            e.setAmount(e.getAmount() * 0.5F);
        }
    }

    /** (059f) A god's blow, at the start of its hurt: true when the guard undid it (the hurt then does nothing). */
    public static boolean meetGod(SupremeEntity god, DamageSource src, float amount) {
        return !god.level().isClientSide && meet(god, src, amount) == UNDONE;
    }

    /** A blow on a mob met by its guard: a parry, a block, its guard broken, or nothing (its effects and moments shown). */
    static int meet(Mob m, DamageSource src, float amount) {
        if (!(m.level() instanceof ServerLevel sl)) {
            return NONE;
        }
        if (!(src.getEntity() instanceof LivingEntity attacker) || attacker == m || unblockable(src)) {
            return NONE;
        }
        boolean projectile = src.getDirectEntity() instanceof Projectile;
        boolean melee = !projectile && src.getDirectEntity() == attacker;
        if (!melee && !projectile || !guards(m) || projectile && ranged(m) || nativeGuardUp(m)) {
            return NONE;
        }
        // (058) a relic's art or technique is no blow a guard can take, nor is any blow on a guard a technique broke
        // or a seal undid, while that lasts
        long now = sl.getGameTime();
        if (jp.oror.reborn.RelicArts.busy() || m.getPersistentData().getLong("ororSealUntil") > now
            || m.getPersistentData().getLong("ororGuardBrokenUntil") > now) {
            return NONE;
        }
        Guard g = guard(m);
        if (g.remaining <= 0 || g.stagger > 0) {
            // struck with the guard down: it goes up again sooner, for a later blow of the combo
            if (melee && g.stagger <= 0) {
                g.delay = Math.min(g.delay, tier(m).cycle / 2);
            }
            return NONE;
        }
        Vec3 from = src.getSourcePosition();
        if (from == null) {
            return NONE;
        }
        Vec3 to = from.subtract(m.position()).multiply(1, 0, 1);
        Vec3 facing = m.getLookAngle().multiply(1, 0, 1);
        if (to.lengthSqr() < 1.0E-6 || facing.lengthSqr() < 1.0E-6 || to.normalize().dot(facing.normalize()) < 0.2) {
            return NONE;
        }
        Tier tier = tier(m);
        // (059e) the first half of the guard parries (it was its first three ticks: parries were rare enough to go unseen)
        boolean perfect = g.age <= tier.window / 2;
        if (projectile && !(tier == Tier.BOSS || shield(m) || perfect && tier == Tier.ARMED)) {
            return NONE;
        }
        float cost = Math.max(1F, amount * (perfect ? 0.05F : 0.3F));
        if (g.stamina < cost) {
            // the guard breaks under the blow: the blow lands, and the mob staggers
            g.stamina = 0F;
            g.remaining = 0;
            g.stagger = 20;
            m.getNavigation().stop();
            count(m, "OrorGuardBreaks");
            effects(sl, m, "break", m.getEyePosition().add(0, -0.3, 0), true);
            show(m, "break", 22, attacker);
            return BROKEN;
        }
        g.stamina -= cost;
        Vec3 contact = m.getEyePosition().lerp(from.add(0, attacker.getBbHeight() * 0.6, 0), 0.35);
        if (perfect) {
            count(m, "OrorParries");
            effects(sl, m, "parry", contact, true);
            show(m, "parry", 14, attacker);
            if (melee) {
                parried(attacker, m.position());
            }
            return UNDONE;
        }
        boolean whole = tier == Tier.BOSS || shield(m);
        count(m, "OrorBlocks");
        effects(sl, m, "block", contact, true);
        // (059e) Epic Fight's short guard hit only where the blow is undone: a halved blow plays its own hit (053: a
        // guard hit on every block left mobs standing in it through a brawl)
        show(m, whole ? "block" : "block_soft", 12, attacker);
        return whole ? UNDONE : HALVED;
    }

    /**
     * (059f) A guard's moment heard and seen where the blow met it (contact), the same for every mob, the royals and
     * OROR's characters included (the user: "パリイの時のエフェクトも確認"):
     * <ul>
     * <li>a parry: a bright flash and a ring of steel (the anvil's clang, high), a spray of crits thrown off the blade,
     * a few sparks and the sweep of the deflecting edge;</li>
     * <li>a block: the shield's knock, a burst of sparks, a little dust knocked off;</li>
     * <li>a broken guard: the shield's crack, crits flung all about, a puff of smoke.</li>
     * </ul>
     */
    static void effects(ServerLevel sl, LivingEntity m, String kind, Vec3 contact, boolean sound) {
        switch (kind) {
            case "parry" -> {
                if (sound) {
                    sl.playSound(null, m.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.5F, 1.8F);
                    sl.playSound(null, m.blockPosition(), SoundEvents.TRIDENT_HIT, SoundSource.HOSTILE, 0.7F, 1.4F);
                }
                sl.sendParticles(ParticleTypes.FLASH, contact.x, contact.y, contact.z, 1, 0, 0, 0, 0);
                sl.sendParticles(ParticleTypes.CRIT, contact.x, contact.y, contact.z, 14, 0.2, 0.2, 0.2, 0.35);
                sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, contact.x, contact.y, contact.z, 8, 0.15, 0.15, 0.15, 0.25);
                sl.sendParticles(ParticleTypes.SWEEP_ATTACK, contact.x, contact.y, contact.z, 1, 0, 0, 0, 0);
            }
            case "block" -> {
                if (sound) {
                    sl.playSound(null, m.blockPosition(), SoundEvents.SHIELD_BLOCK, SoundSource.HOSTILE, 0.6F, 1.0F);
                }
                sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, contact.x, contact.y, contact.z, 10, 0.25, 0.2, 0.25, 0.08);
                sl.sendParticles(ParticleTypes.CRIT, contact.x, contact.y, contact.z, 4, 0.15, 0.15, 0.15, 0.1);
                sl.sendParticles(ParticleTypes.POOF, contact.x, contact.y - 0.2, contact.z, 2, 0.1, 0.05, 0.1, 0.01);
            }
            case "break" -> {
                if (sound) {
                    sl.playSound(null, m.blockPosition(), SoundEvents.SHIELD_BREAK, SoundSource.HOSTILE, 0.8F, 0.9F);
                }
                sl.sendParticles(ParticleTypes.CRIT, contact.x, contact.y, contact.z, 18, 0.35, 0.3, 0.35, 0.2);
                sl.sendParticles(ParticleTypes.POOF, contact.x, contact.y, contact.z, 6, 0.3, 0.2, 0.3, 0.02);
            }
            default -> {
            }
        }
    }

    /** Where a blow met a mob's guard: between its eyes and its foe's chest, or a little before its face. */
    static Vec3 contact(LivingEntity m, LivingEntity other) {
        if (other != null) {
            return m.getEyePosition().lerp(other.position().add(0, other.getBbHeight() * 0.6, 0), 0.35);
        }
        Vec3 look = m.getLookAngle().multiply(1, 0, 1);
        look = look.lengthSqr() < 1.0E-6 ? Vec3.ZERO : look.normalize();
        return m.getEyePosition().add(look.scale(Math.max(0.6, m.getBbWidth() * 0.7))).add(0, -0.2, 0);
    }

    /**
     * The royals guard by their own hand (RoyalMob.defend, at the highest priority): what it parried or blocked is
     * seen here afterwards, shown on their rig, and a parried attacker is thrown back as by any other guard.
     */
    @SubscribeEvent(priority = EventPriority.LOWEST, receiveCanceled = true)
    public static void royal(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof RoyalMob r) || r.level().isClientSide) {
            return;
        }
        CompoundTag d = r.getPersistentData();
        int parries = d.getInt("RoyalParries"), blocks = d.getInt("RoyalBlocks");
        LivingEntity attacker = e.getSource().getEntity() instanceof LivingEntity l ? l : null;
        if (parries > d.getInt("OrorShownParries")) {
            d.putInt("OrorShownParries", parries);
            if (r.level() instanceof ServerLevel sl) {
                effects(sl, r, "parry", contact(r, attacker), false);
            }
            TechniqueShow.send(r, "parry", 0, 1, 14, attacker == null ? -1 : attacker.getId());
            if (attacker != null && attacker != r && e.getSource().getDirectEntity() == attacker) {
                parried(attacker, r.position());
            }
        } else if (blocks > d.getInt("OrorShownBlocks")) {
            d.putInt("OrorShownBlocks", blocks);
            if (r.level() instanceof ServerLevel sl) {
                effects(sl, r, "block", contact(r, attacker), false);
            }
            TechniqueShow.send(r, "block", 0, 1, 12, attacker == null ? -1 : attacker.getId());
        }
    }

    private static boolean unblockable(DamageSource src) {
        return src.is(DamageTypeTags.BYPASSES_INVULNERABILITY) || src.is(DamageTypeTags.IS_EXPLOSION) || src.is(DamageTypeTags.IS_FIRE)
            || src.is(DamageTypes.MAGIC) || src.is(DamageTypes.INDIRECT_MAGIC) || src.is(DamageTypes.THORNS) || src.is(DamageTypes.SONIC_BOOM)
            || src.typeHolder().unwrapKey().map(k -> k.location().getNamespace().equals("irons_spellbooks")).orElse(false);
    }

    private static void count(LivingEntity m, String key) {
        CompoundTag d = m.getPersistentData();
        d.putInt(key, d.getInt(key) + 1);
    }

    /**
     * The guard's moment, seen: Epic Fight's animation on its humanoids, the pose on OROR's own rigs and (059e) on every
     * other mob Minecraft draws (GuardPoses).
     */
    private static void show(LivingEntity m, String kind, int length, LivingEntity other) {
        if (ModList.get().isLoaded("epicfight") && Ef.play(m, kind)) {
            count(m, "OrorGuardAnims");
        }
        TechniqueShow.send(m, kind.equals("block_soft") ? "block" : kind, 0, 1, length, other == null ? -1 : other.getId());
        count(m, "OrorGuardShown");
    }

    /**
     * An attacker parried, by a mob's guard or a player's: thrown back from where it was parried and staggered for
     * most of a second (Epic Fight's long stun on a mob it has a patch for; a mob's own guard down and its legs slowed
     * otherwise; a player only pushed back and slowed a moment).
     */
    public static void parried(LivingEntity attacker, Vec3 from) {
        if (attacker.level().isClientSide || !attacker.isAlive()) {
            return;
        }
        CompoundTag d = attacker.getPersistentData();
        long now = attacker.level().getGameTime();
        if (now - d.getLong("OrorParriedAt") < 4) {
            return;
        }
        d.putLong("OrorParriedAt", now);
        double dx = from.x - attacker.getX(), dz = from.z - attacker.getZ();
        if (dx * dx + dz * dz < 1.0E-4) {
            Vec3 look = attacker.getLookAngle();
            dx = look.x;
            dz = look.z;
        }
        attacker.knockback(attacker instanceof Player ? 0.45 : 0.7, dx, dz);
        attacker.hurtMarked = true;
        count(attacker, "OrorParried");
        if (attacker instanceof Player p) {
            p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 10, 1, false, false, true));
            return;
        }
        if (attacker instanceof Mob mob) {
            mob.getNavigation().stop();
            if (guards(mob)) {
                Guard g = guard(mob);
                g.stagger = Math.max(g.stagger, 16);
            }
        }
        boolean stunned = ModList.get().isLoaded("epicfight") && Ef.stun(attacker);
        if (!stunned) {
            attacker.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 16, 4, false, false, false));
            attacker.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 16, 2, false, false, false));
        } else {
            // (059e) Epic Fight's stun stops the mob dead and cancels its knockback (CI 24: "push 0.00"): the throw back
            // given again after it, as a velocity of its own
            double len = Math.sqrt(dx * dx + dz * dz);
            if (len > 1.0E-4) {
                attacker.setDeltaMovement(-dx / len * 0.55, attacker.onGround() ? 0.22 : attacker.getDeltaMovement().y, -dz / len * 0.55);
                attacker.hurtMarked = true;
            }
        }
        TechniqueShow.send(attacker, "parried", 0, 1, 18, -1);
    }

    /**
     * (059e) A guard's moment shown on a mob as a real one is (Epic Fight's animation where it animates the mob, the pose
     * on Minecraft's models and OROR's rigs), without a blow: for the look client's guard scene.
     */
    public static boolean demo(LivingEntity m, String kind, int length) {
        boolean ef = ModList.get().isLoaded("epicfight") && Ef.play(m, kind);
        TechniqueShow.send(m, kind, 0, 1, length, -1);
        if (m.level() instanceof ServerLevel sl) {
            effects(sl, m, kind, kind.equals("break") ? m.getEyePosition().add(0, -0.3, 0) : contact(m, null), true);
        }
        return ef;
    }

    /** How a mob guards (for the checks): by these rules and its tier, or by its own mod's guard (its patch). */
    public static String describe(Mob m) {
        if (m instanceof RoyalMob) {
            return "royal";
        }
        String patch = ModList.get().isLoaded("epicfight") ? Ef.patchClass(m) : "";
        patch = patch == null ? "?" : patch.isEmpty() ? "no patch" : patch.substring(patch.lastIndexOf('.') + 1);
        return (guards(m) ? (nativeMob(m) ? "native+oror " : "oror ") + tier(m).name().toLowerCase(java.util.Locale.ROOT)
            + (ranged(m) ? " ranged" : "") : "none") + " [" + patch + "]";
    }

    /** What a mob has guarded (for the checks): parries, blocks, broken guards, and times it was parried. */
    public static String tally(LivingEntity m) {
        CompoundTag d = m.getPersistentData();
        if (m instanceof RoyalMob) {
            // (059f) a royal counts its own (RoyalMob.defend)
            return d.getInt("RoyalParries") + "/" + d.getInt("RoyalBlocks") + "/-/" + d.getInt("OrorParried");
        }
        return d.getInt("OrorParries") + "/" + d.getInt("OrorBlocks") + "/" + d.getInt("OrorGuardBreaks") + "/" + d.getInt("OrorParried");
    }

    /** (059e) How its guard was seen (for the checks): moments told to the players, Epic Fight animations played. */
    public static String motions(LivingEntity m) {
        CompoundTag d = m.getPersistentData();
        return "shown " + d.getInt("OrorGuardShown") + " ef " + d.getInt("OrorGuardAnims");
    }

    // ------------------------------------------------------------------------------------------------------- Epic Fight

    /** Epic Fight, reached by name, so that this works the same across its versions (and without it). */
    static final class Ef {
        // (059e) looked up one method at a time (MethodHandles): asking Epic Fight's classes for all their methods
        // (Class.getMethod, getMethods) loads every type they name, the client's among them, which a dedicated server
        // refuses; there every mob passed for one without a patch (the checks' "[no patch]") and no guard was animated
        private static java.lang.invoke.MethodHandle getPatch, play, stun;
        private static Class<?> humanoid, living, entityPatch;
        private static Object stunShort;
        private static final Map<String, Object> ANIMS = new HashMap<>();
        private static boolean looked, broken, playLooked;
        private static int alternate;

        private Ef() {
        }

        private static void look() {
            if (looked) {
                return;
            }
            looked = true;
            java.lang.invoke.MethodHandles.Lookup lk = java.lang.invoke.MethodHandles.publicLookup();
            try {
                Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
                living = Class.forName("yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch");
                entityPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.EntityPatch");
                humanoid = Class.forName("yesman.epicfight.world.capabilities.entitypatch.HumanoidMobPatch");
                for (Class<?> ret : new Class<?>[]{entityPatch, living, Object.class}) {
                    try {
                        getPatch = lk.findStatic(caps, "getEntityPatch",
                            java.lang.invoke.MethodType.methodType(ret, net.minecraft.world.entity.Entity.class, Class.class));
                        break;
                    } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                        // another erasure of its return
                    }
                }
                Class<?> stunType = Class.forName("yesman.epicfight.world.damagesource.StunType");
                for (Object c : stunType.getEnumConstants()) {
                    if (((Enum<?>) c).name().equals("SHORT")) {
                        stunShort = c;
                    }
                }
                for (Class<?> ret : new Class<?>[]{boolean.class, void.class}) {
                    try {
                        stun = lk.findVirtual(humanoid, "applyStun", java.lang.invoke.MethodType.methodType(ret, stunType, float.class));
                        break;
                    } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                        // the other return
                    }
                }
                Class<?> animations = Class.forName("yesman.epicfight.gameasset.Animations");
                for (String name : new String[]{"LONGSWORD_GUARD_ACTIVE_HIT1", "LONGSWORD_GUARD_ACTIVE_HIT2", "SWORD_GUARD_ACTIVE_HIT1",
                    "SWORD_GUARD_ACTIVE_HIT2", "SWORD_GUARD_HIT", "BIPED_HIT_SHIELD", "BIPED_COMMON_NEUTRALIZED"}) {
                    try {
                        ANIMS.put(name, lk.findStaticGetter(animations, name, animations.getField(name).getType()).invoke());
                    } catch (Throwable ex) {
                        // that animation is not in this version: its moment goes without it
                    }
                }
                broken = getPatch == null;
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                broken = true;
            }
        }

        /** playAnimationSynchronized(animation, float), its first parameter's type found from an animation itself. */
        private static java.lang.invoke.MethodHandle play(Object anim) {
            if (playLooked || anim == null) {
                return play;
            }
            playLooked = true;
            java.lang.invoke.MethodHandles.Lookup lk = java.lang.invoke.MethodHandles.publicLookup();
            java.util.ArrayDeque<Class<?>> todo = new java.util.ArrayDeque<>();
            java.util.Set<Class<?>> seen = new java.util.HashSet<>();
            todo.add(anim.getClass());
            while (!todo.isEmpty() && play == null) {
                Class<?> c = todo.poll();
                if (c == null || !seen.add(c)) {
                    continue;
                }
                try {
                    play = lk.findVirtual(living, "playAnimationSynchronized", java.lang.invoke.MethodType.methodType(void.class, c, float.class));
                } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                    // (059e) an interface's superclass (and Object's) is null, which an ArrayDeque refuses: the walk threw
                    // at the animation's first interface, before it reached AssetAccessor, and no guard was ever animated
                    // (CI 24: "ef 0" on every mob)
                    if (c.getSuperclass() != null) {
                        todo.add(c.getSuperclass());
                    }
                    todo.addAll(java.util.List.of(c.getInterfaces()));
                }
            }
            return play;
        }

        private static Object patch(LivingEntity e) throws Throwable {
            look();
            if (broken || getPatch == null || living == null) {
                return null;
            }
            Object p = getPatch.invoke(e, living);
            return living.isInstance(p) ? p : null;
        }

        /** The class of a mob's Epic Fight patch ("" without one, null if it may not have been given one yet). */
        static String patchClass(Mob m) {
            try {
                Object p = patch(m);
                if (p == null) {
                    return m.tickCount > 40 ? "" : null;
                }
                return p.getClass().getName();
            } catch (Throwable ex) {
                return "";
            }
        }

        /** Plays the moment's animation on an Epic Fight humanoid; whether one was played. */
        static boolean play(LivingEntity m, String kind) {
            try {
                Object p = patch(m);
                if (p == null || !humanoid.isInstance(p)) {
                    return false;
                }
                boolean shield = shield(m);
                String[] parries = {"SWORD_GUARD_ACTIVE_HIT1", "LONGSWORD_GUARD_ACTIVE_HIT1", "SWORD_GUARD_ACTIVE_HIT2", "LONGSWORD_GUARD_ACTIVE_HIT2"};
                Object anim = switch (kind) {
                    case "parry" -> shield && ANIMS.containsKey("BIPED_HIT_SHIELD") ? ANIMS.get("BIPED_HIT_SHIELD")
                        : ANIMS.getOrDefault(parries[alternate++ & 3], ANIMS.get("SWORD_GUARD_HIT"));
                    // (059e) a block too, as the blow it took would have been (Epic Fight's short guard hit, not its guard stance)
                    case "block" -> shield && ANIMS.containsKey("BIPED_HIT_SHIELD") ? ANIMS.get("BIPED_HIT_SHIELD") : ANIMS.get("SWORD_GUARD_HIT");
                    case "break" -> ANIMS.get("SWORD_GUARD_HIT");
                    default -> null;
                };
                java.lang.invoke.MethodHandle h = play(anim);
                if (anim != null && h != null) {
                    h.invoke(p, anim, 0.0F);
                    return true;
                }
            } catch (Throwable ex) {
                // the moment goes unanimated
            }
            return false;
        }

        private static final Map<Class<?>, java.util.Optional<java.lang.invoke.MethodHandle>> BLOCKING = new HashMap<>();

        /** Whether a guarding mod's patch has its guard up (its isBlocking(), where it has one). */
        static boolean blocking(LivingEntity m) {
            try {
                Object p = patch(m);
                if (p == null) {
                    return false;
                }
                java.lang.invoke.MethodHandle h = BLOCKING.computeIfAbsent(p.getClass(), c -> {
                    try {
                        return java.util.Optional.of(java.lang.invoke.MethodHandles.publicLookup().findVirtual(c, "isBlocking",
                            java.lang.invoke.MethodType.methodType(boolean.class)));
                    } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                        return java.util.Optional.empty();
                    }
                }).orElse(null);
                return h != null && (boolean) h.invoke(p);
            } catch (Throwable ex) {
                return false;
            }
        }

        static boolean stun(LivingEntity m) {
            try {
                Object p = patch(m);
                if (p == null || stun == null || stunShort == null || !humanoid.isInstance(p)) {
                    return false;
                }
                stun.invoke(p, stunShort, 1.0F);
                return true;
            } catch (Throwable ex) {
                return false;
            }
        }
    }

    /** Debugging: the id of a mob type, for the checks' notes. */
    static String id(LivingEntity e) {
        return BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString();
    }
}
