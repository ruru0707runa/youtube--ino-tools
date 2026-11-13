#!/usr/bin/env python3
import subprocess, os, json, sys

BASE = os.path.expanduser("~/workspace/reel_shiba_test")
WORK = BASE + "/work"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
W, H = 1080, 1920
GAP = 1.0
TAIL = 2.0

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
# visual spec per line: ("clip", key, offset) or ("still", key)
PLAN = {
"A1": [("clip", "teacher", 0), ("clip", "teacher", 4), ("clip", "surprised", 0), ("clip", "teacher", 2), ("clip", "checklist", 0)],
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
"A1": [["投稿作り、Claudeに", "丸投げする3ステップ"], ["①型を渡す"], ["②自分の数字を渡す"], ["③人間は最後に直すだけ"], ["「型」とコメントで", "手順リストを送るワン"]],
"B1": [["なんで僕のリール", "伸びないの…"], ["冒頭3秒、見た？"], ["結論を最初に！"], ["伸びるかは最初の3秒で決まる"], ["みんなは冒頭どうしてる？"]],
"C1": [["伸びないリールは", "AIに診断させる"], ["聞き方は1つだけ"], ["「最初の3秒の", "離脱原因は？」"], ["直すのは3つだけ"], ["聞き方は保存して使って"]],
"A2": [["SNS運用のClaude Skill", "5選"], ["①リサーチ ②台本", "③テロップ ④分析 ⑤記録"], ["毎回の説明がゼロに"], ["「スキル」とコメントで一覧"]],
"B2": [["台本、全部AIでいい？"], ["型はいい。魂はダメ"], ["体験は自分、型はAI"], ["AIは手、体験は心臓"], ["みんなはどこまで任せてる？"]],
"C2": [["AIエージェントに", "台本を作らせた"], ["渡したのは指示書だけ"], ["テーマだけで下書きまで"], ["コツは指示書に型と数字"], ["指示書の中身は次回"]],
"A3": [["Museの使い方", "3選"], ["①指示書を渡す"], ["②覚えさせる"], ["③並行で調べさせる"], ["「指示書」とコメントで例"]],
"B3": [["フォロワー、スタートは87人"], ["数字は小さい。でも本物だ"], ["9本テストで比べるワン"], ["結果は全部出せ"], ["結果は最後に公開"]],
"C3": [["9本テスト、全部出そろった"], ["形式は3つ"], ["比べる数字は4つ"], ["結果編は別で全部出す"], ["次の10本も見届けて"]],
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:]); sys.exit(1)

durs = json.load(open(BASE + "/audio/durations.json"))
sil = WORK + "/sil03.wav"
tail = WORK + "/tail20.wav"
if not os.path.exists(sil):
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(GAP), sil])
if not os.path.exists(tail):
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(TAIL), tail])

only = sys.argv[1:] or list(PLAN.keys())
for reel in only:
    lines = durs[reel]
    plan = PLAN[reel]; telops = TELOP[reel]
    assert len(lines) == len(plan) == len(telops), reel
    seg_files = []
    for i, (ln, vis, tel) in enumerate(zip(lines, plan, telops)):
        dur = ln["dur"] + (GAP if i < len(lines) - 1 else TAIL)
        out = "%s/%s_seg%d.mp4" % (WORK, reel, i)
        vf = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=30" % (W, H, W, H)
        if vis[0] == "still":
            vf = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,zoompan=z='min(zoom+0.0008,1.10)':d=%d:s=%dx%d:fps=30" % (W, H, W, H, int(dur * 30), W, H)
        for j, t in enumerate(tel):
            vf += ",drawtext=fontfile=%s:text='%s':fontsize=64:fontcolor=white:borderw=6:bordercolor=black:x=(w-text_w)/2:y=%d" % (FONT, t, 170 + j * 84)
        if i == 0:
            vf += ",drawtext=fontfile=%s:text='【音声ON推奨】':fontsize=52:fontcolor=yellow:borderw=5:bordercolor=black:x=(w-text_w)/2:y=60:enable='between(t,0.5,2.5)'" % FONT
        if vis[0] == "clip":
            run(["ffmpeg", "-y", "-v", "error", "-ss", str(vis[2]), "-i", CLIP[vis[1]], "-vf", vf, "-t", str(dur), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", out])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", STILL[vis[1]], "-vf", vf, "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", out])
        seg_files.append(out)
    lst = "%s/%s_concat.txt" % (WORK, reel)
    with open(lst, "w") as f:
        for s in seg_files:
            f.write("file '%s'" % s + chr(10))
    silent = "%s/%s_silent.mp4" % (WORK, reel)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    alst = "%s/%s_audio.txt" % (WORK, reel)
    with open(alst, "w") as f:
        for i, ln in enumerate(lines):
            wav = "%s/%s_line%d.wav" % (WORK, reel, i)
            run(["ffmpeg", "-y", "-v", "error", "-i", ln["file"], "-ar", "44100", "-ac", "2", wav])
            f.write("file '%s'" % wav + chr(10))
            if i < len(lines) - 1:
                f.write("file '%s'" % sil + chr(10))
        f.write("file '%s'" % tail + chr(10))
    atrack = "%s/%s_voice.wav" % (WORK, reel)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alst, "-c", "copy", atrack])
    final = "%s/out/%s_final.mp4" % (BASE, reel)
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", atrack, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", final])
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final], capture_output=True, text=True)
    print(reel, "DONE", r.stdout.strip(), final, flush=True)
print("ALL_ASSEMBLED")
