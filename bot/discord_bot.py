import discord
from discord import app_commands


class PriceBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")


def create_bot() -> PriceBot:
    bot = PriceBot()

    @bot.tree.command(name="price", description="Get eBay sold prices for a Pokemon card")
    @app_commands.describe(card_name="Name of the Pokemon card to search")
    async def price(interaction: discord.Interaction, card_name: str):
        await interaction.response.defer()

        # TODO: Replace with actual eBay API call
        embed = discord.Embed(
            title=f"Price Check: {card_name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="eBay API not yet connected", inline=False)
        embed.add_field(name="Search Term", value=card_name, inline=False)

        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="ping", description="Check if the bot is responsive")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms")

    return bot
