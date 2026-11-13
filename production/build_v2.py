#!/usr/bin/env python3
"""v2 layout rebuild: PIL background canvases + ffmpeg window compositing.
Audio/telop/segment durations identical to assemble_all.py (reuses work/{reel}_voice.wav).
"""
import subprocess, os, json, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.expanduser("~/workspace/reel_shiba_test")
WORK = BASE + "/work"
WV2 = BASE + "/work_v2"
OUT = BASE + "/out_v2"
ASSETS = OUT + "/assets"
os.makedirs(WV2, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1080, 1920
GAP, TAIL = 1.0, 2.0

CLIP = {
"teacher": WORK + "/media-generation-a1-lipsync-test-0-0784808f-574a-48e7-9796-30797bdf2cd5.mp4",
"surprised": WORK + "/media-generation-a1-surprised-talk-0-90e6a51a-3a0d-4991-81cb-33a56b8f863a.mp4",
"checklist": WORK + "/media-generation-a1-checklist-talk-0-e207df22-208f-4eb5-af61-acac3a2179f9.mp4",
"sad": WORK + "/media-generation-b-sad-talk-0-ab5f40b2-ee7b-4700-a29d-b98a38c6cee7.mp4",
"side": WORK + "/media-generation-b-side-talk-0-fce10f06-c624-4e76-be02-5c09d694349a.mp4",
"listen": WORK + "/media-generation-b-listen-nod-0-bd435866-2ef2-4340-a478-312e7a17e6f0.mp4",
"pc": WORK + "/media-generation-c-pc-work-0-bf7c4d07-5659-4c7e-8f33-9619c842c24d.mp4",
"graph": WORK + "/media-generation-c-graph-talk-0-c8e73f87-4018-4a79-a1c5-fce0b55e8e54.mp4",
"duo": WORK + "/media-generation-b-duo-talk-0-ec99923c-d92c-4fc2-93fa-01a510a1feeb.mp4",
}
STILL = {
"memo": BASE + "/stills/g_memo.jpg",
"cards5": BASE + "/stills/g_cards5.jpg",
"gift": BASE + "/stills/g_gift.jpg",
"no": BASE + "/stills/g_no.jpg",
"clock": BASE + "/stills/g_clock.jpg",
"phone": BASE + "/stills/g_phone.jpg",
"think": BASE + "/stills/g_think.jpg",
"real": os.path.expanduser("~/workspace/goals/maki-threads/files/ig_anime/assets/dogs.jpg"),
}
PLAN = {
"B1": [("clip", "sad", 0), ("still", "real"), ("clip", "side", 0), ("still", "real"), ("clip", "listen", 0)],
"C1": [("still", "phone"), ("still", "phone"), ("still", "memo"), ("still", "no"), ("still", "gift")],
"A2": [("clip", "teacher", 0), ("still", "cards5"), ("clip", "pc", 0), ("still", "gift")],
"B2": [("clip", "pc", 0), ("still", "real"), ("still", "think"), ("still", "real"), ("clip", "side", 0)],
"C2": [("clip", "pc", 0), ("still", "memo"), ("clip", "pc", 4), ("clip", "teacher", 0), ("clip", "checklist", 0)],
"A3": [("clip", "teacher", 0), ("still", "memo"), ("clip", "listen", 0), ("clip", "pc", 0), ("still", "gift")],
"B3": [("clip", "side", 0), ("still", "real"), ("clip", "graph", 0), ("still", "real"), ("clip", "duo", 0)],
"C3": [("clip", "graph", 0), ("clip", "duo", 0), ("clip", "graph", 5), ("still", "clock"), ("clip", "teacher", 0)],
}
TELOP = {
"B1": [["なんで僕のリール", "伸びないの…"], ["冒頭3秒、見た？"], ["結論を最初に！"], ["伸びるかは最初の3秒で決まる"], ["みんなは冒頭どうしてる？"]],
"C1": [["伸びないリールは", "AIに診断させる"], ["聞き方は1つだけ"], ["「最初の3秒の", "離脱原因は？」"], ["直すのは3つだけ"], ["聞き方は保存して使って"]],
"A2": [["SNS運用のClaude Skill", "5選"], ["①リサーチ ②台本", "③テロップ ④分析 ⑤記録"], ["毎回の説明がゼロに"], ["「スキル」とコメントで一覧"]],
"B2": [["台本、全部AIでいい？"], ["型はいい。魂はダメ"], ["体験は自分、型はAI"], ["AIは手、体験は心臓"], ["みんなはどこまで任せてる？"]],
"C2": [["AIエージェントに", "台本を作らせた"], ["渡したのは指示書だけ"], ["テーマだけで下書きまで"], ["コツは指示書に型と数字"], ["指示書の中身は次回"]],
"A3": [["Museの使い方", "3選"], ["①指示書を渡す"], ["②覚えさせる"], ["③並行で調べさせる"], ["「指示書」とコメントで例"]],
"B3": [["フォロワー、スタートは87人"], ["数字は小さい。でも本物だ"], ["9本テストで比べるワン"], ["結果は全部出せ"], ["結果は最後に公開"]],
"C3": [["9本テスト、全部出そろった"], ["形式は3つ"], ["比べる数字は4つ"], ["結果編は別で全部出す"], ["次の10本も見届けて"]],
}
CHIPS = {"B1": None, "C1": "gemini", "A2": "claude", "B2": "trio", "C2": "trio",
         "A3": "claude", "B3": None, "C3": "trio"}
BIGCARD = {"B1", "B3"}
INK = (43, 34, 26)
CARD_LINE = (234, 217, 174)
WIN_X, WIN_Y, WIN_S = 80, 900, 920

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(cmd)[:300])
        print(r.stderr[-2500:])
        sys.exit(1)
    return r

def font(fs):
    return ImageFont.truetype(FONT, fs)

def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]

def fit_font(draw, lines, max_w, start, minimum=54):
    fs = start
    while fs > minimum:
        f = font(fs)
        if all(text_w(draw, s, f) <= max_w for s in lines):
            return f, fs
        fs -= 2
    return font(minimum), minimum

def split_line(s):
    for sep in ["、", "。"]:
        if sep in s[1:-1]:
            i = s.index(sep, 1)
            return [s[:i + 1], s[i + 1:]]
    if " " in s[1:-1]:
        parts = s.split(" ")
        mid = len(s) / 2
        acc, best = 0, 1
        for i, p in enumerate(parts[:-1]):
            acc += len(p) + 1
            if abs(acc - mid) < abs(best - mid):
                best = acc
        return [s[:best].rstrip(), s[best:].lstrip()]
    mid = len(s) // 2
    return [s[:mid], s[mid:]]

def maybe_split(lines, draw, max_w, fs):
    if len(lines) != 1:
        return lines
    if text_w(draw, lines[0], font(fs)) <= max_w:
        return lines
    return split_line(lines[0])

# ---------- icons ----------
def make_claude_icon(path, size=420):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = size / 2
    R = size * 0.46
    for i in range(12):
        a = math.radians(i * 30)
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx
        r0, r1 = R * 0.10, R
        w0, w1 = R * 0.16, R * 0.028
        pts = [(cx + dx * r0 + px * w0, cy + dy * r0 + py * w0),
               (cx + dx * r1 + px * w1, cy + dy * r1 + py * w1),
               (cx + dx * r1 - px * w1, cy + dy * r1 - py * w1),
               (cx + dx * r0 - px * w0, cy + dy * r0 - py * w0)]
        d.polygon(pts, fill=(217, 119, 87, 255))
    d.ellipse([cx - R * 0.17, cy - R * 0.17, cx + R * 0.17, cy + R * 0.17], fill=(217, 119, 87, 255))
    img.save(path)

def sparkle_points(cx, cy, R, rot=0.0):
    pts = []
    for k in range(160):
        th = rot + 2 * math.pi * k / 160
        r = R * (0.14 + 0.86 * abs(math.cos(2 * (th - rot))) ** 1.5)
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    return pts


def sparkle_shape(cx, cy, R):
    """Classic 4-point sparkle via quadratic Beziers bowing toward the center."""
    tips = [(cx, cy - R), (cx + R, cy), (cx, cy + R), (cx - R, cy)]
    pts = []
    import math as _m
    for i in range(4):
        x0, y0 = tips[i]
        x1, y1 = tips[(i + 1) % 4]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        # control point pulled toward center (deep concave sides)
        qx = cx + (mx - cx) * 0.16
        qy = cy + (my - cy) * 0.16
        for k in range(25):
            t = k / 25
            bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * qx + t ** 2 * x1
            by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * qy + t ** 2 * y1
            pts.append((bx, by))
    return pts

def make_gemini_icon(path, size=420):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad = Image.new("RGB", (size, size))
    gd = ImageDraw.Draw(grad)
    c_top, c_mid, c_bot = (66, 133, 244), (155, 114, 203), (224, 101, 90)
    for y in range(size):
        t = y / size
        if t < 0.55:
            u = t / 0.55
            c = tuple(int(c_top[i] + (c_mid[i] - c_top[i]) * u) for i in range(3))
        else:
            u = (t - 0.55) / 0.45
            c = tuple(int(c_mid[i] + (c_bot[i] - c_mid[i]) * u) for i in range(3))
        gd.line([(0, y), (size, y)], fill=c)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(sparkle_shape(size / 2, size / 2, size * 0.47), fill=255)
    img.paste(grad, (0, 0), mask)
    img.save(path)

def ensure_icons():
    claude = ASSETS + "/claude.png"
    gemini = ASSETS + "/gemini.png"
    openai = ASSETS + "/openai.png"
    if not os.path.exists(claude):
        make_claude_icon(claude)
    if not os.path.exists(gemini):
        make_gemini_icon(gemini)
    assert os.path.exists(openai) and os.path.getsize(openai) > 5000, "openai icon missing"
    return {"claude": Image.open(claude).convert("RGBA"),
            "gemini": Image.open(gemini).convert("RGBA"),
            "openai": Image.open(openai).convert("RGBA")}

ICONS = ensure_icons()

def make_chip(icon_key, size):
    pad = 26
    canvas = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([pad + 3, pad + 8, pad + size - 3, pad + size + 6], radius=size * 0.24, fill=(90, 70, 40, 90))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([pad, pad, pad + size, pad + size], radius=size * 0.24, fill=(255, 255, 255, 255), outline=(231, 220, 196, 255), width=2)
    isz = int(size * 0.70)
    icon_r = ICONS[icon_key].resize((isz, isz), Image.LANCZOS)
    canvas.alpha_composite(icon_r, (pad + (size - isz) // 2, pad + (size - isz) // 2))
    return canvas

def paste_chip(base, icon_key, size, cx, y):
    chip = make_chip(icon_key, size)
    base.alpha_composite(chip, (int(cx - chip.width / 2), y - 26))

def chip_row(base, kind, size, y):
    if kind == "trio":
        keys = ["openai", "claude", "gemini"]
        gap = 26 if size >= 120 else 22
        total = size * 3 + gap * 2
        x = (W - total) / 2
        for k in keys:
            paste_chip(base, k, size, x + size / 2, y)
            x += size + gap
    else:
        paste_chip(base, kind, size, W / 2, y)

# ---------- background ----------
def gradient_base():
    top, bot = (252, 244, 224), (242, 226, 192)
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    return img.convert("RGBA")

def deco_layer():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for gy in range(40, H, 92):
        off = 46 if (gy // 92) % 2 else 0
        for gx in range(30 + off, W, 92):
            d.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=(226, 199, 148, 30))
    col = (214, 180, 116)
    for (sx, sy, sr, al) in [(64, 520, 26, 46), (1016, 520, 26, 46), (64, 868, 20, 34),
                             (1016, 868, 20, 34), (150, 268, 17, 40), (930, 268, 17, 40)]:
        d.polygon(sparkle_points(sx, sy, sr), fill=col + (al,))
    dx, dy = 58, 596
    d.rounded_rectangle([dx, dy, dx + 44, dy + 58], radius=8, outline=col + (44,), width=4)
    for i in range(3):
        yy = dy + 14 + i * 13
        d.line([(dx + 9, yy), (dx + 35, yy)], fill=col + (44,), width=4)
    d.line([(986, 620), (1022, 584)], fill=col + (40,), width=6)
    d.polygon([(1022, 584), (1030, 606), (1008, 598)], fill=col + (40,))
    return lay

def draw_window_frame(img):
    fx, fy, fw, fh = 68, 888, 944, 944
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([fx + 4, fy + 12, fx + fw + 4, fy + fh + 12], radius=42, fill=(96, 76, 44, 80))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([fx, fy, fx + fw, fy + fh], radius=42, fill=(255, 255, 255, 255), outline=(231, 220, 196, 255), width=2)

def draw_card(img, lines, big=False):
    x0, x1 = 64, 1016
    y0, y1 = (404, 856) if big else (428, 832)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0 + 3, y0 + 9, x1 + 3, y1 + 9], radius=36, fill=(96, 76, 44, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=(255, 255, 255, 255), outline=CARD_LINE, width=2)
    lines2 = maybe_split(lines, d, 872, 88)
    f, fs = fit_font(d, lines2, 872, 92 if big else 88)
    lh = int(fs * 1.34)
    total = lh * len(lines2) - (lh - fs)
    ty = (y0 + y1) / 2 - total / 2
    for s in lines2:
        tw = text_w(d, s, f)
        d.text(((W - tw) / 2, ty), s, font=f, fill=INK)
        ty += lh

def draw_seg0(img, reel, lines):
    d = ImageDraw.Draw(img)
    kind = CHIPS[reel]
    big = reel in BIGCARD
    lines2 = maybe_split(lines, d, 950, 100)
    f, fs = fit_font(d, lines2, 950, 100 if big else 96)
    lh = int(fs * 1.18)
    ty = 118 if len(lines2) > 1 else 140
    for s in lines2:
        tw = text_w(d, s, f)
        d.text(((W - tw) / 2, ty), s, font=f, fill=INK)
        ty += lh
    dd = ImageDraw.Draw(img)
    if kind:
        chip_row(img, kind, 110, 356)
        dd.polygon(sparkle_points(W / 2, 668, 54), fill=(214, 180, 116, 26))
        dd.polygon(sparkle_points(196, 700, 26), fill=(214, 180, 116, 34))
        dd.polygon(sparkle_points(884, 700, 26), fill=(214, 180, 116, 34))
    else:
        dd.polygon(sparkle_points(W / 2, 560, 60), fill=(214, 180, 116, 28))
        dd.polygon(sparkle_points(180, 700, 30), fill=(214, 180, 116, 36))
        dd.polygon(sparkle_points(900, 700, 30), fill=(214, 180, 116, 36))

def build_bg(reel, idx, lines):
    img = gradient_base()
    img.alpha_composite(deco_layer())
    draw_window_frame(img)
    if idx == 0:
        draw_seg0(img, reel, lines)
    else:
        kind = CHIPS[reel]
        if kind:
            if kind == "trio":
                chip_row(img, "trio", 120, 100)
            else:
                paste_chip(img, kind, 150, W / 2, 88)
        draw_card(img, lines, big=(reel in BIGCARD))
    p = "%s/%s_bg%d.png" % (WV2, reel, idx)
    img.convert("RGB").save(p)
    return p

# ---------- segment rendering ----------
MASK = WV2 + "/winmask.png"

def window_mask():
    if os.path.exists(MASK):
        return
    m = Image.new("L", (WIN_S, WIN_S), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, WIN_S, WIN_S], radius=34, fill=255)
    m.save(MASK)

window_mask()

def render_segment(reel, idx, vis, dur, bg):
    out = "%s/%s_v2seg%d.mp4" % (WV2, reel, idx)
    frames = max(1, int(round(dur * 30)))
    frac = 0.12 if (vis[0] == "still" and vis[1] == "real") else 1.0
    crop = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d:(iw-%d)/2:(ih-%d)*%.2f" % (
        WIN_S, WIN_S, WIN_S, WIN_S, WIN_S, WIN_S, frac)
    if vis[0] == "clip":
        src = ["-ss", str(vis[2]), "-i", CLIP[vis[1]]]
        winf = crop + ",fps=30"
    else:
        src = ["-loop", "1", "-i", STILL[vis[1]]]
        winf = crop + (",zoompan=z='min(1+0.00026*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=30" % (frames, WIN_S, WIN_S))
    fc = ("[0:v]%s,format=rgba[win];[2:v]format=gray[msk];[win][msk]alphamerge[winm];"
          "[1:v]format=rgb24[bgv];[bgv][winm]overlay=%d:%d[vout]" % (winf, WIN_X, WIN_Y))
    if idx == 0:
        fc += ("[v];[v]drawtext=fontfile=%s:text='【音声ON推奨】':fontsize=48:fontcolor=yellow:borderw=5:bordercolor=black:"
               "x=(w-text_w)/2:y=28:enable='between(t,0.5,2.5)'[vout]" % FONT)
        # note: label chain fix below
        fc = ("[0:v]%s,format=rgba[win];[2:v]format=gray[msk];[win][msk]alphamerge[winm];"
              "[1:v]format=rgb24[bgv];[bgv][winm]overlay=%d:%d[v];"
              "[v]drawtext=fontfile=%s:text='【音声ON推奨】':fontsize=48:fontcolor=yellow:borderw=5:bordercolor=black:"
              "x=(w-text_w)/2:y=28:enable='between(t,0.5,2.5)'[vout]" % (winf, WIN_X, WIN_Y, FONT))
    cmd = ["ffmpeg", "-y", "-v", "error"] + src + ["-loop", "1", "-i", bg, "-loop", "1", "-i", MASK,
          "-filter_complex", fc, "-map", "[vout]", "-t", str(dur), "-an",
          "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", out]
    run(cmd)
    return out

if __name__ == "__main__":
    durs = json.load(open(BASE + "/audio/durations.json"))
    only = sys.argv[1:] or ["B1", "C1", "A2", "B2", "C2", "A3", "B3", "C3"]
    for reel in only:
        lines = durs[reel]
        plan = PLAN[reel]
        telops = TELOP[reel]
        assert len(lines) == len(plan) == len(telops), reel
        seg_files = []
        for i, (ln, vis, tel) in enumerate(zip(lines, plan, telops)):
            dur = ln["dur"] + (GAP if i < len(lines) - 1 else TAIL)
            bg = build_bg(reel, i, tel)
            seg_files.append(render_segment(reel, i, vis, dur, bg))
            print(reel, "seg", i, "ok", flush=True)
        lst = "%s/%s_v2concat.txt" % (WV2, reel)
        with open(lst, "w") as f:
            for s in seg_files:
                f.write("file '%s'\n" % s)
        silent = "%s/%s_v2silent.mp4" % (WV2, reel)
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
        voice = "%s/%s_voice.wav" % (WORK, reel)
        assert os.path.exists(voice), voice
        final = "%s/%s_v2.mp4" % (OUT, reel)
        run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", voice, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", final])
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final], capture_output=True, text=True)
        print(reel, "DONE", r.stdout.strip(), final, flush=True)
    print("ALL_V2_DONE")
