# Hand-maintained hierarchy/generics for Minecraft 1.21.1 + NeoForge 21.1 compile stubs.
M = 'net.minecraft.'
W = M + 'world.'
E = W + 'entity.'
NF = 'net.neoforged.neoforge.'

def c(**k): return k

OV = {
 # ---------- entities ----------
 'net/minecraft/world/entity/Entity': c(implements='net.minecraft.world.level.entity.EntityAccess', drop=['getPassengers'], members=['public java.util.List<net.minecraft.world.entity.Entity> getPassengers() { return null; }']),
 'net/minecraft/world/level/entity/EntityAccess': c(kind='interface'),
 'net/minecraft/world/entity/LivingEntity': c(extends=E+'Entity'),
 'net/minecraft/world/entity/Mob': c(extends=E+'LivingEntity', members=[
     'public net.minecraft.world.entity.ai.goal.GoalSelector goalSelector;',
     'public net.minecraft.world.entity.ai.goal.GoalSelector targetSelector;',
     'public net.minecraft.world.entity.ai.navigation.PathNavigation navigation;']),
 'net/minecraft/world/entity/PathfinderMob': c(extends=E+'Mob'),
 'net/minecraft/world/entity/AgeableMob': c(extends=E+'PathfinderMob'),
 'net/minecraft/world/entity/animal/Animal': c(extends=E+'AgeableMob'),
 'net/minecraft/world/entity/TamableAnimal': c(extends=E+'animal.Animal'),
 'net/minecraft/world/entity/animal/Wolf': c(extends=E+'TamableAnimal'),
 'net/minecraft/world/entity/animal/Cow': c(extends=E+'animal.Animal'),
 'net/minecraft/world/entity/animal/Sheep': c(extends=E+'animal.Animal'),
 'net/minecraft/world/entity/animal/AbstractGolem': c(extends=E+'PathfinderMob'),
 'net/minecraft/world/entity/animal/IronGolem': c(extends=E+'animal.AbstractGolem'),
 'net/minecraft/world/entity/monster/Monster': c(extends=E+'PathfinderMob', implements=E+'monster.Enemy'),
 'net/minecraft/world/entity/monster/Enemy': c(kind='interface'),
 'net/minecraft/world/entity/monster/Zombie': c(extends=E+'monster.Monster'),
 'net/minecraft/world/entity/monster/Husk': c(extends=E+'monster.Zombie'),
 'net/minecraft/world/entity/npc/AbstractVillager': c(extends=E+'AgeableMob'),
 'net/minecraft/world/entity/npc/Villager': c(extends=E+'npc.AbstractVillager'),
 'net/minecraft/world/entity/player/Player': c(extends=E+'LivingEntity'),
 'net/minecraft/server/level/ServerPlayer': c(extends=E+'player.Player'),
 'net/minecraft/client/player/AbstractClientPlayer': c(extends=E+'player.Player'),
 'net/minecraft/client/player/LocalPlayer': c(extends=M+'client.player.AbstractClientPlayer'),
 'net/neoforged/neoforge/common/util/FakePlayer': c(extends=M+'server.level.ServerPlayer'),
 'net/minecraft/world/entity/projectile/Projectile': c(extends=E+'Entity'),
 'net/minecraft/world/entity/projectile/AbstractArrow': c(extends=E+'projectile.Projectile', members=['public net.minecraft.world.entity.projectile.AbstractArrow.Pickup pickup;']),
 'net/minecraft/world/entity/projectile/AbstractArrow$Pickup': c(kind='enum', consts=['DISALLOWED', 'ALLOWED', 'CREATIVE_ONLY']),
 'net/minecraft/world/entity/projectile/Arrow': c(extends=E+'projectile.AbstractArrow'),
 'net/minecraft/world/entity/projectile/ThrownTrident': c(extends=E+'projectile.AbstractArrow'),
 'net/minecraft/world/entity/item/ItemEntity': c(extends=E+'Entity'),
 'net/minecraft/world/entity/EquipmentSlot': c(kind='enum', consts=['MAINHAND', 'OFFHAND', 'FEET', 'LEGS', 'CHEST', 'HEAD', 'BODY']),
 'net/minecraft/world/entity/MobCategory': c(kind='enum'),
 'net/minecraft/world/entity/Pose': c(kind='enum'),
 'net/minecraft/world/entity/Entity$RemovalReason': c(kind='enum'),
 'net/minecraft/world/InteractionHand': c(kind='enum', consts=['MAIN_HAND', 'OFF_HAND']),
 'net/minecraft/world/InteractionResult': c(kind='enum'),
 'net/minecraft/world/InteractionResultHolder': c(tparams='<T>'),
 'net/minecraft/world/entity/EntityType': c(tparams='<T extends net.minecraft.world.entity.Entity>', drop=['create'], members=[
     'public T create(net.minecraft.world.level.Level p0) { return null; }']),
 'net/minecraft/world/entity/EntityType$Builder': c(tparams='<T extends net.minecraft.world.entity.Entity>', drop=['of', 'sized', 'clientTrackingRange', 'updateInterval', 'build', 'fireImmune'], members=[
     'public static <T extends net.minecraft.world.entity.Entity> Builder<T> of(EntityFactory<T> p0, net.minecraft.world.entity.MobCategory p1) { return null; }',
     'public Builder<T> sized(float p0, float p1) { return this; }',
     'public Builder<T> clientTrackingRange(int p0) { return this; }',
     'public Builder<T> updateInterval(int p0) { return this; }',
     'public Builder<T> fireImmune() { return this; }',
     'public EntityType<T> build(String p0) { return null; }']),
 'net/minecraft/world/entity/EntityType$EntityFactory': c(kind='interface', tparams='<T extends net.minecraft.world.entity.Entity>', drop=['create'], members=[
     'T create(EntityType<T> p0, net.minecraft.world.level.Level p1);']),
 'net/minecraft/world/entity/EntityDimensions': c(),
 'net/minecraft/world/BossEvent$BossBarColor': c(kind='enum'),
 'net/minecraft/world/BossEvent$BossBarOverlay': c(kind='enum'),
 'net/minecraft/world/entity/ai/attributes/AttributeModifier$Operation': c(kind='enum'),
 'net/minecraft/world/entity/ai/attributes/Attribute': c(),
 'net/minecraft/world/entity/ai/attributes/Attributes': c(drop=['ATTACK_DAMAGE','MAX_HEALTH','MOVEMENT_SPEED','ARMOR','ARMOR_TOUGHNESS','FLYING_SPEED','FOLLOW_RANGE','KNOCKBACK_RESISTANCE','STEP_HEIGHT','SCALE','ATTACK_SPEED','LUCK','GRAVITY','SAFE_FALL_DISTANCE','ATTACK_KNOCKBACK','ENTITY_INTERACTION_RANGE','BLOCK_INTERACTION_RANGE'], members=[
     f'public static net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> {n};' for n in ['ATTACK_DAMAGE','MAX_HEALTH','MOVEMENT_SPEED','ARMOR','ARMOR_TOUGHNESS','FLYING_SPEED','FOLLOW_RANGE','KNOCKBACK_RESISTANCE','STEP_HEIGHT','SCALE','ATTACK_SPEED','LUCK','GRAVITY','SAFE_FALL_DISTANCE','ATTACK_KNOCKBACK','ENTITY_INTERACTION_RANGE','BLOCK_INTERACTION_RANGE']]),
 'net/minecraft/world/effect/MobEffects': c(drop=['POISON','WITHER','WEAKNESS','MOVEMENT_SLOWDOWN','MOVEMENT_SPEED','DIG_SLOWDOWN','DAMAGE_BOOST','DAMAGE_RESISTANCE','REGENERATION','ABSORPTION','LEVITATION','CONFUSION','DARKNESS','LUCK','WATER_BREATHING','DOLPHINS_GRACE','GLOWING','FIRE_RESISTANCE','HEAL','INVISIBILITY','NIGHT_VISION','SLOW_FALLING','BLINDNESS','HUNGER','SATURATION','HEALTH_BOOST','JUMP','DIG_SPEED','HARM','BAD_OMEN','HERO_OF_THE_VILLAGE','UNLUCK'], members=[
     f'public static net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> {n};' for n in ['POISON','WITHER','WEAKNESS','MOVEMENT_SLOWDOWN','MOVEMENT_SPEED','DIG_SLOWDOWN','DAMAGE_BOOST','DAMAGE_RESISTANCE','REGENERATION','ABSORPTION','LEVITATION','CONFUSION','DARKNESS','LUCK','WATER_BREATHING','DOLPHINS_GRACE','GLOWING','FIRE_RESISTANCE','HEAL','INVISIBILITY','NIGHT_VISION','SLOW_FALLING','BLINDNESS','HUNGER','SATURATION','HEALTH_BOOST','JUMP','DIG_SPEED','HARM','BAD_OMEN','HERO_OF_THE_VILLAGE','UNLUCK']]),
 'net/minecraft/world/effect/MobEffectInstance': c(drop=['getEffect'], members=['public net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> getEffect() { return null; }']),
 # ---------- core / registry ----------
 'net/minecraft/core/Holder': c(kind='interface', tparams='<T>', drop=['value', 'unwrapKey', 'is'], members=[
     'default T value() { return null; }',
     'default java.util.Optional<net.minecraft.resources.ResourceKey<T>> unwrapKey() { return null; }',
     'default boolean is(net.minecraft.resources.ResourceKey<T> p0) { return false; }',
     'default boolean is(net.minecraft.tags.TagKey<T> p0) { return false; }',
     'default boolean is(net.minecraft.resources.ResourceLocation p0) { return false; }']),
 'net/minecraft/core/Holder$Reference': c(tparams='<T>', implements='net.minecraft.core.Holder<T>'),
 'net/minecraft/resources/ResourceKey': c(tparams='<T>', drop=['create', 'location'], members=[
     'public static <T> ResourceKey<T> create(ResourceKey<? extends net.minecraft.core.Registry<T>> p0, net.minecraft.resources.ResourceLocation p1) { return null; }',
     'public net.minecraft.resources.ResourceLocation location() { return null; }']),
 'net/minecraft/core/Registry': c(kind='interface', tparams='<T>', drop=['getKey', 'get', 'getHolderOrThrow', 'containsKey', 'getHolder', 'stream', 'keySet', 'getOptional', 'getTag', 'getTagOrEmpty', 'wrapAsHolder', 'register'], members=[
     'default net.minecraft.resources.ResourceLocation getKey(T p0) { return null; }',
     'default T get(net.minecraft.resources.ResourceLocation p0) { return null; }',
     'default T get(net.minecraft.resources.ResourceKey<T> p0) { return null; }',
     'default java.util.Optional<T> getOptional(net.minecraft.resources.ResourceLocation p0) { return null; }',
     'default boolean containsKey(net.minecraft.resources.ResourceLocation p0) { return false; }',
     'default net.minecraft.core.Holder.Reference<T> getHolderOrThrow(net.minecraft.resources.ResourceKey<T> p0) { return null; }',
     'default java.util.Optional<net.minecraft.core.Holder.Reference<T>> getHolder(net.minecraft.resources.ResourceLocation p0) { return null; }',
     'default java.util.Optional<net.minecraft.core.Holder.Reference<T>> getHolder(net.minecraft.resources.ResourceKey<T> p0) { return null; }',
     'default net.minecraft.core.Holder<T> wrapAsHolder(T p0) { return null; }',
     'default java.util.stream.Stream<T> stream() { return null; }',
     'default java.util.Set<net.minecraft.resources.ResourceLocation> keySet() { return null; }']),
 'net/minecraft/core/DefaultedRegistry': c(kind='interface', tparams='<T>', extends='net.minecraft.core.Registry<T>', drop=['get','getKey','getHolderOrThrow','containsKey','getHolder','stream','keySet','getOptional','wrapAsHolder']),
 'net/minecraft/core/registries/BuiltInRegistries': c(drop=['ITEM','BLOCK','ENTITY_TYPE','MOB_EFFECT','SOUND_EVENT','PARTICLE_TYPE','ATTRIBUTE','ENCHANTMENT_PROVIDER_TYPE','POINT_OF_INTEREST_TYPE','VILLAGER_PROFESSION','DATA_COMPONENT_TYPE','RECIPE_TYPE','LOOT_FUNCTION_TYPE','POTION','FLUID'], members=[
     'public static net.minecraft.core.DefaultedRegistry<net.minecraft.world.item.Item> ITEM;',
     'public static net.minecraft.core.DefaultedRegistry<net.minecraft.world.level.block.Block> BLOCK;',
     'public static net.minecraft.core.DefaultedRegistry<net.minecraft.world.entity.EntityType<?>> ENTITY_TYPE;',
     'public static net.minecraft.core.Registry<net.minecraft.world.effect.MobEffect> MOB_EFFECT;',
     'public static net.minecraft.core.Registry<net.minecraft.sounds.SoundEvent> SOUND_EVENT;',
     'public static net.minecraft.core.Registry<net.minecraft.world.entity.ai.attributes.Attribute> ATTRIBUTE;',
     'public static net.minecraft.core.DefaultedRegistry<net.minecraft.world.entity.npc.VillagerProfession> VILLAGER_PROFESSION;',
     'public static net.minecraft.core.Registry<net.minecraft.world.entity.ai.village.poi.PoiType> POINT_OF_INTEREST_TYPE;']),
 'net/minecraft/core/registries/Registries': c(drop=['DAMAGE_TYPE','ENCHANTMENT','ENTITY_TYPE','ITEM','BLOCK','CREATIVE_MODE_TAB','POINT_OF_INTEREST_TYPE','VILLAGER_PROFESSION','LOOT_FUNCTION_TYPE','BIOME','STRUCTURE','LOOT_TABLE','MOB_EFFECT'], members=[
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.damagesource.DamageType>> DAMAGE_TYPE;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.item.enchantment.Enchantment>> ENCHANTMENT;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.entity.EntityType<?>>> ENTITY_TYPE;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.item.Item>> ITEM;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.level.block.Block>> BLOCK;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.item.CreativeModeTab>> CREATIVE_MODE_TAB;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.entity.ai.village.poi.PoiType>> POINT_OF_INTEREST_TYPE;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.entity.npc.VillagerProfession>> VILLAGER_PROFESSION;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.level.storage.loot.LootTable>> LOOT_TABLE;',
     'public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.effect.MobEffect>> MOB_EFFECT;']),
 'net/minecraft/core/HolderLookup$Provider': c(kind='interface'),
 'net/minecraft/core/RegistryAccess': c(kind='interface', extends='net.minecraft.core.HolderLookup.Provider', drop=['registryOrThrow', 'registry'], members=[
     'default <E> net.minecraft.core.Registry<E> registryOrThrow(net.minecraft.resources.ResourceKey<? extends net.minecraft.core.Registry<? extends E>> p0) { return null; }']),
 'net/minecraft/world/damagesource/DamageType': c(),
 'net/minecraft/world/item/enchantment/Enchantment': c(),
 'net/minecraft/world/item/enchantment/Enchantments': c(drop=['UNBREAKING','PROTECTION','POWER','QUICK_CHARGE','EFFICIENCY','SHARPNESS','LOOTING','FORTUNE','MENDING','FIRE_ASPECT','SMITE','PUNCH','INFINITY','PIERCING','MULTISHOT','LOYALTY','RIPTIDE','IMPALING','FEATHER_FALLING','FIRE_PROTECTION','BLAST_PROTECTION','PROJECTILE_PROTECTION','THORNS','DENSITY','BREACH','WIND_BURST'], members=[
     f'public static net.minecraft.resources.ResourceKey<net.minecraft.world.item.enchantment.Enchantment> {n};' for n in ['UNBREAKING','PROTECTION','POWER','QUICK_CHARGE','EFFICIENCY','SHARPNESS','LOOTING','FORTUNE','MENDING','FIRE_ASPECT','SMITE','PUNCH','INFINITY','PIERCING','MULTISHOT','LOYALTY','RIPTIDE','IMPALING','FEATHER_FALLING','FIRE_PROTECTION','BLAST_PROTECTION','PROJECTILE_PROTECTION','THORNS','DENSITY','BREACH','WIND_BURST']]),
 'net/minecraft/tags/TagKey': c(tparams='<T>'),
 'net/minecraft/core/component/DataComponentType': c(kind='interface', tparams='<T>'),
 'net/minecraft/core/NonNullList': c(tparams='<E>', extends='java.util.AbstractList<E>', members=['public E get(int p0) { return null; }', 'public int size() { return 0; }']),
 'net/minecraft/core/Direction': c(kind='enum', consts=['DOWN', 'UP', 'NORTH', 'SOUTH', 'WEST', 'EAST']),
 'net/minecraft/core/Direction$Plane': c(kind='enum', consts=['HORIZONTAL', 'VERTICAL'], implements='java.lang.Iterable<net.minecraft.core.Direction>', members=['public java.util.Iterator<net.minecraft.core.Direction> iterator() { return null; }']),
 'net/minecraft/core/Vec3i': c(),
 'net/minecraft/core/BlockPos': c(extends='net.minecraft.core.Vec3i', drop=['betweenClosed'], members=[
     'public static java.lang.Iterable<BlockPos> betweenClosed(BlockPos p0, BlockPos p1) { return null; }']),
 'net/minecraft/core/Position': c(kind='interface'),
 'net/minecraft/world/phys/Vec3': c(implements='net.minecraft.core.Position'),
 'net/minecraft/world/phys/HitResult': c(),
 'net/minecraft/world/phys/BlockHitResult': c(extends='net.minecraft.world.phys.HitResult'),
 'net/minecraft/world/phys/HitResult$Type': c(kind='enum', consts=['MISS', 'BLOCK', 'ENTITY']),
 # ---------- nbt / chat ----------
 'net/minecraft/nbt/Tag': c(kind='interface'),
 'net/minecraft/nbt/CompoundTag': c(implements='net.minecraft.nbt.Tag', drop=['getAllKeys'], members=['public java.util.Set<String> getAllKeys() { return null; }']),
 'net/minecraft/nbt/ListTag': c(extends='java.util.AbstractList<net.minecraft.nbt.Tag>', implements='net.minecraft.nbt.Tag', drop=['get','size','remove','add'], members=['public net.minecraft.nbt.Tag get(int p0) { return null; }', 'public int size() { return 0; }']),
 'net/minecraft/nbt/StringTag': c(implements='net.minecraft.nbt.Tag'),
 'net/minecraft/network/chat/Component': c(kind='interface', extends='com.mojang.brigadier.Message'),
 'net/minecraft/network/chat/MutableComponent': c(implements='net.minecraft.network.chat.Component'),
 'com/mojang/brigadier/Message': c(kind='interface'),
 'net/minecraft/ChatFormatting': c(kind='enum'),
 # ---------- level ----------
 'net/minecraft/world/level/BlockGetter': c(kind='interface'),
 'net/minecraft/world/level/LevelReader': c(kind='interface', extends='net.minecraft.world.level.BlockGetter'),
 'net/minecraft/world/level/chunk/LevelChunk': c(members=['public java.util.Map<net.minecraft.core.BlockPos, net.minecraft.world.level.block.entity.BlockEntity> getBlockEntities() { return null; }']),
 'net/minecraft/world/level/LevelAccessor': c(kind='interface', extends='net.minecraft.world.level.LevelReader'),
 'net/minecraft/world/level/ServerLevelAccessor': c(kind='interface', extends='net.minecraft.world.level.LevelAccessor'),
 'net/minecraft/world/level/Level': c(implements='net.minecraft.world.level.LevelAccessor', drop=['getEntitiesOfClass', 'players', 'getEntities'], members=[
     'public boolean isClientSide;',
     'public net.minecraft.util.RandomSource random;',
     'public <T extends net.minecraft.world.entity.Entity> java.util.List<T> getEntitiesOfClass(Class<T> p0, net.minecraft.world.phys.AABB p1, java.util.function.Predicate<? super T> p2) { return null; }',
     'public <T extends net.minecraft.world.entity.Entity> java.util.List<T> getEntitiesOfClass(Class<T> p0, net.minecraft.world.phys.AABB p1) { return null; }',
     'public java.util.List<net.minecraft.world.entity.Entity> getEntities(net.minecraft.world.entity.Entity p0, net.minecraft.world.phys.AABB p1, java.util.function.Predicate<? super net.minecraft.world.entity.Entity> p2) { return null; }',
     'public java.util.List<? extends net.minecraft.world.entity.player.Player> players() { return null; }']),
 'net/minecraft/server/level/ServerLevel': c(extends='net.minecraft.world.level.Level', implements='net.minecraft.world.level.ServerLevelAccessor', drop=['players', 'getAllEntities'], members=[
     'public java.util.List<net.minecraft.server.level.ServerPlayer> players() { return null; }',
     'public java.lang.Iterable<net.minecraft.world.entity.Entity> getAllEntities() { return null; }']),
 'net/minecraft/client/multiplayer/ClientLevel': c(extends='net.minecraft.world.level.Level'),
 'net/minecraft/world/level/GameRules$Key': c(tparams='<T>'),
 'net/minecraft/world/level/GameRules': c(drop=['RULE_MOBGRIEFING', 'getBoolean', 'RULE_DOMOBSPAWNING', 'RULE_DAYLIGHT', 'RULE_DOFIRETICK', 'RULE_WEATHER_CYCLE', 'RULE_KEEPINVENTORY'], members=[
     'public static Key<BooleanValue> RULE_MOBGRIEFING;', 'public static Key<BooleanValue> RULE_DOMOBSPAWNING;', 'public static Key<BooleanValue> RULE_DAYLIGHT;', 'public static Key<BooleanValue> RULE_WEATHER_CYCLE;', 'public static Key<BooleanValue> RULE_KEEPINVENTORY;',
     'public boolean getBoolean(Key<BooleanValue> p0) { return false; }']),
 'net/minecraft/world/level/GameRules$Value': c(tparams='<T extends net.minecraft.world.level.GameRules.Value<T>>'),
 'net/minecraft/world/level/GameRules$BooleanValue': c(extends='net.minecraft.world.level.GameRules.Value<net.minecraft.world.level.GameRules.BooleanValue>'),
 'net/minecraft/world/level/ClipContext$Block': c(kind='enum', consts=['COLLIDER', 'OUTLINE', 'VISUAL', 'FALLDAMAGE_RESETTING']),
 'net/minecraft/world/level/ClipContext$Fluid': c(kind='enum', consts=['NONE', 'SOURCE_ONLY', 'ANY', 'WATER']),
 'net/minecraft/world/level/levelgen/Heightmap$Types': c(kind='enum'),
 'net/minecraft/world/level/ItemLike': c(kind='interface'),
 'net/minecraft/world/level/block/state/BlockBehaviour': c(),
 'net/minecraft/world/level/block/Block': c(extends='net.minecraft.world.level.block.state.BlockBehaviour', implements='net.minecraft.world.level.ItemLike'),
 'net/minecraft/world/level/block/BaseEntityBlock': c(extends='net.minecraft.world.level.block.Block'),
 'net/minecraft/world/level/block/AbstractFurnaceBlock': c(extends='net.minecraft.world.level.block.BaseEntityBlock'),
 'net/minecraft/world/level/block/ChestBlock': c(extends='net.minecraft.world.level.block.BaseEntityBlock'),
 'net/minecraft/world/level/block/BedBlock': c(extends='net.minecraft.world.level.block.Block'),
 'net/minecraft/world/level/block/CropBlock': c(extends='net.minecraft.world.level.block.Block'),
 'net/minecraft/world/level/block/DoorBlock': c(extends='net.minecraft.world.level.block.Block'),
 'net/minecraft/world/level/block/FarmBlock': c(extends='net.minecraft.world.level.block.Block'),
 'net/minecraft/world/level/block/state/StateHolder': c(tparams='<O, S>', members=[
     'public <T extends Comparable<T>> T getValue(net.minecraft.world.level.block.state.properties.Property<T> p0) { return null; }',
     'public <T extends Comparable<T>, V extends T> S setValue(net.minecraft.world.level.block.state.properties.Property<T> p0, V p1) { return null; }']),
 'net/minecraft/world/level/block/state/BlockState': c(extends='net.minecraft.world.level.block.state.StateHolder<net.minecraft.world.level.block.Block, net.minecraft.world.level.block.state.BlockState>', drop=['getValue', 'setValue', 'is'], members=[
     'public boolean is(net.minecraft.world.level.block.Block p0) { return false; }',
     'public boolean is(net.minecraft.tags.TagKey<net.minecraft.world.level.block.Block> p0) { return false; }']),
 'net/minecraft/world/level/block/state/properties/Property': c(tparams='<T extends Comparable<T>>'),
 'net/minecraft/world/level/block/state/properties/BooleanProperty': c(extends='net.minecraft.world.level.block.state.properties.Property<Boolean>'),
 'net/minecraft/world/level/block/state/properties/IntegerProperty': c(extends='net.minecraft.world.level.block.state.properties.Property<Integer>'),
 'net/minecraft/world/level/block/state/properties/EnumProperty': c(tparams='<T extends Enum<T>>', extends='net.minecraft.world.level.block.state.properties.Property<T>'),
 'net/minecraft/world/level/block/state/properties/DirectionProperty': c(extends='net.minecraft.world.level.block.state.properties.EnumProperty<net.minecraft.core.Direction>'),
 'net/minecraft/world/level/block/state/properties/BedPart': c(kind='enum', consts=['HEAD', 'FOOT']),
 'net/minecraft/world/level/block/state/properties/DoubleBlockHalf': c(kind='enum', consts=['UPPER', 'LOWER']),
 'net/minecraft/world/level/block/entity/BlockEntity': c(),
 'net/minecraft/world/Container': c(kind='interface'),
 'net/minecraft/world/CompoundContainer': c(implements='net.minecraft.world.Container'),
 'net/minecraft/world/SimpleContainer': c(implements='net.minecraft.world.Container'),
 'net/minecraft/world/level/block/entity/BaseContainerBlockEntity': c(extends='net.minecraft.world.level.block.entity.BlockEntity', implements='net.minecraft.world.Container'),
 'net/minecraft/world/level/block/entity/AbstractFurnaceBlockEntity': c(extends='net.minecraft.world.level.block.entity.BaseContainerBlockEntity'),
 'net/minecraft/world/level/block/entity/FurnaceBlockEntity': c(extends='net.minecraft.world.level.block.entity.AbstractFurnaceBlockEntity'),
 'net/minecraft/world/level/block/entity/ChestBlockEntity': c(extends='net.minecraft.world.level.block.entity.BaseContainerBlockEntity'),
 # ---------- items ----------
 'net/minecraft/world/item/Item': c(implements='net.minecraft.world.level.ItemLike', members=[
     'public void appendHoverText(net.minecraft.world.item.ItemStack p0, net.minecraft.world.item.Item.TooltipContext p1, java.util.List<net.minecraft.network.chat.Component> p2, net.minecraft.world.item.TooltipFlag p3) {}']),
 'net/minecraft/world/item/Item$TooltipContext': c(kind='interface'),
 'net/minecraft/world/item/TooltipFlag': c(kind='interface'),
 'net/minecraft/world/entity/LightningBolt': c(extends='net.minecraft.world.entity.Entity'),
 'net/minecraft/world/item/TieredItem': c(extends='net.minecraft.world.item.Item'),
 'net/minecraft/world/item/SwordItem': c(extends='net.minecraft.world.item.TieredItem'),
 'net/minecraft/world/item/DiggerItem': c(extends='net.minecraft.world.item.TieredItem'),
 'net/minecraft/world/item/AxeItem': c(extends='net.minecraft.world.item.DiggerItem'),
 'net/minecraft/world/item/ArmorItem': c(extends='net.minecraft.world.item.Item'),
 'net/minecraft/world/item/ArmorItem$Type': c(kind='enum', consts=['HELMET', 'CHESTPLATE', 'LEGGINGS', 'BOOTS', 'BODY']),
 'net/minecraft/world/item/BlockItem': c(extends='net.minecraft.world.item.Item'),
 'net/minecraft/world/item/ProjectileWeaponItem': c(extends='net.minecraft.world.item.Item'),
 'net/minecraft/world/item/BowItem': c(extends='net.minecraft.world.item.ProjectileWeaponItem'),
 'net/minecraft/world/item/ShieldItem': c(extends='net.minecraft.world.item.Item'),
 'net/minecraft/world/entity/EquipmentSlotGroup': c(kind='enum'),
 'net/minecraft/world/item/CrossbowItem': c(extends='net.minecraft.world.item.ProjectileWeaponItem'),
 'net/minecraft/world/item/SpawnEggItem': c(extends='net.minecraft.world.item.Item'),
 'net/neoforged/neoforge/common/DeferredSpawnEggItem': c(extends='net.minecraft.world.item.SpawnEggItem'),
 'net/minecraft/world/item/Tier': c(kind='interface'),
 'net/minecraft/world/item/Tiers': c(kind='enum', implements='net.minecraft.world.item.Tier'),
 'net/minecraft/world/item/Rarity': c(kind='enum'),
 'net/minecraft/world/item/ItemDisplayContext': c(kind='enum', consts=['NONE', 'THIRD_PERSON_LEFT_HAND', 'THIRD_PERSON_RIGHT_HAND', 'FIRST_PERSON_LEFT_HAND', 'FIRST_PERSON_RIGHT_HAND', 'HEAD', 'GUI', 'GROUND', 'FIXED']),
 'net/minecraft/world/item/ItemStack': c(members=['public static ItemStack EMPTY;']),
 'net/minecraft/world/item/CreativeModeTab$DisplayItemsGenerator': c(kind='interface', functional='accept'),
 'net/minecraft/world/item/CreativeModeTab$Output': c(kind='interface'),
 'net/minecraft/world/entity/player/Inventory': c(implements='net.minecraft.world.Container', drop=['items', 'armor', 'offhand'], members=[
     'public net.minecraft.core.NonNullList<net.minecraft.world.item.ItemStack> items;',
     'public net.minecraft.core.NonNullList<net.minecraft.world.item.ItemStack> armor;',
     'public net.minecraft.core.NonNullList<net.minecraft.world.item.ItemStack> offhand;']),
 # ---------- sync data ----------
 'net/minecraft/network/syncher/EntityDataAccessor': c(tparams='<T>'),
 'net/minecraft/network/syncher/EntityDataSerializer': c(kind='interface', tparams='<T>'),
 'net/minecraft/network/syncher/EntityDataSerializers': c(drop=['INT', 'FLOAT', 'LONG', 'BOOLEAN', 'STRING', 'BYTE'], members=[
     'public static EntityDataSerializer<Integer> INT;', 'public static EntityDataSerializer<Float> FLOAT;', 'public static EntityDataSerializer<Long> LONG;',
     'public static EntityDataSerializer<Boolean> BOOLEAN;', 'public static EntityDataSerializer<String> STRING;', 'public static EntityDataSerializer<Byte> BYTE;']),
 'net/minecraft/network/syncher/SynchedEntityData': c(drop=['get', 'set', 'defineId'], members=[
     'public <T> T get(EntityDataAccessor<T> p0) { return null; }',
     'public <T> void set(EntityDataAccessor<T> p0, T p1) {}',
     'public static <T> EntityDataAccessor<T> defineId(Class<?> p0, EntityDataSerializer<T> p1) { return null; }']),
 'net/minecraft/network/syncher/SynchedEntityData$Builder': c(drop=['define'], members=['public <T> Builder define(EntityDataAccessor<T> p0, T p1) { return this; }']),
 # ---------- client rendering ----------
 'net/minecraft/client/model/Model': c(),
 'net/minecraft/client/model/EntityModel': c(tparams='<T extends net.minecraft.world.entity.Entity>', extends='net.minecraft.client.model.Model', members=[
     'public void setupAnim(T p0, float p1, float p2, float p3, float p4, float p5) {}',
     'public void renderToBuffer(com.mojang.blaze3d.vertex.PoseStack p0, com.mojang.blaze3d.vertex.VertexConsumer p1, int p2, int p3, int p4) {}',
     'public void prepareMobModel(T p0, float p1, float p2, float p3) {}',
     'public float attackTime;', 'public boolean riding;', 'public boolean young;']),
 'net/minecraft/client/model/HumanoidModel': c(tparams='<T extends net.minecraft.world.entity.LivingEntity>', extends='net.minecraft.client.model.EntityModel<T>', drop=['setupAnim'], members=['public void setupAnim(T p0, float p1, float p2, float p3, float p4, float p5) {}', 'public net.minecraft.client.model.HumanoidModel.ArmPose rightArmPose;', 'public net.minecraft.client.model.HumanoidModel.ArmPose leftArmPose;']),
 'net/minecraft/client/model/HumanoidModel$ArmPose': c(kind='enum'),
 'net/minecraft/client/model/VillagerModel': c(tparams='<T extends net.minecraft.world.entity.Entity>', extends='net.minecraft.client.model.EntityModel<T>'),
 'net/minecraft/client/model/geom/ModelPart': c(drop=['getAllParts'], members=['public java.util.stream.Stream<ModelPart> getAllParts() { return null; }', 'public boolean visible;', 'public boolean skipDraw;']),
 'net/minecraft/client/renderer/entity/EntityRenderer': c(tparams='<T extends net.minecraft.world.entity.Entity>', members=[
     'public net.minecraft.resources.ResourceLocation getTextureLocation(T p0) { return null; }',
     'public void render(T p0, float p1, float p2, com.mojang.blaze3d.vertex.PoseStack p3, net.minecraft.client.renderer.MultiBufferSource p4, int p5) {}',
     'protected float shadowRadius;']),
 'net/minecraft/client/renderer/entity/LivingEntityRenderer': c(tparams='<T extends net.minecraft.world.entity.LivingEntity, M extends net.minecraft.client.model.EntityModel<T>>', extends='net.minecraft.client.renderer.entity.EntityRenderer<T>', implements='net.minecraft.client.renderer.entity.RenderLayerParent<T, M>', members=[
     'protected M model;',
     'public LivingEntityRenderer(net.minecraft.client.renderer.entity.EntityRendererProvider.Context p0, M p1, float p2) {}',
     'public void render(T p0, float p1, float p2, com.mojang.blaze3d.vertex.PoseStack p3, net.minecraft.client.renderer.MultiBufferSource p4, int p5) {}',
     'protected void scale(T p0, com.mojang.blaze3d.vertex.PoseStack p1, float p2) {}',
     'protected net.minecraft.client.renderer.RenderType getRenderType(T p0, boolean p1, boolean p2, boolean p3) { return null; }',
     'public final boolean addLayer(net.minecraft.client.renderer.entity.layers.RenderLayer<T, M> p0) { return false; }',
     'public M getModel() { return null; }']),
 'net/minecraft/client/renderer/entity/MobRenderer': c(tparams='<T extends net.minecraft.world.entity.Mob, M extends net.minecraft.client.model.EntityModel<T>>', extends='net.minecraft.client.renderer.entity.LivingEntityRenderer<T, M>', no_default_ctor=True, drop=['<init>', 'getRenderType', 'render'], members=[
     'public MobRenderer(net.minecraft.client.renderer.entity.EntityRendererProvider.Context p0, M p1, float p2) { super(p0, p1, p2); }']),
 'net/minecraft/client/renderer/entity/RenderLayerParent': c(kind='interface', tparams='<T extends net.minecraft.world.entity.Entity, M extends net.minecraft.client.model.EntityModel<T>>', drop=['getModel', 'getTextureLocation'], members=['default M getModel() { return null; }', 'default net.minecraft.resources.ResourceLocation getTextureLocation(T p0) { return null; }']),
 'net/minecraft/client/renderer/entity/layers/RenderLayer': c(tparams='<T extends net.minecraft.world.entity.Entity, M extends net.minecraft.client.model.EntityModel<T>>', no_default_ctor=True, drop=['<init>', 'getParentModel', 'getTextureLocation', 'render'], members=[
     'public RenderLayer(net.minecraft.client.renderer.entity.RenderLayerParent<T, M> p0) {}',
     'public M getParentModel() { return null; }',
     'protected net.minecraft.resources.ResourceLocation getTextureLocation(T p0) { return null; }',
     'public void render(com.mojang.blaze3d.vertex.PoseStack p0, net.minecraft.client.renderer.MultiBufferSource p1, int p2, T p3, float p4, float p5, float p6, float p7, float p8, float p9) {}']),
 'net/minecraft/client/renderer/entity/EntityRendererProvider': c(kind='interface', tparams='<T extends net.minecraft.world.entity.Entity>', members=['net.minecraft.client.renderer.entity.EntityRenderer<T> create(Context p0);']),
 'net/minecraft/client/renderer/entity/VillagerRenderer': c(extends='net.minecraft.client.renderer.entity.MobRenderer<net.minecraft.world.entity.npc.Villager, net.minecraft.client.model.VillagerModel<net.minecraft.world.entity.npc.Villager>>', no_default_ctor=True, drop=['render', 'getTextureLocation'], members=['public net.minecraft.resources.ResourceLocation getTextureLocation(net.minecraft.world.entity.npc.Villager p0) { return null; }']),
 'net/minecraft/client/renderer/entity/ZombieRenderer': c(extends='net.minecraft.client.renderer.entity.MobRenderer<net.minecraft.world.entity.monster.Zombie, net.minecraft.client.model.EntityModel<net.minecraft.world.entity.monster.Zombie>>', no_default_ctor=True),
 'net/minecraft/client/renderer/entity/layers/HumanoidArmorLayer': c(tparams='<T extends net.minecraft.world.entity.LivingEntity, M extends net.minecraft.client.model.HumanoidModel<T>, A extends net.minecraft.client.model.HumanoidModel<T>>', extends='net.minecraft.client.renderer.entity.layers.RenderLayer<T, M>', no_default_ctor=True, drop=['<init>', 'render'], members=[
     'public HumanoidArmorLayer(net.minecraft.client.renderer.entity.RenderLayerParent<T, M> p0, A p1, A p2, net.minecraft.client.resources.model.ModelManager p3) { super(p0); }']),
 'net/minecraft/client/renderer/entity/layers/ItemInHandLayer': c(tparams='<T extends net.minecraft.world.entity.LivingEntity, M extends net.minecraft.client.model.EntityModel<T>>', extends='net.minecraft.client.renderer.entity.layers.RenderLayer<T, M>', no_default_ctor=True, drop=['<init>'], members=[
     'public ItemInHandLayer(net.minecraft.client.renderer.entity.RenderLayerParent<T, M> p0, net.minecraft.client.renderer.ItemInHandRenderer p1) { super(p0); }']),
 'net/minecraft/client/renderer/MultiBufferSource': c(kind='interface'),
 'com/mojang/blaze3d/vertex/VertexConsumer': c(kind='interface'),
 'net/neoforged/neoforge/client/event/EntityRenderersEvent$RegisterRenderers': c(extends='net.neoforged.bus.api.Event', drop=['registerEntityRenderer'], members=[
     'public <T extends net.minecraft.world.entity.Entity> void registerEntityRenderer(net.minecraft.world.entity.EntityType<? extends T> p0, net.minecraft.client.renderer.entity.EntityRendererProvider<T> p1) {}']),
 # ---------- neoforge ----------
 'net/neoforged/bus/api/Event': c(),
 'net/neoforged/bus/api/IEventBus': c(kind='interface', drop=['addListener', 'register'], members=['default <T extends net.neoforged.bus.api.Event> void addListener(java.util.function.Consumer<T> p0) {}', 'default void register(Object p0) {}']),
 'net/neoforged/neoforge/registries/DeferredRegister': c(tparams='<T>', drop=['register', 'create', 'createItems', 'getEntries'], members=[
     'public static <R> DeferredRegister<R> create(net.minecraft.resources.ResourceKey<? extends net.minecraft.core.Registry<R>> p0, String p1) { return null; }',
     'public static Items createItems(String p0) { return null; }',
     'public <I extends T> DeferredHolder<T, I> register(String p0, java.util.function.Supplier<? extends I> p1) { return null; }',
     'public void register(net.neoforged.bus.api.IEventBus p0) {}',
     'public java.util.Collection<DeferredHolder<T, ? extends T>> getEntries() { return null; }']),
 'net/neoforged/neoforge/registries/DeferredRegister$Items': c(extends='net.neoforged.neoforge.registries.DeferredRegister<net.minecraft.world.item.Item>', drop=['register', 'registerItem', 'registerSimpleItem'], members=[
     'public <I extends net.minecraft.world.item.Item> DeferredItem<I> register(String p0, java.util.function.Supplier<? extends I> p1) { return null; }']),
 'net/neoforged/neoforge/registries/DeferredHolder': c(tparams='<R, T extends R>', implements='net.minecraft.core.Holder<R>, java.util.function.Supplier<T>', drop=['get', 'getId', 'getKey', 'value'], members=[
     'public T get() { return null; }', 'public net.minecraft.resources.ResourceLocation getId() { return null; }', 'public R value() { return null; }']),
 'net/neoforged/neoforge/registries/DeferredItem': c(tparams='<T extends net.minecraft.world.item.Item>', extends='net.neoforged.neoforge.registries.DeferredHolder<net.minecraft.world.item.Item, T>', implements='net.minecraft.world.level.ItemLike'),
 'net/neoforged/neoforge/common/ModConfigSpec$ConfigValue': c(tparams='<T>', implements='java.util.function.Supplier<T>', drop=['get', 'set'], members=['public T get() { return null; }', 'public void set(T p0) {}']),
 'net/neoforged/neoforge/common/ModConfigSpec$BooleanValue': c(extends='net.neoforged.neoforge.common.ModConfigSpec.ConfigValue<Boolean>'),
 'net/neoforged/neoforge/common/ModConfigSpec$IntValue': c(extends='net.neoforged.neoforge.common.ModConfigSpec.ConfigValue<Integer>'),
 'net/neoforged/neoforge/common/ModConfigSpec$DoubleValue': c(extends='net.neoforged.neoforge.common.ModConfigSpec.ConfigValue<Double>'),
 'net/neoforged/neoforge/common/ModConfigSpec$Builder': c(drop=['define'], members=['public <T> ConfigValue<T> define(String p0, T p1) { return null; }', 'public BooleanValue define(String p0, boolean p1) { return null; }']),
 'net/neoforged/fml/config/ModConfig$Type': c(kind='enum', consts=['COMMON', 'CLIENT', 'SERVER', 'STARTUP']),
 'net/neoforged/neoforge/event/tick/EntityTickEvent$Pre': c(extends='net.neoforged.bus.api.Event'),
 'net/neoforged/neoforge/event/tick/EntityTickEvent$Post': c(extends='net.neoforged.bus.api.Event'),
 'net/neoforged/api/distmarker/Dist': c(kind='enum', consts=['CLIENT', 'DEDICATED_SERVER']),
 'net/neoforged/fml/common/EventBusSubscriber': c(kind='annotation', imports=['java.lang.annotation.*'], members=['String modid() default "";', 'net.neoforged.api.distmarker.Dist[] value() default {};', 'Bus bus() default Bus.GAME;', 'enum Bus { GAME, MOD }']),
 'net/neoforged/bus/api/SubscribeEvent': c(kind='annotation'),
 'net/minecraft/gametest/framework/GameTest': c(kind='annotation', members=['String template() default "";', 'String batch() default "defaultBatch";', 'long setupTicks() default 0L;', 'int timeoutTicks() default 100;']),
 'net/neoforged/neoforge/gametest/GameTestHolder': c(kind='annotation', members=['String value() default "minecraft";']),
 'net/neoforged/neoforge/gametest/PrefixGameTestTemplate': c(kind='annotation', members=['boolean value() default true;']),
 'net/neoforged/fml/common/Mod': c(kind='annotation', members=['String value();']),
 'net/neoforged/neoforge/event/entity/living/LivingSwapItemsEvent': c(extends='net.neoforged.bus.api.Event'),
 'net/neoforged/neoforge/event/entity/living/LivingSwapItemsEvent$Hands': c(extends='net.neoforged.neoforge.event.entity.living.LivingSwapItemsEvent'),
}
# events that only need Event as superclass
for ev in ['net/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent', 'net/neoforged/neoforge/event/entity/living/LivingHealEvent',
           'net/neoforged/neoforge/event/entity/living/LivingDeathEvent', 'net/neoforged/neoforge/event/entity/living/LivingDropsEvent',
           'net/neoforged/neoforge/event/entity/living/LivingExperienceDropEvent', 'net/neoforged/neoforge/event/entity/living/LivingDamageEvent$Post',
           'net/neoforged/neoforge/event/tick/LevelTickEvent$Post', 'net/neoforged/neoforge/event/tick/PlayerTickEvent$Post', 'net/neoforged/neoforge/event/tick/ServerTickEvent$Post',
           'net/neoforged/neoforge/event/entity/player/PlayerEvent$Clone', 'net/neoforged/neoforge/event/entity/player/PlayerEvent$StartTracking',
           'net/neoforged/neoforge/event/entity/player/PlayerInteractEvent$EntityInteract', 'net/neoforged/neoforge/event/entity/player/PlayerInteractEvent$RightClickBlock',
           'net/neoforged/neoforge/event/level/BlockEvent$BreakEvent', 'net/neoforged/neoforge/event/level/BlockEvent$EntityPlaceEvent',
           'net/neoforged/neoforge/event/server/ServerStoppingEvent', 'net/neoforged/neoforge/event/RegisterCommandsEvent', 'net/neoforged/neoforge/event/ServerChatEvent',
           'net/neoforged/neoforge/event/entity/EntityAttributeCreationEvent', 'net/neoforged/neoforge/event/entity/EntityAttributeModificationEvent',
           'net/neoforged/neoforge/event/AddPackFindersEvent', 'net/neoforged/neoforge/event/entity/player/ItemTooltipEvent',
           'net/neoforged/neoforge/event/entity/player/PlayerContainerEvent$Open', 'net/neoforged/neoforge/event/entity/player/PlayerContainerEvent$Close',
           'net/neoforged/neoforge/event/entity/player/TradeWithVillagerEvent', 'net/neoforged/neoforge/event/village/VillagerTradesEvent',
           'net/neoforged/neoforge/client/event/ClientTickEvent$Post', 'net/neoforged/neoforge/network/event/RegisterPayloadHandlersEvent']:
    OV.setdefault(ev, {}).setdefault('extends', 'net.neoforged.bus.api.Event')

OV.update({
 'net/minecraft/core/particles/ParticleOptions': c(kind='interface'),
 'net/minecraft/core/particles/ParticleType': c(tparams='<T extends net.minecraft.core.particles.ParticleOptions>'),
 'net/minecraft/core/particles/SimpleParticleType': c(extends='net.minecraft.core.particles.ParticleType<net.minecraft.core.particles.SimpleParticleType>', implements='net.minecraft.core.particles.ParticleOptions'),
 'net/minecraft/core/particles/DustParticleOptions': c(implements='net.minecraft.core.particles.ParticleOptions'),
 'net/minecraft/world/entity/ai/attributes/AttributeModifier': c(members=['public net.minecraft.resources.ResourceLocation id() { return null; }', 'public double amount() { return 0; }', 'public net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation operation() { return null; }']),
 'net/neoforged/neoforge/common/ModConfigSpec': c(implements='net.neoforged.fml.config.IConfigSpec'),
 'net/neoforged/fml/config/IConfigSpec': c(kind='interface'),
 'net/minecraft/world/item/CreativeModeTab$DisplayItemsGenerator': c(kind='interface', drop=['accept'], members=['void accept(net.minecraft.world.item.CreativeModeTab.ItemDisplayParameters p0, net.minecraft.world.item.CreativeModeTab.Output p1);']),
 'net/minecraft/world/item/CreativeModeTab$Builder': c(drop=['icon'], members=['public Builder icon(java.util.function.Supplier<net.minecraft.world.item.ItemStack> p0) { return this; }']),
})
LIVING_GENERIC = ['public java.lang.Iterable<net.minecraft.world.item.ItemStack> getAllSlots() { return null; }',
                  'public java.lang.Iterable<net.minecraft.world.item.ItemStack> getArmorSlots() { return null; }',
                  'public java.util.Collection<net.minecraft.world.effect.MobEffectInstance> getActiveEffects() { return null; }']
OV['net/minecraft/world/entity/LivingEntity'].setdefault('members', []).extend(LIVING_GENERIC)
OV['net/minecraft/world/item/ItemStack'].setdefault('members', []).append('public void forEachModifier(net.minecraft.world.entity.EquipmentSlot p0, java.util.function.BiConsumer<net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute>, net.minecraft.world.entity.ai.attributes.AttributeModifier> p1) {}')
for g in ['FloatGoal', 'LookAtPlayerGoal', 'RandomLookAroundGoal', 'RandomStrollGoal']:
    OV['net/minecraft/world/entity/ai/goal/' + g] = c(extends='net.minecraft.world.entity.ai.goal.Goal')
OV['net/minecraft/world/entity/ai/goal/WaterAvoidingRandomStrollGoal'] = c(extends='net.minecraft.world.entity.ai.goal.RandomStrollGoal')
OV['net/minecraft/world/entity/Entity'].setdefault('members', []).append('public void onSyncedDataUpdated(net.minecraft.network.syncher.EntityDataAccessor<?> p0) {}')
OV['net/minecraft/world/entity/Entity']['drop'] = ['onSyncedDataUpdated']
OV['net/minecraft/world/entity/PathfinderMob'] = c(extends=E+'Mob', drop=['onSyncedDataUpdated'])
OV['net/minecraft/world/damagesource/DamageSource'] = c(drop=['typeHolder'], members=['public net.minecraft.core.Holder<net.minecraft.world.damagesource.DamageType> typeHolder() { return null; }'])
OV['net/minecraft/nbt/Tag']['members'] = ['default String getAsString() { return null; }']
COLL = ['getFirst','getLast','removeFirst','removeLast','addFirst','addLast','reversed','forEach','stream','iterator','isEmpty','contains','addAll','clear','set','indexOf','removeIf','sort','toArray','listIterator','subList']
for k in ['net/minecraft/nbt/ListTag', 'net/minecraft/core/NonNullList']:
    OV[k].setdefault('drop', []).extend(COLL)
OV.update({
 'net/minecraft/world/inventory/AbstractContainerMenu': c(),
 'net/minecraft/world/inventory/ChestMenu': c(extends='net.minecraft.world.inventory.AbstractContainerMenu'),
 'net/minecraft/world/item/trading/MerchantOffers': c(extends='java.util.ArrayList<net.minecraft.world.item.trading.MerchantOffer>', drop=COLL + ['get','size','add','remove']),
 'net/minecraft/world/entity/npc/VillagerTrades$ItemListing': c(kind='interface', drop=['getOffer'], members=['net.minecraft.world.item.trading.MerchantOffer getOffer(net.minecraft.world.entity.Entity p0, net.minecraft.util.RandomSource p1);']),
 'net/neoforged/neoforge/event/village/VillagerTradesEvent': c(extends='net.neoforged.bus.api.Event', drop=['getTrades'], members=['public it.unimi.dsi.fastutil.ints.Int2ObjectMap<java.util.List<net.minecraft.world.entity.npc.VillagerTrades.ItemListing>> getTrades() { return null; }']),
 'net/minecraft/world/item/crafting/RecipeInput': c(kind='interface'),
 'net/minecraft/world/item/crafting/CraftingInput': c(implements='net.minecraft.world.item.crafting.RecipeInput', drop=['of'], members=['public static CraftingInput of(int p0, int p1, java.util.List<net.minecraft.world.item.ItemStack> p2) { return null; }']),
 'net/minecraft/world/item/crafting/SingleRecipeInput': c(implements='net.minecraft.world.item.crafting.RecipeInput'),
 'net/minecraft/world/item/crafting/Recipe': c(kind='interface', tparams='<T extends net.minecraft.world.item.crafting.RecipeInput>', drop=['matches','assemble','getRemainingItems','getIngredients','getResultItem'], members=[
     'default boolean matches(T p0, net.minecraft.world.level.Level p1) { return false; }',
     'default net.minecraft.world.item.ItemStack assemble(T p0, net.minecraft.core.HolderLookup.Provider p1) { return null; }',
     'default net.minecraft.core.NonNullList<net.minecraft.world.item.ItemStack> getRemainingItems(T p0) { return null; }',
     'default net.minecraft.core.NonNullList<net.minecraft.world.item.crafting.Ingredient> getIngredients() { return null; }',
     'default net.minecraft.world.item.ItemStack getResultItem(net.minecraft.core.HolderLookup.Provider p0) { return null; }']),
 'net/minecraft/world/item/crafting/CraftingRecipe': c(kind='interface', extends='net.minecraft.world.item.crafting.Recipe<net.minecraft.world.item.crafting.CraftingInput>'),
 'net/minecraft/world/item/crafting/ShapedRecipe': c(implements='net.minecraft.world.item.crafting.CraftingRecipe'),
 'net/minecraft/world/item/crafting/AbstractCookingRecipe': c(implements='net.minecraft.world.item.crafting.Recipe<net.minecraft.world.item.crafting.SingleRecipeInput>'),
 'net/minecraft/world/item/crafting/SmeltingRecipe': c(extends='net.minecraft.world.item.crafting.AbstractCookingRecipe'),
 'net/minecraft/world/item/crafting/BlastingRecipe': c(extends='net.minecraft.world.item.crafting.AbstractCookingRecipe'),
 'net/minecraft/world/item/crafting/RecipeHolder': c(tparams='<T extends net.minecraft.world.item.crafting.Recipe<?>>', drop=['value','id'], members=['public T value() { return null; }', 'public net.minecraft.resources.ResourceLocation id() { return null; }']),
 'net/minecraft/world/item/crafting/RecipeType': c(kind='interface', tparams='<T extends net.minecraft.world.item.crafting.Recipe<?>>', drop=['CRAFTING','SMELTING','BLASTING','SMOKING'], members=[
     'RecipeType<net.minecraft.world.item.crafting.CraftingRecipe> CRAFTING = null;', 'RecipeType<net.minecraft.world.item.crafting.SmeltingRecipe> SMELTING = null;', 'RecipeType<net.minecraft.world.item.crafting.BlastingRecipe> BLASTING = null;']),
 'net/minecraft/world/item/crafting/RecipeManager': c(drop=['getAllRecipesFor','getRecipeFor'], members=[
     'public <I extends net.minecraft.world.item.crafting.RecipeInput, T extends net.minecraft.world.item.crafting.Recipe<I>> java.util.List<net.minecraft.world.item.crafting.RecipeHolder<T>> getAllRecipesFor(net.minecraft.world.item.crafting.RecipeType<T> p0) { return null; }',
     'public <I extends net.minecraft.world.item.crafting.RecipeInput, T extends net.minecraft.world.item.crafting.Recipe<I>> java.util.Optional<net.minecraft.world.item.crafting.RecipeHolder<T>> getRecipeFor(net.minecraft.world.item.crafting.RecipeType<T> p0, I p1, net.minecraft.world.level.Level p2) { return null; }']),
 'net/minecraft/world/SimpleContainer': c(implements='net.minecraft.world.Container', drop=['getItems'], members=['public net.minecraft.core.NonNullList<net.minecraft.world.item.ItemStack> getItems() { return null; }']),
})
OV['net/minecraft/world/level/block/LeavesBlock'] = c(extends='net.minecraft.world.level.block.Block')
OV['net/minecraft/world/level/block/state/StateHolder']['members'].append('public boolean hasProperty(net.minecraft.world.level.block.state.properties.Property<?> p0) { return false; }')
OV['net/minecraft/world/entity/npc/VillagerProfession'] = c(drop=['<init>'], members=['public VillagerProfession(String p0, java.util.function.Predicate<net.minecraft.core.Holder<net.minecraft.world.entity.ai.village.poi.PoiType>> p1, java.util.function.Predicate<net.minecraft.core.Holder<net.minecraft.world.entity.ai.village.poi.PoiType>> p2, com.google.common.collect.ImmutableSet<net.minecraft.world.item.Item> p3, com.google.common.collect.ImmutableSet<net.minecraft.world.level.block.Block> p4, net.minecraft.sounds.SoundEvent p5) {}'])
OV['net/neoforged/neoforge/registries/DeferredHolder']['members'].append('public net.minecraft.resources.ResourceKey<R> getKey() { return null; }')
EXTRA_CLASSES = ['net/minecraft/world/level/block/LeavesBlock', 'net/minecraft/world/level/block/state/StateHolder', 'net/minecraft/world/item/crafting/AbstractCookingRecipe', 'net/minecraft/world/item/crafting/SmeltingRecipe', 'net/minecraft/world/item/crafting/BlastingRecipe', 'net/minecraft/world/entity/ai/goal/RandomStrollGoal', 'net/minecraft/core/particles/ParticleType', 'net/minecraft/world/entity/AgeableMob', 'net/minecraft/world/entity/animal/AbstractGolem', 'net/minecraft/world/entity/monster/Monster',
                 'net/minecraft/client/player/AbstractClientPlayer', 'net/minecraft/world/item/DiggerItem', 'net/minecraft/world/item/SpawnEggItem',
                 'net/minecraft/world/level/block/state/BlockBehaviour', 'net/minecraft/client/renderer/entity/LivingEntityRenderer', 'net/minecraft/client/model/Model',
                 'net/minecraft/world/level/block/entity/BaseContainerBlockEntity', 'net/minecraft/world/phys/HitResult', 'net/minecraft/world/level/entity/EntityAccess',
                 'net/minecraft/world/damagesource/DamageType', 'net/minecraft/world/item/enchantment/Enchantment', 'net/neoforged/api/distmarker/Dist',
                 'net/minecraft/world/entity/ai/attributes/Attribute']
