"""Hierarchy and generics of the Minecraft 1.20.1 compile stubs: the 1.21.1 table (overrides.py) with the 1.20.1
differences applied. Forge classes are not listed here: they come from skeletons of the real Forge 1.20.1 sources."""
import importlib.util, os

_spec = importlib.util.spec_from_file_location('ov121', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overrides.py'))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
c = _m.c
OV = {k: dict(v) for k, v in _m.OV.items() if not k.startswith(('net/neoforged/', 'com/mojang/brigadier/', 'org/spongepowered/'))}
EXTRA_CLASSES = [x for x in _m.EXTRA_CLASSES if not x.startswith('net/neoforged/')]

ATTRS = ['ATTACK_DAMAGE', 'MAX_HEALTH', 'MOVEMENT_SPEED', 'ARMOR', 'ARMOR_TOUGHNESS', 'FLYING_SPEED', 'FOLLOW_RANGE',
         'KNOCKBACK_RESISTANCE', 'ATTACK_SPEED', 'LUCK', 'ATTACK_KNOCKBACK']
OV['net/minecraft/world/entity/ai/attributes/Attributes'] = c(
    drop=ATTRS + ['STEP_HEIGHT', 'SCALE', 'GRAVITY', 'SAFE_FALL_DISTANCE', 'ENTITY_INTERACTION_RANGE', 'BLOCK_INTERACTION_RANGE'],
    members=[f'public static net.minecraft.world.entity.ai.attributes.Attribute {n};' for n in ATTRS])
EFFECTS = ['POISON', 'WITHER', 'WEAKNESS', 'MOVEMENT_SLOWDOWN', 'MOVEMENT_SPEED', 'DIG_SLOWDOWN', 'DAMAGE_BOOST',
           'DAMAGE_RESISTANCE', 'REGENERATION', 'ABSORPTION', 'LEVITATION', 'CONFUSION', 'DARKNESS', 'LUCK', 'WATER_BREATHING',
           'DOLPHINS_GRACE', 'GLOWING', 'FIRE_RESISTANCE', 'HEAL', 'INVISIBILITY', 'NIGHT_VISION', 'SLOW_FALLING', 'BLINDNESS',
           'HUNGER', 'SATURATION', 'HEALTH_BOOST', 'JUMP', 'DIG_SPEED', 'HARM', 'BAD_OMEN', 'HERO_OF_THE_VILLAGE', 'UNLUCK']
OV['net/minecraft/world/effect/MobEffects'] = c(drop=EFFECTS, members=[f'public static net.minecraft.world.effect.MobEffect {n};' for n in EFFECTS])
OV['net/minecraft/world/effect/MobEffect'] = c()
OV['net/minecraft/world/effect/MobEffectInstance'] = c()
ENCH = ['UNBREAKING', 'ALL_DAMAGE_PROTECTION', 'POWER_ARROWS', 'QUICK_CHARGE', 'BLOCK_EFFICIENCY', 'SHARPNESS', 'MOB_LOOTING',
        'BLOCK_FORTUNE', 'MENDING', 'FIRE_ASPECT', 'SMITE', 'PUNCH_ARROWS', 'INFINITY_ARROWS', 'PIERCING', 'MULTISHOT', 'LOYALTY',
        'RIPTIDE', 'IMPALING', 'FALL_PROTECTION', 'FIRE_PROTECTION', 'BLAST_PROTECTION', 'PROJECTILE_PROTECTION', 'THORNS',
        'FLAMING_ARROWS', 'SILK_TOUCH', 'KNOCKBACK', 'BANE_OF_ARTHROPODS', 'SWEEPING_EDGE']
OV['net/minecraft/world/item/enchantment/Enchantments'] = c(drop=ENCH, members=[f'public static net.minecraft.world.item.enchantment.Enchantment {n};' for n in ENCH])
reg = OV['net/minecraft/core/registries/Registries']
reg['members'] = [m for m in reg['members'] if 'LOOT_TABLE' not in m]
for k in ['net/minecraft/core/component/DataComponentType', 'net/minecraft/world/entity/EquipmentSlotGroup', 'net/minecraft/world/item/Item$TooltipContext',
          'net/minecraft/server/ReloadableServerRegistries$Holder', 'net/minecraft/network/syncher/SynchedEntityData$Builder',
          'net/minecraft/world/item/crafting/RecipeInput', 'net/minecraft/world/item/crafting/CraftingInput',
          'net/minecraft/world/item/crafting/SingleRecipeInput', 'net/minecraft/world/item/crafting/RecipeHolder']:
    OV.pop(k, None)
OV['net/minecraft/world/item/Item'] = c(implements='net.minecraft.world.level.ItemLike, net.minecraftforge.common.extensions.IForgeItem', members=[
    'public void appendHoverText(net.minecraft.world.item.ItemStack p0, net.minecraft.world.level.Level p1, java.util.List<net.minecraft.network.chat.Component> p2, net.minecraft.world.item.TooltipFlag p3) {}',
    'public com.google.common.collect.Multimap<net.minecraft.world.entity.ai.attributes.Attribute, net.minecraft.world.entity.ai.attributes.AttributeModifier> getDefaultAttributeModifiers(net.minecraft.world.entity.EquipmentSlot p0) { return null; }',
    'protected static java.util.UUID BASE_ATTACK_DAMAGE_UUID;', 'protected static java.util.UUID BASE_ATTACK_SPEED_UUID;'])
OV['net/minecraft/world/entity/EquipmentSlot'] = c(kind='enum', consts=['MAINHAND', 'OFFHAND', 'FEET', 'LEGS', 'CHEST', 'HEAD'])
OV['net/minecraft/world/item/ArmorItem$Type'] = c(kind='enum', consts=['HELMET', 'CHESTPLATE', 'LEGGINGS', 'BOOTS'])
OV['net/minecraft/world/item/ArmorMaterial'] = c(kind='interface', members=[
    'int getDurabilityForType(net.minecraft.world.item.ArmorItem.Type p0);',
    'int getDefenseForType(net.minecraft.world.item.ArmorItem.Type p0);',
    'int getEnchantmentValue();', 'net.minecraft.sounds.SoundEvent getEquipSound();',
    'net.minecraft.world.item.crafting.Ingredient getRepairIngredient();', 'String getName();',
    'float getToughness();', 'float getKnockbackResistance();'])
OV['net/minecraft/world/item/ArmorMaterials'] = c(kind='enum', implements='net.minecraft.world.item.ArmorMaterial', consts=['LEATHER', 'CHAIN', 'IRON', 'GOLD', 'DIAMOND', 'TURTLE', 'NETHERITE'],
    members=['public int getDurabilityForType(net.minecraft.world.item.ArmorItem.Type p0) { return 0; }',
             'public int getDefenseForType(net.minecraft.world.item.ArmorItem.Type p0) { return 0; }',
             'public int getEnchantmentValue() { return 0; }', 'public net.minecraft.sounds.SoundEvent getEquipSound() { return null; }',
             'public net.minecraft.world.item.crafting.Ingredient getRepairIngredient() { return null; }', 'public String getName() { return null; }',
             'public float getToughness() { return 0; }', 'public float getKnockbackResistance() { return 0; }'])
OV['net/minecraft/network/syncher/SynchedEntityData'] = c(drop=['get', 'set', 'defineId', 'define'], members=[
    'public <T> T get(net.minecraft.network.syncher.EntityDataAccessor<T> p0) { return null; }',
    'public <T> void set(net.minecraft.network.syncher.EntityDataAccessor<T> p0, T p1) {}',
    'public <T> void define(net.minecraft.network.syncher.EntityDataAccessor<T> p0, T p1) {}',
    'public static <T> net.minecraft.network.syncher.EntityDataAccessor<T> defineId(Class<? extends net.minecraft.world.entity.Entity> p0, net.minecraft.network.syncher.EntityDataSerializer<T> p1) { return null; }'])
# Model.renderToBuffer and EntityModel.setupAnim are abstract: a subclass with the 1.21 signature must not compile
_RTB = 'void renderToBuffer(com.mojang.blaze3d.vertex.PoseStack p0, com.mojang.blaze3d.vertex.VertexConsumer p1, int p2, int p3, float p4, float p5, float p6, float p7)'
OV['net/minecraft/client/model/Model'] = c(abstract=True, members=['public abstract ' + _RTB + ';'])
em = OV['net/minecraft/client/model/EntityModel']
em['abstract'] = True
em['members'] = [m for m in em['members'] if 'renderToBuffer' not in m and 'setupAnim' not in m] + [
    'public abstract void setupAnim(T p0, float p1, float p2, float p3, float p4, float p5);']
for _m in ['net/minecraft/client/model/HumanoidModel', 'net/minecraft/client/model/VillagerModel']:
    OV[_m]['members'] = [m for m in OV[_m].get('members', []) if 'setupAnim' not in m] + [
        'public ' + _RTB + ' {}', 'public void setupAnim(T p0, float p1, float p2, float p3, float p4, float p5) {}']
    OV[_m]['drop'] = OV[_m].get('drop', []) + ['setupAnim', 'renderToBuffer']
OV.pop('net/minecraft/network/syncher/SynchedEntityData$Builder', None)
OV['net/minecraft/world/entity/ai/attributes/AttributeModifier'] = c(members=[
    'public java.util.UUID getId() { return null; }', 'public double getAmount() { return 0; }',
    'public net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation getOperation() { return null; }', 'public String getName() { return null; }'])
OV['net/minecraft/world/entity/ai/attributes/AttributeModifier$Operation'] = c(kind='enum', consts=['ADDITION', 'MULTIPLY_BASE', 'MULTIPLY_TOTAL'])
st = OV['net/minecraft/world/item/ItemStack']
st['members'] = [m for m in st['members'] if 'forEachModifier' not in m]
OV['net/minecraft/world/damagesource/DamageSource'] = c(drop=['typeHolder'], members=['public net.minecraft.core.Holder<net.minecraft.world.damagesource.DamageType> typeHolder() { return null; }'])
# recipes take containers in 1.20.1
OV.update({
    'net/minecraft/world/item/crafting/Recipe': c(kind='interface', tparams='<C extends net.minecraft.world.Container>', drop=['matches', 'assemble', 'getRemainingItems', 'getIngredients', 'getResultItem'], members=[
        'default boolean matches(C p0, net.minecraft.world.level.Level p1) { return false; }',
        'default net.minecraft.world.item.ItemStack assemble(C p0, net.minecraft.core.RegistryAccess p1) { return null; }',
        'default net.minecraft.core.NonNullList<net.minecraft.world.item.ItemStack> getRemainingItems(C p0) { return null; }',
        'default net.minecraft.core.NonNullList<net.minecraft.world.item.crafting.Ingredient> getIngredients() { return null; }',
        'default net.minecraft.world.item.ItemStack getResultItem(net.minecraft.core.RegistryAccess p0) { return null; }',
        'default net.minecraft.resources.ResourceLocation getId() { return null; }']),
    'net/minecraft/world/inventory/CraftingContainer': c(kind='interface', extends='net.minecraft.world.Container'),
    'net/minecraft/world/inventory/TransientCraftingContainer': c(implements='net.minecraft.world.inventory.CraftingContainer', drop=['<init>'], members=[
        'public TransientCraftingContainer(net.minecraft.world.inventory.AbstractContainerMenu p0, int p1, int p2) {}']),
    'net/minecraft/world/item/crafting/CraftingRecipe': c(kind='interface', extends='net.minecraft.world.item.crafting.Recipe<net.minecraft.world.inventory.CraftingContainer>'),
    'net/minecraft/world/item/crafting/ShapedRecipe': c(implements='net.minecraft.world.item.crafting.CraftingRecipe'),
    'net/minecraft/world/item/crafting/AbstractCookingRecipe': c(implements='net.minecraft.world.item.crafting.Recipe<net.minecraft.world.Container>'),
    'net/minecraft/world/item/crafting/RecipeManager': c(drop=['getAllRecipesFor', 'getRecipeFor'], members=[
        'public <C extends net.minecraft.world.Container, T extends net.minecraft.world.item.crafting.Recipe<C>> java.util.List<T> getAllRecipesFor(net.minecraft.world.item.crafting.RecipeType<T> p0) { return null; }',
        'public <C extends net.minecraft.world.Container, T extends net.minecraft.world.item.crafting.Recipe<C>> java.util.Optional<T> getRecipeFor(net.minecraft.world.item.crafting.RecipeType<T> p0, C p1, net.minecraft.world.level.Level p2) { return null; }']),
})
EXTRA_CLASSES += ['net/minecraft/world/inventory/CraftingContainer', 'net/minecraft/world/inventory/TransientCraftingContainer']

# Forge's patches: the extension interfaces
OV['net/minecraft/world/entity/Entity']['implements'] = 'net.minecraft.world.level.entity.EntityAccess, net.minecraftforge.common.extensions.IForgeEntity'
OV['net/minecraft/world/entity/LivingEntity']['implements'] = 'net.minecraftforge.common.extensions.IForgeLivingEntity'
OV['net/minecraft/world/item/ItemStack']['implements'] = 'net.minecraftforge.common.extensions.IForgeItemStack'
# brigadier argument types (real brigadier sources compile with the stubs, so the argument classes need their types)
OV['net/minecraft/commands/arguments/coordinates/BlockPosArgument'] = c(implements='com.mojang.brigadier.arguments.ArgumentType<net.minecraft.commands.arguments.coordinates.Coordinates>', members=[
    'public net.minecraft.commands.arguments.coordinates.Coordinates parse(com.mojang.brigadier.StringReader p0) { return null; }'])
OV['net/minecraft/commands/arguments/coordinates/Coordinates'] = c(kind='interface')
OV['net/minecraft/commands/arguments/selector/EntitySelector'] = c()
OV['net/minecraft/commands/arguments/EntityArgument'] = c(implements='com.mojang.brigadier.arguments.ArgumentType<net.minecraft.commands.arguments.selector.EntitySelector>', drop=['getEntities'], members=[
    'public net.minecraft.commands.arguments.selector.EntitySelector parse(com.mojang.brigadier.StringReader p0) { return null; }',
    'public static java.util.Collection<? extends net.minecraft.world.entity.Entity> getEntities(com.mojang.brigadier.context.CommandContext<net.minecraft.commands.CommandSourceStack> p0, String p1) throws com.mojang.brigadier.exceptions.CommandSyntaxException { return null; }'])
OV['net/minecraft/client/multiplayer/ClientLevel'] = c(extends='net.minecraft.world.level.Level', drop=['entitiesForRendering'], members=[
    'public java.lang.Iterable<net.minecraft.world.entity.Entity> entitiesForRendering() { return null; }'])
EXTRA_CLASSES += ['net/minecraft/commands/arguments/coordinates/Coordinates', 'net/minecraft/commands/arguments/selector/EntitySelector']
# loot: 1.20.1 function types wrap a JSON serializer
reg = OV['net/minecraft/core/registries/Registries']
reg['members'].append('public static net.minecraft.resources.ResourceKey<net.minecraft.core.Registry<net.minecraft.world.level.storage.loot.functions.LootItemFunctionType>> LOOT_FUNCTION_TYPE;')
OV['net/minecraft/world/level/storage/loot/Serializer'] = c(kind='interface', tparams='<T>', members=[
    'void serialize(com.google.gson.JsonObject p0, T p1, com.google.gson.JsonSerializationContext p2);',
    'T deserialize(com.google.gson.JsonObject p0, com.google.gson.JsonDeserializationContext p1);'])
OV['net/minecraft/world/level/storage/loot/functions/LootItemFunctionType'] = c(drop=['<init>'], members=[
    'public LootItemFunctionType(net.minecraft.world.level.storage.loot.Serializer<? extends net.minecraft.world.level.storage.loot.functions.LootItemFunction> p0) {}'])
OV['net/minecraft/world/level/storage/loot/functions/LootItemFunction'] = c(kind='interface', extends='java.util.function.BiFunction<net.minecraft.world.item.ItemStack, net.minecraft.world.level.storage.loot.LootContext, net.minecraft.world.item.ItemStack>', drop=['getType', 'apply'], members=[
    'net.minecraft.world.level.storage.loot.functions.LootItemFunctionType getType();'])
EXTRA_CLASSES += ['net/minecraft/world/level/storage/loot/Serializer']
OV['net/minecraft/commands/Commands'] = c(drop=['argument', 'literal'], members=[
    'public static com.mojang.brigadier.builder.LiteralArgumentBuilder<net.minecraft.commands.CommandSourceStack> literal(String p0) { return null; }',
    'public static <T> com.mojang.brigadier.builder.RequiredArgumentBuilder<net.minecraft.commands.CommandSourceStack, T> argument(String p0, com.mojang.brigadier.arguments.ArgumentType<T> p1) { return null; }'])
OV['net/minecraft/commands/SharedSuggestionProvider'] = c(kind='interface', drop=['suggest'], members=[
    'static java.util.concurrent.CompletableFuture<com.mojang.brigadier.suggestion.Suggestions> suggest(java.lang.Iterable<String> p0, com.mojang.brigadier.suggestion.SuggestionsBuilder p1) { return null; }'])
st = OV['net/minecraft/world/item/ItemStack']
st.setdefault('drop', []).append('hurtAndBreak')
st['members'].append('public <T extends net.minecraft.world.entity.LivingEntity> void hurtAndBreak(int p0, T p1, java.util.function.Consumer<T> p2) {}')
sc = OV['net/minecraft/world/SimpleContainer']
sc['members'] = sc.get('members', []) + ['public SimpleContainer(net.minecraft.world.item.ItemStack... p0) {}']
# entity type constants carry their entity class
_ET = {'ARROW': 'projectile.Arrow', 'COW': 'animal.Cow', 'HUSK': 'monster.Husk', 'IRON_GOLEM': 'animal.IronGolem', 'PIG': 'animal.Pig',
       'VILLAGER': 'npc.Villager', 'WOLF': 'animal.Wolf', 'ZOMBIE': 'monster.Zombie', 'LIGHTNING_BOLT': 'LightningBolt',
       'PILLAGER': 'monster.Pillager', 'WANDERING_TRADER': 'npc.WanderingTrader', 'TRADER_LLAMA': 'animal.horse.TraderLlama'}
et = OV['net/minecraft/world/entity/EntityType']
et['drop'] = et.get('drop', []) + list(_ET)
et['members'] = et.get('members', []) + [f'public static EntityType<net.minecraft.world.entity.{c}> {n};' for n, c in _ET.items()]
for _c in ['net/minecraft/world/entity/animal/Pig', 'net/minecraft/world/entity/monster/Pillager']:
    OV.setdefault(_c, c(extends=('net.minecraft.world.entity.animal.Animal' if _c.endswith('Pig') else 'net.minecraft.world.entity.raid.Raider')))
EXTRA_CLASSES += ['net/minecraft/world/entity/animal/Pig', 'net/minecraft/world/entity/monster/Pillager']
# saved data: 1.20.1 save(tag) and computeIfAbsent(load, create, name)
OV['net/minecraft/world/level/saveddata/SavedData'] = c(drop=['save'], members=['public net.minecraft.nbt.CompoundTag save(net.minecraft.nbt.CompoundTag p0) { return null; }'])
OV['net/minecraft/world/level/storage/DimensionDataStorage'] = c(drop=['computeIfAbsent'], members=[
    'public <T extends net.minecraft.world.level.saveddata.SavedData> T computeIfAbsent(java.util.function.Function<net.minecraft.nbt.CompoundTag, T> p0, java.util.function.Supplier<T> p1, String p2) { return null; }'])
OV.pop('net/minecraft/world/level/saveddata/SavedData$Factory', None)
st = OV['net/minecraft/world/item/ItemStack']
st['drop'].append('getAttributeModifiers')
st['members'].append('public com.google.common.collect.Multimap<net.minecraft.world.entity.ai.attributes.Attribute, net.minecraft.world.entity.ai.attributes.AttributeModifier> getAttributeModifiers(net.minecraft.world.entity.EquipmentSlot p0) { return null; }')
# loot data: 1.20.1 keeps loot tables in LootDataManager, keyed by ResourceLocation
OV['net/minecraft/world/level/storage/loot/LootDataManager'] = c(members=[
    'public net.minecraft.world.level.storage.loot.LootTable getLootTable(net.minecraft.resources.ResourceLocation p0) { return null; }',
    'public java.util.Collection<net.minecraft.resources.ResourceLocation> getKeys(net.minecraft.world.level.storage.loot.LootDataType<?> p0) { return null; }'])
OV['net/minecraft/world/level/storage/loot/LootDataType'] = c(members=[
    'public static LootDataType<net.minecraft.world.level.storage.loot.LootTable> TABLE;'], tparams='<T>')
EXTRA_CLASSES += ['net/minecraft/world/level/storage/loot/LootDataType']
gs = OV.setdefault('net/minecraft/world/entity/ai/goal/GoalSelector', c())
gs['members'] = gs.get('members', []) + ['public void removeAllGoals(java.util.function.Predicate<net.minecraft.world.entity.ai.goal.Goal> p0) {}']
