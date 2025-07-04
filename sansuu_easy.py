import random
import asyncio
import discord
from discord.ext import commands
from data import get_coin, update_coin, save_data

def setup_sansuu_easy(bot: commands.Bot):
    @bot.tree.command(name="sansuu_easy", description="計算問題に正解してにゃんにゃんをゲットするきつ！")
    async def sansuu_easy(interaction: discord.Interaction):
        user_id = interaction.user.id

        if get_coin(user_id) == 0:
            update_coin(user_id, 1000)

        operators = ['+', '-']
        operator = random.choice(operators)

        if operator == '+':
            a = random.randint(10, 99)
            b = random.randint(10, 99)
        else:
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            if b > a:
                a, b = b, a

        answer = a + b if operator == '+' else a - b
        question = f"{a} {operator} {b} = ?"

        embed = discord.Embed(
            title="算数（簡単）",
            description=question,
            color=discord.Color.blurple()
        )
        embed.set_footer(text="15秒以内に正しい数字をチャットで答えてきつ！")
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
                reward = random.randint(5, 15)
                update_coin(user_id, reward)
                save_data()
                await user_msg.reply(f"🎉 正解きつ！ +{reward}にゃんにゃんゲットきつ！\n🪙 所持にゃんにゃん：{get_coin(user_id)}にゃんにゃん")
            else:
                await user_msg.reply(f"❌ 残念きつ…答えは `{answer}` だったきつ。")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"⌛ 時間切れきつ…答えは `{answer}` だったきつ。", ephemeral=True)
