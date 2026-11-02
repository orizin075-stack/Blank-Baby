package jp.oror.reborn.gear;

import java.lang.reflect.Field;
import java.util.Set;
import jp.oror.reborn.royal.RoyalMob;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LightBlock;
import net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.registries.RegisterEvent;

/**
 * (052) OROR's gear set down in the world: not only carried and used, but stood somewhere to do its work (what is worn
 * is worn instead: WornGear). Sneak and use
 * one of these on the top of a block and it stands there (its 3D model, turned to face whoever set it down); hit it to
 * take it back. While it stands:
 * <ul>
 * <li>the squad banner (戦団の旗標): its band, within twelve blocks (players, villagers, the kingdom's people), are
 * stronger and harder to hurt (Strength I, Resistance I);</li>
 * <li>the dragon core (龍炉核): a furnace's light all round it, and the furnaces within three blocks smelt twice as fast
 * while they burn;</li>
 * <li>the star shard (星脈結晶): a crystal's light, and those within eight blocks work faster (Haste I);</li>
 * <li>the forge core (工廠演算核): a repair station: use a worn tool, weapon or armour on it to mend a quarter of it,
 * for a level of experience;</li>
 * <li>the omniregistry treasure (万象登録の秘宝): an armillary turning slowly on its stand, giving light.</li>
 * </ul>
 * Its light is a light block where it stands (taken away with it).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public class PlacedGear extends Entity {
    public static EntityType<PlacedGear> TYPE;
    public static final Set<String> PLACEABLE = Set.of("squad_banner", "dragon_core", "star_shard", "forge_core", "omniregistry_treasure");
    private static final EntityDataAccessor<ItemStack> ITEM = SynchedEntityData.defineId(PlacedGear.class, EntityDataSerializers.ITEM_STACK);
    private static Field progressField, totalField;
    private static boolean looked;
    private BlockPos litAt;

    public PlacedGear(EntityType<? extends PlacedGear> type, Level level) {
        super(type, level);
    }

    /** Registered with the game's entity types (the mod bus). */
    @EventBusSubscriber(modid = "oror_supreme_bosses", bus = EventBusSubscriber.Bus.MOD)
    public static final class Types {
        private Types() {
        }

        @SubscribeEvent
        public static void register(RegisterEvent e) {
            e.register(Registries.ENTITY_TYPE, helper -> {
                TYPE = EntityType.Builder.<PlacedGear>of(PlacedGear::new, MobCategory.MISC).sized(0.7F, 0.9F).clientTrackingRange(10)
                    .updateInterval(20).build("placed_gear");
                helper.register(ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "placed_gear"), TYPE);
            });
        }
    }

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder b) {
        b.define(ITEM, ItemStack.EMPTY);
    }

    public ItemStack item() {
        return this.entityData.get(ITEM);
    }

    /** What stands here: the item's id (its path). */
    public String kind() {
        ItemStack s = this.item();
        return s.isEmpty() ? "" : BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
    }

    void setItem(ItemStack s) {
        this.entityData.set(ITEM, s.copyWithCount(1));
    }

    @Override
    protected void readAdditionalSaveData(CompoundTag t) {
        if (t.contains("Item")) {
            this.setItem(ItemStack.parseOptional(this.registryAccess(), t.getCompound("Item")));
        }
        if (t.contains("LitAt")) {
            this.litAt = BlockPos.of(t.getLong("LitAt"));
        }
    }

    @Override
    protected void addAdditionalSaveData(CompoundTag t) {
        if (!this.item().isEmpty()) {
            t.put("Item", this.item().save(this.registryAccess()));
        }
        if (this.litAt != null) {
            t.putLong("LitAt", this.litAt.asLong());
        }
    }

    @Override
    public boolean isPickable() {
        return !this.isRemoved();
    }

    @Override
    public boolean hurt(DamageSource src, float amount) {
        if (this.isRemoved() || this.isInvulnerableTo(src)) {
            return false;
        }
        if (this.level().isClientSide) {
            return true;
        }
        if (src.getEntity() instanceof Player p) {
            ItemStack back = this.item().copy();
            if (!p.getAbilities().instabuild && !p.getInventory().add(back)) {
                this.spawnAtLocation(back);
            }
            this.level().playSound(null, this.blockPosition(), SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 0.6F, 1.0F);
            this.discard();
            return true;
        }
        if (src.is(DamageTypeTags.IS_EXPLOSION) || src.is(DamageTypeTags.IS_FIRE) && !this.kind().equals("dragon_core")) {
            this.spawnAtLocation(this.item().copy());
            this.discard();
            return true;
        }
        return false;
    }

    @Override
    public InteractionResult interact(Player p, InteractionHand hand) {
        return this.kind().equals("forge_core") ? this.repair(p, hand) : InteractionResult.PASS;
    }

    @Override
    public void remove(RemovalReason reason) {
        if (reason.shouldDestroy()) {
            this.unlight();
        }
        super.remove(reason);
    }

    @Override
    public void tick() {
        super.tick();
        if (this.level().isClientSide || this.item().isEmpty()) {
            return;
        }
        String k = this.kind();
        int t = this.tickCount;
        int glow = switch (k) {
            case "dragon_core" -> 15;
            case "star_shard" -> 12;
            case "omniregistry_treasure" -> 10;
            case "forge_core" -> 8;
            default -> 0;
        };
        if (t % 20 == 0 && glow > 0) {
            this.light(glow);
        }
        if (t % 40 == 0) {
            switch (k) {
                case "squad_banner" -> this.aura(12, MobEffects.DAMAGE_BOOST, MobEffects.DAMAGE_RESISTANCE);
                case "star_shard" -> this.aura(8, MobEffects.DIG_SPEED, null);
                default -> {
                }
            }
        }
        if (k.equals("dragon_core") && t % 10 == 0) {
            this.stoke();
        }
        if (t % 20 == 0 && this.level() instanceof ServerLevel sl) {
            ParticleOptions p = switch (k) {
                case "squad_banner" -> ParticleTypes.ENCHANTED_HIT;
                case "dragon_core" -> ParticleTypes.FLAME;
                case "star_shard" -> ParticleTypes.END_ROD;
                case "forge_core" -> ParticleTypes.ELECTRIC_SPARK;
                default -> ParticleTypes.ENCHANT;
            };
            double top = k.equals("squad_banner") ? 2.0 : 0.7;
            sl.sendParticles(p, this.getX(), this.getY() + top, this.getZ(), 3, 0.25, 0.2, 0.25, 0.01);
        }
    }

    private void aura(double r, Holder<MobEffect> a, Holder<MobEffect> b) {
        for (LivingEntity e : this.level().getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(r),
            x -> x instanceof Player || RoyalMob.civilian(x))) {
            if (e.distanceToSqr(this) > r * r) {
                continue;
            }
            e.addEffect(new MobEffectInstance(a, 80, 0, true, true));
            if (b != null) {
                e.addEffect(new MobEffectInstance(b, 80, 0, true, true));
            }
        }
    }

    /** The furnaces round the dragon core, burning, smelt twice as fast. */
    private void stoke() {
        try {
            if (!looked) {
                looked = true;
                progressField = AbstractFurnaceBlockEntity.class.getDeclaredField("cookingProgress");
                totalField = AbstractFurnaceBlockEntity.class.getDeclaredField("cookingTotalTime");
                progressField.setAccessible(true);
                totalField.setAccessible(true);
            }
            if (progressField == null) {
                return;
            }
            BlockPos at = this.blockPosition();
            for (BlockPos q : BlockPos.betweenClosed(at.offset(-3, -2, -3), at.offset(3, 2, 3))) {
                BlockEntity be = this.level().getBlockEntity(q);
                if (!(be instanceof AbstractFurnaceBlockEntity f)) {
                    continue;
                }
                BlockState s = this.level().getBlockState(q);
                if (!s.hasProperty(BlockStateProperties.LIT) || !s.getValue(BlockStateProperties.LIT)) {
                    continue;
                }
                int p = progressField.getInt(f), total = totalField.getInt(f);
                if (p > 0 && p + 10 < total) {
                    progressField.setInt(f, p + 10);
                }
            }
        } catch (ReflectiveOperationException | RuntimeException ex) {
            progressField = null;
        }
    }

    private void light(int level) {
        BlockPos at = this.blockPosition();
        BlockState s = this.level().getBlockState(at);
        if (s.isAir() || s.is(Blocks.LIGHT)) {
            if (!s.is(Blocks.LIGHT) || s.getValue(LightBlock.LEVEL) != level) {
                this.level().setBlock(at, Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, level), 3);
            }
            if (this.litAt != null && !this.litAt.equals(at)) {
                this.unlight();
            }
            this.litAt = at.immutable();
        }
    }

    private void unlight() {
        if (this.litAt != null && !this.level().isClientSide && this.level().getBlockState(this.litAt).is(Blocks.LIGHT)) {
            this.level().setBlock(this.litAt, Blocks.AIR.defaultBlockState(), 3);
        }
        this.litAt = null;
    }

    private InteractionResult repair(Player p, InteractionHand hand) {
        ItemStack s = p.getItemInHand(hand);
        if (!s.isDamageableItem() || !s.isDamaged()) {
            return InteractionResult.PASS;
        }
        if (this.level().isClientSide) {
            return InteractionResult.SUCCESS;
        }
        if (!p.getAbilities().instabuild && p.experienceLevel < 1) {
            p.displayClientMessage(Component.translatable("message.oror_supreme_bosses.placed_gear.need_level").withStyle(ChatFormatting.GRAY), true);
            return InteractionResult.FAIL;
        }
        s.setDamageValue(Math.max(0, s.getDamageValue() - Math.max(1, s.getMaxDamage() / 4)));
        if (!p.getAbilities().instabuild) {
            p.giveExperienceLevels(-1);
        }
        this.level().playSound(null, this.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.BLOCKS, 0.7F, 1.2F);
        if (this.level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.ELECTRIC_SPARK, this.getX(), this.getY() + 0.8, this.getZ(), 12, 0.3, 0.3, 0.3, 0.05);
        }
        return InteractionResult.CONSUME;
    }

    // ---------------------------------------------------------------------------------------------------- setting it down

    @SubscribeEvent
    public static void place(PlayerInteractEvent.RightClickBlock e) {
        Player p = e.getEntity();
        ItemStack s = e.getItemStack();
        if (!p.isShiftKeyDown() || s.isEmpty() || e.getFace() != Direction.UP || TYPE == null) {
            return;
        }
        ResourceLocation id = BuiltInRegistries.ITEM.getKey(s.getItem());
        if (!id.getNamespace().equals("oror_supreme_bosses") || !PLACEABLE.contains(id.getPath())) {
            return;
        }
        Level level = e.getLevel();
        Vec3 at = e.getHitVec().getLocation();
        if (!level.getEntitiesOfClass(PlacedGear.class, new AABB(at, at).inflate(0.45)).isEmpty()) {
            return;
        }
        e.setCanceled(true);
        e.setCancellationResult(InteractionResult.sidedSuccess(level.isClientSide));
        if (level.isClientSide) {
            return;
        }
        PlacedGear g = new PlacedGear(TYPE, level);
        g.setItem(s);
        g.moveTo(at.x, at.y, at.z, p.getYRot() + 180F, 0F);
        level.addFreshEntity(g);
        level.playSound(null, BlockPos.containing(at), SoundEvents.ARMOR_EQUIP_GENERIC.value(), SoundSource.BLOCKS, 0.8F, 1.0F);
        if (!p.getAbilities().instabuild) {
            s.shrink(1);
        }
    }
}
