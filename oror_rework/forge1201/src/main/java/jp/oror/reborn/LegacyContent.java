package jp.oror.reborn;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.EntityType.Builder;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour.Properties;
import net.minecraftforge.event.entity.player.PlayerInteractEvent.RightClickBlock;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.DeferredRegister;

public final class LegacyContent {
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(Registries.BLOCK, "oror_supreme_bosses");
    public static final List<RegistryObject<?>> CONTENT = new ArrayList<>();
    private static final Map<String, RegistryObject<Block>> SEALS = new LinkedHashMap<>();
    public static final RegistryObject<EntityType<CitadelGuard>> DUNGEON = OrorReborn.ENTITIES
        .register("dungeon_minion", () -> Builder.of(CitadelGuard::new, MobCategory.MONSTER).sized(0.6F, 1.95F).build("oror_supreme_bosses:dungeon_minion"));

    public static void seal(RightClickBlock e) {
        if (!e.getLevel().isClientSide) {
            for (Entry<String, RegistryObject<Block>> entry : SEALS.entrySet()) {
                if (e.getLevel().getBlockState(e.getPos()).is((Block)entry.getValue().get())) {
                    SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(entry.getKey()).get()).create(e.getLevel());
                    if (b == null) {
                        return;
                    }

                    BlockPos p = e.getPos().above();
                    b.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
                    if (e.getLevel().noCollision(b)) {
                        e.getLevel().removeBlock(e.getPos(), false);
                        e.getLevel().addFreshEntity(b);
                        e.setCanceled(true);
                    }

                    return;
                }
            }
        }
    }

    static {
        // v0.17.4: only the seal block is left of the per-character content (citadels place it; right-clicking it summons
        // the boss). Its item, the citadel bricks, the essences, the Echo replicas and the 41 guard eggs are gone.
        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            SEALS.put(s.id, BLOCKS.register(s.id + "_boss_seal", () -> new Block(Properties.of().strength(6.0F, 30.0F))));
        }

        CONTENT.add(OrorReborn.ITEMS.register("omniregistry_treasure", () -> new net.minecraft.world.item.Item(new net.minecraft.world.item.Item.Properties())));
    }
}
