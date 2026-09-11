import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

jobs = [
    ("cut01_v2.mp4", "cut01_sfx.mp4",
     "quiet van interior ambience, a tired middle-aged man exhales a deep audible sigh, faint distant traffic, subtle cloth rustle, no music"),
    ("cut02_v4.mp4", "cut02_sfx.mp4",
     "quiet office at night, faint fluorescent light hum, mouse clicks, paper documents rustling and shifting, a weary sigh, no music"),
    ("cut03_v2.mp4", "cut03_sfx.mp4",
     "outdoor construction site ambience, distant machinery and clanking, light wind, a smartphone camera shutter click, no music"),
    ("cut05_v2.mp4", "cut05_sfx.mp4",
     "outdoor evening ambience, light breeze, a soft smartphone tap sound, a relieved short exhale, distant site sounds, no music"),
]

for src, dst, prompt in jobs:
    out = f"ad-prototype/public/mirai/{dst}"
    if os.path.exists(out):
        print("SKIP", dst, flush=True)
        continue
    vid = base64.b64encode(open(f"ad-prototype/public/mirai/{src}", 'rb').read()).decode()
    body = json.dumps({
        "video_url": f"data:video/mp4;base64,{vid}",
        "prompt": prompt,
        "negative_prompt": "music, melody, speech, voice, talking",
    }).encode()
    req = urllib.request.Request(
        "https://fal.run/fal-ai/mmaudio-v2",
        data=body,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.load(r)
        url = d.get("video", {}).get("url") or d.get("audio", {}).get("url")
        urllib.request.urlretrieve(url, out)
        print("OK", dst, flush=True)
    except Exception as e:
        print("ERR", dst, repr(e)[:300], flush=True)
