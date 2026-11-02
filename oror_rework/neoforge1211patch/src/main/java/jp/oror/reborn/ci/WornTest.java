package jp.oror.reborn.ci;

import com.mojang.authlib.GameProfile;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import jp.oror.reborn.gear.WornGear;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Zombie;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.levelgen.Heightmap;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.damagesource.DamageContainer;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (052) /oror worn test: the gear worn (Curios) does what it is for. A stand-in player with the slots Curios gives a
 * player wears each piece in turn and is struck (the blows handed to WornGear as the game hands them): the emblem turns
 * aside a zombie's blow from in front and answers it, the talon dodges a blow from behind, the banner rallies when
 * struck, the bloom and then the talisman each turn back a blow that would kill (the talisman spent), the King's token
 * makes a Hero of the Village. WORN-RESULT {...} with "pass".
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class WornTest {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Worn");
    public static volatile boolean resultLogged;

    private WornTest() {
    }

    /** The stand-in player: moved where a teleport would take it (it has no client to tell). */
    static final class Stand extends FakePlayer {
        Stand(ServerLevel level) {
            super(level, new GameProfile(UUID.fromString("0f0e0d0c-0b0a-4908-8706-0504030201ee"), "[OROR Worn]"));
        }

        @Override
        public void teleportTo(double x, double y, double z) {
            this.moveTo(x, y, z);
        }
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("worn").then(Commands.literal("test")
            .requires(s -> s.hasPermission(2)).executes(c -> run(c.getSource())))));
    }

    private static int run(CommandSourceStack src) {
        Map<String, Object> r = new LinkedHashMap<>();
        List<Zombie> made = new ArrayList<>();
        boolean pass = false;
        try {
            ServerLevel level = src.getServer().overworld();
            BlockPos at = BlockPos.containing(src.getPosition());
            at = new BlockPos(at.getX(), level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, at.getX(), at.getZ()), at.getZ());
            Stand p = new Stand(level);
            p.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, 0F, 0F);
            p.setHealth(p.getMaxHealth());
            r.put("curios", WornGear.CURIOS);
            String[][] wear = {{"bracelet", "parry_emblem"}, {"hands", "dodge_talon"}, {"back", "squad_banner"}, {"head", "last_bloom"},
                {"necklace", "rewind_talisman"}};
            Map<String, Boolean> fits = new LinkedHashMap<>();
            for (String[] w : wear) {
                fits.put(w[0], WornGear.wear(p, w[0], ItemStack.EMPTY));
            }
            r.put("slots", WornGear.slots(p));
            r.put("fits", fits);

            // the emblem: a zombie's blow from in front
            put(p, "bracelet", "parry_emblem");
            Zombie front = zombie(level, made, p, 0, 2);
            boolean parried = strike(p, p.damageSources().mobAttack(front), 6F);
            r.put("emblem_parried", parried);
            r.put("emblem_answered", !front.isAlive() || front.getHealth() < front.getMaxHealth());
            r.put("emblem_recharging", p.getCooldowns().isOnCooldown(WornGear.item("parry_emblem")));
            WornGear.wear(p, "bracelet", ItemStack.EMPTY);

            // the talon: a blow from behind
            put(p, "hands", "dodge_talon");
            Zombie behind = zombie(level, made, p, 0, -2);
            boolean dodged = strike(p, p.damageSources().mobAttack(behind), 6F);
            r.put("talon_dodged", dodged);
            r.put("talon_moved", Math.round(Math.sqrt(p.distanceToSqr(at.getX() + 0.5, at.getY(), at.getZ() + 0.5)) * 10) / 10.0);
            r.put("talon_recharging", p.getCooldowns().isOnCooldown(WornGear.item("dodge_talon")));
            WornGear.wear(p, "hands", ItemStack.EMPTY);

            // the banner: struck in a fight
            put(p, "back", "squad_banner");
            boolean hurt = !strike(p, p.damageSources().mobAttack(behind), 3F);
            r.put("banner_rallied", hurt && p.hasEffect(MobEffects.DAMAGE_BOOST) && p.hasEffect(MobEffects.DAMAGE_RESISTANCE));
            r.put("banner_recharging", p.getCooldowns().isOnCooldown(WornGear.item("squad_banner")));

            // the bloom, then the talisman: a blow that would kill
            put(p, "head", "last_bloom");
            put(p, "necklace", "rewind_talisman");
            p.setHealth(10F);
            boolean bloomSaved = strike(p, p.damageSources().generic(), 1000F);
            r.put("bloom_saved", bloomSaved && p.getHealth() >= 11.9F);
            r.put("bloom_recharging", p.getCooldowns().isOnCooldown(WornGear.item("last_bloom")));
            p.setHealth(10F);
            boolean talismanSaved = strike(p, p.damageSources().generic(), 1000F);
            r.put("talisman_saved", talismanSaved && p.getHealth() >= p.getMaxHealth() - 0.1F);
            r.put("talisman_spent", WornGear.worn(p, WornGear.item("rewind_talisman")).isEmpty());

            // the King's token round the neck
            ItemStack token = new ItemStack(WornGear.item("villager_king_token"));
            CompoundTag t = new CompoundTag();
            t.putInt("LivesDefeated", 4);
            token.set(DataComponents.CUSTOM_DATA, CustomData.of(t));
            WornGear.wear(p, "necklace", token);
            p.tickCount = 40;
            WornGear.tick(new PlayerTickEvent.Post(p));
            r.put("token_hero", p.hasEffect(MobEffects.HERO_OF_THE_VILLAGE));

            pass = WornGear.CURIOS && fits.values().stream().allMatch(b -> b) && parried && (boolean) r.get("emblem_answered") && dodged
                && (boolean) r.get("banner_rallied") && (boolean) r.get("bloom_saved") && (boolean) r.get("talisman_saved")
                && (boolean) r.get("talisman_spent") && (boolean) r.get("token_hero");
        } catch (RuntimeException ex) {
            r.put("error", String.valueOf(ex));
            LOG.error("WORN-ERROR", ex);
        } finally {
            for (Zombie z : made) {
                z.discard();
            }
        }
        r.put("pass", pass);
        LOG.info("WORN-RESULT {}", json(r));
        resultLogged = true;
        return 1;
    }

    private static void put(FakePlayer p, String slot, String id) {
        WornGear.wear(p, slot, new ItemStack(WornGear.item(id)));
    }

    private static Zombie zombie(ServerLevel level, List<Zombie> made, FakePlayer p, double dx, double dz) {
        Zombie z = EntityType.ZOMBIE.create(level);
        z.moveTo(p.getX() + dx, p.getY(), p.getZ() + dz, 0F, 0F);
        z.setNoAi(true);
        z.setPersistenceRequired();
        level.addFreshEntity(z);
        made.add(z);
        return z;
    }

    /** A blow as the game hands it to the handlers; true if it was turned aside (cancelled). */
    private static boolean strike(FakePlayer p, DamageSource src, float amount) {
        LivingIncomingDamageEvent ev = new LivingIncomingDamageEvent(p, new DamageContainer(src, amount));
        WornGear.hurt(ev);
        return ev.isCanceled();
    }

    private static String json(Map<String, Object> m) {
        StringBuilder b = new StringBuilder("{");
        for (Map.Entry<String, Object> en : m.entrySet()) {
            if (b.length() > 1) {
                b.append(',');
            }
            b.append('"').append(en.getKey()).append("\":");
            Object v = en.getValue();
            if (v instanceof Map<?, ?> sub) {
                StringBuilder s = new StringBuilder("{");
                for (Map.Entry<?, ?> x : sub.entrySet()) {
                    if (s.length() > 1) {
                        s.append(',');
                    }
                    s.append('"').append(x.getKey()).append("\":").append(x.getValue());
                }
                b.append(s).append('}');
            } else if (v instanceof List<?> l) {
                b.append('[');
                for (int i = 0; i < l.size(); i++) {
                    b.append(i > 0 ? "," : "").append('"').append(l.get(i)).append('"');
                }
                b.append(']');
            } else if (v instanceof String s) {
                b.append('"').append(s.replace("\"", "'")).append('"');
            } else {
                b.append(v);
            }
        }
        return b.append('}').toString();
    }
}
