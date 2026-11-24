package jp.oror.reborn.duel;

import com.mojang.brigadier.arguments.StringArgumentType;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.monster.AbstractIllager;
import net.minecraft.world.entity.monster.AbstractSkeleton;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.Pillager;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.living.LivingDeathEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (r72, the user: "決闘から逃げたら世界中のモブが敵対状態になって普段は協力しないモブたちまで協力して殺しにくる上最上位武器が解禁されて
 * リス狩りされる　敵対状態の解除は基本不可能で気が済むまでボコされてください") A player who runs from a Duel Dominion duel (out of its
 * reach, logged out of it, or gone to another world in the middle of it) bears the deserter's mark (逃亡者の烙印):
 * <ul>
 * <li>every mob about the deserter (eighty blocks; villagers, golems, beasts, the kingdom's people, monsters, all of them)
 * turns on it, and they hunt it together: none of them fights another while the deserter is near, and those with no
 * attack of their own run it down and strike it;</li>
 * <li>the highest arms are unlocked for them: those with hands take up netherite swords and armour of the best
 * enchantments, archers bows of Power V and Flame, crossbowmen crossbows of Multishot and Piercing (never dropped),
 * and all of them are quickened and strengthened;</li>
 * <li>its respawn is camped: a hunting party is waiting where it wakes, and more come every minute wherever it is;</li>
 * <li>the mark does not wear off with time and nothing lifts it: the world is done with the deserter only after it has
 * died ten times. (An operator may lift it: /oror deserter &lt;player&gt; clear.)</li>
 * </ul>
 * Who ran is who moved the farthest from where the duel began (a mob knocked or carried off is not the player's flight);
 * a duel that ran out of time is a draw, not a flight. The mark lives in the player's persisted data: death and logging out
 * keep it.
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class Deserters {
    private static final Logger LOG = LoggerFactory.getLogger("OROR Deserters");
    public static final String KEY = "OrorDeserter", HUNTER = "OrorDeserterHunter", ARMED = "OrorDeserterArmed";
    public static final int DEATHS = 10;
    private static final int REACH = 80, PARTY = 8, WAVE = 4, MOST_HUNTERS = 30;

    private record Start(Vec3 a, Vec3 b) {
    }

    private static final Map<String, Start> STARTS = new HashMap<>();
    private static final Map<Mob, Long> STRUCK = new java.util.WeakHashMap<>();
    private static final Map<UUID, Long> CAMP = new HashMap<>();
    public static int marked, hunted, parties;

    private Deserters() {
    }

    private static String key(LivingEntity a, LivingEntity b) {
        return a.getUUID() + "/" + b.getUUID();
    }

    /** (DuelCrowdMixin) where the two stood when their duel began */
    public static void begun(LivingEntity a, LivingEntity b) {
        STARTS.put(key(a, b), new Start(a.position(), b.position()));
    }

    /** (DuelCrowdMixin) the duel is over, for this reason (Duel Dominion's own words): did a player run from it? */
    public static void ended(LivingEntity a, LivingEntity b, String why) {
        Start s = STARTS.remove(key(a, b));
        if (why == null) {
            return;
        }
        boolean far = why.contains("距離超過"), left = why.contains("ログアウト"), gone = why.contains("消失");
        if (!far && !left && !gone) {
            return;
        }
        LivingEntity fled = null;
        if (left) {
            fled = a instanceof ServerPlayer pa && pa.hasDisconnected() ? a : b instanceof ServerPlayer pb && pb.hasDisconnected() ? b : null;
        } else if (gone) {
            // to another world mid-duel (a portal, a warp): the one still alive somewhere else
            fled = a instanceof ServerPlayer pa && pa.isAlive() && b.isAlive() && pa.level() != b.level() ? a
                : b instanceof ServerPlayer pb && pb.isAlive() && a.isAlive() && pb.level() != a.level() ? b : null;
        } else if (s != null) {
            fled = a.position().distanceTo(s.a()) >= b.position().distanceTo(s.b()) ? a : b;
        } else {
            fled = a instanceof ServerPlayer ? a : b instanceof ServerPlayer ? b : null;
        }
        if (fled instanceof ServerPlayer p) {
            mark(p, why);
        }
    }

    private static CompoundTag kept(Player p) {
        return p.getPersistentData().getCompound(Player.PERSISTED_NBT_TAG);
    }

    public static boolean marked(Player p) {
        return kept(p).contains(KEY);
    }

    public static int deathsLeft(Player p) {
        return marked(p) ? DEATHS - kept(p).getCompound(KEY).getInt("deaths") : 0;
    }

    public static void mark(ServerPlayer p, String why) {
        CompoundTag all = kept(p);
        if (all.contains(KEY)) {
            return;
        }
        CompoundTag m = new CompoundTag();
        m.putInt("deaths", 0);
        m.putLong("since", p.serverLevel().getGameTime());
        m.putString("why", why);
        all.put(KEY, m);
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, all);
        marked++;
        LOG.info("DESERTER marked {} ({})", p.getGameProfile().getName(), why);
        if (p.connection != null) {
            p.connection.send(new ClientboundSetTitleTextPacket(Component.literal("逃亡者").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD)));
            p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("世界中が、お前を狩りに来る").withStyle(ChatFormatting.RED)));
            p.sendSystemMessage(Component.literal("【逃亡者の烙印】決闘から逃げた。世界中のモブが手を組み、最上位の武器を手にお前を狩る。"
                + "気が済むまで（" + DEATHS + "回死ぬまで）終わらない。").withStyle(ChatFormatting.DARK_RED));
            p.serverLevel().playSound(null, p.blockPosition(), SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 0.8F, 0.7F);
        }
    }

    public static void clear(ServerPlayer p, boolean satisfied) {
        CompoundTag all = kept(p);
        if (!all.contains(KEY)) {
            return;
        }
        all.remove(KEY);
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, all);
        LOG.info("DESERTER cleared {} ({})", p.getGameProfile().getName(), satisfied ? "the world is satisfied" : "an operator");
        p.sendSystemMessage(Component.literal(satisfied ? "……世界は気が済んだようだ。逃亡者の烙印が消えた。" : "逃亡者の烙印が取り除かれた。")
            .withStyle(ChatFormatting.GRAY));
        // the hunters go; the mobs of the world return to their ways
        ServerLevel level = p.serverLevel();
        for (Mob m : level.getEntitiesOfClass(Mob.class, p.getBoundingBox().inflate(REACH, 48, REACH), x -> x.isAlive())) {
            if (m.getTags().contains(HUNTER)) {
                level.sendParticles(ParticleTypes.POOF, m.getX(), m.getY() + 1, m.getZ(), 8, 0.3, 0.5, 0.3, 0.02);
                m.discard();
            } else if (m.getTarget() == p && !(m instanceof Monster)) {
                m.setTarget(null);
            }
        }
    }

    // ------------------------------------------------------------------------------------------------- the hunt

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post e) {
        int now = e.getServer().getTickCount();
        if (now % 10 != 0) {
            return;
        }
        for (ServerPlayer p : List.copyOf(e.getServer().getPlayerList().getPlayers())) {
            if (!marked(p) || !p.isAlive() || p.isCreative() || p.isSpectator()) {
                continue;
            }
            try {
                hunt(p, now);
            } catch (RuntimeException ex) {
                LOG.warn("DESERTER hunt failed: {}", ex.toString());
            }
        }
    }

    static void hunt(ServerPlayer p, int now) {
        ServerLevel level = p.serverLevel();
        long time = level.getGameTime();
        List<Mob> all = level.getEntitiesOfClass(Mob.class, p.getBoundingBox().inflate(REACH, 48, REACH),
            m -> m.isAlive() && !m.isNoAi() && !(m.getControllingPassenger() instanceof Player));
        int hunters = 0;
        for (Mob m : all) {
            hunted++;
            if (m.getTags().contains(HUNTER)) {
                hunters++;
            }
            // together: every one of them on the deserter, none on another
            if (m.getTarget() != p) {
                m.setTarget(p);
            }
            if (m.getBrain().checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
                m.getBrain().setMemory(MemoryModuleType.ATTACK_TARGET, p);
            }
            if (now % 40 == 0) {
                m.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 60, 0, false, false));
                m.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 60, 1, false, false));
                m.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 60, 0, false, false));
            }
            arm(level, m);
            // those with no attack of their own (beasts, villagers, golems' kin): run it down and strike
            boolean ownAttack = (m instanceof Monster || m instanceof IronGolem || m instanceof AbstractPiglin || m instanceof net.minecraft.world.entity.NeutralMob)
                && !(m instanceof AbstractVillager) && m.getAttribute(Attributes.ATTACK_DAMAGE) != null;
            if (!ownAttack && m instanceof PathfinderMob pm) {
                if (now % 20 == 0) {
                    pm.getNavigation().moveTo(p, 1.35);
                }
                double reach = 1.6 + m.getBbWidth() / 2;
                Long last = STRUCK.get(m);
                if (m.distanceTo(p) < reach && (last == null || time - last >= 20)) {
                    STRUCK.put(m, time);
                    m.swing(net.minecraft.world.InteractionHand.MAIN_HAND, true);
                    float dmg = m.getAttribute(Attributes.ATTACK_DAMAGE) != null ? (float) m.getAttributeValue(Attributes.ATTACK_DAMAGE)
                        : Math.min(8F, 2.5F + m.getBbHeight() * 1.5F);
                    if (!m.getMainHandItem().isEmpty()) {
                        dmg += 6F;
                    }
                    p.hurt(level.damageSources().mobAttack(m), dmg);
                }
            }
        }
        // more of them every minute, wherever the deserter is
        if (now % 1200 == 0 && hunters < MOST_HUNTERS) {
            party(p, WAVE, 14, 22);
        }
        // the camp at its waking place
        Long camp = CAMP.get(p.getUUID());
        if (camp != null && time >= camp) {
            CAMP.remove(p.getUUID());
            party(p, PARTY, 5, 9);
        }
    }

    private static final EntityType<?>[] PARTY_KINDS = {EntityType.VINDICATOR, EntityType.PILLAGER, EntityType.ZOMBIE, EntityType.SKELETON, EntityType.HUSK,
        EntityType.WITCH, EntityType.VINDICATOR, EntityType.PILLAGER, EntityType.IRON_GOLEM, EntityType.EVOKER, EntityType.RAVAGER};

    /** n hunters about the player, between near and far blocks off, armed and set on it. */
    public static void party(ServerPlayer p, int n, int near, int far) {
        ServerLevel level = p.serverLevel();
        RandomSource rnd = level.random;
        int made = 0;
        for (int i = 0; i < n * 3 && made < n; i++) {
            EntityType<?> type = PARTY_KINDS[rnd.nextInt(PARTY_KINDS.length - (made == 0 ? 0 : 1))];
            double ang = rnd.nextDouble() * Math.PI * 2, d = near + rnd.nextDouble() * (far - near);
            int x = (int) Math.floor(p.getX() + Math.cos(ang) * d), z = (int) Math.floor(p.getZ() + Math.sin(ang) * d);
            int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
            if (Math.abs(y - p.getY()) > 12) {
                y = (int) Math.floor(p.getY());
            }
            BlockPos at = new BlockPos(x, y, z);
            if (!level.getBlockState(at).isAir() || !level.getBlockState(at.above()).isAir()) {
                continue;
            }
            if (!(type.create(level) instanceof Mob m)) {
                continue;
            }
            m.moveTo(x + 0.5, y, z + 0.5, rnd.nextFloat() * 360F, 0F);
            m.finalizeSpawn(level, level.getCurrentDifficultyAt(at), MobSpawnType.EVENT, null);
            m.addTag(HUNTER);
            m.setTarget(p);
            arm(level, m);
            level.addFreshEntity(m);
            level.sendParticles(ParticleTypes.LARGE_SMOKE, x + 0.5, y + 1, z + 0.5, 10, 0.3, 0.6, 0.3, 0.02);
            made++;
        }
        if (made > 0) {
            parties++;
            level.playSound(null, p.blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 1.2F, 1.0F);
            LOG.info("DESERTER party of {} about {}", made, p.getGameProfile().getName());
        }
    }

    /** The highest arms, once, never dropped: netherite and the best enchantments for those with hands. */
    private static void arm(ServerLevel level, Mob m) {
        if (m.getTags().contains(ARMED)) {
            return;
        }
        m.addTag(ARMED);
        boolean hands = m instanceof AbstractSkeleton || m instanceof AbstractIllager || m instanceof AbstractPiglin || m instanceof AbstractVillager
            || m instanceof net.minecraft.world.entity.monster.Zombie || m instanceof jp.oror.reborn.royal.RoyalMob;
        if (!hands) {
            return;
        }
        ItemStack weapon;
        if (m instanceof AbstractSkeleton) {
            weapon = enchanted(level, new ItemStack(Items.BOW), Enchantments.POWER, 5, Enchantments.FLAME, 1, Enchantments.PUNCH, 2);
        } else if (m instanceof Pillager) {
            weapon = enchanted(level, new ItemStack(Items.CROSSBOW), Enchantments.MULTISHOT, 1, Enchantments.QUICK_CHARGE, 3, Enchantments.PIERCING, 4);
        } else if (m instanceof AbstractIllager) {
            weapon = enchanted(level, new ItemStack(Items.NETHERITE_AXE), Enchantments.SHARPNESS, 5, Enchantments.FIRE_ASPECT, 2, null, 0);
        } else {
            weapon = enchanted(level, new ItemStack(Items.NETHERITE_SWORD), Enchantments.SHARPNESS, 5, Enchantments.FIRE_ASPECT, 2, Enchantments.KNOCKBACK, 2);
        }
        if (!(m instanceof net.minecraft.world.entity.monster.SpellcasterIllager)) {
            // (an evoker or an illusioner casts; it is not handed a blade)
            m.setItemSlot(EquipmentSlot.MAINHAND, weapon);
            m.setDropChance(EquipmentSlot.MAINHAND, 0F);
        }
        EquipmentSlot[] slots = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};
        net.minecraft.world.item.Item[] armour = {Items.NETHERITE_HELMET, Items.NETHERITE_CHESTPLATE, Items.NETHERITE_LEGGINGS, Items.NETHERITE_BOOTS};
        for (int i = 0; i < 4; i++) {
            m.setItemSlot(slots[i], enchanted(level, new ItemStack(armour[i]), Enchantments.PROTECTION, 4, null, 0, null, 0));
            m.setDropChance(slots[i], 0F);
        }
    }

    private static ItemStack enchanted(ServerLevel level, ItemStack s, ResourceKey<Enchantment> a, int la, ResourceKey<Enchantment> b, int lb,
        ResourceKey<Enchantment> c, int lc) {
        var reg = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
        for (Object[] e : new Object[][]{{a, la}, {b, lb}, {c, lc}}) {
            if (e[0] != null) {
                @SuppressWarnings("unchecked")
                ResourceKey<Enchantment> k = (ResourceKey<Enchantment>) e[0];
                Holder<Enchantment> h = reg.getOrThrow(k);
                s.enchant(h, (Integer) e[1]);
            }
        }
        return s;
    }

    // ------------------------------------------------------------------------------------- death, respawn, the end

    @SubscribeEvent
    public static void died(LivingDeathEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p) || !marked(p)) {
            return;
        }
        CompoundTag all = kept(p);
        CompoundTag m = all.getCompound(KEY);
        int deaths = m.getInt("deaths") + 1;
        m.putInt("deaths", deaths);
        all.put(KEY, m);
        p.getPersistentData().put(Player.PERSISTED_NBT_TAG, all);
        LOG.info("DESERTER {} died ({} of {})", p.getGameProfile().getName(), deaths, DEATHS);
        if (deaths >= DEATHS) {
            clear(p, true);
        } else {
            p.sendSystemMessage(Component.literal("【逃亡者】まだ終わらない。（あと" + (DEATHS - deaths) + "回）").withStyle(ChatFormatting.DARK_RED));
        }
    }

    @SubscribeEvent
    public static void respawned(PlayerEvent.PlayerRespawnEvent e) {
        if (e.getEntity() instanceof ServerPlayer p && marked(p) && !e.isEndConquered()) {
            // the camp: a hunting party where it wakes, a second after
            CAMP.put(p.getUUID(), p.serverLevel().getGameTime() + 20);
        }
    }

    @SubscribeEvent
    public static void commands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("oror").then(Commands.literal("deserter").requires(s -> s.hasPermission(2))
            .then(Commands.argument("player", EntityArgument.player())
                .then(Commands.literal("clear").executes(c -> {
                    clear(EntityArgument.getPlayer(c, "player"), false);
                    return 1;
                }))
                .then(Commands.literal("mark").executes(c -> {
                    mark(EntityArgument.getPlayer(c, "player"), "operator");
                    return 1;
                }))
                .then(Commands.literal("party").executes(c -> {
                    party(EntityArgument.getPlayer(c, "player"), PARTY, 5, 9);
                    return 1;
                })))));
    }

    /** For the CI check: a list of the mobs set on the deserter about it now. */
    public static List<Mob> on(ServerPlayer p) {
        List<Mob> out = new ArrayList<>();
        for (Mob m : p.serverLevel().getEntitiesOfClass(Mob.class, p.getBoundingBox().inflate(32), x -> x.getTarget() == p)) {
            out.add(m);
        }
        return out;
    }
}
