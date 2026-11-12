package jp.oror.reborn.safety;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (059e) NightFall's summoned sword (efn:summoned_sword, NightFall 3.4.0) takes the server down when it ticks without
 * its owner: its Epic Fight patch asks its owner's patch for a target (SummonedSwordPatch.target) and that is null
 * ("Ticking entity", found in the user's Duel Dominion × Nightfall 052 check: a sword made without an owner, as a spawn
 * egg, a summon command or any mod that makes entities of every kind makes it; a sword whose owner is gone or not yet
 * loaded with it is the same). Such a sword is taken away before Epic Fight ticks it: when it would join the world
 * without an owner, and on any tick (before every other listener) that finds its owner gone. A sword with its owner is
 * left alone. If the patch cannot be read (another NightFall), nothing is done.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class OwnerlessSwords {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Safety");
    private static final ResourceLocation SWORD = ResourceLocation.fromNamespaceAndPath("efn", "summoned_sword");
    private static MethodHandle patchOf;
    private static Class<?> livingPatch, entityPatch;
    private static final java.util.Map<Class<?>, MethodHandle> OWNER = new java.util.HashMap<>();
    private static final MethodHandle NO_OWNER = MethodHandles.constant(Object.class, null);
    private static boolean unusable, bypassJoin;
    public static int removed;
    public static volatile boolean testLogged;
    private static net.minecraft.server.level.ServerLevel testLevel;
    private static Entity testSword;
    private static long testAt;
    private static boolean testJoinAdded;
    private static net.minecraft.world.level.ChunkPos testChunk;

    private OwnerlessSwords() {
    }

    private static boolean sword(Entity e) {
        return SWORD.equals(BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()));
    }

    /** True when the sword's Epic Fight patch is there and has no owner's patch; false when it has one or cannot be read. */
    static boolean ownerless(Entity e) {
        if (unusable) {
            return false;
        }
        try {
            if (patchOf == null) {
                // looked up one method at a time (MethodHandles): asking Epic Fight's capabilities class for all its methods
                // (Class.getMethod) loads every type they name, a client player among them, which a dedicated server
                // refuses (CI 21: "Attempted to load class net/minecraft/client/player/LocalPlayer for invalid dist")
                MethodHandles.Lookup lk = MethodHandles.publicLookup();
                livingPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.LivingEntityPatch");
                entityPatch = Class.forName("yesman.epicfight.world.capabilities.entitypatch.EntityPatch");
                Class<?> caps = Class.forName("yesman.epicfight.world.capabilities.EpicFightCapabilities");
                for (Class<?> ret : new Class<?>[]{entityPatch, livingPatch, Object.class}) {
                    try {
                        patchOf = lk.findStatic(caps, "getEntityPatch", MethodType.methodType(ret, Entity.class, Class.class));
                        break;
                    } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                        // another erasure of its return
                    }
                }
                if (patchOf == null) {
                    unusable = true;
                    LOG.warn("OWNERLESS-SWORDS no EpicFightCapabilities.getEntityPatch: left as it is");
                    return false;
                }
            }
            Object patch = patchOf.invoke(e, entityPatch);
            if (patch == null) {
                return false;
            }
            MethodHandle owner = OWNER.computeIfAbsent(patch.getClass(), OwnerlessSwords::ownerOf);
            if (owner == NO_OWNER) {
                unusable = true;
                LOG.warn("OWNERLESS-SWORDS no getOwnerPatch on {}: left as it is", patch.getClass().getName());
                return false;
            }
            return owner.invoke(patch) == null;
        } catch (Throwable ex) {
            unusable = true;
            LOG.warn("OWNERLESS-SWORDS cannot read the sword's patch: left as it is ({})", ex.toString());
            return false;
        }
    }

    private static MethodHandle ownerOf(Class<?> c) {
        MethodHandles.Lookup lk = MethodHandles.publicLookup();
        for (Class<?> ret : new Class<?>[]{livingPatch, entityPatch, Object.class}) {
            try {
                return lk.findVirtual(c, "getOwnerPatch", MethodType.methodType(ret));
            } catch (ReflectiveOperationException | LinkageError | RuntimeException ex) {
                // another type of its return
            }
        }
        return NO_OWNER;
    }

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void tick(EntityTickEvent.Pre e) {
        Entity en = e.getEntity();
        if (!sword(en) || !ownerless(en)) {
            return;
        }
        e.setCanceled(true);
        if (!en.level().isClientSide) {
            en.discard();
            if (removed++ < 20) {
                LOG.info("OWNERLESS-SWORD removed at {} (its owner gone: NightFall would stop the server on its tick)", en.blockPosition().toShortString());
            }
        }
    }

    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void join(EntityJoinLevelEvent e) {
        if (e.getLevel().isClientSide() || bypassJoin || !sword(e.getEntity()) || e.loadedFromDisk()) {
            return;
        }
        // made without an owner (a spawn egg, a summon command): it would stop the server on its first tick
        if (ownerless(e.getEntity())) {
            e.setCanceled(true);
            removed++;
        }
    }

    /**
     * CI check "swords" (/oror swords test): a summoned sword made without an owner and added as a spawn egg would (it
     * must not join), then one let in past that (it must be taken away before its first tick ends the server).
     */
    @SubscribeEvent
    public static void commands(net.neoforged.neoforge.event.RegisterCommandsEvent e) {
        e.getDispatcher().register(net.minecraft.commands.Commands.literal("oror").then(net.minecraft.commands.Commands.literal("swords")
            .then(net.minecraft.commands.Commands.literal("test").requires(s -> s.hasPermission(2)).executes(c -> {
                net.minecraft.server.level.ServerLevel level = c.getSource().getServer().overworld();
                var type = BuiltInRegistries.ENTITY_TYPE.getOptional(SWORD);
                if (type.isEmpty()) {
                    LOG.info("OWNERLESS-SWORD-TEST {\"present\":false,\"pass\":true}");
                    testLogged = true;
                    return 1;
                }
                net.minecraft.core.BlockPos at = level.getSharedSpawnPos().offset(40, 0, 40);
                // (CI 22: the second sword never ticked out there) its chunk loaded and ticking for the test
                testChunk = new net.minecraft.world.level.ChunkPos(at);
                level.setChunkForced(testChunk.x, testChunk.z, true);
                at = level.getHeightmapPos(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING, at).above(2);
                Entity first = type.get().create(level);
                if (first != null) {
                    first.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5);
                    testJoinAdded = level.addFreshEntity(first) && first.isAlive() && !first.isRemoved();
                }
                Entity second = type.get().create(level);
                if (second != null) {
                    second.moveTo(at.getX() + 2.5, at.getY(), at.getZ() + 0.5);
                    bypassJoin = true;
                    try {
                        level.addFreshEntity(second);
                    } finally {
                        bypassJoin = false;
                    }
                }
                testLevel = level;
                testSword = second;
                testAt = level.getGameTime();
                return 1;
            }))));
    }

    @SubscribeEvent
    public static void serverTick(net.neoforged.neoforge.event.tick.ServerTickEvent.Post e) {
        if (testLevel == null || testLevel.getGameTime() - testAt < 40) {
            return;
        }
        boolean gone = testSword == null || testSword.isRemoved();
        LOG.info(String.format(java.util.Locale.ROOT, "OWNERLESS-SWORD-TEST {\"present\":true,\"readable\":%b,\"joinedWithoutOwner\":%b,"
            + "\"secondRemoved\":%b,\"removed\":%d,\"pass\":%b}", !unusable, testJoinAdded, gone, removed, !testJoinAdded && gone));
        if (testChunk != null) {
            testLevel.setChunkForced(testChunk.x, testChunk.z, false);
            testChunk = null;
        }
        testLevel = null;
        testSword = null;
        testLogged = true;
    }
}
