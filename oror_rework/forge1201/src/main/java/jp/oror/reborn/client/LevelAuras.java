package jp.oror.reborn.client;

import java.awt.Color;
import java.util.HashMap;
import java.util.Map;
import jp.oror.reborn.RebornConfig;
import jp.oror.reborn.TierSignals;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.TickEvent.ClientTickEvent;
import org.joml.Vector3f;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    value = {Dist.CLIENT}
)
public final class LevelAuras {
    private static final Map<Integer, TierSignals.Rank> GRADES = new HashMap<>();
    private static Object world;

    public static void accept(TierSignals.Rank rank) {
        ClientLevel current = Minecraft.getInstance().level;
        if (current != world) {
            world = current;
            GRADES.clear();
        }

        GRADES.put(rank.entity(), rank);
    }

    @SubscribeEvent
    public static void tick(ClientTickEvent e) {
        if (e.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (mc.level != world) {
            world = mc.level;
            GRADES.clear();
        }

        if (mc.level != null && mc.player != null && (Boolean)RebornConfig.AURAS.get()) {
            int budget = 96;
            long time = mc.level.getGameTime();

            for (Entity entity : mc.level.entitiesForRendering()) {
                if (entity instanceof Mob) {
                    Mob m = (Mob)entity;
                    if (m.isAlive() && !(m.distanceToSqr(mc.player) > 1024.0)) {
                        TierSignals.Rank grade = GRADES.get(m.getId());
                        if (grade != null && grade.rank() >= 2) {
                            int interval = Math.max(2, 14 - grade.rank() * 2);
                            if (Math.floorMod(time + (long)m.getId(), interval) == 0 && budget-- > 0) {
                                double angle = (double)time * 0.12 + (double)m.getId();
                                double radius = (double)m.getBbWidth() * (0.6 + (double)grade.rank() * 0.03);
                                int c = grade.color();
                                if (grade.rank() == 6) {
                                    float hue = (float)(((double)time * 0.01 + (double)m.getId() * 0.13) % 1.0);
                                    c = Color.HSBtoRGB(hue, 0.75F, 1.0F);
                                }

                                Vector3f color = new Vector3f((float)(c >> 16 & 0xFF) / 255.0F, (float)(c >> 8 & 0xFF) / 255.0F, (float)(c & 0xFF) / 255.0F);
                                mc.level
                                    .addParticle(
                                        new DustParticleOptions(color, grade.rank() >= 5 ? 1.2F : 0.65F),
                                        m.getX() + Math.cos(angle) * radius,
                                        m.getY() + 0.15 + (double)(time % 40L) / 40.0 * (double)m.getBbHeight(),
                                        m.getZ() + Math.sin(angle) * radius,
                                        0.0,
                                        0.02,
                                        0.0
                                    );
                            }
                        }
                    }
                }
            }

            if (GRADES.size() > 8192) {
                GRADES.entrySet().removeIf(a -> mc.level.getEntity(a.getKey()) == null);
            }
        }
    }

    private LevelAuras() {
    }
}
