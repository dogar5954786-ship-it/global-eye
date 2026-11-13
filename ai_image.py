#!/usr/bin/env python3
"""Make an AI background picture for a story.

Uses Google Gemini if the GEMINI_API_KEY secret is set (paid, best quality),
otherwise the free Pollinations.ai service.

Usage: python3 ai_image.py "<prompt>" out.jpg [seed]
"""
import base64, json, os, sys, time, urllib.parse, urllib.request

STYLE = (" Photorealistic editorial news photo, cinematic lighting, sharp focus, rich colour, "
         "portrait 4:5 framing with the main subject in the upper-middle part of the frame. "
         "Absolutely no text, no letters, no watermarks, no logos, no flags.")


def gemini(prompt, out, key):
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-2.5-flash-image:generateContent?key=" + key)
    body = {"contents": [{"parts": [{"text": prompt + STYLE}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "4:5"}}}
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req, timeout=120))
    for p in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            open(out, "wb").write(base64.b64decode(p["inlineData"]["data"]))
            return True
    raise RuntimeError("no image in Gemini answer")


def pollinations(prompt, out, seed):
    q = urllib.parse.quote(prompt + STYLE)
    url = f"https://image.pollinations.ai/prompt/{q}?width=1080&height=1350&nologo=true&model=flux&seed={seed}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GlobalEyeBot/1.0"})
            data = urllib.request.urlopen(req, timeout=180).read()
            if len(data) > 20000:
                open(out, "wb").write(data)
                return True
        except Exception as e:
            print("pollinations attempt", attempt + 1, "failed:", e)
        time.sleep(15)
    raise RuntimeError("Pollinations failed")


def main():
    prompt, out = sys.argv[1], sys.argv[2]
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        try:
            gemini(prompt, out, key)
            print("made with gemini")
            return
        except Exception as e:
            print("gemini failed, using pollinations:", e)
    pollinations(prompt, out, seed)
    print("made with pollinations")


if __name__ == "__main__":
    main()
