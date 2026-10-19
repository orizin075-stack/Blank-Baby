package jp.oror.reborn;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.ArmorItem.Type;
import net.minecraft.world.item.ArmorMaterial.Layer;
import net.minecraft.world.item.Item.Properties;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ClipContext.Fluid;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent.RightClickBlock;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.RegistryObject;
import net.minecraftforge.registries.DeferredRegister;

public final class AdventureContent {
    public static final List<RegistryObject<?>> CONTENT = new ArrayList<>();
    public static final DeferredRegister<ArmorMaterial> MATERIALS = DeferredRegister.create(Registries.ARMOR_MATERIAL, "oror_supreme_bosses");
    public static final RegistryObject<Item> STAR = plain("star_shard");
    public static final RegistryObject<Item> DRAGON = plain("dragon_core");
    public static final RegistryObject<Item> FORGE = plain("forge_core");
    public static final RegistryObject<Item> CURSE = plain("curse_residue");
    public static final RegistryObject<Item> THREAD = plain("world_thread");
    public static final RegistryObject<ArmorMaterial> ARMOR = MATERIALS.register(
        "dragon_furnace",
        () -> new ArmorMaterial(
                Map.of(Type.HELMET, 5, Type.CHESTPLATE, 12, Type.LEGGINGS, 9, Type.BOOTS, 5, Type.BODY, 12),
                25,
                SoundEvents.ARMOR_EQUIP_NETHERITE,
                () -> Ingredient.of(new ItemLike[]{(ItemLike)DRAGON.get()}),
                List.of(new Layer(new ResourceLocation("oror_supreme_bosses", "dragon_furnace"))),
                4.0F,
                0.2F
            )
    );
    public static final RegistryObject<SwordItem> BLADE = add(OrorReborn.ITEMS.register("azure_blade", () -> new AdventureContent.AzureBlade()));
    public static final RegistryObject<Item> STAFF = add(OrorReborn.ITEMS.register("star_staff", () -> new AdventureContent.Staff()));
    public static final RegistryObject<Item> TOOL = add(OrorReborn.ITEMS.register("forge_tool", () -> new AdventureContent.RepairTool()));
    public static final RegistryObject<Item> TALISMAN = plain("rewind_talisman");
    public static final RegistryObject<Item> DEW = add(OrorReborn.ITEMS.register("purifying_dew", () -> new AdventureContent.Dose(false)));
    public static final RegistryObject<Item> MANA = add(OrorReborn.ITEMS.register("mana_crystal", () -> new AdventureContent.Dose(true)));
    public static final RegistryObject<Item> KEY = plain("dungeon_key");
    public static final RegistryObject<Item> GUIDE = add(OrorReborn.ITEMS.register("field_guide", () -> new AdventureContent.Guide()));
    public static final RegistryObject<ArmorItem> COAT = add(OrorReborn.ITEMS.register("dragon_coat", () -> new AdventureContent.RelicArmor(Type.CHESTPLATE)));
    public static final RegistryObject<ArmorItem> BOOTS = add(OrorReborn.ITEMS.register("teia_boots", () -> new AdventureContent.RelicArmor(Type.BOOTS)));
    public static final Map<String, RegistryObject<Block>> GATES = new LinkedHashMap<>();
    public static final Map<String, String> GATE_BOSSES = Map.of(
        "sword_gate", "kokuhaku", "laboratory_gate", "relentless_research", "tragedy_gate", "cursed_love"
    );

    private static <T extends Item> RegistryObject<T> add(RegistryObject<T> i) {
        CONTENT.add(i);
        return i;
    }

    private static RegistryObject<Item> plain(String id) {
        return add(OrorReborn.ITEMS.registerSimpleItem(id, new Properties().rarity(Rarity.RARE)));
    }

    private static boolean hostile(Player p, LivingEntity e) {
        if (e == p || !e.isAlive() || e.isAlliedTo(p) || e.isSpectator()) {
            return false;
        } else {
            if (e instanceof Player q && q.isCreative()) {
                return false;
            }

            if (e instanceof SupremeEntity b) {
                return !p.getUUID().equals(b.owner) && b.getTarget() == p;
            }

            if (e instanceof Enemy) {
                return true;
            } else {
                if (e instanceof Mob m && m.getTarget() == p) {
                    return true;
                }

                return false;
            }
        }
    }

    private static void used(Player p, InteractionHand h, Item item, int cooldown) {
        if (!p.isCreative()) {
            p.getItemInHand(h).shrink(1);
        }

        p.getCooldowns().addCooldown(item, cooldown);
    }

    public static void damage(LivingHurtEvent e) {
        LivingEntity p = e.getEntity();
        if (!p.level().isClientSide
            && !e.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)
            && p instanceof Player
            && p.getOffhandItem().is((Item)TALISMAN.get())
            && !(e.getAmount() < p.getHealth())
            && p.level().getGameTime() >= p.getPersistentData().getLong("ororRelicSaveUntil")) {
            p.getPersistentData().putLong("ororRelicSaveUntil", p.level().getGameTime() + 200L);
            p.setHealth(p.getMaxHealth());
            p.getOffhandItem().shrink(1);
            p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 100, 4));
            e.setAmount(0.0F);
            e.setCanceled(true);
            System.out.println("[OROR_RELIC_TEST] lethal hit canceled");
        }
    }

    public static void gate(RightClickBlock e) {
        if (!e.getLevel().isClientSide) {
            Player p = e.getEntity();

            for (Entry<String, RegistryObject<Block>> entry : GATES.entrySet()) {
                if (e.getLevel().getBlockState(e.getPos()).is((Block)entry.getValue().get())) {
                    if (!p.isCreative() && !e.getItemStack().is((Item)KEY.get())) {
                        p.displayClientMessage(Component.literal("封域の鍵が必要です。"), true);
                        e.setCanceled(true);
                        return;
                    }

                    SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(GATE_BOSSES.get(entry.getKey())).get()).create(e.getLevel());
                    if (b == null) {
                        return;
                    }

                    BlockPos at = e.getPos().above();
                    b.moveTo((double)at.getX() + 0.5, (double)at.getY(), (double)at.getZ() + 0.5, 0.0F, 0.0F);
                    if (e.getLevel().noCollision(b)) {
                        b.arena = true;
                        if (!p.isCreative()) {
                            b.setTarget(p);
                        }

                        e.getLevel().removeBlock(e.getPos(), false);
                        e.getLevel().addFreshEntity(b);
                        if (!p.isCreative()) {
                            e.getItemStack().shrink(1);
                        }

                        e.setCanceled(true);
                    }

                    return;
                }
            }
        }
    }

    static {
        for (String id : GATE_BOSSES.keySet().stream().sorted().toList()) {
            RegistryObject<Block> b = LegacyContent.BLOCKS
                .register(id, () -> new Block(net.minecraft.world.level.block.state.BlockBehaviour.Properties.of().strength(8.0F, 120.0F).lightLevel(s -> 10)));
            GATES.put(id, b);
            add(OrorReborn.ITEMS.register(id, () -> new BlockItem((Block)b.get(), new Properties())));
        }
    }

    public static final class AzureBlade extends SwordItem {
        AzureBlade() {
            super(
                Tiers.NETHERITE,
                new Properties().durability(4096).fireResistant().rarity(Rarity.EPIC).attributes(SwordItem.createAttributes(Tiers.NETHERITE, 28, -2.0F))
            );
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            ItemStack stack = p.getItemInHand(h);
            if (p.getCooldowns().isOnCooldown(this)) {
                return InteractionResultHolder.fail(stack);
            } else {
                if (l instanceof ServerLevel sl) {
                    Vec3 start = p.getEyePosition();
                    Vec3 dir = p.getLookAngle();
                    BlockHitResult ray = l.clip(
                        new ClipContext(start, start.add(dir.scale(24.0)), net.minecraft.world.level.ClipContext.Block.COLLIDER, Fluid.NONE, p)
                    );
                    double reach = start.distanceTo(ray.getLocation());

                    for (double n = 0.0; n < reach; n += 0.6) {
                        Vec3 v = start.add(dir.scale(n));
                        sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, v.x, v.y, v.z, 1, 0.0, 0.0, 0.0, 0.0);
                    }

                    for (LivingEntity e : l.getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(25.0), v -> AdventureContent.hostile(p, v))) {
                        Vec3 d = e.getBoundingBox().getCenter().subtract(start);
                        double along = d.dot(dir);
                        if (along >= 0.0 && along <= reach + 1.0 && d.subtract(dir.scale(along)).length() < 2.0) {
                            e.hurt(p.damageSources().playerAttack(p), 256.0F);
                        }
                    }

                    stack.hurtAndBreak(2, p, LivingEntity.getSlotForHand(h));
                    p.getCooldowns().addCooldown(this, 40);
                }

                return InteractionResultHolder.sidedSuccess(stack, l.isClientSide);
            }
        }
    }

    public static final class Dose extends Item {
        private final boolean mana;

        Dose(boolean mana) {
            super(new Properties().stacksTo(16).rarity(Rarity.RARE));
            this.mana = mana;
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            ItemStack s = p.getItemInHand(h);
            if (p.getCooldowns().isOnCooldown(this)) {
                return InteractionResultHolder.fail(s);
            } else {
                if (!l.isClientSide) {
                    if (this.mana) {
                        p.heal(8.0F);
                        p.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 200, 1));
                    } else {
                        for (MobEffectInstance effect : new ArrayList(p.getActiveEffects())) {
                            if (!((MobEffect)effect.getEffect().value()).isBeneficial()) {
                                p.removeEffect(effect.getEffect());
                            }
                        }

                        p.heal(6.0F);
                    }

                    AdventureContent.used(p, h, this, 80);
                }

                return InteractionResultHolder.sidedSuccess(s, l.isClientSide);
            }
        }
    }

    public static final class Guide extends Item {
        Guide() {
            super(new Properties().stacksTo(1));
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            if (!l.isClientSide) {
                p.displayClientMessage(
                    Component.literal(
                        "OROR冒険手帳：メルスなど14体は放浪。26体は封域。蒼珀剣宮・外業生命禁域・邪沌悲劇劇場は封域の鍵で開門。甘契の未怪はHP35%以下で訪問、契約はエメラルドを持ちしゃがんで右クリック。詳細 /oror encounters と配布ガイド。"
                    ),
                    false
                );
            }

            return InteractionResultHolder.sidedSuccess(p.getItemInHand(h), l.isClientSide);
        }
    }

    public static final class RelicArmor extends ArmorItem {
        RelicArmor(Type type) {
            super(AdventureContent.ARMOR, type, new Properties().durability(type.getDurability(64)).fireResistant().rarity(Rarity.EPIC));
        }

        public void inventoryTick(ItemStack stack, Level l, Entity e, int slot, boolean selected) {
            super.inventoryTick(stack, l, e, slot, selected);
            if (!l.isClientSide && e.tickCount % 20 == 0 && e instanceof LivingEntity v && v.getItemBySlot(this.getEquipmentSlot()) == stack) {
                if (this.getEquipmentSlot() == EquipmentSlot.FEET) {
                    v.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 60, 3));
                    v.addEffect(new MobEffectInstance(MobEffects.JUMP, 60, 2));
                } else {
                    v.heal(2.0F);
                    v.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 60));
                }

                return;
            }
        }
    }

    public static final class RepairTool extends Item {
        RepairTool() {
            super(new Properties().durability(512).rarity(Rarity.RARE));
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            ItemStack s = p.getItemInHand(h);
            if (p.getCooldowns().isOnCooldown(this)) {
                return InteractionResultHolder.fail(s);
            } else {
                if (!l.isClientSide) {
                    int n = 0;

                    for (ItemStack v : p.getInventory().items) {
                        if (v != s && v.isDamaged() && n++ < 4) {
                            v.setDamageValue(Math.max(0, v.getDamageValue() - 64));
                        }
                    }

                    ItemStack off = p.getOffhandItem();
                    if (off != s && off.isDamaged()) {
                        off.setDamageValue(Math.max(0, off.getDamageValue() - 64));
                        n++;
                    }

                    if (n > 0) {
                        s.hurtAndBreak(1, p, LivingEntity.getSlotForHand(h));
                    }

                    p.getCooldowns().addCooldown(this, 80);
                }

                return InteractionResultHolder.sidedSuccess(s, l.isClientSide);
            }
        }
    }

    public static final class Staff extends Item {
        Staff() {
            super(new Properties().durability(1024).rarity(Rarity.EPIC));
        }

        public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) {
            ItemStack s = p.getItemInHand(h);
            if (p.getCooldowns().isOnCooldown(this)) {
                return InteractionResultHolder.fail(s);
            } else {
                if (!l.isClientSide) {
                    for (LivingEntity e : l.getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(14.0), v -> AdventureContent.hostile(p, v))) {
                        e.hurt(p.damageSources().magic(), 160.0F);
                    }

                    p.heal(10.0F);
                    s.hurtAndBreak(1, p, LivingEntity.getSlotForHand(h));
                    p.getCooldowns().addCooldown(this, 80);
                }

                return InteractionResultHolder.sidedSuccess(s, l.isClientSide);
            }
        }
    }
}
