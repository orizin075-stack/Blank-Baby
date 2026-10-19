"""Mechanical first pass of the NeoForge 21.1 (MC 1.21.1) -> Forge 47 (MC 1.20.1) source port.

  python3 -I port_java.py <src/main/java>

Only renames whose meaning is the same on both sides: packages, event class names that map one to one, the
ResourceLocation factories, renamed vanilla members. Everything that changes shape (data components, attribute
modifiers, enchantment holders, networking, rendering, registration) is done by hand afterwards, guided by javac.
"""
import os, re, sys

ROOT = sys.argv[1]

IMPORTS = [
    ('net.neoforged.fml.common.EventBusSubscriber.Bus', 'net.minecraftforge.fml.common.Mod.EventBusSubscriber.Bus'),
    ('net.neoforged.fml.common.EventBusSubscriber', 'net.minecraftforge.fml.common.Mod.EventBusSubscriber'),
    ('net.neoforged.fml.config.ModConfig', 'net.minecraftforge.fml.config.ModConfig'),
    ('net.neoforged.fml.loading.LoadingModList', 'net.minecraftforge.fml.loading.LoadingModList'),
    ('net.neoforged.fml.', 'net.minecraftforge.fml.'),
    ('net.neoforged.bus.api.', 'net.minecraftforge.eventbus.api.'),
    ('net.neoforged.api.distmarker.', 'net.minecraftforge.api.distmarker.'),
    ('net.neoforged.neoforge.common.NeoForge', 'net.minecraftforge.common.MinecraftForge'),
    ('net.neoforged.neoforge.common.ModConfigSpec', 'net.minecraftforge.common.ForgeConfigSpec'),
    ('net.neoforged.neoforge.common.DeferredSpawnEggItem', 'net.minecraftforge.common.ForgeSpawnEggItem'),
    ('net.neoforged.neoforge.common.ItemAbilities', 'net.minecraftforge.common.ToolActions'),
    ('net.neoforged.neoforge.common.ItemAbility', 'net.minecraftforge.common.ToolAction'),
    ('net.neoforged.neoforge.common.util.', 'net.minecraftforge.common.util.'),
    ('net.neoforged.neoforge.common.Tags', 'net.minecraftforge.common.Tags'),
    ('net.neoforged.neoforge.server.ServerLifecycleHooks', 'net.minecraftforge.server.ServerLifecycleHooks'),
    ('net.neoforged.neoforge.fluids.', 'net.minecraftforge.fluids.'),
    ('net.neoforged.neoforge.gametest.', 'net.minecraftforge.gametest.'),
    ('net.neoforged.neoforge.registries.DeferredHolder', 'net.minecraftforge.registries.RegistryObject'),
    ('net.neoforged.neoforge.registries.DeferredItem', 'net.minecraftforge.registries.RegistryObject'),
    ('net.neoforged.neoforge.registries.DeferredRegister', 'net.minecraftforge.registries.DeferredRegister'),
    ('net.neoforged.neoforge.event.tick.PlayerTickEvent', 'net.minecraftforge.event.TickEvent.PlayerTickEvent'),
    ('net.neoforged.neoforge.event.tick.LevelTickEvent', 'net.minecraftforge.event.TickEvent.LevelTickEvent'),
    ('net.neoforged.neoforge.event.tick.ServerTickEvent', 'net.minecraftforge.event.TickEvent.ServerTickEvent'),
    ('net.neoforged.neoforge.client.event.ClientTickEvent', 'net.minecraftforge.event.TickEvent.ClientTickEvent'),
    ('net.neoforged.neoforge.event.tick.EntityTickEvent', 'net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent'),
    ('net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent', 'net.minecraftforge.event.entity.living.LivingHurtEvent'),
    ('net.neoforged.neoforge.event.entity.living.LivingDamageEvent', 'net.minecraftforge.event.entity.living.LivingDamageEvent'),
    ('net.neoforged.neoforge.client.event.', 'net.minecraftforge.client.event.'),
    ('net.neoforged.neoforge.event.', 'net.minecraftforge.event.'),
    ('net.neoforged.neoforge.network.', 'net.minecraftforge.network.'),
]

# simple expression-level renames (1.21.1 name -> 1.20.1 name)
CODE = [
    (r'ResourceLocation\.fromNamespaceAndPath\(', 'new ResourceLocation('),
    (r'ResourceLocation\.parse\(', 'new ResourceLocation('),
    (r'\bNeoForge\.EVENT_BUS\b', 'MinecraftForge.EVENT_BUS'),
    (r'\bModConfigSpec\b', 'ForgeConfigSpec'),
    (r'\bDeferredSpawnEggItem\b', 'ForgeSpawnEggItem'),
    (r'\bItemAbilities\b', 'ToolActions'),
    (r'\bItemAbility\b', 'ToolAction'),
    (r'\bLivingIncomingDamageEvent\b', 'LivingHurtEvent'),
    (r'\bDeferredHolder<[^,<>]+(?:<[^<>]*>)?,\s*', 'RegistryObject<'),
    (r'\bDeferredItem<', 'RegistryObject<'),
    (r'\bisSameItemSameComponents\(', 'isSameItemSameTags('),
    (r'"NeoForgeData"', '"ForgeData"'),
    (r'AttributeModifier\.Operation\.ADD_VALUE\b', 'AttributeModifier.Operation.ADDITION'),
    (r'AttributeModifier\.Operation\.ADD_MULTIPLIED_BASE\b', 'AttributeModifier.Operation.MULTIPLY_BASE'),
    (r'AttributeModifier\.Operation\.ADD_MULTIPLIED_TOTAL\b', 'AttributeModifier.Operation.MULTIPLY_TOTAL'),
    (r'\bOperation\.ADD_VALUE\b', 'Operation.ADDITION'),
    (r'\bOperation\.ADD_MULTIPLIED_BASE\b', 'Operation.MULTIPLY_BASE'),
    (r'\bOperation\.ADD_MULTIPLIED_TOTAL\b', 'Operation.MULTIPLY_TOTAL'),
]

changed = 0
for base, dirs, files in os.walk(ROOT):
    for f in files:
        if not f.endswith('.java'):
            continue
        p = os.path.join(base, f)
        s = open(p, encoding='utf-8').read()
        o = s
        # "import ...XTickEvent.Post;" leaves the bare name Post in the code: give it its class name first
        for m in re.finditer(r'import net\.neoforged\.[\w.]*\.(\w+)\.(Post|Pre);', o):
            outer, inner = m.group(1), m.group(2)
            body = s.split('\n')
            s = '\n'.join(l if l.startswith('import ') else re.sub(r'(?<![.\w])' + inner + r'\b(?!\s*\()', outer, l) for l in body)
            s = s.replace(m.group(0), 'import net.neoforged.' + m.group(0)[len('import net.neoforged.'):].rsplit('.', 1)[0] + ';')
        for a, b in IMPORTS:
            s = s.replace(a, b)
        for a, b in CODE:
            s = re.sub(a, b, s)
        # tick events: Forge 1.20.1 has one class per tick with a phase; the NeoForge .Post types become the class
        s = re.sub(r'\b(PlayerTickEvent|LevelTickEvent|ServerTickEvent|ClientTickEvent|LivingDamageEvent)\.Post\b', r'\1', s)
        s = re.sub(r'\bEntityTickEvent(\.(Pre|Post))?\b', 'LivingTickEvent', s)
        if s != o:
            open(p, 'w', encoding='utf-8').write(s)
            changed += 1
print('files changed', changed)
