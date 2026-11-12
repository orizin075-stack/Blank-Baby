package jp.oror.reborn.royal;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

/**
 * The forbidden vault's king-slayers: weapons (any item carrying OrorKingslayer in its custom data: a sword, a bow, a
 * gun) whose blow shatters the Villager King's field outright, so that for ten seconds he takes the full weight of every
 * hit; nothing else breaks it short of a single blow of twice its strength. They are forbidden for a reason: held, they
 * wither their bearer, and every blow at the king costs blood.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class ForbiddenArms {
    public static final String KINGSLAYER = "OrorKingslayer";
    /** (059d) On an arrow, a bolt, a thrown trident or a round: it left a king-slayer (V20 05_weapons_12.md). */
    public static final String SHOT = "OrorKingslayerShot";

    private ForbiddenArms() {
    }

    public static boolean kingslayer(ItemStack stack) {
        return KingslayerArms.is(stack) || marked(stack);
    }

    /** Carrying the mark in its custom data (the vault's king-slayers before 051 were vanilla arms so marked). */
    public static boolean marked(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data != null && data.copyTag().getBoolean(KINGSLAYER);
    }

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void strike(LivingIncomingDamageEvent e) {
        if (!(e.getEntity() instanceof RoyalMob king) || king.role() != RoyalRole.KING || king.sovereign() == null
            || !(e.getSource().getEntity() instanceof Player player)) {
            return;
        }
        // (059d) a shot is a king-slayer's by the arm it left, not by what the hand holds when it lands (V20: drawn from
        // the king-slayer bow, then the hand changed, the arrow lost its power; a common arrow landing while the hand
        // held the king-slayer sword had it)
        net.minecraft.world.entity.Entity direct = e.getSource().getDirectEntity();
        boolean slayer = direct instanceof net.minecraft.world.entity.projectile.Projectile shot ? shot.getPersistentData().getBoolean(SHOT)
            : kingslayer(player.getMainHandItem());
        if (!slayer) {
            return;
        }
        RoyalSovereign sovereign = king.sovereign();
        if (!sovereign.breached()) {
            // a blow of the field's full breaking strength: the field falls for its ten seconds
            sovereign.incoming((float) sovereign.breakThreshold());
            if (king.level() instanceof ServerLevel level) {
                level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, king.getX(), king.getY() + 1.2, king.getZ(), 1, 0, 0, 0, 0);
                level.sendParticles(ParticleTypes.END_ROD, king.getX(), king.getY() + 1.2, king.getZ(), 80, 1.2, 1.2, 1.2, 0.3);
                level.playSound(null, king.blockPosition(), SoundEvents.GLASS_BREAK, SoundSource.HOSTILE, 3F, 0.5F);
            }
            player.displayClientMessage(Component.literal("王殺しの刃が村人王の結界を砕いた！（10秒）"), true);
        }
        // the price of the forbidden arms
        player.hurt(player.damageSources().magic(), 4F);
    }

    /** (059d) A shot leaving a king-slayer (bow, crossbow, trident, gun: in the hand that launched it) carries its mark. */
    @SubscribeEvent
    public static void shot(net.neoforged.neoforge.event.entity.EntityJoinLevelEvent e) {
        if (e.getLevel().isClientSide() || !(e.getEntity() instanceof net.minecraft.world.entity.projectile.Projectile pr)
            || !(pr.getOwner() instanceof Player p) || pr.tickCount > 1 || pr.getPersistentData().contains(SHOT)) {
            return;
        }
        ItemStack main = p.getMainHandItem(), off = p.getOffhandItem();
        boolean slayer = launcher(main) ? kingslayer(main) : launcher(off) && kingslayer(off);
        pr.getPersistentData().putBoolean(SHOT, slayer);
    }

    private static boolean launcher(ItemStack s) {
        return s.getItem() instanceof net.minecraft.world.item.ProjectileWeaponItem || s.getItem() instanceof net.minecraft.world.item.TridentItem
            || s.getItem().getClass().getName().contains("Gun");
    }

    @SubscribeEvent
    public static void carry(PlayerTickEvent.Post e) {
        Player player = e.getEntity();
        if (player.level().isClientSide || player.tickCount % 40 != 0) {
            return;
        }
        if (kingslayer(player.getMainHandItem()) || kingslayer(player.getOffhandItem())) {
            player.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 1, true, true));
            player.addEffect(new MobEffectInstance(MobEffects.HUNGER, 60, 1, true, false));
        }
    }
}
