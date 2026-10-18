package jp.oror.reborn;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.EnchantedBookItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.living.LivingDropsEvent;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;

/**
 * Wandering expedition parties, and the price of crossing one (v0.17.16).
 * - Rich: a fallen party member drops its enchanted netherite gear and weapon and the pack it has carried on its travels
 *   (emeralds, diamonds, netherite, enchanted books, golden apples, totems, the spoils of the Nether and the End).
 * - Feuds: now and then two parties from different villages meet on the road and fight it out.
 * - No witnesses: a player who attacks a party has to finish it. A badly hurt member runs; one that gets 40 blocks away
 *   (or runs for 45 seconds), or a party the player leaves behind for half a minute, gets home and tells - and from then
 *   on every village in the world knows. Every village's score for that player is the lowest there is (villagers refuse
 *   them and strong villagers attack), iron golems turn on them, and wandering parties hunt them down.
 */
public final class VillageFeuds {
    private VillageFeuds() {
    }

    // ------------------------------------------------------------------------------------- outlaws
    private static VillageProgress world(ServerLevel sl) {
        return VillageProgress.get(sl.getServer().overworld());
    }

    /** Known to every village as an attacker of an expedition party. */
    static boolean outlaw(ServerLevel sl, UUID player) {
        return world(sl).outlaws.containsKey(player);
    }

    /** Word reaches every village: the lowest score everywhere, and news for every player on the server. */
    static void declare(ServerLevel sl, UUID player, String name, String party) {
        VillageProgress db = world(sl);
        if (db.outlaws.containsKey(player)) {
            return;
        }
        db.outlaws.put(player, name);
        db.setDirty();
        ServerLevel ow = sl.getServer().overworld();
        VillageLedger ledger = VillageLedger.get(ow);
        for (VillageLedger.Village v : new ArrayList<>(ledger.villages.values())) {
            ledger.change(v, player, -2000, ow.getGameTime(), "遠征隊襲撃の噂");
        }
        Component line = Component.literal("【急報】" + party + "の生き残りが村へ逃げ帰り、" + name
            + "が遠征隊を襲ったことが世界中の村に知れ渡った。すべての村が敵に回った");
        for (Object o : sl.getServer().getPlayerList().getPlayers()) {
            if (o instanceof ServerPlayer p) {
                p.sendSystemMessage(line);
            }
        }
    }

    /** The village review (every 30 s): a village that has not heard yet, or a score that crept back up, is set right. */
    static void enforce(ServerLevel sl, VillageLedger.Village village) {
        VillageProgress db = world(sl);
        if (db.outlaws.isEmpty()) {
            return;
        }
        VillageLedger ledger = VillageLedger.get(sl);
        for (UUID id : db.outlaws.keySet()) {
            if (village.score(id) > -900) {
                ledger.change(village, id, -2000, sl.getGameTime(), "遠征隊襲撃の噂");
            }
        }
    }

    // ------------------------------------------------------------------------------------- engaging a party
    private static UUID party(CompoundTag root) {
        return root.hasUUID("OrorParty") ? root.getUUID("OrorParty") : (root.hasUUID("OrorVillage") ? root.getUUID("OrorVillage") : null);
    }

    private static List<Villager> members(ServerLevel sl, Villager v, double range) {
        UUID id = party(v.getPersistentData());
        return sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(range),
            x -> x.isAlive() && x.getPersistentData().getBoolean("OrorWanderer") && id != null && id.equals(party(x.getPersistentData())));
    }

    /** WorldEvents.damage: a player hurting a party member sets the whole party on them. */
    static void attacked(LivingIncomingDamageEvent e) {
        if (e.getEntity() instanceof Villager v && v.level() instanceof ServerLevel sl && e.getSource().getEntity() instanceof Player p
            && !p.isCreative() && !p.isSpectator()) {
            CompoundTag root = v.getPersistentData();
            if (root.getBoolean("OrorWanderer") && !root.hasUUID("OrorCaravan")) {
                engage(sl, v, p);
            }
        }
    }

    static void engage(ServerLevel sl, Villager v, Player p) {
        boolean fresh = !v.getPersistentData().hasUUID("OrorEngaged");
        for (Villager m : members(sl, v, 64.0)) {
            CompoundTag root = m.getPersistentData();
            root.putUUID("OrorEngaged", p.getUUID());
            root.putString("OrorEngagedName", p.getName().getString());
            if (!root.getBoolean("OrorFleeing")) {
                m.setTarget(p);
            }
        }
        if (fresh && !outlaw(sl, p.getUUID())) {
            p.displayClientMessage(Component.literal("§c遠征隊に手を出した！ 一人でも逃がせば、世界中の村に知れ渡る"), true);
        }
    }

    /**
     * VillageExpeditions.wander (once a second): a party at war with a player, at feud with another party, or that has
     * caught sight of an outlaw. True when this has taken the party's second (its journey waits).
     */
    static boolean wander(Villager v, ServerLevel sl) {
        CompoundTag root = v.getPersistentData();
        long now = sl.getGameTime();
        if (root.hasUUID("OrorEngaged")) {
            UUID id = root.getUUID("OrorEngaged");
            Player p = sl.getPlayerByUUID(id);
            boolean near = p != null && p.isAlive() && !p.isSpectator() && v.distanceToSqr(p) < 96.0 * 96.0;
            if (!near) {
                // the player has gone: after half a minute the party goes home with the story
                int far = root.getInt("OrorEngagedFar") + 1;
                root.putInt("OrorEngagedFar", far);
                if (far >= 30) {
                    escape(sl, v, id, root.getString("OrorEngagedName"));
                }
                return true;
            }
            root.putInt("OrorEngagedFar", 0);
            if (!root.getBoolean("OrorFleeing") && v.getHealth() < v.getMaxHealth() * 0.3F) {
                root.putBoolean("OrorFleeing", true);
                root.putLong("OrorFleeSince", now);
                v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 1200, 1));
                if (!outlaw(sl, id)) {
                    p.displayClientMessage(Component.literal("§c" + v.getName().getString() + "が逃げ出した！ 逃がすと世界中の村に知られる"), true);
                }
            }
            if (root.getBoolean("OrorFleeing")) {
                v.setTarget(null);
                Vec3 away = v.position().subtract(p.position()).multiply(1.0, 0.0, 1.0);
                away = away.lengthSqr() < 1.0E-4 ? new Vec3(1.0, 0.0, 0.0) : away.normalize().scale(16.0);
                BlockPos to = VillageExpeditions.top(sl, v.blockPosition().offset((int)away.x, 0, (int)away.z));
                if (to != null) {
                    VillageAI.walk(v, to, VillageAI.pace(v, VillageAI.FLEE), 1);
                }
                VillagerLife.data(v).putString("Task", "逃走中");
                if (v.distanceToSqr(p) > 40.0 * 40.0 || now - root.getLong("OrorFleeSince") > 900L) {
                    escape(sl, v, id, p.getName().getString());
                }
                return true;
            }
            if (v.getTarget() != p && v.distanceToSqr(p) < 48.0 * 48.0) {
                v.setTarget(p);
            }
            VillagerLife.data(v).putString("Task", "交戦中");
            return true;
        }
        if (root.getBoolean("OrorHunter")) {
            // hunters keep making for the outlaw
            Player prey = null;
            double best = 160.0 * 160.0;
            for (Player x : sl.players()) {
                double d = v.distanceToSqr(x);
                if (d < best && !x.isCreative() && !x.isSpectator() && outlaw(sl, x.getUUID())) {
                    best = d;
                    prey = x;
                }
            }
            if (prey != null) {
                root.putDouble("OrorWanderHeading", Math.atan2(prey.getZ() - v.getZ(), prey.getX() - v.getX()));
            }
        }
        if (v.getTarget() != null && v.getTarget().isAlive()) {
            return false;
        }
        // an outlaw in sight: the party falls on them
        for (Player p : sl.getEntitiesOfClass(Player.class, v.getBoundingBox().inflate(24.0, 8.0, 24.0),
                x -> !x.isCreative() && !x.isSpectator() && outlaw(sl, x.getUUID()) && v.hasLineOfSight(x))) {
            engage(sl, v, p);
            VillagerLife.data(v).putString("Task", "お尋ね者の討伐");
            return true;
        }
        // a feud: the rival party within reach
        if (root.hasUUID("OrorRival")) {
            UUID rival = root.getUUID("OrorRival");
            Villager foe = null;
            double best = 18.0 * 18.0;
            for (Villager x : sl.getEntitiesOfClass(Villager.class, v.getBoundingBox().inflate(18.0, 6.0, 18.0),
                    x -> x.isAlive() && rival.equals(party(x.getPersistentData())))) {
                double d = v.distanceToSqr(x);
                if (d < best) {
                    best = d;
                    foe = x;
                }
            }
            if (foe != null) {
                v.setTarget(foe);
                VillagerLife.data(v).putString("Task", "遠征隊同士の争い");
                if (!root.getBoolean("OrorFeudSeen")) {
                    for (Villager m : members(sl, v, 48.0)) {
                        m.getPersistentData().putBoolean("OrorFeudSeen", true);
                    }
                    Component line = Component.literal("§6" + v.getName().getString() + "と" + foe.getName().getString() + "が鉢合わせし、争い始めた！");
                    for (Player p : sl.getEntitiesOfClass(Player.class, v.getBoundingBox().inflate(96.0))) {
                        p.displayClientMessage(line, false);
                    }
                }
                return true;
            }
        }
        return false;
    }

    /** A member gets away (or the party outlasted the player): word goes home. */
    private static void escape(ServerLevel sl, Villager v, UUID player, String name) {
        sl.sendParticles(ParticleTypes.CLOUD, v.getX(), v.getY() + 1.0, v.getZ(), 30, 0.5, 0.8, 0.5, 0.05);
        sl.sendParticles(ParticleTypes.PORTAL, v.getX(), v.getY() + 1.0, v.getZ(), 40, 0.4, 0.8, 0.4, 0.4);
        RelicEffects.sound(sl, v.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, 1.0F, 0.8F);
        String party = v.getName().getString();
        v.discard();
        declare(sl, player, name == null || name.isEmpty() ? "あるプレイヤー" : name, party);
    }

    /** VillageAI.tick: a fleeing member is left to run (no stand, no retaliation). */
    static boolean fleeing(Villager v) {
        return v.getPersistentData().getBoolean("OrorFleeing");
    }

    // ------------------------------------------------------------------------------------- the spoils
    /** VillagerIndustry.drops: a fallen party member's (or caravan guard's) gear and pack. */
    static void drops(LivingDropsEvent e) {
        if (!(e.getEntity() instanceof Villager v) || !(v.level() instanceof ServerLevel sl) || !v.getPersistentData().getBoolean("OrorWanderer")) {
            return;
        }
        List<ItemStack> bag = new ArrayList<>();
        for (EquipmentSlot slot : new EquipmentSlot[]{EquipmentSlot.MAINHAND, EquipmentSlot.OFFHAND, EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
            ItemStack st = v.getItemBySlot(slot);
            if (!st.isEmpty()) {
                bag.add(st.copy());
                v.setItemSlot(slot, ItemStack.EMPTY);
            }
        }
        boolean leader = v.getPersistentData().getBoolean("OrorLeader");
        bag.addAll(pack(sl, leader));
        for (ItemStack st : bag) {
            e.getDrops().add(new ItemEntity(sl, v.getX(), v.getY() + 0.5, v.getZ(), st));
        }
    }

    /** What a party member carries home from its travels. */
    static List<ItemStack> pack(ServerLevel sl, boolean leader) {
        List<ItemStack> out = new ArrayList<>();
        add(out, sl, "emerald", 12, 40);
        if (leader) {
            add(out, sl, "emerald_block", 3, 8);
        }
        add(out, sl, "diamond", 3, 10);
        if (chance(sl, 0.4)) {
            add(out, sl, "netherite_ingot", 1, 2);
        }
        if (chance(sl, 0.3)) {
            add(out, sl, "ancient_debris", 2, 4);
        }
        add(out, sl, "golden_apple", 2, 4);
        if (chance(sl, 0.1)) {
            add(out, sl, "enchanted_golden_apple", 1, 1);
        }
        if (chance(sl, 0.2)) {
            add(out, sl, "totem_of_undying", 1, 1);
        }
        add(out, sl, "ender_pearl", 4, 12);
        add(out, sl, "blaze_rod", 3, 8);
        add(out, sl, "experience_bottle", 8, 24);
        if (chance(sl, 0.25)) {
            add(out, sl, "shulker_shell", 2, 4);
        }
        if (chance(sl, 0.15)) {
            add(out, sl, "netherite_upgrade_smithing_template", 1, 1);
        }
        if (chance(sl, 0.2)) {
            add(out, sl, "dragon_breath", 1, 3);
        }
        if (chance(sl, 0.05)) {
            add(out, sl, "elytra", 1, 1);
        }
        int books = 1 + sl.random.nextInt(leader ? 3 : 2);
        for (int i = 0; i < books; i++) {
            out.add(book(sl));
        }
        return out;
    }

    private static final Object[][] BOOKS = {
        {Enchantments.MENDING, 1}, {Enchantments.PROTECTION, 4}, {Enchantments.SHARPNESS, 5}, {Enchantments.EFFICIENCY, 5},
        {Enchantments.FORTUNE, 3}, {Enchantments.LOOTING, 3}, {Enchantments.UNBREAKING, 3}, {Enchantments.FEATHER_FALLING, 4},
        {Enchantments.POWER, 5}, {Enchantments.SILK_TOUCH, 1}, {Enchantments.MENDING, 1}
    };

    @SuppressWarnings("unchecked")
    private static ItemStack book(ServerLevel sl) {
        Object[] b = BOOKS[sl.random.nextInt(BOOKS.length)];
        Holder<Enchantment> h = sl.registryAccess().registryOrThrow(Registries.ENCHANTMENT).getHolderOrThrow((ResourceKey<Enchantment>)b[0]);
        return EnchantedBookItem.createForEnchantment(new EnchantmentInstance(h, (Integer)b[1]));
    }

    static void add(List<ItemStack> out, ServerLevel sl, String id, int min, int max) {
        Item item = (Item)BuiltInRegistries.ITEM.get(ResourceLocation.withDefaultNamespace(id));
        int n = min + (max > min ? sl.random.nextInt(max - min + 1) : 0);
        while (n > 0 && item != null && item != net.minecraft.world.item.Items.AIR) {
            int part = Math.min(n, item.getDefaultInstance().getMaxStackSize());
            out.add(item.getDefaultInstance().copyWithCount(part));
            n -= part;
        }
    }

    private static boolean chance(ServerLevel sl, double p) {
        return sl.random.nextDouble() < p;
    }

    /** VillageReputation.death: the last of a party falls, and nobody will tell. */
    static void died(LivingDeathEvent e) {
        if (e.getEntity() instanceof Villager v && v.level() instanceof ServerLevel sl && v.getPersistentData().hasUUID("OrorEngaged")
            && e.getSource().getEntity() instanceof Player p && p.getUUID().equals(v.getPersistentData().getUUID("OrorEngaged"))) {
            List<Villager> left = members(sl, v, 128.0);
            left.remove(v);
            if (left.isEmpty() && !outlaw(sl, p.getUUID())) {
                p.displayClientMessage(Component.literal("§a遠征隊を全滅させた。噂が広まることはない"), false);
            }
        }
    }

    /** VillageReputation.tick: an outlaw near a villager - the villager remembers it the vanilla way too (iron golems act on it). */
    static void gossip(Villager v, Player p) {
        if (v.level() instanceof ServerLevel sl && outlaw(sl, p.getUUID())) {
            v.getGossips().add(p.getUUID(), net.minecraft.world.entity.ai.gossip.GossipType.MAJOR_NEGATIVE, 25);
        }
    }
}
