import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

GUARD = (" Crisp sharp motion without motion blur, high detail. His face stays exactly the same throughout, "
         "detailed skin texture preserved. He NEVER looks toward the camera. Documentary style, natural muted colors.")

jobs = [
    ("generated/cut02_hd.png", "ad-prototype/public/mirai/cut02_veo.mp4",
     "The tired Japanese man in the dark night office lowers his hand from his neck, looks at the PC monitor and "
     "wearily turns pages of construction photo prints. His chest keeps breathing. LIGHT DESIGN: the monitor glow is "
     "the key light, flickering subtly on his face and creating a soft catchlight in his eyes; the desk surface and "
     "camera body catch a faint sheen from the screen; the wall clock glass glints faintly. LIVING WORLD: papers on "
     "the desk shift slightly, steam rises faintly from the coffee cup, shadows breathe with the monitor light. "
     "Camera slowly pushes in." + GUARD),
    ("generated/cut01_imagen4.png", "ad-prototype/public/mirai/cut01_veo.mp4",
     "The tired Japanese construction supervisor keeps his eyes closed and exhales a deep weary sigh, shoulders "
     "dropping, then slowly half-opens his eyes and looks DOWN at the documents on the passenger seat, gaze staying "
     "low the entire time. LIGHT DESIGN: soft overcast daylight through the windshield from front-left, a gentle "
     "sheen moving across the dashboard, soft catchlight in his eyes, the white papers catching window light. "
     "LIVING WORLD: outside the window a distant car passes and roadside trees sway gently, light shifts subtly as "
     "clouds move. Camera slowly pushes in." + GUARD),
    ("generated/cut05_v2.png", "ad-prototype/public/mirai/cut05_veo.mp4",
     "The Japanese man smiles warmly looking down at his smartphone, taps the screen once as if sending a file, then "
     "looks up with relief toward the sky, gaze away from the camera. LIGHT DESIGN: low warm dusk sun from the west "
     "gives a soft rim light on his hair and shoulder, warm reflections glow softly on the white van panel, the phone "
     "screen lights his face faintly from below. LIVING WORLD: clouds drift slowly in the dusk sky, a light breeze "
     "moves his collar, distant site lights begin to glow. Camera slowly pushes in." + GUARD),
    ("generated/cut05b_client_v2.png", "ad-prototype/public/mirai/cut05b_veo.mp4",
     "The Japanese office man looks at the monitor, eyebrows raising in pleasant surprise, leaning in slightly and "
     "nodding with an impressed small smile, gaze fixed on the monitor. LIGHT DESIGN: soft daylight from the window "
     "blinds falls in gentle stripes across the desk, a soft sheen on the monitor bezel and desk surface, catchlight "
     "in his eyes. LIVING WORLD: a colleague walks past in the blurred background, the blind light shifts faintly, "
     "the phone cord sways slightly. Camera slowly pushes in." + GUARD),
    ("generated/cut05b_vertical2.png", "ad-prototype/public/mirai/cut05b_v_veo.mp4",
     "The Japanese office man looks at the monitor, eyebrows raising in pleasant surprise, leaning in slightly and "
     "nodding with an impressed small smile, gaze fixed on the monitor. LIGHT DESIGN: soft daylight from the window "
     "falls across the desk, a soft sheen on the monitor bezel, catchlight in his eyes. LIVING WORLD: a colleague "
     "walks past in the blurred background, the window light shifts faintly. Camera slowly pushes in." + GUARD),
]

for srcimg, out, prompt in jobs:
    if os.path.exists(out + ".done"):
        print("SKIP", out, flush=True)
        continue
    img = base64.b64encode(open(srcimg, 'rb').read()).decode()
    body = json.dumps({
        "prompt": prompt,
        "image_url": f"data:image/png;base64,{img}",
        "duration": "6s",
        "resolution": "1080p",
        "generate_audio": False,
        "negative_prompt": "looking at camera, eye contact, morphing face, changing face, distortion, motion blur, ghosting, trailing, soft focus, blurry"
    }).encode()
    req = urllib.request.Request("https://fal.run/fal-ai/veo3.1/image-to-video", data=body,
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.load(r)
        urllib.request.urlretrieve(d["video"]["url"], out)
        open(out + ".done", "w").write("1")
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
