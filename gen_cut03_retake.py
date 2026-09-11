import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

out = "ad-prototype/public/mirai/cut03_v3.mp4"
if not os.path.exists(out):
    img = base64.b64encode(open("generated/cut03_v2.png", 'rb').read()).decode()
    body = json.dumps({
        "prompt": "Locked-off tripod shot, completely stable camera with no shake and no handheld movement, only an extremely slow gentle push in. The Japanese construction supervisor steadies his smartphone and taps the shutter once, then gives a small satisfied nod looking at the screen. His face stays exactly the same throughout. Documentary style, natural subtle motion.",
        "image_url": f"data:image/png;base64,{img}",
        "duration": "5",
        "negative_prompt": "camera shake, handheld wobble, shaky footage, blur, distortion, low quality, extra fingers, morphing face, changing face, oversaturated"
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
        print("OK", flush=True)
    except Exception as e:
        print("ERR", repr(e)[:300], flush=True)
else:
    print("SKIP", flush=True)
