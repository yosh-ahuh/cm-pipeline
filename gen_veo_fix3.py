import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

GUARD = (" Crisp sharp motion without motion blur, high detail. Documentary style, natural muted colors.")
FACE = (" His face stays exactly the same throughout, detailed skin texture preserved. "
        "He NEVER looks toward the camera.")

jobs = [
    ("generated/cut01_imagen4.png", "ad-prototype/public/mirai/cut01_veo.mp4",
     "The van is PARKED and completely stationary, engine off, the scenery outside the windows does NOT move or "
     "scroll. The tired Japanese construction supervisor keeps his eyes closed and exhales a deep weary sigh, "
     "shoulders dropping, then slowly half-opens his eyes and looks DOWN at the documents on the passenger seat, "
     "gaze staying low. LIGHT DESIGN: soft overcast daylight through the windshield, a gentle sheen on the dashboard, "
     "soft catchlight in his eyes. LIVING WORLD (outside the parked van only): roadside trees sway gently in the "
     "wind, one distant car passes by on the road, light shifts subtly as clouds move. Camera slowly pushes in."
     + FACE + GUARD),
    ("generated/cut02_hd2.png", "ad-prototype/public/mirai/cut02_veo.mp4",
     "The tired Japanese man in the night office lowers his hand from his neck, looks at the PC monitor and wearily "
     "turns pages of construction photo prints. His chest keeps breathing. LIGHT DESIGN: the warm desk lamp and cool "
     "monitor glow cross-light his face, catchlight in his eyes, warm sheen on the desk, prints and camera body. "
     "LIVING WORLD: papers shift slightly, steam rises faintly from the cup, the lamp light breathes very subtly. "
     "Camera slowly pushes in." + FACE + GUARD),
    ("generated/papers_hd2.png", "ad-prototype/public/mirai/papers_veo.mp4",
     "The dozens of white documents and construction photo prints tumble and fall slowly through the air, each sheet "
     "rotating gently and catching the warm lamp light and cool monitor glow on its edges as it falls, papers "
     "drifting downward like leaves, a few new sheets entering from the top. The room stays still, only the papers "
     "move. Camera pushes in very slowly." + GUARD),
]

for srcimg, out, prompt in jobs:
    if os.path.exists(out + ".done3"):
        print("SKIP", out, flush=True)
        continue
    img = base64.b64encode(open(srcimg, 'rb').read()).decode()
    body = json.dumps({
        "prompt": prompt,
        "image_url": f"data:image/png;base64,{img}",
        "duration": "6s",
        "resolution": "1080p",
        "generate_audio": False,
        "negative_prompt": "looking at camera, eye contact, morphing face, changing face, distortion, motion blur, "
                           "ghosting, trailing, soft focus, blurry, driving, moving vehicle, scrolling background, "
                           "strings, wires"
    }).encode()
    req = urllib.request.Request("https://fal.run/fal-ai/veo3.1/image-to-video", data=body,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.load(r)
        urllib.request.urlretrieve(d["video"]["url"], out)
        open(out + ".done3", "w").write("1")
        print("OK", out, flush=True)
    except Exception as e:
        msg = ""
        if hasattr(e, 'read'):
            try:
                msg = e.read().decode()[:200]
            except Exception:
                pass
        print("ERR", out, repr(e)[:120], msg, flush=True)
print("BATCH DONE", flush=True)
