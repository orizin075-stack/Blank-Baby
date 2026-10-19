package jp.oror.reborn;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.SimpleCommandExceptionType;
import com.mojang.brigadier.tree.LiteralCommandNode;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.RegisterCommandsEvent;

public final class RebornCommands {
    public static void register(RegisterCommandsEvent e) {
        LiteralArgumentBuilder<CommandSourceStack> r = Commands.literal("oror");
        r.then(Commands.literal("list").executes(c -> {
            ((CommandSourceStack)c.getSource()).sendSuccess(() -> Component.literal(String.join(", ", CharacterSpec.ALL.keySet())), false);
            return CharacterSpec.ALL.size();
        }));
        r.then(
            ((LiteralArgumentBuilder)Commands.literal("spawn").requires(s -> s.hasPermission(2)))
                .then(
                    Commands.argument("character", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(CharacterSpec.ALL.keySet(), b))
                        .executes(
                            c -> {
                                spawn(
                                    (CommandSourceStack)c.getSource(),
                                    StringArgumentType.getString(c, "character"),
                                    ((CommandSourceStack)c.getSource()).getPosition().add(3.0, 0.0, 0.0),
                                    false
                                );
                                return 1;
                            }
                        )
                )
        );
        r.then(
            ((LiteralArgumentBuilder)Commands.literal("battle").requires(s -> s.hasPermission(2)))
                .then(
                    Commands.argument("first", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(CharacterSpec.ALL.keySet(), b))
                        .then(
                            Commands.argument("second", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(CharacterSpec.ALL.keySet(), b))
                                .executes(c -> {
                                    String a = StringArgumentType.getString(c, "first");
                                    String d = StringArgumentType.getString(c, "second");
                                    check(a);
                                    check(d);
                                    CommandSourceStack s = (CommandSourceStack)c.getSource();
                                    SupremeEntity b1 = spawn(s, a, s.getPosition().add(-6.0, 0.0, 0.0), true);

                                    SupremeEntity b2;
                                    try {
                                        b2 = spawn(s, d, s.getPosition().add(6.0, 0.0, 0.0), true);
                                    } catch (CommandSyntaxException var7) {
                                        b1.discard();
                                        throw var7;
                                    }

                                    b1.setTarget(b2);
                                    b2.setTarget(b1);
                                    return 2;
                                })
                        )
                )
        );
        r.then(
            ((LiteralArgumentBuilder)Commands.literal("clear").requires(s -> s.hasPermission(2)))
                .executes(
                    c -> {
                        int n = 0;

                        for (Entity v : ((CommandSourceStack)c.getSource())
                            .getLevel()
                            .getEntitiesOfClass(
                                Entity.class,
                                new AABB(((CommandSourceStack)c.getSource()).getPosition(), ((CommandSourceStack)c.getSource()).getPosition()).inflate(64.0),
                                x -> x instanceof SupremeEntity || x instanceof FamiliarEntity
                            )) {
                            v.discard();
                            n++;
                        }

                        return n;
                    }
                )
        );
        r.then(
            Commands.literal("info")
                .then(
                    Commands.argument("character", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(CharacterSpec.ALL.keySet(), b))
                        .executes(
                            c -> {
                                String id = StringArgumentType.getString(c, "character");
                                check(id);
                                CharacterSpec s = CharacterSpec.ALL.get(id);
                                ((CommandSourceStack)c.getSource())
                                    .sendSuccess(
                                        () -> Component.literal(
                                                s.name
                                                    + "："
                                                    + s.ability
                                                    + " HP="
                                                    + (RebornConfig.LORE.get() && s.loreHealth > 0.0F ? s.loreHealth : s.health)
                                                    + " MP="
                                                    + (RebornConfig.LORE.get() && s.loreMana > 0.0F ? s.loreMana : s.mana)
                                                    + " 遭遇="
                                                    + (EncounterRules.dungeon(id) ? "ダンジョン" : (id.equals("sweet_pact") ? "特殊条件" : "放浪"))
                                            ),
                                        false
                                    );
                                return 1;
                            }
                        )
                )
        );
        r.then(
            ((LiteralArgumentBuilder)((LiteralArgumentBuilder)Commands.literal("mode").requires(s -> s.hasPermission(2)))
                    .then(Commands.literal("lore").executes(c -> {
                        RebornConfig.LORE.set(true);
                        ((CommandSourceStack)c.getSource()).sendSuccess(() -> Component.literal("設定優先モード ON"), true);
                        return 1;
                    })))
                .then(Commands.literal("balanced").executes(c -> {
                    RebornConfig.LORE.set(false);
                    return 1;
                }))
        );
        r.then(
            Commands.literal("encounters")
                .executes(
                    c -> {
                        ((CommandSourceStack)c.getSource())
                            .sendSuccess(() -> Component.literal("放浪：" + String.join(", ", EncounterRules.WANDERERS) + "。甘契の未怪：HP35%以下。他26体：ダンジョン。"), false);
                        return 1;
                    }
                )
        );
        MindCommands.add(r);
        LiteralCommandNode<CommandSourceStack> node = e.getDispatcher().register(r);
        e.getDispatcher().register((LiteralArgumentBuilder)Commands.literal("ororboss").redirect(node));
    }

    private static void check(String id) throws CommandSyntaxException {
        if (!CharacterSpec.ALL.containsKey(id)) {
            throw new SimpleCommandExceptionType(Component.literal("未登録：" + id)).create();
        }
    }

    private static SupremeEntity spawn(CommandSourceStack s, String id, Vec3 p, boolean arena) throws CommandSyntaxException {
        check(id);
        ServerLevel l = s.getLevel();
        SupremeEntity b = (SupremeEntity)((EntityType)OrorReborn.TYPES.get(id).get()).create(l);
        if (b == null) {
            throw new SimpleCommandExceptionType(Component.literal("生成失敗")).create();
        } else {
            b.moveTo(p.x, p.y, p.z, 0.0F, 0.0F);
            if (l.hasChunkAt(b.blockPosition()) && l.getWorldBorder().isWithinBounds(b.blockPosition()) && l.noCollision(b)) {
                b.arena = arena;
                l.addFreshEntity(b);
                return b;
            } else {
                throw new SimpleCommandExceptionType(Component.literal("広い場所で召喚してください。")).create();
            }
        }
    }
}
