import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
import asyncio
import datetime
import matplotlib.pyplot as plt

from data import get_coin, update_coin

INVEST_FILE = "invest_stats.json"
MARKET_FILE = "invest_market.json"
HISTORY_FILE = "market_history.json"

DEFAULT_MARKET = {
    "にゃんこ証券": {"price_per_share": 12, "gain_range": [1.1, 1.4], "loss_range": [0.6, 0.9], "wait_seconds": 5},
    "もちもち銀行": {"price_per_share": 18, "gain_range": [1.2, 1.6], "loss_range": [0.4, 0.8], "wait_seconds": 7},
    "たこやき産業": {"price_per_share": 8, "gain_range": [1.05, 1.2], "loss_range": [0.7, 0.95], "wait_seconds": 4},
    "ペンギン重工": {"price_per_share": 20, "gain_range": [1.3, 1.8], "loss_range": [0.3, 0.7], "wait_seconds": 6}
}

def load_json(file, default={}):
    if not os.path.exists(file):
        save_json(file, default)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

class Invest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invest_data = load_json(INVEST_FILE)
        self.market = load_json(MARKET_FILE)
        self.history = load_json(HISTORY_FILE, {k: [] for k in DEFAULT_MARKET})

    def save_all(self):
        save_json(INVEST_FILE, self.invest_data)
        save_json(MARKET_FILE, self.market)
        save_json(HISTORY_FILE, self.history)

    def update_stats(self, user_id: str, amount: int, result: int):
        user_id = str(user_id)
        stats = self.invest_data.setdefault(user_id, {
            "total_invested": 0, "total_result": 0, "count": 0, "successes": 0, "fails": 0
        })
        stats["total_invested"] += amount
        stats["total_result"] += result
        stats["count"] += 1
        if result > 0:
            stats["successes"] += 1
        elif result < 0:
            stats["fails"] += 1

    def log_price(self, target):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        price = self.market[target]["price_per_share"]
        self.history[target].append({"time": now, "price": price})
        self.history[target] = self.history[target][-30:]  # 直近30件に制限

    async def target_autocomplete(self, interaction: discord.Interaction, current: str):
        return [app_commands.Choice(name=name, value=name) for name in self.market if current.lower() in name.lower()][:25]

    @app_commands.command(name="invest", description="にゃんにゃんを投資してみよう！")
    @app_commands.describe(shares="株数（100株単位）", target="投資先")
    @app_commands.autocomplete(target=target_autocomplete)
    async def invest(self, interaction: discord.Interaction, shares: int, target: str):
        user_id = str(interaction.user.id)
        current = get_coin(user_id)

        if shares <= 0 or shares % 100 != 0:
            return await interaction.response.send_message("❌ 株数は100株単位で指定してきつ！", ephemeral=True)

        if target not in self.market:
            return await interaction.response.send_message("❌ 投資先が無効きつ！", ephemeral=True)

        info = self.market[target]
        cost = shares * info["price_per_share"]

        if current < cost:
            return await interaction.response.send_message("❌ にゃんにゃんが足りないきつ！", ephemeral=True)

        update_coin(user_id, -cost)
        await interaction.response.send_message(f"📤 {target} に {shares} 株（{cost} にゃんにゃん）を投資したきつ…結果を待つきつ…（{info['wait_seconds']}秒）")

        await asyncio.sleep(info["wait_seconds"])

        outcome = random.choices(["gain", "loss", "double", "fail"], weights=[35, 35, 20, 10])[0]
        result = 0

        if outcome == "gain":
            result = int(cost * random.uniform(*info["gain_range"]))
            info["price_per_share"] += 1
            msg = f"📈 {target} が上昇！{result - cost} にゃんにゃんの利益きつ！"
        elif outcome == "double":
            result = cost * 2
            info["price_per_share"] += 2
            msg = f"💹 {target} が爆上げ！投資が2倍になったきつ！"
        elif outcome == "loss":
            result = int(cost * random.uniform(*info["loss_range"]))
            info["price_per_share"] = max(1, info["price_per_share"] - 1)
            msg = f"📉 {target} が下落…{cost - result} にゃんにゃんの損失きつ。"
        else:
            result = 0
            info["price_per_share"] = max(1, info["price_per_share"] - 2)
            msg = f"💥 {target} が大暴落！投資が全損したきつ…"

        update_coin(user_id, result)
        self.update_stats(user_id, cost, result - cost)
        self.log_price(target)
        self.save_all()

        await interaction.followup.send(f"{msg}\n💰 残高: {get_coin(user_id)} にゃんにゃん")

    @app_commands.command(name="invest_stats", description="自分の投資成績を見るきつ")
    async def invest_stats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = self.invest_data.get(user_id)
        if not data:
            return await interaction.response.send_message("まだ投資記録がないきつ", ephemeral=True)

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
            embed.add_field(name=f"{i}. {name}", value=f"損益: {stats['total_result']} にゃんにゃん\n投資額: {stats['total_invested']} にゃんにゃん", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invest_chart", description="企業の株価履歴チャートを表示")
    @app_commands.describe(target="企業名")
    @app_commands.autocomplete(target=target_autocomplete)
    async def invest_chart(self, interaction: discord.Interaction, target: str):
        if target not in self.history or not self.history[target]:
            await interaction.response.send_message("📉 株価履歴がないきつ！", ephemeral=True)
            return

        data = self.history[target]
        times = [datetime.datetime.strptime(p["time"], "%Y-%m-%d %H:%M") for p in data]
        prices = [p["price"] for p in data]

        plt.figure(figsize=(6, 4))
        plt.plot(times, prices, marker="o", linestyle="-")
        plt.title(f"{target} の株価履歴")
        plt.xlabel("時間")
        plt.ylabel("株価")
        plt.xticks(rotation=45)
        plt.tight_layout()

        path = f"chart_{target}.png"
        plt.savefig(path)
        plt.close()

        await interaction.response.send_message(file=discord.File(path))
        os.remove(path)

# セットアップ関数
async def setup(bot):
    await bot.add_cog(Invest(bot))
