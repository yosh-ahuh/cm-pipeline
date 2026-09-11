import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

out = "ad-prototype/public/mirai/papers_bg.mp4"
if not os.path.exists(out):
    img = base64.b64encode(open("generated/papers_bg.png", 'rb').read()).decode()
    body = json.dumps({
        "prompt": "The documents and photos slowly fall and drift through the dark office air in slow motion, gently rotating and tumbling, camera slowly pushes in, moody cinematic atmosphere stays constant, no people.",
        "image_url": f"data:image/png;base64,{img}",
        "duration": "5",
        "negative_prompt": "blur, distortion, low quality, oversaturated, people, hands, text"
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
