package jp.oror.reborn.compat;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import yesman.epicfight.network.EpicFightNetworkManager;
import yesman.epicfight.registry.entries.EpicFightSkills;
import yesman.epicfight.skill.SkillContainer;
import yesman.epicfight.skill.SkillSlots;
import yesman.epicfight.skill.guard.ParryingSkill;
import yesman.epicfight.world.capabilities.EpicFightCapabilities;
import yesman.epicfight.world.capabilities.entitypatch.player.ServerPlayerPatch;

/**
 * 0.17.22: a player whose guard slot is empty or holds the plain Guard gets the basic Parrying (basicParry=true).
 *
 * 0.17.24: Guard is replaced only once per player. Before, a player who chose Guard again in the skill screen was
 * switched back to Parrying within a second, every time. An empty slot is still filled.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class NightfallBasicParry {
    private static final String GIVEN = "OrorBasicParry022";

    @SubscribeEvent
    public static void tick(PlayerTickEvent.Post event) {
        if (!NightfallPatchSettings.BASIC_PARRY || !(event.getEntity() instanceof ServerPlayer player) || player.tickCount % 20 != 0) {
            return;
        }
        ServerPlayerPatch patch = EpicFightCapabilities.getServerPlayerPatch(player);
        if (patch == null) {
            return;
        }
        SkillContainer guard = patch.getSkill(SkillSlots.GUARD);
        if (guard == null) {
            return;
        }
        boolean given = player.getPersistentData().getBoolean(GIVEN);
        if (guard.getSkill() != null && (given || guard.getSkill() != EpicFightSkills.GUARD.get())) {
            return;
        }
        ParryingSkill parrying = (ParryingSkill)EpicFightSkills.PARRYING.get();
        patch.getPlayerSkills().addLearnedSkill(parrying);
        if (guard.setSkill(parrying)) {
            EpicFightNetworkManager.sendToPlayer(guard.createSyncPacketToLocalPlayer(), player);
            if (!given) {
                player.getPersistentData().putBoolean(GIVEN, true);
                player.sendSystemMessage(Component.translatable("oror.patch.parry_ready"));
            }
        }
    }

    private NightfallBasicParry() {
    }
}
