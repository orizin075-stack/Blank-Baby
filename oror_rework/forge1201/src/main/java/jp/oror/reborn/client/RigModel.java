package jp.oror.reborn.client;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * Data-driven model: bones, cubes and animation tags come from assets/oror_supreme_bosses/rigs.json.
 * Bones form a real hierarchy (hair, horns and halos follow the head; sleeves and weapons follow the arms)
 * and every cube has its own UV box, so textures can carry faces, hair strands and clothing detail.
 * A rig may also name a sculpted mesh (assets/oror_supreme_bosses/meshes/<name>.bin): smooth, per-vertex-normal
 * quads attached to the same bones, drawn like ModelPart cubes so every animation tag still applies.
 */
public abstract class RigModel<T extends LivingEntity> extends EntityModel<T> {
    private static final Map<String, Rig> RIGS = load();
    public final ModelPart root;
    public final String key;
    public final ResourceLocation texture;
    public final ResourceLocation glowTexture;
    public final float height;
    public final boolean translucent;
    private final int tint;
    private final List<Animated> animated = new ArrayList<>();
    private final Map<String, ModelPart> parts = new HashMap<>();
    private final List<ModelPart> chainRight = new ArrayList<>();
    private final List<ModelPart> chainLeft = new ArrayList<>();
    private float reachRight = 10.0F;
    private float reachLeft = 10.0F;
    private MeshNode[] meshRoots;
    private float[] scratch = new float[0];
    private final Vector3f tmp = new Vector3f();

    private static Map<String, Rig> load() {
        try (InputStream in = RigModel.class.getResourceAsStream("/assets/oror_supreme_bosses/rigs.json")) {
            if (in == null) {
                throw new IllegalStateException("Missing rigs.json");
            }

            Map<String, Rig> rigs = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), new TypeToken<Map<String, Rig>>() {
            }.getType());
            return Collections.unmodifiableMap(rigs);
        } catch (IOException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    public static boolean has(String key) {
        return RIGS.containsKey(key);
    }

    protected RigModel(String key, int tint) {
        Rig rig = RIGS.get(key);
        if (rig == null) {
            throw new IllegalStateException("Missing rig " + key);
        }

        this.key = key;
        this.tint = tint;
        this.height = rig.height;
        this.translucent = rig.translucent;
        this.texture = new ResourceLocation("oror_supreme_bosses", "textures/entity/" + rig.texture + ".png");
        this.glowTexture = new ResourceLocation("oror_supreme_bosses", "textures/entity/" + rig.texture + "_glow.png");
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition top = mesh.getRoot();
        Map<String, PartDefinition> defs = new HashMap<>();

        for (Bone b : rig.bones) {
            CubeListBuilder cubes = CubeListBuilder.create();

            for (Cube c : b.cubes) {
                cubes = cubes.texOffs(c.uv[0], c.uv[1]).addBox(c.o[0], c.o[1], c.o[2], c.s[0], c.s[1], c.s[2]);
            }

            PartDefinition parent = b.parent == null ? top : defs.get(b.parent);
            defs.put(b.name, parent.addOrReplaceChild(b.name, cubes, PartPose.offsetAndRotation(b.at[0], b.at[1], b.at[2], b.rot[0], b.rot[1], b.rot[2])));
        }

        this.root = LayerDefinition.create(mesh, rig.size[0], rig.size[1]).bakeRoot();
        Map<String, String> parentOf = new HashMap<>();

        for (Bone b : rig.bones) {
            ModelPart part = b.parent == null ? this.root.getChild(b.name) : this.parts.get(b.parent).getChild(b.name);
            this.parts.put(b.name, part);
            parentOf.put(b.name, b.parent);
            if (b.anim != null && !b.anim.isEmpty()) {
                this.animated.add(new Animated(part, b.anim, b.p == null ? Map.of() : b.p, b.name.endsWith("_l") || b.name.contains("_l_")));
            }

            if (b.name.equals("arm_r") && b.p != null && b.p.containsKey("reach")) {
                this.reachRight = b.p.get("reach");
            }

            if (b.name.equals("arm_l") && b.p != null && b.p.containsKey("reach")) {
                this.reachLeft = b.p.get("reach");
            }
        }

        String handR = "arm_r";
        String handL = "arm_l";
        for (Bone b : rig.bones) {
            if (b.name.equals("fore_r") && b.p != null && b.p.containsKey("reach")) {
                handR = "fore_r";
                this.reachRight = b.p.get("reach");
            }

            if (b.name.equals("fore_l") && b.p != null && b.p.containsKey("reach")) {
                handL = "fore_l";
                this.reachLeft = b.p.get("reach");
            }
        }

        chain(parentOf, handR, this.chainRight);
        chain(parentOf, handL, this.chainLeft);
        if (rig.mesh != null) {
            try {
                this.meshRoots = loadMesh(rig, this.parts);
            } catch (RuntimeException e) {
                // a broken or missing mesh must not take the game down: the character is then simply not drawn
                System.err.println("[oror_supreme_bosses] could not load mesh for rig " + key + ": " + e);
                this.meshRoots = null;
            }
        }
    }

    /**
     * Reads meshes/<name>.bin: per bone (rig order) its vertices (1/32 px, uv / 65535, normal / 127), its quads and
     * the subset of quads that carry emissive texels (the only ones the glow pass has to draw).
     */
    private static MeshNode[] loadMesh(Rig rig, Map<String, ModelPart> parts) {
        String path = "/assets/oror_supreme_bosses/meshes/" + rig.mesh + ".bin";
        try (InputStream raw = RigModel.class.getResourceAsStream(path)) {
            if (raw == null) {
                throw new IllegalStateException("Missing " + path);
            }

            DataInputStream in = new DataInputStream(new BufferedInputStream(raw));
            if (in.readInt() != 0x4F524D33 || in.readInt() != rig.bones.size()) {
                throw new IllegalStateException("Bad mesh " + path);
            }

            Map<String, MeshNode> nodes = new HashMap<>();
            List<MeshNode> roots = new ArrayList<>();
            List<MeshNode> order = new ArrayList<>();
            for (Bone b : rig.bones) {
                int vc = in.readInt();
                float[] v = new float[vc * 8];
                int[] q = new int[0];
                int[] g = new int[0];
                if (vc > 0) {
                    for (int i = 0; i < vc; i++) {
                        int o = i * 8;
                        v[o] = in.readShort() / 512.0F;
                        v[o + 1] = in.readShort() / 512.0F;
                        v[o + 2] = in.readShort() / 512.0F;
                        v[o + 3] = in.readChar() / 65535.0F;
                        v[o + 4] = in.readChar() / 65535.0F;
                        v[o + 5] = in.readByte() / 127.0F;
                        v[o + 6] = in.readByte() / 127.0F;
                        v[o + 7] = in.readByte() / 127.0F;
                    }

                    q = new int[in.readInt() * 4];
                    for (int i = 0; i < q.length; i++) {
                        q[i] = in.readChar();
                    }

                    g = new int[in.readInt() * 4];
                    for (int i = 0; i < g.length; i++) {
                        g[i] = in.readChar();
                    }
                }

                MeshNode n = new MeshNode(parts.get(b.name), v, q, g);
                nodes.put(b.name, n);
                order.add(n);
                if (b.parent == null) {
                    roots.add(n);
                } else {
                    nodes.get(b.parent).children.add(n);
                }
            }

            for (int i = order.size() - 1; i >= 0; i--) {
                MeshNode n = order.get(i);
                n.children.removeIf(c -> !c.used);
                n.used = n.quads.length > 0 || !n.children.isEmpty();
            }

            roots.removeIf(n -> !n.used);
            return roots.toArray(new MeshNode[0]);
        } catch (IOException e) {
            throw new IllegalStateException("Unreadable " + path, e);
        }
    }

    private void renderMeshes(PoseStack p, VertexConsumer v, int light, int overlay, int color, boolean glow) {
        if (this.meshRoots == null) {
            return;
        }

        p.pushPose();
        this.root.translateAndRotate(p);
        for (MeshNode n : this.meshRoots) {
            this.draw(n, p, v, light, overlay, color, glow);
        }

        p.popPose();
    }

    private void draw(MeshNode n, PoseStack p, VertexConsumer v, int light, int overlay, int color, boolean glow) {
        ModelPart part = n.part;
        if (part.xScale == 0.0F && part.yScale == 0.0F && part.zScale == 0.0F) {
            return;
        }

        p.pushPose();
        part.translateAndRotate(p);
        int[] quads = glow ? n.glowQuads : n.quads;
        if (quads.length > 0) {
            PoseStack.Pose pose = p.last();
            Matrix4f m = pose.pose();
            Matrix3f nm = pose.normal();
            float[] d = n.verts;
            int count = d.length / 8;
            if (this.scratch.length < count * 6) {
                this.scratch = new float[count * 6];
            }

            float[] out = this.scratch;
            Vector3f t = this.tmp;
            for (int i = 0; i < count; i++) {
                int k = i * 8;
                int o = i * 6;
                m.transformPosition(d[k], d[k + 1], d[k + 2], t);
                out[o] = t.x;
                out[o + 1] = t.y;
                out[o + 2] = t.z;
                nm.transform(d[k + 5], d[k + 6], d[k + 7], t);
                t.normalize();
                out[o + 3] = t.x;
                out[o + 4] = t.y;
                out[o + 5] = t.z;
            }

            for (int q : quads) {
                int k = q * 8;
                int o = q * 6;
                v.vertex(out[o], out[o + 1], out[o + 2])
                    .color(color >> 16 & 255, color >> 8 & 255, color & 255, color >>> 24)
                    .uv(d[k + 3], d[k + 4])
                    .overlayCoords(overlay)
                    .uv2(light)
                    .normal(out[o + 3], out[o + 4], out[o + 5])
                    .endVertex();
            }
        }

        for (MeshNode c : n.children) {
            this.draw(c, p, v, light, overlay, color, glow);
        }

        p.popPose();
    }

    private void chain(Map<String, String> parentOf, String end, List<ModelPart> out) {
        if (!this.parts.containsKey(end)) {
            return;
        }

        List<String> names = new ArrayList<>();

        for (String n = end; n != null; n = parentOf.get(n)) {
            names.add(0, n);
        }

        out.add(this.root);

        for (String n : names) {
            out.add(this.parts.get(n));
        }
    }

    /** Moves the pose stack to the palm of an arm; returns false when the rig has no such arm. */
    public boolean translateToHand(PoseStack p, boolean left) {
        List<ModelPart> chain = left ? this.chainLeft : this.chainRight;
        if (chain.isEmpty()) {
            return false;
        }

        for (ModelPart part : chain) {
            part.translateAndRotate(p);
        }

        p.translate(0.0, (double)((left ? this.reachLeft : this.reachRight) / 16.0F), 0.0);
        return true;
    }

    protected void animate(T e, float swing, float amount, float age, float yaw, float pitch, int motion, float progress, int action, int form) {
        this.root.getAllParts().forEach(ModelPart::resetPose);
        float pulse = Mth.sin(progress * (float) Math.PI);
        // off the ground (leaps, knock-ups, dashes) the legs tuck up
        float air = e.onGround() ? 0.0F : 1.0F;

        for (Animated a : this.animated) {
            ModelPart part = a.part;
            float amp = a.f("amp", 0.1F);
            float speed = a.f("speed", 0.08F);
            float phase = a.f("phase", 0.0F);
            float side = a.left ? -1.0F : 1.0F;
            switch (a.anim) {
                case "root": {
                    float hover = a.f("hover", 0.0F);
                    if (hover > 0.0F) {
                        part.y = part.y - hover - Mth.sin(age * a.f("speed", 0.06F)) * hover;
                    }

                    if (motion == 4) {
                        part.yRot = part.yRot + progress * (float) (Math.PI * 2);
                    } else if (motion == 6) {
                        part.zRot = part.zRot + pulse * 0.15F;
                    } else if (motion == 7) {
                        part.y = part.y - pulse * 3.0F;
                    } else if (motion == 10) {
                        part.xRot = part.xRot - pulse * 0.15F;
                    } else if (motion == 12) {
                        part.yRot = part.yRot - pulse * 0.4F;
                    } else if (motion == 1 || motion == 9) {
                        part.yRot = part.yRot - pulse * 0.3F;
                    } else if (motion == 5) {
                        part.yRot = part.yRot + pulse * 0.45F;
                    } else if (motion == 2) {
                        part.xRot = part.xRot + pulse * 0.22F;
                    } else if (motion == 3) {
                        part.xRot = part.xRot + pulse * 0.18F;
                        part.y = part.y + pulse * 1.2F;
                    } else if (motion == 13) {
                        part.y = part.y - pulse * 0.8F;
                    } else if (motion == 8 || motion == 11 || motion == 15) {
                        part.xRot = part.xRot - pulse * 0.08F;
                    }
                    break;
                }
                case "breath":
                    part.xRot = part.xRot + Mth.sin(age * 0.08F) * 0.015F + (action > 0 ? 0.08F : 0.0F);
                    if (motion == 1 || motion == 3 || motion == 5) {
                        part.yRot = part.yRot + pulse * 0.35F;
                    } else if (motion == 9 || motion == 12) {
                        part.yRot = part.yRot - pulse * 0.35F;
                    } else if (motion == 2) {
                        part.xRot = part.xRot + pulse * 0.15F;
                    } else if (motion == 16) {
                        part.xRot = part.xRot - pulse * 0.12F;
                    }
                    break;
                case "head":
                    part.yRot = part.yRot + yaw * (float) (Math.PI / 180.0);
                    part.xRot = part.xRot + pitch * (float) (Math.PI / 180.0);
                    if (motion == 9 || motion == 10 || motion == 14) {
                        part.xRot = part.xRot + (motion == 9 ? 0.3F : -0.25F) * pulse;
                    }
                    break;
                case "arm_r":
                case "arm_l": {
                    boolean left = a.anim.equals("arm_l");
                    float sign = left ? -1.0F : 1.0F;
                    part.xRot = part.xRot + Mth.cos(swing * 0.6662F + (left ? 0.0F : (float) Math.PI)) * amount * 0.6F;
                    part.zRot = part.zRot + sign * (Mth.cos(age * 0.09F) * 0.03F + 0.04F);
                    if (action > 0) {
                        part.xRot -= 0.6F;
                    }

                    arm(part, motion, pulse, sign, left);
                    break;
                }
                case "leg_r":
                case "leg_l": {
                    boolean leftLeg = a.anim.equals("leg_l");
                    part.xRot = part.xRot + Mth.cos(swing * 0.6662F + (leftLeg ? (float) Math.PI : 0.0F)) * amount * 0.8F * (1.0F - air);
                    part.xRot = part.xRot - air * (leftLeg ? 0.35F : 0.7F);
                    leg(part, motion, pulse, leftLeg ? -1.0F : 1.0F, leftLeg);
                    break;
                }
                case "skirt":
                    part.xRot = part.xRot - Math.abs(Mth.cos(swing * 0.6662F)) * amount * 0.12F * a.f("k", 1.0F);
                    part.zRot = part.zRot + Mth.sin(age * 0.05F) * 0.012F;
                    break;
                case "hair":
                case "cape":
                    part.xRot = part.xRot + amount * a.f("drag", a.anim.equals("cape") ? 0.9F : 0.5F) * 0.6F + Mth.sin(age * speed + phase) * amp;
                    part.zRot = part.zRot + Mth.cos(age * speed * 0.7F + phase) * amp * 0.3F;
                    break;
                case "tail": {
                    float i = a.f("i", 0.0F);
                    part.yRot = part.yRot + Mth.sin(age * speed - i * 0.6F) * amp * (1.0F + i * 0.15F);
                    part.xRot = part.xRot + Mth.cos(age * speed * 0.7F - i * 0.5F) * amp * 0.25F;
                    if (motion == 3 || motion == 4) {
                        part.yRot = part.yRot + pulse * 0.8F / (1.0F + i);
                    }
                    break;
                }
                case "wing_r":
                case "wing_l": {
                    float flap = Mth.sin(age * speed) * amp + (motion == 11 || motion == 14 ? pulse * 0.7F : 0.0F) + amount * 0.3F;
                    part.yRot = part.yRot + (a.anim.equals("wing_l") ? -flap : flap);
                    break;
                }
                case "spin": {
                    float turn = age * speed + (float)form * a.f("form", 0.0F);
                    int axis = (int)a.f("ax", 0.0F);
                    if (axis == 1) {
                        part.xRot += turn;
                    } else if (axis == 2) {
                        part.zRot += turn;
                    } else {
                        part.yRot += turn;
                    }

                    if ((motion == 8 || motion == 12) && a.f("cast", 1.0F) > 0.0F) {
                        part.yRot = part.yRot + progress * (float) (Math.PI * 2);
                    }
                    break;
                }
                case "float":
                    part.y = part.y + Mth.sin(age * speed + phase) * amp;
                    break;
                case "pulse": {
                    float s = 1.0F + Mth.sin(age * speed + phase) * amp + (action > 0 ? 0.08F : 0.0F);
                    part.xScale = s;
                    part.yScale = s;
                    part.zScale = s;
                    break;
                }
                case "sway": {
                    float v = Mth.sin(age * speed + phase) * amp;
                    int axis = (int)a.f("ax", 0.0F);
                    if (axis == 1) {
                        part.yRot += v;
                    } else if (axis == 2) {
                        part.zRot += v;
                    } else {
                        part.xRot += v;
                    }
                    break;
                }
                case "blink": {
                    // eyelids: shown for three ticks every 'every' ticks, offset per entity
                    int every = Math.max(20, (int)a.f("every", 90.0F));
                    float t = (age + (float)Math.floorMod(System.identityHashCode(e), every)) % (float)every;
                    float s = t < 3.0F ? 1.0F : 0.0F;
                    part.xScale = s;
                    part.yScale = s;
                    part.zScale = s;
                    break;
                }
                case "knee":
                    part.xRot = part.xRot + Math.max(0.0F, Mth.cos(swing * 0.6662F + (a.left ? (float) Math.PI : 0.0F))) * amount * 0.9F
                        + air * 0.9F + (motion == 3 || motion == 7 ? pulse * 0.8F : 0.0F) + (motion == 2 && !a.left ? pulse * 0.5F : 0.0F);
                    break;
                case "elbow":
                    part.xRot = part.xRot - Math.max(0.0F, -Mth.cos(swing * 0.6662F + (a.left ? 0.0F : (float) Math.PI))) * amount * 0.5F
                        - (action > 0 ? 0.25F : 0.0F);
                    break;
                case "jaw":
                    part.xRot = part.xRot + Mth.sin(age * 0.05F) * 0.03F + (action > 0 ? 0.25F : 0.0F) + pulse * 0.45F;
                    break;
                case "chaos":
                    part.y = part.y + Mth.sin(age * 0.07F + phase) * 2.0F;
                    part.yRot = part.yRot + age * 0.01F + (float)form * 0.2F;
                    break;
                case "liquid":
                    part.xScale = 1.0F + Mth.sin(age * 0.12F + phase) * amp;
                    part.zScale = 1.0F + Mth.cos(age * 0.12F + phase) * amp;
                    part.yScale = 1.0F - Mth.sin(age * 0.12F + phase) * amp * 0.6F;
                    break;
                default:
                    break;
            }
        }
    }

    /** Footwork for the attack motions: a lunge for thrusts, a planted stance for swings and smashes, a crouch for slams. */
    private static void leg(ModelPart part, int motion, float pulse, float sign, boolean left) {
        switch (motion) {
            case 2:
                part.xRot = part.xRot + (left ? 0.5F : -0.75F) * pulse;
                break;
            case 1:
            case 5:
            case 9:
            case 12:
                part.zRot = part.zRot + sign * pulse * 0.18F;
                part.xRot = part.xRot + (left ? 0.25F : -0.25F) * pulse;
                break;
            case 3:
                part.zRot = part.zRot + sign * pulse * 0.22F;
                part.xRot = part.xRot - pulse * 0.3F;
                break;
            case 6:
                part.zRot = part.zRot + sign * pulse * 0.35F;
                break;
            case 7:
                part.xRot = part.xRot - pulse * 0.45F;
                part.zRot = part.zRot + sign * pulse * 0.15F;
                break;
            case 10:
                part.xRot = part.xRot + pulse * 0.3F;
                break;
            case 14:
                part.xRot = part.xRot + pulse * 0.25F;
                break;
            case 16:
                part.xRot = part.xRot - (left ? 0.0F : 0.6F) * pulse;
                break;
            default:
                break;
        }
    }

    private static void arm(ModelPart part, int motion, float pulse, float sign, boolean left) {
        switch (motion) {
            case 1:
                part.xRot -= pulse * 1.6F;
                part.yRot = part.yRot + sign * pulse * 1.2F;
                break;
            case 2:
                part.xRot -= pulse * 1.6F;
                part.z -= pulse * 2.0F;
                break;
            case 3:
                part.xRot -= pulse * 2.4F;
                part.yRot = part.yRot + sign * pulse * 0.4F;
                break;
            case 4:
                part.zRot = part.zRot + sign * pulse * 1.4F;
                break;
            case 5:
                part.xRot -= pulse * 1.1F;
                part.yRot = part.yRot - sign * pulse * 0.6F;
                break;
            case 6:
            case 7:
                part.xRot = part.xRot + pulse * 0.8F;
                break;
            case 8:
            case 11:
            case 15:
                part.xRot -= pulse * 1.7F;
                part.zRot = part.zRot + sign * pulse * 0.5F;
                break;
            case 9:
            case 12:
                part.xRot -= pulse * 0.8F;
                part.yRot = part.yRot - sign * pulse * 0.9F;
                break;
            case 13:
                part.xScale = 1.0F + pulse * 0.2F;
                part.zRot = part.zRot + sign * pulse * 0.3F;
                break;
            case 14:
                part.xRot -= pulse * 0.4F;
                break;
            case 16:
                if (!left) {
                    part.xRot -= pulse * 2.0F;
                }
                break;
            default:
                break;
        }
    }

    public void renderGlow(PoseStack p, VertexConsumer v, int overlay) {
        render(this.root, p, v, 15728880, overlay, -1);
        this.renderMeshes(p, v, 15728880, overlay, -1, true);
    }

    @Override
    public void renderToBuffer(PoseStack p, VertexConsumer v, int light, int overlay, float red, float green, float blue, float alpha) {
        int color = channel(alpha) << 24 | channel(red) << 16 | channel(green) << 8 | channel(blue);
        int c = this.tint == -1 ? color : multiply(color, this.tint);
        render(this.root, p, v, light, overlay, c);
        this.renderMeshes(p, v, light, overlay, c, false);
    }

    /** ModelPart.render with a packed ARGB colour: 1.20.1 takes the channels as floats. */
    public static void render(ModelPart part, PoseStack p, VertexConsumer v, int light, int overlay, int color) {
        part.render(p, v, light, overlay, (color >> 16 & 255) / 255.0F, (color >> 8 & 255) / 255.0F, (color & 255) / 255.0F, (color >>> 24) / 255.0F);
    }

    private static int channel(float f) {
        return Math.round(Math.max(0.0F, Math.min(1.0F, f)) * 255.0F);
    }

    private static int multiply(int a, int b) {
        int alpha = ((a >>> 24) * (b >>> 24)) / 255;
        int red = ((a >> 16 & 255) * (b >> 16 & 255)) / 255;
        int green = ((a >> 8 & 255) * (b >> 8 & 255)) / 255;
        int blue = ((a & 255) * (b & 255)) / 255;
        return alpha << 24 | red << 16 | green << 8 | blue;
    }

    private static final class Animated {
        final ModelPart part;
        final String anim;
        final Map<String, Float> p;
        final boolean left;

        Animated(ModelPart part, String anim, Map<String, Float> p, boolean left) {
            this.part = part;
            this.anim = anim;
            this.p = p;
            this.left = left;
        }

        float f(String k, float fallback) {
            Float v = this.p.get(k);
            return v == null ? fallback : v;
        }
    }

    private static final class MeshNode {
        final ModelPart part;
        final float[] verts;
        final int[] quads;
        final int[] glowQuads;
        final List<MeshNode> children = new ArrayList<>();
        boolean used;

        MeshNode(ModelPart part, float[] verts, int[] quads, int[] glowQuads) {
            this.part = part;
            this.verts = verts;
            this.quads = quads;
            this.glowQuads = glowQuads;
        }
    }

    static final class Rig {
        String texture;
        String mesh;
        int[] size;
        float height;
        boolean translucent;
        List<Bone> bones;
    }

    static final class Bone {
        String name;
        String parent;
        float[] at;
        float[] rot;
        String anim;
        Map<String, Float> p;
        List<Cube> cubes;
    }

    static final class Cube {
        int[] uv;
        float[] o;
        float[] s;
    }
}
