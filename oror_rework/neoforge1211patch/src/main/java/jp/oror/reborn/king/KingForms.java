package jp.oror.reborn.king;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import jp.oror.reborn.royal.RoyalMob;
import jp.oror.reborn.royal.RoyalRegistry;
import jp.oror.reborn.royal.RoyalRole;
import jp.oror.reborn.royal.RoyalSovereign;
import jp.oror.reborn.royal.RoyalThreats;
import jp.oror.reborn.show.TechniqueShow;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * (054) The villager king's forms (the user: he changes his form each time he comes back from death, arms himself more
 * viciously, his name falls apart into garbage with each return, and in the third his true name shows, a name of a god
 * and a devil, and he fights as befits it).
 * <p>
 * His true name is Baal Zebul (バアル＝ゼブル): Baal, the storm god who struck with thunder and the two clubs the smith of
 * the gods made him, Yagrush ("Chaser") and Aymur ("Driver"); turned by those who feared him into Beelzebub, the lord of
 * the flies. His name is that name written in UTF-8 and read as Shift_JIS ("繝舌い繝ｫ＝繧ｼ繝悶Ν"): at first only a
 * corner of it shows under "村人王", then most of it, and at the last the name itself.
 * <ul>
 * <li>First return, the Iron-Blooded (villager_king_1): a shockwave; three imperial guards called; every thirty
 * seconds of a fight two more (six at most).</li>
 * <li>Second return, the Hellfire King (villager_king_2): a nova of fire; two archmages called; every twelve seconds a
 * ring of fire round him; one far off whom he hunts, he leaps to.</li>
 * <li>Third return, Baal Zebul (villager_king_3): eight bolts of lightning round him and a storm over the world; his
 * guns put away for the two clubs, Yagrush and Aymur; every six seconds the thunder on his enemy and those round it,
 * every ten the flies (poison, withering, blindness, two hearts a second for five seconds), and the clubs' leap and
 * smash on one who comes close.</li>
 * </ul>
 * Each is shown by a motion of its own (TechniqueShow "move:king_...", RoyalModel) and by the skin of the form
 * (RoyalRenderer).
 */
@EventBusSubscriber(modid = "oror_supreme_bosses")
public final class KingForms {
    private static final Logger LOG = LoggerFactory.getLogger("OROR King");
    public static final String TRUE_NAME = "バアル＝ゼブル";
    public static final String TRUE_TITLE = "天の王にして蝿の王";
    /** The true name, and the king's own, as UTF-8 read as Shift_JIS. */
    static final String GARBLED_NAME = "繝舌い繝ｫ＝繧ｼ繝悶Ν";
    static final String GARBLED_KING = "譚台ｺｺ邇";
    static final String SUMMONED = "OrorKingSummon";
    /** The flies on whom they are, and until when, by the king who sent them. */
    private static final Map<LivingEntity, long[]> SWARMS = new WeakHashMap<>();
    private static final Map<LivingEntity, RoyalMob> SWARM_KING = new WeakHashMap<>();

    private KingForms() {
    }

    // --------------------------------------------------------------------------------------------------------- names

    /** The name over his head in each form; flickering where it is falling apart. */
    public static Component name(RoyalMob king, int phase, long time) {
        int beat = (int) ((time / 20 + king.getId()) % 4);
        return switch (phase) {
            case 0 -> Component.literal("Lv.6 村人王").withStyle(ChatFormatting.GOLD);
            case 1 -> Component.literal("Lv.6 村人" + (beat == 0 ? "邇" : "王") + "《").withStyle(ChatFormatting.GOLD)
                .append(Component.literal(GARBLED_NAME.substring(0, 5)).withStyle(ChatFormatting.DARK_RED))
                .append(Component.literal("》").withStyle(ChatFormatting.GOLD));
            case 2 -> Component.literal("Lv.6 ").withStyle(ChatFormatting.DARK_RED)
                .append(Component.literal(beat % 2 == 0 ? GARBLED_KING : "村" + GARBLED_KING.substring(1)).withStyle(ChatFormatting.RED))
                .append(Component.literal("《" + GARBLED_NAME.substring(0, 6)).withStyle(ChatFormatting.DARK_RED))
                .append(Component.literal("ゼブ").withStyle(ChatFormatting.DARK_RED, ChatFormatting.OBFUSCATED))
                .append(Component.literal("》").withStyle(ChatFormatting.DARK_RED));
            default -> Component.literal("Lv.6 " + TRUE_NAME).withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD)
                .append(Component.literal("［" + TRUE_TITLE + "］").withStyle(ChatFormatting.LIGHT_PURPLE));
        };
    }

    /** The boss bar's name in each form. */
    public static Component bossName(int phase) {
        MutableComponent c = switch (phase) {
            case 0 -> Component.literal("Lv.6 村人王");
            case 1 -> Component.literal("Lv.6 村人王《" + GARBLED_NAME.substring(0, 5) + "》");
            case 2 -> Component.literal("Lv.6 " + GARBLED_KING + "《" + GARBLED_NAME + "》");
            default -> Component.literal("Lv.6 " + TRUE_NAME + "［" + TRUE_TITLE + "］");
        };
        return c.append(Component.literal("［復活 " + phase + "/3］"));
    }

    // -------------------------------------------------------------------------------------------- coming back

    /** He has come back from death into the given form (RoyalSovereign.onDeath, KingSovereignMixin). */
    public static void reborn(RoyalMob king, int phase) {
        if (!(king.level() instanceof ServerLevel sl)) {
            return;
        }
        CompoundTag d = king.getPersistentData();
        d.putInt("OrorKingForm", phase);
        String[] lines = switch (phase) {
            case 1 -> new String[]{"村人王：……まだだ。王は、斃れぬ。", "村人王：我が名は――" + GARBLED_NAME.substring(0, 5) + "……"};
            case 2 -> new String[]{GARBLED_KING + "：炎ハ、冥府ヨリ来タル。", GARBLED_KING + "：我ガ名ハ、" + GARBLED_NAME + "……"};
            default -> new String[]{"――我が真名を知れ。", TRUE_NAME + "：我は" + TRUE_NAME + "。" + TRUE_TITLE + "なり。",
                TRUE_NAME + "：雷よ、ヤグルシよ、アイムールよ。蝿どもよ。この者らを喰らえ。"};
        };
        for (ServerPlayer p : sl.players()) {
            if (p.distanceToSqr(king) < 256 * 256) {
                for (String line : lines) {
                    p.sendSystemMessage(Component.literal(line).withStyle(phase >= 3 ? ChatFormatting.DARK_PURPLE : ChatFormatting.DARK_RED));
                }
            }
        }
        TechniqueShow.send(king, "move:king_revive", 0, 10, 40, -1);
        switch (phase) {
            case 1 -> {
                burst(king, sl, 10.0, 20F, 1.6, false);
                sl.sendParticles(ParticleTypes.EXPLOSION, king.getX(), king.getY() + 1, king.getZ(), 6, 2, 0.5, 2, 0);
                sl.playSound(null, king.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 3F, 0.7F);
                call(king, sl, RoyalRole.IMPERIAL, 3);
            }
            case 2 -> {
                burst(king, sl, 12.0, 30F, 1.2, true);
                sl.sendParticles(ParticleTypes.FLAME, king.getX(), king.getY() + 1, king.getZ(), 300, 6, 1, 6, 0.08);
                sl.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, king.getX(), king.getY() + 1, king.getZ(), 120, 4, 1, 4, 0.05);
                sl.playSound(null, king.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 3F, 0.5F);
                call(king, sl, RoyalRole.ARCHMAGE, 2);
            }
            default -> {
                for (int i = 0; i < 8; i++) {
                    double a = i * Math.PI / 4;
                    bolt(sl, king.position().add(Math.cos(a) * 7, 0, Math.sin(a) * 7));
                }
                for (LivingEntity e : foes(king, sl, 24.0)) {
                    e.hurt(king.damageSources().indirectMagic(king, king), 24F);
                    swarm(king, e, sl.getGameTime() + 100);
                }
                sl.setWeatherParameters(0, 6000, true, true);
                arm(king, 3);
            }
        }
        LOG.info("KING-FORM {\"phase\":{},\"name\":\"{}\"}", phase, bossName(phase).getString());
    }

    /** His hands in the form: the third puts the guns away for the two clubs of Baal. */
    public static void arm(RoyalMob king, int phase) {
        if (phase < 3) {
            return;
        }
        var ench = king.registryAccess().registryOrThrow(Registries.ENCHANTMENT);
        ItemStack yagrush = new ItemStack(Items.MACE);
        yagrush.set(DataComponents.CUSTOM_NAME, Component.literal("雷霆棍ヤグルシ（追い払う者）").withStyle(ChatFormatting.LIGHT_PURPLE));
        yagrush.enchant(ench.getHolderOrThrow(Enchantments.DENSITY), 5);
        yagrush.enchant(ench.getHolderOrThrow(Enchantments.BREACH), 4);
        yagrush.set(DataComponents.RARITY, Rarity.EPIC);
        ItemStack aymur = new ItemStack(Items.MACE);
        aymur.set(DataComponents.CUSTOM_NAME, Component.literal("雷霆棍アイムール（駆り立てる者）").withStyle(ChatFormatting.LIGHT_PURPLE));
        aymur.enchant(ench.getHolderOrThrow(Enchantments.WIND_BURST), 3);
        aymur.enchant(ench.getHolderOrThrow(Enchantments.DENSITY), 5);
        aymur.set(DataComponents.RARITY, Rarity.EPIC);
        king.setItemSlot(EquipmentSlot.MAINHAND, yagrush);
        king.setItemSlot(EquipmentSlot.OFFHAND, aymur);
        king.setDropChance(EquipmentSlot.MAINHAND, 0F);
        king.setDropChance(EquipmentSlot.OFFHAND, 0F);
    }

    // ------------------------------------------------------------------------------------------------ every tick

    /** RoyalSovereign.tick's end (KingSovereignMixin): his name, and his deeds in the form. */
    public static void tick(RoyalMob king, int phase) {
        if (!(king.level() instanceof ServerLevel sl)) {
            return;
        }
        long now = sl.getGameTime();
        if (king.tickCount % 20 == 0) {
            king.setCustomName(name(king, phase, now));
            king.setCustomNameVisible(true);
            KingCourt.bossBars(king, sl);
            if (phase >= 3 && !(king.getMainHandItem().is(Items.MACE))) {
                arm(king, phase);
            }
        }
        KingCourt.hunt(king, sl, phase);
        LivingEntity t = king.getTarget();
        if (t == null || !t.isAlive() || !foe(king, t)) {
            return;
        }
        CompoundTag d = king.getPersistentData();
        double dist = king.distanceTo(t);
        if (phase >= 1 && ready(d, "OrorKingRally", now, 600)) {
            long called = sl.getEntitiesOfClass(RoyalMob.class, king.getBoundingBox().inflate(48),
                m -> m.isAlive() && m.getPersistentData().getBoolean(SUMMONED)).size();
            if (called < 6) {
                TechniqueShow.send(king, "move:king_rally", 0, 6, 24, t.getId());
                call(king, sl, RoyalRole.IMPERIAL, 2);
            }
        }
        if (phase >= 2 && ready(d, "OrorKingFlame", now, 240)) {
            TechniqueShow.send(king, "move:king_flame", 0, 10, 30, t.getId());
            burst(king, sl, 8.0, 16F, 0.8, true);
            for (int i = 0; i < 48; i++) {
                double a = i * Math.PI / 24;
                sl.sendParticles(ParticleTypes.FLAME, king.getX() + Math.cos(a) * 8, king.getY() + 0.2, king.getZ() + Math.sin(a) * 8, 3, 0.1, 0.4, 0.1, 0.01);
            }
            sl.playSound(null, king.blockPosition(), SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 2F, 0.6F);
        }
        if (phase >= 2 && dist > 16 && dist < 128 && ready(d, "OrorKingBlink", now, 200)) {
            Vec3 behind = t.position().subtract(t.getLookAngle().multiply(3, 0, 3));
            BlockPos at = sl.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.containing(behind));
            if (Math.abs(at.getY() - t.getY()) < 6) {
                TechniqueShow.send(king, "move:king_blink", 0, 4, 12, t.getId());
                sl.sendParticles(ParticleTypes.PORTAL, king.getX(), king.getY() + 1, king.getZ(), 60, 0.5, 1, 0.5, 0.5);
                king.teleportTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5);
                sl.sendParticles(ParticleTypes.REVERSE_PORTAL, king.getX(), king.getY() + 1, king.getZ(), 60, 0.5, 1, 0.5, 0.2);
                sl.playSound(null, king.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 2F, 0.5F);
            }
        }
        if (phase >= 3) {
            if (ready(d, "OrorKingStorm", now, 120)) {
                TechniqueShow.send(king, "move:king_storm", 0, 12, 36, t.getId());
                List<LivingEntity> struck = new ArrayList<>(List.of(t));
                for (LivingEntity e : foes(king, sl, 24.0)) {
                    if (struck.size() >= 4) {
                        break;
                    }
                    if (e != t) {
                        struck.add(e);
                    }
                }
                for (LivingEntity e : struck) {
                    bolt(sl, e.position());
                    e.hurt(king.damageSources().indirectMagic(king, king), 24F);
                    e.igniteForSeconds(4);
                }
                d.putInt("OrorKingBolts", d.getInt("OrorKingBolts") + struck.size());
            }
            if (ready(d, "OrorKingSwarm", now, 200)) {
                TechniqueShow.send(king, "move:king_swarm", 0, 10, 40, t.getId());
                swarm(king, t, now + 100);
                for (LivingEntity e : foes(king, sl, 6.0).stream().filter(x -> x.distanceTo(t) < 6).toList()) {
                    swarm(king, e, now + 100);
                }
                sl.playSound(null, t.blockPosition(), SoundEvents.BEE_LOOP_AGGRESSIVE, SoundSource.HOSTILE, 3F, 0.6F);
                d.putInt("OrorKingSwarms", d.getInt("OrorKingSwarms") + 1);
            }
            if (dist < 6 && ready(d, "OrorKingSlam", now, 100)) {
                TechniqueShow.send(king, "move:king_slam", 0, 10, 26, t.getId());
                king.setDeltaMovement(t.position().subtract(king.position()).normalize().scale(0.6).add(0, 0.6, 0));
                burst(king, sl, 6.0, 36F, 2.0, false);
                sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, t.getX(), t.getY(), t.getZ(), 1, 0, 0, 0, 0);
                sl.playSound(null, king.blockPosition(), SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.HOSTILE, 3F, 0.6F);
                d.putInt("OrorKingSlams", d.getInt("OrorKingSlams") + 1);
            }
        }
    }

    private static boolean ready(CompoundTag d, String key, long now, int every) {
        if (now < d.getLong(key)) {
            return false;
        }
        d.putLong(key, now + every);
        return true;
    }

    // ---------------------------------------------------------------------------------------------------- deeds

    /** One the king fights: a player who has turned on the kingdom, a monster (never his own, a villager, a creative player). */
    public static boolean foe(RoyalMob king, LivingEntity e) {
        if (e == king || !e.isAlive() || king.isAlliedTo(e)) {
            return false;
        }
        if (e instanceof Player p) {
            return !p.isCreative() && !p.isSpectator() && RoyalThreats.hostilePlayer(p);
        }
        return RoyalSovereign.hostile(e) || e.getPersistentData().getBoolean(RebelPact.ALLY);
    }

    static List<LivingEntity> foes(RoyalMob king, ServerLevel sl, double r) {
        return sl.getEntitiesOfClass(LivingEntity.class, king.getBoundingBox().inflate(r), e -> foe(king, e) && e.distanceTo(king) <= r);
    }

    /** A blow on all his foes round him: damage, a throw away from him, and fire if it is hellfire. */
    static void burst(RoyalMob king, ServerLevel sl, double r, float damage, double throwBack, boolean fire) {
        for (LivingEntity e : foes(king, sl, r)) {
            e.hurt(king.damageSources().mobAttack(king), damage);
            Vec3 away = e.position().subtract(king.position()).multiply(1, 0, 1);
            if (away.lengthSqr() > 1.0E-4) {
                away = away.normalize();
                e.knockback(throwBack, -away.x, -away.z);
            }
            if (fire) {
                e.igniteForSeconds(8);
            }
        }
    }

    static void bolt(ServerLevel sl, Vec3 at) {
        LightningBolt b = EntityType.LIGHTNING_BOLT.create(sl);
        if (b != null) {
            b.moveTo(at.x, at.y, at.z);
            b.setVisualOnly(true);
            sl.addFreshEntity(b);
        }
        sl.playSound(null, BlockPos.containing(at), SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 4F, 0.8F);
    }

    /** Calls n of his people of a role to his side, set on his enemy. */
    static void call(RoyalMob king, ServerLevel sl, RoyalRole role, int n) {
        EntityType<RoyalMob> type = RoyalRegistry.TYPES.get(role);
        if (type == null) {
            return;
        }
        for (int i = 0; i < n; i++) {
            RoyalMob m = type.create(sl);
            if (m == null) {
                continue;
            }
            double a = sl.random.nextDouble() * Math.PI * 2;
            BlockPos at = sl.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                BlockPos.containing(king.getX() + Math.cos(a) * 4, king.getY(), king.getZ() + Math.sin(a) * 4));
            if (Math.abs(at.getY() - king.getY()) > 6) {
                at = king.blockPosition();
            }
            m.moveTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, king.getYRot(), 0F);
            m.setPersistenceRequired();
            m.getPersistentData().putBoolean(SUMMONED, true);
            sl.addFreshEntity(m);
            if (king.getTarget() != null) {
                m.setTarget(king.getTarget());
            }
            sl.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, m.getX(), m.getY() + 1, m.getZ(), 20, 0.4, 0.8, 0.4, 0.2);
        }
        CompoundTag d = king.getPersistentData();
        d.putInt("OrorKingCalled", d.getInt("OrorKingCalled") + n);
    }

    static void swarm(RoyalMob king, LivingEntity e, long until) {
        SWARMS.put(e, new long[]{until});
        SWARM_KING.put(e, king);
    }

    /** The flies at work: two hearts a second, poison, withering and blindness, a black cloud round the one they are on. */
    @SubscribeEvent
    public static void flies(ServerTickEvent.Post e) {
        if (SWARMS.isEmpty()) {
            return;
        }
        for (Map.Entry<LivingEntity, long[]> en : List.copyOf(SWARMS.entrySet())) {
            LivingEntity t = en.getKey();
            if (!(t.level() instanceof ServerLevel sl) || !t.isAlive() || sl.getGameTime() > en.getValue()[0]) {
                SWARMS.remove(t);
                SWARM_KING.remove(t);
                continue;
            }
            sl.sendParticles(ParticleTypes.ASH, t.getX(), t.getY() + 1, t.getZ(), 12, 0.8, 0.9, 0.8, 0.02);
            sl.sendParticles(ParticleTypes.SQUID_INK, t.getX(), t.getY() + 1.2, t.getZ(), 2, 0.6, 0.6, 0.6, 0.01);
            if (sl.getGameTime() % 20 == 0) {
                RoyalMob king = SWARM_KING.get(t);
                t.hurt(king != null ? king.damageSources().indirectMagic(king, king) : sl.damageSources().magic(), 4F);
                t.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 1));
                t.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 0));
                t.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 30, 0));
                t.addEffect(new MobEffectInstance(MobEffects.HUNGER, 60, 1));
            }
        }
    }

    /** Whether flies are on this one now (the CI's check). */
    public static boolean swarmed(LivingEntity e) {
        return SWARMS.containsKey(e);
    }
}
