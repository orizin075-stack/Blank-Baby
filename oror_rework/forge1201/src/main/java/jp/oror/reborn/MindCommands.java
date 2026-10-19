package jp.oror.reborn;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import java.util.Comparator;
import java.util.Set;
import java.util.UUID;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.phys.AABB;

public final class MindCommands {
    public static void add(LiteralArgumentBuilder<CommandSourceStack> root) {
        root.then(
            ((LiteralArgumentBuilder)((LiteralArgumentBuilder)Commands.literal("quest").then(Commands.literal("list").executes(c -> {
                        NightfallFusion.list(((CommandSourceStack)c.getSource()).getPlayerOrException());
                        return 1;
                    })))
                    .then(
                        Commands.literal("accept")
                            .then(
                                Commands.argument("id", StringArgumentType.word())
                                    .executes(
                                        c -> NightfallFusion.accept(
                                                    ((CommandSourceStack)c.getSource()).getPlayerOrException(), StringArgumentType.getString(c, "id")
                                                )
                                                ? 1
                                                : 0
                                    )
                            )
                    ))
                .then(
                    Commands.literal("claim")
                        .then(
                            Commands.argument("id", StringArgumentType.word())
                                .executes(
                                    c -> NightfallFusion.claim(
                                                ((CommandSourceStack)c.getSource()).getPlayerOrException(), StringArgumentType.getString(c, "id")
                                            )
                                            ? 1
                                            : 0
                                )
                        )
                )
        );
        root.then(Commands.literal("temper").executes(c -> {
            ServerPlayer p = ((CommandSourceStack)c.getSource()).getPlayerOrException();
            boolean ok = NightfallFusion.temper(p);
            p.sendSystemMessage(Component.literal(ok ? "淬霊：武器を強化しました。最大5段階。" : "剣と魔力素材が必要です。強化段階が上がるほど必要数が増えます。"));
            return ok ? 1 : 0;
        }));
        root.then(Commands.literal("difficulty").then(Commands.argument("mode", StringArgumentType.word()).suggests((c, b) -> {
            for (String mode : new String[]{"easy", "normal", "hard"}) {
                b.suggest(mode);
            }

            return b.buildFuture();
        }).executes(c -> {
            String mode = StringArgumentType.getString(c, "mode");
            if (!Set.of("easy", "normal", "hard").contains(mode)) {
                return 0;
            } else {
                ServerPlayer p = ((CommandSourceStack)c.getSource()).getPlayerOrException();
                NightfallFusion.data(p).putString("Difficulty", mode);
                p.sendSystemMessage(Component.literal("個人の難易度を " + mode + " に変更しました。"));
                return 1;
            }
        })));
        root.then(((LiteralArgumentBuilder)((LiteralArgumentBuilder)Commands.literal("village").then(Commands.literal("score").executes(c -> {
            ServerPlayer p = ((CommandSourceStack)c.getSource()).getPlayerOrException();
            VillageLedger.Village v = VillageLedger.get(((CommandSourceStack)c.getSource()).getLevel()).nearest(p.blockPosition());
            p.sendSystemMessage(Component.literal(v == null ? "近くに登録された村はありません。" : "村人スコア " + v.score(p.getUUID()) + " / " + v.center.toShortString()));
            return v == null ? 0 : 1;
        }))).then(Commands.literal("supply").then(Commands.argument("mob", StringArgumentType.word()).executes(c -> {
            ServerPlayer p = ((CommandSourceStack)c.getSource()).getPlayerOrException();
            if (find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob")) instanceof Villager v && !p.getMainHandItem().isEmpty()) {
                ItemStack give = p.getMainHandItem().copyWithCount(Math.min(16, p.getMainHandItem().getCount()));
                ItemStack rest = v.getInventory().addItem(give);
                int transferred = give.getCount() - rest.getCount();
                if (transferred <= 0) {
                    return 0;
                }

                if (!p.isCreative()) {
                    p.getMainHandItem().shrink(transferred);
                }

                VillageReputation.change(((CommandSourceStack)c.getSource()).getLevel(), VillageLedger.of(v), p, 2, "物資の提供");
                return transferred;
            }

            return 0;
        })))).then(Commands.literal("share").then(Commands.argument("pos", BlockPosArgument.blockPos()).executes(c -> {
            ServerPlayer p = ((CommandSourceStack)c.getSource()).getPlayerOrException();
            BlockPos at = BlockPosArgument.getLoadedBlockPos(c, "pos");
            VillageLedger db = VillageLedger.get(((CommandSourceStack)c.getSource()).getLevel());
            VillageLedger.Village v = db.nearest(at);
            if (v != null && ((CommandSourceStack)c.getSource()).getLevel().getBlockEntity(at) instanceof ChestBlockEntity) {
                UUID owner = v.property.get(at.asLong());
                if (owner != null && !owner.equals(p.getUUID())) {
                    return 0;
                } else {
                    v.property.remove(at.asLong());
                    v.communal.add(at.asLong());
                    db.setDirty();
                    p.sendSystemMessage(Component.literal("このチェストを村の共有収納にしました。"));
                    return 1;
                }
            } else {
                return 0;
            }
        }))));
        root.then(
            Commands.literal("follow")
                .then(
                    Commands.argument("mob", StringArgumentType.word())
                        .executes(
                            c -> {
                                ServerPlayer player = ((CommandSourceStack)c.getSource()).getPlayerOrException();
                                if (find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob")) instanceof SupremeEntity b
                                    && (b.owner == null || b.owner.equals(player.getUUID()))) {
                                    b.owner = b.owner == null ? player.getUUID() : null;
                                    player.sendSystemMessage(Component.literal(b.spec.name + (b.owner == null ? "：ここで過ごします。" : "：一緒に行こう。")));
                                    return 1;
                                }

                                ((CommandSourceStack)c.getSource()).sendFailure(Component.literal("この相手の同行は切り替えられません。"));
                                return 0;
                            }
                        )
                )
        );
        root.then(
            ((LiteralArgumentBuilder)Commands.literal("level").requires(s -> s.hasPermission(2)))
                .then(Commands.argument("targets", EntityArgument.entities()).then(Commands.argument("rank", IntegerArgumentType.integer(1, 6)).executes(c -> {
                    int count = 0;

                    for (Entity entity : EntityArgument.getEntities(c, "targets")) {
                        if (entity instanceof Mob m) {
                            MobLevels.set(m, IntegerArgumentType.getInteger(c, "rank"));
                            MobLevels.refresh(m);
                            count++;
                        }
                    }

                    return count;
                })))
        );
        root.then(Commands.literal("chat").then(Commands.argument("mob", StringArgumentType.word()).executes(c -> {
            ServerPlayer player = ((CommandSourceStack)c.getSource()).getPlayerOrException();
            Mob m = find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob"));
            if (m == null) {
                return 0;
            } else {
                MobConversation.focus(m, player);
                return 1;
            }
        })));
        root.then(Commands.literal("industry").then(Commands.argument("mob", StringArgumentType.word()).executes(c -> {
            if (find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob")) instanceof Villager v) {
                ((CommandSourceStack)c.getSource()).sendSuccess(() -> Component.literal(VillagerIndustry.status(v)), false);
                return 1;
            } else {
                return 0;
            }
        })));

        for (String action : new String[]{"talk", "research"}) {
            root.then(Commands.literal(action).then(Commands.argument("mob", StringArgumentType.word()).suggests((c, b) -> {
                b.suggest("nearest");
                CharacterSpec.ALL.keySet().forEach(b::suggest);
                return b.buildFuture();
            }).then(Commands.argument("message", StringArgumentType.greedyString()).executes(c -> {
                ServerPlayer player = ((CommandSourceStack)c.getSource()).getPlayerOrException();
                Mob mob = find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob"));
                if (mob == null) {
                    ((CommandSourceStack)c.getSource()).sendFailure(Component.literal("32ブロック以内に対象のモブが見つかりません。"));
                    return 0;
                } else {
                    return MobConversation.request(mob, player, StringArgumentType.getString(c, "message"), action.equals("research")) ? 1 : 0;
                }
            }))));
        }

        root.then(Commands.literal("mind").then(Commands.argument("mob", StringArgumentType.word()).executes(c -> {
            Mob mob = find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob"));
            if (mob == null) {
                return 0;
            } else {
                ((CommandSourceStack)c.getSource()).sendSuccess(() -> Component.literal(MobConversation.name(mob) + " / " + MobMind.description(mob)), false);
                return 1;
            }
        })));
        root.then(
            Commands.literal("tukuyo")
                .then(Commands.argument("mob", StringArgumentType.word()).then(Commands.argument("message", StringArgumentType.greedyString()).executes(c -> {
                    ServerPlayer p = ((CommandSourceStack)c.getSource()).getPlayerOrException();
                    Mob m = find((CommandSourceStack)c.getSource(), StringArgumentType.getString(c, "mob"));
                    return m != null && TukuyoBridge.request(m, p, StringArgumentType.getString(c, "message")) ? 1 : 0;
                })))
        );
        root.then(
            ((LiteralArgumentBuilder)Commands.literal("ai")
                    .then(((LiteralArgumentBuilder)Commands.literal("status").requires(s -> s.hasPermission(2))).executes(c -> {
                        ((CommandSourceStack)c.getSource()).sendSuccess(() -> Component.literal("外部AI：" + MobConversation.status()), false);
                        return 1;
                    })))
                .then(((LiteralArgumentBuilder)Commands.literal("retry").requires(s -> s.hasPermission(2))).executes(c -> {
                    MobConversation.retry();
                    return 1;
                }))
        );
    }

    private static Mob find(CommandSourceStack source, String query) {
        return source.getLevel()
            .getEntitiesOfClass(
                Mob.class,
                new AABB(source.getPosition(), source.getPosition()).inflate(32.0),
                m -> m.isAlive()
                        && (query.equals("nearest") || m.getUUID().toString().equals(query) || m instanceof SupremeEntity b && b.spec.id.equals(query))
            )
            .stream()
            .min(Comparator.comparingDouble(m -> m.position().distanceToSqr(source.getPosition())))
            .orElse(null);
    }
}
