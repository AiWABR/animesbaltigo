import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from core.http_client import get_http_client
from config import ANIME_SOURCE, SOURCE_SITE_BASE


BASE_URL = SOURCE_SITE_BASE or "https://sushianimes.com.br"

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE_URL,
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


async def _get(url: str) -> str:
    client = await get_http_client()
    r = await client.get(url, headers=_HTTP_HEADERS)
    r.raise_for_status()
    return r.text


def _extract_episode_links_from_home(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    if ANIME_SOURCE == "sushi" or "sushianimes" in BASE_URL.lower():
        for a in soup.select("a[href*='/anime/'][href*='-season-'][href*='-episode']"):
            href = (a.get("href") or "").strip()
            full_url = urljoin(BASE_URL, href)
            path = full_url.split("/anime/", 1)[-1].strip("/")
            match = re.search(r"^(.+)-(\d+)-season-(\d+)-episode$", path)
            if not match:
                continue

            anime_id = match.group(1)
            season = int(match.group(2))
            episode = int(match.group(3))
            episode_key = f"S{season}E{episode}"
            key = f"{anime_id}|{episode_key}"
            if key in seen:
                continue
            seen.add(key)

            text = _clean(a.get_text(" ", strip=True))
            title = re.sub(r"(?i)^(hoje|ontem|dublado|fullhd|hd|sd)\s+", "", text).strip()
            title = re.sub(r"\s*\d+\D*\s*Temporada\s*\|\s*\d+\D*\s*Epis[oó]dio.*$", "", title, flags=re.I).strip()

            if not title:
                img = a.find("img")
                if img:
                    title = _clean(img.get("alt"))

            if not title:
                title = anime_id.replace("-", " ").title()

            results.append({
                "anime_id": anime_id,
                "episode": episode_key,
                "season": season,
                "episode_number": episode,
                "title": title,
                "episode_url": full_url,
                "key": key,
            })

        return results

    for a in soup.select("a[href*='/animes/']"):
        href = (a.get("href") or "").strip()
        full_url = urljoin(BASE_URL, href)

        m = re.search(r"/animes/([^/]+)/(\d+)(?:/)?$", full_url)
        if not m:
            continue

        anime_slug = m.group(1)
        episode = m.group(2)

        key = f"{anime_slug}|{episode}"
        if key in seen:
            continue
        seen.add(key)

        text = _clean(a.get_text(" ", strip=True))
        title = re.sub(r"\s*-\s*[Ee]pis[oó]dio\s+\d+\s*$", "", text).strip()
        title = re.sub(r"\s*[Ee]pis[oó]dio\s+\d+\s*$", "", title).strip()

        if not title:
            img = a.find("img")
            if img:
                title = _clean(img.get("alt"))

        if not title:
            title = anime_slug.replace("-", " ").title()

        results.append({
            "anime_id": anime_slug,
            "episode": episode,
            "title": title,
            "episode_url": full_url,
            "key": key,
        })

    return results


async def get_recent_episodes(limit: int = 12) -> list[dict]:
    html = await _get(BASE_URL)
    items = _extract_episode_links_from_home(html)
    return items[:limit]
