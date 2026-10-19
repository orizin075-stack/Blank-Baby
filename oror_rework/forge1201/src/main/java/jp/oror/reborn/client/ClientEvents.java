package jp.oror.reborn.client;

import jp.oror.reborn.CharacterSpec;
import jp.oror.reborn.LegacyContent;
import jp.oror.reborn.OrorReborn;
import net.minecraft.client.renderer.entity.ZombieRenderer;
import net.minecraft.world.entity.EntityType;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber.Bus;
import net.minecraftforge.client.event.EntityRenderersEvent.RegisterRenderers;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    value = {Dist.CLIENT},
    bus = Bus.MOD
)
public final class ClientEvents {
    @SubscribeEvent
    public static void renderers(RegisterRenderers e) {
        OrorReborn.TYPES.forEach((id, t) -> e.registerEntityRenderer((EntityType)t.get(), ctx -> new CharacterRenderer(ctx, CharacterSpec.ALL.get(id))));
        e.registerEntityRenderer(EntityType.VILLAGER, HumanVillagerRenderer::new);
        e.registerEntityRenderer((EntityType)OrorReborn.FAMILIAR.get(), FamiliarRenderer::new);
        e.registerEntityRenderer((EntityType)LegacyContent.DUNGEON.get(), ZombieRenderer::new);
        System.out.println("[OROR] Registered 41 character renderers and humanoid villagers");
    }
}
