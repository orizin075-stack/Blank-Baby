package jp.oror.reborn.client;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
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

/**
 * Data-driven model: bones, cubes and animation tags come from assets/oror_supreme_bosses/rigs.json.
 * Bones form a real hierarchy (hair, horns and halos follow the head; sleeves and weapons follow the arms)
 * and every cube has its own UV box, so textures can carry faces, hair strands and clothing detail.
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
        this.texture = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/" + rig.texture + ".png");
        this.glowTexture = ResourceLocation.fromNamespaceAndPath("oror_supreme_bosses", "textures/entity/" + rig.texture + "_glow.png");
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

        chain(parentOf, "arm_r", this.chainRight);
        chain(parentOf, "arm_l", this.chainLeft);
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
                    }
                    break;
                }
                case "breath":
                    part.xRot = part.xRot + Mth.sin(age * 0.08F) * 0.015F + (action > 0 ? 0.08F : 0.0F);
                    if (motion == 1 || motion == 3 || motion == 5) {
                        part.yRot = part.yRot + pulse * 0.35F;
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
                case "leg_l":
                    part.xRot = part.xRot + Mth.cos(swing * 0.6662F + (a.anim.equals("leg_l") ? (float) Math.PI : 0.0F)) * amount * 0.8F;
                    break;
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
        this.root.render(p, v, 15728880, overlay, -1);
    }

    public void renderToBuffer(PoseStack p, VertexConsumer v, int light, int overlay, int color) {
        this.root.render(p, v, light, overlay, this.tint == -1 ? color : multiply(color, this.tint));
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

    static final class Rig {
        String texture;
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
