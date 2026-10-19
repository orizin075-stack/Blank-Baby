package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_compat")
@PrefixGameTestTemplate(false)
public final class CompatibilityGameTests {
    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 300,
        batch = "compat"
    )
    public static void external_mobs_and_oror_share_combat(GameTestHelper h) {
        Collection<String> packs = h.getLevel().getServer().getPackRepository().getSelectedIds();

        for (String p : List.of("dungeons_arise_2168", "golemdungeons_209", "iceandfire_214", "modulargolems_3143")) {
            h.assertTrue(packs.contains("mod/oror_supreme_bosses:resourcepacks/" + p), "Exact-version pack active " + p);
        }

        System.out.println("[OROR_COMPAT] correctionPacks=4 active=true");
        ArrayList<LivingEntity> all = new ArrayList<>();
        int i = 0;

        for (String ns : List.of("cataclysm", "alexscaves", "mowziesmobs", "iceandfire", "irons_spellbooks", "macabre", "modulargolems", "friendsandfoes")) {
            LivingEntity guest = null;

            for (ResourceLocation key : BuiltInRegistries.ENTITY_TYPE.keySet().stream().filter(k -> k.getNamespace().equals(ns)).sorted().toList()) {
                if (((EntityType)BuiltInRegistries.ENTITY_TYPE.get(key)).create(h.getLevel()) instanceof LivingEntity l) {
                    guest = l;
                    break;
                }
            }

            h.assertTrue(guest != null, "External living entity found: " + ns);
            BlockPos p = h.absolutePos(new BlockPos(5 + i % 4 * 5, 2, 5 + i / 4 * 8));
            if (guest instanceof Mob persistent) {
                persistent.setPersistenceRequired();
            }

            guest.moveTo((double)(p.getX() + 3), (double)p.getY(), (double)p.getZ(), 0.0F, 0.0F);
            h.getLevel().addFreshEntity(guest);
            SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get("kokuhaku").get()).create(h.getLevel());
            b.balanced = true;
            b.mana(b.spec.mana);
            b.moveTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5, 0.0F, 0.0F);
            h.getLevel().addFreshEntity(b);
            b.setTarget(guest);
            float hp = guest.getHealth();
            float mp = b.mana();
            Abilities.cast(b, h.getLevel(), guest);
            h.assertTrue(b.mana() < mp, "OROR skill accepted external target " + ns);
            b.hurt(b.damageSources().mobAttack(guest), 12.0F);
            h.assertTrue(b.memory.count("minecraft:mob_attack") > 0, "Incoming external damage processed " + ns);
            if (guest instanceof Mob m) {
                m.setTarget(b);
            }

            all.add(b);
            all.add(guest);
            System.out
                .println(
                    "[OROR_COMPAT] guest="
                        + BuiltInRegistries.ENTITY_TYPE.getKey(guest.getType())
                        + " hp="
                        + hp
                        + "->"
                        + guest.getHealth()
                        + " ororHP="
                        + b.getHealth()
                );
            i++;
        }

        h.runAfterDelay(
            200L,
            () -> {
                for (LivingEntity e : all) {
                    h.assertTrue(
                        Double.isFinite(e.getX()) && Double.isFinite(e.getY()) && Double.isFinite(e.getZ()) && Float.isFinite(e.getHealth()),
                        "Finite combat state"
                    );
                }

                System.out.println("[OROR_COMPAT] namespaces=8 simulatedTicks=200 completed");
                h.succeed();
            }
        );
    }
}
