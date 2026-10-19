package jp.oror.reborn;

import java.util.List;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.LootParams.Builder;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;

public final class RelicDrops {
    public static List<ItemStack> roll(SupremeEntity b, Player p, DamageSource s, long seed) {
        ServerLevel sl = (ServerLevel)b.level();
        LootParams params = new Builder(sl)
            .withParameter(LootContextParams.THIS_ENTITY, b)
            .withParameter(LootContextParams.ORIGIN, b.position())
            .withParameter(LootContextParams.DAMAGE_SOURCE, s)
            .withOptionalParameter(LootContextParams.KILLER_ENTITY, s.getEntity())
            .withOptionalParameter(LootContextParams.DIRECT_KILLER_ENTITY, s.getDirectEntity())
            .withParameter(LootContextParams.LAST_DAMAGE_PLAYER, p)
            .create(LootContextParamSets.ENTITY);
        LootTable table = sl.getServer().getLootData().getLootTable(new ResourceLocation("oror_supreme_bosses", "defeats/" + b.spec.id));
        return table.getRandomItems(params, seed);
    }

    public static boolean defeat(SupremeEntity b, DamageSource s) {
        if (b.level() instanceof ServerLevel sl
            && !s.is(DamageTypeTags.BYPASSES_INVULNERABILITY)
            && s.getEntity() instanceof Player p
            && sl.getGameRules().getBoolean(GameRules.RULE_DOMOBLOOT)
            && sl.getGameTime() >= b.nextRelicDrop) {
            b.nextRelicDrop = sl.getGameTime() + 12000L;

            for (ItemStack stack : roll(b, p, s, sl.random.nextLong())) {
                b.spawnAtLocation(stack);
            }

            RelicEffects.show(sl, b, b.spec.accent, 3);
            p.displayClientMessage(Component.literal(b.spec.name + "：顕現攻略。特殊装備が顕れた。"), false);
            return true;
        }

        return false;
    }

    public static void fracture(SupremeEntity b, Player p, float force) {
        if (b.lore() && LorePowers.IMMORTAL.contains(b.spec.id) && b.level().getGameTime() >= b.nextRelicDrop) {
            b.avatarFracture = b.avatarFracture + Math.max(0.0F, Math.min(force, 1000000.0F));
            if (b.avatarFracture >= 100000.0F) {
                b.avatarFracture = 0.0F;
                defeat(b, p.damageSources().playerAttack(p));
                b.heal(b.getMaxHealth());
            }
        }
    }
}
