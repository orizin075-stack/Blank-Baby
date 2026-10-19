package jp.oror.reborn;

import java.util.Set;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;

public final class LorePowers {
    public static final Set<String> ABSOLUTE = Set.of("riha", "tenki", "nortia", "demiurgos", "miyohime", "innocence", "ain_sof_aur", "arcana");
    public static final Set<String> IMMORTAL = Set.of(
        "kokuhaku",
        "riha",
        "tenki",
        "chaos",
        "mels",
        "hephaistos",
        "nortia",
        "mary_sue",
        "huang_linghua",
        "yggdrasil",
        "miyohime",
        "ouroboros",
        "ain_sof_aur",
        "angra_mainyu",
        "hakyoku",
        "demiurgos",
        "innocence",
        "brutality",
        "cursed_love",
        "relentless_research",
        "forbidden_arcana",
        "fallen_savior",
        "sweet_pact",
        "magna_mater",
        "kurma"
    );

    public static boolean timeIndependent(SupremeEntity b) {
        return b.lore() && (ABSOLUTE.contains(b.spec.id) || Set.of("teia", "ouroboros", "hakyoku", "forbidden_arcana").contains(b.spec.id));
    }

    public static void grow(SupremeEntity b) {
        if (b.loreEvolution < Long.MAX_VALUE) {
            b.loreEvolution++;
        }
    }

    public static float incoming(SupremeEntity b, DamageSource source, float amount, String kind) {
        if (!b.lore()) {
            return amount;
        } else {
            boolean learned = b.loreAdaptation.contains(kind);
            b.loreAdaptation.add(kind);
            grow(b);
            if (ABSOLUTE.contains(b.spec.id) || b.spec.id.equals("kokuhaku") && source.getEntity() != null) {
                if (source.getDirectEntity() instanceof Projectile p) {
                    p.discard();
                }

                return 0.0F;
            } else if (Set.of("hakyoku", "forbidden_arcana", "valeria", "relentless_research").contains(b.spec.id) && learned) {
                return 0.0F;
            } else if (b.spec.id.equals("shinra") && source.getEntity() instanceof LivingEntity t) {
                b.targetSpecies = BuiltInRegistries.ENTITY_TYPE.getKey(t.getType()).toString();
                return 0.0F;
            } else if (b.spec.id.equals("mels")) {
                return amount * 0.001F;
            } else if (b.spec.id.equals("kurma")) {
                return amount * 1.0E-4F;
            } else if (b.spec.id.equals("ouroboros")) {
                b.rewind();
                return 0.0F;
            } else if (b.spec.id.equals("taika")) {
                b.heal(b.getMaxHealth());
                return Math.min(amount, b.getMaxHealth() * 0.01F);
            } else {
                return amount;
            }
        }
    }

    public static void strike(SupremeEntity b, LivingEntity t, float ordinary, boolean erasure) {
        if (b.validEnemy(t)) {
            if (!b.lore()) {
                t.hurt(b.damageSources().mobAttack(b), ordinary);
            } else if (!erasure || t instanceof SupremeEntity) {
                t.hurt(
                    b.damageSources().mobAttack(b),
                    (float)Math.min(8.5070587E37F, Math.max((double)ordinary, 1000000.0 * (1.0 + Math.log1p((double)b.loreEvolution)) * MobMind.strength(b)))
                );
            } else if (!RelicPowers.shielded(t)) {
                if (t.level()
                        .getEntitiesOfClass(
                            SupremeEntity.class,
                            t.getBoundingBox().inflate(8.0),
                            guard -> guard.spec.id.equals("savior") && guard.lore() && guard.isAlive() && !guard.isNoAi() && guard.ally(t)
                        )
                        .size()
                    <= 0) {
                    ResourceKey<DamageType> key = ResourceKey.create(
                        Registries.DAMAGE_TYPE, new ResourceLocation("oror_supreme_bosses", "erasure")
                    );
                    DamageSource source = new DamageSource(t.level().registryAccess().registryOrThrow(Registries.DAMAGE_TYPE).getHolderOrThrow(key), b);
                    t.getPersistentData().putBoolean("ororErased", true);
                    float amount = (float)Math.min(8.5070587E37F, Math.max(1000000.0, (double)t.getMaxHealth() * 1024.0));
                    t.hurt(source, amount);
                }
            }
        }
    }

    public static void cast(SupremeEntity b, LivingEntity t) {
        if (b.lore()) {
            grow(b);
            DivineDomains.begin(b);
            String var2 = b.spec.id;
            switch (var2) {
                case "kokuhaku":
                case "tenki":
                case "demiurgos":
                case "shinra":
                case "miyohime":
                case "fallen_savior":
                    strike(b, t, 1.0F, true);
                    break;
                case "riha":
                    if (b.tickCount / b.spec.cooldown % 4 == 3) {
                        strike(b, t, 1.0F, true);
                    }
                    break;
                case "hakyoku":
                case "taika":
                case "mels":
                case "brutality":
                case "elseria":
                case "merlinus":
                case "forbidden_arcana":
                case "enkou":
                case "teia":
                    strike(b, t, 1.0F, false);
                    break;
                case "mary_sue":
                    b.heal(b.getMaxHealth());
                    b.shield = 500.0F;
                    break;
                case "chaos":
                case "berit":
                case "nun":
                    t.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 200, 10));
                    t.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 80, 2));
                    break;
                case "cursed_love":
                case "gokuka":
                case "angra_mainyu":
                    t.addEffect(new MobEffectInstance(MobEffects.WITHER, 200, 10));
                    break;
                default:
                    b.shield = Math.max(300.0F, b.shield);
            }
        }
    }
}
