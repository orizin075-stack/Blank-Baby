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
 */
@EventBusSubscriber(modid = "oror_supreme_bosses", value = Dist.CLIENT)
public final class StaminaBars {
    private static final int LIGHT = 0xF000F0;
    private static ClientLevel lastLevel;

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
            lastLevel = l;
        }
        if (l == null || MobStamina.SEEN.isEmpty() || mc.options.hideGui) {
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
        for (Iterator<Map.Entry<Integer, MobStamina.Seen>> it = MobStamina.SEEN.entrySet().iterator(); it.hasNext(); ) {
            Map.Entry<Integer, MobStamina.Seen> en = it.next();
            MobStamina.Seen s = en.getValue();
            Entity ent = l.getEntity(en.getKey());
            if (ent == null || !ent.isAlive() || now - s.at() > 1200) {
                it.remove();
                continue;
            }
            if (s.percent() >= 100 && !s.winded()) {
                if (now - s.at() > 40) {
                    it.remove();
                }
                continue;
            }
            if (ent.isInvisible() || ent.distanceToSqr(cp) > 32 * 32) {
                continue;
            }
            Vec3 at = ent.getPosition(partial).add(0, ent.getBbHeight() + 0.4 + (ent.shouldShowName() ? 0.35 : 0), 0).subtract(cp);
            float hw = 0.42F, hh = 0.04F;
            float frac = Mth.clamp(s.percent() / 100F, 0F, 1F);
            int argb = s.winded() ? ((now / 4) % 2 == 0 ? 0xFFE84040 : 0xFF8A2020) : frac < 0.34F ? 0xFFE8962E : 0xFFF2D24A;
            quad(vc, m, at, left, up, -hw - 0.025F, hw + 0.025F, -hh - 0.025F, hh + 0.025F, 0xB0101010);
            Vec3 front = at.subtract(look.x() * 0.01, look.y() * 0.01, look.z() * 0.01);
            if (frac > 0.005F) {
                quad(vc, m, front, left, up, -hw, -hw + 2 * hw * frac, -hh, hh, argb);
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
