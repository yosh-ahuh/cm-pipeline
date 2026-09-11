import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

GUARD = (" Crisp sharp motion without motion blur. His face stays exactly the same throughout, detailed skin texture with pores and stubble preserved. "
         "He NEVER looks toward the camera, no eye contact with the viewer. "
         "Subtle realistic motion, documentary style, natural muted colors.")

jobs = [
    ("generated/cut02_v4.png", "ad-prototype/public/mirai/cut02_veo.mp4",
     "The tired Japanese man in the night office lowers his hand from his neck, looks at the PC monitor and wearily moves the mouse, organizing photos. He exhales slowly, his shoulders and chest keep breathing naturally. His eyes stay open and steady, gazing at the monitor. Camera slowly pushes in." + GUARD),
    ("generated/cut05_v2.png", "ad-prototype/public/mirai/cut05_veo.mp4",
     "The Japanese man smiles warmly while looking down at his smartphone, taps the screen once as if sending a file, then looks up with relief toward the sky, keeping his gaze away from the camera. Camera slowly pushes in. Dusk light." + GUARD),
    ("generated/cut05b_client_v2.png", "ad-prototype/public/mirai/cut05b_veo.mp4",
     "The Japanese office man looks at the monitor, his eyebrows raise in pleasant surprise, he leans in slightly and nods with an impressed small smile, as if a report arrived much earlier than expected. His gaze stays fixed on the monitor. Camera slowly pushes in." + GUARD),
    ("generated/cut05b_vertical2.png", "ad-prototype/public/mirai/cut05b_v_veo.mp4",
     "The Japanese office man looks at the monitor, his eyebrows raise in pleasant surprise, he leans in slightly and nods with an impressed small smile, as if a report arrived much earlier than expected. His gaze stays fixed on the monitor. Camera slowly pushes in." + GUARD),
]

for src, out, prompt in jobs:
    if os.path.exists(out):
        print("SKIP", out, flush=True)
        continue
    img = base64.b64encode(open(src, 'rb').read()).decode()
    body = json.dumps({
        "prompt": prompt,
        "image_url": f"data:image/png;base64,{img}",
        "duration": "6s",
        "resolution": "1080p",
        "generate_audio": False,
        "negative_prompt": "looking at camera, eye contact, facing the viewer, morphing face, changing face, distortion, motion blur, ghosting, trailing, soft focus, blurry"
    }).encode()
    req = urllib.request.Request(
        "https://fal.run/fal-ai/veo3.1/image-to-video",
        data=body,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.load(r)
        urllib.request.urlretrieve(d["video"]["url"], out)
        print("OK", out, flush=True)
    except urllib.error.HTTPError as e:
        print("ERR", out, e.code, e.read().decode()[:200], flush=True)
    except Exception as e:
        print("ERR", out, repr(e)[:200], flush=True)
print("BATCH DONE", flush=True)
