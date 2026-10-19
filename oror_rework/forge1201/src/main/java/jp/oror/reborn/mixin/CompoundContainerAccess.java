package jp.oror.reborn.mixin;

import net.minecraft.world.CompoundContainer;
import net.minecraft.world.Container;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin({CompoundContainer.class})
public interface CompoundContainerAccess {
    @Accessor("container1")
    Container oror$getFirst();

    @Accessor("container2")
    Container oror$getSecond();
}
