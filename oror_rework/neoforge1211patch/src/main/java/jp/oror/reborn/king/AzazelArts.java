package jp.oror.reborn.king;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.AbstractGolem;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.AbstractIllager;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.EvokerFangs;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * (056) Azazel's own arts (the user: remake Azazel too). He stays an evoker (his fangs and his vexes are his still), and
 * now has ten of his own, each with its motion (KingMotions "azazel_*", drawn by AzazelRig): who he is in them —
 * the Watcher who taught men the forge, bound by Raphael in Dudael under rough stones, the one the scapegoat goes to.
 * <ul>
 * <li>叛神剣・三連: three cuts of the king-slayer blade before him.</li>
 * <li>鍛冶神の剣雨: the swords he taught men to forge fall on his foes (slowed).</li>
 * <li>牙の大陣: the blade driven into the ground: four rings of fangs go out from him.</li>
 * <li>蝕の羽ばたき: his charred wings beat: those before him blinded, darkened, thrown back.</li>
 * <li>贖罪の山羊: a foe made his scapegoat for twelve seconds: six tenths of every wound he takes goes to it.</li>
 * <li>荒野の岩: the jagged stones of Dudael fall on his foes, three waves (stunned).</li>
 * <li>禁断の知識: "who taught you the sword?": the weapon in his foe's hand torn away and thrown down.</li>
 * <li>堕天の急降下: up on his wings and down on his foe.</li>
 * <li>解かれた鎖: the chains he broke lash out: his foes hauled in and held, then the chains burst on them.</li>
 * <li>叛逆の号令: his rebels round him made strong and swift, three vexes more.</li>
 * </ul>
 * His blows are his (the source is him), so they break the villager king's field at once (RebelLord.slayer).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class AzazelArts {
    public static final String HITS = "OrorAzazelHits";
    static final String BUSY = "OrorAzazelBusy", NEXT = "OrorAzazelNext", CD = "OrorAzazelCd_";

    public record Art(String id, String name, int windup, int length, int every, double min, double max) {
    }

    public static final List<Art> ARTS = List.of(
        new Art("rend", "叛神剣・三連", 8, 30, 60, 0, 5),
        new Art("forge", "鍛冶神の剣雨", 14, 34, 180, 3, 20),
        new Art("fangs", "牙の大陣", 12, 28, 140, 0, 9),
        new Art("gust", "蝕の羽ばたき", 10, 22, 120, 0, 9),
        new Art("scapegoat", "贖罪の山羊", 10, 24, 400, 2, 16),
        new Art("dudael", "荒野の岩", 16, 40, 220, 4, 22),
        new Art("disarm", "禁断の知識", 10, 26, 300, 2, 10),
        new Art("dive", "堕天の急降下", 12, 34, 160, 6, 18),
        new Art("chains", "解かれた鎖", 14, 36, 240, 0, 12),
        new Art("rally", "叛逆の号令", 16, 30, 600, 0, 40));

    private record Goat(LivingEntity victim, long until) {
    }

    private static final Map<Mob, Goat> GOATS = new WeakHashMap<>();

    private AzazelArts() {
    }

    public static Art art(String id) {
        for (Art a : ARTS) {
            if (a.id.equals(id)) {
                return a;
            }
        }
        return null;
    }

    static boolean azazel(LivingEntity e) {
        return e instanceof Mob m && m.getPersistentData().getBoolean(RebelLord.LORD);
    }

    /** His foes: never the rebels nor their allies, never a friend of the rebels (unless he is a friend's likeness: then
     * never any player); always the king's people, his target, and whoever is set on him; the villagers and golems too
     * when he is the rebels' lord. */
    static boolean foe(Mob az, LivingEntity e) {
        if (e == az || !e.isAlive() || RebelPact.member(e) || e.getPersistentData().getBoolean(RebelPact.ALLY)) {
            return false;
        }
        if (e instanceof Vex v && v.getOwner() == az) {
            return false;
        }
        boolean likeness = az.getPersistentData().getBoolean(RebelPact.ALLY);
        if (e instanceof Player p) {
            return !likeness && !p.isCreative() && !p.isSpectator() && !RebelPact.friend(p);
        }
        if (e == az.getTarget() || e instanceof RoyalMob || e instanceof Mob m && m.getTarget() == az) {
            return true;
        }
        return !likeness && (e instanceof AbstractGolem || e instanceof AbstractVillager);
    }

    static List<LivingEntity> foes(Mob az, ServerLevel sl, double r) {
        return sl.getEntitiesOfClass(LivingEntity.class, az.getBoundingBox().inflate(r), e -> foe(az, e) && e.distanceTo(az) <= r);
    }

    static boolean hit(Mob az, String id, LivingEntity v, float amount, boolean magic) {
        if (!v.isAlive() || !az.isAlive()) {
            return false;
        }
        boolean landed = v.hurt(magic ? az.damageSources().indirectMagic(az, az) : az.damageSources().mobAttack(az), amount);
        if (landed) {
            count(az, id);
        }
        return landed;
    }

    static void count(Mob az, String id) {
        CompoundTag d = az.getPersistentData();
        CompoundTag h = d.getCompound(HITS);
        h.putInt(id, h.getInt(id) + 1);
        d.put(HITS, h);
    }

    static void say(ServerLevel sl, Mob az, String line) {
        for (ServerPlayer p : sl.players()) {
            if (p.distanceToSqr(az) < 48 * 48) {
                p.sendSystemMessage(Component.literal("アザゼル：" + line).withStyle(ChatFormatting.DARK_PURPLE));
            }
        }
    }

    // ------------------------------------------------------------------------------------------------ choosing

    /** Every quarter second: when he has a foe and is not at an art, one that fits the distance and is ready. */
    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (!(e.getEntity() instanceof Mob az) || !(az.level() instanceof ServerLevel sl) || az.tickCount % 5 != 0 || !azazel(az)
            || !az.isAlive() || az.isNoAi()) {
            return;
        }
        long now = sl.getGameTime();
        CompoundTag d = az.getPersistentData();
        LivingEntity t = az.getTarget();
        if (now < d.getLong(BUSY) || now < d.getLong(NEXT) || t == null || !t.isAlive() || !foe(az, t) || t.distanceTo(az) > 40) {
            return;
        }
        double dist = t.distanceTo(az);
        List<Art> ok = new ArrayList<>();
        for (Art a : ARTS) {
            if (dist >= a.min && dist <= a.max && now >= d.getLong(CD + a.id)) {
                ok.add(a);
            }
        }
        if (ok.isEmpty()) {
            return;
        }
        Art a = ok.get(sl.random.nextInt(ok.size()));
        d.putLong(CD + a.id, now + a.every);
        d.putLong(NEXT, now + a.length + 20 + sl.random.nextInt(30));
        perform(az, sl, a, t);
    }

    /** Does the art on his foe: its motion shown, its working after the windup. */
    public static void perform(Mob az, ServerLevel sl, Art a, LivingEntity t) {
        az.getPersistentData().putLong(BUSY, sl.getGameTime() + a.length);
        TechniqueShow.send(az, "move:azazel_" + a.id, 0, a.windup, a.length, t.getId());
        az.getLookControl().setLookAt(t, 60F, 60F);
        Vec3 c = az.position().add(0, az.getBbHeight() * 0.6, 0);
        sl.sendParticles(ParticleTypes.WITCH, c.x, c.y, c.z, 14, 0.6, 0.6, 0.6, 0.02);
        int w = a.windup;
        switch (a.id) {
            case "rend" -> KingDeeds.each(sl, w, 3, 6, k -> rend(az, sl, k));
            case "forge" -> KingDeeds.later(sl, w, () -> forge(az, sl));
            case "fangs" -> KingDeeds.later(sl, w, () -> fangs(az, sl));
            case "gust" -> KingDeeds.later(sl, w, () -> gust(az, sl));
            case "scapegoat" -> KingDeeds.later(sl, w, () -> scapegoat(az, sl, t));
            case "dudael" -> KingDeeds.each(sl, w, 3, 8, k -> dudael(az, sl));
            case "disarm" -> disarm(az, sl, t, w);
            case "dive" -> dive(az, sl, t, w);
            case "chains" -> chains(az, sl, w);
            case "rally" -> KingDeeds.later(sl, w, () -> rally(az, sl, t));
            default -> {
            }
        }
    }

    // ------------------------------------------------------------------------------------------------ the arts

    private static Vec3 facing(Mob az) {
        LivingEntity t = az.getTarget();
        Vec3 f = t != null ? t.position().subtract(az.position()) : Vec3.directionFromRotation(0, az.getYRot());
        f = new Vec3(f.x, 0, f.z);
        return f.lengthSqr() < 1.0E-4 ? new Vec3(0, 0, 1) : f.normalize();
    }

    private static void rend(Mob az, ServerLevel sl, int k) {
        if (!az.isAlive()) {
            return;
        }
        Vec3 f = facing(az);
        double reach = 4.5 + az.getBbWidth() * 0.5;
        for (LivingEntity v : foes(az, sl, reach + 1)) {
            Vec3 to = v.position().subtract(az.position());
            Vec3 flat = new Vec3(to.x, 0, to.z);
            if (flat.lengthSqr() < 1.0E-4 || flat.normalize().dot(f) > 0.4) {
                v.invulnerableTime = 0;
                hit(az, "rend", v, 14F, false);
            }
        }
        double side = k % 2 == 0 ? 1 : -1;
        for (int i = 0; i < 9; i++) {
            double ang = (i - 4) * 0.22 * side;
            Vec3 d = new Vec3(f.x * Math.cos(ang) - f.z * Math.sin(ang), 0, f.x * Math.sin(ang) + f.z * Math.cos(ang));
            Vec3 p = az.position().add(d.scale(reach * 0.8)).add(0, 1.2, 0);
            sl.sendParticles(ParticleTypes.FLAME, p.x, p.y, p.z, 2, 0.1, 0.1, 0.1, 0.01);
            sl.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, p.y, p.z, 1, 0, 0, 0, 0);
        }
        KingDeeds.sound(sl, az.position(), SoundEvents.PLAYER_ATTACK_SWEEP, 2F, 0.6F + k * 0.1F);
    }

    private static void forge(Mob az, ServerLevel sl) {
        List<LivingEntity> fs = foes(az, sl, 20);
        if (fs.size() > 6) {
            fs = fs.subList(0, 6);
        }
        say(sl, az, "我が鍛えし剣よ、降れ。");
        for (LivingEntity v : fs) {
            Vec3 at = v.position();
            for (int s = 0; s < 3; s++) {
                double ox = (sl.random.nextDouble() - 0.5) * 2.4, oz = (sl.random.nextDouble() - 0.5) * 2.4;
                KingDeeds.line(sl, ParticleTypes.CRIT, at.add(ox, 9, oz), at.add(ox, 0.2, oz), 0.5);
            }
            KingDeeds.later(sl, 6, () -> {
                if (v.isAlive()) {
                    sl.sendParticles(ParticleTypes.ENCHANTED_HIT, v.getX(), v.getY() + 1, v.getZ(), 30, 0.6, 0.8, 0.6, 0.2);
                    sl.sendParticles(ParticleTypes.LAVA, v.getX(), v.getY() + 0.5, v.getZ(), 6, 0.4, 0.2, 0.4, 0);
                    v.invulnerableTime = 0;
                    if (hit(az, "forge", v, 16F, true)) {
                        v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 1));
                    }
                    KingDeeds.sound(sl, v.position(), SoundEvents.ANVIL_LAND, 1.6F, 0.7F);
                }
            });
        }
    }

    private static void fangs(Mob az, ServerLevel sl) {
        double y = az.getY();
        float yaw = az.getYRot() * ((float) Math.PI / 180F);
        double[] radii = {2.5, 4.5, 6.5, 8.5};
        for (int ring = 0; ring < radii.length; ring++) {
            int n = (int) Math.ceil(2 * Math.PI * radii[ring] / 1.4);       // close enough that none slips between
            for (int i = 0; i < n; i++) {
                double a = i * Math.PI * 2 / n + ring * 0.3;
                double x = az.getX() + Math.cos(a) * radii[ring], z = az.getZ() + Math.sin(a) * radii[ring];
                BlockPos ground = BlockPos.containing(x, y + 1, z);
                for (int k = 0; k < 4 && sl.getBlockState(ground.below()).isAir(); k++) {
                    ground = ground.below();
                }
                sl.addFreshEntity(new EvokerFangs(sl, x, ground.getY(), z, (float) a + yaw, ring * 3, az));
            }
        }
        sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, az.getX(), az.getY() + 0.2, az.getZ(), 40, 2.0, 0.1, 2.0, 0.05);
        KingDeeds.sound(sl, az.position(), SoundEvents.EVOKER_FANGS_ATTACK, 3F, 0.6F);
    }

    /** His fangs' bites, for the record (the CI's). */
    @SubscribeEvent
    public static void bitten(LivingIncomingDamageEvent e) {
        if (e.getSource().getDirectEntity() instanceof EvokerFangs f && f.getOwner() instanceof Mob az && azazel(az) && !e.getEntity().level().isClientSide) {
            count(az, "fangs");
        }
    }

    private static void gust(Mob az, ServerLevel sl) {
        Vec3 f = facing(az);
        for (LivingEntity v : foes(az, sl, 10)) {
            Vec3 to = v.position().subtract(az.position());
            Vec3 flat = new Vec3(to.x, 0, to.z);
            if (flat.lengthSqr() > 1.0E-4 && flat.normalize().dot(f) < 0.35) {
                continue;
            }
            v.invulnerableTime = 0;
            hit(az, "gust", v, 8F, true);
            v.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0));
            v.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
            Vec3 away = flat.lengthSqr() > 1.0E-4 ? flat.normalize() : f;
            v.setDeltaMovement(v.getDeltaMovement().add(away.x * 2.0, 0.5, away.z * 2.0));
            v.hurtMarked = true;
        }
        for (int i = 0; i < 60; i++) {
            double ang = (sl.random.nextDouble() - 0.5) * 1.8, dist = 1 + sl.random.nextDouble() * 9;
            Vec3 d = new Vec3(f.x * Math.cos(ang) - f.z * Math.sin(ang), 0, f.x * Math.sin(ang) + f.z * Math.cos(ang));
            Vec3 p = az.position().add(d.scale(dist)).add(0, 0.5 + sl.random.nextDouble() * 2.5, 0);
            sl.sendParticles(i % 3 == 0 ? ParticleTypes.FLAME : ParticleTypes.LARGE_SMOKE, p.x, p.y, p.z, 1, 0, 0, 0, 0.02);
        }
        KingDeeds.sound(sl, az.position(), SoundEvents.ENDER_DRAGON_FLAP, 3F, 0.6F);
    }

    private static void scapegoat(Mob az, ServerLevel sl, LivingEntity t) {
        if (!t.isAlive() || !foe(az, t)) {
            return;
        }
        GOATS.put(az, new Goat(t, sl.getGameTime() + 240));
        count(az, "scapegoat");
        KingDeeds.line(sl, ParticleTypes.SOUL, az.getEyePosition(), t.getEyePosition(), 0.5);
        sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, t.getX(), t.getY() + t.getBbHeight() + 0.6, t.getZ(), 30, 0.3, 0.3, 0.3, 0.02);
        if (t instanceof ServerPlayer p) {
            p.displayClientMessage(Component.literal("贖罪の山羊：アザゼルの受ける傷の6割が、あなたに移る（12秒）").withStyle(ChatFormatting.DARK_PURPLE), true);
        }
        say(sl, az, "汝を我が山羊とする。我が罪を負え。");
        KingDeeds.sound(sl, t.position(), SoundEvents.GOAT_SCREAMING_AMBIENT, 2F, 0.6F);
    }

    /** The scapegoat bears six tenths of his wounds. */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void bears(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof Mob az) || az.level().isClientSide || !azazel(az) || GOATS.isEmpty()) {
            return;
        }
        Goat g = GOATS.get(az);
        if (g == null) {
            return;
        }
        if (az.level().getGameTime() > g.until || !g.victim.isAlive() || g.victim.distanceTo(az) > 32) {
            GOATS.remove(az);
            return;
        }
        float part = e.getAmount() * 0.6F;
        if (part <= 0F) {
            return;
        }
        e.setAmount(e.getAmount() - part);
        g.victim.invulnerableTime = 0;
        if (g.victim.hurt(az.damageSources().indirectMagic(az, az), part)) {
            count(az, "scapegoat_bore");
        }
        if (az.level() instanceof ServerLevel sl) {
            KingDeeds.line(sl, ParticleTypes.SOUL, az.position().add(0, 1.5, 0), g.victim.position().add(0, 1.2, 0), 0.7);
        }
    }

    private static void dudael(Mob az, ServerLevel sl) {
        BlockParticleOption stone = new BlockParticleOption(ParticleTypes.BLOCK, Blocks.BLACKSTONE.defaultBlockState());
        for (LivingEntity v : foes(az, sl, 22)) {
            for (int s = 0; s < 3; s++) {
                Vec3 at = v.position().add((sl.random.nextDouble() - 0.5) * 4, 0, (sl.random.nextDouble() - 0.5) * 4);
                KingDeeds.line(sl, stone, at.add(0, 9, 0), at.add(0, 0.3, 0), 0.6);
                sl.sendParticles(stone, at.x, at.y + 0.3, at.z, 30, 0.6, 0.3, 0.6, 0.1);
                sl.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 0.4, at.z, 6, 0.5, 0.2, 0.5, 0.02);
                if (v.position().distanceTo(at) < 1.8 || s == 0) {
                    v.invulnerableTime = 0;
                    if (hit(az, "dudael", v, 18F, false)) {
                        v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 30, 2));
                    }
                }
            }
            KingDeeds.sound(sl, v.position(), SoundEvents.BASALT_BREAK, 2.5F, 0.5F);
        }
    }

    private static void disarm(Mob az, ServerLevel sl, LivingEntity t, int w) {
        KingDeeds.later(sl, w, () -> {
            if (t.isAlive()) {
                KingDeeds.line(sl, ParticleTypes.WITCH, az.position().add(0, 1.5, 0), t.position().add(0, 1.2, 0), 0.4);
            }
        });
        KingDeeds.later(sl, w + 8, () -> {
            if (!az.isAlive() || !t.isAlive() || !foe(az, t) || t.distanceTo(az) > 14 || t instanceof RoyalMob r && KingCourt.isKing(r)) {
                return;
            }
            ItemStack held = t.getMainHandItem();
            if (held.isEmpty() || t instanceof Player p && p.isCreative()) {
                return;
            }
            ItemStack taken = held.copy();
            if (t instanceof Player p) {
                p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            } else if (t instanceof Mob m) {
                m.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
            }
            double a = sl.random.nextDouble() * Math.PI * 2;
            ItemEntity it = new ItemEntity(sl, t.getX(), t.getY() + 1.2, t.getZ(), taken, Math.cos(a) * 0.45, 0.45, Math.sin(a) * 0.45);
            it.setPickUpDelay(60);
            sl.addFreshEntity(it);
            count(az, "disarm");
            say(sl, az, "剣の作り方を教えたのは我だ。返してもらう。");
            sl.sendParticles(ParticleTypes.ENCHANT, t.getX(), t.getY() + 1.2, t.getZ(), 40, 0.4, 0.6, 0.4, 0.6);
            KingDeeds.sound(sl, t.position(), SoundEvents.ITEM_BREAK, 2F, 0.6F);
        });
    }

    private static void dive(Mob az, ServerLevel sl, LivingEntity t, int w) {
        KingDeeds.later(sl, w, () -> {
            if (!az.isAlive()) {
                return;
            }
            Vec3 to = t.position().subtract(az.position());
            Vec3 flat = new Vec3(to.x, 0, to.z);
            double d = flat.length();
            Vec3 dir = d > 1.0E-3 ? flat.scale(1 / d) : facing(az);
            az.setDeltaMovement(dir.x * Math.min(1.6, d * 0.11), 1.15, dir.z * Math.min(1.6, d * 0.11));
            az.hurtMarked = true;
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, az.getX(), az.getY() + 0.2, az.getZ(), 20, 0.6, 0.1, 0.6, 0.05);
            KingDeeds.sound(sl, az.position(), SoundEvents.ENDER_DRAGON_FLAP, 2.5F, 0.8F);
        });
        KingDeeds.later(sl, w + 14, () -> {
            if (!az.isAlive()) {
                return;
            }
            az.fallDistance = 0F;
            for (LivingEntity v : foes(az, sl, 4.5)) {
                v.invulnerableTime = 0;
                if (hit(az, "dive", v, 22F, false)) {
                    v.setDeltaMovement(v.getDeltaMovement().add(0, 0.6, 0));
                    v.hurtMarked = true;
                }
            }
            sl.sendParticles(ParticleTypes.EXPLOSION, az.getX(), az.getY() + 0.3, az.getZ(), 3, 1.0, 0.2, 1.0, 0);
            sl.sendParticles(ParticleTypes.FLAME, az.getX(), az.getY() + 0.3, az.getZ(), 40, 2.0, 0.2, 2.0, 0.08);
            KingDeeds.sound(sl, az.position(), SoundEvents.GENERIC_EXPLODE.value(), 2F, 0.7F);
        });
    }

    private static void chains(Mob az, ServerLevel sl, int w) {
        List<LivingEntity> held = new ArrayList<>();
        KingDeeds.later(sl, w, () -> {
            if (!az.isAlive()) {
                return;
            }
            say(sl, az, "ラファエルの鎖は、もはや我を縛らぬ。");
            for (LivingEntity v : foes(az, sl, 12)) {
                held.add(v);
                KingDeeds.line(sl, ParticleTypes.CRIT, az.position().add(0, 1.4, 0), v.position().add(0, 1.0, 0), 0.4);
                Vec3 in = az.position().subtract(v.position());
                Vec3 flat = new Vec3(in.x, 0, in.z);
                if (flat.lengthSqr() > 4) {
                    Vec3 pull = flat.normalize().scale(Math.min(1.4, flat.length() * 0.12));
                    v.setDeltaMovement(v.getDeltaMovement().add(pull.x, 0.25, pull.z));
                    v.hurtMarked = true;
                }
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 40, 3));
                count(az, "chains_bound");
            }
            KingDeeds.sound(sl, az.position(), SoundEvents.CHAIN_PLACE, 3F, 0.5F);
        });
        KingDeeds.later(sl, w + 16, () -> {
            if (!az.isAlive()) {
                return;
            }
            for (LivingEntity v : held) {
                if (v.isAlive() && v.distanceTo(az) < 18) {
                    sl.sendParticles(ParticleTypes.CRIT, v.getX(), v.getY() + 1, v.getZ(), 30, 0.5, 0.6, 0.5, 0.4);
                    v.invulnerableTime = 0;
                    hit(az, "chains", v, 14F, true);
                }
            }
            KingDeeds.sound(sl, az.position(), SoundEvents.CHAIN_BREAK, 3F, 0.6F);
        });
    }

    private static void rally(Mob az, ServerLevel sl, LivingEntity t) {
        say(sl, az, "叛け！ 神にも、王にも！");
        int raised = 0;
        for (Mob m : sl.getEntitiesOfClass(Mob.class, az.getBoundingBox().inflate(24), m -> m != az && m.isAlive()
            && (m instanceof AbstractIllager || m instanceof Vex v && v.getOwner() == az))) {
            m.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 400, 1));
            m.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 400, 0));
            m.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 400, 0));
            sl.sendParticles(ParticleTypes.ANGRY_VILLAGER, m.getX(), m.getY() + m.getBbHeight() + 0.3, m.getZ(), 3, 0.3, 0.2, 0.3, 0);
            raised++;
        }
        for (int i = 0; i < 3; i++) {
            Vex v = EntityType.VEX.create(sl);
            if (v == null) {
                continue;
            }
            double a = i * Math.PI * 2 / 3;
            v.moveTo(az.getX() + Math.cos(a) * 2, az.getY() + 2.2, az.getZ() + Math.sin(a) * 2, 0F, 0F);
            v.setOwner(az);
            v.setBoundOrigin(az.blockPosition());
            v.setLimitedLife(20 * 30);
            sl.addFreshEntity(v);
            if (t.isAlive()) {
                v.setTarget(t);
            }
        }
        count(az, "rally");
        az.getPersistentData().putInt("OrorAzazelRallied", raised);
        KingDeeds.sound(sl, az.position(), SoundEvents.RAID_HORN.value(), 4F, 0.8F);
    }
}
