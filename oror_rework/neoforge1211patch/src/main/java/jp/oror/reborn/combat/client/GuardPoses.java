package jp.oror.reborn.combat.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import jp.oror.reborn.SupremeEntity;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.common.ItemAbilities;

/**
 * (059e) A guard's moments on every mob, seen (the user: "すべてのモブがパリイを使えるように きちんとモーションを
 * モブのモーションが機能してなかった"). MobGuard told the players its moments since 052, but only OROR's characters and
 * the royals were drawn moving with them (CharacterModel, RoyalModel); a zombie, a vindicator, a villager or a golem
 * parried with nothing but sparks and a clang. Now each mob drawn by Minecraft's own renderers (the ones Epic Fight does
 * not animate; those play Epic Fight's guard animations, MobGuard.Ef) moves with its guard, posed after its model has
 * been set up for the frame (LivingRendererGuardPoseMixin):
 * <ul>
 * <li>its guard raised: the weapon arm brought across the body, blade up (a shield lifted before it), the head tucked;</li>
 * <li>a parry: the weapon swept up and out across the blow, the body turning with it;</li>
 * <li>a block: both arms braced under the blow, the body pushed back a step;</li>
 * <li>its guard broken: the arms flung up and wide, the body arched back;</li>
 * <li>parried: the weapon knocked high, the body thrown back and shaking.</li>
 * </ul>
 * Arms are found by their names wherever the model has them (a humanoid's, an illager's, the armed villagers', an iron
 * golem's; folded arms are raised instead); the body's motion (the turn, the push, the arch) is given to every model,
 * four legs or none.
 */
public final class GuardPoses {
    /** Where the feet are in a model's space (Minecraft draws a model 1.501 blocks down from where it stands, upside down). */
    private static final float FEET = 1.501F;

    private GuardPoses() {
    }

    /** The parts of a model that move with a guard (any may be absent). */
    private record Parts(ModelPart head, ModelPart body, ModelPart right, ModelPart left, ModelPart folded) {
        static Parts of(EntityModel<?> model) {
            if (model instanceof HumanoidModel<?> h) {
                return new Parts(h.head, h.body, h.rightArm, h.leftArm, null);
            }
            if (model instanceof HierarchicalModel<?> h) {
                return new Parts(find(h, "head"), find(h, "body"), find(h, "right_arm"), find(h, "left_arm"), find(h, "arms"));
            }
            return new Parts(null, null, null, null, null);
        }

        private static ModelPart find(HierarchicalModel<?> h, String name) {
            try {
                return h.getAnyDescendantWithName(name).orElse(null);
            } catch (RuntimeException ex) {
                return null;
            }
        }
    }

    /** Called with the model set up for this frame and the pose stack the model is about to be drawn with. */
    public static void apply(EntityModel<?> model, LivingEntity e, float partial, PoseStack pose) {
        if (e instanceof SupremeEntity || e instanceof RoyalMob) {
            return;   // their own rigs pose their guard (CharacterModel, RoyalModel)
        }
        TechniqueShow.Active show = TechniqueShow.REACT.get(e.getId());
        if (show == null) {
            return;
        }
        float time = e.level().getGameTime() - show.start() + partial;
        float length = Math.max(1, show.length());
        if (time < 0 || time > length) {
            return;
        }
        String kind = show.mechanic();
        float w;
        if (kind.equals("GUARD")) {
            // raised in two ticks and a half, held, lowered in the last three
            w = Math.min(Mth.clamp(time / 2.5F, 0F, 1F), Mth.clamp((length - time) / 3F, 0F, 1F));
        } else {
            float u = time / length;
            w = u < 0.12F ? u / 0.12F : u < 0.45F ? 1F : 1F - (u - 0.45F) / 0.55F;
        }
        w = Mth.clamp(w, 0F, 1F);
        w = w * w * (3F - 2F * w);
        if (w <= 0.001F) {
            return;
        }
        try {
            arms(Parts.of(model), e, kind, w, time, show.start());
        } catch (RuntimeException ex) {
            // a model unlike any known: its body still moves
        }
        body(pose, kind, w, time, length, show.start());
    }

    private static boolean shield(ItemStack s) {
        return !s.isEmpty() && s.canPerformAction(ItemAbilities.SHIELD_BLOCK);
    }

    private static void arms(Parts p, LivingEntity e, String kind, float w, float time, long start) {
        boolean rightHanded = e.getMainArm() != HumanoidArm.LEFT;
        // the weapon arm and the other; s is +1 for a right arm and -1 for a left one (inward turns and outward swings mirror)
        ModelPart weapon = rightHanded ? p.right() : p.left(), other = rightHanded ? p.left() : p.right();
        float sw = rightHanded ? 1F : -1F, so = -sw;
        boolean armsShown = weapon != null && other != null && (p.folded() == null || !p.folded().visible || weapon.visible);
        if (!armsShown) {
            // folded arms (a villager's, an illager's at rest): raised before the face, or thrown up
            if (p.folded() != null) {
                float lift = switch (kind) {
                    case "GUARD" -> -0.75F;
                    case "BLOCK" -> -0.95F;
                    case "PARRY" -> -1.15F;
                    case "BREAK" -> -1.5F;
                    default -> -0.55F;
                };
                p.folded().xRot += lift * w;
            }
        } else {
            boolean offShield = shield(e.getOffhandItem()), mainShield = shield(e.getMainHandItem());
            ModelPart shieldArm = mainShield ? weapon : offShield ? other : null;
            float ss = shieldArm == weapon ? sw : so;
            switch (kind) {
                case "GUARD" -> {
                    if (shieldArm != null) {
                        // the shield lifted before the body (a player's block), the weapon ready
                        pose(shieldArm, w, -1.35F, 0.5F * ss, 0F);
                        if (shieldArm != weapon) {
                            pose(weapon, w, -0.55F, -0.15F * sw, 0F);
                        }
                    } else {
                        // the weapon brought across the body, blade up (Minecraft's old sword block), the other hand forward
                        pose(weapon, w, -0.95F, -0.55F * sw, 0F);
                        pose(other, w, -0.4F, 0.2F * so, 0F);
                    }
                }
                case "PARRY" -> {
                    if (shieldArm != null) {
                        // the shield thrown out into the blow
                        pose(shieldArm, w, -1.7F, 0.8F * ss, 0F);
                    } else {
                        // swept up and out across the blow
                        pose(weapon, w, -1.95F, 0.75F * sw, 0.35F * sw);
                        pose(other, w, -0.25F, 0F, 0.35F * so);
                    }
                    if (p.body() != null) {
                        p.body().yRot += 0.3F * sw * w;
                    }
                }
                case "BLOCK" -> {
                    if (shieldArm != null) {
                        pose(shieldArm, w, -1.5F, 0.45F * ss, 0F);
                    } else {
                        // both arms braced under the blow
                        pose(weapon, w, -1.3F, -0.6F * sw, 0F);
                        pose(other, w, -1.15F, -0.5F * so, 0F);
                    }
                }
                case "BREAK" -> {
                    // the arms flung up and wide
                    pose(weapon, w, -2.5F, 0.2F * sw, 0.65F * sw);
                    pose(other, w, -2.3F, 0.2F * so, 0.65F * so);
                }
                case "PARRIED" -> {
                    // the weapon knocked high and back, the other arm out for balance
                    pose(weapon, w, -2.6F, 0.35F * sw, 0.3F * sw);
                    pose(other, w, -0.3F, 0F, 0.7F * so);
                }
                default -> {
                }
            }
        }
        if (p.head() != null) {
            float head = switch (kind) {
                case "GUARD", "BLOCK" -> 0.2F;        // the chin tucked behind the guard
                case "BREAK" -> -0.45F;               // thrown back
                case "PARRIED" -> -0.35F;
                default -> 0F;
            };
            p.head().xRot += head * w;
        }
    }

    private static void pose(ModelPart arm, float w, float x, float y, float z) {
        if (arm == null) {
            return;
        }
        arm.xRot = Mth.lerp(w, arm.xRot, x);
        arm.yRot = Mth.lerp(w, arm.yRot, y);
        arm.zRot = Mth.lerp(w, arm.zRot, z);
    }

    /** The whole body: turned with a parry, pushed back by a block, arched back by a broken guard, thrown back when parried. */
    private static void body(PoseStack pose, String kind, float w, float time, float length, long start) {
        // in the model's space +z is behind the mob and +y is down; a lean back turns the body about its feet
        float side = (start & 1L) == 0L ? 1F : -1F;
        switch (kind) {
            case "PARRY" -> pose.mulPose(Axis.YP.rotation(0.32F * side * w));
            case "BLOCK" -> {
                pose.translate(0F, 0F, 0.12F * w);
                lean(pose, -0.1F * w);
            }
            case "BREAK" -> {
                pose.translate(0F, 0.05F * w, 0.1F * w);
                lean(pose, -0.3F * w);
            }
            case "PARRIED" -> {
                float shake = Mth.sin(time * 2.4F) * 0.09F * (1F - time / length);
                pose.translate(0F, 0F, 0.18F * w);
                lean(pose, -0.24F * w);
                pose.mulPose(Axis.ZP.rotation(shake));
            }
            case "GUARD" -> lean(pose, 0.05F * w);   // set forward a little, into the guard
            default -> {
            }
        }
    }

    private static void lean(PoseStack pose, float angle) {
        pose.translate(0F, FEET, 0F);
        pose.mulPose(Axis.XP.rotation(angle));
        pose.translate(0F, -FEET, 0F);
    }
}
