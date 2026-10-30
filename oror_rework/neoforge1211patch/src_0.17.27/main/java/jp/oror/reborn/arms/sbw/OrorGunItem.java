package jp.oror.reborn.arms.sbw;

import com.atsuishio.superbwarfare.data.gun.GunData;
import com.atsuishio.superbwarfare.data.gun.GunProp;
import com.atsuishio.superbwarfare.data.gun.ShootParameters;
import com.atsuishio.superbwarfare.item.gun.GunGeoItem;
import java.util.List;
import jp.oror.reborn.arms.ArmsItem;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import org.jetbrains.annotations.Nullable;

/**
 * A gun that fires once per full charge: it can only shoot with its energy store full (Superb Warfare gives every gun
 * item an energy capability sized by the data's MaxEnergy), and every shot empties the store. The shot itself is
 * {@link #fire}: the data sets "Projectile": "empty", so Superb Warfare spawns nothing and runs the ammunition, sounds,
 * recoil and animation around it.
 */
public abstract class OrorGunItem extends GunGeoItem {
    protected OrorGunItem() {
        super(new Properties().fireResistant().rarity(Rarity.EPIC));
    }

    public static boolean fullyCharged(ItemStack stack) {
        IEnergyStorage energy = stack.getCapability(Capabilities.EnergyStorage.ITEM);
        return energy != null && energy.getMaxEnergyStored() > 0 && energy.getEnergyStored() >= energy.getMaxEnergyStored();
    }

    @Override
    public boolean canShoot(GunData data, @Nullable Entity shooter) {
        boolean creative = shooter instanceof Player player && player.isCreative();
        return (creative || fullyCharged(data.stack)) && super.canShoot(data, shooter);
    }

    @Override
    public boolean shootBullet(ShootParameters parameters) {
        if (parameters.shooter == null) {
            return false;
        }
        fire(parameters, ((Number) parameters.data.get(GunProp.DAMAGE)).doubleValue(), ((Number) parameters.data.get(GunProp.HEADSHOT)).doubleValue());
        return true;
    }

    protected abstract void fire(ShootParameters parameters, double damage, double headshot);

    @Override
    public void afterShoot(ShootParameters parameters) {
        super.afterShoot(parameters);
        IEnergyStorage energy = parameters.data.stack.getCapability(Capabilities.EnergyStorage.ITEM);
        if (energy != null) {
            energy.extractEnergy(Integer.MAX_VALUE, false);
        }
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        ArmsItem.tooltip(getDescriptionId(), 4, tooltip);
        IEnergyStorage energy = stack.getCapability(Capabilities.EnergyStorage.ITEM);
        if (energy != null && energy.getMaxEnergyStored() > 0) {
            boolean full = energy.getEnergyStored() >= energy.getMaxEnergyStored();
            tooltip.add(Component.translatable(full ? "des.oror_supreme_bosses.gun.charged" : "des.oror_supreme_bosses.gun.charging",
                String.format("%,d", energy.getEnergyStored()), String.format("%,d", energy.getMaxEnergyStored()))
                .withStyle(full ? ChatFormatting.AQUA : ChatFormatting.RED));
        }
    }
}
