# Global Eye – auto-posting runbook

Global Eye is a Facebook page (page id `1401152919753922`) that posts important world updates
in **tech, sports, politics and climate/weather**. A scheduled task runs this runbook every 2 hours
(7 AM – 11 PM Pakistan time). Posts go live automatically — there is no human check, so accuracy comes first.

## 1. Setup
- Clone this repo (push access). `git config user.name "Global Eye Bot"; git config user.email noreply@anthropic.com`.
- Read `posted.json` (list of everything already posted).

## 2. Find news
- Use WebSearch (several searches, "extended" mode for fresh news) across: world/politics, tech, sports
  (football, cricket, Olympics, F1, tennis, etc.), climate/weather/disasters.
- Look only at events from the **last ~12 hours** that are not already in `posted.json`
  (compare the story, not just the wording — a follow-up with no real new fact is a repeat).

## 3. Is it important enough?
Post only if **all** are true:
- A big international story many people will care about (major leaders, wars/peace deals, elections results,
  big disasters, huge company/tech news, major sports results/finals/records/transfers, major climate events).
- Confirmed by **at least 2 trusted outlets** (Reuters, AP, BBC, Al Jazeera, CNN, NBC, ABC, Bloomberg,
  The Guardian, ESPN, Cricinfo, official statements). No single-source rumours, no "reportedly" leaks alone.
- Not already posted.

Limits: at most **2 posts per run** and **8 per day** (count today's entries in `posted.json`, PKT date).
If nothing passes, post nothing. That is a normal, good outcome.

## 4. Write the post (simple English)
- **Neutral and factual**, especially politics: no opinions, no taking sides, no insults, no predictions.
  Use "alleged", "accused", "suspected", "reported" correctly. Never call someone guilty without a conviction.
- Do not make up or round numbers you did not see in the sources. Death tolls: say "at least X" and the source.
- Avoid graphic details.
- Caption format:
  ```
  🚨 BREAKING: <headline>        (use "🚨 BREAKING:" only for big news from the last ~6 hours; else a fitting emoji)

  <2-3 sentence summary: what happened, where, when, who>

  🔹 <key fact>
  🔹 <key fact>
  🔹 <why it matters / what happens next — only facts>

  💬 <one simple question for comments> 👇

  Sources: <outlet 1>, <outlet 2>

  #GlobalEye #<topic> #<names> ... (4-7 hashtags)
  ```

## 5. Make the picture (style: Split — always)
```
python3 render_post.py --category <tech|sports|politics|climate|world> [--breaking] \
  --headline "Short headline with 1-3 [key words] in brackets" \
  --sub "One short extra line" --emoji "<one emoji that fits the story>" \
  --out posts/<YYYY-MM-DD>-<slug>.jpg
```
- Headline: max ~9 words, punchy, true. Sub line: max ~8 words.
- Emoji ideas: ⚽ 🏏 🏆 🎾 🏎️ 💻 🤖 📱 🚀 🏛️ 🗳️ 🤝 🕊️ 🌍 🌪️ 🌊 🔥 🌡️ ⛈️ 💰 📉 📈 ✈️.
  Never use flags or symbols that look like taking a side. Avoid weapons/blood.
- Open the image with the Read tool and check it looks right (text fits, nothing overlaps).

## 6. Publish
1. `git add posts/... && git commit && git push` (pull --rebase first).
2. Wait ~10 s, check `https://raw.githubusercontent.com/dogar5954786-ship-it/global-eye/main/posts/<file>` returns 200.
3. Zapier → Facebook Pages "Create Page Post" (`selected_api` FacebookV2CLIAPI, action `page_stream`,
   tool_name `facebook_pages_create_page_post`) with params:
   `page` = `1401152919753922`, `message` = caption, `source` = [raw image URL], `save_as_draft` = "false".
4. Append to `posted.json`: `{"date": "<PKT date-time>", "headline", "category", "image", "fb_post_id", "sources": [urls]}`.
   Commit + push.

## 7. Errors
- If Facebook posting fails, retry once. If it still fails, do not keep retrying; note it in the final message.
- Never delete posts or files.
