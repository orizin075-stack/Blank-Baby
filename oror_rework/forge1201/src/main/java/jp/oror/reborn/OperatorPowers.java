package jp.oror.reborn;

import java.util.Set;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;

public final class OperatorPowers {
    public static final Set<String> HOLDERS = Set.of("innocence", "tenki", "miyohime", "riha", "nortia", "demiurgos", "ain_sof_aur");

    public static int level(SupremeEntity b) {
        return b.lore() && HOLDERS.contains(b.spec.id) ? 4 : 0;
    }

    public static void execute(SupremeEntity b, String fixedCommand) {
        if (level(b) == 4 && b.level() instanceof ServerLevel sl) {
            sl.getServer().getCommands().performPrefixedCommand(b.createCommandSourceStack().withSuppressedOutput(), fixedCommand);
        }
    }

    public static void cast(SupremeEntity b, ServerLevel sl, LivingEntity t) {
        if (level(b) == 4) {
            execute(b, "effect give @s minecraft:resistance 10 255 true");
            b.getPersistentData().putLong("ororOperatorExecutions", b.getPersistentData().getLong("ororOperatorExecutions") + 1L);
            RelicEffects.show(sl, b, b.spec.accent, 3);
            if (!(t instanceof SupremeEntity other) || level(other) != 4) {
                Abilities.stun(t, 80);
                t.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 4));
            }

            String var5 = b.spec.id;
            switch (var5) {
                case "miyohime":
                    execute(b, "time set day");
                    execute(b, "weather clear 15");
                    break;
                case "innocence":
                    b.heal(b.getMaxHealth());
                    execute(b, "effect give @s minecraft:regeneration 10 255 true");
                    break;
                case "tenki":
                    b.shield = 500.0F;
                    execute(b, "effect give @s minecraft:strength 10 255 true");
                    break;
                case "riha":
                    execute(b, "weather clear 15");
                    break;
                default:
                    b.shield = 500.0F;
            }
        }
    }
}
