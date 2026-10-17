package jp.oror.reborn;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Moves and movement of the 41 characters (v0.17.7). Each character has five named moves (boss_moves.json, written by
 * tools/mc/boss_moves.py) from a library of 24 techniques that play out over several ticks — dashes, leaps, combos,
 * beams that track, homing orbs, meteor showers, expanding novas, vortices — each telegraphed during its wind-up and
 * animated through the rig motions. Between moves the character moves in its own style: duelists dash in and step
 * back, brawlers and juggernauts leap in, casters and gunners keep their distance and blink away, tricksters blink
 * around their target, flyers swoop. State lives in the entity's persistent data so it survives a reload.
 */
public final class BossMoves {
    private record Spec(String style, List<String> moves) {
    }

    /** windup and total ticks, rig motion, preferred distance band. */
    private record Move(int windup, int length, int motion, double min, double max) {
    }

    private static final Map<String, Spec> SETS = new HashMap<>();
    private static final Map<String, Move> MOVES = new HashMap<>();

    static {
        MOVES.put("dash_slash", new Move(10, 14, 2, 3.0, 16.0));
        MOVES.put("blink_strike", new Move(8, 14, 1, 0.0, 20.0));
        MOVES.put("combo_rush", new Move(6, 30, 1, 0.0, 8.0));
        MOVES.put("spin_slash", new Move(8, 32, 4, 0.0, 7.0));
        MOVES.put("blade_wave", new Move(10, 14, 1, 4.0, 20.0));
        MOVES.put("leap_slam", new Move(8, 40, 6, 4.0, 18.0));
        MOVES.put("uppercut", new Move(8, 26, 16, 0.0, 5.0));
        MOVES.put("ground_spikes", new Move(10, 36, 7, 3.0, 18.0));
        MOVES.put("nova", new Move(12, 34, 13, 0.0, 10.0));
        MOVES.put("vortex", new Move(10, 44, 8, 3.0, 16.0));
        MOVES.put("meteor", new Move(12, 48, 11, 4.0, 24.0));
        MOVES.put("beam", new Move(14, 46, 15, 4.0, 24.0));
        MOVES.put("homing_orbs", new Move(10, 70, 8, 4.0, 24.0));
        MOVES.put("arrow_rain", new Move(10, 44, 16, 4.0, 24.0));
        MOVES.put("bolt_barrage", new Move(6, 28, 8, 4.0, 24.0));
        MOVES.put("bullet_storm", new Move(8, 40, 14, 3.0, 24.0));
        MOVES.put("shell_barrage", new Move(10, 34, 2, 5.0, 28.0));
        MOVES.put("barrier", new Move(6, 24, 13, 0.0, 30.0));
        MOVES.put("chain_pull", new Move(8, 24, 5, 4.0, 14.0));
        MOVES.put("reap", new Move(8, 30, 4, 0.0, 6.0));
        MOVES.put("ricochet", new Move(8, 20, 1, 3.0, 14.0));
        MOVES.put("afterimage", new Move(6, 36, 5, 0.0, 14.0));
        MOVES.put("charge", new Move(10, 30, 2, 5.0, 20.0));
        MOVES.put("breath", new Move(12, 44, 10, 3.0, 14.0));
        try (InputStream in = BossMoves.class.getResourceAsStream("/assets/oror_supreme_bosses/boss_moves.json")) {
            if (in != null) {
                JsonObject chars = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("characters");
                for (String id : chars.keySet()) {
                    JsonObject o = chars.getAsJsonObject(id);
                    List<String> list = new ArrayList<>();
                    JsonArray arr = o.getAsJsonArray("moves");
                    for (int i = 0; i < arr.size(); i++) {
                        if (MOVES.containsKey(arr.get(i).getAsString())) {
                            list.add(arr.get(i).getAsString());
                        }
                    }
                    SETS.put(id, new Spec(o.get("style").getAsString(), list));
                }
            }
        } catch (Exception e) {
            throw new IllegalStateException("Invalid boss_moves.json", e);
        }
    }

    private BossMoves() {
    }

    // ------------------------------------------------------------------------------------- driver
    static void tick(SupremeEntity b, ServerLevel sl, LivingEntity t, boolean awake, int color) {
        Spec spec = SETS.get(b.spec.id);
        if (spec == null || spec.moves().isEmpty()) {
            return;
        }
        long now = sl.getGameTime();
        CompoundTag d = b.getPersistentData();
        String current = d.getString("ororMove");
        if (!current.isEmpty()) {
            Move m = MOVES.get(current);
            int e = (int) (now - d.getLong("ororMoveAt"));
            if (m == null || t == null || !t.isAlive() || e > m.length()) {
                d.putString("ororMove", "");
            } else {
                step(b, sl, t, current, m, e, awake, color, d);
            }
            return;
        }
        if (t == null) {
            return;
        }
        double dist = b.distanceTo(t);
        if (now >= d.getLong("ororMoveNext") && dist < 28.0) {
            String pick = choose(spec, d, dist, sl);
            Move m = MOVES.get(pick);
            d.putString("ororMove", pick);
            d.putLong("ororMoveAt", now);
            d.putLong("ororMoveNext", now + m.length() + (awake ? 20L : (b.lore() ? 40L : 70L)));
            Vec3 aim = t.position();
            d.putDouble("ororAimX", aim.x);
            d.putDouble("ororAimY", aim.y);
            d.putDouble("ororAimZ", aim.z);
            b.motion(m.motion(), m.length());
            announce(b, sl, pick);
            step(b, sl, t, pick, m, 0, awake, color, d);
        } else if (now >= d.getLong("ororStepAt") && dist < 32.0) {
            maneuver(b, sl, t, spec.style(), dist, awake, color, d, now);
        }
    }

    /** Next move: cycle through the set, preferring moves suited to the current distance. */
    private static String choose(Spec spec, CompoundTag d, double dist, ServerLevel sl) {
        List<String> moves = spec.moves();
        int start = d.getInt("ororMoveIdx") + 1 + sl.random.nextInt(2);
        for (int i = 0; i < moves.size(); i++) {
            String id = moves.get((start + i) % moves.size());
            Move m = MOVES.get(id);
            if (dist >= m.min() && dist <= m.max()) {
                d.putInt("ororMoveIdx", (start + i) % moves.size());
                return id;
            }
        }
        d.putInt("ororMoveIdx", start % moves.size());
        return moves.get(start % moves.size());
    }

    private static void announce(SupremeEntity b, ServerLevel sl, String move) {
        Component name = Component.literal(b.spec.name + "「")
            .append(Component.translatable("boss_move.oror_supreme_bosses." + b.spec.id + "." + move))
            .append(Component.literal("」"))
            .withStyle(ChatFormatting.RED);
        for (Player p : sl.getEntitiesOfClass(Player.class, b.getBoundingBox().inflate(32.0), p -> b.validEnemy(p))) {
            p.displayClientMessage(name, true);
        }
    }

    // ------------------------------------------------------------------------------------- moves
    private static void step(SupremeEntity b, ServerLevel sl, LivingEntity t, String id, Move m, int e, boolean awake, int color, CompoundTag d) {
        int w = m.windup();
        float dmg = b.spec.damage * (awake ? 2.0F : 1.2F);
        DustParticleOptions dust = RelicEffects.dust(color, 1.5F);
        Vec3 aim = new Vec3(d.getDouble("ororAimX"), d.getDouble("ororAimY"), d.getDouble("ororAimZ"));
        Vec3 dir = BossPowers.flat(aim.subtract(b.position()));
        Vec3 chest = b.position().add(0.0, b.getBbHeight() * 0.5, 0.0);
        if (e == 0) {
            telegraph(b, sl, id, aim, dir, dust);
        } else if (e < w && e % 3 == 0) {
            // gathering power during the wind-up
            sl.sendParticles(dust, chest.x, chest.y, chest.z, 6, 0.6, 0.6, 0.6, 0.0);
        }
        switch (id) {
            case "dash_slash" -> {
                if (e == w) {
                    Vec3 end = aim.add(dir.scale(3.0));
                    for (LivingEntity x : BossPowers.strip(b, b.position(), end, 1.6)) {
                        BossPowers.hit(b, x, dmg * 1.6F);
                    }
                    RelicEffects.line(sl, chest, end.add(0.0, 1.0, 0.0), ParticleTypes.END_ROD, 0.25);
                    RelicEffects.line(sl, chest, end.add(0.0, 1.0, 0.0), dust, 0.2);
                    blink(b, sl, end, dust);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.2F, 1.5F);
                }
            }
            case "blink_strike" -> {
                if (e == w) {
                    Vec3 behind = t.position().subtract(BossPowers.flat(t.getLookAngle()).scale(2.0));
                    blink(b, sl, behind, dust);
                    b.motion(1, 10);
                    for (LivingEntity x : BossPowers.enemies(b, t.position(), 2.8)) {
                        BossPowers.hit(b, x, dmg * 1.5F);
                    }
                    RelicEffects.burst(sl, t.position().add(0.0, 1.0, 0.0), ParticleTypes.SWEEP_ATTACK, 3, 0.5, 0.0);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_CRIT, 1.2F, 0.8F);
                }
            }
            case "combo_rush" -> {
                if (e >= w && (e - w) % 6 == 0 && e - w <= 18) {
                    int n = (e - w) / 6;
                    Vec3 to = BossPowers.flat(t.position().subtract(b.position()));
                    BossPowers.push(b, to.scale(0.9).add(0.0, 0.1, 0.0));
                    b.motion(new int[] {1, 5, 1, 3}[n], 8);
                    Vec3 front = b.position().add(to.scale(1.6));
                    for (LivingEntity x : BossPowers.enemies(b, front, 2.6)) {
                        BossPowers.hit(b, x, dmg * (n == 3 ? 1.1F : 0.7F));
                        if (n == 3) {
                            BossPowers.push(x, to.scale(1.4).add(0.0, 0.5, 0.0));
                        }
                    }
                    RelicEffects.arc(sl, b, 2.2, n % 2 == 0 ? 0.6 : -0.6, dust, ParticleTypes.CRIT);
                    RelicEffects.sound(sl, b.blockPosition(), n == 3 ? SoundEvents.PLAYER_ATTACK_KNOCKBACK : SoundEvents.PLAYER_ATTACK_SWEEP, 1.0F, 1.0F + n * 0.15F);
                }
            }
            case "spin_slash", "reap" -> {
                if (e >= w && (e - w) % 4 == 0) {
                    boolean reap = id.equals("reap");
                    double r = reap ? 4.5 : 3.5;
                    BossPowers.push(b, BossPowers.flat(t.position().subtract(b.position())).scale(0.35));
                    for (LivingEntity x : BossPowers.enemies(b, b.position(), r)) {
                        BossPowers.hit(b, x, dmg * (reap ? 0.6F : 0.5F));
                        if (reap) {
                            x.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1));
                        }
                    }
                    if ((e - w) % 8 == 0) {
                        b.motion(4, 8);
                    }
                    double a0 = e * 0.9;
                    for (int i = 0; i < 16; i++) {
                        double a = a0 + Math.PI * 2.0 * i / 16.0;
                        sl.sendParticles(i % 4 == 0 ? (reap ? ParticleTypes.SOUL : ParticleTypes.SWEEP_ATTACK) : dust,
                            b.getX() + Math.cos(a) * r * 0.8, b.getY() + 1.0, b.getZ() + Math.sin(a) * r * 0.8, 1, 0.0, 0.0, 0.0, 0.0);
                    }
                    if ((e - w) % 8 == 0) {
                        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 0.9F, 0.8F);
                    }
                }
            }
            case "blade_wave" -> {
                if (e == w) {
                    for (int k = -1; k <= 1; k++) {
                        Vec3 v = rotate(dir, k * 20.0);
                        Vec3 end = b.position().add(v.scale(18.0));
                        for (LivingEntity x : BossPowers.strip(b, b.position(), end, 1.2)) {
                            BossPowers.hit(b, x, dmg * 1.1F);
                        }
                        for (double s = 1.5; s < 18.0; s += 2.0) {
                            Vec3 q = chest.add(v.scale(s));
                            sl.sendParticles(ParticleTypes.SWEEP_ATTACK, q.x, q.y, q.z, 1, 0.0, 0.0, 0.0, 0.0);
                        }
                        RelicEffects.line(sl, chest, chest.add(v.scale(18.0)), dust, 0.3);
                    }
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.3F, 0.9F);
                }
            }
            case "leap_slam" -> {
                if (e == w) {
                    double dist = Math.min(14.0, aim.subtract(b.position()).horizontalDistance());
                    b.setDeltaMovement(dir.scale(dist / 12.0).add(0.0, 1.0, 0.0));
                    b.hurtMarked = true;
                    b.motion(3, 24);
                    RelicEffects.burst(sl, b.position(), ParticleTypes.CLOUD, 16, 0.6, 0.05);
                    d.putInt("ororLeap", 1);
                } else if (e > w + 6 && d.getInt("ororLeap") == 1 && (b.onGround() || e >= m.length() - 1)) {
                    d.putInt("ororLeap", 0);
                    land(b, sl, b.position(), awake ? 6.5 : 5.0, dmg * 1.6F, dust);
                    d.putLong("ororMoveAt", d.getLong("ororMoveAt") - m.length());
                }
            }
            case "uppercut" -> {
                if (e == w) {
                    BossPowers.push(b, BossPowers.flat(t.position().subtract(b.position())).scale(0.6).add(0.0, 0.7, 0.0));
                    for (LivingEntity x : BossPowers.enemies(b, b.position(), 4.0)) {
                        BossPowers.hit(b, x, dmg);
                        BossPowers.lift(x, 1.3);
                    }
                    RelicEffects.line(sl, b.position(), b.position().add(0.0, 5.0, 0.0), dust, 0.2);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.2F, 1.2F);
                } else if (e == w + 10) {
                    b.motion(3, 10);
                    for (LivingEntity x : BossPowers.enemies(b, b.position(), 6.0)) {
                        BossPowers.hit(b, x, dmg * 1.2F);
                        if (!(x instanceof SupremeEntity)) {
                            x.setDeltaMovement(new Vec3(x.getDeltaMovement().x, -1.6, x.getDeltaMovement().z));
                            x.hurtMarked = true;
                        }
                    }
                    RelicEffects.burst(sl, chest, ParticleTypes.EXPLOSION, 2, 0.5, 0.0);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ANVIL_LAND, 1.0F, 0.7F);
                }
            }
            case "ground_spikes" -> {
                if (e >= w && (e - w) % 2 == 0 && (e - w) / 2 < 12) {
                    int i = (e - w) / 2;
                    Vec3 q = b.position().add(dir.scale(1.5 + i * 1.4));
                    for (LivingEntity x : BossPowers.enemies(b, q, 1.7)) {
                        BossPowers.hit(b, x, dmg * 0.7F);
                        BossPowers.lift(x, 0.7);
                    }
                    for (double y = 0.0; y < 2.4; y += 0.3) {
                        sl.sendParticles(dust, q.x, q.y + y, q.z, 2, 0.12, 0.0, 0.12, 0.0);
                    }
                    sl.sendParticles(ParticleTypes.POOF, q.x, q.y + 0.2, q.z, 6, 0.4, 0.1, 0.4, 0.02);
                    sl.sendParticles(ParticleTypes.CRIT, q.x, q.y + 1.0, q.z, 6, 0.2, 0.6, 0.2, 0.1);
                    if (i % 3 == 0) {
                        RelicEffects.sound(sl, BlockPos.containing(q), SoundEvents.STONE_BREAK, 1.0F, 0.6F);
                    }
                }
            }
            case "nova" -> {
                if (e >= w) {
                    double r = (e - w) * 0.6;
                    if (r <= 12.0) {
                        for (LivingEntity x : BossPowers.enemies(b, b.position(), r)) {
                            if (x.position().distanceTo(b.position()) >= r - 0.6) {
                                BossPowers.hit(b, x, dmg);
                                BossPowers.push(x, BossPowers.flat(x.position().subtract(b.position())).scale(1.0).add(0.0, 0.35, 0.0));
                            }
                        }
                        if ((e - w) % 2 == 0) {
                            int n = (int) Math.max(12.0, r * 8.0);
                            for (int i = 0; i < n; i++) {
                                double a = Math.PI * 2.0 * i / n;
                                sl.sendParticles(i % 3 == 0 ? ParticleTypes.END_ROD : dust, b.getX() + Math.cos(a) * r, b.getY() + 0.4, b.getZ() + Math.sin(a) * r, 1, 0.0, 0.0, 0.0, 0.0);
                            }
                        }
                        if (e == w) {
                            RelicEffects.sound(sl, b.blockPosition(), SoundEvents.WARDEN_SONIC_CHARGE, 1.0F, 1.4F);
                        }
                    }
                }
            }
            case "vortex" -> {
                if (e >= w && e < m.length() - 6) {
                    for (LivingEntity x : BossPowers.enemies(b, aim, 10.0)) {
                        Vec3 in = aim.subtract(x.position());
                        if (!(x instanceof SupremeEntity) && in.lengthSqr() > 1.0) {
                            BossPowers.push(x, in.normalize().scale(0.22));
                        }
                    }
                    double a0 = e * 0.5;
                    for (int i = 0; i < 4; i++) {
                        double a = a0 + Math.PI * 0.5 * i;
                        double r = 6.0 - (e - w) % 12 * 0.45;
                        sl.sendParticles(i % 2 == 0 ? dust : ParticleTypes.PORTAL, aim.x + Math.cos(a) * r, aim.y + 0.6, aim.z + Math.sin(a) * r, 1, 0.0, 0.0, 0.0, 0.0);
                    }
                } else if (e == m.length() - 6) {
                    for (LivingEntity x : BossPowers.enemies(b, aim, 4.0)) {
                        BossPowers.hit(b, x, dmg * 1.4F);
                        BossPowers.lift(x, 0.8);
                    }
                    RelicEffects.burst(sl, aim.add(0.0, 1.0, 0.0), dust, 40, 1.5, 0.0);
                    RelicEffects.shock(sl, aim.add(0.0, 0.5, 0.0), 32, ParticleTypes.END_ROD, 0.5);
                    RelicEffects.sound(sl, BlockPos.containing(aim), SoundEvents.FIREWORK_ROCKET_BLAST, 1.6F, 0.6F);
                }
            }
            case "meteor" -> {
                if (e == 0) {
                    for (int i = 0; i < 5; i++) {
                        d.putDouble("ororMet" + i + "x", aim.x + (sl.random.nextDouble() - 0.5) * 9.0);
                        d.putDouble("ororMet" + i + "z", aim.z + (sl.random.nextDouble() - 0.5) * 9.0);
                        RelicEffects.circle(sl, new Vec3(d.getDouble("ororMet" + i + "x"), aim.y + 0.1, d.getDouble("ororMet" + i + "z")), 2.5, dust);
                    }
                }
                if (e >= w && (e - w) % 6 == 0 && (e - w) / 6 < 5) {
                    int i = (e - w) / 6;
                    Vec3 at = new Vec3(d.getDouble("ororMet" + i + "x"), aim.y, d.getDouble("ororMet" + i + "z"));
                    RelicEffects.line(sl, at.add(2.0, 14.0, 2.0), at, ParticleTypes.FLAME, 0.4);
                    RelicEffects.line(sl, at.add(2.0, 14.0, 2.0), at, dust, 0.3);
                    sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y + 0.5, at.z, 1, 0.0, 0.0, 0.0, 0.0);
                    for (LivingEntity x : BossPowers.enemies(b, at, 3.0)) {
                        BossPowers.hit(b, x, dmg * 1.2F);
                        BossPowers.lift(x, 0.5);
                    }
                    RelicEffects.sound(sl, BlockPos.containing(at), SoundEvents.FIREWORK_ROCKET_BLAST, 1.8F, 0.5F);
                }
            }
            case "beam", "breath" -> {
                boolean breath = id.equals("breath");
                Vec3 eye = b.getEyePosition();
                Vec3 want = t.getEyePosition().subtract(eye).normalize();
                if (e == w) {
                    d.putDouble("ororBeamX", want.x);
                    d.putDouble("ororBeamY", want.y);
                    d.putDouble("ororBeamZ", want.z);
                    RelicEffects.sound(sl, b.blockPosition(), breath ? SoundEvents.ENDER_DRAGON_GROWL : SoundEvents.WARDEN_SONIC_CHARGE, 1.0F, breath ? 1.2F : 1.8F);
                }
                if (e >= w) {
                    Vec3 v = new Vec3(d.getDouble("ororBeamX"), d.getDouble("ororBeamY"), d.getDouble("ororBeamZ"));
                    v = v.add(want.subtract(v).scale(breath ? 0.18 : 0.12)).normalize();
                    d.putDouble("ororBeamX", v.x);
                    d.putDouble("ororBeamY", v.y);
                    d.putDouble("ororBeamZ", v.z);
                    double len = breath ? 12.0 : 24.0;
                    var wall = sl.clip(new ClipContext(eye, eye.add(v.scale(len)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, b));
                    if (wall.getType() != HitResult.Type.MISS) {
                        len = wall.getLocation().distanceTo(eye);
                    }
                    if (breath) {
                        for (double s = 1.0; s < len; s += 0.8) {
                            Vec3 q = eye.add(v.scale(s));
                            double sp = s * 0.18;
                            sl.sendParticles(dust, q.x, q.y, q.z, 2, sp, sp, sp, 0.0);
                            if (((int) (s * 10) + e) % 3 == 0) {
                                sl.sendParticles(ParticleTypes.END_ROD, q.x, q.y, q.z, 1, sp, sp, sp, 0.02);
                            }
                        }
                    } else {
                        RelicEffects.line(sl, eye, eye.add(v.scale(len)), dust, 0.35);
                        RelicEffects.line(sl, eye, eye.add(v.scale(len)), ParticleTypes.END_ROD, 1.0);
                    }
                    if ((e - w) % 4 == 0) {
                        for (LivingEntity x : breath ? cone(b, eye, v, len, 25.0) : BossPowers.strip(b, eye, eye.add(v.scale(len)), 0.9)) {
                            BossPowers.hit(b, x, dmg * (breath ? 0.35F : 0.45F));
                        }
                    }
                }
            }
            case "homing_orbs" -> {
                int n = awake ? 6 : 4;
                if (e == w) {
                    Vec3 eye = b.getEyePosition();
                    for (int i = 0; i < n; i++) {
                        double a = Math.PI * 2.0 * i / n;
                        d.putDouble("ororOrb" + i + "x", eye.x + Math.cos(a) * 1.6);
                        d.putDouble("ororOrb" + i + "y", eye.y + 0.4);
                        d.putDouble("ororOrb" + i + "z", eye.z + Math.sin(a) * 1.6);
                        d.putBoolean("ororOrb" + i, true);
                    }
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.EVOKER_PREPARE_SUMMON, 1.0F, 1.4F);
                } else if (e > w) {
                    for (int i = 0; i < n; i++) {
                        if (!d.getBoolean("ororOrb" + i)) {
                            continue;
                        }
                        Vec3 o = new Vec3(d.getDouble("ororOrb" + i + "x"), d.getDouble("ororOrb" + i + "y"), d.getDouble("ororOrb" + i + "z"));
                        double speed = Math.min(0.75, 0.25 + (e - w) * 0.02) * (1.0 + i * 0.05);
                        Vec3 to = t.position().add(0.0, t.getBbHeight() * 0.5, 0.0).subtract(o);
                        o = o.add(to.lengthSqr() > 1.0E-4 ? to.normalize().scale(speed) : Vec3.ZERO);
                        d.putDouble("ororOrb" + i + "x", o.x);
                        d.putDouble("ororOrb" + i + "y", o.y);
                        d.putDouble("ororOrb" + i + "z", o.z);
                        sl.sendParticles(dust, o.x, o.y, o.z, 3, 0.1, 0.1, 0.1, 0.0);
                        sl.sendParticles(ParticleTypes.END_ROD, o.x, o.y, o.z, 1, 0.0, 0.0, 0.0, 0.0);
                        List<LivingEntity> touched = BossPowers.enemies(b, o, 1.3);
                        if (!touched.isEmpty() || e == m.length()) {
                            d.putBoolean("ororOrb" + i, false);
                            for (LivingEntity x : BossPowers.enemies(b, o, 2.2)) {
                                BossPowers.hit(b, x, dmg * 0.8F);
                            }
                            RelicEffects.burst(sl, o, dust, 16, 0.5, 0.0);
                            RelicEffects.burst(sl, o, ParticleTypes.FIREWORK, 8, 0.2, 0.15);
                            RelicEffects.sound(sl, BlockPos.containing(o), SoundEvents.AMETHYST_BLOCK_CHIME, 1.0F, 0.7F);
                        }
                    }
                }
            }
            case "arrow_rain" -> {
                if (e >= w && (e - w) % 2 == 0) {
                    ItemStack bow = b.getMainHandItem().isEmpty() ? new ItemStack(Items.BOW) : b.getMainHandItem();
                    for (int i = 0; i < 2; i++) {
                        Arrow a = new Arrow(sl, b, new ItemStack(Items.ARROW), bow);
                        a.moveTo(aim.x + (sl.random.nextDouble() - 0.5) * 10.0, aim.y + 12.0, aim.z + (sl.random.nextDouble() - 0.5) * 10.0);
                        a.setDeltaMovement(0.0, -2.6, 0.0);
                        a.setBaseDamage(dmg * 0.3F);
                        a.pickup = AbstractArrow.Pickup.DISALLOWED;
                        sl.addFreshEntity(a);
                    }
                    if ((e - w) % 6 == 0) {
                        RelicEffects.burst(sl, aim.add(0.0, 12.0, 0.0), dust, 20, 3.0, 0.0);
                        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ARROW_SHOOT, 1.0F, 0.6F);
                    }
                }
            }
            case "bolt_barrage" -> {
                if (e >= w && (e - w) % 3 == 0) {
                    List<LivingEntity> near = BossPowers.enemies(b, aim, 10.0);
                    if (!near.isEmpty()) {
                        BossPowers.bolt(b, sl, near.get(((e - w) / 3) % near.size()), dmg * 0.5F, dust, false);
                        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, 0.8F, 1.5F);
                    }
                }
            }
            case "bullet_storm" -> {
                if (e >= w) {
                    BossPowers.bolt(b, sl, t, dmg * 0.18F, dust, true);
                    if ((e - w) % 3 == 0) {
                        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, 0.6F, 1.9F);
                    }
                }
            }
            case "shell_barrage" -> {
                if (e >= w && (e - w) % 6 == 0 && (e - w) / 6 < 4) {
                    Vec3 at = aim.add((sl.random.nextDouble() - 0.5) * 6.0, 0.0, (sl.random.nextDouble() - 0.5) * 6.0);
                    RelicEffects.line(sl, chest, at.add(0.0, 0.5, 0.0), ParticleTypes.LARGE_SMOKE, 0.8);
                    for (LivingEntity x : BossPowers.enemies(b, at, 3.5)) {
                        BossPowers.hit(b, x, dmg * 1.0F);
                        BossPowers.lift(x, 0.6);
                    }
                    sl.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y + 0.5, at.z, 1, 0.0, 0.0, 0.0, 0.0);
                    RelicEffects.burst(sl, at.add(0.0, 0.5, 0.0), dust, 16, 1.2, 0.0);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.WITHER_SHOOT, 1.2F, 0.9F);
                }
            }
            case "barrier" -> {
                if (e == w) {
                    b.shield += b.spec.damage * 4.0F;
                    for (LivingEntity x : BossPowers.enemies(b, b.position(), 5.0)) {
                        BossPowers.hit(b, x, dmg * 0.6F);
                        BossPowers.push(x, BossPowers.flat(x.position().subtract(b.position())).scale(1.6).add(0.0, 0.4, 0.0));
                    }
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ANVIL_LAND, 0.9F, 1.6F);
                }
                if (e >= w && (e - w) % 4 == 0) {
                    for (Projectile pr : sl.getEntitiesOfClass(Projectile.class, b.getBoundingBox().inflate(8.0),
                        x -> x.getOwner() instanceof LivingEntity o && b.validEnemy(o))) {
                        Vec3 back = pr.getOwner().position().add(0.0, 1.0, 0.0).subtract(pr.position()).normalize();
                        pr.setOwner(b);
                        pr.setDeltaMovement(back.scale(Math.max(1.2, pr.getDeltaMovement().length() * 1.5)));
                        pr.hasImpulse = true;
                    }
                    double a0 = e * 0.4;
                    for (int i = 0; i < 20; i++) {
                        double a = a0 + Math.PI * 2.0 * i / 20.0;
                        double y = (i % 5) * 0.5;
                        sl.sendParticles(dust, b.getX() + Math.cos(a) * 2.2, b.getY() + y, b.getZ() + Math.sin(a) * 2.2, 1, 0.0, 0.0, 0.0, 0.0);
                    }
                }
            }
            case "chain_pull" -> {
                if (e == w) {
                    for (LivingEntity x : BossPowers.enemies(b, b.position(), 14.0)) {
                        Vec3 to = x.position().add(0.0, x.getBbHeight() * 0.5, 0.0);
                        RelicEffects.line(sl, chest, to, dust, 0.2);
                        RelicEffects.line(sl, chest, to, ParticleTypes.CRIT, 0.8);
                        if (!(x instanceof SupremeEntity)) {
                            BossPowers.push(x, b.position().subtract(x.position()).normalize().scale(1.5).add(0.0, 0.35, 0.0));
                        }
                        x.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 3));
                    }
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.CHAIN_BREAK, 1.2F, 0.8F);
                } else if (e == w + 10) {
                    b.motion(3, 10);
                    for (LivingEntity x : BossPowers.enemies(b, b.position(), 3.5)) {
                        BossPowers.hit(b, x, dmg * 1.1F);
                    }
                    RelicEffects.shock(sl, b.position().add(0.0, 0.3, 0.0), 32, ParticleTypes.POOF, 0.45);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.2F, 0.8F);
                }
            }
            case "ricochet" -> {
                if (e == w) {
                    List<LivingEntity> chain = BossPowers.enemies(b, aim, 14.0);
                    chain.sort(Comparator.comparingDouble(x -> x.position().distanceToSqr(aim)));
                    Vec3 at = chest;
                    for (int i = 0; i < Math.min(chain.size(), awake ? 8 : 6); i++) {
                        LivingEntity x = chain.get(i);
                        Vec3 to = x.position().add(0.0, x.getBbHeight() * 0.5, 0.0);
                        RelicEffects.line(sl, at, to, dust, 0.2);
                        RelicEffects.line(sl, at, to, ParticleTypes.CRIT, 0.6);
                        BossPowers.hit(b, x, dmg * 0.9F);
                        at = to;
                    }
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.CHAIN_BREAK, 1.0F, 1.7F);
                }
            }
            case "afterimage" -> {
                if (e >= w && (e - w) % 8 == 0 && (e - w) / 8 < 4) {
                    int n = (e - w) / 8;
                    double a = sl.random.nextDouble() * Math.PI * 2.0;
                    Vec3 to = t.position().add(Math.cos(a) * 3.0, 0.0, Math.sin(a) * 3.0);
                    blink(b, sl, to, dust);
                    b.motion(n % 2 == 0 ? 1 : 5, 8);
                    for (LivingEntity x : BossPowers.enemies(b, t.position(), 2.6)) {
                        BossPowers.hit(b, x, dmg * 0.7F);
                    }
                    RelicEffects.arc(sl, b, 2.0, n % 2 == 0 ? 0.7 : -0.7, dust, ParticleTypes.END_ROD);
                    RelicEffects.sound(sl, b.blockPosition(), SoundEvents.PLAYER_ATTACK_SWEEP, 1.0F, 1.3F + n * 0.1F);
                }
            }
            case "charge" -> {
                if (e >= w && e < w + 14) {
                    BossPowers.push(b, dir.scale(0.55));
                    sl.sendParticles(dust, b.getX(), b.getY() + 0.6, b.getZ(), 4, 0.3, 0.3, 0.3, 0.0);
                    sl.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.1, b.getZ(), 2, 0.2, 0.0, 0.2, 0.01);
                    if ((e - w) % 3 == 0) {
                        for (LivingEntity x : BossPowers.enemies(b, b.position().add(dir.scale(1.2)), 2.0)) {
                            BossPowers.hit(b, x, dmg * 0.6F);
                            BossPowers.push(x, dir.scale(1.2).add(0.0, 0.45, 0.0));
                        }
                    }
                    if (e == w) {
                        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ENDER_DRAGON_GROWL, 0.6F, 1.6F);
                    }
                }
            }
            default -> {
            }
        }
    }

    /** What each move shows during its wind-up. */
    private static void telegraph(SupremeEntity b, ServerLevel sl, String id, Vec3 aim, Vec3 dir, DustParticleOptions dust) {
        Vec3 base = b.position().add(0.0, 0.1, 0.0);
        switch (id) {
            case "dash_slash", "blade_wave", "ground_spikes", "charge" ->
                RelicEffects.line(sl, base, base.add(dir.scale(id.equals("ground_spikes") ? 18.0 : 16.0)), dust, 0.35);
            case "spin_slash", "reap", "nova", "barrier", "chain_pull", "uppercut" ->
                RelicEffects.circle(sl, base, id.equals("nova") ? 10.0 : (id.equals("chain_pull") ? 14.0 : 4.5), dust);
            case "beam", "breath", "bolt_barrage", "bullet_storm" ->
                RelicEffects.line(sl, b.getEyePosition(), aim.add(0.0, 1.0, 0.0), dust, 0.5);
            default -> RelicEffects.circle(sl, aim.add(0.0, 0.1, 0.0), id.equals("arrow_rain") ? 5.0 : (id.equals("vortex") ? 4.0 : 3.0), dust);
        }
        sl.sendParticles(ParticleTypes.END_ROD, aim.x, aim.y + 0.2, aim.z, 10, 0.5, 0.05, 0.5, 0.02);
        RelicEffects.sound(sl, b.blockPosition(), SoundEvents.EVOKER_CAST_SPELL, 1.0F, 0.7F);
    }

    // ------------------------------------------------------------------------------------- movement
    private static void maneuver(SupremeEntity b, ServerLevel sl, LivingEntity t, String style, double dist, boolean awake, int color, CompoundTag d, long now) {
        int gap = switch (style) {
            case "duelist", "gunner", "swimmer" -> 30;
            case "caster", "brawler", "flyer" -> 38;
            case "trickster", "guardian" -> 44;
            case "juggernaut" -> 50;
            default -> 60;
        };
        d.putLong("ororStepAt", now + (long) (gap * (awake ? 0.6 : 1.0)));
        Vec3 to = BossPowers.flat(t.position().subtract(b.position()));
        Vec3 side = new Vec3(-to.z, 0.0, to.x).scale((sl.random.nextInt(2) == 0) ? 1.0 : -1.0);
        DustParticleOptions dust = RelicEffects.dust(color, 1.2F);
        switch (style) {
            case "duelist" -> {
                if (dist > 7.0) {
                    dash(b, sl, to.scale(1.3).add(0.0, 0.1, 0.0), dust, 2);
                } else if (dist < 2.5) {
                    dash(b, sl, to.scale(-1.0).add(0.0, 0.3, 0.0), dust, 10);
                } else {
                    dash(b, sl, side.scale(1.0).add(0.0, 0.15, 0.0), dust, 6);
                }
            }
            case "brawler", "juggernaut" -> {
                if (dist > (style.equals("brawler") ? 5.0 : 8.0)) {
                    dash(b, sl, to.scale(Math.min(1.7, dist * 0.13)).add(0.0, 0.65, 0.0), dust, 6);
                } else if (style.equals("brawler")) {
                    dash(b, sl, side.scale(0.8).add(0.0, 0.2, 0.0), dust, 6);
                }
            }
            case "caster", "gunner" -> {
                if (dist < (style.equals("caster") ? 7.0 : 6.0)) {
                    if (style.equals("caster") && (sl.random.nextInt(2) == 0)) {
                        blink(b, sl, b.position().subtract(to.scale(7.0)).add(side.scale(2.0)), dust);
                    } else {
                        dash(b, sl, to.scale(-1.1).add(side.scale(0.4)).add(0.0, 0.3, 0.0), dust, 10);
                    }
                } else if (dist > 16.0) {
                    dash(b, sl, to.scale(0.7).add(0.0, 0.1, 0.0), dust, 0);
                } else {
                    dash(b, sl, side.scale(0.8).add(0.0, 0.1, 0.0), dust, 6);
                }
            }
            case "guardian" -> {
                if (dist > 4.0) {
                    dash(b, sl, to.scale(0.6).add(0.0, 0.05, 0.0), dust, 0);
                } else {
                    dash(b, sl, side.scale(0.7).add(0.0, 0.1, 0.0), dust, 6);
                }
            }
            case "flyer" -> {
                double dy = t.getY() + 1.0 - b.getY();
                dash(b, sl, to.scale(1.4).add(0.0, Math.max(-0.6, Math.min(0.6, dy * 0.15)), 0.0), dust, 14);
            }
            case "swimmer" -> dash(b, sl, to.scale(1.2).add(side.scale(0.5)), dust, 2);
            case "trickster" -> {
                double a = sl.random.nextDouble() * Math.PI * 2.0;
                double r = 4.0 + sl.random.nextDouble() * 4.0;
                blink(b, sl, t.position().add(Math.cos(a) * r, 0.0, Math.sin(a) * r), dust);
            }
            default -> {
            }
        }
    }

    private static void dash(SupremeEntity b, ServerLevel sl, Vec3 v, DustParticleOptions dust, int motion) {
        BossPowers.push(b, v);
        if (motion > 0) {
            b.motion(motion, 10);
        }
        for (int i = 0; i < 5; i++) {
            Vec3 q = b.position().subtract(v.scale(i * 0.5)).add(0.0, 0.8, 0.0);
            sl.sendParticles(dust, q.x, q.y, q.z, 2, 0.2, 0.4, 0.2, 0.0);
        }
        sl.sendParticles(ParticleTypes.CLOUD, b.getX(), b.getY() + 0.1, b.getZ(), 4, 0.3, 0.0, 0.3, 0.02);
    }

    /** Teleports to a free spot near `to` (feet level), leaving a trail. Rooted characters never blink. */
    private static void blink(SupremeEntity b, ServerLevel sl, Vec3 to, DustParticleOptions dust) {
        if (b.spec.model.equals("tree")) {
            return;
        }
        Vec3 from = b.position();
        for (int i = 0; i < 4; i++) {
            Vec3 q = to.add(0.0, i * 0.5, 0.0);
            if (sl.noCollision(b, b.getBoundingBox().move(q.subtract(from)))) {
                RelicEffects.line(sl, from.add(0.0, 1.0, 0.0), q.add(0.0, 1.0, 0.0), dust, 0.4);
                sl.sendParticles(ParticleTypes.REVERSE_PORTAL, from.x, from.y + 1.0, from.z, 20, 0.3, 0.6, 0.3, 0.05);
                b.teleportTo(q.x, q.y, q.z);
                sl.sendParticles(ParticleTypes.REVERSE_PORTAL, q.x, q.y + 1.0, q.z, 20, 0.3, 0.6, 0.3, 0.05);
                RelicEffects.sound(sl, b.blockPosition(), SoundEvents.ENDERMAN_TELEPORT, 0.7F, 1.4F);
                return;
            }
        }
    }

    private static void land(SupremeEntity b, ServerLevel sl, Vec3 at, double r, float dmg, DustParticleOptions dust) {
        for (LivingEntity x : BossPowers.enemies(b, at, r)) {
            BossPowers.hit(b, x, dmg);
            BossPowers.lift(x, 0.7);
            x.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 60, 2));
        }
        b.motion(7, 12);
        RelicEffects.shock(sl, at.add(0.0, 0.2, 0.0), 56, ParticleTypes.CLOUD, 0.65);
        RelicEffects.circle(sl, at.add(0.0, 0.1, 0.0), r, dust);
        sl.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.5, at.z, 6, r * 0.3, 0.3, r * 0.3, 0.0);
        RelicEffects.sound(sl, BlockPos.containing(at), SoundEvents.ANVIL_LAND, 1.4F, 0.5F);
        RelicEffects.sound(sl, BlockPos.containing(at), SoundEvents.FIREWORK_ROCKET_BLAST, 1.6F, 0.5F);
    }

    private static List<LivingEntity> cone(SupremeEntity b, Vec3 eye, Vec3 v, double len, double deg) {
        double cos = Math.cos(Math.toRadians(deg));
        List<LivingEntity> out = new ArrayList<>();
        for (LivingEntity x : BossPowers.enemies(b, eye, len)) {
            Vec3 q = x.position().add(0.0, x.getBbHeight() * 0.5, 0.0).subtract(eye);
            if (q.lengthSqr() < 1.0 || q.normalize().dot(v) >= cos) {
                out.add(x);
            }
        }
        return out;
    }

    private static Vec3 rotate(Vec3 v, double deg) {
        double a = Math.toRadians(deg);
        return new Vec3(v.x * Math.cos(a) - v.z * Math.sin(a), 0.0, v.x * Math.sin(a) + v.z * Math.cos(a));
    }
}
