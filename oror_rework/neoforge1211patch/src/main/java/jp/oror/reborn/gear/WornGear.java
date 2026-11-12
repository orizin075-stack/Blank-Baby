package jp.oror.reborn.gear;

import java.util.ArrayList;
import java.util.List;
import jp.oror.reborn.combat.MobGuard;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;
import top.theillusivec4.curios.api.CuriosApi;
import top.theillusivec4.curios.api.SlotResult;

/**
 * (052) The gear that can be worn is worn (Curios): what it did in the hand or the off hand it does on the body, and
 * what had to be used is set off by what it was made for.
 * <ul>
 * <li>the rewind talisman (首飾り / necklace): a blow that would kill turned back, the talisman spent (as in the off
 * hand);</li>
 * <li>the Villager King's token (necklace): Hero of the Village II while it is worn (as in the hand);</li>
 * <li>the parry emblem (腕輪 / bracelet: a buckler on the left forearm): a blow struck at the wearer from the front, hand
 * to hand, turned aside and answered (its parry, 256), when it is ready (five seconds);</li>
 * <li>the dodge talon (手 / hands: on the right hand): a blow or a shot, when it is ready (three seconds), dodged: the
 * wearer is a few steps to the side and unhurt;</li>
 * <li>the squad banner (背中 / back: a banner worn on the back): when the wearer strikes or is struck in a fight and it
 * is ready (thirty seconds), it rallies the band within twelve blocks (healed, Strength IV, Resistance III);</li>
 * <li>the last bloom (頭 / head: in the hair): a blow that would kill, when it is ready (three minutes), turned aside
 * (as in the off hand).</li>
 * </ul>
 * The gear works as before in the hand; the cooldown is the item's, held or worn. Without Curios nothing here runs.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class WornGear {
    public static final String NS = "oror_supreme_bosses";
    public static final boolean CURIOS = ModList.get().isLoaded("curios");
    /** What can be worn (data/curios/tags/item: necklace, bracelet, hands, back, head). */
    public static final java.util.Set<String> WEARABLE = java.util.Set.of("rewind_talisman", "villager_king_token", "parry_emblem",
        "dodge_talon", "squad_banner", "last_bloom");

    private WornGear() {
    }

    public static Item item(String id) {
        return BuiltInRegistries.ITEM.get(ResourceLocation.fromNamespaceAndPath(NS, id));
    }

    /** The first of this gear the entity wears (the stack itself), or empty. */
    public static ItemStack worn(LivingEntity e, Item item) {
        return CURIOS && item != Items.AIR ? Curio.first(e, item, false) : ItemStack.EMPTY;
    }

    /** The first of this gear the entity wears and shows (its slot's render toggle on), or empty. */
    public static ItemStack shown(LivingEntity e, Item item) {
        return CURIOS && item != Items.AIR ? Curio.first(e, item, true) : ItemStack.EMPTY;
    }

    /** The Curios side, only loaded when Curios is. */
    static final class Curio {
        private Curio() {
        }

        static ItemStack first(LivingEntity e, Item item, boolean shownOnly) {
            // by a predicate, not by the item: Curios keeps what it found for an item until the wearer next ticks, so a
            // look before the item is put on would hide it until then
            List<SlotResult> found = CuriosApi.getCuriosInventory(e).map(h -> h.findCurios((ItemStack st) -> st.is(item))).orElse(List.of());
            for (SlotResult r : found) {
                if (!r.stack().isEmpty() && (!shownOnly || r.slotContext().visible() && !r.slotContext().cosmetic())) {
                    return r.stack();
                }
            }
            if (shownOnly) {
                // a cosmetic slot shows what it holds
                for (SlotResult r : found) {
                    if (!r.stack().isEmpty() && r.slotContext().cosmetic()) {
                        return r.stack();
                    }
                }
            }
            return ItemStack.EMPTY;
        }

        /** The slot ids a player has, each with its number of slots (id:n). */
        static List<String> slots(LivingEntity e) {
            List<String> out = new ArrayList<>();
            CuriosApi.getCuriosInventory(e).ifPresent(h -> h.getCurios().forEach((id, st) -> out.add(id + ":" + st.getSlots())));
            return out;
        }

        static boolean wear(LivingEntity e, String slot, ItemStack s) {
            return CuriosApi.getCuriosInventory(e).map(h -> {
                if (h.getStacksHandler(slot).isEmpty() && h.getCurios().isEmpty()) {
                    // an inventory never set up (a player that has not joined a level): its slots as they should be
                    h.reset();
                }
                if (h.getStacksHandler(slot).map(st -> st.getSlots() < 1).orElse(true)) {
                    return false;
                }
                h.setEquippedCurio(slot, 0, s);
                return ItemStack.matches(h.getStacksHandler(slot).get().getStacks().getStackInSlot(0), s);
            }).orElse(false);
        }
    }

    /** The slot ids the entity has (empty without Curios). */
    public static List<String> slots(LivingEntity e) {
        return CURIOS ? Curio.slots(e) : List.of();
    }

    /** Puts the stack in the entity's first slot of that kind (the CI and the look check); false if it has none. */
    public static boolean wear(LivingEntity e, String slot, ItemStack s) {
        return CURIOS && Curio.wear(e, slot, s);
    }

    private static boolean ready(Player p, Item item) {
        return !p.getCooldowns().isOnCooldown(item);
    }

    private static boolean enemy(Player p, Entity e) {
        return e instanceof LivingEntity l && l != p && l.isAlive() && !l.isAlliedTo(p) && !l.isSpectator()
            && !(l instanceof Player q && q.isCreative()) && (l instanceof Enemy || l instanceof Mob m && m.getTarget() == p || l instanceof Player);
    }

    private static void sparkle(ServerLevel sl, LivingEntity at, net.minecraft.core.particles.ParticleOptions kind, int n) {
        sl.sendParticles(kind, at.getX(), at.getY() + 1.0, at.getZ(), n, 0.5, 0.5, 0.5, 0.02);
    }

    // ---------------------------------------------------------------------------------------------- blows and shots

    /** After the gear's own handlers (in the hand and the off hand, which cancel first): only what is worn. */
    @SubscribeEvent(priority = EventPriority.LOW)
    public static void hurt(LivingIncomingDamageEvent e) {
        if (!CURIOS || !(e.getEntity().level() instanceof ServerLevel sl)) {
            return;
        }
        DamageSource src = e.getSource();
        if (src.getEntity() instanceof Player striker && striker != e.getEntity() && enemy(striker, e.getEntity())) {
            rally(sl, striker);
        }
        if (!(e.getEntity() instanceof Player p) || src.is(DamageTypeTags.BYPASSES_INVULNERABILITY) || p.isCreative() || p.isSpectator()) {
            return;
        }
        if (parry(sl, p, e) || dodge(sl, p, e)) {
            return;
        }
        if (src.getEntity() != null && enemy(p, src.getEntity())) {
            rally(sl, p);
        }
        if (e.getAmount() >= p.getHealth()) {
            lastBreath(sl, p, e);
        }
    }

    /** The parry emblem: a blow from in front, hand to hand, turned aside and answered. */
    private static boolean parry(ServerLevel sl, Player p, LivingIncomingDamageEvent e) {
        Item emblem = item("parry_emblem");
        DamageSource src = e.getSource();
        if (!(src.getDirectEntity() instanceof LivingEntity attacker) || src.getEntity() != attacker || !enemy(p, attacker)
            || src.is(DamageTypeTags.IS_EXPLOSION) || src.is(DamageTypeTags.IS_FIRE) || !ready(p, emblem) || worn(p, emblem).isEmpty()) {
            return false;
        }
        Vec3 look = p.getLookAngle().multiply(1, 0, 1);
        Vec3 to = attacker.position().subtract(p.position()).multiply(1, 0, 1);
        if (look.lengthSqr() < 1.0E-4 || to.lengthSqr() < 1.0E-4 || look.normalize().dot(to.normalize()) < 0.2) {
            return false;
        }
        e.setCanceled(true);
        attacker.hurt(p.damageSources().playerAttack(p), 256.0F);
        MobGuard.parried(attacker, p.position());
        p.getCooldowns().addCooldown(emblem, 100);
        sl.playSound(null, p.blockPosition(), SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 1.0F, 1.3F);
        sl.playSound(null, p.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.35F, 1.8F);
        sparkle(sl, p, ParticleTypes.END_ROD, 20);
        return true;
    }

    /** The dodge talon: a blow or a shot dodged, the wearer a few steps to the side of it. */
    private static boolean dodge(ServerLevel sl, Player p, LivingIncomingDamageEvent e) {
        Item talon = item("dodge_talon");
        DamageSource src = e.getSource();
        Entity from = src.getDirectEntity() != null ? src.getDirectEntity() : src.getEntity();
        if (from == null || from == p || e.getAmount() < 2.0F || src.is(DamageTypeTags.IS_EXPLOSION) || src.is(DamageTypeTags.IS_FIRE)
            || !ready(p, talon) || worn(p, talon).isEmpty()) {
            return false;
        }
        Vec3 to = from.position().subtract(p.position()).multiply(1, 0, 1);
        if (to.lengthSqr() < 1.0E-4) {
            to = p.getLookAngle().multiply(1, 0, 1);
        }
        Vec3 side = new Vec3(-to.z, 0, to.x).normalize();
        if (p.getRandom().nextBoolean()) {
            side = side.scale(-1);
        }
        Vec3 dest = null;
        for (Vec3 dir : new Vec3[]{side, side.scale(-1), to.normalize().scale(-1)}) {
            for (double d = 3.0; d >= 1.0; d -= 0.5) {
                Vec3 off = dir.scale(d);
                net.minecraft.world.phys.AABB box = p.getBoundingBox().move(off);
                // (059d, V20 05_weapons_12.md) only where the wearer lands safely: room to stand, and (when standing) a
                // floor within three blocks under it, not over a drop nor into water or lava
                if (sl.noCollision(p, box) && (!p.onGround() || !sl.noCollision(p, box.expandTowards(0, -3.0, 0)))
                    && !sl.containsAnyLiquid(box.expandTowards(0, -1.0, 0))) {
                    dest = p.position().add(off);
                    break;
                }
            }
            if (dest != null) {
                break;
            }
        }
        if (dest == null) {
            return false;
        }
        e.setCanceled(true);
        sparkle(sl, p, ParticleTypes.CLOUD, 12);
        p.teleportTo(dest.x, dest.y, dest.z);
        p.getCooldowns().addCooldown(talon, 60);
        sl.playSound(null, p.blockPosition(), SoundEvents.PHANTOM_FLAP, SoundSource.PLAYERS, 0.8F, 1.6F);
        return true;
    }

    /** The squad banner on the back: in a fight, when it is ready, the band is rallied. */
    private static void rally(ServerLevel sl, Player p) {
        Item banner = item("squad_banner");
        if (!ready(p, banner) || worn(p, banner).isEmpty()) {
            return;
        }
        List<LivingEntity> band = new ArrayList<>(List.of(p));
        band.addAll(sl.getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(12.0), x -> x != p && (x.isAlliedTo(p)
            || x.getPersistentData().hasUUID("ororRelicOwner") && x.getPersistentData().getUUID("ororRelicOwner").equals(p.getUUID()))));
        for (LivingEntity x : band) {
            x.heal(20.0F);
            x.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 400, 3));
            x.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 400, 2));
        }
        p.getCooldowns().addCooldown(banner, 600);
        sl.playSound(null, p.blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.PLAYERS, 0.6F, 1.4F);
        sparkle(sl, p, ParticleTypes.END_ROD, 30);
    }

    /** A blow that would kill: the last bloom in the hair (when it is ready), else the rewind talisman round the neck. */
    private static void lastBreath(ServerLevel sl, Player p, LivingIncomingDamageEvent e) {
        Item bloom = item("last_bloom");
        if (ready(p, bloom) && !worn(p, bloom).isEmpty()) {
            e.setCanceled(true);
            p.setHealth(Math.min(p.getMaxHealth(), 12.0F));
            p.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 300, 4));
            p.getCooldowns().addCooldown(bloom, 3600);
            sparkle(sl, p, ParticleTypes.CHERRY_LEAVES, 40);
            sl.playSound(null, p.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.6F, 1.4F);
            return;
        }
        Item talisman = item("rewind_talisman");
        ItemStack t = worn(p, talisman);
        long now = sl.getGameTime();
        if (!t.isEmpty() && now >= p.getPersistentData().getLong("ororRelicSaveUntil")) {
            e.setCanceled(true);
            p.getPersistentData().putLong("ororRelicSaveUntil", now + 200L);
            p.setHealth(p.getMaxHealth());
            t.shrink(1);
            p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 100, 4));
            sparkle(sl, p, ParticleTypes.REVERSE_PORTAL, 40);
            sl.playSound(null, p.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.6F, 0.7F);
        }
    }

    // -------------------------------------------------------------------------------------------------------- the token

    @SubscribeEvent
    public static void tick(PlayerTickEvent.Post e) {
        Player p = e.getEntity();
        if (!CURIOS || p.level().isClientSide || p.tickCount % 40 != 0) {
            return;
        }
        ItemStack token = worn(p, item("villager_king_token"));
        if (!token.isEmpty() && token.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag().getInt("LivesDefeated") == 4) {
            p.addEffect(new MobEffectInstance(MobEffects.HERO_OF_THE_VILLAGE, 100, 1, true, false));
        }
    }
}
