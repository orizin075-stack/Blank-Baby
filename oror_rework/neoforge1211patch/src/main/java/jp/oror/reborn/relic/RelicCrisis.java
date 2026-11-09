package jp.oror.reborn.relic;

import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.RelicArts;
import jp.oror.reborn.RelicPowers;
import jp.oror.reborn.RelicSpec;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;

/**
 * (058) The charms' crisis guard (V9 危機対応能力), working by itself while the charm is worn: five kinds, as the design
 * gives each god's charm.
 *
 * <ul>
 * <li>counter: at 35% health, or just before a great blow (30% of the wearer's maximum at once), that blow cut by 90%,
 * 25% of health back, the blow returned and its maker's strengths undone once, and 4 s in which the next blow lands
 * twice as hard. 65 s.</li>
 * <li>brand: hurt to 40%: 75% cut for 3 s, 35% back, the attacker branded 4 s (its blows weakened, slowed). 80 s.</li>
 * <li>repel: at 35%: 80% cut for 3.5 s, 45% back, those close thrown back and struck once. 75 s; never again within.</li>
 * <li>repair: at 35%: up to four repair units set out, 40% back, 80% cut for 6 s. 90 s.</li>
 * <li>rescue: the wearer or a friend within 20 blocks at 30%: that one 65% back and 85% cut for 5 s. 90 s, shared by
 * every rescue charm the wearer has; no one already dead is brought back.</li>
 * </ul>
 * A wearer is one with the charm on (its Curios slot ticks it) or in a hand. The cooldowns are by kind, so two charms of
 * one kind share it (the design's 同系加護では共有CD).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class RelicCrisis {
    public static int fired;
    public static final List<String> LOG = new ArrayList<>();

    private RelicCrisis() {
    }

    /** The charm this player wears (or holds), if any, with its V9 guard. */
    static RelicV9.Info charm(Player p) {
        CompoundTag d = p.getPersistentData();
        String id = null;
        if (p.level().getGameTime() - d.getLong("ororWornCharmAt") <= 40) {
            id = d.getString("ororWornCharm");
        }
        for (var stack : List.of(p.getMainHandItem(), p.getOffhandItem())) {
            RelicSpec s = CharacterRelics.of(stack);
            if (s != null && s.slot.equals("charm")) {
                id = s.id;
            }
        }
        RelicV9.Info i = RelicV9.info(id);
        return i != null && i.crisis != null ? i : null;
    }

    private static boolean ready(Player p, String kind, long now) {
        return now >= p.getPersistentData().getLong("ororCrisisNext_" + kind);
    }

    private static void spend(Player p, String kind, long now, JsonObject c) {
        p.getPersistentData().putLong("ororCrisisNext_" + kind, now + c.get("cd").getAsLong());
    }

    @SubscribeEvent(priority = EventPriority.LOW)
    public static void incoming(LivingIncomingDamageEvent e) {
        LivingEntity v = e.getEntity();
        if (!(v.level() instanceof ServerLevel sl) || e.getAmount() <= 0.0F) {
            return;
        }
        long now = sl.getGameTime();
        if (v instanceof Player p) {
            RelicV9.Info info = charm(p);
            if (info != null && !info.crisis.get("k").getAsString().equals("rescue")) {
                guard(e, p, info, sl, now);
                return;
            }
        }
        // a rescue charm guards its wearer and the friends about it
        if (v instanceof Player || v.getPersistentData().hasUUID("ororRelicOwner")) {
            for (Player p : sl.getEntitiesOfClass(Player.class, v.getBoundingBox().inflate(20.0), q -> q == v || !RelicPowers.enemy(q, v))) {
                RelicV9.Info info = charm(p);
                if (info != null && info.crisis.get("k").getAsString().equals("rescue")) {
                    rescue(e, p, v, info, sl, now);
                    return;
                }
            }
        }
    }

    private static void guard(LivingIncomingDamageEvent e, Player p, RelicV9.Info info, ServerLevel sl, long now) {
        JsonObject c = info.crisis;
        String kind = c.get("k").getAsString();
        if (!ready(p, kind, now)) {
            return;
        }
        float after = p.getHealth() - e.getAmount();
        boolean low = after <= p.getMaxHealth() * c.get("hp").getAsFloat();
        boolean big = kind.equals("counter") && e.getAmount() >= p.getMaxHealth() * c.get("big").getAsFloat();
        if (!low && !big) {
            return;
        }
        spend(p, kind, now, c);
        fired++;
        LOG.add(info.id + " " + kind + " at " + now);
        Entity src = e.getSource().getEntity();
        int colour = colour(info);
        switch (kind) {
            case "counter" -> {
                e.setAmount(e.getAmount() * (1.0F - c.get("cut").getAsFloat()));
                p.heal(p.getMaxHealth() * c.get("heal").getAsFloat());
                if (src instanceof LivingEntity att && att != p) {
                    // the blow's way back: struck and its strengths undone
                    RelicArts.quiet(() -> {
                        att.invulnerableTime = 0;
                        att.hurt(p.damageSources().playerAttack(p), Math.max(40.0F, e.getAmount() * 2.0F) + 6000.0F);
                    });
                    new ArrayList<>(att.getActiveEffects()).stream().filter(m -> m.getEffect().value().isBeneficial()).forEach(m -> att.removeEffect(m.getEffect()));
                    RelicFx.send(p, 0, colour, att.position().add(0, att.getBbHeight() * 0.5, 0), att.position().subtract(p.position()).normalize(), 2.5F,
                        10, 30, 0, "");
                }
                RelicTech.window(p, "ororTechNext", now + c.get("window").getAsLong(), 2.0F);
            }
            case "brand" -> {
                RelicTech.window(p, "ororTechReduce", now + c.get("span").getAsLong(), c.get("cut").getAsFloat());
                e.setAmount(e.getAmount() * (1.0F - c.get("cut").getAsFloat()));
                p.heal(p.getMaxHealth() * c.get("heal").getAsFloat());
                if (src instanceof LivingEntity att && att != p) {
                    int t = c.get("brand").getAsInt();
                    RelicTech.Mods.add(att, net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE, "brand", -0.5, t);
                    att.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, t, 2));
                    att.addEffect(new MobEffectInstance(MobEffects.GLOWING, t, 0));
                    RelicFx.send(p, 4, colour, att.position().add(0, att.getBbHeight() + 0.2, 0), new Vec3(0, 1, 0), 1.2F, t, 1.0F, 0, "");
                }
            }
            case "repel" -> {
                RelicTech.window(p, "ororTechReduce", now + c.get("span").getAsLong(), c.get("cut").getAsFloat());
                e.setAmount(e.getAmount() * (1.0F - c.get("cut").getAsFloat()));
                p.heal(p.getMaxHealth() * c.get("heal").getAsFloat());
                for (LivingEntity f : RelicArts.near(p, p.position(), 6.0)) {
                    RelicArts.quiet(() -> {
                        f.invulnerableTime = 0;
                        f.hurt(p.damageSources().playerAttack(p), 6000.0F);
                    });
                    RelicArts.push(f, RelicArts.flat(f.position().subtract(p.position())).scale(2.2).add(0, 0.5, 0));
                }
                RelicFx.send(p, 3, colour, p.position().add(0, 0.1, 0), new Vec3(0, 1, 0), 6.0F, 12, 0, 0, "");
            }
            case "repair" -> {
                RelicTech.window(p, "ororTechReduce", now + c.get("span").getAsLong(), c.get("cut").getAsFloat());
                e.setAmount(e.getAmount() * (1.0F - c.get("cut").getAsFloat()));
                p.heal(p.getMaxHealth() * c.get("heal").getAsFloat());
                RelicWorld.place(p, info.id, "vine", c.get("units").getAsInt(), 120, 120.0F, 0.0F, 0.0F, 20, 4.0, 0.03F, colour);
            }
            default -> {
            }
        }
        RelicFx.send(p, 9, colour, p.position().add(0, 1.0, 0), new Vec3(0, 1, 0), 1.8F, 20, 0, 0, "");
        sl.playSound(null, p.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.7F, 1.4F);
        p.displayClientMessage(Component.literal(info.name + "：危機対応").withStyle(ChatFormatting.GOLD), true);
    }

    private static void rescue(LivingIncomingDamageEvent e, Player wearer, LivingEntity v, RelicV9.Info info, ServerLevel sl, long now) {
        JsonObject c = info.crisis;
        if (!ready(wearer, "rescue", now) || v.getHealth() - e.getAmount() > v.getMaxHealth() * c.get("hp").getAsFloat() || !v.isAlive()) {
            return;
        }
        spend(wearer, "rescue", now, c);
        fired++;
        LOG.add(info.id + " rescue " + (v == wearer ? "self" : "friend") + " at " + now);
        RelicTech.window(v, "ororTechReduce", now + c.get("span").getAsLong(), c.get("cut").getAsFloat());
        e.setAmount(e.getAmount() * (1.0F - c.get("cut").getAsFloat()));
        v.heal(v.getMaxHealth() * c.get("heal").getAsFloat());
        int colour = colour(info);
        RelicFx.send(wearer, 5, colour, v.position(), new Vec3(0, 1, 0), 1.2F, 24, 0, 8.0F, "");
        RelicFx.send(wearer, 9, colour, v.position().add(0, 1.0, 0), new Vec3(0, 1, 0), 1.6F, 30, 0, 0, "");
        sl.playSound(null, v.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.7F, 1.6F);
        wearer.displayClientMessage(Component.literal(info.name + "：救済").withStyle(ChatFormatting.GOLD), true);
    }

    private static int colour(RelicV9.Info info) {
        RelicSpec s = RelicSpec.ALL.get(info.id);
        return s != null ? s.color : 0xFFFFFF;
    }
}
