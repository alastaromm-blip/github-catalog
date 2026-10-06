"""Pure helpers for GitHub catalog sync (no network, no sheets)."""
from datetime import datetime, timezone
from dateutil import parser as date_parser

HUB_KEYWORDS = {
    "video": "video",
    "bots": "bots",
    "parsing": "parsing",
    "sites": "sites",
    "tables": "tables",
    "saas": "saas",
    "ai": "ai",
    "cloud": "cloud",
    "promo": "promo",
}


def parse_repo_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if "github.com/" in url:
        part = url.split("github.com/", 1)[1]
    else:
        part = url
    owner, _, repo = part.partition("/")
    repo = repo.split("/")[0].split("#")[0].split("?")[0]
    return f"{owner.strip()}/{repo.strip()}"


def dedupe_repos(repos: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for r in repos:
        key = r.strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(r.strip())
    return out


def is_fresh(pushed_at: str, max_days: int, now_iso: str) -> bool:
    pushed = date_parser.isoparse(pushed_at)
    now = date_parser.isoparse(now_iso)
    if pushed.tzinfo is None:
        pushed = pushed.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - pushed).days <= max_days


def hub_for_topics(topics: list[str]) -> str:
    t = {x.lower() for x in topics}
    if t & {"image-generation", "stable-diffusion", "text2image", "text-to-image", "comfy", "midjourney", "image-editing"}:
        return "images"
    if t & {"database", "postgres", "firebase", "backend", "search-engine", "vector-database", "embeddings"}:
        return "data"
    if t & {"boilerplate", "saas", "stripe", "authentication", "payments"}:
        return "saas"
    if t & {"spreadsheet", "crm", "dashboard", "airtable", "erp"}:
        return "crm"
    if t & {"seo"}:
        return "seo"
    if t & {"social-media", "tiktok", "youtube", "instagram", "twitter"}:
        return "smm"
    if t & {"rss", "scheduler", "newsletter", "broadcast", "mailchimp"}:
        return "mailing"
    if t & {"ai-agent", "agents", "mcp", "assistant", "skills", "low-code", "llm", "rag", "ai-chatbot", "ai"}:
        return "ai"
    if t & {"telegram-bot", "discord-bot", "chatbot", "telegram"}:
        return "bots"
    if t & {"scraping", "crawler", "parser"}:
        return "parsing"
    if t & {"prompts", "prompt-engineering", "markdown", "writing", "blog", "newsletter"}:
        return "content"
    if t & {"landing-page", "portfolio", "static-site", "cms", "ecommerce", "forms"}:
        return "sites"
    if t & {"self-hosted", "cloud-storage", "file-sharing", "dashboard"}:
        return "crm"
    if t & {"video-editing", "video-automation", "ffmpeg", "text-to-speech", "speech-to-text", "subtitles"}:
        return "video"
    return "other"
