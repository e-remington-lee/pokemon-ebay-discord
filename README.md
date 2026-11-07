# Pokemon eBay Price Bot

A Discord bot that checks eBay sold prices for Pokemon cards.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **New Application** → name it
3. Go to **Bot** tab → click **Add Bot**
4. Click **Reset Token** → copy the token
5. Under **Privileged Gateway Intents**, enable:
   - Message Content Intent

### 3. Invite Bot to Server

1. Go to **OAuth2 → URL Generator**
2. Scopes: `bot`, `applications.commands`
3. Bot Permissions: `Send Messages`, `Read Message History`, `View Channels`
4. Open the generated URL → select your server → Authorize

### 4. Get Channel ID

1. In Discord, go to **Settings → Advanced → Developer Mode** (turn on)
2. Right-click the channel you want the bot to post in
3. Click **Copy Channel ID**

### 5. Configure Environment

```bash
copy .env.example .env
```

Edit `.env`:
```
DISCORD_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
```

### 6. Run the Bot

```bash
python main.py
```

## Usage

### Slash Commands

Slash commands are used **in Discord**, not in the terminal.

1. Go to any channel in your server where the bot is
2. Type `/ping` or `/price`
3. Discord will show autocomplete for your bot's commands
4. Press Enter to run

| Command | Description |
|---------|-------------|
| `/ping` | Check if bot is responsive |
| `/price <card_name>` | Get eBay sold prices for a card |

If commands don't appear, wait a few minutes (they sync globally) or restart Discord (Ctrl+R).

### The Terminal

The terminal running `python main.py` is just for:
- Seeing logs/output
- Keeping the bot alive
- Stopping the bot (Ctrl+C)

## Project Structure

```
pokemon-ebay-price/
├── .env                 # Your API keys (not committed)
├── .env.example         # Template for .env
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── bot/
    └── discord_bot.py   # Discord bot logic
```


## Testing Ebay 
 python -m bot.ebay_client "Nintendo Pokémon TCG Jungle 1995 Japanese sealed booster pack" --min-price 700