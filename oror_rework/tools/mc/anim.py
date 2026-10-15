"""Python mirror of RigModel.animate (rotation parts only) for preview frames."""
import math

def pose(rig, age=0.0, swing=0.0, amount=0.0, motion=0, progress=0.0, action=0):
    out = {}
    pulse = math.sin(progress * math.pi)
    for b in rig.bones:
        a, p = b.anim, b.params
        if not a:
            continue
        amp, speed, phase = p.get('amp', 0.1), p.get('speed', 0.08), p.get('phase', 0.0)
        left = b.name.endswith('_l') or '_l_' in b.name
        dx = dy = dz = 0.0
        if a == 'breath':
            dx += math.sin(age * 0.08) * 0.015 + (0.08 if action > 0 else 0)
        elif a in ('arm_r', 'arm_l'):
            l = a == 'arm_l'
            sign = -1 if l else 1
            dx += math.cos(swing * 0.6662 + (0 if l else math.pi)) * amount * 0.6
            dz += sign * (math.cos(age * 0.09) * 0.03 + 0.04)
            if action > 0:
                dx -= 0.6
            if motion == 1:
                dx -= pulse * 1.6; dy += sign * pulse * 1.2
            elif motion == 3:
                dx -= pulse * 2.4; dy += sign * pulse * 0.4
            elif motion in (8, 11, 15):
                dx -= pulse * 1.7; dz += sign * pulse * 0.5
        elif a in ('leg_r', 'leg_l'):
            dx += math.cos(swing * 0.6662 + (math.pi if a == 'leg_l' else 0)) * amount * 0.8
        elif a == 'skirt':
            dx -= abs(math.cos(swing * 0.6662)) * amount * 0.12 * p.get('k', 1.0)
            dz += math.sin(age * 0.05) * 0.012
        elif a in ('hair', 'cape'):
            dx += amount * p.get('drag', 0.9 if a == 'cape' else 0.5) * 0.6 + math.sin(age * speed + phase) * amp
            dz += math.cos(age * speed * 0.7 + phase) * amp * 0.3
        elif a == 'tail':
            i = p.get('i', 0.0)
            dy += math.sin(age * speed - i * 0.6) * amp * (1 + i * 0.15)
            dx += math.cos(age * speed * 0.7 - i * 0.5) * amp * 0.25
        elif a in ('wing_r', 'wing_l'):
            flap = math.sin(age * speed) * amp + amount * 0.3
            dy += -flap if a == 'wing_l' else flap
        elif a == 'sway':
            v = math.sin(age * speed + phase) * amp
            ax = int(p.get('ax', 0))
            if ax == 1: dy += v
            elif ax == 2: dz += v
            else: dx += v
        elif a == 'spin':
            turn = age * speed
            ax = int(p.get('ax', 0))
            if ax == 1: dx += turn
            elif ax == 2: dz += turn
            else: dy += turn
        elif a == 'jaw':
            dx += math.sin(age * 0.05) * 0.03 + pulse * 0.45
        out[b.name] = (dx, dy, dz)
    return out
