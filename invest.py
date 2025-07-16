import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import json
import os
import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 明示的に日本語フォントを指定（Render対応）
font_path = "assets/fonts/ipaexg.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()

from data import get_coin, update_coin

INVEST_FILE = "invest_stats.json"
MARKET_FILE = "invest_market.json"
HISTORY_FILE = "market_history.json"
PORTFOLIO_FILE = "invest_portfolio.json"

DEFAULT_MARKET = {
    "のば鉄道": {"price_per_share": 1000, "up_rate": 0.1, "down_rate": 0.05, "min_price": 500},
    "くるあパティスリー": {"price_per_share": 200, "up_rate": 0.2, "down_rate": 0.15, "min_price": 100},
    "きつね製麺": {"price_per_share": 20, "up_rate": 0.2, "down_rate": 0.1, "min_price": 10},
    "なえくん水族館": {"price_per_share": 40, "up_rate": 0.5, "down_rate": 0.25, "min_price": 20},
    "しし動物園": {"price_per_share": 60, "up_rate": 0.4, "down_rate": 0.2, "min_price": 30},
    "はむっちペットショップ": {"price_per_share": 80, "up_rate": 0.3, "down_rate": 0.2, "min_price": 40},
    "くろねこ画廊": {"price_per_share": 600, "up_rate": 0.4, "down_rate": 0.2, "min_price": 300},
    "やまとん銃工": {"price_per_share": 800, "up_rate": 0.3, "down_rate": 0.15, "min_price": 400},
    "あゆかは精肉店": {"price_per_share": 100, "up_rate": 0.1, "down_rate": 0.05, "min_price": 50},
    "ぴー貴族": {"price_per_share": 400, "up_rate": 0.5, "down_rate": 0.25, "min_price": 200},
}

def load_json(file, default={}):
    if not os.path.exists(file):
        save_json(file, default)
    try:
        with open(file, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                print(f"⚠️ {file} の構造が不正です。初期化します。")
                save_json(file, default)
                return default
            return data
    except Exception as e:
        print(f"⚠️ {file} 読み込み失敗: {e}")
        save_json(file, default)
        return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

class Invest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.market = load_json(MARKET_FILE, DEFAULT_MARKET.copy())
        self.history = load_json(HISTORY_FILE, {k: [] for k in DEFAULT_MARKET})
        self.invest_data = load_json(INVEST_FILE)
        self.portfolio = load_json(PORTFOLIO_FILE)
        self.update_prices.start()

    def cog_unload(self):
        self.update_prices.cancel()

    def save_all(self):
        save_json(MARKET_FILE, self.market)
        save_json(HISTORY_FILE, self.history)
        save_json(INVEST_FILE, self.invest_data)
        save_json(PORTFOLIO_FILE, self.portfolio)

    def log_price(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        for name, info in self.market.items():
            self.history.setdefault(name, []).append({"time": now, "price": info["price_per_share"]})
            self.history[name] = self.history[name][-1440:]

    @tasks.loop(minutes=1)
    async def update_prices(self):
        for name, info in self.market.items():
            up_rate = info.get("up_rate", 0.1)
            down_rate = info.get("down_rate", 0.1)
            min_price = info.get("min_price", 1)
            direction = random.choice(["up", "down"])
            if direction == "up":
                factor = random.uniform(1, 1 + up_rate)
            else:
                factor = random.uniform(1 - down_rate, 1)

            new_price = int(info["price_per_share"] * factor)
            info["price_per_share"] = max(int(min_price), new_price)
        self.log_price()
        self.save_all()

    async def target_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            market_data = load_json(MARKET_FILE, DEFAULT_MARKET.copy())
            choices = []
            for name, info in market_data.items():
                if not isinstance(info, dict):
                    continue
                price = info.get("price_per_share")
                if not isinstance(price, (int, float)):
                    continue
                if current.lower() in name.lower():
                    display_name = f"{name}（{price} にゃんにゃん/株）"
                    choices.append(app_commands.Choice(name=display_name[:100], value=name))
            return choices[:25]
        except Exception as e:
            print(f"[Autocomplete Error]: {e}")
            return []

    @app_commands.command(name="invest_buy", description="にゃんにゃんで株を購入するきつ！")
    @app_commands.describe(target="企業名", shares="株数（100株単位）")
    @app_commands.autocomplete(target=target_autocomplete)
    async def invest(self, interaction: discord.Interaction, target: str, shares: int):
        user_id = str(interaction.user.id)
        if shares <= 0 or shares % 100 != 0:
            return await interaction.response.send_message("❌ 株数は100株単位できつ！", ephemeral=True)
        if target not in self.market:
            return await interaction.response.send_message("❌ 無効な企業名きつ", ephemeral=True)

        price = self.market[target]["price_per_share"]
        cost = shares * price
        balance = get_coin(user_id)

        if balance < cost:
            return await interaction.response.send_message("❌ にゃんにゃんが足りないきつ！", ephemeral=True)

        update_coin(user_id, -cost)
        self.portfolio.setdefault(user_id, {}).setdefault(target, 0)
        self.portfolio[user_id][target] += shares
        self.invest_data.setdefault(user_id, {"total_invested": 0, "total_result": 0})
        self.invest_data[user_id]["total_invested"] += cost
        self.save_all()
        await interaction.response.send_message(f"✅ {target} の株を {shares} 株（{cost} にゃんにゃん）購入したきつ！")

    @app_commands.command(name="invest_sell", description="株を売却してにゃんにゃんに戻すきつ！")
    @app_commands.describe(target="企業名", shares="売る株数")
    @app_commands.autocomplete(target=target_autocomplete)
    async def sell(self, interaction: discord.Interaction, target: str, shares: int):
        user_id = str(interaction.user.id)
        if target not in self.market or shares <= 0:
            return await interaction.response.send_message("❌ 売却内容が無効きつ", ephemeral=True)
        owned = self.portfolio.get(user_id, {}).get(target, 0)
        if owned < shares:
            return await interaction.response.send_message("❌ そんなに株を持っていないきつ", ephemeral=True)

        price = self.market[target]["price_per_share"]
        revenue = shares * price
        update_coin(user_id, revenue)
        self.portfolio[user_id][target] -= shares
        if self.portfolio[user_id][target] == 0:
            del self.portfolio[user_id][target]
        if not self.portfolio[user_id]:
            del self.portfolio[user_id]
        self.invest_data.setdefault(user_id, {"total_invested": 0, "total_result": 0})
        self.invest_data[user_id]["total_result"] += revenue
        self.save_all()
        await interaction.response.send_message(f"💰 {shares} 株 売却して {revenue} にゃんにゃん を手に入れたきつ！")

    @app_commands.command(name="invest_portfolio", description="自分の保有株を確認するきつ")
    async def portfolio(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        holdings = self.portfolio.get(user_id)
        if not holdings:
            return await interaction.response.send_message("📭 株を保有していないきつ", ephemeral=True)

        embed = discord.Embed(title="📦 あなたのポートフォリオ", color=discord.Color.blue())
        total_value = 0
        for company, amount in holdings.items():
            price = self.market[company]["price_per_share"]
            value = amount * price
            total_value += value
            embed.add_field(name=company, value=f"{amount} 株（{value} にゃんにゃん）", inline=False)
        embed.set_footer(text=f"総評価額: {total_value} にゃんにゃん")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invest_chart", description="株価の履歴チャートを見るきつ")
    @app_commands.describe(target="企業名")
    @app_commands.autocomplete(target=target_autocomplete)
    async def invest_chart(self, interaction: discord.Interaction, target: str):
        if target not in self.history or not self.history[target]:
            return await interaction.response.send_message("📉 データがないきつ", ephemeral=True)
        data = self.history[target]
        times = [datetime.datetime.strptime(p["time"], "%Y-%m-%d %H:%M") for p in data]
        prices = [p["price"] for p in data]

        plt.figure(figsize=(6, 4))
        plt.plot(times, prices, marker="o", linestyle="-")
        plt.title(f"{target} の株価履歴", fontproperties=font_prop)
        plt.xlabel("時間", fontproperties=font_prop)
        plt.ylabel("株価", fontproperties=font_prop)
        plt.xticks(rotation=45, fontproperties=font_prop)
        plt.yticks(fontproperties=font_prop)
        plt.tight_layout()
        path = f"chart_{target}.png"
        plt.savefig(path)
        plt.close()
        await interaction.response.send_message(file=discord.File(path))
        os.remove(path)

    @app_commands.command(name="invest_market", description="現在の株価を一覧で見るきつ！")
    async def market(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📈 現在の株価一覧", color=discord.Color.green())
        for name, info in self.market.items():
            price = info.get("price_per_share", "?")
            embed.add_field(
                name=name,
                value=f"{price} にゃんにゃん/株",
                inline=False
            )
        embed.set_footer(text="価格は1分ごとに変動するきつ！")
        await interaction.response.send_message(embed=embed)

# セットアップ関数
async def setup(bot):
    await bot.add_cog(Invest(bot))
