"""
Async eBay client for searching listings via the eBay Browse API.

Auth: OAuth2 "client credentials" flow (application token). You only need the
App ID (Client ID) and Cert ID (Client Secret) from https://developer.ebay.com/my/keys
-- no user login required.

Uses aiohttp, which is already installed as a dependency of discord.py, so the
calls are non-blocking and safe to await inside slash command handlers.

Quick test from the project root:
    python -m bot.ebay_client "charizard base set holo"
"""

import asyncio
import base64
import os
import time
from dataclasses import dataclass

import aiohttp

ENVIRONMENTS = {
    "production": "https://api.ebay.com",
    "sandbox": "https://api.sandbox.ebay.com",
}

OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"

# Category IDs are configured per search in bot/search_targets.py.


class EbayAPIError(Exception):
    pass


@dataclass
class Listing:
    item_id: str
    title: str
    price: float | None
    currency: str | None
    url: str
    image_url: str | None
    condition: str | None
    buying_options: list[str]

    @property
    def short_url(self) -> str:
        """Clean ebay.com/itm/<id> link (itemWebUrl can be hundreds of chars of tracking)."""
        parts = self.item_id.split("|")  # Browse API ids look like "v1|123456789|0"
        return f"https://www.ebay.com/itm/{parts[1]}" if len(parts) >= 2 else self.url

    @classmethod
    def from_api(cls, item: dict) -> "Listing":
        price = item.get("price") or {}
        return cls(
            item_id=item.get("itemId", ""),
            title=item.get("title", ""),
            price=float(price["value"]) if "value" in price else None,
            currency=price.get("currency"),
            url=item.get("itemWebUrl", ""),
            image_url=(item.get("image") or {}).get("imageUrl"),
            condition=item.get("condition"),
            buying_options=item.get("buyingOptions", []),
        )


class EbayClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        environment: str | None = None,
        marketplace_id: str = "EBAY_US",
    ):
        self.client_id = client_id or os.getenv("EBAY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("EBAY_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise EbayAPIError("EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set")

        env = (environment or os.getenv("EBAY_ENVIRONMENT", "production")).lower()
        if env not in ENVIRONMENTS:
            raise EbayAPIError(f"EBAY_ENVIRONMENT must be one of {list(ENVIRONMENTS)}")
        self.base_url = ENVIRONMENTS[env]
        self.marketplace_id = marketplace_id

        self._session: aiohttp.ClientSession | None = None
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_token(self) -> str:
        """Fetch an application access token, cached until shortly before it expires (~2h)."""
        async with self._token_lock:
            if self._token and time.time() < self._token_expires_at - 60:
                return self._token

            creds = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/identity/v1/oauth2/token",
                headers={
                    "Authorization": f"Basic {creds}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials", "scope": OAUTH_SCOPE},
            ) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200:
                    raise EbayAPIError(f"Token request failed ({resp.status}): {body}")

            self._token = body["access_token"]
            self._token_expires_at = time.time() + int(body.get("expires_in", 7200))
            return self._token

    async def search(
        self,
        keywords: str,
        limit: int = 10,
        category_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        buy_it_now_only: bool = False,
        sort: str | None = None,
    ) -> tuple[int, list[Listing]]:
        """
        Search active eBay listings matching `keywords`.

        sort: None (best match), "price", "-price", or "newlyListed".
        Returns (total_matches, listings).
        """
        filters = []
        if min_price is not None or max_price is not None:
            lo = "" if min_price is None else min_price
            hi = "" if max_price is None else max_price
            filters.append(f"price:[{lo}..{hi}]")
            filters.append("priceCurrency:USD")
        if buy_it_now_only:
            filters.append("buyingOptions:{FIXED_PRICE}")

        params = {"q": keywords, "limit": str(max(1, min(limit, 200)))}
        if category_id:
            params["category_ids"] = category_id
        if filters:
            params["filter"] = ",".join(filters)
        if sort:
            params["sort"] = sort

        token = await self._get_token()
        session = await self._get_session()
        async with session.get(
            f"{self.base_url}/buy/browse/v1/item_summary/search",
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
            },
            params=params,
        ) as resp:
            body = await resp.json(content_type=None)
            if resp.status != 200:
                raise EbayAPIError(f"Search failed ({resp.status}): {body}")

        items = [Listing.from_api(i) for i in body.get("itemSummaries", [])]
        return body.get("total", 0), items


async def _demo(keywords: str, min_price: float | None):
    from dotenv import load_dotenv

    load_dotenv()
    client = EbayClient()
    try:
        total, listings = await client.search(keywords, limit=10, min_price=min_price)
        print(f"{total} total matches for {keywords!r}; showing {len(listings)}:\n")
        for item in listings:
            price = f"{item.price:.2f} {item.currency}" if item.price is not None else "n/a"
            print(f"- {price:>14}  {item.title}")
            print(f"  {item.url}")
    finally:
        await client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search active eBay listings")
    parser.add_argument("keywords", nargs="+")
    parser.add_argument("--min-price", type=float, default=None)
    args = parser.parse_args()
    asyncio.run(_demo(" ".join(args.keywords), args.min_price))
