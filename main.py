import os
from dotenv import load_dotenv
from bot.discord_bot import create_bot


def main():
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in .env file")
        print("Copy .env.example to .env and add your bot token")
        return

    bot = create_bot()
    bot.run(token)


if __name__ == "__main__":
    main()
