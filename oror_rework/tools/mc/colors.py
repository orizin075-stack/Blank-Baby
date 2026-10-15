"""Colour helpers with hue-shifted shading (shadows lean cool, lights lean warm)."""
import colorsys

def hexc(c):
    if isinstance(c, str):
        c = c.lstrip('#')
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    if isinstance(c, int):
        return ((c >> 16) & 255, (c >> 8) & 255, c & 255)
    return tuple(int(round(float(v))) for v in c[:3])

def mix(a, b, t):
    a, b = hexc(a), hexc(b)
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))

def _toward(h, target, amt):
    d = ((target - h + 0.5) % 1) - 0.5
    return h + max(-abs(amt), min(abs(amt), d))

def hue_shift(c, k):
    """k < 1 darkens towards blue-violet, k > 1 lightens towards warm yellow."""
    r, g, b = [v / 255 for v in hexc(c)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if k < 1:
        t = 1 - k
        h = _toward(h, 0.72, 0.09 * t) if s > 0.04 else h
        s = min(1, s * (1 + 0.35 * t) + (0.08 * t if s < 0.2 else 0))
        v = v * k
    else:
        t = k - 1
        h = _toward(h, 0.14, 0.06 * t)
        s = s * (1 - 0.45 * t)
        v = min(1, v + (1 - v) * 0.8 * t + 0.08 * t)
    r, g, b = colorsys.hsv_to_rgb(h % 1, max(0, min(1, s)), max(0, min(1, v)))
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

def shade(c, k):
    return hue_shift(c, k)

def lum(c):
    r, g, b = hexc(c)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255
