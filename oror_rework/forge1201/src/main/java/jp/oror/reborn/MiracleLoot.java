package jp.oror.reborn;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.functions.LootItemFunction;
import net.minecraft.world.level.storage.loot.functions.LootItemFunctionType;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.DeferredRegister;

public final class MiracleLoot {
    public static final DeferredRegister<LootItemFunctionType<?>> FUNCTIONS = DeferredRegister.create(Registries.LOOT_FUNCTION_TYPE, "oror_supreme_bosses");
    public static final RegistryObject<LootItemFunctionType<MiracleLoot.Swap>> TYPE = FUNCTIONS.register(
        "miracle_weapon", () -> new LootItemFunctionType(MapCodec.unit(new MiracleLoot.Swap()))
    );
    private static final String[] WEAPONS = new String[]{"agony", "herrscher", "ruine", "moonless", "solar", "antitheus"};

    private MiracleLoot() {
    }

    public static final class Swap implements LootItemFunction {
        public LootItemFunctionType<MiracleLoot.Swap> getType() {
            return (LootItemFunctionType<MiracleLoot.Swap>)MiracleLoot.TYPE.get();
        }

        public ItemStack apply(ItemStack input, LootContext context) {
            if (!ModList.get().isLoaded("wom")) {
                return input;
            } else {
                Item item = (Item)BuiltInRegistries.ITEM
                    .get(new ResourceLocation("wom", MiracleLoot.WEAPONS[context.getRandom().nextInt(MiracleLoot.WEAPONS.length)]));
                return item == Items.AIR ? input : item.getDefaultInstance();
            }
        }
    }
}
