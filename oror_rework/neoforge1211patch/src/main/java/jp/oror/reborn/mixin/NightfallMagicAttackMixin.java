package jp.oror.reborn.mixin;

import io.redspace.ironsspellbooks.api.events.SpellPreCastEvent;
import io.redspace.ironsspellbooks.api.magic.MagicData;
import io.redspace.ironsspellbooks.api.magic.SpellSelectionManager;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import io.redspace.ironsspellbooks.api.spells.CastResult;
import io.redspace.ironsspellbooks.api.spells.CastType;
import io.redspace.ironsspellbooks.api.spells.SpellData;
import io.redspace.ironsspellbooks.network.casting.OnCastStartedPacket;
import io.redspace.ironsspellbooks.network.casting.UpdateCastingStatePacket;
import jp.oror.reborn.compat.NightfallWeaponCasting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.network.PacketDistributor;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import yesman.epicfight.api.animation.types.StaticAnimation;
import yesman.epicfight.skill.SkillContainer;
import yesman.epicfight.skill.common.ComboAttacks;

/**
 * 0.17.22: a dash or air attack with one of the restored tcrcore magic_ weapons starts the selected spell at half its
 * level, without EFIS's attack wait and casting motion.
 *
 * 0.17.24: the cast now goes through Iron's own canBeCastedBy first, as AbstractSpell.attemptInitiateCast does: an
 * unlearned spell, a spell on cooldown or too little mana no longer casts (before, mana only bottomed out at 0 and the
 * cooldown restarted, so a weapon could cast the same spell on every dash). The reason is shown like a normal cast's.
 */
@Mixin(value = ComboAttacks.class, remap = false)
public abstract class NightfallMagicAttackMixin {
    @Inject(method = "executeOnServer", at = @At("HEAD"))
    private void oror$captureAttack(SkillContainer container, CompoundTag args, CallbackInfo ci) {
        ServerPlayer player = (ServerPlayer)container.getServerExecutor().getOriginal();
        args.putBoolean("oror_magic_trigger", player.isSprinting() || !player.onGround() && !player.isInWater());
    }

    @Inject(method = "executeOnServer", at = @At("TAIL"))
    private void oror$magicAttack(SkillContainer container, CompoundTag args, CallbackInfo ci) {
        boolean trigger = args.getBoolean("oror_magic_trigger");
        args.remove("oror_magic_trigger");
        ServerPlayer player = (ServerPlayer)container.getServerExecutor().getOriginal();
        ResourceLocation weapon = BuiltInRegistries.ITEM.getKey(player.getMainHandItem().getItem());
        if (!trigger || !weapon.getNamespace().equals("tcrcore") || !weapon.getPath().startsWith("magic_") || container.getServerExecutor().isStunned()) {
            return;
        }
        MagicData magic = MagicData.getPlayerMagicData(player);
        if (magic.isCasting()) {
            return;
        }
        SpellSelectionManager selection = new SpellSelectionManager(player);
        SpellSelectionManager.SelectionOption option = selection.getSelection();
        SpellData selected = selection.getSelectedSpellData();
        if (option == null || selected == null || selected == SpellData.EMPTY) {
            return;
        }
        AbstractSpell spell = selected.getSpell();
        int level = spell.getLevelFor(selected.getLevel(), player) / 2;
        if (level <= 0) {
            return;
        }
        CastResult allowed = spell.canBeCastedBy(level, option.getCastSource(), magic, player);
        if (!allowed.isSuccess()) {
            if (allowed.message != null) {
                player.connection.send(new ClientboundSetActionBarTextPacket(allowed.message));
            }
            return;
        }
        if (!spell.checkPreCastConditions(player.level(), level, player, magic)
            || !NightfallWeaponCasting.allow(player, new SpellPreCastEvent(player, spell.getSpellId(), level, spell.getSchoolType(), option.getCastSource()))) {
            return;
        }
        int duration = 1;
        if (spell.getCastType() == CastType.CONTINUOUS) {
            StaticAnimation attack = container.getServerExecutor().getAnimator().getPlayerFor(null).getRealAnimation().get();
            duration = Math.max(1, (int)(attack.getTotalTime() * 20.0F));
        }
        magic.initiateCast(spell, level, duration, option.getCastSource(), option.slot);
        magic.setPlayerCastingItem(ItemStack.EMPTY);
        spell.onServerPreCast(player.level(), level, player, magic);
        PacketDistributor.sendToPlayer(player, new UpdateCastingStatePacket(spell.getSpellId(), level, duration, option.getCastSource(), option.slot));
        PacketDistributor.sendToPlayersTrackingEntityAndSelf(player, new OnCastStartedPacket(player.getUUID(), spell.getSpellId(), level));
    }
}
