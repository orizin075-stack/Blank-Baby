package jp.oror.reborn;

import java.util.List;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent;
import net.minecraftforge.event.TickEvent.LevelTickEvent;

public final class WorldEvents {
    public static void livingTick(LivingTickEvent e) {
        Entity v = e.getEntity();
        if (!v.level().isClientSide) {
            CompoundTag n = v.getPersistentData();
            long now = v.level().getGameTime();
            if (v instanceof SupremeEntity boss && v.level() instanceof ServerLevel bl && (n.getLong("ororFreezeUntil") <= now || LorePowers.timeIndependent(boss))) {
                BossPowers.tick(boss, bl);
            }
            if (v instanceof Player wearer && now % 20L == 3L) {
                CharacterRelics.unwear(wearer);
            }
            if (v instanceof Player gunner && now % 5L == 1L) {
                GunCompat.tick(gunner);
            }
            // v0.17.18: NightfallCraft's multiplayer boss fight, a boss grows with the players around it
            if (v instanceof LivingEntity big && now % 40L == 13L && v.level() instanceof ServerLevel partyLevel) {
                NightfallRules.party(big, partyLevel);
            }
            if (!(v instanceof Player) && (!(v instanceof SupremeEntity b) || !LorePowers.timeIndependent(b)) && n.getLong("ororFreezeUntil") > now) {
                v.setDeltaMovement(Vec3.ZERO);
                e.setCanceled(true);
            } else {
                if (v instanceof LivingEntity victim
                    && n.getLong("ororTragedyUntil") > now
                    && now % 20L == 0L
                    && v.level() instanceof ServerLevel ts
                    && n.hasUUID("ororTragedyCreator")
                    && ts.getEntity(n.getUUID("ororTragedyCreator")) instanceof SupremeEntity curse
                    && curse.validEnemy(victim)) {
                    float old = n.getFloat("ororTragedyHealth");
                    if (victim.getHealth() > old) {
                        victim.hurt(curse.damageSources().mobAttack(curse), Math.max(4.0F, victim.getHealth() - old));
                    }

                    n.putFloat("ororTragedyHealth", victim.getHealth());
                }

                if (n.getLong("ororGameUntil") > now
                    && v instanceof LivingEntity t
                    && now % 10L == 0L
                    && v.level() instanceof ServerLevel sl
                    && n.hasUUID("ororGameCreator")
                    && sl.getEntity(n.getUUID("ororGameCreator")) instanceof SupremeEntity b
                    && b.validEnemy(t)) {
                    int r = n.getInt("ororGameRule");
                    double dx = v.getX() - n.getDouble("ororGameX");
                    double dz = v.getZ() - n.getDouble("ororGameZ");
                    boolean fail = r == 0 && dx * dx + dz * dz > 0.25 || r == 1 && v.onGround() || r == 2 && b.distanceTo(v) < 3.0F;
                    if (fail) {
                        t.hurt(b.damageSources().mobAttack(b), 8.0F);
                        if (v instanceof Player p) {
                            p.displayClientMessage(Component.literal("ノルティア：ルール違反、罰ゲーム！"), true);
                        }
                    }
                }
            }
        }
    }

    public static void damage(LivingHurtEvent e) {
        LivingEntity v = e.getEntity();
        if (!v.level().isClientSide) {
            // v0.17.16: crossing an expedition party, a wandering trader or a caravan, and a raid messenger's ritual
            VillageFeuds.attacked(e);
            WanderingTraders.attacked(e);
            VillageRaids.hurt(e);
            // v0.17.18: a boss sharing its fight with several players (NightfallCraft's multiplayer boss fight)
            NightfallRules.damage(e);
        }
        if (v instanceof SupremeEntity boss && !v.level().isClientSide) {
            BossPowers.incoming(e, boss);
        }
        if (!v.level().isClientSide && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
            List<SupremeEntity> guards = v.level()
                .getEntitiesOfClass(SupremeEntity.class, v.getBoundingBox().inflate(8.0), bx -> bx.ally(v) && bx.isAlive() && !bx.isNoAi());

            for (SupremeEntity b : guards) {
                if (b.spec.id.equals("savior") && b.lore()) {
                    e.setAmount(0.0F);
                    e.setCanceled(true);
                    return;
                }
            }

            for (SupremeEntity bx : guards) {
                if (bx.spec.id.equals("savior") && bx.spend(3.0F)) {
                    e.setAmount(e.getAmount() * 0.5F);
                    break;
                }
            }

            if (!(e.getAmount() < v.getHealth()) && v.getPersistentData().getLong("ororSavedUntil") < v.level().getGameTime()) {
                for (SupremeEntity bxx : guards) {
                    if (bxx.spec.id.equals("arcana") && bxx.spend(35.0F)) {
                        v.getPersistentData().putLong("ororSavedUntil", v.level().getGameTime() + 600L);
                        e.setAmount(Math.max(0.0F, v.getHealth() - 1.0F));
                        Abilities.burst(bxx, ParticleTypes.END_ROD, 16);
                        break;
                    }
                }
            }
        }
    }

    public static void levelTick(LevelTickEvent e) {
        if (e.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        if (e.level instanceof ServerLevel cleanup) {
            // Forge 1.20.1 ticks only living entities through an event: the village's aircraft and vehicles (and any
            // other non-living entity) are visited here instead. Copied first, since a flight that lands discards its
            // crew and craft, and only where the level ticks entities, as the 1.21.1 entity tick event did.
            if (!cleanup.players().isEmpty() || !cleanup.getForcedChunks().isEmpty()) {
                List<Entity> things = new java.util.ArrayList<>();
                for (Entity thing : cleanup.getAllEntities()) {
                    if (!(thing instanceof LivingEntity) && cleanup.isPositionEntityTicking(thing.blockPosition())) {
                        things.add(thing);
                    }
                }
                for (Entity thing : things) {
                    if (!thing.isRemoved()) {
                        VillageFlights.tick(thing);
                    }
                    if (!thing.isRemoved()) {
                        VillageVehicles.tick(thing);
                    }
                }
            }
            // v0.17.18: NightfallCraft's spawn caps (its InControl rules)
            NightfallRules.hook();
            TerrainPlay.cleanup(cleanup);
            RelicShells.tick(cleanup);
            // v0.17.15: gates to put out, and now and then a wandering expedition party
            VillageExpeditions.timers(cleanup);
            if ((Boolean)RebornConfig.VILLAGE_LIFE.get()) {
                VillageExpeditions.wanderers(cleanup);
                // v0.17.16: traders' grenades and smoke, caravans, raid messengers' hordes
                WanderingTraders.levelTick(cleanup);
                VillageRaids.levelTick(cleanup);
                // v0.17.17: the village review also at night and while everyone hides (it held the threat check for
                // the tanks and jets, and it only ran when some villager was doing its day's chores)
                VillageWork.watch(cleanup);
            }
        }

        if (e.level instanceof ServerLevel sl && (Boolean)RebornConfig.NATURAL.get() && !sl.players().isEmpty()) {
            EncounterRules.special(sl);
            if (sl.getGameTime() % (long)((Integer)RebornConfig.ENCOUNTER_INTERVAL.get()).intValue() != 0L) {
                return;
            }

            int count = 0;

            for (Entity v : sl.getAllEntities()) {
                if (v instanceof SupremeEntity) {
                    count++;
                }
            }

            if (count >= 16) {
                return;
            }

            ServerPlayer p = (ServerPlayer)sl.players().get(sl.random.nextInt(sl.players().size()));
            List<String> ids = EncounterRules.WANDERERS.stream().sorted().toList();
            EncounterRules.spawn(sl, ids.get(sl.random.nextInt(ids.size())), p.blockPosition(), 24);
            return;
        }
    }
}
