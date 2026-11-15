package jp.oror.reborn;

import jp.oror.reborn.raid.RaidTable;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRole;

/**
 * (059g, the user: "それぞれ１０００００ぐらいにして　上限なんて関係ない　攻撃力も１０～５０倍に") The 41 gods: 100,000 health each
 * (their own was 600 to 1,024, Minecraft's cap; MaxHealthCapMixin lifts it), and what they deal ten to fifty times what it
 * was: by the god's place in the user's raid table (RaidTable's times, ten to a hundred), ten times for the least of them
 * (Kurma) up to fifty for the greatest (Miyohime, the Omnipotent Innocence). Their raid health (RaidTable) is 100,000 too.
 * <p>(the user: "村人王は１００００くらい　以下も魔導士から５～１０倍くらいに") The kingdom too: the villager king 10,000 health (his
 * blows were 1,024 already), and below him health and blows five to ten times what they were, by rank: a general ten, the
 * imperial guard nine, a bodyguard eight, the sage seven, an archmage six, a court mage and a kingdom guard five.</p>
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class GodStrength {
    public static final double HEALTH = 100_000;
    static final ResourceLocation GOD_HEALTH = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "god_health");
    private static final String FULL = "OrorGodFull";

    private GodStrength() {
    }

    public static final double KING_HEALTH = 10_000;

    /** A royal's health and blows multiplied by (the king's health is set to 10,000, his blows as they were). */
    public static double royalTimes(RoyalRole r) {
        return switch (r) {
            case KING -> 1.0;
            case GENERAL -> 10.0;
            case IMPERIAL -> 9.0;
            case BODYGUARD -> 8.0;
            case SAGE -> 7.0;
            case ARCHMAGE -> 6.0;
            case MAGE, GUARD -> 5.0;
        };
    }

    /** A royal's health: the king 10,000, the rest five to ten times their own (a lasting modifier over their own). */
    static void harden(RoyalMob m) {
        AttributeInstance hp = m.getAttribute(Attributes.MAX_HEALTH);
        if (hp == null || m.role() == null) {
            return;
        }
        double base = hp.getBaseValue();
        double add = m.role() == RoyalRole.KING ? KING_HEALTH - base : base * (royalTimes(m.role()) - 1.0);
        AttributeModifier have = hp.getModifier(GOD_HEALTH);
        if (have == null || Math.abs(have.amount() - add) > 0.5) {
            hp.removeModifier(GOD_HEALTH);
            if (add > 0) {
                hp.addPermanentModifier(new AttributeModifier(GOD_HEALTH, add, AttributeModifier.Operation.ADD_VALUE));
            }
        }
    }

    /** What a god's blows are multiplied by: ten to fifty, by its raid table times (ten to a hundred). */
    public static double damageTimes(String id) {
        RaidTable.Entry e = RaidTable.ALL.get(id);
        int times = e == null ? 30 : e.times();
        return 10.0 + 40.0 * Math.max(0, Math.min(90, times - 10)) / 90.0;
    }

    /** A god's health made 100,000 (a lasting modifier over its own, so its own may change under it). */
    static void harden(SupremeEntity b) {
        AttributeInstance hp = b.getAttribute(Attributes.MAX_HEALTH);
        if (hp == null) {
            return;
        }
        double add = HEALTH - hp.getBaseValue();
        AttributeModifier have = hp.getModifier(GOD_HEALTH);
        if (have == null || Math.abs(have.amount() - add) > 0.5) {
            hp.removeModifier(GOD_HEALTH);
            if (add > 0) {
                hp.addPermanentModifier(new AttributeModifier(GOD_HEALTH, add, AttributeModifier.Operation.ADD_VALUE));
            }
        }
    }

    @SubscribeEvent
    public static void joined(EntityJoinLevelEvent e) {
        if (e.getLevel() instanceof ServerLevel && e.getEntity() instanceof SupremeEntity b) {
            harden(b);
        } else if (e.getLevel() instanceof ServerLevel && e.getEntity() instanceof RoyalMob m) {
            harden(m);
        }
    }

    /** The first tick of a god new to the world: whole at its 100,000 (its spawning set its own health). */
    @SubscribeEvent
    public static void tick(EntityTickEvent.Post e) {
        if (e.getEntity() instanceof SupremeEntity b && !b.level().isClientSide && !b.getPersistentData().getBoolean(FULL)) {
            harden(b);
            b.setHealth(b.getMaxHealth());
            b.getPersistentData().putBoolean(FULL, true);
        } else if (e.getEntity() instanceof RoyalMob m && !m.level().isClientSide && !m.getPersistentData().getBoolean(FULL)) {
            harden(m);
            m.setHealth(m.getMaxHealth());
            m.getPersistentData().putBoolean(FULL, true);
        }
    }

    /** A god's blow (its own, its spells', its shots': whatever it is the cause of) ten to fifty times as hard. */
    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void hurt(LivingIncomingDamageEvent e) {
        Entity by = e.getSource().getEntity();
        if (by instanceof SupremeEntity b && b != e.getEntity() && b.spec != null) {
            e.setAmount((float) (e.getAmount() * damageTimes(b.spec.id)));
        } else if (by instanceof RoyalMob m && m != e.getEntity() && m.role() != null && m.role() != RoyalRole.KING) {
            e.setAmount((float) (e.getAmount() * royalTimes(m.role())));
        }
    }
}
