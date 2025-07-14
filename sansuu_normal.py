import random
import asyncio
import discord
from discord.ext import commands
from data import get_coin, update_coin  # ✅ save_data は不要

def setup_sansuu_normal(bot: commands.Bot):
    @bot.tree.command(name="sansuu_normal", description="計算問題に正解してにゃんにゃんをゲットするきつ！")
    async def sansuu_normal(interaction: discord.Interaction):
        user_id = interaction.user.id

        # 初回ユーザーに1000にゃんにゃん付与
        if get_coin(user_id) == 0:
            update_coin(user_id, 1000)

        # 問題の種類と難易度設定
        operators = ['+', '-', '×']
        operator = random.choice(operators)

        if operator == '+':
            a, b = random.randint(100, 999), random.randint(100, 999)
            answer = a + b
        elif operator == '-':
            a, b = sorted([random.randint(10, 99), random.randint(10, 99)], reverse=True)
            answer = a - b
        else:  # ×
            a, b = random.randint(1, 9), random.randint(1, 9)
            answer = a * b

        question = f"{a} {operator} {b} = ?"

        embed = discord.Embed(
            title="📘 算数（普通）",
            description=question,
            color=discord.Color.green()
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
                reward = random.randint(50, 150)
                update_coin(user_id, reward)
                await user_msg.reply(f"🎉 正解きつ！ +{reward} にゃんにゃんゲットきつ！\n🪙 所持：{get_coin(user_id)} にゃんにゃん")
            else:
                await user_msg.reply(f"❌ 不正解きつ…正解は `{answer}` だったきつ。")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"⌛ 時間切れきつ…正解は `{answer}` だったきつ。", ephemeral=True)
