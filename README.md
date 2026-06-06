# GlitchGrowth Content Agent

A local-first Streamlit app that generates actual ready-to-use social media content for a tech-meme / AI-news / chaotic girl-in-tech creator brand.

This app is **not** an Instagram bot. It does not auto-like, auto-follow, scrape, mass-DM, or fake engagement. It creates content packets that a human reviews and posts manually.

## What it creates

- meme posts
- captions
- hashtags
- CTAs
- carousel slide copy
- Reel scripts
- Story packs
- product promo posts
- weekly content batches
- lead / DM reply drafts
- compliance reminders for affiliate, sponsored, gifted, or paid content

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run smoke checks

```bash
python scripts/smoke_test.py
pytest
```

## First monetization offer to test

Start with a small product:

**Chaotic Tech Creator Kit**

Suggested price: `$9-$19`

Includes:
- tech meme prompts
- caption templates
- CTA templates
- carousel structures
- AI workflow prompts
- weekly content calendar
- basic analytics tracker

## Offer Lab / manual launch workflow

Use Offer Lab to define what you are selling before you make launch content:

1. Define the offer, audience, pain point, promise, deliverables, format, price, and CTA keyword.
2. Generate a launch pack with launch posts, story slides, comment CTAs, DM reply templates, FAQ, objections, and a first-week manual posting plan.
3. Optionally save the launch posts to the Content Library.
4. Add saved posts to the Posting Queue when they are ready.
5. Post manually from your own social accounts.
6. Track comments, DMs, saves, profile visits, link clicks, and sales manually.

Offer Lab stores offers locally in `data/offers.json`. It does not connect to checkout tools, scrape social platforms, post content, or automate engagement.

## Safe operating rules

- Human approves all posts and DMs.
- No scraping.
- No mass-DM automation.
- No fake engagement.
- Clearly disclose affiliate links, sponsorships, gifted products, and paid partnerships.
