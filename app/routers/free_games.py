"""
/v1/free-games — current and upcoming Epic Games Store free games
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import make_meta, now_iso
from app.models import FreeGame, FreeGamesResponse, GameImage

router = APIRouter(prefix="/v1/free-games", tags=["Free Games"])


async def _fetch_free_games(locale: str = "en-US") -> Optional[Dict[str, Any]]:
    return await fetch_json(
        settings.EPIC_FREE_GAMES_URL,
        params={"locale": locale, "country": "US", "allowCountries": "US"},
    )


def _parse_images(raw_images: List[Dict]) -> List[GameImage]:
    out = []
    for img in raw_images:
        url = img.get("url", "")
        if url:
            out.append(GameImage(
                url=url,
                type=img.get("type"),
                md5=img.get("md5"),
                width=img.get("width"),
                height=img.get("height"),
            ))
    return out


def _parse_games(raw: Dict[str, Any]) -> tuple[List[FreeGame], List[FreeGame]]:
    elements = (
        raw.get("data", {})
        .get("Catalog", {})
        .get("searchStore", {})
        .get("elements", [])
    )
    now = datetime.now(timezone.utc)
    current_free: List[FreeGame] = []
    upcoming_free: List[FreeGame] = []

    for game in elements:
        promotions = game.get("promotions")
        if not promotions:
            continue

        title = game.get("title", "Unknown Game")
        description = game.get("description", "")
        url_slug = game.get("urlSlug", "")
        store_url = f"https://store.epicgames.com/p/{url_slug}" if url_slug else None
        images = _parse_images(game.get("keyImages", []))
        original_price = game.get("price", {}).get("totalPrice", {}).get("originalPrice")
        publisher = game.get("publisherDisplayName")
        developer = game.get("developerDisplayName")
        item_id = game.get("id")

        # Current free games
        for offer_set in promotions.get("promotionalOffers", []):
            for offer in offer_set.get("promotionalOffers", []):
                if offer.get("discountSetting", {}).get("discountPercentage", -1) == 0:
                    end_date = offer.get("endDate")
                    start_date = offer.get("startDate")
                    days_remaining = hours_remaining = None
                    if end_date:
                        try:
                            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                            if end_dt > now:
                                delta = end_dt - now
                                days_remaining = delta.days
                                hours_remaining = int(delta.total_seconds() // 3600) % 24
                        except Exception:
                            pass
                    current_free.append(FreeGame(
                        id=item_id,
                        title=title,
                        description=description,
                        url_slug=url_slug,
                        store_url=store_url,
                        images=images,
                        original_price=original_price,
                        publisher=publisher,
                        developer=developer,
                        offer_end_date=end_date,
                        offer_start_date=start_date,
                        days_remaining=days_remaining,
                        hours_remaining=hours_remaining,
                        is_current=True,
                    ))

        # Upcoming free games
        for offer_set in promotions.get("upcomingPromotionalOffers", []):
            for offer in offer_set.get("promotionalOffers", []):
                if offer.get("discountSetting", {}).get("discountPercentage", -1) == 0:
                    start_date = offer.get("startDate")
                    end_date = offer.get("endDate")
                    days_remaining = None
                    if start_date:
                        try:
                            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                            days_remaining = (start_dt - now).days
                        except Exception:
                            pass
                    upcoming_free.append(FreeGame(
                        id=item_id,
                        title=title,
                        description=description,
                        url_slug=url_slug,
                        store_url=store_url,
                        images=images,
                        original_price=original_price,
                        publisher=publisher,
                        developer=developer,
                        offer_start_date=start_date,
                        offer_end_date=end_date,
                        days_remaining=days_remaining,
                        is_current=False,
                    ))

    return current_free, upcoming_free


@router.get(
    "",
    response_model=FreeGamesResponse,
    summary="Current and upcoming free games",
    description=(
        "Returns the current Epic Games Store free game(s) and upcoming free games. "
        "Includes store URLs, cover images, publisher, countdown timers, and more. "
        "Use `locale` to get localized titles (e.g. `en-US`, `de-DE`, `fr-FR`)."
    ),
)
async def get_free_games(
    request: Request,
    locale: str = Query("en-US", description="Locale for game titles and descriptions"),
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> FreeGamesResponse:
    ttl = settings.CACHE_TTL_FREE_GAMES
    cache_key = f"free_games:{locale}"

    if force_refresh:
        cache.invalidate(cache_key)

    async def fetch() -> Optional[Dict[str, Any]]:
        return await _fetch_free_games(locale)

    raw = await cache.get_or_fetch(cache_key, ttl, fetch)
    fetched_at = now_iso()

    if raw is None:
        return FreeGamesResponse(
            current=[],
            upcoming=[],
            current_count=0,
            upcoming_count=0,
            summary="Unable to fetch free games from Epic Games Store.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    current_free, upcoming_free = _parse_games(raw)

    if current_free:
        titles = ", ".join(g.title for g in current_free)
        summary = f"🎮 {len(current_free)} free game(s) available now: {titles}."
        if upcoming_free:
            next_titles = ", ".join(g.title for g in upcoming_free[:2])
            summary += f" Coming soon: {next_titles}."
    else:
        summary = "No free games currently available on the Epic Games Store."
        if upcoming_free:
            next_titles = ", ".join(g.title for g in upcoming_free[:2])
            summary += f" Coming soon: {next_titles}."

    return FreeGamesResponse(
        current=current_free,
        upcoming=upcoming_free,
        current_count=len(current_free),
        upcoming_count=len(upcoming_free),
        summary=summary,
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/current",
    summary="Currently free games only",
    description="Shortcut returning only the games that are free right now.",
)
async def get_current_free_games(
    request: Request,
    locale: str = Query("en-US"),
) -> Dict[str, Any]:
    resp = await get_free_games(request, locale=locale)
    return {
        "games": resp.current,
        "count": resp.current_count,
        "summary": resp.summary,
        "meta": resp.meta,
    }


@router.get(
    "/upcoming",
    summary="Upcoming free games only",
    description="Shortcut returning only the games that will be free soon.",
)
async def get_upcoming_free_games(
    request: Request,
    locale: str = Query("en-US"),
) -> Dict[str, Any]:
    resp = await get_free_games(request, locale=locale)
    return {
        "games": resp.upcoming,
        "count": resp.upcoming_count,
        "meta": resp.meta,
    }
