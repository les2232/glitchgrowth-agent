import csv
import io
import json
from pathlib import Path

import streamlit as st

from agent_mode import run_weekly_agent_mode
from analytics_engine import analyze_post_metrics
from brand_voice import DEFAULT_BRAND_VOICE, load_brand_voice, save_brand_voice
from compliance_engine import check_compliance
from content_engine import (
    generate_carousel,
    generate_meme_post,
    generate_product_promo,
    generate_reel,
    generate_story_pack,
    generate_weekly_batch,
)
from export_utils import save_packet, save_weekly_batch
from lead_engine import classify_messages
from library_engine import load_library, save_to_library, search_library, update_library_item
from offer_lab_engine import (
    OFFER_FORMATS,
    OFFER_STATUSES,
    archive_offer,
    generate_launch_pack,
    load_offers,
    save_offer,
    search_offers,
    update_offer,
)
from quality_engine import score_content
from queue_engine import (
    QUEUE_STATUSES,
    add_to_queue,
    load_queue,
    remove_from_queue,
    search_queue,
    update_queue_item,
)
from swipe_engine import (
    get_random_examples,
    load_swipe_file,
    save_swipe_item,
    search_swipe_file,
)

st.set_page_config(
    page_title="GlitchGrowth Content Agent",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ GlitchGrowth Content Agent")
st.caption("A local-first content production room for tech memes, AI creator content, and soft monetization.")

with st.sidebar:
    st.header("Safe mode")
    st.write("This app creates content packets. It does not auto-post, scrape, mass-DM, or fake engagement.")
    st.divider()
    st.header("Default offer")
    st.write("**Chaotic Tech Creator Kit**")
    st.write("Start with a small $9-$19 product and test demand with comments/DMs.")

tabs = st.tabs([
    "Brand Voice",
    "Create Meme Post",
    "Create Carousel",
    "Create Reel",
    "Create Story Pack",
    "Create Product Promo",
    "Weekly Batch",
    "Lead / DM Replies",
    "Analytics Review",
    "Compliance Check",
    "Content Library",
    "Swipe File",
    "Quality Review",
    "Posting Queue",
    "Agent Mode",
    "Offer Lab",
])

def _format_copy_block(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        blocks = []
        for item in value:
            if isinstance(item, dict):
                heading = item.get("slide") or item.get("time") or item.get("type")
                parts = []
                if heading:
                    parts.append(str(heading))
                for key, item_value in item.items():
                    if key in {"slide", "time", "type"}:
                        continue
                    formatted = _format_copy_block(item_value)
                    if formatted:
                        parts.append(f"{key.replace('_', ' ').title()}: {formatted}")
                blocks.append("\n".join(parts))
            else:
                blocks.append(_format_copy_block(item))
        return "\n\n".join(block for block in blocks if block)
    if isinstance(value, dict):
        parts = []
        for key, item_value in value.items():
            formatted = _format_copy_block(item_value)
            if formatted:
                parts.append(f"{key.replace('_', ' ').title()}: {formatted}")
        return "\n\n".join(parts)
    return str(value)

def _first_packet_value(packet, keys):
    for key in keys:
        value = packet.get(key)
        if value:
            return value
    return ""

def _packet_sections(packet):
    return {
        "Meme Text / Text Overlay": _first_packet_value(
            packet,
            ["text_overlay", "hook", "voiceover", "slides", "stories", "launch_post"],
        ),
        "Visual Concept": _first_packet_value(
            packet,
            ["visual_concept", "scenes", "slides", "stories", "image_layout_notes", "story_sequence"],
        ),
        "Caption": _first_packet_value(
            packet,
            ["caption", "launch_post", "soft_sell_post", "urgency_post", "dm_reply"],
        ),
        "CTA": _first_packet_value(packet, ["cta", "launch_post", "soft_sell_post", "urgency_post"]),
        "Hashtags": packet.get("hashtags", ""),
        "Image Generation Prompt": _first_packet_value(
            packet,
            ["image_generation_prompt", "image_layout_notes", "scenes"],
        ),
        "Monetization Angle": _first_packet_value(
            packet,
            ["monetization_angle", "product_name", "price"],
        ),
        "Metric to Track": packet.get("metric_to_track", ""),
    }

def _reference_examples(query, content_type=None, limit=3):
    examples = search_swipe_file(query, content_type=content_type)
    if len(examples) < limit:
        seen_ids = {example["id"] for example in examples}
        for example in get_random_examples(limit):
            if example["id"] not in seen_ids:
                examples.append(example)
                seen_ids.add(example["id"])
            if len(examples) >= limit:
                break
    return examples[:limit]

def show_reference_examples(examples):
    if not examples:
        st.info("No swipe file examples found yet.")
        return

    st.subheader("Reference Examples")
    for index, example in enumerate(examples, start=1):
        with st.expander(f"Example {index}: {example.get('hook') or example.get('content_type') or 'Swipe item'}"):
            st.text_area(
                "Hook",
                example.get("hook", ""),
                height=80,
                disabled=True,
                key=f"reference-{example['id']}-hook",
            )
            st.text_area(
                "Caption",
                example.get("caption", ""),
                height=120,
                disabled=True,
                key=f"reference-{example['id']}-caption",
            )
            st.text_area(
                "Text Overlay",
                example.get("text_overlay", ""),
                height=80,
                disabled=True,
                key=f"reference-{example['id']}-overlay",
            )
            st.text_area(
                "CTA",
                example.get("cta", ""),
                height=80,
                disabled=True,
                key=f"reference-{example['id']}-cta",
            )
            st.text_area(
                "Why It Works",
                example.get("why_it_works", ""),
                height=100,
                disabled=True,
                key=f"reference-{example['id']}-why",
            )

def show_quality_review(review, key_prefix="quality"):
    st.subheader("Content Quality Review")
    score_cols = st.columns(3)
    score_cols[0].metric("Overall", review["overall_score"])
    score_cols[1].metric("Hook", review["hook_score"])
    score_cols[2].metric("Caption", review["caption_score"])

    detail_cols = st.columns(3)
    detail_cols[0].metric("CTA", review["cta_score"])
    detail_cols[1].metric("Brand Fit", review["brand_fit_score"])
    detail_cols[2].metric("Specificity", review["specificity_score"])
    st.metric("Monetization Fit", review["monetization_fit_score"])

    st.write(f"Recommended format: **{review['recommended_format']}**")

    st.write("Detected issues")
    for issue in review["detected_issues"]:
        st.write(f"- {issue}")

    st.write("Improvement suggestions")
    for suggestion in review["improvement_suggestions"]:
        st.write(f"- {suggestion}")

    st.write("Rewritten caption variants")
    variants = review["rewritten_caption_variants"]
    st.text_area("Punchier", variants["punchier"], height=130, key=f"{key_prefix}-punchier")
    st.text_area("More chaotic", variants["more_chaotic"], height=150, key=f"{key_prefix}-chaotic")
    st.text_area("Softer sell", variants["softer_sell"], height=150, key=f"{key_prefix}-soft")

def render_agent_summary_markdown(summary):
    lines = [
        "# GlitchGrowth Agent Mode Summary",
        "",
        f"Generated count: {summary['generated_count']}",
        f"Saved to library: {summary['saved_to_library_count']}",
        f"Queued count: {summary['queued_count']}",
        f"Needs revision: {summary['needs_revision_count']}",
        f"Average quality score: {summary['average_quality_score']}",
        "",
        "## Queued Schedule",
        "",
    ]
    for item in summary["planned_schedule"]:
        lines.append(
            f"- {item['planned_date']} {item['planned_time']} | {item['format']} | "
            f"{item['title']} | score {item['quality_score']}"
        )
    lines.extend(["", "## Needs Revision", ""])
    for item in summary["revision_items"]:
        lines.append(f"- {item['title']} | {item['format']} | score {item['quality_score']}")
        for issue in item.get("issues", []):
            lines.append(f"  - Issue: {issue}")
        for suggestion in item.get("suggestions", []):
            lines.append(f"  - Suggestion: {suggestion}")
    return "\n".join(lines)

def render_agent_schedule_csv(summary):
    output = io.StringIO()
    fieldnames = ["planned_date", "planned_time", "format", "title", "goal", "quality_score", "queue_id"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for item in summary["planned_schedule"]:
        writer.writerow({field: item.get(field, "") for field in fieldnames})
    return output.getvalue()

def offer_name_input(label, default, key):
    offers = load_offers()
    if not offers:
        return st.text_input(label, default, key=f"{key}-custom")

    offer_names = [offer["name"] for offer in offers]
    options = offer_names + ["Custom / free text"]
    selected = st.selectbox(label, options, key=f"{key}-select")
    if selected == "Custom / free text":
        return st.text_input("Custom offer / CTA target", default, key=f"{key}-custom")
    return selected

def render_launch_pack_markdown(pack):
    lines = [
        f"# Launch Pack: {pack['offer_name']}",
        "",
        "## Positioning",
        pack["offer_positioning_summary"],
        "",
        "## Audience Pain",
        pack["audience_pain_summary"],
        "",
    ]
    for key, title in [
        ("launch_post", "Launch Post"),
        ("soft_sell_post", "Soft-Sell Post"),
        ("urgency_final_call_post", "Urgency / Final-Call Post"),
    ]:
        post = pack[key]
        lines.extend([
            f"## {title}",
            "",
            f"**Text overlay:** {post.get('text_overlay', '')}",
            "",
            f"**Caption:**\n\n{post.get('caption', '')}",
            "",
            f"**CTA:** {post.get('cta', '')}",
            "",
        ])
    lines.extend(["## Story Slides", ""])
    for slide in pack["story_slides"]:
        lines.append(f"- Slide {slide['slide']} ({slide['type']}): {slide['copy']}")
    lines.extend(["", "## Comment CTAs", ""])
    for cta in pack["comment_ctas"]:
        lines.append(f"- {cta}")
    lines.extend(["", "## DM Reply Templates", ""])
    for reply in pack["dm_reply_templates"]:
        lines.append(f"- {reply}")
    lines.extend(["", "## Short FAQ", ""])
    for item in pack["short_faq"]:
        lines.append(f"- **{item['question']}** {item['answer']}")
    lines.extend(["", "## Objections + Replies", ""])
    for item in pack["common_objections_replies"]:
        lines.append(f"- **{item['objection']}** {item['reply']}")
    lines.extend(["", "## First-Week Posting Plan", ""])
    for item in pack["recommended_first_week_posting_plan"]:
        lines.append(f"- {item['day']}: {item['post']} - {item['goal']}")
    return "\n".join(lines)

def launch_post_to_library_packet(post, offer_name):
    return {
        "type": post.get("type", "offer_launch_post"),
        "title": post.get("title", offer_name),
        "text_overlay": post.get("text_overlay", ""),
        "caption": post.get("caption", ""),
        "cta": post.get("cta", ""),
        "hashtags": "#ContentCreator #CreatorTools #AICreator",
        "monetization_angle": f"Manual launch content for {offer_name}.",
        "metric_to_track": "comments, DMs, saves, profile visits, link clicks",
    }

def show_packet(packet, name_hint="content-packet", influenced_by_swipe=False):
    st.subheader("Generated Content")
    for label, value in _packet_sections(packet).items():
        st.text_area(
            label,
            value=_format_copy_block(value),
            height=140,
            key=f"{name_hint}-{label}",
        )

    if influenced_by_swipe:
        st.caption("Influenced by swipe examples, not copied.")

    if st.button("Save to Content Library", key=f"{name_hint}-save-library"):
        saved_item = save_to_library(packet)
        st.success(f"Saved to Content Library: {saved_item['title']}")

    if st.button("Review Content Quality", key=f"{name_hint}-quality-review"):
        show_quality_review(score_content(packet, load_brand_voice()), key_prefix=f"{name_hint}-quality")

    with st.expander("Show raw data"):
        st.json(packet)

    markdown_path = save_packet(packet, name_hint)
    st.success(f"Saved Markdown packet: {markdown_path}")
    st.download_button(
        "Download Markdown",
        data=markdown_path.read_text(encoding="utf-8"),
        file_name=markdown_path.name,
        mime="text/markdown",
    )

with tabs[0]:
    st.header("Brand Voice")
    profile = load_brand_voice()
    edited = st.text_area(
        "Edit brand voice JSON",
        value=json.dumps(profile, indent=2),
        height=420,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Brand Voice"):
            try:
                save_brand_voice(json.loads(edited))
                st.success("Brand voice saved.")
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON: {exc}")
    with col2:
        if st.button("Reset to Default"):
            save_brand_voice(DEFAULT_BRAND_VOICE)
            st.success("Reset saved. Refresh the page to reload it.")

with tabs[1]:
    st.header("Create Meme Post")
    with st.form("meme_form"):
        topic = st.text_input("Topic", "AI agents are becoming normal")
        audience = st.text_input("Audience", "tech creators and IT people")
        mood = st.selectbox("Mood", ["chaotic funny", "dramatic", "soft", "smart", "unhinged"])
        content_goal = st.selectbox("Content goal", ["growth", "engagement", "lead capture", "product sale", "affiliate", "service lead"])
        offer = offer_name_input("Offer / CTA target", "Chaotic Tech Creator Kit", "meme-offer")
        use_swipe_examples = st.checkbox("Use swipe file examples", key="meme-use-swipe")
        submitted = st.form_submit_button("Generate Meme Post")
    if submitted:
        swipe_examples = _reference_examples(topic, content_type="meme") if use_swipe_examples else None
        if use_swipe_examples:
            show_reference_examples(swipe_examples)
        packet = generate_meme_post(topic, audience, mood, content_goal, offer, swipe_examples=swipe_examples)
        show_packet(packet, "meme-post", influenced_by_swipe=use_swipe_examples and bool(swipe_examples))

with tabs[2]:
    st.header("Create Carousel")
    with st.form("carousel_form"):
        topic = st.text_input("Carousel topic", "How to turn one meme into a tiny product")
        number_of_slides = st.slider("Number of slides", 4, 10, 7)
        goal = st.selectbox("Goal", ["lead capture", "save/share", "product sale", "growth", "engagement"])
        offer = offer_name_input("Offer", "Chaotic Tech Creator Kit", "carousel-offer")
        use_swipe_examples = st.checkbox("Use swipe file examples", key="carousel-use-swipe")
        submitted = st.form_submit_button("Generate Carousel")
    if submitted:
        swipe_examples = _reference_examples(topic, content_type="carousel") if use_swipe_examples else None
        if use_swipe_examples:
            show_reference_examples(swipe_examples)
        packet = generate_carousel(topic, number_of_slides, goal, offer, swipe_examples=swipe_examples)
        show_packet(packet, "carousel", influenced_by_swipe=use_swipe_examples and bool(swipe_examples))

with tabs[3]:
    st.header("Create Reel")
    with st.form("reel_form"):
        topic = st.text_input("Reel topic", "AI gave me a business idea again")
        desired_length = st.text_input("Desired length", "12-18 seconds")
        style = st.text_input("Style", "fast chaotic talking-head")
        offer = offer_name_input("Offer", "Chaotic Creator Prompt Pack", "reel-offer")
        use_swipe_examples = st.checkbox("Use swipe file examples", key="reel-use-swipe")
        submitted = st.form_submit_button("Generate Reel")
    if submitted:
        swipe_examples = _reference_examples(topic, content_type="reel") if use_swipe_examples else None
        if use_swipe_examples:
            show_reference_examples(swipe_examples)
        packet = generate_reel(topic, desired_length, style, offer, swipe_examples=swipe_examples)
        show_packet(packet, "reel", influenced_by_swipe=use_swipe_examples and bool(swipe_examples))

with tabs[4]:
    st.header("Create Story Pack")
    with st.form("story_form"):
        topic = st.text_input("Story topic", "posting consistently with AI")
        offer = offer_name_input("Offer", "Chaotic Tech Creator Kit", "story-offer")
        goal = st.selectbox("Goal", ["lead capture", "product sale", "engagement", "growth"])
        use_swipe_examples = st.checkbox("Use swipe file examples", key="story-use-swipe")
        submitted = st.form_submit_button("Generate Story Pack")
    if submitted:
        swipe_examples = _reference_examples(topic, content_type="story") if use_swipe_examples else None
        if use_swipe_examples:
            show_reference_examples(swipe_examples)
        packet = generate_story_pack(topic, offer, goal, swipe_examples=swipe_examples)
        show_packet(packet, "story-pack", influenced_by_swipe=use_swipe_examples and bool(swipe_examples))

with tabs[5]:
    st.header("Create Product Promo")
    with st.form("promo_form"):
        product_name = offer_name_input("Product name", "Chaotic Tech Creator Kit", "promo-offer")
        product_description = st.text_area(
            "Product description",
            "tech meme prompts, caption templates, CTA ideas, carousel structures, and AI workflow prompts",
        )
        price = st.text_input("Price", "$9-$19")
        pain = st.text_input("Audience pain point", "posting consistently while feeling scattered")
        use_swipe_examples = st.checkbox("Use swipe file examples", key="promo-use-swipe")
        submitted = st.form_submit_button("Generate Product Promo")
    if submitted:
        swipe_examples = _reference_examples(product_name, content_type="product_promo") if use_swipe_examples else None
        if use_swipe_examples:
            show_reference_examples(swipe_examples)
        packet = generate_product_promo(product_name, product_description, price, pain, swipe_examples=swipe_examples)
        show_packet(packet, "product-promo", influenced_by_swipe=use_swipe_examples and bool(swipe_examples))

with tabs[6]:
    st.header("Weekly Batch Generator")
    with st.form("weekly_form"):
        week_theme = st.text_input("Week theme", "AI creator chaos")
        posting_frequency = st.text_input("Posting frequency", "2 posts per weekday")
        offer = offer_name_input("Offer to promote", "Chaotic Tech Creator Kit", "weekly-offer")
        use_swipe_examples = st.checkbox("Use swipe file examples", key="weekly-use-swipe")
        submitted = st.form_submit_button("Generate Weekly Batch")
    if submitted:
        swipe_examples = _reference_examples(week_theme) if use_swipe_examples else None
        if use_swipe_examples:
            show_reference_examples(swipe_examples)
        batch = generate_weekly_batch(week_theme, posting_frequency, offer, swipe_examples=swipe_examples)
        st.subheader("Generated Weekly Batch")
        st.json(batch)
        if use_swipe_examples and swipe_examples:
            st.caption("Influenced by swipe examples, not copied.")
        paths = save_weekly_batch(batch)
        st.success("Saved weekly batch files:")
        for p in paths:
            st.write(f"- {p}")
        for p in paths:
            st.download_button(
                f"Download {p.name}",
                data=p.read_text(encoding="utf-8"),
                file_name=p.name,
                mime="text/plain",
            )

with tabs[7]:
    st.header("Lead / DM Replies")
    raw = st.text_area(
        "Paste comments or DMs, one per line",
        "KIT please\nhow do you make these prompts?\ncollab?\nfollow me for crypto gains",
        height=200,
    )
    if st.button("Classify + Draft Replies"):
        results = classify_messages(raw)
        st.json(results)

with tabs[8]:
    st.header("Analytics Review")
    with st.form("analytics_form"):
        post_title = st.text_input("Post title", "AI workflow meme")
        post_format = st.selectbox("Post format", ["meme", "carousel", "reel", "story", "product promo"])
        reach = st.number_input("Reach", min_value=0, value=1000)
        likes = st.number_input("Likes", min_value=0, value=80)
        comments = st.number_input("Comments", min_value=0, value=8)
        shares = st.number_input("Shares", min_value=0, value=12)
        saves = st.number_input("Saves", min_value=0, value=20)
        follows = st.number_input("Follows", min_value=0, value=5)
        profile_visits = st.number_input("Profile visits", min_value=0, value=35)
        submitted = st.form_submit_button("Analyze")
    if submitted:
        analysis = analyze_post_metrics(
            post_title,
            post_format,
            reach,
            likes,
            comments,
            shares,
            saves,
            follows,
            profile_visits,
        )
        st.json(analysis)

with tabs[9]:
    st.header("Compliance Check")
    st.write("Use this before posting anything monetized.")
    sponsored = st.checkbox("Sponsored / paid partnership")
    gifted = st.checkbox("Gifted item or free product")
    affiliate = st.checkbox("Affiliate link")
    brand_relationship = st.checkbox("Any brand relationship or exchange of value")
    if st.button("Check Disclosure"):
        result = check_compliance(sponsored, gifted, affiliate, brand_relationship)
        if result["needs_disclosure"]:
            st.warning(result["guidance"])
            for sample in result["sample_disclosures"]:
                st.write(f"- {sample}")
        else:
            st.success(result["guidance"])
        st.json(result)

with tabs[10]:
    st.header("Content Library")
    library_items = load_library()

    content_types = sorted({item["content_type"] for item in library_items if item.get("content_type")})
    statuses = sorted({item["status"] for item in library_items if item.get("status")})

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input("Search", "")
    with col2:
        selected_type = st.selectbox("Content type", ["All"] + content_types)
    with col3:
        selected_status = st.selectbox("Status", ["All"] + statuses)

    filtered_items = search_library(
        query,
        content_type=None if selected_type == "All" else selected_type,
        status=None if selected_status == "All" else selected_status,
    )

    st.subheader("Saved Content")
    if filtered_items:
        table_fields = ["created_at", "content_type", "title", "status", "topic", "posted_date"]
        st.dataframe(
            [{field: item.get(field, "") for field in table_fields} for item in filtered_items],
            use_container_width=True,
            hide_index=True,
        )

        item_labels = [
            f"{item.get('title', 'Untitled')} | {item.get('content_type', 'content')} | {item.get('status', 'draft')}"
            for item in filtered_items
        ]
        selected_label = st.selectbox("Inspect item", item_labels)
        selected_item = filtered_items[item_labels.index(selected_label)]

        st.subheader("Selected Item")
        detail_col1, detail_col2 = st.columns(2)
        detail_fields = [
            "id",
            "created_at",
            "content_type",
            "title",
            "status",
            "goal",
            "topic",
            "posted_date",
        ]
        for index, field in enumerate(detail_fields):
            target = detail_col1 if index % 2 == 0 else detail_col2
            target.text_input(field.replace("_", " ").title(), selected_item.get(field, ""), disabled=True)

        st.text_area("Caption", selected_item.get("caption", ""), height=180, disabled=True)
        st.text_area("CTA", selected_item.get("cta", ""), height=90, disabled=True)
        st.text_area("Hashtags", selected_item.get("hashtags", ""), height=90, disabled=True)
        st.text_area("Image Prompt", selected_item.get("image_prompt", ""), height=160, disabled=True)

        if st.button("Add to Posting Queue", key=f"add-library-{selected_item['id']}-to-queue"):
            queued_item = add_to_queue({
                "library_item_id": selected_item.get("id", ""),
                "format": selected_item.get("content_type", ""),
                "title": selected_item.get("title", ""),
                "goal": selected_item.get("goal", ""),
                "status": "planned",
                "caption": selected_item.get("caption", ""),
                "cta": selected_item.get("cta", ""),
                "notes": selected_item.get("notes", ""),
            })
            st.success(f"Added to Posting Queue: {queued_item['title']}")

        with st.form("update_library_item_form"):
            status_options = sorted(set(statuses + ["draft", "ready", "posted", "archived"]))
            current_status = selected_item.get("status", "draft")
            status_index = status_options.index(current_status) if current_status in status_options else 0
            updated_status = st.selectbox("Update status", status_options, index=status_index)
            updated_notes = st.text_area("Notes", selected_item.get("notes", ""), height=140)
            updated_posted_date = st.text_input("Posted date", selected_item.get("posted_date", ""))
            submitted_update = st.form_submit_button("Update Library Item")

        if submitted_update:
            update_library_item(
                selected_item["id"],
                {
                    "status": updated_status,
                    "notes": updated_notes,
                    "posted_date": updated_posted_date,
                },
            )
            st.success("Content Library item updated.")
            st.rerun()
    else:
        st.info("No saved content matches those filters yet.")

with tabs[11]:
    st.header("Swipe File")

    with st.form("add_swipe_item_form"):
        st.subheader("Add Swipe Item")
        col1, col2 = st.columns(2)
        with col1:
            swipe_content_type = st.selectbox(
                "Content type",
                ["meme", "caption", "hook", "carousel", "reel", "story", "cta", "product_promo", "other"],
            )
            swipe_source = st.text_input("Source", "")
            swipe_hook = st.text_area("Hook", "", height=90)
            swipe_text_overlay = st.text_area("Text overlay", "", height=90)
        with col2:
            swipe_caption = st.text_area("Caption", "", height=140)
            swipe_cta = st.text_area("CTA", "", height=90)
            swipe_tone_tags = st.text_input("Tone tags", "")
        swipe_why = st.text_area("Why it works", "", height=120)
        swipe_notes = st.text_area("Notes", "", height=120)
        submitted_swipe = st.form_submit_button("Save Swipe Item")

    if submitted_swipe:
        saved_swipe = save_swipe_item({
            "content_type": swipe_content_type,
            "source": swipe_source,
            "hook": swipe_hook,
            "caption": swipe_caption,
            "text_overlay": swipe_text_overlay,
            "cta": swipe_cta,
            "why_it_works": swipe_why,
            "tone_tags": swipe_tone_tags,
            "notes": swipe_notes,
        })
        st.success(f"Saved swipe item: {saved_swipe['hook'] or saved_swipe['content_type']}")

    swipe_items = load_swipe_file()
    swipe_types = sorted({item["content_type"] for item in swipe_items if item.get("content_type")})

    st.subheader("Saved Swipe Items")
    filter_col1, filter_col2 = st.columns([2, 1])
    with filter_col1:
        swipe_query = st.text_input("Search swipe file", "")
    with filter_col2:
        selected_swipe_type = st.selectbox("Filter content type", ["All"] + swipe_types)

    filtered_swipes = search_swipe_file(
        swipe_query,
        content_type=None if selected_swipe_type == "All" else selected_swipe_type,
    )

    if filtered_swipes:
        swipe_table_fields = ["created_at", "content_type", "source", "hook", "tone_tags"]
        st.dataframe(
            [{field: item.get(field, "") for field in swipe_table_fields} for item in filtered_swipes],
            use_container_width=True,
            hide_index=True,
        )

        swipe_labels = [
            f"{item.get('hook') or item.get('caption') or 'Untitled'} | {item.get('content_type', 'example')}"
            for item in filtered_swipes
        ]
        selected_swipe_label = st.selectbox("Inspect swipe item", swipe_labels)
        selected_swipe = filtered_swipes[swipe_labels.index(selected_swipe_label)]

        st.subheader("Selected Swipe Item")
        inspect_col1, inspect_col2 = st.columns(2)
        inspect_col1.text_input("ID", selected_swipe.get("id", ""), disabled=True)
        inspect_col2.text_input("Created At", selected_swipe.get("created_at", ""), disabled=True)
        inspect_col1.text_input("Content Type", selected_swipe.get("content_type", ""), disabled=True)
        inspect_col2.text_input("Source", selected_swipe.get("source", ""), disabled=True)
        st.text_area("Hook", selected_swipe.get("hook", ""), height=90, disabled=True)
        st.text_area("Caption", selected_swipe.get("caption", ""), height=140, disabled=True)
        st.text_area("Text Overlay", selected_swipe.get("text_overlay", ""), height=90, disabled=True)
        st.text_area("CTA", selected_swipe.get("cta", ""), height=90, disabled=True)
        st.text_area("Why It Works", selected_swipe.get("why_it_works", ""), height=120, disabled=True)
        st.text_area("Tone Tags", selected_swipe.get("tone_tags", ""), height=80, disabled=True)
        st.text_area("Notes", selected_swipe.get("notes", ""), height=120, disabled=True)
    else:
        st.info("No swipe file items match those filters yet.")

with tabs[12]:
    st.header("Quality Review")
    with st.form("quality_review_form"):
        review_overlay = st.text_area("Text overlay", "", height=100)
        review_visual = st.text_area("Visual concept", "", height=120)
        review_caption = st.text_area("Caption", "", height=180)
        review_cta = st.text_area("CTA", "", height=90)
        review_hashtags = st.text_area("Hashtags", "", height=80)
        review_goal = st.text_input("Content goal", "lead capture")
        submitted_review = st.form_submit_button("Review Content")

    if submitted_review:
        review_packet = {
            "type": "manual_quality_review",
            "text_overlay": review_overlay,
            "visual_concept": review_visual,
            "caption": review_caption,
            "cta": review_cta,
            "hashtags": review_hashtags,
            "goal": review_goal,
            "monetization_angle": review_goal,
        }
        show_quality_review(score_content(review_packet, load_brand_voice()), key_prefix="manual-quality")

with tabs[13]:
    st.header("Posting Queue")
    queue_items = load_queue()
    platforms = sorted({item["platform"] for item in queue_items if item.get("platform")})

    st.subheader("This Week")
    if queue_items:
        grouped = {}
        for item in queue_items:
            planned_date = item.get("planned_date") or "Unscheduled"
            grouped.setdefault(planned_date, []).append(item)
        for planned_date in sorted(grouped.keys(), key=lambda value: (value == "Unscheduled", value)):
            with st.expander(f"{planned_date} ({len(grouped[planned_date])})", expanded=planned_date == "Unscheduled"):
                for item in grouped[planned_date]:
                    time_part = item.get("planned_time") or "no time"
                    platform_part = item.get("platform") or "no platform"
                    st.write(f"- {time_part} | {platform_part} | {item.get('title', 'Untitled')} | {item.get('status', 'planned')}")
    else:
        st.info("No queued posts yet.")

    st.subheader("Queue")
    queue_filter_col1, queue_filter_col2, queue_filter_col3 = st.columns([2, 1, 1])
    with queue_filter_col1:
        queue_query = st.text_input("Search queue", "")
    with queue_filter_col2:
        queue_status = st.selectbox("Queue status", ["All"] + QUEUE_STATUSES)
    with queue_filter_col3:
        queue_platform = st.selectbox("Platform", ["All"] + platforms)

    filtered_queue = search_queue(
        queue_query,
        status=None if queue_status == "All" else queue_status,
        platform=None if queue_platform == "All" else queue_platform,
    )

    if filtered_queue:
        queue_table_fields = ["planned_date", "planned_time", "platform", "format", "title", "goal", "status"]
        st.dataframe(
            [{field: item.get(field, "") for field in queue_table_fields} for item in filtered_queue],
            use_container_width=True,
            hide_index=True,
        )

        queue_labels = [
            f"{item.get('planned_date') or 'Unscheduled'} | {item.get('title') or 'Untitled'} | {item.get('status', 'planned')}"
            for item in filtered_queue
        ]
        selected_queue_label = st.selectbox("Inspect queue item", queue_labels)
        selected_queue_item = filtered_queue[queue_labels.index(selected_queue_label)]

        st.subheader("Selected Queue Item")
        queue_detail_col1, queue_detail_col2 = st.columns(2)
        queue_detail_col1.text_input("Queue ID", selected_queue_item.get("queue_id", ""), disabled=True)
        queue_detail_col2.text_input("Library Item ID", selected_queue_item.get("library_item_id", ""), disabled=True)
        queue_detail_col1.text_input("Created At", selected_queue_item.get("created_at", ""), disabled=True)
        queue_detail_col2.text_input("Format", selected_queue_item.get("format", ""), disabled=True)
        st.text_area("Caption", selected_queue_item.get("caption", ""), height=160, disabled=True)
        st.text_area("CTA", selected_queue_item.get("cta", ""), height=90, disabled=True)

        with st.form("update_queue_item_form"):
            updated_planned_date = st.text_input("Planned date", selected_queue_item.get("planned_date", ""))
            updated_planned_time = st.text_input("Planned time", selected_queue_item.get("planned_time", ""))
            updated_platform = st.text_input("Platform", selected_queue_item.get("platform", "Instagram"))
            current_queue_status = selected_queue_item.get("status", "planned")
            queue_status_index = QUEUE_STATUSES.index(current_queue_status) if current_queue_status in QUEUE_STATUSES else 0
            updated_queue_status = st.selectbox("Status", QUEUE_STATUSES, index=queue_status_index)
            updated_queue_notes = st.text_area("Notes", selected_queue_item.get("notes", ""), height=130)
            submitted_queue_update = st.form_submit_button("Update Queue Item")

        if submitted_queue_update:
            update_queue_item(
                selected_queue_item["queue_id"],
                {
                    "planned_date": updated_planned_date,
                    "planned_time": updated_planned_time,
                    "platform": updated_platform,
                    "status": updated_queue_status,
                    "notes": updated_queue_notes,
                },
            )
            st.success("Posting Queue item updated.")
            st.rerun()

        if st.button("Remove from Queue", key=f"remove-queue-{selected_queue_item['queue_id']}"):
            remove_from_queue(selected_queue_item["queue_id"])
            st.success("Removed from Posting Queue.")
            st.rerun()
    else:
        st.info("No queued posts match those filters yet.")

with tabs[14]:
    st.header("Agent Mode")
    with st.form("agent_mode_form"):
        agent_week_theme = st.text_input("Week theme", "AI creator chaos")
        agent_offer = offer_name_input("Offer", "Chaotic Tech Creator Kit", "agent-offer")
        agent_posting_frequency = st.text_input("Posting frequency", "2 posts per weekday")
        agent_minimum_score = st.slider("Minimum quality score", 0, 100, 75)
        agent_use_swipe = st.checkbox("Use swipe file examples", key="agent-use-swipe")
        submitted_agent = st.form_submit_button("Run Agent Mode")

    if submitted_agent:
        agent_swipe_examples = _reference_examples(agent_week_theme) if agent_use_swipe else None
        if agent_use_swipe:
            show_reference_examples(agent_swipe_examples)

        summary = run_weekly_agent_mode(
            agent_week_theme,
            agent_offer,
            agent_posting_frequency,
            minimum_quality_score=agent_minimum_score,
            use_swipe_examples=agent_use_swipe,
            swipe_examples=agent_swipe_examples,
        )

        st.subheader("Agent Mode Summary")
        metric_cols = st.columns(5)
        metric_cols[0].metric("Generated", summary["generated_count"])
        metric_cols[1].metric("Saved", summary["saved_to_library_count"])
        metric_cols[2].metric("Queued", summary["queued_count"])
        metric_cols[3].metric("Needs Revision", summary["needs_revision_count"])
        metric_cols[4].metric("Avg Score", summary["average_quality_score"])

        st.subheader("Queued Schedule")
        if summary["planned_schedule"]:
            st.dataframe(summary["planned_schedule"], use_container_width=True, hide_index=True)
        else:
            st.info("No posts met the quality threshold for queueing.")

        st.subheader("Revision Items")
        if summary["revision_items"]:
            revision_rows = []
            for item in summary["revision_items"]:
                revision_rows.append({
                    "title": item.get("title", ""),
                    "format": item.get("format", ""),
                    "quality_score": item.get("quality_score", ""),
                    "issues": " | ".join(item.get("issues", [])),
                    "suggestions": " | ".join(item.get("suggestions", [])),
                })
            st.dataframe(revision_rows, use_container_width=True, hide_index=True)
        else:
            st.success("No revision items. Everything met the queue threshold.")

        st.download_button(
            "Download Agent Mode Summary Markdown",
            data=render_agent_summary_markdown(summary),
            file_name="agent-mode-summary.md",
            mime="text/markdown",
        )
        st.download_button(
            "Download Queued Schedule CSV",
            data=render_agent_schedule_csv(summary),
            file_name="queued-schedule.csv",
            mime="text/csv",
        )

with tabs[15]:
    st.header("Offer Lab")

    with st.form("create_offer_form"):
        st.subheader("Create Offer")
        offer_col1, offer_col2 = st.columns(2)
        with offer_col1:
            new_offer_name = st.text_input("Name", "Chaotic Tech Creator Kit")
            new_offer_status = st.selectbox("Status", OFFER_STATUSES, index=0)
            new_offer_audience = st.text_input("Audience", "tech creators and chaotic online creators")
            new_offer_pain = st.text_area("Pain point", "posting consistently while feeling scattered", height=90)
            new_offer_format = st.selectbox("Format", OFFER_FORMATS)
            new_offer_price = st.text_input("Price", "$9-$19")
        with offer_col2:
            new_offer_promise = st.text_area("Promise", "Create faster without sounding painfully corporate.", height=100)
            new_offer_deliverables = st.text_area(
                "Deliverables",
                "meme prompts, caption templates, CTA ideas, carousel structures, and AI workflow prompts",
                height=120,
            )
            new_offer_keyword = st.text_input("CTA keyword", "KIT")
            new_offer_checkout = st.text_input("Checkout URL optional", "")
            new_offer_notes = st.text_area("Notes", "", height=90)
        submitted_offer = st.form_submit_button("Save Offer")

    if submitted_offer:
        created_offer = save_offer({
            "name": new_offer_name,
            "status": new_offer_status,
            "audience": new_offer_audience,
            "pain_point": new_offer_pain,
            "promise": new_offer_promise,
            "deliverables": new_offer_deliverables,
            "format": new_offer_format,
            "price": new_offer_price,
            "cta_keyword": new_offer_keyword,
            "checkout_url": new_offer_checkout,
            "notes": new_offer_notes,
        })
        st.success(f"Saved offer: {created_offer['name']}")

    offers = load_offers()
    st.subheader("Saved Offers")
    offer_filter_col1, offer_filter_col2, offer_filter_col3 = st.columns([2, 1, 1])
    with offer_filter_col1:
        offer_query = st.text_input("Search offers", "")
    with offer_filter_col2:
        offer_status_filter = st.selectbox("Offer status", ["All"] + OFFER_STATUSES)
    with offer_filter_col3:
        offer_format_filter = st.selectbox("Offer format", ["All"] + OFFER_FORMATS)

    filtered_offers = search_offers(
        offer_query,
        status=None if offer_status_filter == "All" else offer_status_filter,
        format=None if offer_format_filter == "All" else offer_format_filter,
    )

    if filtered_offers:
        offer_table_fields = ["name", "status", "format", "price", "cta_keyword", "audience"]
        st.dataframe(
            [{field: offer.get(field, "") for field in offer_table_fields} for offer in filtered_offers],
            use_container_width=True,
            hide_index=True,
        )
        offer_labels = [
            f"{offer.get('name', 'Untitled')} | {offer.get('status', 'idea')} | {offer.get('format', 'other')}"
            for offer in filtered_offers
        ]
        selected_offer_label = st.selectbox("Inspect offer", offer_labels)
        selected_offer = filtered_offers[offer_labels.index(selected_offer_label)]

        st.subheader("Selected Offer")
        detail_col1, detail_col2 = st.columns(2)
        detail_col1.text_input("ID", selected_offer.get("id", ""), disabled=True)
        detail_col2.text_input("Created At", selected_offer.get("created_at", ""), disabled=True)
        detail_col1.text_input("Name", selected_offer.get("name", ""), disabled=True)
        detail_col2.text_input("CTA Keyword", selected_offer.get("cta_keyword", ""), disabled=True)
        st.text_area("Audience", selected_offer.get("audience", ""), height=80, disabled=True)
        st.text_area("Pain Point", selected_offer.get("pain_point", ""), height=90, disabled=True)
        st.text_area("Promise", selected_offer.get("promise", ""), height=90, disabled=True)
        st.text_area("Deliverables", selected_offer.get("deliverables", ""), height=110, disabled=True)

        with st.form("update_offer_form"):
            current_offer_status = selected_offer.get("status", "idea")
            current_offer_format = selected_offer.get("format", "other")
            updated_offer_status = st.selectbox(
                "Update status",
                OFFER_STATUSES,
                index=OFFER_STATUSES.index(current_offer_status) if current_offer_status in OFFER_STATUSES else 0,
            )
            updated_offer_format = st.selectbox(
                "Update format",
                OFFER_FORMATS,
                index=OFFER_FORMATS.index(current_offer_format) if current_offer_format in OFFER_FORMATS else 0,
            )
            updated_offer_price = st.text_input("Price", selected_offer.get("price", ""))
            updated_checkout_url = st.text_input("Checkout URL optional", selected_offer.get("checkout_url", ""))
            updated_offer_notes = st.text_area("Notes", selected_offer.get("notes", ""), height=120)
            submitted_offer_update = st.form_submit_button("Update Offer")

        if submitted_offer_update:
            update_offer(
                selected_offer["id"],
                {
                    "status": updated_offer_status,
                    "format": updated_offer_format,
                    "price": updated_offer_price,
                    "checkout_url": updated_checkout_url,
                    "notes": updated_offer_notes,
                },
            )
            st.success("Offer updated.")
            st.rerun()

        if st.button("Archive Offer", key=f"archive-offer-{selected_offer['id']}"):
            archive_offer(selected_offer["id"])
            st.success("Offer archived.")
            st.rerun()

        st.subheader("Launch Pack")
        tone_tags_raw = st.text_input("Tone tags optional", "chaotic, useful, soft-sell")
        if st.button("Generate Launch Pack", key=f"launch-pack-{selected_offer['id']}"):
            tone_tags = [tag.strip() for tag in tone_tags_raw.split(",") if tag.strip()]
            launch_pack = generate_launch_pack(selected_offer, tone_tags=tone_tags)
            st.session_state[f"launch-pack-{selected_offer['id']}"] = launch_pack

        launch_pack = st.session_state.get(f"launch-pack-{selected_offer['id']}")
        if launch_pack:
            st.text_area("Offer positioning summary", launch_pack["offer_positioning_summary"], height=90)
            st.text_area("Audience pain summary", launch_pack["audience_pain_summary"], height=90)
            for key, label in [
                ("launch_post", "Launch Post"),
                ("soft_sell_post", "Soft-Sell Post"),
                ("urgency_final_call_post", "Urgency / Final-Call Post"),
            ]:
                post = launch_pack[key]
                with st.expander(label, expanded=key == "launch_post"):
                    st.text_area("Text overlay", post.get("text_overlay", ""), height=70, key=f"{key}-overlay-{selected_offer['id']}")
                    st.text_area("Caption", post.get("caption", ""), height=180, key=f"{key}-caption-{selected_offer['id']}")
                    st.text_area("CTA", post.get("cta", ""), height=70, key=f"{key}-cta-{selected_offer['id']}")

            st.write("Story slides")
            st.dataframe(launch_pack["story_slides"], use_container_width=True, hide_index=True)
            st.write("Comment CTAs")
            for cta in launch_pack["comment_ctas"]:
                st.write(f"- {cta}")
            st.write("DM reply templates")
            for reply in launch_pack["dm_reply_templates"]:
                st.write(f"- {reply}")
            st.write("Short FAQ")
            st.dataframe(launch_pack["short_faq"], use_container_width=True, hide_index=True)
            st.write("Common objections + replies")
            st.dataframe(launch_pack["common_objections_replies"], use_container_width=True, hide_index=True)
            st.write("Recommended first-week posting plan")
            st.dataframe(launch_pack["recommended_first_week_posting_plan"], use_container_width=True, hide_index=True)

            markdown = render_launch_pack_markdown(launch_pack)
            st.download_button(
                "Download Launch Pack Markdown",
                data=markdown,
                file_name=f"{selected_offer['id']}-launch-pack.md",
                mime="text/markdown",
            )

            if st.button("Save launch posts to Content Library", key=f"save-launch-posts-{selected_offer['id']}"):
                for post_key in ["launch_post", "soft_sell_post", "urgency_final_call_post"]:
                    save_to_library(launch_post_to_library_packet(launch_pack[post_key], launch_pack["offer_name"]))
                st.success("Saved launch, soft-sell, and urgency posts to Content Library.")
    else:
        st.info("No offers match those filters yet.")
