import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
import asyncio

from data import get_coin, update_coin

INVEST_FILE = "invest_stats.json"

# 投資先データ定義
INVEST_OPTIONS = {
    "にゃんこ証券": {
        "price_per_share": 12,
        "wait_seconds": 5,
        "gain_range": (1.1, 1.4),
        "loss_range": (0.6, 0.9)
    },
    "もちもち銀行": {
        "price_per_share": 18,
        "wait_seconds": 7,
        "gain_range": (1.2, 1.6),
        "loss_range": (0.4, 0.8)
    },
    "たこやき産業": {
        "price_per_share": 8,
        "wait_seconds": 4,
        "gain_range": (1.05, 1.2),
        "loss_range": (0.7, 0.95)
    },
    "ペンギン重工": {
        "price_per_share": 20,
        "wait_seconds": 6,
        "gain_range": (1.3, 1.8),
        "loss_range": (0.3, 0.7)
    }
}

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
    @app_commands.describe(
        target="投資先（省略でランダム）",
        shares="株数（100株単位）"
    )
    async def invest(self, interaction: discord.Interaction, shares: int, target: str = None):
        user = interaction.user
        user_id = str(user.id)
        current = get_coin(user_id)

        if shares <= 0 or shares % 100 != 0:
            await interaction.response.send_message("❌ 株数は100株単位で指定するきつ！", ephemeral=True)
            return

        if target:
            if target not in INVEST_OPTIONS:
                await interaction.response.send_message("❌ 投資先が無効きつ！", ephemeral=True)
                return
        else:
            target = random.choice(list(INVEST_OPTIONS.keys()))

        option = INVEST_OPTIONS[target]
        total_cost = shares * option["price_per_share"]

        if current < total_cost:
            await interaction.response.send_message("❌ にゃんにゃんが足りないきつ！", ephemeral=True)
            return

        update_coin(user_id, -total_cost)
        await interaction.response.send_message(
            f"📤 {target} に {shares} 株（{total_cost} にゃんにゃん）を投資したきつ…結果を待つきつ…（{option['wait_seconds']}秒）")

        await asyncio.sleep(option["wait_seconds"])

        outcome = random.choices(
            population=["gain", "loss", "double", "fail"],
            weights=[35, 35, 20, 10],
            k=1
        )[0]

        if outcome == "gain":
            multiplier = random.uniform(*option["gain_range"])
            result = int(total_cost * multiplier)
            message = f"📈 {target} が上昇！{result - total_cost} にゃんにゃんの利益きつ！"
        elif outcome == "double":
            result = total_cost * 2
            message = f"💹 {target} が爆上げ！投資が2倍になったきつ！"
        elif outcome == "loss":
            multiplier = random.uniform(*option["loss_range"])
            result = int(total_cost * multiplier)
            message = f"📉 {target} が下落…{total_cost - result} にゃんにゃんの損失きつ。"
        else:
            result = 0
            message = f"💥 {target} が大暴落！投資が全損したきつ…"

        update_coin(user_id, result)
        self.update_stats(user_id, total_cost, result - total_cost)

        await interaction.followup.send(f"{message}\n💰 残高: {get_coin(user_id)} にゃんにゃん")

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
