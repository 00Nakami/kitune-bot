import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os

from data import get_coin, update_coin

INVEST_FILE = "invest_stats.json"

def load_invest_data():
    if not os.path.exists(INVEST_FILE):
        return {}
    with open(INVEST_FILE, "r") as f:
        return json.load(f)

def save_invest_data(data):
    with open(INVEST_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Invest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invest_data = load_invest_data()

    def update_stats(self, user_id: str, amount: int, result: int):
        user_id = str(user_id)
        if user_id not in self.invest_data:
            self.invest_data[user_id] = {
                "total_invested": 0,
                "total_result": 0,
                "count": 0,
                "successes": 0,
                "fails": 0
            }
        self.invest_data[user_id]["total_invested"] += amount
        self.invest_data[user_id]["total_result"] += result
        self.invest_data[user_id]["count"] += 1
        if result > 0:
            self.invest_data[user_id]["successes"] += 1
        elif result < 0:
            self.invest_data[user_id]["fails"] += 1
        save_invest_data(self.invest_data)

    @app_commands.command(name="invest", description="にゃんにゃんを投資してみよう！")
    @app_commands.describe(amount="投資額（にゃんにゃん）")
    async def invest(self, interaction: discord.Interaction, amount: int):
        user = interaction.user
        user_id = str(user.id)
        current = get_coin(user_id)

        if amount <= 0:
            await interaction.response.send_message("❌ 投資額は1以上にするきつ！", ephemeral=True)
            return

        if current < amount:
            await interaction.response.send_message("❌ にゃんにゃんが足りないきつ！", ephemeral=True)
            return

        outcome = random.choices(
            population=["gain", "loss", "double", "fail"],
            weights=[35, 35, 20, 10],
            k=1
        )[0]

        if outcome == "gain":
            result = int(amount * random.uniform(1.1, 1.5))
            message = f"📈 投資成功！{result - amount}にゃんにゃんの利益きつ！"
        elif outcome == "double":
            result = amount * 2
            message = f"💹 大成功！投資が2倍になったきつ！"
        elif outcome == "loss":
            result = int(amount * random.uniform(0.3, 0.9))
            message = f"📉 損失発生…{amount - result}にゃんにゃんの損失きつ。"
        else:
            result = 0
            message = f"💥 大失敗！投資が全損したきつ…"

        update_coin(user_id, result - amount)
        self.update_stats(user_id, amount, result - amount)

        await interaction.response.send_message(f"{message}\n💰 残高: {get_coin(user_id)}にゃんにゃん")

    @app_commands.command(name="invest_stats", description="自分の投資成績を見るきつ")
    async def invest_stats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = self.invest_data.get(user_id)
        if not data:
            await interaction.response.send_message("まだ投資記録がないきつ", ephemeral=True)
            return

        embed = discord.Embed(title=f"📊 {interaction.user.display_name} の投資成績", color=discord.Color.gold())
        embed.add_field(name="総投資額", value=f"{data['total_invested']} にゃんにゃん")
        embed.add_field(name="総損益", value=f"{data['total_result']} にゃんにゃん")
        embed.add_field(name="回数", value=f"{data['count']} 回")
        embed.add_field(name="成功", value=f"{data['successes']} 回")
        embed.add_field(name="失敗", value=f"{data['fails']} 回")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invest_ranking", description="投資成績ランキングを表示")
    async def invest_ranking(self, interaction: discord.Interaction):
        sorted_users = sorted(self.invest_data.items(), key=lambda x: x[1]["total_result"], reverse=True)[:10]
        embed = discord.Embed(title="🏆 投資成績ランキング", color=discord.Color.green())

        for i, (uid, stats) in enumerate(sorted_users, 1):
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"ユーザー({uid})"
            embed.add_field(
                name=f"{i}. {name}",
                value=f"損益: {stats['total_result']} にゃんにゃん\n投資額: {stats['total_invested']} にゃんにゃん",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

# セットアップ関数
async def setup(bot):
    await bot.add_cog(Invest(bot))
