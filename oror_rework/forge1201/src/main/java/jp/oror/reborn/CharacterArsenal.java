package jp.oror.reborn;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingHealEvent;
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent;

public final class CharacterArsenal {
    public static final Map<String, List<CharacterArsenal.Skill>> ALL = load();

    private static Map<String, List<CharacterArsenal.Skill>> load() {
        try {
            Map var2;
            try (InputStream in = CharacterArsenal.class.getResourceAsStream("/assets/oror_supreme_bosses/arsenal.json")) {
                if (in == null) {
                    throw new IllegalStateException("Missing arsenal");
                }

                Map<String, List<CharacterArsenal.Skill>> result = (Map<String, List<CharacterArsenal.Skill>>)new Gson()
                    .fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), (new TypeToken<Map<String, List<CharacterArsenal.Skill>>>() {
                    }).getType());
                if (!result.keySet().equals(CharacterSpec.ALL.keySet()) || result.values().stream().anyMatch(s -> s.size() != 3)) {
                    throw new IllegalStateException("Arsenal roster mismatch");
                }

                var2 = Collections.unmodifiableMap(result);
            }

            return var2;
        } catch (IOException var5) {
            throw new ExceptionInInitializerError(var5);
        }
    }

    public static int baseMotion(SupremeEntity b) {
        if (Abilities.melee(b.spec.id)) {
            return b.spec.id.equals("mels") ? 4 : (!b.spec.id.equals("taika") && !b.spec.id.equals("brutality") ? 1 : 3);
        } else if (!b.spec.airborne() && !b.spec.aquatic()) {
            return !b.spec.id.equals("riha") && !b.spec.id.equals("nortia") ? 8 : 9;
        } else {
            return 14;
        }
    }

    public static boolean cast(SupremeEntity b, ServerLevel sl, LivingEntity target, int index) {
        if ((Boolean)RebornConfig.EXTRA_ABILITIES.get() && b.validEnemy(target)) {
            CharacterArsenal.Skill skill = ALL.get(b.spec.id).get(Math.floorMod(index, 3));
            if (b.lore() && b.mana() < (float)skill.cost) {
                b.mana((float)skill.cost);
            }

            if (!b.spend((float)skill.cost)) {
                return false;
            } else {
                b.motion(skill.motion, 24);
                CompoundTag n = b.getPersistentData();
                n.putString("OrorLastTechnique", skill.name);
                n.putInt("OrorExtraCasts", n.getInt("OrorExtraCasts") + 1);
                List<LivingEntity> targets = Abilities.enemies(b, 18.0);
                String var7 = skill.mechanic;
                switch (var7) {
                    case "SLASH":
                        Vec3 toward = target.position().subtract(b.position()).normalize();
                        Abilities.blink(b, target.position().subtract(toward.scale(2.0)));
                        strike(b, target, 2.0F, false);
                        b.swing(InteractionHand.MAIN_HAND);
                        break;
                    case "ERASE":
                        strike(b, target, 3.0F, true);
                        break;
                    case "BURST": {
                        for (LivingEntity foe : targets) {
                            strike(b, foe, 1.2F, false);
                            Vec3 d = foe.position().subtract(b.position()).normalize();
                            foe.setDeltaMovement(d.scale(1.4).add(0.0, 0.45, 0.0));
                            foe.hurtMarked = true;
                        }
                        break;
                    }
                    case "BARRAGE": {
                        CompoundTag t = target.getPersistentData();
                        t.putUUID("OrorBarrageSource", b.getUUID());
                        t.putInt("OrorBarrageRemaining", b.spec.id.equals("mels") ? 100 : 12);
                        t.putLong("OrorBarrageNext", sl.getGameTime() + 2L);
                        strike(b, target, 0.5F, false);
                        break;
                    }
                    case "SEAL": {
                        for (LivingEntity foe : targets) {
                            Abilities.stun(foe, 60);
                            foe.getPersistentData().putLong("OrorSilencedUntil", sl.getGameTime() + 80L);
                            foe.getPersistentData().putLong("OrorHealLockedUntil", sl.getGameTime() + 60L);
                        }
                        break;
                    }
                    case "HEAL":
                    case "FATE":
                        b.heal(60.0F);
                        b.healAllies(40.0F);
                        b.shield = Math.max(120.0F, b.shield);

                        for (LivingEntity friend : sl.getEntitiesOfClass(LivingEntity.class, b.getBoundingBox().inflate(12.0), b::ally)) {
                            RelicPowers.cleanse(friend);
                            if (skill.mechanic.equals("FATE")) {
                                friend.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 100, 3));
                            }
                        }
                        break;
                    case "GUARD":
                        b.shield = Math.max(180.0F, b.shield);

                        for (LivingEntity friend : sl.getEntitiesOfClass(LivingEntity.class, b.getBoundingBox().inflate(12.0), b::ally)) {
                            friend.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 120, 2));
                        }
                        break;
                    case "DRAIN":
                        float before = target.getHealth();
                        strike(b, target, 1.0F, false);
                        b.heal(Math.max(4.0F, before - target.getHealth()));
                        b.mana(b.mana() + 20.0F);
                        target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 2));
                        break;
                    case "REFLECT":
                        for (Projectile px : sl.getEntitiesOfClass(
                            Projectile.class,
                            b.getBoundingBox().inflate(14.0),
                            pxx -> pxx.getOwner() != b && (!(pxx.getOwner() instanceof LivingEntity a) || !b.ally(a))
                        )) {
                            px.setOwner(b);
                            px.setDeltaMovement(px.getDeltaMovement().scale(-1.0));
                            px.hasImpulse = true;
                        }

                        b.shield = Math.max(50.0F, b.shield);
                        break;
                    case "SUMMON":
                        FamiliarEntity.create(
                            b,
                            sl,
                            b.spec.id.equals("gokuka") ? 3 : (!b.spec.id.equals("eomaia") && !b.spec.id.equals("magna_mater") ? Math.floorMod(index, 3) : 1),
                            2
                        );
                        b.shield = Math.max(30.0F, b.shield);
                        break;
                    case "REPAIR":
                        for (ItemStack item : b.getAllSlots()) {
                            if (item.isDamageableItem()) {
                                item.setDamageValue(Math.max(0, item.getDamageValue() - 40));
                            }
                        }

                        if (b.owner != null && sl.getEntity(b.owner) instanceof LivingEntity owner && b.distanceToSqr(owner) < 144.0) {
                            for (ItemStack itemx : owner.getAllSlots()) {
                                if (itemx.isDamageableItem()) {
                                    itemx.setDamageValue(Math.max(0, itemx.getDamageValue() - 40));
                                }
                            }
                        }

                        b.shield = Math.max(40.0F, b.shield);
                        break;
                    case "MANA":
                        b.mana(b.mana() + 100.0F);

                        for (SupremeEntity friend : sl.getEntitiesOfClass(SupremeEntity.class, b.getBoundingBox().inflate(16.0), b::ally)) {
                            friend.mana(friend.mana() + 50.0F);
                        }
                        break;
                    case "ADAPT":
                        b.evolution = CombatMemory.boundedEvolution(b.evolution + 2);
                        LorePowers.grow(b);
                        b.memory.observe("arsenal:" + target.getType().toShortString());
                        b.shield = Math.max(100.0F, b.shield);
                        b.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 120, 2));
                        break;
                    case "COPY":
                        b.setForm(b.form() + 1);
                        if (!target.getMainHandItem().isEmpty() && !b.spec.id.equals("kokuhaku")) {
                            b.setItemInHand(InteractionHand.MAIN_HAND, target.getMainHandItem().copyWithCount(1));
                            b.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
                        }

                        b.targetSpecies = BuiltInRegistries.ENTITY_TYPE.getKey(target.getType()).toString();
                        b.shield = Math.max(80.0F, b.shield);
                        break;
                    case "REWIND":
                        b.rewind();
                        b.heal(30.0F);
                        CompoundTag t = target.getPersistentData();
                        if (t.contains("OrorRecallPos")) {
                            BlockPos p = BlockPos.of(t.getLong("OrorRecallPos"));
                            if (sl.hasChunkAt(p) && sl.noCollision(target, target.getBoundingBox().move(Vec3.atBottomCenterOf(p).subtract(target.position())))) {
                                target.teleportTo((double)p.getX() + 0.5, (double)p.getY(), (double)p.getZ() + 0.5);
                            }
                        }

                        t.putLong("OrorRecallPos", target.blockPosition().asLong());
                        Abilities.stun(target, 35);
                        break;
                    case "SHIFT":
                        Vec3 away = target.position().subtract(b.position()).normalize();
                        Abilities.blink(b, target.position().add(-away.z * 4.0, 1.0, away.x * 4.0));
                        b.setForm(b.form() + 1);
                        b.shield = Math.max(40.0F, b.shield);
                        break;
                    case "PULL": {
                        for (LivingEntity foe : targets) {
                            Vec3 d = b.position().subtract(foe.position()).normalize();
                            foe.setDeltaMovement(d.scale(0.9).add(0.0, 0.2, 0.0));
                            foe.hurtMarked = true;
                            Abilities.stun(foe, 20);
                        }

                        strike(b, target, 0.7F, false);
                        break;
                    }
                    case "CURSE": {
                        for (LivingEntity foe : targets) {
                            foe.addEffect(new MobEffectInstance(MobEffects.WITHER, 120, 2));
                            foe.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 120, 0));
                            foe.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 120, 2));
                            foe.getPersistentData().putUUID("ororTragedyCreator", b.getUUID());
                            foe.getPersistentData().putLong("ororTragedyUntil", sl.getGameTime() + 240L);
                            foe.getPersistentData().putFloat("ororTragedyHealth", foe.getHealth());
                        }
                        break;
                    }
                    case "LAW": {
                        for (LivingEntity foe : targets) {
                            foe.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 60, 1));
                            foe.getPersistentData().putLong("OrorSilencedUntil", sl.getGameTime() + 60L);
                            foe.setDeltaMovement(foe.getDeltaMovement().add(0.0, 0.5, 0.0));
                            foe.hurtMarked = true;
                        }
                        break;
                    }
                    case "TOY":
                        // Forge 1.20.1 has no scale attribute: the toy curse slows and weakens instead of shrinking
                        target.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 120, 3));
                        target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 120, 2));

                        Abilities.stun(target, 40);
                        break;
                    case "GROW":
                        int grown = 0;

                        for (BlockPos p : BlockPos.betweenClosed(b.blockPosition().offset(-5, -2, -5), b.blockPosition().offset(5, 2, 5))) {
                            if (grown < 16 && sl.hasChunkAt(p) && sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
                                BlockState state = sl.getBlockState(p);
                                Block var14 = state.getBlock();
                                if (var14 instanceof CropBlock) {
                                    CropBlock crop = (CropBlock)var14;
                                    if (!crop.isMaxAge(state)) {
                                        sl.setBlock(p, crop.getStateForAge(crop.getMaxAge()), 3);
                                        grown++;
                                    }
                                }
                            }
                        }

                        n.putInt("OrorCropsGrown", n.getInt("OrorCropsGrown") + grown);
                        b.healAllies(10.0F);
                        b.shield = Math.max(30.0F, b.shield);
                        break;
                    case "WEATHER":
                        if (sl.dimensionType().hasSkyLight()) {
                            sl.setWeatherParameters(12000, 0, false, false);
                        }

                        b.removeAllEffects();
                        b.shield = Math.max(40.0F, b.shield);
                        break;
                    case "TRANSMUTE":
                        if ((Boolean)RebornConfig.TERRAIN.get() && sl.getGameRules().getBoolean(GameRules.RULE_MOBGRIEFING)) {
                            BlockPos p = target.blockPosition().below();
                            BlockState s = sl.getBlockState(p);
                            if (sl.hasChunkAt(p) && sl.getBlockEntity(p) == null && (s.is(Blocks.STONE) || s.is(Blocks.DIRT))) {
                                sl.setBlock(p, Blocks.GOLD_BLOCK.defaultBlockState(), 3);
                            }
                        }

                        Abilities.stun(target, 40);
                        b.shield = Math.max(60.0F, b.shield);
                        break;
                    default:
                        throw new IllegalStateException("Unsupported technique " + skill.mechanic);
                }

                Abilities.burst(b, skill.motion != 1 && skill.motion != 3 ? ParticleTypes.ENCHANT : ParticleTypes.CRIT, 12);
                DivineDomains.begin(b);
                return true;
            }
        } else {
            return false;
        }
    }

    private static void strike(SupremeEntity b, LivingEntity t, float factor, boolean erasure) {
        LorePowers.strike(b, t, (float)b.getAttributeValue(Attributes.ATTACK_DAMAGE) * factor * ((Double)RebornConfig.DAMAGE.get()).floatValue(), erasure);
    }

    public static void heal(LivingHealEvent e) {
        if (e.getEntity().getPersistentData().getLong("OrorHealLockedUntil") > e.getEntity().level().getGameTime()) {
            e.setCanceled(true);
        }
    }

    public static void tick(LivingTickEvent e) {
        LivingEntity t = e.getEntity();
        if (t.level() instanceof ServerLevel sl) {
            CompoundTag var11 = t.getPersistentData();
            long now = sl.getGameTime();
            if (var11.contains("OrorOldScale") && var11.getLong("OrorToyUntil") <= now) {
                // left by the 1.21.1 build's toy curse in a world carried over
                var11.remove("OrorOldScale");
                var11.remove("OrorToyUntil");
            }

            if (var11.getInt("OrorBarrageRemaining") > 0 && var11.getLong("OrorBarrageNext") <= now && var11.hasUUID("OrorBarrageSource")) {
                if (sl.getEntity(var11.getUUID("OrorBarrageSource")) instanceof SupremeEntity b && b.isAlive() && !b.isNoAi() && b.validEnemy(t)) {
                    int remaining = var11.getInt("OrorBarrageRemaining");
                    int count = Math.min(4, remaining);

                    for (int i = 0; i < count && t.isAlive(); i++) {
                        t.invulnerableTime = 0;
                        strike(b, t, 0.12F, false);
                    }

                    var11.putInt("OrorBarrageRemaining", remaining - count);
                    var11.putLong("OrorBarrageNext", now + 2L);
                    return;
                }

                var11.remove("OrorBarrageRemaining");
            }

            return;
        }
    }

    private CharacterArsenal() {
    }

    public static record Skill(String name, String mechanic, int motion, int cost, int cooldown) {
    }
}
