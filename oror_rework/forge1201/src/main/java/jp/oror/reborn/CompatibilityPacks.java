package jp.oror.reborn;

import java.util.stream.Stream;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraft.server.packs.repository.Pack.Position;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.event.AddPackFindersEvent;

public final class CompatibilityPacks {
    public static void add(AddPackFindersEvent e) {
        addResources(e, "macabre", "0.9.1", "macabre_091_atlas");
        addResources(e, "gtbcs_geomancy_plus", "1.1.0-1.21.1", "geomancy_110_atlas");
        addResources(e, "modulargolems", "3.1.43", "golems_guide_3143");
        addResources(e, "mowziesmobs", "1.8.2", "mowzie_182");
        addResources(e, "superbwarfare", "0.8.9.2", "sbw_0892");
        addResources(e, "jeg", "1.8.2", "jeg_182");
        add(e, "dungeons_arise", "2.1.68", "dungeons_arise_2168");
        add(e, "golemdungeons", "2.0.9", "golemdungeons_209");
        add(e, "iceandfire", "2.0", "iceandfire_20");
        add(e, "iceandfire", "2.1.4", "iceandfire_214");
        add(e, "irons_spellbooks", "1.21.1-3.16.2", "irons_spellbooks_3162");
        if (Stream.of("l2artifacts", "l2hostility", "artifacts", "accessories").noneMatch(id -> ModList.get().isLoaded(id))) {
            add(e, "modulargolems", "3.1.43", "modulargolems_3143");
        }
    }

    private static void addResources(AddPackFindersEvent e, String id, String version, String folder) {
        if (ModList.get().getModContainerById(id).map(m -> m.getModInfo().getVersion().toString().equals(version)).orElse(false)) {
            e.addPackFinders(
                new ResourceLocation("oror_supreme_bosses", "resourcepacks/" + folder),
                PackType.CLIENT_RESOURCES,
                Component.literal("OROR finite animations: " + id),
                PackSource.BUILT_IN,
                true,
                Position.TOP
            );
        }
    }

    private static void add(AddPackFindersEvent e, String id, String version, String folder) {
        if (ModList.get().getModContainerById(id).map(m -> m.getModInfo().getVersion().toString().equals(version)).orElse(false)) {
            e.addPackFinders(
                new ResourceLocation("oror_supreme_bosses", "resourcepacks/" + folder),
                PackType.SERVER_DATA,
                Component.literal("OROR compatibility: " + id),
                PackSource.BUILT_IN,
                true,
                Position.TOP
            );
        }
    }
}
