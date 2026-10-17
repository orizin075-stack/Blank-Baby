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
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour.Properties;
import net.neoforged.neoforge.common.DeferredSpawnEggItem;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.RightClickBlock;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class LegacyContent {
    public static final DeferredRegister<Block> BLOCKS = DeferredRegister.create(Registries.BLOCK, "oror_supreme_bosses");
    public static final List<DeferredItem<?>> CONTENT = new ArrayList<>();
    private static final Map<String, DeferredHolder<Block, Block>> SEALS = new LinkedHashMap<>();
    public static final DeferredHolder<EntityType<?>, EntityType<CitadelGuard>> DUNGEON = OrorReborn.ENTITIES
        .register("dungeon_minion", () -> Builder.of(CitadelGuard::new, MobCategory.MONSTER).sized(0.6F, 1.95F).build("oror_supreme_bosses:dungeon_minion"));

    public static void seal(RightClickBlock e) {
        if (!e.getLevel().isClientSide) {
            for (Entry<String, DeferredHolder<Block, Block>> entry : SEALS.entrySet()) {
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
        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            for (String suffix : List.of("_citadel_bricks", "_boss_seal")) {
                DeferredHolder<Block, Block> b = BLOCKS.register(s.id + suffix, () -> new Block(Properties.of().strength(6.0F, 30.0F)));
                if (suffix.equals("_boss_seal")) {
                    SEALS.put(s.id, b);
                }

                CONTENT.add(OrorReborn.ITEMS.register(s.id + suffix, () -> new BlockItem((Block)b.get(), new net.minecraft.world.item.Item.Properties())));
            }

            CONTENT.add(OrorReborn.ITEMS.register(s.id + "_essence", () -> new Item(new net.minecraft.world.item.Item.Properties())));
            CONTENT.add(
                OrorReborn.ITEMS
                    .register(s.id + "_relic_weapon", () -> CharacterRelics.replica(s.id))
            );
            CONTENT.add(
                OrorReborn.ITEMS
                    .register(
                        s.id + "_dungeon_spawn_egg",
                        () -> new DeferredSpawnEggItem(DUNGEON, s.outfit, s.accent, new net.minecraft.world.item.Item.Properties())
                    )
            );
        }

        CONTENT.add(OrorReborn.ITEMS.register("omniregistry_treasure", () -> new Item(new net.minecraft.world.item.Item.Properties())));
    }
}
