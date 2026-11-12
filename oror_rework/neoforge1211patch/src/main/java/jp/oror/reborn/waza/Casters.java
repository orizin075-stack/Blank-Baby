package jp.oror.reborn.waza;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import jp.oror.reborn.FamiliarEntity;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Vex;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * (059c) Who casts the techniques, and what the engine asks of a caster. Until 059b only the 41 characters
 * (SupremeEntity) did; now also the Villager King, his four forms' new actions of V20 (03_king_4_forms.md: king1..king4),
 * and Azazel (04_azazel.md: azazel2, azazel3, azazel_coop). The characters answer for themselves; the king and Azazel are
 * answered here: their foes and friends as their own code reckons them (KingForms.foe, AzazelArts.foe), their blows'
 * weight from V20's own number for each action (its 仮基準威力) grown with the king's form, their summons from their own
 * people (the king's guards, Azazel's vexes).
 */
public final class Casters {
    /** V20's own weight of a royal action (by technique id): its 仮基準威力 / 提案の追加威力指定. */
    static final Map<String, Float> POWER = new HashMap<>();
    public static final String KING_FORM = "OrorWazaKingForm";
    public static final String SUMMONED_BY = "OrorWazaSummoner";

    private Casters() {
    }

    /** The technique book this caster draws from (Waza.BY_CHARACTER's key), or null. */
    public static String character(Mob b) {
        if (b instanceof SupremeEntity s) {
            return s.spec == null ? null : s.spec.id;
        }
        if (b instanceof RoyalMob r && r.getPersistentData().contains(KING_FORM)) {
            return "king" + (r.getPersistentData().getInt(KING_FORM) + 1);
        }
        if (jp.oror.reborn.king.AzazelArts.isAzazel(b)) {
            // against the king himself, his six made for that fight (04_azazel.md 対村人王専用連携) a third of the time
            if (b.getTarget() instanceof RoyalMob k && k.getPersistentData().contains(KING_FORM) && (b.level().getGameTime() / 100) % 3 == 0) {
                return "azazel_coop";
            }
            return b.getHealth() > b.getMaxHealth() * 0.5F ? "azazel2" : "azazel3";
        }
        return null;
    }

    public static boolean validEnemy(Mob b, LivingEntity t) {
        if (t == null || t == b || !t.isAlive()) {
            return false;
        }
        if (b instanceof SupremeEntity s) {
            return s.validEnemy(t);
        }
        if (b instanceof RoyalMob r && r.getPersistentData().contains(KING_FORM)) {
            return jp.oror.reborn.king.KingForms.foe(r, t);
        }
        if (jp.oror.reborn.king.AzazelArts.isAzazel(b)) {
            return jp.oror.reborn.king.AzazelArts.isFoe(b, t);
        }
        return t == b.getTarget();
    }

    public static boolean ally(Mob b, LivingEntity t) {
        if (t == null || t == b) {
            return t == b;
        }
        if (b instanceof SupremeEntity s) {
            return s.ally(t);
        }
        if (summoner(t) == b.getId()) {
            return true;
        }
        if (b instanceof RoyalMob) {
            return t instanceof RoyalMob || t instanceof net.minecraft.world.entity.npc.AbstractVillager
                || t instanceof net.minecraft.world.entity.animal.IronGolem;
        }
        if (jp.oror.reborn.king.AzazelArts.isAzazel(b)) {
            return !validEnemy(b, t) && !(t instanceof Player);
        }
        return false;
    }

    public static boolean airborne(Mob b) {
        return b instanceof SupremeEntity s ? s.spec.airborne() : jp.oror.reborn.king.AzazelArts.isAzazel(b);
    }

    public static boolean aquatic(Mob b) {
        return b instanceof SupremeEntity s && s.spec.aquatic();
    }

    public static boolean lore(Mob b) {
        return b instanceof SupremeEntity s && s.lore();
    }

    /** What the caster has seen of its foes' ways (the characters' learning): only the characters remember. */
    public static Map<String, Integer> memory(Mob b) {
        return b instanceof SupremeEntity s ? s.memory.entries() : Map.of();
    }

    /** A technique's whole damage. The characters' as 057 made it; a royal action's V20 weight, greater in each form. */
    public static float whole(Mob b, Waza w, float tierFactor) {
        if (b instanceof SupremeEntity) {
            return (float) (b.getAttributeValue(Attributes.ATTACK_DAMAGE) * jp.oror.reborn.RebornConfig.DAMAGE.get() * tierFactor);
        }
        float p = POWER.getOrDefault(w.id(), 16F);
        int form = b.getPersistentData().getInt(KING_FORM);
        return p * (b instanceof RoyalMob ? 1.0F + 0.5F * form : 1.2F) * (0.8F + 0.2F * w.tier());
    }

    public static int summoner(net.minecraft.world.entity.Entity e) {
        return e.getPersistentData().contains(SUMMONED_BY) ? e.getPersistentData().getInt(SUMMONED_BY) : -1;
    }

    /** n helpers: the characters' familiars of the style; the king's guards; Azazel's vexes. Returns those made. */
    public static List<Mob> summon(Mob b, ServerLevel sl, int style, int n) {
        List<Mob> made = new java.util.ArrayList<>();
        if (b instanceof SupremeEntity s) {
            java.util.Set<java.util.UUID> before = new java.util.HashSet<>();
            for (FamiliarEntity f : sl.getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(16))) {
                before.add(f.getUUID());
            }
            FamiliarEntity.create(s, sl, style, n);
            for (FamiliarEntity f : sl.getEntitiesOfClass(FamiliarEntity.class, b.getBoundingBox().inflate(16))) {
                if (!before.contains(f.getUUID()) && b.getUUID().equals(f.creator)) {
                    made.add(f);
                }
            }
            return made;
        }
        for (int i = 0; i < n; i++) {
            double a = Math.PI * 2 * i / Math.max(1, n) + b.getRandom().nextDouble() * 0.4;
            Vec3 at = b.position().add(Math.cos(a) * 2.5, 0.2, Math.sin(a) * 2.5);
            Mob m;
            if (b instanceof RoyalMob) {
                EntityType<?> type = net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.get(
                    net.minecraft.resources.ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "kingdom_guard"));
                if (!(type.create(sl) instanceof Mob guard)) {
                    continue;
                }
                m = guard;
            } else {
                Vex v = EntityType.VEX.create(sl);
                if (v == null) {
                    continue;
                }
                v.setOwner(b);
                v.setLimitedLife(20 * 30);
                m = v;
            }
            m.moveTo(at.x, at.y, at.z, b.getYRot(), 0);
            m.finalizeSpawn(sl, sl.getCurrentDifficultyAt(m.blockPosition()), MobSpawnType.MOB_SUMMONED, null);
            m.getPersistentData().putInt(SUMMONED_BY, b.getId());
            m.addTag("oror_waza");
            if (b.getTarget() != null && validEnemy(b, b.getTarget())) {
                m.setTarget(b.getTarget());
            }
            if (sl.addFreshEntity(m)) {
                made.add(m);
            }
        }
        return made;
    }
}
