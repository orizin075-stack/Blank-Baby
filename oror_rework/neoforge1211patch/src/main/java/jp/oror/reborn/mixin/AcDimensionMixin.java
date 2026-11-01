package jp.oror.reborn.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Alex's Caves remembers the dimension a thread samples biomes for (ACWorldSeedHolder.setDimension), and it is told so
 * on every chunk lookup of the server (its hook in ServerChunkCache.getChunk): each block a path search or a collision
 * looks at sets the thread's value again, nearly always to what it already is. In the hundred-man battle that was a
 * tenth of the server thread (049's CI profile), in ThreadLocal.set. When the last call of all was this thread's, with
 * the same dimension, the thread's value is already that one and the call is skipped. The last call is kept as one
 * pair (thread, dimension), replaced whole, so that no thread can see another's half; the server's own thread keeps
 * its last dimension apart, since only it changes its own value (the chunk workers' calls in between missed the shared
 * pair: a third of the cost was left). A reset forgets both.
 */
@Pseudo
@Mixin(targets = "com.github.alexmodguy.alexscaves.server.level.biome.ACWorldSeedHolder", remap = false)
public abstract class AcDimensionMixin {
    @Unique
    private static volatile Object[] oror$last;

    /** The server's own thread and what it set last: only that thread changes its own value, whoever else calls between. */
    @Unique
    private static volatile Thread oror$main;

    @Unique
    private static volatile Object oror$mainKey;

    @Inject(method = "setDimension", at = @At("HEAD"), cancellable = true, remap = false)
    private static void oror$same(net.minecraft.resources.ResourceKey<net.minecraft.world.level.Level> key, CallbackInfo ci) {
        Thread t = Thread.currentThread();
        if (t == oror$main) {
            if (key == oror$mainKey) {
                ci.cancel();
            }
            return;
        }
        Object[] last = oror$last;
        if (last != null && last[0] == t && last[1] == key) {
            ci.cancel();
        }
    }

    @Inject(method = "setDimension", at = @At("RETURN"), remap = false)
    private static void oror$set(net.minecraft.resources.ResourceKey<net.minecraft.world.level.Level> key, CallbackInfo ci) {
        Thread t = Thread.currentThread();
        if (t == oror$main) {
            oror$mainKey = key;
            return;
        }
        net.minecraft.server.MinecraftServer server = net.neoforged.neoforge.server.ServerLifecycleHooks.getCurrentServer();
        if (server != null && server.getRunningThread() == t) {
            oror$mainKey = key;
            oror$main = t;
        } else {
            oror$last = new Object[]{t, key};
        }
    }

    @Inject(method = "reset", at = @At("HEAD"), remap = false)
    private static void oror$reset(CallbackInfo ci) {
        oror$main = null;
        oror$mainKey = null;
        oror$last = null;
    }
}
