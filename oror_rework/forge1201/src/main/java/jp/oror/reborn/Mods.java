package jp.oror.reborn;

import java.nio.charset.StandardCharsets;
import java.util.UUID;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;

/**
 * Forge 1.20.1 port: attribute modifiers are keyed by UUID there, by ResourceLocation in 1.21.1. Each of the mod's
 * modifier names keeps its ResourceLocation and gets a fixed UUID derived from it, so a modifier saved with an entity
 * is found again after a reload.
 */
public final class Mods {
    public static UUID id(ResourceLocation name) {
        return UUID.nameUUIDFromBytes(name.toString().getBytes(StandardCharsets.UTF_8));
    }

    public static AttributeModifier make(ResourceLocation name, double amount, AttributeModifier.Operation op) {
        return new AttributeModifier(id(name), name.toString(), amount, op);
    }

    public static boolean has(AttributeInstance a, ResourceLocation name) {
        return a.getModifier(id(name)) != null;
    }

    public static AttributeModifier get(AttributeInstance a, ResourceLocation name) {
        return a.getModifier(id(name));
    }

    public static void remove(AttributeInstance a, ResourceLocation name) {
        a.removeModifier(id(name));
    }

    private Mods() {
    }
}
