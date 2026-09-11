import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

jobs = [
    ("cut03_v2.png", "cut03_v2.mp4",
     "The Japanese construction supervisor steadies his smartphone and taps the shutter once, then gives a small satisfied nod looking at the screen. Camera slowly pushes in. His face stays exactly the same throughout. Documentary style, natural motion."),
    ("cut05_v2.png", "cut05_v2.mp4",
     "The Japanese man smiles warmly while looking at his smartphone, taps the screen once as if sending a file, then looks up with relief. Camera slowly pushes in. His face stays exactly the same throughout. Dusk light, documentary style, natural motion."),
]

for src, dst, prompt in jobs:
    out = f"ad-prototype/public/mirai/{dst}"
    if os.path.exists(out):
        print("SKIP", dst, flush=True)
        continue
    img = base64.b64encode(open(f"generated/{src}", 'rb').read()).decode()
    body = json.dumps({
        "prompt": prompt,
        "image_url": f"data:image/png;base64,{img}",
        "duration": "5",
        "negative_prompt": "blur, distortion, low quality, extra fingers, morphing face, changing face, changing clothes, oversaturated"
    }).encode()
    req = urllib.request.Request(
        "https://fal.run/fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
        data=body,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.load(r)
        urllib.request.urlretrieve(d["video"]["url"], out)
        print("OK", dst, flush=True)
    except Exception as e:
        print("ERR", dst, repr(e)[:300], flush=True)
