import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import asyncio

# モジュールのインポート
from janken import setup_janken
from nyan import setup_nyan
from slot import setup_slot
import bj
import give
from sansuu_easy import setup_sansuu_easy
from sansuu_normal import setup_sansuu_normal
from sansuu_hard import setup_sansuu_hard
from data import load_all_data, get_quotes, add_quote
from avatar import setup_avatar
from dentaku import setup_dentaku
from giveaway import Giveaway
from omikuji import setup_omikuji
from roulette import setup as setup_roulette
from tictactoe import setup_tictactoe

# 🔻 RenderではVCやVoiceVoxが使えないため、opusライブラリは不要
# try:
#     import discord.opus
#     discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.5.2/lib/libopus.dylib')
# except Exception:
#     pass

# .envファイルからトークン読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# データ読み込み（全体）
load_all_data()

# Botの初期設定
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # ボイスチャット機能が今は使われてないならFalseでもOK
bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

# 起動時イベント
@bot.event
async def on_ready():
    await bot.add_cog(Giveaway(bot))

    # 🔻 VoiceVox連携中止中なのでコメントアウト
    # from tts import setup as setup_tts
    # await setup_tts(bot)

    await setup_roulette(bot)

    try:
        await bot.load_extension("help")
    except Exception as e:
        print(f"❌ help の読み込みに失敗: {e}")

    try:
        await bot.load_extension("nyan_ranking")
    except Exception as e:
        print(f"❌ nyan_ranking の読み込みに失敗: {e}")
    
    try:
        await bot.load_extension("wordwolf")
    except Exception as e:
        print(f"❌ wordwolf の読み込みに失敗: {e}")

    await bot.tree.sync()
    print("✅ スラッシュコマンドを再同期したきつ")
    print(f"✅ ログイン完了: {bot.user}")

# 各種コマンド登録（非同期が必要なものには await を付ける）
async def setup_all_commands():
    setup_janken(bot)
    setup_nyan(bot)
    setup_slot(bot)
    bj.setup_bj(bot)
    await give.setup_give(bot)
    setup_sansuu_easy(bot)
    setup_sansuu_normal(bot)
    setup_sansuu_hard(bot)
    setup_avatar(bot)
    setup_dentaku(bot)
    setup_omikuji(bot)
    setup_tictactoe(bot)

# Bot起動
if TOKEN:
    async def main():
        async with bot:
            await setup_all_commands()
            await bot.start(TOKEN)

    asyncio.run(main())
else:
    print("❌ DISCORD_TOKEN が .env または Render の環境変数に設定されていないきつ")
