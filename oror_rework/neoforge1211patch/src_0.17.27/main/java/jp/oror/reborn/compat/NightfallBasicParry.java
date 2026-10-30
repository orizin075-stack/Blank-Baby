package jp.oror.reborn.compat;

import com.hm.efn.gameasset.EFNSkills;
import com.p1nero.dpr.gameassets.DPRSkills;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import yesman.epicfight.network.EpicFightNetworkManager;
import yesman.epicfight.registry.entries.EpicFightSkills;
import yesman.epicfight.skill.Skill;
import yesman.epicfight.skill.SkillContainer;
import yesman.epicfight.skill.SkillSlot;
import yesman.epicfight.skill.SkillSlots;
import yesman.epicfight.world.capabilities.EpicFightCapabilities;
import yesman.epicfight.world.capabilities.entitypatch.player.ServerPlayerPatch;

/**
 * 0.17.24 (native combat line): players get Nightfall's own parry (efn:efn_parry) and NightfallCraft's starter dodge
 * and stamina skills, once; the basic Parrying given automatically by 0.17.22-0.17.23 is migrated (basicParry=true).
 *
 * 0.17.25: plain Guard is replaced on the first check only. Before, a player who chose Guard in the skill screen was
 * switched back to Nightfall's parry within a second, every time. An empty guard slot is still filled. Without
 * Nightfall (SETUP_NIGHTFALL.cmd not run) nothing is touched, instead of failing on Nightfall's classes every second.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class NightfallBasicParry {
    private static final String MIGRATED = "OrorNativeSkills024";
    private static final String OLD_AUTOMATIC = "OrorBasicParry022";

    @SubscribeEvent
    public static void tick(PlayerTickEvent.Post event) {
        if (!NightfallPatchSettings.BASIC_PARRY || !(event.getEntity() instanceof ServerPlayer player) || player.tickCount % 20 != 0
                || !ModList.get().isLoaded("efn")) {
            return;
        }
        ServerPlayerPatch patch = EpicFightCapabilities.getServerPlayerPatch(player);
        if (patch != null) {
            Native.equip(player, patch);
        }
    }

    /** Refers to Nightfall's and Dodge Parry Reward's skills, so it is only loaded when Nightfall is. */
    private static final class Native {
        static void equip(ServerPlayer player, ServerPlayerPatch patch) {
            SkillContainer guard = patch.getSkill(SkillSlots.GUARD);
            if (guard == null) {
                return;
            }
            CompoundTag data = player.getPersistentData();
            boolean migrated = data.getBoolean(MIGRATED);
            Skill current = guard.getSkill();
            boolean oldAutomatic = data.getBoolean(OLD_AUTOMATIC) && current == EpicFightSkills.PARRYING.get();
            if (current == null || !migrated && (current == EpicFightSkills.GUARD.get() || oldAutomatic)) {
                if (set(player, patch, SkillSlots.GUARD, EFNSkills.EFN_PARRY)) {
                    player.sendSystemMessage(Component.translatable("oror.patch.parry_ready"));
                }
            }
            if (migrated) {
                return;
            }
            // NightfallCraft's starter skills; equipped custom skills and all progression are kept.
            SkillContainer dodge = patch.getSkill(SkillSlots.DODGE);
            if (dodge != null && (dodge.getSkill() == null || dodge.getSkill() == EpicFightSkills.ROLL.get())) {
                set(player, patch, SkillSlots.DODGE, EFNSkills.EFN_DODGE_ROLL);
            }
            SkillContainer passive = patch.getSkill(SkillSlots.PASSIVE1);
            if (passive != null && passive.getSkill() == null && ModList.get().isLoaded("dodge_parry_reward")) {
                set(player, patch, SkillSlots.PASSIVE1, DPRSkills.STAMINA1.get());
            }
            patch.getPlayerSkills().addLearnedSkill(EFNSkills.EFN_DODGE_STEP);
            data.putBoolean(MIGRATED, true);
        }

        private static boolean set(ServerPlayer player, ServerPlayerPatch patch, SkillSlot slot, Skill skill) {
            patch.getPlayerSkills().addLearnedSkill(skill);
            SkillContainer container = patch.getSkill(slot);
            if (container == null || !container.setSkill(skill)) {
                return false;
            }
            EpicFightNetworkManager.sendToPlayer(container.createSyncPacketToLocalPlayer(), player);
            return true;
        }
    }

    private NightfallBasicParry() {
    }
}
