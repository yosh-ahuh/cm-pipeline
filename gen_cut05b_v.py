import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

out = "ad-prototype/public/mirai/cut05b_v.mp4"
if not os.path.exists(out):
    img = base64.b64encode(open("generated/cut05b_vertical2.png", 'rb').read()).decode()
    body = json.dumps({
        "prompt": "The Japanese office man looks at the monitor, his eyebrows raise in pleasant surprise, he leans in slightly and nods with an impressed small smile, as if a report arrived much earlier than expected. Camera slowly pushes in. His face stays exactly the same throughout. Documentary style, muted colors, subtle realistic motion.",
        "image_url": f"data:image/png;base64,{img}",
        "duration": "5",
        "negative_prompt": "blur, distortion, low quality, extra fingers, morphing face, changing face, oversaturated, text"
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
