import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

img = base64.b64encode(open("generated/cut02_v4.png", 'rb').read()).decode()
body = json.dumps({
    "prompt": "The tired Japanese man lowers his hand from his neck, looks at the PC monitor and wearily moves the mouse. He exhales slowly. Camera slowly pushes in. His face stays exactly the same throughout. Documentary style, muted colors, subtle realistic motion.",
    "image_url": f"data:image/png;base64,{img}",
    "duration": "5",
    "negative_prompt": "blur, distortion, low quality, extra fingers, morphing face, changing face, changing clothes, oversaturated, text appearing"
}).encode()
req = urllib.request.Request(
    "https://fal.run/fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    data=body,
    headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=560) as r:
        d = json.load(r)
    urllib.request.urlretrieve(d["video"]["url"], "ad-prototype/public/mirai/cut02_v4.mp4")
    print("OK", flush=True)
except Exception as e:
    print("ERR", repr(e)[:300], flush=True)
