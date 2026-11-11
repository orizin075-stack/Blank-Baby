package jp.oror.reborn.relic.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.RelicSpec;
import jp.oror.reborn.relic.RelicNet;
import jp.oror.reborn.relic.RelicV9;
import jp.oror.reborn.waza.client.WazaVisuals;
import net.minecraft.client.Camera;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;
import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;
import net.neoforged.neoforge.client.event.RenderLevelStageEvent;
import net.neoforged.neoforge.client.gui.VanillaGuiLayers;
import net.neoforged.neoforge.network.PacketDistributor;
import org.joml.Matrix4f;

/**
 * (058) The relic techniques on a client: the three keys (G, H, J unless set otherwise; in a category of their own), the
 * gauge of the held weapon's three techniques over the hotbar, the warning while one is readied (its reach on the
 * ground, the light gathering at the weapon), the 3D shapes the server cues (blades, waves, beams, rings, circles,
 * pillars, spikes, rain, chains, domes, words, orbs, flashes, wings, trees, clocks, fists, arrows) and the units and
 * fields it sets down. Only ever what the server said: nothing here decides a hit.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class RelicClient {
    public static final KeyMapping[] KEYS = {
        new KeyMapping("key.oror_supreme_bosses.tech0", InputConstants.Type.KEYSYM, InputConstants.KEY_G, "key.categories.oror_supreme_bosses.relic"),
        new KeyMapping("key.oror_supreme_bosses.tech1", InputConstants.Type.KEYSYM, InputConstants.KEY_H, "key.categories.oror_supreme_bosses.relic"),
        new KeyMapping("key.oror_supreme_bosses.tech2", InputConstants.Type.KEYSYM, InputConstants.KEY_J, "key.categories.oror_supreme_bosses.relic")};
    private static final Map<Integer, Long> READY = new HashMap<>();
    private static final Map<Integer, RelicNet.Show> READYING = new HashMap<>();
    private static final List<Shape> SHAPES = new ArrayList<>();
    private static final Map<Integer, Thing> THINGS = new HashMap<>();
    private static final RandomSource R = RandomSource.create();

    private RelicClient() {
    }

    public static boolean shift() {
        return Screen.hasShiftDown();
    }

    public static String keyName(int k) {
        return KEYS[k].getTranslatedKeyMessage().getString().toUpperCase(java.util.Locale.ROOT);
    }

    @EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
    public static final class Setup {
        private Setup() {
        }

        @SubscribeEvent
        public static void keys(RegisterKeyMappingsEvent e) {
            for (KeyMapping k : KEYS) {
                e.register(k);
            }
        }

        @SubscribeEvent
        public static void gui(RegisterGuiLayersEvent e) {
            e.registerAbove(VanillaGuiLayers.HOTBAR, ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "relic_gauge"), RelicClient::gauge);
        }
    }

    // ------------------------------------------------------------------------------------------------------ the data

    static final class Shape {
        int kind, colour, life, owner;
        Vec3 at, dir;
        float size, a, h;
        String text;
        long born;
        long seed;
    }

    static final class Thing {
        int id, colour, owner;
        String kind;
        Vec3 at, was;
        float radius, hp;
        long born, until;
    }

    public static void receive(Object payload) {
        ClientLevel l = Minecraft.getInstance().level;
        if (l == null) {
            return;
        }
        long now = l.getGameTime();
        if (payload instanceof RelicNet.Show s) {
            if (s.index() < 0) {
                READYING.remove(s.entity());
            } else {
                READYING.put(s.entity(), s);
            }
        } else if (payload instanceof RelicNet.Cue c) {
            Shape s = new Shape();
            s.kind = c.kind();
            s.colour = c.colour();
            s.at = new Vec3(c.x(), c.y(), c.z());
            s.dir = new Vec3(c.dx(), c.dy(), c.dz());
            s.size = c.size();
            s.life = Math.max(2, c.life());
            s.a = c.a();
            s.h = c.h();
            s.owner = c.owner();
            s.text = c.text();
            s.born = now;
            s.seed = R.nextLong();
            synchronized (SHAPES) {
                if (SHAPES.size() > 400) {
                    SHAPES.remove(0);
                }
                SHAPES.add(s);
            }
            motes(l, s);
        } else if (payload instanceof RelicNet.Thing t) {
            if (t.op() == 2) {
                THINGS.remove(t.id());
                return;
            }
            Thing x = THINGS.get(t.id());
            if (x == null) {
                x = new Thing();
                x.id = t.id();
                x.born = now;
                x.at = new Vec3(t.x(), t.y(), t.z());
                THINGS.put(t.id(), x);
            }
            x.was = x.at;
            x.at = new Vec3(t.x(), t.y(), t.z());
            x.kind = t.kind();
            x.colour = t.colour();
            x.radius = t.radius();
            x.owner = t.owner();
            x.hp = t.hp();
            x.until = now + t.life();
        } else if (payload instanceof RelicNet.Ready r) {
            READY.put(r.index(), r.at());
        }
    }

    /** The god's themes for its motes (the mods' particles first: WazaVisuals' census). */
    static WazaVisuals.Theme theme(String character, int k) {
        WazaVisuals.Theme[] t = switch (character) {
            case "kokuhaku" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.SLASH, WazaVisuals.Theme.SPARK};
            case "chaos", "gokuka", "magna_mater", "relentless_research" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.POISON, WazaVisuals.Theme.DARK};
            case "berit", "kurma", "brutality", "eomaia" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.EARTH, WazaVisuals.Theme.SPARK};
            case "elseria", "merlinus", "nun", "demiurgos", "ain_sof_aur", "ouroboros", "miyohime", "forbidden_arcana", "innocence" ->
                new WazaVisuals.Theme[]{WazaVisuals.Theme.MAGIC, WazaVisuals.Theme.HOLY};
            case "valeria", "huang_linghua" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.LIGHTNING, WazaVisuals.Theme.SPARK};
            case "ferdinand", "hephaistos", "taika", "hakyoku" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.FIRE, WazaVisuals.Theme.SPARK};
            case "mels", "enkou", "bahamut" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.WATER, WazaVisuals.Theme.LIGHTNING};
            case "lucifara", "angra_mainyu", "cursed_love" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.DARK, WazaVisuals.Theme.BLOOD};
            case "yggdrasil", "nortia" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.NATURE, WazaVisuals.Theme.HOLY};
            case "teia", "shinra" -> new WazaVisuals.Theme[]{WazaVisuals.Theme.HOLY, WazaVisuals.Theme.WIND};
            default -> new WazaVisuals.Theme[]{WazaVisuals.Theme.HOLY, WazaVisuals.Theme.MAGIC};
        };
        return t[Math.floorMod(k, t.length)];
    }

    private static String characterOf(int owner) {
        ClientLevel l = Minecraft.getInstance().level;
        Entity e = l == null ? null : l.getEntity(owner);
        if (e instanceof Player p) {
            RelicSpec s = CharacterRelics.of(p.getMainHandItem());
            if (s != null) {
                return s.character;
            }
        }
        return "";
    }

    /**
     * The god's particles where a shape appears: the mods' own slashes, cuts, sparks and glyphs with vanilla's, by the
     * god's themes (the look the user chose: rich, as the first 058 pictures were). Two budgets a tick keep it a storm
     * and not a wall: the great ones (a slash, a cut: a sprite as long as a body) and the small.
     */
    private static long budgetTick;
    private static int small, great;

    private static void budgets(ClientLevel l) {
        long now = l.getGameTime();
        if (now != budgetTick) {
            budgetTick = now;
            small = 160;
            great = 14;
        }
    }

    static boolean spend(ClientLevel l, ParticleOptions p) {
        budgets(l);
        if (WazaVisuals.great(p)) {
            if (great <= 0) {
                return false;
            }
            great--;
        } else {
            if (small <= 0) {
                return false;
            }
            small--;
        }
        return true;
    }

    private static void motes(ClientLevel l, Shape s) {
        String ch = characterOf(s.owner);
        int n = Math.min(20, 5 + (int) (s.size * 1.5F));
        int greatHere = 0;
        for (int i = 0; i < n; i++) {
            ParticleOptions p = WazaVisuals.mote(theme(ch, i), (int) s.seed + i);
            if (WazaVisuals.great(p) && ++greatHere > 3) {
                // no more than three great ones to a shape: the rest of its particles are vanilla's small ones
                p = WazaVisuals.themedVanilla(theme(ch, i), (int) s.seed + i);
            }
            if (!spend(l, p)) {
                continue;
            }
            double r = Math.min(4.0, s.size) * R.nextDouble();
            double ang = R.nextDouble() * Math.PI * 2;
            WazaVisuals.put(l, p, s.at.x + Math.cos(ang) * r, s.at.y + R.nextDouble() * 1.2, s.at.z + Math.sin(ang) * r, (R.nextDouble() - 0.5) * 0.08,
                R.nextDouble() * 0.06, (R.nextDouble() - 0.5) * 0.08);
        }
    }

    // ------------------------------------------------------------------------------------------------------- the keys

    @SubscribeEvent
    public static void tick(ClientTickEvent.Post e) {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel l = mc.level;
        if (l == null || mc.player == null) {
            return;
        }
        RelicSpec held = CharacterRelics.of(mc.player.getMainHandItem());
        boolean weapon = held != null && RelicV9.of(held.id) != null;
        for (int k = 0; k < 3; k++) {
            while (KEYS[k].consumeClick()) {
                // only with a god-slaying weapon in hand (the keys are free for other things otherwise)
                if (mc.screen == null && weapon) {
                    PacketDistributor.sendToServer(new RelicNet.Key(k));
                }
            }
        }
        long now = l.getGameTime();
        synchronized (SHAPES) {
            SHAPES.removeIf(s -> now - s.born > s.life);
        }
        THINGS.values().removeIf(t -> now > t.until + 20);
        // the readying light gathers at the weapon, and the units and fields give off their motes
        for (Map.Entry<Integer, RelicNet.Show> en : READYING.entrySet()) {
            Entity ent = l.getEntity(en.getKey());
            RelicV9.Tech t = RelicV9.tech(en.getValue().index());
            if (ent == null || t == null) {
                continue;
            }
            Vec3 hand = ent.getEyePosition().add(ent.getLookAngle().scale(0.8)).add(0, -0.4, 0);
            for (int i = 0; i < (t.slot == 2 ? 4 : 2); i++) {
                // gathering light: small ones only (a slash flying into the hand would be no gathering)
                ParticleOptions p = WazaVisuals.themedVanilla(theme(t.character, i), t.index * 7 + i);
                if (!spend(l, p)) {
                    break;
                }
                Vec3 from = hand.add((R.nextDouble() - 0.5) * 3, (R.nextDouble() - 0.5) * 2.4, (R.nextDouble() - 0.5) * 3);
                Vec3 v = hand.subtract(from).scale(0.12);
                WazaVisuals.put(l, p, from.x, from.y, from.z, v.x, v.y, v.z);
            }
        }
        for (Thing t : THINGS.values()) {
            if ((now + t.id) % 4 == 0) {
                ParticleOptions p = WazaVisuals.mote(theme(characterOf(t.owner), t.id), t.id);
                if (!spend(l, p)) {
                    continue;
                }
                double ang = R.nextDouble() * Math.PI * 2, r = t.kind.startsWith("field:") ? t.radius * Math.sqrt(R.nextDouble()) : 0.5;
                WazaVisuals.put(l, p, t.at.x + Math.cos(ang) * r, t.at.y + 0.2, t.at.z + Math.sin(ang) * r, 0, 0.04, 0);
            }
        }
    }

    // ------------------------------------------------------------------------------------------------------ the gauge

    private static void gauge(GuiGraphics g, net.minecraft.client.DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui) {
            return;
        }
        RelicSpec s = CharacterRelics.of(mc.player.getMainHandItem());
        RelicV9.Tech[] ts = s == null ? null : RelicV9.of(s.id);
        if (ts == null) {
            return;
        }
        Font font = mc.font;
        long now = mc.level.getGameTime();
        int w = g.guiWidth(), h = g.guiHeight();
        int x0 = w / 2 + 96, y0 = h - 40;
        RelicNet.Show readying = READYING.get(mc.player.getId());
        for (int i = 0; i < 3; i++) {
            RelicV9.Tech t = ts[i];
            if (t == null) {
                continue;
            }
            int y = y0 - (2 - i) * 13;
            long at = READY.getOrDefault(t.index, 0L);
            float left = Math.max(0, at - now) / (float) Math.max(1, t.cd);
            boolean busy = readying != null && readying.index() == t.index;
            int colour = busy ? 0xFFFFE070 : left > 0 ? 0xFF808080 : (i == 2 ? 0xFFFFC040 : 0xFF70E0FF);
            g.fill(x0 - 1, y - 1, x0 + 101, y + 11, 0x90000000);
            g.fill(x0, y + 9, x0 + (int) (100 * (1 - left)), y + 11, (colour & 0x00FFFFFF) | 0xC0000000);
            String label = "[" + keyName(i) + "] " + t.name + (left > 0 ? " " + ((at - now + 19) / 20) + "s" : "");
            g.drawString(font, Component.literal(label), x0 + 2, y, colour, true);
        }
    }

    // ----------------------------------------------------------------------------------------------------- the light

    @SubscribeEvent
    public static void render(RenderLevelStageEvent e) {
        if (e.getStage() != RenderLevelStageEvent.Stage.AFTER_ENTITIES) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        ClientLevel l = mc.level;
        if (l == null || (SHAPES.isEmpty() && THINGS.isEmpty() && READYING.isEmpty())) {
            return;
        }
        Camera cam = e.getCamera();
        Vec3 cp = cam.getPosition();
        float partial = e.getPartialTick().getGameTimeDeltaPartialTick(false);
        long now = l.getGameTime();
        MultiBufferSource.BufferSource buffers = mc.renderBuffers().bufferSource();
        VertexConsumer vc = buffers.getBuffer(RenderType.lightning());
        PoseStack ps = e.getPoseStack();
        Matrix4f m = ps.last().pose();
        List<Shape> texts = new ArrayList<>();
        synchronized (SHAPES) {
            for (Shape s : SHAPES) {
                float age = now - s.born + partial;
                if (age < 0 || age > s.life || s.at.distanceToSqr(cp) > 160 * 160) {
                    continue;
                }
                if (s.kind == 10) {
                    texts.add(s);
                    continue;
                }
                RelicShapes.draw(l, vc, m, cp, s, age, partial);
            }
        }
        for (Map.Entry<Integer, RelicNet.Show> en : READYING.entrySet()) {
            Entity ent = l.getEntity(en.getKey());
            RelicV9.Tech t = RelicV9.tech(en.getValue().index());
            if (ent != null && t != null) {
                float f = Mth.clamp((now - en.getValue().start() + partial) / Math.max(1F, en.getValue().release() - en.getValue().start()), 0, 1);
                RelicShapes.telegraph(vc, m, cp, ent, t, f, partial, now);
            }
        }
        for (Thing t : THINGS.values()) {
            RelicShapes.thing(vc, m, cp, t.kind, t.colour, t.was.lerp(t.at, Mth.clamp(partial, 0, 1)), t.radius, now - t.born + partial, t.hp);
        }
        buffers.endBatch(RenderType.lightning());
        if (!texts.isEmpty()) {
            Font font = mc.font;
            for (Shape s : texts) {
                float age = now - s.born + partial;
                float fade = Math.min(1F, Math.min(age / 4F, (s.life - age) / 6F));
                ps.pushPose();
                ps.translate(s.at.x - cp.x, s.at.y - cp.y + age * 0.01, s.at.z - cp.z);
                ps.mulPose(cam.rotation());
                float sc = 0.03F * Math.max(0.6F, s.size);
                ps.scale(-sc, -sc, sc);
                int a = (int) (Mth.clamp(fade, 0, 1) * 255);
                if (a > 8) {
                    float x = -font.width(s.text) / 2F;
                    font.drawInBatch(s.text, x, 0, (a << 24) | (s.colour & 0xFFFFFF), false, ps.last().pose(), buffers, Font.DisplayMode.SEE_THROUGH,
                        0, 0xF000F0);
                }
                ps.popPose();
            }
            buffers.endBatch();
        }
    }

    /** Where the bearer looks on the ground (for a target warning), within reach. */
    static Vec3 lookPoint(Entity ent, double reach) {
        HitResult hit = ent.pick(reach, 0, false);
        return hit.getType() == HitResult.Type.MISS ? ent.position().add(ent.getLookAngle().multiply(1, 0, 1).normalize().scale(Math.min(reach, 8)))
            : hit.getLocation();
    }

    /** For the look run: the shapes alive now. */
    public static int shapes() {
        return SHAPES.size();
    }

    static Iterator<Shape> unused() {
        return SHAPES.iterator();
    }
}
