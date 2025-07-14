import random
import asyncio
import discord
from discord.ext import commands
from data import get_coin, update_coin  # ✅ save_data は不要

def setup_sansuu_hard(bot: commands.Bot):
    @bot.tree.command(name="sansuu_hard", description="計算問題に正解してにゃんにゃんをゲットするきつ！")
    async def sansuu_hard(interaction: discord.Interaction):
        user_id = interaction.user.id

        # 初回プレイヤーに初期にゃんにゃん付与
        if get_coin(user_id) == 0:
            update_coin(user_id, 1000)

        # 難しい計算問題生成（+、-、×）
        operators = ['+', '-', '×']
        operator = random.choice(operators)

        if operator == '+':
            a, b = random.randint(1000, 9999), random.randint(1000, 9999)
            answer = a + b
        elif operator == '-':
            a, b = sorted([random.randint(100, 999), random.randint(100, 999)], reverse=True)
            answer = a - b
        else:  # ×
            a, b = random.randint(10, 99), random.randint(10, 99)
            answer = a * b

        question = f"{a} {operator} {b} = ?"

        embed = discord.Embed(
            title="📐 算数（難しい）",
            description=question,
            color=discord.Color.red()
        )
        embed.set_footer(text="⏱ 15秒以内に正しい数字をチャットで答えてきつ！")
        await interaction.response.send_message(embed=embed)

        def check(msg):
            return (
                msg.author.id == user_id and
                msg.channel == interaction.channel and
                msg.content.strip().lstrip('-').isdigit()
            )

        try:
            user_msg = await bot.wait_for("message", timeout=15.0, check=check)
            user_answer = int(user_msg.content.strip())
            if user_answer == answer:
                reward = random.randint(500, 1500)
                update_coin(user_id, reward)
                await user_msg.reply(f"🎉 正解きつ！ +{reward} にゃんにゃんゲットきつ！\n🪙 所持：{get_coin(user_id)} にゃんにゃん")
            else:
                await user_msg.reply(f"❌ 不正解きつ…正解は `{answer}` だったきつ。")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"⌛ 時間切れきつ…正解は `{answer}` だったきつ。", ephemeral=True)
