from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parent.parent
MOCKUP_PATH = BASE_DIR / "assets" / "anime_update_mockup.png"
ANILIST_API_URL = "https://graphql.anilist.co"

IMAGE_X = 995
IMAGE_Y = 85
IMAGE_WIDTH = 516
IMAGE_HEIGHT = 772
IMAGE_ZOOM = 1.0
IMAGE_BORDER_RADIUS = 28

ANILIST_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    coverImage {
      extraLarge
      large
      medium
    }
    bannerImage
  }
}
"""


async def fetch_anilist_cover_url(title: str) -> str:
    title = str(title or "").strip()
    if not title:
        return ""

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.post(
            ANILIST_API_URL,
            json={"query": ANILIST_QUERY, "variables": {"search": title}},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )
        response.raise_for_status()

    media = (((response.json() or {}).get("data") or {}).get("Media") or {})
    cover = media.get("coverImage") or {}
    return (
        cover.get("extraLarge")
        or cover.get("large")
        or cover.get("medium")
        or media.get("bannerImage")
        or ""
    )


async def render_anime_update_mockup(title: str) -> BytesIO:
    image_url = await fetch_anilist_cover_url(title)
    if not image_url:
        raise ValueError(f"Imagem do AniList nao encontrada para: {title}")
    if not MOCKUP_PATH.exists():
        raise FileNotFoundError(f"Mockup nao encontrado: {MOCKUP_PATH}")

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(image_url)
        response.raise_for_status()

    mockup = Image.open(MOCKUP_PATH).convert("RGBA")
    cover = Image.open(BytesIO(response.content)).convert("RGBA")

    ratio = max(IMAGE_WIDTH / cover.width, IMAGE_HEIGHT / cover.height)
    new_width = int(cover.width * ratio * IMAGE_ZOOM)
    new_height = int(cover.height * ratio * IMAGE_ZOOM)
    cover = cover.resize((new_width, new_height), Image.Resampling.LANCZOS)

    left = max(0, (new_width - IMAGE_WIDTH) // 2)
    top = max(0, (new_height - IMAGE_HEIGHT) // 2)
    cover = cover.crop((left, top, left + IMAGE_WIDTH, top + IMAGE_HEIGHT))

    mask = Image.new("L", (IMAGE_WIDTH, IMAGE_HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [0, 0, IMAGE_WIDTH, IMAGE_HEIGHT],
        radius=IMAGE_BORDER_RADIUS,
        fill=255,
    )
    cover.putalpha(mask)

    mockup.paste(cover, (IMAGE_X, IMAGE_Y), cover)

    output = BytesIO()
    output.name = "novo_episodio_anime.png"
    mockup.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
