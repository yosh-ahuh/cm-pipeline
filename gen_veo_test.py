import base64, json, urllib.request, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
key = open('.fal_key').read().strip()

out = "generated/cut01_veo.mp4"
if os.path.exists(out):
    print("SKIP", flush=True)
    raise SystemExit

img = base64.b64encode(open("generated/cut01_imagen4.png", 'rb').read()).decode()
prompt = ("The tired Japanese construction supervisor exhales a deep weary sigh, his shoulders drop slightly, "
          "then he slowly opens his eyes and glances down at the pile of documents and the digital camera "
          "on the passenger seat. Camera slowly pushes in. Subtle realistic motion, documentary style, "
          "natural muted colors.")

for endpoint, body in [
    ("fal-ai/veo3.1/image-to-video",
     {"prompt": prompt, "image_url": f"data:image/png;base64,{img}", "duration": "6s", "generate_audio": False}),
    ("fal-ai/veo3.1/image-to-video",
     {"prompt": prompt, "image_url": f"data:image/png;base64,{img}"}),
    ("fal-ai/veo3/image-to-video",
     {"prompt": prompt, "image_url": f"data:image/png;base64,{img}"}),
]:
    req = urllib.request.Request(
        f"https://fal.run/{endpoint}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=560) as r:
            d = json.load(r)
        url = d.get("video", {}).get("url")
        if url:
            urllib.request.urlretrieve(url, out)
            print("OK", endpoint, flush=True)
            break
    except urllib.error.HTTPError as e:
        print("ERR", endpoint, e.code, e.read().decode()[:200], flush=True)
    except Exception as e:
        print("ERR", endpoint, repr(e)[:200], flush=True)
