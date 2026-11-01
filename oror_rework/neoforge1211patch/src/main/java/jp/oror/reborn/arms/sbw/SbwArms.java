package jp.oror.reborn.arms.sbw;

import jp.oror.reborn.arms.OrorArms;
import net.minecraft.world.item.Item;
import net.neoforged.neoforge.registries.RegisterEvent.RegisterHelper;

/** Registers the Superb Warfare guns; only called with Superb Warfare loaded, so its classes stay unloaded otherwise. */
public final class SbwArms {
    public static void register(RegisterHelper<Item> helper) {
        OrorArms.RAILGUN = new RailgunItem();
        OrorArms.LASER_GUN = new LaserGunItem();
        helper.register(OrorArms.id("railgun"), OrorArms.RAILGUN);
        helper.register(OrorArms.id("laser_gun"), OrorArms.LASER_GUN);
    }

    private SbwArms() {
    }
}
