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
import meigen
from giveaway import Giveaway
import discord.opus
discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.5.2/lib/libopus.dylib')  # ✅ opusライブラリの読み込み
from omikuji import setup_omikuji
from roulette import setup as setup_roulette
from tictactoe import setup_tictactoe

# .envファイルからトークン読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# データ読み込み（全体）
load_all_data()

# Botの初期設定
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='/', intents=intents)

# 起動時イベント
@bot.event
async def on_ready():
    await bot.add_cog(Giveaway(bot))
    
    # ✅ TTSのCog登録（遅延importで初期化順エラー回避）
    from tts import setup as setup_tts
    await setup_tts(bot)

    await setup_roulette(bot)
    await bot.load_extension("nyan_ranking")
    await bot.load_extension("help")

    await bot.tree.sync()
    print(f"✅ ログイン完了: {bot.user}")

# メッセージ監視（名言GIF専用）
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # 名言GIF用（@Botへのリプライ）
    if message.reference and bot.user in message.mentions:
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
            original_text = ref_msg.content.strip()
            author = ref_msg.author

            if not original_text:
                await message.channel.send("⚠️ リプライ先のメッセージにテキストがないきつ")
                return

            # data.py経由で名言を保存
            add_quote(author.id, {
                "text": original_text,
                "timestamp": str(ref_msg.created_at)
            })

            user_quotes = get_quotes(author.id)
            texts = [q["text"] for q in user_quotes]
            timestamps = [q["timestamp"] for q in user_quotes]

            await meigen.create_credits_gif_and_send(
                texts,
                message.channel,
                bot.user,
                author,
                timestamps,
                ref_msg
            )

        except Exception as e:
            await message.channel.send(f"❌ エラーが発生したきつ: {e}")

    await bot.process_commands(message)

# 各種コマンドを登録
setup_janken(bot)
setup_nyan(bot)
setup_slot(bot)
bj.setup_bj(bot)
give.setup_give(bot)
setup_sansuu_easy(bot)
setup_sansuu_normal(bot)
setup_sansuu_hard(bot)
setup_avatar(bot)
setup_dentaku(bot)
setup_omikuji(bot)
setup_tictactoe(bot)

# Bot起動
bot.run(TOKEN)
