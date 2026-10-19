"""Second mechanical pass (1.21.1 -> 1.20.1) for patterns that are safe to rewrite textually:
holders of effects/attributes/enchantments become the objects, renamed enchantments, ResourceLocation defaults,
enchantment lookups through the registry become the static objects."""
import os, re, sys
ROOT = sys.argv[1]
ENCH = {'EFFICIENCY': 'BLOCK_EFFICIENCY', 'POWER': 'POWER_ARROWS', 'PROTECTION': 'ALL_DAMAGE_PROTECTION', 'FORTUNE': 'BLOCK_FORTUNE',
        'LOOTING': 'MOB_LOOTING', 'FEATHER_FALLING': 'FALL_PROTECTION', 'FLAME': 'FLAMING_ARROWS', 'INFINITY': 'INFINITY_ARROWS',
        'PUNCH': 'PUNCH_ARROWS'}
n = 0
for base, dirs, files in os.walk(ROOT):
    for f in files:
        if not f.endswith('.java'): continue
        p = os.path.join(base, f); s = open(p, encoding='utf-8').read(); o = s
        s = s.replace('Holder<MobEffect>', 'MobEffect').replace('Holder<Attribute>', 'Attribute')
        s = s.replace('Holder<net.minecraft.world.effect.MobEffect>', 'net.minecraft.world.effect.MobEffect')
        s = s.replace('Holder<net.minecraft.world.entity.ai.attributes.Attribute>', 'net.minecraft.world.entity.ai.attributes.Attribute')
        s = re.sub(r'ResourceLocation\.withDefaultNamespace\(', 'new ResourceLocation(', s)
        for a, b in ENCH.items():
            s = re.sub(r'\bEnchantments\.' + a + r'\b', 'Enchantments.' + b, s)
        # x.registryAccess().registryOrThrow(Registries.ENCHANTMENT).getHolderOrThrow(E) -> E
        s = re.sub(r'[\w().]*\.registryAccess\(\)\.registryOrThrow\(Registries\.ENCHANTMENT\)\.getHolderOrThrow\(([^()]*(?:\([^()]*\))?[^()]*)\)', r'\1', s)
        s = re.sub(r'\b\w+\.getHolderOrThrow\((Enchantments\.\w+)\)', r'\1', s)
        s = s.replace('ResourceKey<Enchantment>', 'Enchantment')
        if s != o:
            open(p, 'w', encoding='utf-8').write(s); n += 1
print('files', n)
