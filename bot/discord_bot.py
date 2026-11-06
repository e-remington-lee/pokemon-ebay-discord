import os

import discord
from discord import app_commands

from bot.ebay_client import EbayAPIError, EbayClient, Listing
from bot.search_targets import SEARCH_TARGETS, SearchTarget, active_targets


def find_target(name: str) -> SearchTarget | None:
    """Case-insensitive lookup so '/price jungle 2' matches 'Jungle 2'."""
    wanted = name.strip().lower()
    return next((t for t in SEARCH_TARGETS if t.name.lower() == wanted), None)


FETCH_LIMIT = 15  # listings pulled from eBay per search, before the required-words filter


def build_listings_embed(target: SearchTarget, total: int, fetched: list[Listing]) -> discord.Embed:
    """Drop listings whose title is missing any of target.required, then format the rest."""
    listings = [item for item in fetched if target.matches(item.title)]
    # eBay's sort=price isn't strictly ordered, so sort cheapest-first here too.
    listings.sort(key=lambda item: item.price if item.price is not None else float("inf"))
    dropped = len(fetched) - len(listings)

    floor = f" (≥ ${target.min_price:,.0f})" if target.min_price else ""
    description = f"Search: `{target.keywords}`"
    if target.required:
        description += "\nMust contain: " + ", ".join(f"`{w}`" for w in target.required)
    embed = discord.Embed(
        title=f"{target.name}: {len(listings)} matching listing{'s' if len(listings) != 1 else ''}{floor}",
        description=description,
        color=discord.Color.blue(),
    )
    embed.set_footer(
        text=f"Fetched {len(fetched)} of {total} on eBay · {dropped} filtered out by required words"
    )
    if not listings:
        embed.add_field(name="No results", value="Nothing on eBay matches right now.", inline=False)
        return embed

    lines = []
    for item in listings:
        price = f"${item.price:,.2f}" if item.price is not None else "n/a"
        title = item.title if len(item.title) <= 80 else item.title[:77] + "..."
        lines.append(f"**{price}** · [{title}]({item.short_url})")
    # Description allows 4096 chars (a field only 1024), enough for 15 listings.
    embed.description += "\n\n" + "\n".join(lines)

    if listings[0].image_url:
        embed.set_thumbnail(url=listings[0].image_url)
    return embed


class PriceBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.general_channel = None
        self.ebay: EbayClient | None = None

    async def setup_hook(self):
        try:
            self.ebay = EbayClient()  # one shared client so the OAuth token gets reused
        except EbayAPIError as e:
            print(f"Warning: eBay disabled: {e}")
        await self.tree.sync()

    async def close(self):
        if self.ebay:
            await self.ebay.close()
        await super().close()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

        channel_id = os.getenv("DISCORD_CHANNEL_ID")
        if channel_id:
            self.general_channel = self.get_channel(int(channel_id))
            if self.general_channel:
                await self.general_channel.send("Price bot is online!")
            else:
                print(f"Warning: Could not find channel {channel_id}")
        else:
            print("Warning: DISCORD_CHANNEL_ID not set in .env")

    async def post_to_channel(self, content=None, embed=None):
        """Send a message to the general channel."""
        if self.general_channel:
            await self.general_channel.send(content=content, embed=embed)


def create_bot() -> PriceBot:
    bot = PriceBot()

    async def item_autocomplete(interaction: discord.Interaction, current: str):
        current = current.lower()
        return [
            app_commands.Choice(name=t.name, value=t.name)
            for t in active_targets()
            if current in t.name.lower()
        ][:25]

    @bot.tree.command(name="price", description="Search eBay listings for one of the tracked items")
    @app_commands.describe(item="Which tracked item to search (e.g. Jungle 2)")
    @app_commands.autocomplete(item=item_autocomplete)
    async def price(interaction: discord.Interaction, item: str):
        target = find_target(item)
        if target is None:
            names = ", ".join(t.name for t in SEARCH_TARGETS)
            await interaction.response.send_message(
                f"Unknown item `{item}`. Options: {names}", ephemeral=True
            )
            return
        if target.keywords == "TODO":
            await interaction.response.send_message(
                f"`{target.name}` doesn't have search keywords yet (bot/search_targets.py).",
                ephemeral=True,
            )
            return
        if bot.ebay is None:
            await interaction.response.send_message(
                "eBay isn't configured: set EBAY_CLIENT_ID / EBAY_CLIENT_SECRET in .env.",
                ephemeral=True,
            )
            return

        # eBay can take a few seconds; defer so Discord doesn't time out the interaction (3s limit).
        await interaction.response.defer()

        try:
            total, listings = await bot.ebay.search(
                target.keywords,
                limit=FETCH_LIMIT,
                min_price=target.min_price,
                category_id=target.category_id,
                sort="price",
            )
        except EbayAPIError as e:
            await interaction.followup.send(f"eBay request failed: {str(e)[:1800]}")
            return

        await interaction.followup.send(embed=build_listings_embed(target, total, listings))

    @bot.tree.command(name="ping", description="Check if the bot is responsive")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms")

    return bot
