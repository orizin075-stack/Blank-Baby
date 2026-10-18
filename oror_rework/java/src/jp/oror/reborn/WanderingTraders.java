package jp.oror.reborn;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.WeakHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.horse.Llama;
import net.minecraft.world.entity.animal.horse.TraderLlama;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.WanderingTrader;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent.EntityInteract;

/**
 * Wandering traders, reworked (v0.17.16).
 * - Arms dealers: besides their usual wares they sell weapons at outrageous prices - Superb Warfare's rocket launchers,
 *   anti-materiel rifles, machine guns and missiles, explosives and ammunition, and enchanted netherite.
 * - True colours: attacked, a trader shows what it really is on the instant. Its llamas become turrets that hose the
 *   attacker with sentry-gun fire from their mouths, and the trader becomes a debuffer: a flashbang (blindness, nausea),
 *   a taser (slowness, mining fatigue, weakness, and a stun), smoke (blindness and slowness for whoever is in it, and
 *   cover for itself), poisoned darts (poison, hunger) and a poisoned knife once its prey is crippled. It is strong.
 * - Thieves: now and then a trader in a village helps itself from the communal chests. Seen at it (by a player or a
 *   villager), it turns on every witness to silence them, villagers included. Killed, it drops what it took.
 * - Caravans: rarely, a great caravan crosses the land - three traders with their llamas and six heavily armed guards.
 *   Its traders deal in what cannot otherwise be had (relic weapons, end portal frames, spawners, spawn eggs...). Strike
 *   any of it and the whole caravan fights.
 */
public final class WanderingTraders {
    private static final ResourceLocation TRUE = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "trader_true_power");
    private static final Map<ServerLevel, List<Cloud>> CLOUDS = new WeakHashMap<>();
    private static final Map<Mob, Boolean> CLEARED = new WeakHashMap<>();

    /** A flashbang about to go off (smoke false), or a smoke cloud hanging (smoke true). */
    private record Cloud(boolean smoke, Vec3 at, long from, long until, UUID side) {
    }

    private WanderingTraders() {
    }

    // ------------------------------------------------------------------------------------- the stock
    /** {item, emeralds, diamonds}: weapons for the outrageously rich. */
    private static final String[][] ARMS = {
        {"superbwarfare:rpg", "64", "16"}, {"superbwarfare:m_79", "48", "8"}, {"superbwarfare:minigun", "64", "32"},
        {"superbwarfare:ntw_20", "64", "24"}, {"superbwarfare:awm", "64", "16"}, {"superbwarfare:m_98b", "56", "12"},
        {"superbwarfare:javelin", "64", "32"}, {"superbwarfare:igla_9k38", "64", "24"}, {"superbwarfare:m_2_hb", "64", "20"},
        {"superbwarfare:rpk", "48", "10"}, {"superbwarfare:m_60", "56", "12"}, {"superbwarfare:aa_12", "56", "12"},
        {"superbwarfare:taser", "32", "4"}, {"superbwarfare:secondary_cataclysm", "64", "32"}, {"superbwarfare:sentinel", "64", "20"}
    };
    /** {item, count, emeralds, diamonds}: what the weapons eat. */
    private static final String[][] MUNITIONS = {
        {"superbwarfare:rpg_rocket_standard", "4", "24", "0"}, {"superbwarfare:grenade_40mm", "8", "20", "0"},
        {"superbwarfare:javelin_missile", "2", "40", "4"}, {"superbwarfare:hand_grenade", "8", "16", "0"},
        {"superbwarfare:m18_smoke_grenade", "8", "12", "0"}, {"superbwarfare:c4_bomb", "4", "32", "2"},
        {"superbwarfare:claymore_mine", "6", "24", "0"}, {"superbwarfare:rifle_ammo_box", "1", "16", "0"},
        {"superbwarfare:sniper_ammo_box", "1", "20", "0"}, {"superbwarfare:handgun_ammo_box", "1", "10", "0"},
        {"superbwarfare:shotgun_ammo_box", "1", "14", "0"}, {"superbwarfare:heavy_ammo", "64", "24", "0"}
    };
    /** {item, count, price item, price, second price item, second price}: a caravan's wares, not to be had otherwise. */
    private static final String[][] RARE = {
        {"minecraft:end_portal_frame", "1", "emerald", "64", "diamond", "8"},
        {"minecraft:spawner", "1", "emerald", "64", "diamond", "16"},
        {"minecraft:budding_amethyst", "1", "emerald", "32", "", "0"},
        {"minecraft:reinforced_deepslate", "4", "emerald", "48", "", "0"},
        {"minecraft:villager_spawn_egg", "1", "emerald", "32", "diamond", "2"},
        {"minecraft:iron_golem_spawn_egg", "1", "emerald", "48", "diamond", "4"},
        {"minecraft:enchanted_golden_apple", "1", "emerald", "64", "", "0"},
        {"minecraft:totem_of_undying", "1", "emerald", "48", "", "0"},
        {"minecraft:elytra", "1", "emerald", "64", "diamond", "16"},
        {"minecraft:heavy_core", "1", "emerald", "64", "diamond", "8"},
        {"superbwarfare:creative_ammo_box", "1", "emerald_block", "64", "netherite_ingot", "8"},
        {"superbwarfare:legendary_material_pack", "1", "emerald", "48", "diamond", "16"},
        {"superbwarfare:legendary_blueprint_data_chip", "1", "emerald", "48", "diamond", "16"}
    };

    private static Item item(String id) {
        ResourceLocation rl = id.contains(":") ? ResourceLocation.fromNamespaceAndPath(id.substring(0, id.indexOf(':')), id.substring(id.indexOf(':') + 1))
            : ResourceLocation.withDefaultNamespace(id);
        return BuiltInRegistries.ITEM.containsKey(rl) ? (Item)BuiltInRegistries.ITEM.get(rl) : null;
    }

    private static MerchantOffer offer(ItemStack result, Item a, int na, Item b, int nb, int uses) {
        return new MerchantOffer(new ItemCost(a, Math.min(64, na)), b == null || nb <= 0 ? Optional.empty() : Optional.of(new ItemCost(b, Math.min(64, nb))),
            result, uses, 0, 0.0F);
    }

    /** Once per trader: the weapons (a caravan trader: the rare wares too). */
    private static void stock(ServerLevel sl, WanderingTrader t, CompoundTag root) {
        root.putBoolean("OrorStocked", true);
        MerchantOffers offers = t.getOffers();
        List<String[]> arms = new ArrayList<>(List.of(ARMS));
        Collections.shuffle(arms, new java.util.Random(sl.random.nextLong()));
        int n = 0;
        for (String[] a : arms) {
            Item it = item(a[0]);
            if (it != null && n < 3) {
                offers.add(offer(it.getDefaultInstance(), Items.EMERALD, Integer.parseInt(a[1]), Items.DIAMOND, Integer.parseInt(a[2]), 1));
                n++;
            }
        }
        List<String[]> ammo = new ArrayList<>(List.of(MUNITIONS));
        Collections.shuffle(ammo, new java.util.Random(sl.random.nextLong()));
        n = 0;
        for (String[] a : ammo) {
            Item it = item(a[0]);
            if (it != null && n < 2) {
                offers.add(offer(it.getDefaultInstance().copyWithCount(Math.min(it.getDefaultInstance().getMaxStackSize(), Integer.parseInt(a[1]))),
                    Items.EMERALD, Integer.parseInt(a[2]), Items.DIAMOND, Integer.parseInt(a[3]), 4));
                n++;
            }
        }
        // enchanted netherite, whatever else is installed
        var ench = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        ItemStack sword = Items.NETHERITE_SWORD.getDefaultInstance();
        sword.enchant(ench.getHolderOrThrow(Enchantments.SHARPNESS), 5);
        sword.enchant(ench.getHolderOrThrow(Enchantments.LOOTING), 3);
        sword.enchant(ench.getHolderOrThrow(Enchantments.FIRE_ASPECT), 2);
        sword.enchant(ench.getHolderOrThrow(Enchantments.UNBREAKING), 3);
        offers.add(offer(sword, Items.EMERALD, 56, Items.DIAMOND, 12, 1));
        ItemStack bow = Items.BOW.getDefaultInstance();
        bow.enchant(ench.getHolderOrThrow(Enchantments.POWER), 5);
        bow.enchant(ench.getHolderOrThrow(Enchantments.FLAME), 1);
        bow.enchant(ench.getHolderOrThrow(Enchantments.INFINITY), 1);
        bow.enchant(ench.getHolderOrThrow(Enchantments.UNBREAKING), 3);
        offers.add(offer(bow, Items.EMERALD, 40, Items.DIAMOND, 6, 1));
        if (!root.hasUUID("OrorCaravan")) {
            return;
        }
        List<String[]> rare = new ArrayList<>(List.of(RARE));
        Collections.shuffle(rare, new java.util.Random(sl.random.nextLong()));
        n = 0;
        for (String[] a : rare) {
            Item it = item(a[0]);
            if (it == null || n >= 4) {
                continue;
            }
            offers.add(offer(it.getDefaultInstance().copyWithCount(Integer.parseInt(a[1])), item(a[2]), Integer.parseInt(a[3]),
                a[4].isEmpty() ? null : item(a[4]), Integer.parseInt(a[5]), 2));
            n++;
        }
        // a relic weapon, which otherwise only falls from its owner
        List<String> relics = new ArrayList<>();
        for (String id : CharacterRelics.ITEMS.keySet()) {
            if (id.endsWith("_weapon")) {
                relics.add(id);
            }
        }
        if (!relics.isEmpty()) {
            Item relic = (Item)CharacterRelics.ITEMS.get(relics.get(sl.random.nextInt(relics.size()))).get();
            offers.add(offer(relic.getDefaultInstance(), Items.EMERALD_BLOCK, 40, Items.NETHERITE_INGOT, 4, 1));
        }
    }

    // ------------------------------------------------------------------------------------- every tick
    /** VillagerLife.tick hands every other entity here: traders, their llamas. */
    static void tick(Entity e) {
        if (e instanceof WanderingTrader t && t.level() instanceof ServerLevel sl && t.isAlive()) {
            CompoundTag root = t.getPersistentData();
            if (!root.getBoolean("OrorStocked") && t.tickCount > 5) {
                stock(sl, t, root);
            }
            if (root.getBoolean("OrorRevealed")) {
                fight(sl, t, root);
                return;
            }
            if (t.tickCount % 20 == Math.floorMod(t.getId(), 20)) {
                if (root.hasUUID("OrorCaravan")) {
                    follow(sl, t, root);
                } else {
                    thief(sl, t, root);
                }
            }
        } else if (e instanceof Llama l && l.level() instanceof ServerLevel sl && l.isAlive() && l.getPersistentData().getBoolean("OrorTurret")) {
            turret(sl, l);
        }
    }

    /** AdaptiveCombat leaves these alone: a trader in its true colours and its turrets fight their own way. */
    static boolean driven(Mob m) {
        return m instanceof WanderingTrader && m.getPersistentData().getBoolean("OrorRevealed")
            || m instanceof Llama && m.getPersistentData().getBoolean("OrorTurret");
    }

    /** VillageReputation.interact: no trading with a trader trying to kill you. */
    static boolean refuse(EntityInteract e) {
        if (e.getTarget() instanceof WanderingTrader t && t.getPersistentData().getBoolean("OrorRevealed")) {
            e.setCancellationResult(InteractionResult.FAIL);
            e.setCanceled(true);
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------------------------------- true colours
    private static boolean side(Entity x, CompoundTag traderRoot, UUID trader) {
        if (x == null) {
            return false;
        }
        CompoundTag r = x.getPersistentData();
        if (x.getUUID().equals(trader) || r.hasUUID("OrorTurretOwner") && r.getUUID("OrorTurretOwner").equals(trader)) {
            return true;
        }
        return traderRoot.hasUUID("OrorCaravan") && r.hasUUID("OrorCaravan") && r.getUUID("OrorCaravan").equals(traderRoot.getUUID("OrorCaravan"));
    }

    private static void modifier(LivingEntity e, Holder<Attribute> a, double amount, AttributeModifier.Operation op) {
        AttributeInstance i = e.getAttribute(a);
        if (i != null) {
            i.removeModifier(TRUE);
            i.addPermanentModifier(new AttributeModifier(TRUE, amount, op));
        }
    }

    /** The instant it is struck (or seen stealing): the trader's true strength, and its llamas become turrets. */
    static void reveal(ServerLevel sl, WanderingTrader t, LivingEntity foe) {
        CompoundTag root = t.getPersistentData();
        if (!root.getBoolean("OrorRevealed")) {
            root.putBoolean("OrorRevealed", true);
            modifier(t, Attributes.MAX_HEALTH, 8.0, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
            modifier(t, Attributes.ARMOR, 14.0, AttributeModifier.Operation.ADD_VALUE);
            modifier(t, Attributes.ARMOR_TOUGHNESS, 6.0, AttributeModifier.Operation.ADD_VALUE);
            modifier(t, Attributes.KNOCKBACK_RESISTANCE, 0.6, AttributeModifier.Operation.ADD_VALUE);
            modifier(t, Attributes.MOVEMENT_SPEED, 0.3, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
            t.setHealth(t.getMaxHealth());
            t.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 72000, 0));
            t.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 72000, 0));
            t.setDespawnDelay(0);
            t.setPersistenceRequired();
            ItemStack knife = item("superbwarfare:knife") != null ? item("superbwarfare:knife").getDefaultInstance() : Items.NETHERITE_SWORD.getDefaultInstance();
            t.setItemSlot(EquipmentSlot.MAINHAND, knife);
            t.setDropChance(EquipmentSlot.MAINHAND, 0.0F);
            t.setCustomName(Component.literal("§4" + (root.hasUUID("OrorCaravan") ? "大キャラバンの闇商人" : "闇の行商人")));
            t.setCustomNameVisible(true);
            sl.sendParticles(ParticleTypes.LARGE_SMOKE, t.getX(), t.getY() + 1.0, t.getZ(), 40, 0.6, 0.9, 0.6, 0.05);
            sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, t.getX(), t.getY() + 1.0, t.getZ(), 30, 0.5, 0.9, 0.5, 0.08);
            RelicEffects.sound(sl, t.blockPosition(), SoundEvents.ILLUSIONER_MIRROR_MOVE, 1.4F, 0.6F);
            RelicEffects.sound(sl, t.blockPosition(), SoundEvents.EVOKER_PREPARE_SUMMON, 1.2F, 0.8F);
            for (Player p : sl.getEntitiesOfClass(Player.class, t.getBoundingBox().inflate(32.0))) {
                p.displayClientMessage(Component.literal("§4行商人が本性を現した！"), true);
            }
            for (Llama l : sl.getEntitiesOfClass(Llama.class, t.getBoundingBox().inflate(24.0),
                    l -> l.getLeashHolder() == t || side(l, root, t.getUUID()))) {
                turret(sl, l, t);
            }
        }
        if (foe != null && !side(foe, root, t.getUUID())) {
            ListTag foes = root.getList("OrorFoes", 10);
            boolean known = false;
            for (Tag x : foes) {
                known |= ((CompoundTag)x).getUUID("Id").equals(foe.getUUID());
            }
            if (!known) {
                foes.add(VillageProgress.uuid(foe.getUUID()));
                root.put("OrorFoes", foes);
            }
            if (t.getTarget() == null || !t.getTarget().isAlive()) {
                t.setTarget(foe);
            }
        }
    }

    /** A llama turned gun turret: rooted to the spot, tougher, firing from its mouth. */
    private static void turret(ServerLevel sl, Llama l, WanderingTrader owner) {
        CompoundTag root = l.getPersistentData();
        if (root.getBoolean("OrorTurret")) {
            return;
        }
        root.putBoolean("OrorTurret", true);
        root.putUUID("OrorTurretOwner", owner.getUUID());
        if (l.getLeashHolder() != null) {
            l.dropLeash(true, false);
        }
        modifier(l, Attributes.MAX_HEALTH, 3.0, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
        modifier(l, Attributes.ARMOR, 12.0, AttributeModifier.Operation.ADD_VALUE);
        modifier(l, Attributes.MOVEMENT_SPEED, -1.0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        l.setHealth(l.getMaxHealth());
        l.setCustomName(Component.literal("§c砲台ラマ"));
        l.setCustomNameVisible(true);
        sl.sendParticles(ParticleTypes.CRIT, l.getX(), l.getY() + 1.2, l.getZ(), 30, 0.5, 0.6, 0.5, 0.3);
        RelicEffects.sound(sl, l.blockPosition(), SoundEvents.ANVIL_LAND, 0.8F, 1.6F);
    }

    /** Sentry-gun fire from the mouth at the trader's quarry (or whoever hit it), three rounds a second and more. */
    private static void turret(ServerLevel sl, Llama l) {
        CompoundTag root = l.getPersistentData();
        long now = sl.getGameTime();
        Entity owner = root.hasUUID("OrorTurretOwner") ? sl.getEntity(root.getUUID("OrorTurretOwner")) : null;
        LivingEntity t = owner instanceof Mob m && m.isAlive() ? m.getTarget() : null;
        if (!valid(l, t)) {
            t = l.getLastHurtByMob();
        }
        if (!valid(l, t) || l.distanceToSqr(t) > 32.0 * 32.0) {
            return;
        }
        l.getLookControl().setLookAt(t, 60.0F, 60.0F);
        if ((now + l.getId()) % 3L != 0L) {
            return;
        }
        Vec3 mouth = l.getEyePosition().add(l.getLookAngle().scale(0.8));
        Vec3 aim = t.getEyePosition().add((sl.random.nextDouble() - 0.5) * 0.9, (sl.random.nextDouble() - 0.5) * 0.9 - 0.3, (sl.random.nextDouble() - 0.5) * 0.9);
        BlockHitResult hit = sl.clip(new ClipContext(mouth, aim, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, l));
        boolean clear = hit.getType() == HitResult.Type.MISS;
        tracer(sl, mouth, clear ? aim : hit.getLocation(), ParticleTypes.CRIT);
        sl.sendParticles(ParticleTypes.SMOKE, mouth.x, mouth.y, mouth.z, 2, 0.05, 0.05, 0.05, 0.01);
        if ((now + l.getId()) % 6L == 0L) {
            RelicEffects.sound(sl, l.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, 0.6F, 1.9F);
        }
        if (clear && sl.random.nextDouble() < 0.65) {
            t.invulnerableTime = 0;
            t.hurt(l.damageSources().mobAttack(l), 1.2F);
        }
    }

    private static boolean valid(LivingEntity self, LivingEntity t) {
        return t != null && t != self && t.isAlive() && !(t instanceof Player p && (p.isCreative() || p.isSpectator()))
            && !side(t, self.getPersistentData(), self.getPersistentData().hasUUID("OrorTurretOwner") ? self.getPersistentData().getUUID("OrorTurretOwner") : self.getUUID());
    }

    private static void tracer(ServerLevel sl, Vec3 from, Vec3 to, ParticleOptions p) {
        Vec3 d = to.subtract(from);
        int steps = Math.max(1, (int)(d.length() / 1.2));
        for (int i = 1; i <= steps; i++) {
            Vec3 at = from.add(d.scale(i / (double)steps));
            sl.sendParticles(p, at.x, at.y, at.z, 1, 0.0, 0.0, 0.0, 0.0);
        }
    }

    // ------------------------------------------------------------------------------------- the debuffer
    private static java.lang.reflect.Field goals;
    private static boolean noGoals;

    /** Clear a mob's goals (its goal selector reached by reflection, as its access differs between versions). */
    private static void calm(Mob m) {
        if (noGoals) {
            return;
        }
        try {
            if (goals == null) {
                goals = Mob.class.getDeclaredField("goalSelector");
                goals.setAccessible(true);
            }
            Object selector = goals.get(m);
            java.util.function.Predicate<Object> all = g -> true;
            selector.getClass().getMethod("removeAllGoals", java.util.function.Predicate.class).invoke(selector, all);
        } catch (ReflectiveOperationException | RuntimeException | LinkageError ex) {
            // its own goals stay; the navigation set every half second still wins most of the time
            noGoals = true;
        }
    }

    private static boolean ready(CompoundTag root, String key, long now) {
        return root.getLong("OrorCd" + key) <= now;
    }

    private static void cool(CompoundTag root, String key, long now, long ticks) {
        root.putLong("OrorCd" + key, now + ticks);
    }

    /** A trader in its true colours: cripple the quarry with gadgets, then the knife. */
    private static void fight(ServerLevel sl, WanderingTrader t, CompoundTag root) {
        long now = sl.getGameTime();
        if (!CLEARED.containsKey(t)) {
            // no more panicking, drinking potions or trading: it fights now
            calm(t);
            CLEARED.put(t, true);
        }
        LivingEntity foe = t.getTarget();
        if (!valid(t, foe) || t.distanceToSqr(foe) > 48.0 * 48.0) {
            foe = null;
            for (Tag x : root.getList("OrorFoes", 10)) {
                if (sl.getEntity(((CompoundTag)x).getUUID("Id")) instanceof LivingEntity c && valid(t, c) && t.distanceToSqr(c) < 40.0 * 40.0) {
                    foe = c;
                    break;
                }
            }
            t.setTarget(foe);
        }
        if (foe == null) {
            // nobody left to silence: gone in a puff of smoke after half a minute
            long idle = root.getLong("OrorIdleSince");
            if (idle == 0L) {
                root.putLong("OrorIdleSince", now);
            } else if (now - idle > 600L) {
                sl.sendParticles(ParticleTypes.LARGE_SMOKE, t.getX(), t.getY() + 1.0, t.getZ(), 40, 0.6, 0.9, 0.6, 0.05);
                RelicEffects.sound(sl, t.blockPosition(), SoundEvents.FIRE_EXTINGUISH, 1.0F, 0.8F);
                t.discard();
            }
            return;
        }
        root.remove("OrorIdleSince");
        double d = t.distanceTo(foe);
        boolean sight = t.hasLineOfSight(foe);
        t.getLookControl().setLookAt(foe, 30.0F, 30.0F);
        if (t.tickCount % 10 == 0) {
            if (d > 2.4) {
                t.getNavigation().moveTo(foe, d > 10.0 ? 0.42 : 0.34);
            } else {
                t.getNavigation().stop();
            }
        }
        if (sight && d < 16.0 && ready(root, "Flash", now)) {
            flash(sl, t, foe);
            cool(root, "Flash", now, 180L);
        } else if (sight && d < 10.0 && ready(root, "Taser", now)) {
            taser(sl, t, foe);
            cool(root, "Taser", now, 100L);
        } else if ((t.getHealth() < t.getMaxHealth() * 0.7F || d < 5.0) && ready(root, "Smoke", now)) {
            smoke(sl, t);
            cool(root, "Smoke", now, 260L);
        } else if (sight && d > 3.0 && d < 14.0 && ready(root, "Dart", now)) {
            dart(sl, t, foe);
            cool(root, "Dart", now, 50L);
        } else if (d < 2.8 && ready(root, "Knife", now)) {
            knife(sl, t, foe);
            cool(root, "Knife", now, 14L);
        }
    }

    private static void effect(LivingEntity e, Holder<MobEffect> what, int ticks, int amp) {
        e.addEffect(new MobEffectInstance(what, ticks, amp));
    }

    /** A flashbang lobbed at the quarry's feet: it goes off a moment later. */
    private static void flash(ServerLevel sl, WanderingTrader t, LivingEntity foe) {
        t.swing(InteractionHand.OFF_HAND);
        tracer(sl, t.getEyePosition(), foe.position().add(0.0, 0.3, 0.0), ParticleTypes.SMOKE);
        RelicEffects.sound(sl, t.blockPosition(), SoundEvents.ARROW_SHOOT, 0.8F, 0.6F);
        long now = sl.getGameTime();
        CLOUDS.computeIfAbsent(sl, k -> new ArrayList<>()).add(new Cloud(false, foe.position(), now + 16L, now + 16L, t.getUUID()));
    }

    /** The taser: electrodes into the quarry - slowness, mining fatigue, weakness, and it stops dead. */
    private static void taser(ServerLevel sl, WanderingTrader t, LivingEntity foe) {
        t.swing(InteractionHand.MAIN_HAND);
        tracer(sl, t.getEyePosition(), foe.getEyePosition().add(0.0, -0.4, 0.0), ParticleTypes.ELECTRIC_SPARK);
        sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, foe.getX(), foe.getY() + 1.0, foe.getZ(), 30, 0.4, 0.7, 0.4, 0.3);
        RelicEffects.sound(sl, foe.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 1.2F, 2.0F);
        RelicEffects.sound(sl, foe.blockPosition(), SoundEvents.CHAIN_BREAK, 1.0F, 1.8F);
        foe.hurt(t.damageSources().mobAttack(t), 4.0F);
        effect(foe, MobEffects.MOVEMENT_SLOWDOWN, 60, 3);
        effect(foe, MobEffects.DIG_SLOWDOWN, 200, 2);
        effect(foe, MobEffects.WEAKNESS, 200, 1);
        foe.setDeltaMovement(0.0, Math.min(0.0, foe.getDeltaMovement().y), 0.0);
        foe.hurtMarked = true;
    }

    /** Smoke round itself: blind and slow for whoever is in it, cover for the trader. */
    private static void smoke(ServerLevel sl, WanderingTrader t) {
        RelicEffects.sound(sl, t.blockPosition(), SoundEvents.FIRE_EXTINGUISH, 1.2F, 0.5F);
        long now = sl.getGameTime();
        CLOUDS.computeIfAbsent(sl, k -> new ArrayList<>()).add(new Cloud(true, t.position(), now, now + 160L, t.getUUID()));
    }

    /** A poisoned dart: poison and hunger. */
    private static void dart(ServerLevel sl, WanderingTrader t, LivingEntity foe) {
        t.swing(InteractionHand.MAIN_HAND);
        tracer(sl, t.getEyePosition(), foe.getEyePosition(), ParticleTypes.CRIT);
        RelicEffects.sound(sl, t.blockPosition(), SoundEvents.ARROW_SHOOT, 0.9F, 1.6F);
        if (sl.random.nextDouble() < 0.85) {
            foe.hurt(t.damageSources().mobAttack(t), 3.0F);
            effect(foe, MobEffects.POISON, 100, 1);
            effect(foe, MobEffects.HUNGER, 200, 2);
        }
    }

    /** The knife, once the quarry is down to size. */
    private static void knife(ServerLevel sl, WanderingTrader t, LivingEntity foe) {
        t.swing(InteractionHand.MAIN_HAND);
        RelicEffects.sound(sl, t.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.0F, 1.3F);
        foe.hurt(t.damageSources().mobAttack(t), 9.0F);
        effect(foe, MobEffects.POISON, 60, 0);
    }

    /** WorldEvents.levelTick: flashbangs going off, smoke hanging; and now and then a caravan. */
    static void levelTick(ServerLevel sl) {
        List<Cloud> clouds = CLOUDS.get(sl);
        long now = sl.getGameTime();
        if (clouds != null && !clouds.isEmpty()) {
            for (Cloud c : new ArrayList<>(clouds)) {
                if (!c.smoke()) {
                    if (now >= c.from()) {
                        clouds.remove(c);
                        bang(sl, c);
                    }
                } else if (now > c.until()) {
                    clouds.remove(c);
                } else if (now % 4L == 0L) {
                    haze(sl, c);
                }
            }
        }
        caravans(sl);
    }

    private static boolean ours(ServerLevel sl, Entity x, UUID trader) {
        Entity t = sl.getEntity(trader);
        return t != null && side(x, t.getPersistentData(), trader);
    }

    private static void bang(ServerLevel sl, Cloud c) {
        sl.sendParticles(ParticleTypes.FLASH, c.at().x, c.at().y + 0.5, c.at().z, 1, 0.0, 0.0, 0.0, 0.0);
        sl.sendParticles(ParticleTypes.END_ROD, c.at().x, c.at().y + 0.5, c.at().z, 40, 0.3, 0.3, 0.3, 0.4);
        RelicEffects.sound(sl, BlockPos.containing(c.at()), SoundEvents.FIREWORK_ROCKET_BLAST, 2.0F, 0.6F);
        for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(c.at())).inflate(7.0), x -> !ours(sl, x, c.side()))) {
            effect(e, MobEffects.BLINDNESS, 100, 0);
            effect(e, MobEffects.CONFUSION, 200, 0);
            effect(e, MobEffects.MOVEMENT_SLOWDOWN, 60, 0);
        }
    }

    private static void haze(ServerLevel sl, Cloud c) {
        sl.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, c.at().x, c.at().y + 0.8, c.at().z, 10, 2.2, 0.8, 2.2, 0.01);
        sl.sendParticles(ParticleTypes.LARGE_SMOKE, c.at().x, c.at().y + 0.8, c.at().z, 8, 2.0, 0.8, 2.0, 0.01);
        for (LivingEntity e : sl.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(c.at())).inflate(4.5, 2.5, 4.5))) {
            if (ours(sl, e, c.side())) {
                effect(e, MobEffects.INVISIBILITY, 30, 0);
            } else {
                effect(e, MobEffects.BLINDNESS, 40, 0);
                effect(e, MobEffects.MOVEMENT_SLOWDOWN, 40, 1);
            }
        }
    }

    // ------------------------------------------------------------------------------------- struck
    /** WorldEvents.damage: a trader, its llama or a caravan guard struck - true colours, for the whole caravan. */
    static void attacked(LivingIncomingDamageEvent e) {
        if (!(e.getEntity().level() instanceof ServerLevel sl) || !(e.getSource().getEntity() instanceof LivingEntity foe)) {
            return;
        }
        // found out by people (players, villagers and guards, golems), not by a passing zombie
        if (!(foe instanceof Player || foe instanceof Mob fm && AdaptiveCombat.guardian(fm) || foe instanceof net.minecraft.world.entity.animal.IronGolem)) {
            return;
        }
        LivingEntity v = e.getEntity();
        WanderingTrader owner = null;
        if (v instanceof WanderingTrader t) {
            owner = t;
        } else if (v instanceof Llama l) {
            Entity o = l.getLeashHolder();
            if (o == null && l.getPersistentData().hasUUID("OrorTurretOwner")) {
                o = sl.getEntity(l.getPersistentData().getUUID("OrorTurretOwner"));
            }
            owner = o instanceof WanderingTrader t ? t : null;
        }
        CompoundTag root = v.getPersistentData();
        if (owner != null && !side(foe, owner.getPersistentData(), owner.getUUID())) {
            reveal(sl, owner, foe);
        }
        UUID caravan = root.hasUUID("OrorCaravan") ? root.getUUID("OrorCaravan") : (owner != null && owner.getPersistentData().hasUUID("OrorCaravan")
            ? owner.getPersistentData().getUUID("OrorCaravan") : null);
        if (caravan != null && !(foe.getPersistentData().hasUUID("OrorCaravan") && caravan.equals(foe.getPersistentData().getUUID("OrorCaravan")))) {
            alarm(sl, v, caravan, foe);
        }
    }

    /** The whole caravan turns on whoever struck it. */
    private static void alarm(ServerLevel sl, LivingEntity at, UUID caravan, LivingEntity foe) {
        for (Mob m : sl.getEntitiesOfClass(Mob.class, at.getBoundingBox().inflate(96.0),
                x -> x.isAlive() && x.getPersistentData().hasUUID("OrorCaravan") && caravan.equals(x.getPersistentData().getUUID("OrorCaravan")))) {
            if (m instanceof WanderingTrader t) {
                reveal(sl, t, foe);
            } else if (m instanceof Villager g && (g.getTarget() == null || !g.getTarget().isAlive())) {
                g.setTarget(foe);
            }
        }
    }

    // ------------------------------------------------------------------------------------- the thief
    private static boolean valuable(ItemStack st) {
        String id = BuiltInRegistries.ITEM.getKey(st.getItem()).getPath();
        return id.startsWith("emerald") || id.startsWith("diamond") && !id.contains("_") || id.equals("diamond_block") || id.startsWith("gold_")
            || id.startsWith("iron_ingot") || id.equals("iron_block") || id.startsWith("netherite") || id.equals("ancient_debris") || id.startsWith("ender_")
            || id.equals("blaze_rod") || id.contains("golden_apple") || id.equals("totem_of_undying") || id.equals("lapis_lazuli");
    }

    /** Once a day at most, a trader in a village may make for a communal chest and help itself. */
    private static void thief(ServerLevel sl, WanderingTrader t, CompoundTag root) {
        long now = sl.getGameTime();
        String phase = root.getString("OrorThief");
        if (phase.isEmpty()) {
            if (root.getBoolean("OrorThiefRolled") || !sl.isDay()) {
                return;
            }
            VillageLedger.Village village = VillageLedger.get(sl).nearest(t.blockPosition());
            if (village == null || village.communal.isEmpty()) {
                return;
            }
            root.putBoolean("OrorThiefRolled", true);
            if (sl.random.nextDouble() > 0.3) {
                return;
            }
            List<Long> boxes = new ArrayList<>(village.communal);
            BlockPos chest = BlockPos.of(boxes.get(sl.random.nextInt(boxes.size())));
            if (!sl.hasChunkAt(chest) || !(sl.getBlockEntity(chest) instanceof Container)) {
                return;
            }
            root.putString("OrorThief", "sneak");
            root.putLong("OrorThiefChest", chest.asLong());
            root.putLong("OrorThiefSince", now);
            return;
        }
        BlockPos chest = BlockPos.of(root.getLong("OrorThiefChest"));
        long since = root.getLong("OrorThiefSince");
        if (phase.equals("sneak")) {
            if (now - since > 2400L) {
                root.putString("OrorThief", "done");
                return;
            }
            t.getNavigation().moveTo(chest.getX() + 0.5, chest.getY(), chest.getZ() + 0.5, 0.43);
            if (t.distanceToSqr(Vec3.atCenterOf(chest)) < 6.25) {
                steal(sl, t, root, chest);
                root.putString("OrorThief", "flee");
                root.putLong("OrorThiefSince", now);
                witnesses(sl, t, root);
            }
        } else if (phase.equals("flee")) {
            if (now - since < 200L) {
                witnesses(sl, t, root);
            }
            VillageLedger.Village village = VillageLedger.get(sl).nearest(chest);
            if (village != null) {
                Vec3 out = t.position().subtract(Vec3.atCenterOf(village.center)).multiply(1.0, 0.0, 1.0);
                out = out.lengthSqr() < 1.0E-4 ? new Vec3(1.0, 0.0, 0.0) : out.normalize();
                t.getNavigation().moveTo(t.getX() + out.x * 16.0, t.getY(), t.getZ() + out.z * 16.0, 0.53);
            }
            if (now - since > 600L) {
                root.putString("OrorThief", "done");
            }
        }
    }

    private static void steal(ServerLevel sl, WanderingTrader t, CompoundTag root, BlockPos chest) {
        if (!(sl.getBlockEntity(chest) instanceof Container box)) {
            return;
        }
        RelicEffects.sound(sl, chest, SoundEvents.CHEST_OPEN, 0.6F, 1.0F);
        ListTag loot = root.getList("OrorLoot", 10);
        int taken = 0;
        for (int i = 0; i < box.getContainerSize() && taken < 3; i++) {
            ItemStack st = box.getItem(i);
            if (!st.isEmpty() && valuable(st)) {
                loot.add(st.save(sl.registryAccess()));
                box.setItem(i, ItemStack.EMPTY);
                taken++;
            }
        }
        box.setChanged();
        root.put("OrorLoot", loot);
        RelicEffects.sound(sl, chest, SoundEvents.CHEST_CLOSE, 0.6F, 1.0F);
    }

    /** Anyone who sees it at it - a player within 24 blocks, a villager within 12 - is to be silenced. */
    private static void witnesses(ServerLevel sl, WanderingTrader t, CompoundTag root) {
        List<LivingEntity> seen = new ArrayList<>();
        for (Player p : sl.getEntitiesOfClass(Player.class, t.getBoundingBox().inflate(24.0, 8.0, 24.0),
                p -> !p.isCreative() && !p.isSpectator() && p.hasLineOfSight(t))) {
            seen.add(p);
            p.displayClientMessage(Component.literal("§c行商人が村の物資を盗むところを見てしまった！ 口封じに来る！"), true);
        }
        seen.addAll(sl.getEntitiesOfClass(Villager.class, t.getBoundingBox().inflate(12.0, 4.0, 12.0),
            v -> v.isAlive() && !v.isBaby() && !v.getPersistentData().getBoolean("OrorWanderer") && v.hasLineOfSight(t)));
        if (seen.isEmpty()) {
            return;
        }
        root.putString("OrorThief", "seen");
        for (LivingEntity w : seen) {
            reveal(sl, t, w);
        }
    }

    // ------------------------------------------------------------------------------------- caravans
    /** Rarely (about once in a few days per player, in the open by day), a great caravan comes into view. */
    private static void caravans(ServerLevel sl) {
        if (!sl.dimension().location().getPath().equals("overworld") || sl.getGameTime() % 6000L != 3000L || !sl.isDay()) {
            return;
        }
        for (ServerPlayer p : sl.players()) {
            if (p.isSpectator() || sl.random.nextDouble() > 0.04 || VillageLedger.get(sl).nearest(p.blockPosition()) != null) {
                continue;
            }
            if (!sl.getEntitiesOfClass(WanderingTrader.class, p.getBoundingBox().inflate(256.0), x -> x.getPersistentData().hasUUID("OrorCaravan")).isEmpty()) {
                continue;
            }
            double a = sl.random.nextDouble() * Math.PI * 2.0;
            BlockPos at = VillageExpeditions.top(sl, p.blockPosition().offset((int)(Math.cos(a) * 56.0), 0, (int)(Math.sin(a) * 56.0)));
            if (at == null || !sl.getFluidState(at.below()).isEmpty() || !sl.getBlockState(at).canBeReplaced()) {
                continue;
            }
            caravan(sl, at, sl.random.nextDouble() * Math.PI * 2.0);
            p.displayClientMessage(Component.literal("§6地平の向こうに大キャラバンが見える。ふつうは手に入らない品を扱っているらしい"), false);
        }
    }

    private static void caravan(ServerLevel sl, BlockPos at, double heading) {
        UUID id = UUID.randomUUID();
        long until = sl.getGameTime() + 24000L;
        for (Villager g : VillageExpeditions.party(sl, at, heading, null, "のキャラバン護衛", 6, false)) {
            CompoundTag root = g.getPersistentData();
            root.putUUID("OrorCaravan", id);
            root.putLong("OrorWanderUntil", until);
            g.setCustomName(Component.literal("大キャラバンの護衛"));
        }
        for (int i = 0; i < 3; i++) {
            WanderingTrader t = (WanderingTrader)EntityType.WANDERING_TRADER.create(sl);
            if (t == null) {
                return;
            }
            t.moveTo(at.getX() + 0.5 + (i - 1) * 2.5, at.getY(), at.getZ() + 2.5, (float)Math.toDegrees(heading), 0.0F);
            t.getPersistentData().putUUID("OrorCaravan", id);
            t.setDespawnDelay(24000);
            t.setPersistenceRequired();
            t.setCustomName(Component.literal("大キャラバンの商人"));
            t.setCustomNameVisible(true);
            if (!sl.addFreshEntity(t)) {
                continue;
            }
            for (int j = 0; j < 3; j++) {
                TraderLlama l = (TraderLlama)EntityType.TRADER_LLAMA.create(sl);
                if (l == null) {
                    break;
                }
                l.moveTo(t.getX() + (j - 1) * 1.5, t.getY(), t.getZ() + 2.0, t.getYRot(), 0.0F);
                l.getPersistentData().putUUID("OrorCaravan", id);
                if (sl.addFreshEntity(l)) {
                    l.setLeashedTo(t, true);
                }
            }
        }
    }

    /** A caravan trader keeps up with its guards. */
    private static void follow(ServerLevel sl, WanderingTrader t, CompoundTag root) {
        UUID id = root.getUUID("OrorCaravan");
        Villager guard = null;
        double best = 64.0 * 64.0;
        for (Villager g : sl.getEntitiesOfClass(Villager.class, t.getBoundingBox().inflate(64.0),
                x -> x.isAlive() && x.getPersistentData().hasUUID("OrorCaravan") && id.equals(x.getPersistentData().getUUID("OrorCaravan")))) {
            double d = t.distanceToSqr(g);
            if (d < best) {
                best = d;
                guard = g;
            }
        }
        if (guard != null && best > 36.0) {
            t.getNavigation().moveTo(guard, 0.43);
        }
    }

    /** VillageExpeditions.wander: a caravan guard does not leave its traders behind. True while it walks back to them. */
    static boolean escort(Villager g, ServerLevel sl) {
        UUID id = g.getPersistentData().getUUID("OrorCaravan");
        WanderingTrader near = null;
        double best = Double.MAX_VALUE;
        for (WanderingTrader t : sl.getEntitiesOfClass(WanderingTrader.class, g.getBoundingBox().inflate(64.0),
                x -> x.isAlive() && x.getPersistentData().hasUUID("OrorCaravan") && id.equals(x.getPersistentData().getUUID("OrorCaravan")))) {
            double d = g.distanceToSqr(t);
            if (d < best) {
                best = d;
                near = t;
            }
        }
        if (near != null && best > 16.0 * 16.0) {
            VillageAI.walk(g, near.blockPosition(), VillageAI.pace(g, VillageAI.WORK), 3);
            VillagerLife.data(g).putString("Task", "キャラバンの護衛");
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------------------------------- the end of it
    /** VillageReputation.death: word to the player who brought a trader in its true colours down. */
    static void died(LivingDeathEvent e) {
        if (e.getEntity() instanceof WanderingTrader t && t.getPersistentData().getBoolean("OrorRevealed") && e.getSource().getEntity() instanceof Player p) {
            p.displayClientMessage(Component.literal("§a闇の行商人を倒した"), true);
        }
    }

    /** VillagerIndustry.drops: what a trader stole and carried; a fallen turret's scrap. */
    static void drops(LivingDropsEvent e) {
        if (!(e.getEntity().level() instanceof ServerLevel sl)) {
            return;
        }
        LivingEntity v = e.getEntity();
        CompoundTag root = v.getPersistentData();
        List<ItemStack> out = new ArrayList<>();
        if (v instanceof WanderingTrader t) {
            for (Tag x : root.getList("OrorLoot", 10)) {
                ItemStack st = ItemStack.parseOptional(sl.registryAccess(), (CompoundTag)x);
                if (!st.isEmpty()) {
                    out.add(st);
                }
            }
            if (root.getBoolean("OrorRevealed")) {
                VillageFeuds.add(out, sl, "emerald", 16, 40);
                for (String g : new String[]{"superbwarfare:m18_smoke_grenade", "superbwarfare:hand_grenade"}) {
                    Item it = item(g);
                    if (it != null && sl.random.nextInt(2) == 0) {
                        out.add(it.getDefaultInstance().copyWithCount(2 + sl.random.nextInt(3)));
                    }
                }
                Item taser = item("superbwarfare:taser");
                if (taser != null && sl.random.nextDouble() < 0.25) {
                    out.add(taser.getDefaultInstance());
                }
                if (root.hasUUID("OrorCaravan")) {
                    // a caravan merchant's goods: one or two of its rare wares
                    List<ItemStack> wares = new ArrayList<>();
                    for (MerchantOffer o : t.getOffers()) {
                        wares.add(o.getResult().copy());
                    }
                    for (int i = 0; i < 2 && !wares.isEmpty(); i++) {
                        if (sl.random.nextDouble() < 0.5) {
                            out.add(wares.remove(sl.random.nextInt(wares.size())));
                        }
                    }
                }
            }
        } else if (v instanceof Llama && root.getBoolean("OrorTurret")) {
            VillageFeuds.add(out, sl, "iron_ingot", 4, 8);
            VillageFeuds.add(out, sl, "gunpowder", 4, 8);
        }
        for (ItemStack st : out) {
            e.getDrops().add(new ItemEntity(sl, v.getX(), v.getY() + 0.5, v.getZ(), st));
        }
    }
}
