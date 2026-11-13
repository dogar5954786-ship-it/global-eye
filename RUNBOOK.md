# Global Eye – auto-posting runbook (photo workflow)

Global Eye is a Facebook page (page id `1401152919753922`) that posts important world updates in
**tech, sports, politics and climate/weather**. A scheduled task runs this runbook **every hour, 7 AM – 11 PM
Pakistan time (PKT, UTC+5)** to find news and email photo requests. Every post has a big real photo of the main person / company / place.
Claude never downloads photos of people from the web: **Abdullah supplies every photo** by uploading it to
`inbox/<slug>/` in this repo. The bot does everything else.

Files:
- `pending.json` – stories waiting for a photo.
- `posted.json` – everything already posted (or expired).
- `inbox/<slug>/` – Abdullah's photo for that story (any image file; jpg/png/webp).
- `posts/` – final pictures that were published.

## 0. Setup
Clone this repo (push access). `git config user.name "Global Eye Bot"; git config user.email noreply@anthropic.com`.
Always `git pull --rebase` before changing files; commit + push after each step.

## 1. Publish ready stories (do this FIRST, every run)
When Abdullah uploads a photo to `inbox/<slug>/`, the GitHub workflow `.github/workflows/publish.yml` runs
`publish_ready.py`: it renders `posts/<slug>.jpg` and sets the story in `pending.json` to `"status": "ready"`
(with `image` and `image_url`). This bot posts it:
- Safety net first: if a pending story has a photo in `inbox/<slug>/` but is not `ready` (workflow failed), run
  `python3 publish_ready.py`, then commit + push.
- For every `ready` story:
  1. Open `posts/<slug>.jpg` with the Read tool. Check the main subject is visible and the text fits. If badly cropped,
     re-render with a better `--focus` (see section 5), push, and use the new picture.
  2. Check the raw URL returns 200 (wait ~10 s after a push).
  3. Post with Zapier → Facebook Pages "Create Page Post" (`selected_api` FacebookV2CLIAPI, action `page_stream`,
     tool_name `facebook_pages_create_page_post`): `page` = `1401152919753922`, `message` = caption,
     `source` = [image_url], `save_as_draft` = "false".
  4. Move the story from `pending.json` to `posted.json` with `"status": "posted"`, `fb_post_id`, `posted` time (PKT).
     Commit + push right after each post (so it is never posted twice).
  5. Reply in the story's email thread: "[Global Eye bot] Posted: <headline>".
- If Facebook says the login/session is invalid: do not retry; email Abdullah once (subject "Global Eye - Facebook
  needs reconnecting") with the link https://zapier.com/app/connections and keep the story `ready`.
- A story with no photo older than **8 hours**: move it to `posted.json` with `"status": "expired"`. No email.
- A `ready` story older than **10 hours** (from `created`): the news is stale; mark `"status": "expired"` instead of posting.
- Story fields: `slug, headline, category, breaking, caption, focus` (focus 0-1, default 0.3; ~0.2 for portraits).

## 2. Find news (only on even hours: 8, 10, 12 ... 22 PKT, and on the first run of the day)
- WebSearch ("extended" mode for fresh news): world/politics, tech, sports (football, cricket, Olympics, F1, tennis...),
  climate/weather/disasters.
- Only events from the **last ~12 hours** that are not already in `posted.json` or `pending.json`
  (compare the story, not just wording; a follow-up with no real new fact is a repeat).

## 3. Is it important enough?
Only if **all** are true:
- A big international story many people will care about.
- Confirmed by **at least 2 trusted outlets** (Reuters, AP, BBC, Al Jazeera, CNN, NBC, ABC, Bloomberg, The Guardian,
  ESPN, Cricinfo, official statements). No single-source rumours.
- Not already posted or pending.
Limits: at most **2 new stories per run** and **8 per day** (posted + pending, PKT date). If nothing passes, do nothing.

## 4. Prepare the story and ask Abdullah for the photo
- slug: `<YYYY-MM-DD>-<short-words>`.
- Write: headline in the Startup-Pakistan style: a short hook first, then the facts, max ~14 words, e.g.
  "[Big Shake-Up!] Nvidia CEO Jensen Huang Resigns After [33 Years]". Put the hook and the key number/name in
  [brackets] (they get colour blocks; max 2-3 bracketed parts). Title Case. Hook must be true, not clickbait.
  Then: sub line (max ~8 words), category, breaking yes/no,
  full caption (format below), and **photo_needed** = exactly what the photo should show
  (e.g. "Jensen Huang, face clearly visible" / "Nvidia headquarters or logo sign" / "Pakistan team celebrating").
- Create `inbox/<slug>/README.md` with the photo_needed text (so the folder exists for uploading).
- Render a preview with the placeholder (no --photo) to `posts/preview-<slug>.jpg`.
- Add to `pending.json`: `{slug, created (PKT), headline, sub, category, breaking, caption, photo_needed, sources: [urls],
  email_thread_id}`. Commit + push.
- Gmail via Zapier, Send Email (`selected_api` GoogleMailV2CLIAPI, action `message`, tool_name `gmail_send_email`),
  to `dogar5954786@gmail.com`, body_type plain, subject `Global Eye - photo needed: <headline without brackets>`:
  ```
  [Global Eye bot]
  New story ready to post on Global Eye.

  HEADLINE: <headline>
  PHOTO NEEDED: <photo_needed>
  Tip: a big, clear, landscape photo works best (from the official website, a press kit, or a news article).

  UPLOAD THE PHOTO HERE (tap, choose the photo, press "Commit changes"):
  https://github.com/dogar5954786-ship-it/global-eye/upload/main/inbox/<slug>
  (Optional: type the photo credit, e.g. "Reuters", in the commit message box.)

  The post goes live on Facebook within about 1 hour after you upload. If no photo arrives within 8 hours, the story is skipped.

  Preview (with empty photo space):
  https://raw.githubusercontent.com/dogar5954786-ship-it/global-eye/main/posts/preview-<slug>.jpg

  CAPTION:
  <caption>
  ```
  Save the email's thread id in the pending entry.

## Caption rules (simple English)
- **Neutral and factual**, especially politics: no opinions, no sides, no insults, no predictions.
  Use "alleged", "accused", "suspected", "reported" correctly. Never call someone guilty without a conviction.
- Never invent or round numbers. Death tolls: "at least X", per the source. No graphic details.
- Format:
  ```
  🚨 BREAKING: <headline>        (only for big news from the last ~6 hours; else a fitting emoji)

  <2-3 sentence summary: what, where, when, who>

  🔹 <key fact>
  🔹 <key fact>
  🔹 <why it matters / what happens next — facts only>

  💬 <one simple question for comments> 👇

  Sources: <outlet 1>, <outlet 2>

  #GlobalEye #<topic> #<names> (4-7 hashtags)
  ```

## 5. Re-rendering a picture
```
python3 render_post.py --style photo --category <tech|sports|politics|climate|world> [--breaking] \
  --headline "<headline with [key words]>" \
  --photo inbox/<slug>/<file> [--focus 0.0-1.0] [--credit "<credit>"] \
  --out posts/<slug>.jpg
```
- `--focus`: which part of the photo to keep when cropping (0 = top, 1 = bottom; default 0.3 keeps faces).
- Open the picture with the Read tool. Check: the main subject is visible and not covered by the headline, text fits,
  nothing overlaps. Adjust `--focus` and re-render if needed. If the uploaded file is not a usable photo, do not post;
  reply in the email thread asking for another photo (once).
- Keep the JPEG under 4 MB.
- Commit + push, then post as in section 1.

## 6. Errors
- Facebook post fails → retry once (unless it is a login/session error, see section 1); then keep the entry `ready` and note the error in the final message.
- Never delete Facebook posts, photos in inbox, or git history.
