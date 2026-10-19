package jp.oror.reborn;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

@GameTestHolder("oror_supreme_bosses")
@PrefixGameTestTemplate(false)
public final class EquipmentGameTests {
    private static Mob enemy(GameTestHelper h, Villager v) {
        Cow e = (Cow)EntityType.COW.create(h.getLevel());
        e.moveTo(v.getX() + 6.0, v.getY(), v.getZ());
        e.setNoAi(true);
        e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1024.0);
        e.setHealth(1024.0F);
        h.getLevel().addFreshEntity(e);
        v.setTarget(e);
        return e;
    }

    private static void equip(Villager v, ItemStack item) {
        v.setItemInHand(InteractionHand.MAIN_HAND, item);
        v.setNoAi(false);
        MobMind.data(v).putBoolean("OriginalAuto", false);
        MobMind.data(v).remove("Selected");
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 240,
        batch = "equipment"
    )
    public static void tacz_real_gun_fires_hits_and_consumes_gifted_magazine(GameTestHelper h) throws ReflectiveOperationException {
        h.assertTrue(ModList.get().isLoaded("tacz"), "TaCZ present");
        Villager v = CivilizationGameTests.worker(h, 8, 8);
        Mob t = enemy(h, v);
        Class<?> api = Class.forName("com.tacz.guns.api.item.builder.GunItemBuilder");
        Object builder = api.getMethod("create").invoke(null);
        api.getMethod("setId", ResourceLocation.class).invoke(builder, new ResourceLocation("tacz:ak47"));
        api.getMethod("setAmmoCount", int.class).invoke(builder, 8);
        api.getMethod("setAmmoInBarrel", boolean.class).invoke(builder, true);
        ItemStack gun = (ItemStack)api.getMethod("build").invoke(builder);
        h.assertTrue(!gun.isEmpty() && MobEquipmentUse.kind(gun).equals("gun"), "Actual TaCZ gun recognized");
        equip(v, gun);
        h.succeedWhen(() -> {
            h.assertTrue(MobMind.data(v).getInt("GunShots") > 0 && t.getHealth() < 1024.0F, "Actual TaCZ projectile damage; " + MobMind.data(v));

            try {
                Class<?> ig = Class.forName("com.tacz.guns.api.item.IGun");
                Object op = ig.getMethod("getIGunOrNull", ItemStack.class).invoke(null, v.getMainHandItem());
                int ammo = (Integer)ig.getMethod("getCurrentAmmoCount", ItemStack.class).invoke(op, v.getMainHandItem());
                h.assertTrue(ammo < 8, "Native magazine consumed");
                System.out.println("[OROR_EQUIPMENT_CHECK] provider=tacz damage=" + (1024.0F - t.getHealth()) + " remaining_ammo=" + ammo);
            } catch (ReflectiveOperationException var6) {
                throw new IllegalStateException(var6);
            }
        });
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 240,
        batch = "equipment"
    )
    public static void irons_real_scroll_cast_hits_and_silence_blocks_casting(GameTestHelper h) throws ReflectiveOperationException {
        Villager v = CivilizationGameTests.worker(h, 8, 8);
        Mob t = enemy(h, v);
        ItemStack scroll = ((Item)BuiltInRegistries.ITEM.get(new ResourceLocation("irons_spellbooks:scroll"))).getDefaultInstance();
        Class<?> registry = Class.forName("io.redspace.ironsspellbooks.api.registry.SpellRegistry");
        Object spell = registry.getMethod("getSpell", String.class).invoke(null, "irons_spellbooks:firebolt");
        Class<?> sp = Class.forName("io.redspace.ironsspellbooks.api.spells.AbstractSpell");
        Class<?> api = Class.forName("io.redspace.ironsspellbooks.api.spells.ISpellContainer");
        Object container = api.getMethod("createScrollContainer", sp, int.class, ItemStack.class).invoke(null, spell, 3, scroll);
        h.assertTrue(MobEquipmentUse.kind(scroll).equals("magic"), "Real spell components recognized");
        equip(v, scroll);
        v.getPersistentData().putLong("OrorSilencedUntil", h.getLevel().getGameTime() + 100L);
        h.assertTrue(!MobEquipmentUse.use(v, t, h.getLevel(), "magic") && MobMind.data(v).getInt("SpellCasts") == 0, "Silence blocks provider invocation");
        v.getPersistentData().remove("OrorSilencedUntil");
        h.succeedWhen(
            () -> {
                h.assertTrue(MobMind.data(v).getInt("SpellCasts") > 0 && t.getHealth() < 1024.0F, "Actual Iron's spell damage; " + MobMind.data(v));
                System.out
                    .println(
                        "[OROR_EQUIPMENT_CHECK] provider=irons_spellbooks damage="
                            + (1024.0F - t.getHealth())
                            + " spell="
                            + MobMind.data(v).getString("LastSpell")
                    );
            }
        );
    }

    @GameTest(
        template = "empty",
        setupTicks = 40L,
        timeoutTicks = 240,
        batch = "equipment"
    )
    public static void superb_warfare_real_gun_hits_with_finite_native_ammo(GameTestHelper h) throws ReflectiveOperationException {
        Villager v = CivilizationGameTests.worker(h, 8, 8);
        Mob t = enemy(h, v);
        ItemStack gun = ((Item)BuiltInRegistries.ITEM.get(new ResourceLocation("superbwarfare:ak_47"))).getDefaultInstance();
        Class<?> api = Class.forName("com.atsuishio.superbwarfare.data.gun.GunData");
        Object data = api.getMethod("from", ItemStack.class).invoke(null, gun);
        Object ammo = api.getField("ammo").get(data);
        ammo.getClass().getMethod("set", int.class).invoke(ammo, 8);
        api.getMethod("save").invoke(data);
        h.assertTrue(MobEquipmentUse.kind(gun).equals("gun"), "Actual Superb Warfare rifle recognized");
        equip(v, gun);
        h.succeedWhen(() -> {
            h.assertTrue(MobMind.data(v).getInt("GunShots") > 0 && t.getHealth() < 1024.0F, "Actual Superb Warfare projectile damage; " + MobMind.data(v));

            try {
                Object current = api.getMethod("from", ItemStack.class).invoke(null, v.getMainHandItem());
                Object a = api.getField("ammo").get(current);
                int left = (Integer)a.getClass().getMethod("get").invoke(a);
                h.assertTrue(left < 8, "Native ammunition consumed");
                System.out.println("[OROR_EQUIPMENT_CHECK] provider=superbwarfare damage=" + (1024.0F - t.getHealth()) + " remaining_ammo=" + left);
            } catch (ReflectiveOperationException var7) {
                throw new IllegalStateException(var7);
            }
        });
    }
}
