package jp.oror.reborn;

import com.google.gson.JsonDeserializationContext;
import com.google.gson.JsonObject;
import com.google.gson.JsonSerializationContext;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.Serializer;
import net.minecraft.world.level.storage.loot.functions.LootItemFunction;
import net.minecraft.world.level.storage.loot.functions.LootItemFunctionType;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.DeferredRegister;

public final class MiracleLoot {
    public static final DeferredRegister<LootItemFunctionType> FUNCTIONS = DeferredRegister.create(Registries.LOOT_FUNCTION_TYPE, "oror_supreme_bosses");
    // Forge 1.20.1: loot functions are read through a JSON serializer (a codec in 1.21.1); this one has no fields
    public static final RegistryObject<LootItemFunctionType> TYPE = FUNCTIONS.register(
        "miracle_weapon", () -> new LootItemFunctionType(new Serializer<MiracleLoot.Swap>() {
            @Override
            public void serialize(JsonObject json, MiracleLoot.Swap value, JsonSerializationContext context) {
            }

            @Override
            public MiracleLoot.Swap deserialize(JsonObject json, JsonDeserializationContext context) {
                return new MiracleLoot.Swap();
            }
        })
    );
    private static final String[] WEAPONS = new String[]{"agony", "herrscher", "ruine", "moonless", "solar", "antitheus"};

    private MiracleLoot() {
    }

    public static final class Swap implements LootItemFunction {
        public LootItemFunctionType getType() {
            return MiracleLoot.TYPE.get();
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
