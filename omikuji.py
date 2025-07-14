import discord
from discord.ext import commands
import random
import time
from data import get_coin, update_coin

# 1時間 = 3600秒
COOLDOWN_SECONDS = 3600

# ユーザーごとの最終おみくじ時間（メモリ上）
last_omikuji_time = {}

def setup_omikuji(bot: commands.Bot):
    @bot.tree.command(name="kitumikuji", description="今日の運勢を占ってにゃんにゃんをゲットするきつ！")
    async def omikuji(interaction: discord.Interaction):
        user_id = interaction.user.id
        user_id_str = str(user_id)  # ⏱ メモリキャッシュ用のキーとしては str を使用
        now = time.time()

        # クールダウンチェック
        last_time = last_omikuji_time.get(user_id_str, 0)
        if now - last_time < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_time))
            minutes = remaining // 60
            seconds = remaining % 60
            await interaction.response.send_message(
                f"⏳ おみくじは1時間に1回だけきつ！\nあと {minutes}分{seconds}秒 とまととまって！！",
                ephemeral=True
            )
            return

        # おみくじ内容と報酬
        fortunes = [
            ("🌟 大狐", "きた！", 1000),
            ("😊 中狐", "もうちょいなんだよなー", 500),
            ("🙂 小狐", "ほい小狐", 200),
            ("😐 狐", "えこれめっちゃいい", 100),
            ("😶 末狐", "ふーん", 50),
            ("😢 苗", "最悪杉", 10),
            ("💀 大苗", "オワッタ", 0),
        ]

        fortune, description, reward = random.choice(fortunes)

        # にゃんにゃんコイン更新
        update_coin(user_id, reward)
        new_coin = get_coin(user_id)

        # 埋め込みメッセージ構築
        embed = discord.Embed(
            title=f"🎴 おみくじの結果：{fortune}",
            description=f"{description}\n**{'+' if reward >= 0 else ''}{reward} にゃんにゃん**",
            color=discord.Color.random()
        )
        embed.set_footer(text=f"現在の所持にゃんにゃん：{new_coin} にゃんにゃん 💰")

        await interaction.response.send_message(embed=embed)

        # 最終実行時間を記録
        last_omikuji_time[user_id_str] = now
