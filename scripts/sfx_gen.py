#!/usr/bin/env python3
"""Genera efectos de sonido sintéticos (sin derechos de autor) en template/public/sfx y template-reel/public/sfx.

Uso:  sfx_gen.py [--seed 7]
Crea variantes de los básicos (whoosh_2, pop_2…) y efectos nuevos: riser, swoosh, glitch, impacto,
shutter, tecleo, brillo. No toca los WAV originales. Solo usa la biblioteca estándar de Python.
"""
import argparse, math, random, struct, wave
from pathlib import Path

SR = 44100
SKILL = Path(__file__).resolve().parent.parent


def env(n, a, d, curve=3.0):
    """ataque lineal de `a` muestras y caída exponencial hasta n"""
    out = []
    for i in range(n):
        if i < a:
            out.append(i / max(1, a))
        else:
            out.append(math.exp(-curve * (i - a) / max(1, n - a)))
    return out


def lowpass(x, cut):
    """filtro de un polo con frecuencia de corte variable (lista o número)"""
    y, prev = [], 0.0
    for i, v in enumerate(x):
        c = cut[i] if isinstance(cut, list) else cut
        a = 1 - math.exp(-2 * math.pi * c / SR)
        prev += a * (v - prev)
        y.append(prev)
    return y


def highpass(x, cut):
    lp = lowpass(x, cut)
    return [a - b for a, b in zip(x, lp)]


def noise(n, rnd):
    return [rnd.uniform(-1, 1) for _ in range(n)]


def norm(x, peak=0.7):
    m = max(1e-9, max(abs(v) for v in x))
    return [v * peak / m for v in x]


def save(name, x):
    data = b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in norm(x))
    for d in (SKILL / "template" / "public" / "sfx", SKILL / "template-reel" / "public" / "sfx"):
        d.mkdir(parents=True, exist_ok=True)
        with wave.open(str(d / f"{name}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data)
    print("·", name)


def whoosh(rnd, dur=0.6, f0=300, f1=4000, peak_at=0.55):
    n = int(SR * dur)
    nz = noise(n, rnd)
    cut = [f0 + (f1 - f0) * math.sin(math.pi * i / n) ** 2 for i in range(n)]
    sig = lowpass(nz, cut)
    e = [math.sin(math.pi * min(1, (i / n) / peak_at if i / n < peak_at else 1 - (i / n - peak_at) / (1 - peak_at) * 0.999)) for i in range(n)]
    return [s * a for s, a in zip(sig, e)]


def pop(rnd, f0=700, f1=180, dur=0.09):
    n = int(SR * dur)
    ph, out = 0.0, []
    for i in range(n):
        f = f1 + (f0 - f1) * math.exp(-i / (n * 0.25))
        ph += 2 * math.pi * f / SR
        out.append(math.sin(ph) * math.exp(-5 * i / n))
    return out


def bell(rnd, f=1320, dur=1.1):
    n = int(SR * dur)
    parts = [(1, 1.0, 3), (2.76, 0.5, 5), (5.4, 0.25, 8), (8.93, 0.12, 12)]
    return [sum(a * math.sin(2 * math.pi * f * r * i / SR) * math.exp(-k * i / n) for r, a, k in parts) for i in range(n)]


def click(rnd, dur=0.012, cut=3000):
    n = int(SR * dur)
    x = highpass(noise(n, rnd), cut)
    return [v * math.exp(-8 * i / n) for i, v in enumerate(x)] + [0.0] * 200


def boom(rnd, f0=110, f1=42, dur=0.9):
    n = int(SR * dur)
    ph, out = 0.0, []
    nz = lowpass(noise(n, rnd), 400)
    for i in range(n):
        f = f1 + (f0 - f1) * math.exp(-i / (n * 0.12))
        ph += 2 * math.pi * f / SR
        out.append(math.sin(ph) * math.exp(-4 * i / n) + 0.35 * nz[i] * math.exp(-14 * i / n))
    return out


def riser(rnd, dur=1.4):
    n = int(SR * dur)
    nz = noise(n, rnd)
    cut = [200 + 7000 * (i / n) ** 2 for i in range(n)]
    sig = lowpass(nz, cut)
    ph, out = 0.0, []
    for i in range(n):
        f = 180 + 900 * (i / n) ** 2
        ph += 2 * math.pi * f / SR
        a = (i / n) ** 2.2
        out.append(a * (0.7 * sig[i] * 2 + 0.25 * math.sin(ph)))
    tail = int(SR * 0.04)
    return out + [out[-1] * (1 - k / tail) for k in range(tail)]


def glitch(rnd, dur=0.38):
    out = []
    while len(out) < SR * dur:
        seg = int(SR * rnd.uniform(0.008, 0.04))
        kind = rnd.random()
        f = rnd.choice([220, 440, 880, 1760, 3520])
        for i in range(seg):
            if kind < 0.4:
                out.append(1.0 if math.sin(2 * math.pi * f * i / SR) > 0 else -1.0)
            elif kind < 0.75:
                out.append(rnd.uniform(-1, 1))
            else:
                out.append(0.0)
    return [v * 0.6 for v in out]


def impacto(rnd):
    b = boom(rnd, 140, 45, 1.0)
    crack = highpass(noise(int(SR * 0.08), rnd), 2500)
    crack = [v * math.exp(-10 * i / len(crack)) for i, v in enumerate(crack)]
    return [b[i] + (1.2 * crack[i] if i < len(crack) else 0) for i in range(len(b))]


def shutter(rnd):
    a = click(rnd, 0.018, 1800)
    gap = [0.0] * int(SR * 0.055)
    b = click(rnd, 0.025, 1200)
    return a + gap + [v * 0.8 for v in b]


def tecleo(rnd, n_keys=7, dur=0.75):
    out = [0.0] * int(SR * dur)
    t = 0.02
    for _ in range(n_keys):
        k = click(rnd, rnd.uniform(0.008, 0.016), rnd.uniform(1500, 3500))
        s = int(SR * t)
        g = rnd.uniform(0.5, 1)
        for i, v in enumerate(k):
            if s + i < len(out):
                out[s + i] += v * g
        t += rnd.uniform(0.07, 0.12)
    return out


def brillo(rnd, dur=0.9):
    n = int(SR * dur)
    notes = [1568, 2093, 2637, 3136]
    out = [0.0] * n
    for k, f in enumerate(notes):
        s = int(SR * 0.06 * k)
        for i in range(s, n):
            j = i - s
            out[i] += 0.5 * math.sin(2 * math.pi * f * j / SR) * math.exp(-5 * j / (n - s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    rnd = random.Random(ap.parse_args().seed)
    save("whoosh_2", whoosh(rnd, 0.5, 250, 5200, 0.6))
    save("whoosh_3", whoosh(rnd, 0.75, 400, 3000, 0.45))
    save("swoosh", whoosh(rnd, 0.32, 900, 7500, 0.5))
    save("swoosh_2", whoosh(rnd, 0.28, 1200, 9000, 0.4))
    save("pop_2", pop(rnd, 900, 260, 0.08))
    save("pop_3", pop(rnd, 520, 140, 0.11))
    save("ding_2", bell(rnd, 1760, 1.0))
    save("click_2", click(rnd, 0.01, 4500))
    save("boom_2", boom(rnd, 95, 38, 1.1))
    save("riser", riser(rnd))
    save("glitch", glitch(rnd))
    save("impacto", impacto(rnd))
    save("shutter", shutter(rnd))
    save("tecleo", tecleo(rnd))
    save("brillo", brillo(rnd))


if __name__ == "__main__":
    main()
