package jp.oror.reborn;

import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.EntityType.Builder;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Item.Properties;
import net.minecraft.world.level.ItemLike;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.event.entity.EntityAttributeModificationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig.Type;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod("oror_supreme_bosses")
public final class OrorReborn {
    public static final String ID = "oror_supreme_bosses";
    public static final DeferredRegister<EntityType<?>> ENTITIES = DeferredRegister.create(Registries.ENTITY_TYPE, "oror_supreme_bosses");
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, "oror_supreme_bosses");
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, "oror_supreme_bosses");
    public static final Map<String, RegistryObject<EntityType<SupremeEntity>>> TYPES = new LinkedHashMap<>();
    public static final Map<String, RegistryObject<Item>> EGGS = new LinkedHashMap<>();
    public static final RegistryObject<EntityType<FamiliarEntity>> FAMILIAR = ENTITIES.register(
        "familiar",
        () -> Builder.of(FamiliarEntity::new, MobCategory.CREATURE)
                .sized(0.6F, 0.8F)
                .clientTrackingRange(8)
                .updateInterval(2)
                .build("oror_supreme_bosses:familiar")
    );

    public OrorReborn() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        TierSignals.init();
        MiracleLoot.FUNCTIONS.register(bus);
        NightfallArsenal.CONTENT.size();
        FusionItems.ITEMS.size();
        CharacterRelics.ITEMS.size();
        AdventureContent.CONTENT.size();
        LegacyContent.BLOCKS.register(bus);
        VillagerIndustry.POIS.register(bus);
        VillagerIndustry.PROFESSIONS.register(bus);
        ENTITIES.register(bus);
        ITEMS.register(bus);
        TABS.register(bus);
        MinecraftForge.EVENT_BUS.addListener(AdaptiveCombat::tick);
        MinecraftForge.EVENT_BUS.addListener(TukuyoBridge::tick);
        MinecraftForge.EVENT_BUS.addListener(AdaptiveCombat::damage);
        MinecraftForge.EVENT_BUS.addListener(VillagerLife::tick);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::tick);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::interact);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::trade);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::placed);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::broken);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::damaged);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::death);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::open);
        MinecraftForge.EVENT_BUS.addListener(VillageReputation::close);
        MinecraftForge.EVENT_BUS.addListener(DivineDomains::tick);
        MinecraftForge.EVENT_BUS.addListener(TierSignals::track);
        MinecraftForge.EVENT_BUS.addListener(LevelRewards::drops);
        MinecraftForge.EVENT_BUS.addListener(LevelRewards::xp);
        MinecraftForge.EVENT_BUS.addListener(CharacterArsenal::tick);
        MinecraftForge.EVENT_BUS.addListener(CharacterArsenal::heal);
        MinecraftForge.EVENT_BUS.addListener(NightfallFusion::kill);
        MinecraftForge.EVENT_BUS.addListener(NightfallFusion::clone);
        MinecraftForge.EVENT_BUS.addListener(NightfallFusion::tick);
        MinecraftForge.EVENT_BUS.addListener(NightfallFusion::damage);
        MinecraftForge.EVENT_BUS.addListener(VillagerIndustry::tick);
        MinecraftForge.EVENT_BUS.addListener(VillagerIndustry::interact);
        MinecraftForge.EVENT_BUS.addListener(VillagerIndustry::trades);
        MinecraftForge.EVENT_BUS.addListener(VillagerIndustry::death);
        MinecraftForge.EVENT_BUS.addListener(VillagerIndustry::drops);
        MinecraftForge.EVENT_BUS.addListener(MobConversation::autonomousTick);
        MinecraftForge.EVENT_BUS.addListener(MobConversation::interact);
        MinecraftForge.EVENT_BUS.addListener(MobConversation::chat);
        bus.addListener(OrorReborn::attributes);
        bus.addListener(OrorReborn::combatAttributes);
        // the compatibility packs patched the 1.21.1 builds of other mods; NightfallCraft runs their 1.20.1 builds
        ModLoadingContext.get().registerConfig(Type.SERVER, RebornConfig.SPEC);
        MinecraftForge.EVENT_BUS.addListener(NightfallArsenal::damage);
        MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.server.ServerStoppingEvent event) -> DialogueArchive.flush(3000L));
        MinecraftForge.EVENT_BUS.addListener(RelicPowers::damage);
        MinecraftForge.EVENT_BUS.addListener(RelicPowers::summonedTick);
        MinecraftForge.EVENT_BUS.addListener(AdventureContent::damage);
        MinecraftForge.EVENT_BUS.addListener(AdventureContent::gate);
        MinecraftForge.EVENT_BUS.addListener(PactSystem::tick);
        MinecraftForge.EVENT_BUS.addListener(PactSystem::clone);
        MinecraftForge.EVENT_BUS.addListener(RebornCommands::register);
        MinecraftForge.EVENT_BUS.addListener(LegacyContent::seal);
        MinecraftForge.EVENT_BUS.addListener(WorldEvents::livingTick);
        MinecraftForge.EVENT_BUS.addListener(WorldEvents::damage);
        MinecraftForge.EVENT_BUS.addListener(WorldEvents::levelTick);
    }

    private static void attributes(EntityAttributeCreationEvent e) {
        TYPES.forEach((id, t) -> e.put((EntityType)t.get(), SupremeEntity.attributes(CharacterSpec.ALL.get(id)).build()));
        e.put((EntityType)FAMILIAR.get(), FamiliarEntity.attributes().build());
        e.put((EntityType)LegacyContent.DUNGEON.get(), Zombie.createAttributes().build());
    }

    private static void combatAttributes(EntityAttributeModificationEvent e) {
        e.add(EntityType.VILLAGER, Attributes.ATTACK_DAMAGE, 48.0);
    }

    static {
        for (CharacterSpec s : CharacterSpec.ALL.values()) {
            RegistryObject<EntityType<SupremeEntity>> t = ENTITIES.register(
                s.id,
                () -> Builder.<SupremeEntity>of((type, l) -> new SupremeEntity(type, l, s), MobCategory.CREATURE)
                        .sized(s.width, s.height)
                        .clientTrackingRange(12)
                        .updateInterval(2)
                        .build("oror_supreme_bosses:" + s.id)
            );
            TYPES.put(s.id, t);
            EGGS.put(s.id, ITEMS.register(s.id + "_spawn_egg", () -> new ForgeSpawnEggItem(t, s.outfit, s.accent, new Properties())));
        }

        TABS.register(
            "supreme_entities",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.oror_supreme_bosses"))
                    .icon(() -> new ItemStack((ItemLike)EGGS.get("kokuhaku").get()))
                    .displayItems((p, o) -> {
                        EGGS.values().forEach(i -> o.accept((ItemLike)i.get()));
                        LegacyContent.CONTENT.forEach(i -> o.accept((ItemLike)i.get()));
                        AdventureContent.CONTENT.forEach(i -> o.accept((ItemLike)i.get()));
                        NightfallArsenal.CONTENT.forEach(i -> o.accept((ItemLike)i.get()));
                        FusionItems.ITEMS.values().forEach(i -> o.accept((ItemLike)i.get()));
                        CharacterRelics.ITEMS.values().forEach(i -> o.accept((ItemLike)i.get()));
                    })
                    .build()
        );
    }
}
