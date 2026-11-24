package jp.oror.reborn.combat.client;

import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.Iterator;
import java.util.Map;
import jp.oror.reborn.combat.MobStamina;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.RenderLevelStageEvent;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * (059h) A mob's stamina, seen (MobStamina): a thin bar over the head of a mob whose stamina is not full, turned to the
 * camera, within 32 blocks; yellow, orange under a third, flashing red while it is winded; gone two seconds after it is
 * full again. Drawn in the world after the entities, so that it is there whoever draws the mob (Epic Fight draws most).
 * <p>
 * (r73, the user: "ナイトフォールクラフトは HPバーとスタミナバー両方出てたでしょ") Its health over it as well, as NightfallCraft
 * shows them, the two together: a red health bar (what a blow has just taken lingering pale a moment before it goes) and
 * the stamina bar under it. Shown over a mob (or another player) in a fight: hurt, not at full health or stamina, struck
 * within the last eight seconds, or under the crosshair; Epic Fight's own health bar over a hurt mob is left off in the
 * pack's config (health_bar_show_option NONE) so that there are not two.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class StaminaBars {
    private static final int LIGHT = 0xF000F0;
    private static ClientLevel lastLevel;
    /** each entity's health as last drawn, and the pale trail of a blow: its health a moment ago and when it was struck */
    private static final Map<Integer, float[]> TRAIL = new java.util.HashMap<>();

    private StaminaBars() {
    }

    @SubscribeEvent
    public static void render(RenderLevelStageEvent e) {
        if (e.getStage() != RenderLevelStageEvent.Stage.AFTER_ENTITIES) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        ClientLevel l = mc.level;
        if (l != lastLevel) {
            MobStamina.SEEN.clear();
            TRAIL.clear();
            lastLevel = l;
        }
        if (l == null || mc.options.hideGui || mc.player == null) {
            return;
        }
        Camera cam = e.getCamera();
        Vec3 cp = cam.getPosition();
        float partial = e.getPartialTick().getGameTimeDeltaPartialTick(false);
        long now = l.getGameTime();
        Vector3f left = cam.getLeftVector(), up = cam.getUpVector(), look = cam.getLookVector();
        MultiBufferSource.BufferSource buffers = mc.renderBuffers().bufferSource();
        VertexConsumer vc = buffers.getBuffer(RenderType.textBackground());
        Matrix4f m = e.getPoseStack().last().pose();
        boolean drew = false;
        Entity aimed = mc.crosshairPickEntity;
        for (Iterator<Map.Entry<Integer, MobStamina.Seen>> it = MobStamina.SEEN.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<Integer, MobStamina.Seen> en = it.next();
            Entity ent = l.getEntity(en.getKey());
            if (ent == null || !ent.isAlive() || now - en.getValue().at() > 1200) {
                it.remove();
            }
        }
        TRAIL.keySet().removeIf(id -> l.getEntity(id) == null);
        for (Entity ent : l.entitiesForRendering()) {
            if (!(ent instanceof LivingEntity le) || !le.isAlive() || le.isInvisible() || ent.distanceToSqr(cp) > 32 * 32
                || ent == mc.player && mc.options.getCameraType().isFirstPerson() || le instanceof net.minecraft.world.entity.decoration.ArmorStand) {
                continue;
            }
            MobStamina.Seen s = MobStamina.SEEN.get(ent.getId());
            float hp = le.getHealth(), max = Math.max(1F, le.getMaxHealth());
            float[] tr = TRAIL.get(ent.getId());
            if (tr == null) {
                tr = new float[]{hp, hp, -1000};
                TRAIL.put(ent.getId(), tr);
            }
            if (hp < tr[0] - 0.01F) {
                // struck: the health before the blow lingers as the pale trail
                tr[1] = Math.max(tr[1], tr[0]);
                tr[2] = now;
            }
            tr[0] = hp;
            if (now - tr[2] > 12) {
                tr[1] = Math.max(hp, tr[1] - max * 0.03F);
            }
            boolean tired = s != null && (s.percent() < 100 || s.winded());
            boolean inFight = le.hurtTime > 0 || hp < max - 0.01F || now - tr[2] < 160 || tired || ent == aimed;
            if (!inFight) {
                continue;
            }
            Vec3 at = ent.getPosition(partial).add(0, ent.getBbHeight() + 0.45 + (ent.shouldShowName() ? 0.35 : 0), 0).subtract(cp);
            float hw = 0.45F;
            // the frame, then the health (red, its trail pale) and under it the stamina
            quad(vc, m, at, left, up, -hw - 0.03F, hw + 0.03F, -0.075F, 0.105F, 0xB0101010);
            Vec3 front = at.subtract(look.x() * 0.01, look.y() * 0.01, look.z() * 0.01);
            Vec3 front2 = at.subtract(look.x() * 0.02, look.y() * 0.02, look.z() * 0.02);
            float hf = Mth.clamp(hp / max, 0F, 1F), tf = Mth.clamp(tr[1] / max, 0F, 1F);
            if (tf > hf + 0.003F) {
                quad(vc, m, front, left, up, -hw + 2 * hw * hf, -hw + 2 * hw * tf, 0.025F, 0.08F, 0xFFF0D8D0);
            }
            if (hf > 0.003F) {
                int hc = hf < 0.25F ? 0xFFE03030 : 0xFFC81E28;
                quad(vc, m, front2, left, up, -hw, -hw + 2 * hw * hf, 0.025F, 0.08F, hc);
                quad(vc, m, front2.subtract(look.x() * 0.005, look.y() * 0.005, look.z() * 0.005), left, up, -hw, -hw + 2 * hw * hf, 0.065F, 0.08F, 0x50FFFFFF);
            }
            float frac = s == null ? 1F : Mth.clamp(s.percent() / 100F, 0F, 1F);
            boolean winded = s != null && s.winded();
            int argb = winded ? ((now / 4) % 2 == 0 ? 0xFFE84040 : 0xFF8A2020) : frac < 0.34F ? 0xFFE8962E : 0xFFF2D24A;
            if (frac > 0.005F) {
                quad(vc, m, front2, left, up, -hw, -hw + 2 * hw * frac, -0.05F, -0.005F, argb);
            }
            drew = true;
        }
        if (drew) {
            buffers.endBatch(RenderType.textBackground());
        }
    }

    /** A rectangle facing the camera about c (relative to the camera): x along the screen's right, y up; both faces. */
    private static void quad(VertexConsumer vc, Matrix4f m, Vec3 c, Vector3f left, Vector3f up, float x0, float x1, float y0, float y1, int argb) {
        int a = argb >>> 24, r = (argb >> 16) & 0xFF, g = (argb >> 8) & 0xFF, b = argb & 0xFF;
        float[][] p = {corner(c, left, up, x0, y0), corner(c, left, up, x0, y1), corner(c, left, up, x1, y1), corner(c, left, up, x1, y0)};
        for (int i = 0; i < 4; i++) {
            vc.addVertex(m, p[i][0], p[i][1], p[i][2]).setColor(r, g, b, a).setLight(LIGHT);
        }
        for (int i = 3; i >= 0; i--) {
            vc.addVertex(m, p[i][0], p[i][1], p[i][2]).setColor(r, g, b, a).setLight(LIGHT);
        }
    }

    private static float[] corner(Vec3 c, Vector3f left, Vector3f up, float x, float y) {
        // the screen's right is the camera's left reversed
        return new float[]{(float) (c.x - left.x() * x + up.x() * y), (float) (c.y - left.y() * x + up.y() * y), (float) (c.z - left.z() * x + up.z() * y)};
    }
}
