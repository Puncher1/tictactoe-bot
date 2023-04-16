import os
from dotenv import load_dotenv

from bot import TicTacToeBot

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if __name__ == "__main__":
    TicTacToeBot().run(TOKEN)  # type: ignore
