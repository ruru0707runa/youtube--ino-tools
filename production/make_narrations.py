#!/usr/bin/env python3
import subprocess, os, json, sys

BASE = os.path.expanduser("~/workspace/reel_shiba_test")
ADIR = BASE + "/audio"
os.makedirs(ADIR, exist_ok=True)
CHILD = "avocado_v2:vdc_11859"
ADULT = "avocado_v2:MAI_03"

LINES = {
 "A1": [("C", "投稿作りは、クロードに丸投げできます。ステップは3つだけ。"),
        ("C", "1つ目、伸びた投稿の型を貼って、型だけ真似してと頼む。"),
        ("C", "2つ目、自分の再生数と反応を渡す。数字があると、台本が自分用になります。"),
        ("C", "3つ目、出てきた案を自分が最後に直す。考えるのはAI、決めるのは人間です。"),
        ("C", "手順リストが欲しい人は、型、とコメントしてね。")],
 "B1": [("C", "先輩、僕のリール、全然伸びないワン。"),
        ("A", "冒頭3秒、自分の顔しか映ってないだろ。結論を先に言え。"),
        ("C", "結論を最初に。じゃあ次は、一番言いたいことを最初の3秒に入れるワン。"),
        ("A", "それだ。伸びるかどうかは、最初の3秒でほぼ決まる。"),
        ("C", "みんなは冒頭、どう作ってる？コメントで教えてワン。")],
 "C1": [("C", "伸びないリールは、AIに診断させると早いよ。"),
        ("C", "やり方は、リールをジェミニに送って、こう聞くだけ。"),
        ("C", "最初の3秒で、見るのをやめたくなる原因を教えて。"),
        ("C", "返ってきた指摘から、直すのは3つだけ。背景、動き、タイトル。"),
        ("C", "全部直す必要はないんだ。聞き方はキャプションに置いたから、保存して使ってね。")],
 "A2": [("C", "SNS運用で本当に使う、クロードのスキルを5つ紹介します。"),
        ("C", "リサーチ、台本、テロップ、分析、記録。"),
        ("C", "この5つをスキルにしておくと、毎回の説明がゼロになります。"),
        ("C", "5つの一覧が欲しい人は、スキル、とコメントしてね。")],
 "B2": [("C", "先輩、台本は全部AIに書かせていいワン？"),
        ("A", "型は任せていい。でも、自分の実体験まで任せたら、誰の発信か分からなくなるぞ。"),
        ("C", "体験は自分、型と清書はAI。それなら量も出せて、自分らしさも残るワン。"),
        ("A", "その分け方が正解だ。AIは手、体験は心臓。"),
        ("C", "みんなはどこまでAIに任せてる？コメントで教えてワン。")],
 "C2": [("C", "ミューズっていうAIエージェントに、リールの台本を作らせてみました。"),
        ("C", "渡したのは、型と数字が入った指示書だけ。"),
        ("C", "テーマを言うだけで、下書きまで返ってきます。"),
        ("C", "コツは、指示書に型と自分の数字を入れておくこと。これがエージェント活用の本体です。"),
        ("C", "指示書の中身は次回出すから、フォローして待っててね。")],
 "A3": [("C", "AIエージェント、ミューズの使い方を3つだけ紹介します。"),
        ("C", "1つ目、毎回説明する代わりに、指示書を先に渡しておく。"),
        ("C", "2つ目、自分の数字と決めたことを覚えさせる。だから続きから話せます。"),
        ("C", "3つ目、リサーチみたいな重い作業は並行で調べさせる。自分は判断に集中できます。"),
        ("C", "指示書の例が欲しい人は、指示書、とコメントしてね。")],
 "B3": [("C", "先輩、正直に言うワン。スタートはフォロワー87人。"),
        ("A", "小さいな。でも、その87は本物だ。盛った数字より価値がある。"),
        ("C", "だから今、形式を3つに分けて9本でテストしてるワン。どれが伸びるか、数字で決める。"),
        ("A", "結果は全部出せ。失敗も含めてな。それが一番の一次情報になる。"),
        ("C", "結果はこのシリーズの最後に全部出すワン。見届けてね。")],
 "C3": [("C", "9本のリールテスト、今日で全部出そろいます。"),
        ("C", "形式は3つ。キャラ解説、掛け合い、実証。"),
        ("C", "比べるのは、フォロワー増、保存、シェア、プロフィール遷移。"),
        ("C", "数字の結果編は、全投稿の反応が出そろってから、別で全部出します。"),
        ("C", "次の10本も見届けてくれる人は、フォローしてね。")],
}

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())

result = {}
for reel, lines in LINES.items():
    result[reel] = []
    for i, (spk, text) in enumerate(lines):
        raw = "%s/%s_%d_raw.mp3" % (ADIR, reel, i)
        out = "%s/%s_%d.mp3" % (ADIR, reel, i)
        if not os.path.exists(out):
            voice = CHILD if spk == "C" else ADULT
            r = subprocess.run(["/opt/hatch/bin/tts", "speak", "--output", raw,
                                "--language", "ja", "--voice", voice, "--text-stdin"],
                               input=text, capture_output=True, text=True)
            if r.returncode != 0:
                print("TTS FAIL", reel, i, r.stdout[-300:], r.stderr[-300:]); sys.exit(1)
            if spk == "C":
                # child pitch: raise pitch 15%, keep duration
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw,
                                "-af", "asetrate=44100*1.15,aresample=44100,atempo=0.8696",
                                out], check=True)
            else:
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-c", "copy", out], check=True)
        d = dur(out)
        result[reel].append({"spk": spk, "text": text, "dur": round(d, 2), "file": out})
        print(reel, i, spk, round(d, 2), flush=True)

json.dump(result, open(BASE + "/audio/durations.json", "w"), ensure_ascii=False, indent=1)
print("ALL_DONE")
