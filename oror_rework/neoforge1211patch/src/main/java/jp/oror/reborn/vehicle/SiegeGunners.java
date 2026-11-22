package jp.oror.reborn.vehicle;

import com.atsuishio.superbwarfare.data.gun.GunData;
import com.atsuishio.superbwarfare.data.gun.GunProp;
import com.atsuishio.superbwarfare.data.gun.ShootParameters;
import java.util.List;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.raid.Raider;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r63, the user: "ドラゴン以外にもヒポグリフライダーとかもいたからそれも追加で そいつらは空飛びながら機関銃とかランチャーとか発射する感じで")
 * Azazel's hippogryph riders are a squadron: each hippogryph of the siege brings two wingmen, a pillager on each, and every
 * rider of a hippogryph or an amphithere carries a machine gun or a launcher (Superb Warfare) and fires it from the air at
 * the kingdom's people within {@value #RANGE} blocks, as the kingdom's own soldiers fire theirs (RoyalGuns: the gun's own
 * shot, its rate, its reload; ammunition without end). The dragons keep their fire and their bite.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class SiegeGunners {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Siege");
    static final String GUNNER = "OrorSiegeGunner", WINGMAN = "OrorSiegeWingman", DELAY = "OrorSiegeGunDelay", SHOTS = "OrorSiegeShots";
    static final int RANGE = 80, WINGMEN = 2;
    private static final List<String> MACHINE_GUNS = List.of("superbwarfare:minigun", "superbwarfare:m_60", "superbwarfare:rpk", "superbwarfare:ak_47");
    private static final List<String> LAUNCHERS = List.of("superbwarfare:rpg", "superbwarfare:m_79", "superbwarfare:javelin", "superbwarfare:m_60");

    private SiegeGunners() {
    }

    static boolean gunMount(Entity v) {
        if (!(v instanceof Mob m) || !m.getPersistentData().getBoolean(SiegeMounts.TAG)) {
            return false;
        }
        String id = BuiltInRegistries.ENTITY_TYPE.getKey(v.getType()).getPath();
        return id.equals("hippogryph") || id.equals("amphithere");
    }

    static Item first(List<String> ids) {
        for (String id : ids) {
            ResourceLocation k = ResourceLocation.tryParse(id);
            if (k != null && BuiltInRegistries.ITEM.containsKey(k)) {
                Item it = BuiltInRegistries.ITEM.get(k);
                if (it != Items.AIR && it instanceof com.atsuishio.superbwarfare.item.gun.GunItem) {
                    return it;
                }
            }
        }
        return null;
    }

    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        Entity self = e.getEntity();
        if (self.level().isClientSide() || !(self.level() instanceof ServerLevel level)) {
            return;
        }
        // a hippogryph of the siege, the first time it is seen, calls its wingmen
        if (self instanceof Mob mount && mount.isAlive() && mount.getPersistentData().getBoolean(SiegeMounts.TAG)
            && BuiltInRegistries.ENTITY_TYPE.getKey(mount.getType()).getPath().equals("hippogryph")
            && !mount.getPersistentData().getBoolean(WINGMAN) && !mount.getPersistentData().getBoolean("OrorSiegeCalled")) {
            mount.getPersistentData().putBoolean("OrorSiegeCalled", true);
            wingmen(level, mount);
        }
        if (!(self instanceof Raider rider) || !rider.isAlive() || !gunMount(rider.getVehicle())) {
            return;
        }
        Mob mount = (Mob) rider.getVehicle();
        var data = rider.getPersistentData();
        if (!data.getBoolean(GUNNER)) {
            data.putBoolean(GUNNER, true);
            // every other gunner a launcher
            boolean launcher = (rider.getUUID().getLeastSignificantBits() & 1) == 0;
            Item gun = first(launcher ? LAUNCHERS : MACHINE_GUNS);
            if (gun == null) {
                gun = first(MACHINE_GUNS);
            }
            if (gun != null) {
                rider.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(gun));
                rider.setDropChance(net.minecraft.world.entity.EquipmentSlot.MAINHAND, 0F);
            }
            LOG.info("SIEGE-GUNNER {\"rider\":\"{}\",\"mount\":\"{}\",\"gun\":\"{}\"}", BuiltInRegistries.ENTITY_TYPE.getKey(rider.getType()).getPath(),
                BuiltInRegistries.ENTITY_TYPE.getKey(mount.getType()).getPath(), gun == null ? "none" : BuiltInRegistries.ITEM.getKey(gun));
        }
        ItemStack held = rider.getMainHandItem();
        if (!(held.getItem() instanceof com.atsuishio.superbwarfare.item.gun.GunItem)) {
            return;
        }
        try {
            fire(level, rider, mount, held);
        } catch (Throwable t) {
            if (!data.getBoolean("OrorSiegeGunFailed")) {
                data.putBoolean("OrorSiegeGunFailed", true);
                LOG.warn("SIEGE-GUNNER failed", t);
            }
        }
    }

    private static void fire(ServerLevel level, Raider rider, Mob mount, ItemStack held) {
        GunData gun = GunData.from(held);
        gun.tick(rider, true);
        if (gun.virtualAmmo.get() < 100) {
            gun.virtualAmmo.set(12000);
        }
        if (gun.shouldStartReloading(rider)) {
            gun.startReload();
        }
        if (gun.shouldStartBolt()) {
            gun.startBolt();
        }
        var data = rider.getPersistentData();
        int delay = data.getInt(DELAY);
        if (delay > 0) {
            data.putInt(DELAY, delay - 1);
            return;
        }
        LivingEntity target = target(level, rider, mount);
        if (target == null || !gun.canShoot(rider)) {
            return;
        }
        // not into the siege's own: no shot at a target with an illager of the siege beside it
        if (!level.getEntitiesOfClass(Raider.class, target.getBoundingBox().inflate(3), x -> x != rider && x.isAlive()).isEmpty()) {
            return;
        }
        Vec3 from = rider.getEyePosition();
        Vec3 aim = target.getEyePosition().add(target.getDeltaMovement().scale(4));
        Vec3 dir = aim.subtract(from).normalize();
        rider.lookAt(target, 180F, 180F);
        gun.shoot(new ShootParameters(rider, rider, level, from, dir, gun, 1.5, true, target.getUUID(), aim));
        int rpm = Math.max(1, (Integer) gun.get(GunProp.RPM));
        data.putInt(DELAY, Math.max(1, (int) Math.ceil(1200.0 / rpm)));
        data.putInt(SHOTS, data.getInt(SHOTS) + 1);
        // the squadron's tally, for the siege test
        mount.getPersistentData().putInt(SHOTS, mount.getPersistentData().getInt(SHOTS) + 1);
    }

    /** The mount's or the rider's target; else the nearest of the kingdom's people in range that the rider can see. */
    static LivingEntity target(ServerLevel level, Raider rider, Mob mount) {
        LivingEntity t = SiegeMounts.target(mount);
        if (t == null && rider.getTarget() != null && rider.getTarget().isAlive()) {
            t = rider.getTarget();
        }
        if (t != null && t.isAlive() && t.distanceTo(rider) <= RANGE && rider.hasLineOfSight(t)) {
            return t;
        }
        LivingEntity best = null;
        double bd = RANGE * RANGE;
        for (LivingEntity c : level.getEntitiesOfClass(LivingEntity.class, new AABB(rider.blockPosition()).inflate(RANGE),
            x -> x.isAlive() && (x instanceof jp.oror.reborn.royal.RoyalMob || x instanceof net.minecraft.world.entity.animal.IronGolem))) {
            double d = c.distanceToSqr(rider);
            if (d < bd && rider.hasLineOfSight(c)) {
                best = c;
                bd = d;
            }
        }
        return best;
    }

    private static void wingmen(ServerLevel level, Mob lead) {
        EntityType<?> type = lead.getType();
        int made = 0;
        for (int i = 0; i < WINGMEN; i++) {
            Entity w = type.create(level);
            Entity p = EntityType.PILLAGER.create(level);
            if (!(w instanceof Mob wing) || !(p instanceof Mob pil)) {
                continue;
            }
            double side = i == 0 ? -6 : 6;
            float yaw = lead.getYRot() * ((float) Math.PI / 180F);
            double x = lead.getX() + Math.cos(yaw) * side - Math.sin(yaw) * -4, z = lead.getZ() + Math.sin(yaw) * side + Math.cos(yaw) * -4;
            wing.moveTo(x, lead.getY() + 1, z, lead.getYRot(), 0F);
            var wd = wing.getPersistentData();
            wd.putBoolean(SiegeMounts.TAG, true);
            wd.putBoolean(WINGMAN, true);
            wd.putBoolean("OrorAzazelCapitalSiege", true);
            pil.moveTo(x, lead.getY() + 2, z, lead.getYRot(), 0F);
            pil.getPersistentData().putBoolean("OrorAzazelCapitalSiege", true);
            pil.setPersistenceRequired();
            wing.setPersistenceRequired();
            if (level.addFreshEntity(wing) && level.addFreshEntity(pil)) {
                pil.startRiding(wing, true);
                made++;
            }
        }
        LOG.info("SIEGE-WINGMEN {\"lead\":\"{}\",\"made\":{}}", BuiltInRegistries.ENTITY_TYPE.getKey(type).getPath(), made);
    }

    /** For the siege test: shots fired by the squadron's riders, counted on their mounts. */
    public static int shots(Entity mount) {
        return mount.getPersistentData().getInt(SHOTS);
    }
}
