"""Minecraft 1.21.1 refs (what the mod used) -> Minecraft 1.20.1 refs, for the compile stubs of the Forge port.

Only Minecraft and Mojang library members are kept (Forge comes from skeletons of its real 1.20.1 sources).
Every rule below is a known difference between 1.21.1 and 1.20.1 (Mojang names); members not touched exist with the
same descriptor in both (checked by corpus_check.py against Forge, Create, Iron's Spells and Epic Fight 1.20.1).

  python3 -I to1201.py refs121_all.txt refs1201.txt
"""
import re, sys
from collections import OrderedDict

H = 'Lnet/minecraft/core/Holder;'
ATTR = 'Lnet/minecraft/world/entity/ai/attributes/Attribute;'
EFF = 'Lnet/minecraft/world/effect/MobEffect;'
ENCH = 'Lnet/minecraft/world/item/enchantment/Enchantment;'
SND = 'Lnet/minecraft/sounds/SoundEvent;'
RL = 'Lnet/minecraft/resources/ResourceLocation;'
UUIDD = 'Ljava/util/UUID;'
OP = 'Lnet/minecraft/world/entity/ai/attributes/AttributeModifier$Operation;'
STACK = 'Lnet/minecraft/world/item/ItemStack;'
TAG = 'Lnet/minecraft/nbt/CompoundTag;'

src, dst = sys.argv[1], sys.argv[2]
classes = OrderedDict()
cur = None
for line in open(src, encoding='utf-8'):
    line = line.rstrip('\n')
    if not line or line.startswith('#'):
        continue
    if not line.startswith('\t'):
        cur = line
        classes.setdefault(cur, [])
        continue
    if line[1:] not in classes[cur]:
        classes[cur].append(line[1:])

# classes that do not exist in 1.20.1 (their uses are ported by hand)
GONE = {
    'net/minecraft/core/component/DataComponentType', 'net/minecraft/core/component/DataComponents',
    'net/minecraft/world/item/component/CustomData', 'net/minecraft/world/item/component/DyedItemColor',
    'net/minecraft/world/item/component/ItemAttributeModifiers', 'net/minecraft/world/item/component/ItemAttributeModifiers$Builder',
    'net/minecraft/world/entity/EquipmentSlotGroup', 'net/minecraft/world/item/ArmorMaterial$Layer',
    'net/minecraft/world/item/crafting/RecipeHolder', 'net/minecraft/world/item/crafting/CraftingInput',
    'net/minecraft/world/item/crafting/RecipeInput', 'net/minecraft/world/item/crafting/SingleRecipeInput',
    'net/minecraft/world/item/trading/ItemCost', 'net/minecraft/server/ReloadableServerRegistries$Holder',
    'net/minecraft/network/codec/StreamCodec', 'net/minecraft/network/codec/ByteBufCodecs',
    'net/minecraft/network/protocol/common/custom/CustomPacketPayload',
    'net/minecraft/network/protocol/common/custom/CustomPacketPayload$Type',
    'net/minecraft/world/TickRateManager', 'net/minecraft/client/multiplayer/TransferState',
    'net/minecraft/advancements/AdvancementHolder', 'net/minecraft/world/item/Item$TooltipContext', 'net/minecraft/world/level/saveddata/SavedData$Factory',
    'net/minecraft/gametest/framework/GameTestBatchFactory', 'net/minecraft/gametest/framework/GameTestRunner$StructureSpawner',
    'net/minecraft/gametest/framework/GameTestRunner', 'net/minecraft/gametest/framework/GameTestRunner$Builder',
    'net/minecraft/network/syncher/SynchedEntityData$Builder',
}

# member -> None (gone) or (new name, new descriptor)
M = {
    # ResourceLocation: constructors instead of factories
    ('net/minecraft/resources/ResourceLocation', 'fromNamespaceAndPath'): None,
    ('net/minecraft/resources/ResourceLocation', 'parse'): None,
    ('net/minecraft/resources/ResourceLocation', 'withDefaultNamespace'): None,
    # attribute modifiers are named by UUID
    ('net/minecraft/world/entity/ai/attributes/AttributeModifier', 'amount'): ('getAmount', '()D'),
    ('net/minecraft/world/entity/ai/attributes/AttributeModifier', 'id'): ('getId', '()' + UUIDD),
    ('net/minecraft/world/entity/ai/attributes/AttributeModifier', 'operation'): ('getOperation', '()' + OP),
    ('net/minecraft/world/entity/ai/attributes/AttributeInstance', 'hasModifier'): ('hasModifier', '(Lnet/minecraft/world/entity/ai/attributes/AttributeModifier;)Z'),
    ('net/minecraft/world/entity/ai/attributes/AttributeInstance', 'removeModifier'): ('removeModifier', '(' + UUIDD + ')V'),
    ('net/minecraft/world/entity/ai/attributes/AttributeModifier$Operation', 'ADD_VALUE'): ('ADDITION', OP),
    ('net/minecraft/world/entity/ai/attributes/AttributeModifier$Operation', 'ADD_MULTIPLIED_BASE'): ('MULTIPLY_BASE', OP),
    ('net/minecraft/world/entity/ai/attributes/AttributeModifier$Operation', 'ADD_MULTIPLIED_TOTAL'): ('MULTIPLY_TOTAL', OP),
    ('net/minecraft/world/entity/ai/attributes/Attributes', 'SCALE'): None,
    ('net/minecraft/world/entity/ai/attributes/Attributes', 'STEP_HEIGHT'): None,
    # enchantments are objects, some renamed
    ('net/minecraft/world/item/enchantment/Enchantments', 'EFFICIENCY'): ('BLOCK_EFFICIENCY', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'POWER'): ('POWER_ARROWS', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'PROTECTION'): ('ALL_DAMAGE_PROTECTION', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'FORTUNE'): ('BLOCK_FORTUNE', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'LOOTING'): ('MOB_LOOTING', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'FEATHER_FALLING'): ('FALL_PROTECTION', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'FLAME'): ('FLAMING_ARROWS', ENCH),
    ('net/minecraft/world/item/enchantment/Enchantments', 'INFINITY'): ('INFINITY_ARROWS', ENCH),
    # item stacks: NBT, not components
    ('net/minecraft/world/item/ItemStack', 'get'): None,
    ('net/minecraft/world/item/ItemStack', 'set'): None,
    ('net/minecraft/world/item/ItemStack', 'has'): None,
    ('net/minecraft/world/item/ItemStack', 'getOrDefault'): None,
    ('net/minecraft/world/item/ItemStack', 'isSameItemSameComponents'): ('isSameItemSameTags', '(' + STACK + STACK + ')Z'),
    ('net/minecraft/world/item/ItemStack', 'parseOptional'): ('of', '(' + TAG + ')' + STACK),
    ('net/minecraft/world/item/ItemStack', 'save'): ('save', '(' + TAG + ')' + TAG),
    ('net/minecraft/world/item/ItemStack', 'forEachModifier'): ('getAttributeModifiers', '(Lnet/minecraft/world/entity/EquipmentSlot;)Lcom/google/common/collect/Multimap;'),
    ('net/minecraft/world/item/ItemStack', 'transmuteCopy'): None,
    ('net/minecraft/world/item/ItemStack', 'hurtAndBreak'): ('hurtAndBreak', '(ILnet/minecraft/world/entity/LivingEntity;Ljava/util/function/Consumer;)V'),
    ('net/minecraft/world/item/ItemStack', 'enchant'): ('enchant', '(' + ENCH + 'I)V'),
    ('net/minecraft/world/item/Item', 'getDefaultMaxStackSize'): ('getMaxStackSize', '()I'),
    ('net/minecraft/world/item/Item', 'BASE_ATTACK_DAMAGE_ID'): None,
    ('net/minecraft/world/item/Item', 'BASE_ATTACK_SPEED_ID'): None,
    ('net/minecraft/world/item/Items', 'MACE'): None,
    ('net/minecraft/world/item/ArmorItem$Type', 'getDurability'): None,
    ('net/minecraft/world/item/ArmorItem$Type', 'BODY'): None,  # wolf armour slot, 1.20.5
    # found by the first real Forge 1.20.1 compile (CI)
    ('net/minecraft/world/entity/projectile/Arrow', '<init>'): ('<init>', '(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/LivingEntity;)V'),
    ('net/minecraft/world/SimpleContainer', 'getItems'): None,
    ('net/minecraft/world/entity/LivingEntity', 'registryAccess'): None,
    ('net/minecraft/world/entity/Mob', 'registryAccess'): None,
    ('net/minecraft/world/entity/npc/Villager', 'registryAccess'): None,
    ('net/minecraft/gametest/framework/GameTestHelper', 'makeMockPlayer'): ('makeMockPlayer', '()Lnet/minecraft/world/entity/player/Player;'),
    ('net/minecraft/gametest/framework/GameTestHelper', 'getBounds'): None,
    ('net/minecraft/world/item/ArmorMaterials', 'NETHERITE'): ('NETHERITE', 'Lnet/minecraft/world/item/ArmorMaterials;'),
    # entities
    ('net/minecraft/world/entity/LivingEntity', 'getSlotForHand'): None,
    ('net/minecraft/world/entity/LivingEntity', 'igniteForSeconds'): ('setSecondsOnFire', '(I)V'),
    ('net/minecraft/world/entity/Entity', 'igniteForSeconds'): ('setSecondsOnFire', '(I)V'),
    ('net/minecraft/world/entity/animal/Wolf', 'setTame'): ('setTame', '(Z)V'),
    ('net/minecraft/world/entity/projectile/ProjectileUtil', 'getMobArrow'): ('getMobArrow', '(Lnet/minecraft/world/entity/LivingEntity;' + STACK + 'F)Lnet/minecraft/world/entity/projectile/AbstractArrow;'),
    ('net/minecraft/world/level/storage/loot/parameters/LootContextParams', 'ATTACKING_ENTITY'): ('KILLER_ENTITY', 'Lnet/minecraft/world/level/storage/loot/parameters/LootContextParam;'),
    ('net/minecraft/world/level/storage/loot/parameters/LootContextParams', 'DIRECT_ATTACKING_ENTITY'): ('DIRECT_KILLER_ENTITY', 'Lnet/minecraft/world/level/storage/loot/parameters/LootContextParam;'),
    ('net/minecraft/server/MinecraftServer', 'reloadableRegistries'): None,
    ('net/minecraft/server/MinecraftServer', 'getAverageTickTimeNanos'): ('getAverageTickTime', '()F'),
    ('net/minecraft/client/multiplayer/ClientLevel', 'tickRateManager'): None,
    ('net/minecraft/core/registries/Registries', 'ARMOR_MATERIAL'): None,
    ('net/minecraft/core/registries/Registries', 'LOOT_TABLE'): None,
    ('com/mojang/blaze3d/vertex/VertexConsumer', 'addVertex'): None,
    ('com/mojang/blaze3d/vertex/VertexConsumer', 'setColor'): None,
    ('com/mojang/blaze3d/vertex/VertexConsumer', 'setOverlay'): None,
    ('com/mojang/blaze3d/vertex/VertexConsumer', 'setNormal'): None,
    # 1.20.1 renders with float rgba, not a packed colour
    ('net/minecraft/client/model/geom/ModelPart', 'render'): ('render', '(Lcom/mojang/blaze3d/vertex/PoseStack;Lcom/mojang/blaze3d/vertex/VertexConsumer;II)V'),
    ('net/minecraft/client/model/EntityModel', 'renderToBuffer'): None,
    ('net/minecraft/client/model/EntityModel', 'renderGlow'): None,
    # synched data is defined on the entity in 1.20.1; dimensions are getDimensions
    ('net/minecraft/world/entity/PathfinderMob', 'defineSynchedData'): ('defineSynchedData', '()V'),
    ('net/minecraft/world/entity/monster/Zombie', 'defineSynchedData'): ('defineSynchedData', '()V'),
    ('net/minecraft/world/entity/PathfinderMob', 'getDefaultDimensions'): ('getDimensions', '(Lnet/minecraft/world/entity/Pose;)Lnet/minecraft/world/entity/EntityDimensions;'),
    ('com/mojang/blaze3d/vertex/VertexConsumer', 'setUv'): ('uv', '(FF)Lcom/mojang/blaze3d/vertex/VertexConsumer;'),
    ('com/mojang/blaze3d/vertex/VertexConsumer', 'setLight'): ('uv2', '(I)Lcom/mojang/blaze3d/vertex/VertexConsumer;'),
    ('net/minecraft/world/item/trading/MerchantOffer', '<init>'): ('<init>', '(' + STACK + STACK + 'IIF)V'),
    ('net/minecraft/server/ServerAdvancementManager', 'get'): ('getAdvancement', '(' + RL + ')Lnet/minecraft/advancements/Advancement;'),
    ('net/minecraft/world/item/ArmorMaterial', '<init>'): None,
    ('net/minecraft/world/item/ArmorItem', '<init>'): ('<init>', '(Lnet/minecraft/world/item/ArmorMaterial;Lnet/minecraft/world/item/ArmorItem$Type;Lnet/minecraft/world/item/Item$Properties;)V'),
    ('net/minecraft/world/level/saveddata/SavedData$Factory', '<init>'): None,
    ('net/minecraft/world/level/storage/DimensionDataStorage', 'computeIfAbsent'): None,
    ('net/minecraft/client/gui/screens/ConnectScreen', 'startConnecting'): ('startConnecting', '(Lnet/minecraft/client/gui/screens/Screen;Lnet/minecraft/client/Minecraft;Lnet/minecraft/client/multiplayer/resolver/ServerAddress;Lnet/minecraft/client/multiplayer/ServerData;Z)V'),
    ('net/minecraft/server/PlayerAdvancements', 'getOrStartProgress'): ('getOrStartProgress', '(Lnet/minecraft/advancements/Advancement;)Lnet/minecraft/advancements/AdvancementProgress;'),
}

# Holder<T> -> T where 1.20.1 passes the object itself
HOLDER_TYPE = {
    'net/minecraft/world/effect/MobEffects': EFF,
    'net/minecraft/world/entity/ai/attributes/Attributes': ATTR,
    'net/minecraft/world/effect/MobEffectInstance': EFF,
    'net/minecraft/world/item/enchantment/EnchantmentInstance': ENCH,
    'net/minecraft/sounds/SoundEvents': SND,
}
HOLDER_ATTR_EFFECT_METHODS = {'getAttribute': ATTR, 'getAttributeValue': ATTR, 'getAttributeBaseValue': ATTR,
                              'hasEffect': EFF, 'getEffect': EFF, 'removeEffect': EFF, 'add': ATTR, 'removeEffectNoUpdate': EFF}

# added in 1.20.1 terms
ADD = {
    'net/minecraft/resources/ResourceLocation': ['SP <init> (Ljava/lang/String;)V', 'SP <init> (Ljava/lang/String;Ljava/lang/String;)V'],
    'net/minecraft/world/entity/ai/attributes/AttributeModifier': ['SP <init> (' + UUIDD + 'Ljava/lang/String;D' + OP + ')V'],
    'net/minecraft/world/entity/ai/attributes/AttributeInstance': ['VM getModifier (' + UUIDD + ')Lnet/minecraft/world/entity/ai/attributes/AttributeModifier;',
                                                                  'VM removeModifier (Lnet/minecraft/world/entity/ai/attributes/AttributeModifier;)V',
                                                                  'VM removePermanentModifier (' + UUIDD + ')Z'],
    'net/minecraft/world/item/ItemStack': ['VM getTag ()' + TAG, 'VM getOrCreateTag ()' + TAG, 'VM setTag (' + TAG + ')V',
                                           'VM hasTag ()Z', 'VM getOrCreateTagElement (Ljava/lang/String;)' + TAG,
                                           'VM getTagElement (Ljava/lang/String;)' + TAG, 'VM removeTagKey (Ljava/lang/String;)V',
                                           'VM setHoverName (Lnet/minecraft/network/chat/Component;)' + STACK,
                                           'VM getEnchantmentLevel (' + ENCH + ')I'],
    'net/minecraft/world/item/enchantment/EnchantmentHelper': ['SM getItemEnchantmentLevel (' + ENCH + STACK + ')I',
                                                               'SM getEnchantments (' + STACK + ')Ljava/util/Map;',
                                                               'SM setEnchantments (Ljava/util/Map;' + STACK + ')V'],
    'net/minecraft/server/MinecraftServer': ['VM getLootData ()Lnet/minecraft/world/level/storage/loot/LootDataManager;'],
    'net/minecraft/world/level/storage/loot/LootDataManager': ['VM getLootTable (' + RL + ')Lnet/minecraft/world/level/storage/loot/LootTable;'],
    'net/minecraft/world/entity/Entity': ['VM setSecondsOnFire (I)V', 'VM setMaxUpStep (F)V', 'VM maxUpStep ()F'],
    'net/minecraft/world/item/ArmorMaterial': [],
    'net/minecraft/advancements/Advancement': [],
    'com/mojang/blaze3d/vertex/VertexConsumer': ['IMI vertex (DDD)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI color (IIII)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI color (FFFF)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI uv (FF)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI overlayCoords (I)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI uv2 (I)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI normal (FFF)Lcom/mojang/blaze3d/vertex/VertexConsumer;',
                                                 'IMI endVertex ()V',
                                                 'IMI vertex (FFFFFFFFFIIFFF)V'],
}

# members the port uses that the 1.21.1 build did not (each checked in Forge/Create/Iron's/Epic Fight 1.20.1 code)
import os
extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extra1201.txt')
if os.path.exists(extra):
    cur = None
    for line in open(extra, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#'): continue
        if not line.startswith('\t'):
            cur = line; ADD.setdefault(cur, []); continue
        ADD[cur].append(line[1:])

out = OrderedDict()
for c, members in classes.items():
    if c.startswith(('net/neoforged/', 'com/mojang/brigadier/', 'org/spongepowered/')):
        continue
    if c in GONE:
        continue
    new = []
    for m in members:
        parts = m.split(' ')
        if parts[0] in ('SUPER_OF', 'IFACE_OF'):
            new.append(m)
            continue
        kind, name, desc = parts[0], parts[1], parts[2]
        key = (c, name)
        if key in M:
            r = M[key]
            if r is None:
                continue
            name, desc = r
        desc = (desc.replace('Lnet/neoforged/neoforge/fluids/FluidType;', 'Lnet/minecraftforge/fluids/FluidType;')
                    .replace('Lnet/neoforged/neoforge/common/ItemAbility;', 'Lnet/minecraftforge/common/ToolAction;'))
        if H in desc:
            if c in HOLDER_TYPE:
                desc = desc.replace(H, HOLDER_TYPE[c])
            elif name in HOLDER_ATTR_EFFECT_METHODS:
                desc = desc.replace(H, HOLDER_ATTR_EFFECT_METHODS[name])
        if 'Lnet/minecraft/resources/ResourceKey;' in desc and c == 'net/minecraft/world/item/enchantment/Enchantments':
            desc = ENCH
        if any(g in desc for g in ['Lnet/minecraft/core/component/', 'Lnet/minecraft/world/item/component/',
                                   'EquipmentSlotGroup;', 'Lnet/minecraft/network/codec/', 'CustomPacketPayload',
                                   'Lnet/minecraft/world/item/crafting/RecipeHolder;', 'Lnet/minecraft/world/item/Item$TooltipContext;',
                                   'Lnet/minecraft/core/HolderLookup$Provider;']):
            continue
        line = f'{kind} {name} {desc}'
        if line not in new:
            new.append(line)
    out[c] = new
for c, adds in ADD.items():
    out.setdefault(c, [])
    for a in adds:
        if a not in out[c]:
            out[c].append(a)

with open(dst, 'w', encoding='utf-8') as f:
    for c, members in out.items():
        f.write(c + '\n')
        for m in members:
            f.write('\t' + m + '\n')
print('classes', len(out), 'members', sum(len(v) for v in out.values()))
