package jp.oror.reborn.client;

import jp.oror.reborn.CharacterRelics;
import jp.oror.reborn.SupremeEntity;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.gui.screens.DisconnectedScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.ServerData.Type;
import net.minecraft.client.multiplayer.resolver.ServerAddress;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod.EventBusSubscriber;
import net.minecraftforge.event.TickEvent.ClientTickEvent;
import org.lwjgl.opengl.GL11;

@EventBusSubscriber(
    modid = "oror_supreme_bosses",
    value = {Dist.CLIENT}
)
public final class NetworkClientSmoke {
    private static boolean connected;
    private static boolean humanoid;
    private static boolean tree;
    private static int ticks;
    private static int waiting;

    @SubscribeEvent
    public static void tick(ClientTickEvent event) {
        if (event.phase != net.minecraftforge.event.TickEvent.Phase.END) {
            return;
        }
        String address = System.getProperty("oror.networkConnect", "");
        if (!address.isEmpty()) {
            Minecraft mc = Minecraft.getInstance();
            mc.options.pauseOnLostFocus = false;
            SmokeScreens.acknowledge(mc);
            if (!connected && mc.screen instanceof TitleScreen) {
                connected = true;
                ConnectScreen.startConnecting(
                    mc.screen, mc, ServerAddress.parseString(address), new ServerData("OROR local validation", address, Type.OTHER), false, null
                );
            }

            if (mc.screen instanceof DisconnectedScreen) {
                throw new IllegalStateException("Production network client disconnected");
            } else if (mc.level == null || mc.player == null) {
                if (++waiting > 3600) {
                    throw new IllegalStateException("Network connection timed out");
                }
            } else if (mc.getSingleplayerServer() != null) {
                throw new IllegalStateException("Expected an actual remote server connection");
            } else {
                int actors = 0;
                int operators = 0;

                for (Entity entity : mc.level.entitiesForRendering()) {
                    if (entity instanceof SupremeEntity) {
                        SupremeEntity actor = (SupremeEntity)entity;
                        actors++;
                        if (actor.operatorLevel() == 4) {
                            operators++;
                        }

                        if (actor.spec.id.equals("yggdrasil")) {
                            if (actor.form() == 1) {
                                humanoid = true;
                            } else if (humanoid) {
                                tree = true;
                            }
                        }
                    }
                }

                if (actors == 41 && operators == 7) {
                    if (++ticks == 60) {
                        mc.gameMode.useItem(mc.player, InteractionHand.MAIN_HAND);
                        System.out.println("[OROR_NETWORK_CLIENT] USE_RELIC user=" + mc.player.getGameProfile().getName());
                    }

                    if (ticks == 80) {
                        String command = mc.player.getGameProfile().getName().endsWith("1") ? "oror research kokuhaku 弓の間合いを調べて" : "oror talk riha 空手を教えて";
                        mc.getConnection().sendCommand(command);
                        System.out.println("[OROR_NETWORK_CLIENT] TALK_SENT user=" + mc.player.getGameProfile().getName());
                    }

                    if (ticks == 120) {
                        mc.getConnection().sendCommand(mc.player.getGameProfile().getName().endsWith("1") ? "oror follow kokuhaku" : "oror follow riha");
                    }

                    if (ticks % 100 == 0) {
                        System.out
                            .println(
                                "[OROR_NETWORK_CLIENT] user="
                                    + mc.player.getGameProfile().getName()
                                    + " actors="
                                    + actors
                                    + " operators="
                                    + operators
                                    + " remote=true"
                            );
                    }

                    if (ticks == 880) {
                        Screenshot.grab(
                            mc.gameDirectory,
                            mc.getMainRenderTarget(),
                            message -> System.out.println("[OROR_NETWORK_CLIENT] SCREENSHOT " + message.getString())
                        );
                    }

                    if (ticks >= 1000) {
                        if (!humanoid || !tree) {
                            throw new IllegalStateException("Remote form changes did not synchronize");
                        }

                        int ranks = 0;

                        for (Entity entityx : mc.level.entitiesForRendering()) {
                            if (entityx instanceof Villager) {
                                Villager v = (Villager)entityx;
                                if (v.hasCustomName() && v.getCustomName().getString().startsWith("OROR_RANK_")) {
                                    int rank = Integer.parseInt(v.getCustomName().getString().substring(10));
                                    Item expected = rank == 6
                                        ? (Item)CharacterRelics.ITEMS.get("kokuhaku_legend").get()
                                        : (rank >= 4 ? Items.NETHERITE_SWORD : (rank >= 2 ? Items.DIAMOND_SWORD : Items.IRON_SWORD));
                                    if (!v.getMainHandItem().is(expected) || rank >= 3 && !v.getMainHandItem().isEnchanted()) {
                                        throw new IllegalStateException("Rank equipment did not synchronize " + rank);
                                    }

                                    ranks++;
                                }
                            }
                        }

                        if (ranks != 6) {
                            throw new IllegalStateException("Remote rank sample count " + ranks);
                        }

                        System.out
                            .println(
                                "[OROR_NETWORK_CLIENT] PASS user="
                                    + mc.player.getGameProfile().getName()
                                    + " actors="
                                    + actors
                                    + " operators="
                                    + operators
                                    + " ranks="
                                    + ranks
                                    + " formRoundTrip=true gl_error="
                                    + GL11.glGetError()
                            );
                        mc.stop();
                    }
                }
            }
        }
    }
}
