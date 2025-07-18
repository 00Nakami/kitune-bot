import discord
from discord import app_commands
from discord.ext import commands
import random
import os
import json

from data import get_coin, update_coin

ITEMS_PATH = os.path.join(os.path.dirname(__file__), "data", "items.json")
GACHA_STATS_PATH = os.path.join(os.path.dirname(__file__), "data", "gacha_stats.json")
os.makedirs(os.path.dirname(ITEMS_PATH), exist_ok=True)

# 所持アイテムの読み書き
def load_items():
    try:
        with open(ITEMS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_items(items_data):
    with open(ITEMS_PATH, "w", encoding="utf-8") as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)

# ガチャ回数の読み書き
def load_gacha_stats():
    try:
        with open(GACHA_STATS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_gacha_stats(stats):
    with open(GACHA_STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ガチャのラインナップ
GACHA_ITEMS = [
    {"name": "⬜🦊白狐", "rarity": "Secret", "rate": 0.05},
    {"name": "👶🐧赤ちゃんペンギン", "rarity": "Secret", "rate": 0.05},
    {"name": "⛄️雪だるま", "rarity": "Mythic", "rate": 0.3},
    {"name": "🚊鉄道", "rarity": "Mythic", "rate": 0.3},
    {"name": "🔫ピストル", "rarity": "Mythic", "rate": 0.3},
    {"name": "🐈‍⬛くろねこ", "rarity": "Legendary", "rate": 0.5},
    {"name": "🍣中トロ", "rarity": "Legendary", "rate": 0.5},
    {"name": "🥓ベーコン", "rarity": "Legendary", "rate": 0.5},
    {"name": "🦁ライオン", "rarity": "Legendary", "rate": 0.5},
    {"name": "🎂ケーキ", "rarity": "Epic", "rate": 1.6},
    {"name": "🐹ハムスター", "rarity": "Epic", "rate": 1.6},
    {"name": "🐱ねこ", "rarity": "Epic", "rate": 1.6},
    {"name": "🐦鳥", "rarity": "Epic", "rate": 1.6},
    {"name": "🪄魔法の杖", "rarity": "Epic", "rate": 1.6},
    {"name": "🐟鮎", "rarity": "Rare", "rate": 3.5},
    {"name": "🦊きつね", "rarity": "Rare", "rate": 3.5},
    {"name": "🐧ぺんぎん", "rarity": "Rare", "rate": 3.5},
    {"name": "📃紙", "rarity": "Rare", "rate": 3.5},
    {"name": "🍣大トロ", "rarity": "Rare", "rate": 3.5},
    {"name": "🧊氷", "rarity": "Rare", "rate": 3.5},
    {"name": "🍨アイスクリーム", "rarity": "Uncommon", "rate": 4},
    {"name": "🐯虎", "rarity": "Uncommon", "rate": 4},
    {"name": "❄️雪の結晶", "rarity": "Uncommon", "rate": 4},
    {"name": "🍔ハンバーガー", "rarity": "Uncommon", "rate": 4},
    {"name": "🏓ラケット", "rarity": "Uncommon", "rate": 4},
    {"name": "🀄麻雀", "rarity": "Uncommon", "rate": 4},
    {"name": "🛏️ベッド", "rarity": "Uncommon", "rate": 4},
    {"name": "🖼️絵", "rarity": "Common", "rate": 5},
    {"name": "🌲木", "rarity": "Common", "rate": 5},
    {"name": "🚉駅", "rarity": "Common", "rate": 5},
    {"name": "🍑もも", "rarity": "Common", "rate": 5},
    {"name": "🕸️蜘蛛の巣", "rarity": "Common", "rate": 5},
    {"name": "🦷歯", "rarity": "Common", "rate": 5},
    {"name": "🌱草", "rarity": "Common", "rate": 5},
    {"name": "🍜ラーメン", "rarity": "Common", "rate": 5},
]

RARITY_ORDER = {"Secret": 0, "Mythic": 1, "Legendary": 2, "Epic": 3, "Rare": 4, "Uncommon": 5, "Common": 6}

def get_rarity(item_name):
    for item in GACHA_ITEMS:
        if item["name"] == item_name:
            return item["rarity"]
    return "N"

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gacha", description="にゃんにゃんを使ってガチャを引くきつ（1回1000にゃんにゃん）")
    @app_commands.describe(number="引く回数（最大1000）")
    async def gacha(self, interaction: discord.Interaction, number: int = 1):
        await interaction.response.defer()

        number = max(1, min(1000, number))
        cost = 1000 * number
        user_id = interaction.user.id

        coin = get_coin(user_id)
        if coin < cost:
            await interaction.followup.send("にゃんにゃんが足りないきつ！", ephemeral=True)
            return

        update_coin(user_id, -cost)
        remaining = get_coin(user_id)

        pool = []
        for item in GACHA_ITEMS:
            pool += [item] * int(item["rate"] * 100)

        results = {}
        for _ in range(number):
            result = random.choice(pool)
            name = result["name"]
            results[name] = results.get(name, 0) + 1

        # 所持アイテム保存
        items = load_items()
        user_items = items.get(str(user_id), {})
        for name, count in results.items():
            user_items[name] = user_items.get(name, 0) + count
        items[str(user_id)] = user_items
        save_items(items)

        # 回数加算
        stats = load_gacha_stats()
        stats[str(user_id)] = stats.get(str(user_id), 0) + number
        save_gacha_stats(stats)

        rarity_results = {}
        for name, count in results.items():
            rarity = get_rarity(name)
            rarity_results.setdefault(rarity, []).append((name, count))

        embed = discord.Embed(
            title=f"🎉 ガチャ結果！（{number}回）",
            description=f"{interaction.user.mention} さんの結果：\n💰 残高：{remaining:,} にゃんにゃん",
            color=discord.Color.blurple()
        )
        for rarity in sorted(rarity_results, key=lambda r: RARITY_ORDER.get(r, 99)):
            lines = [f"- {name} ×{count}" for name, count in rarity_results[rarity]]
            embed.add_field(name=f"{rarity}（{len(rarity_results[rarity])}種）", value="\n".join(lines), inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gacha_index", description="自分が集めたアイテムの図鑑を表示するきつ")
    async def gacha_index(self, interaction: discord.Interaction):
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        items = load_items()
        user_items = items.get(user_id, {})

        embed = discord.Embed(
            title=f"{interaction.user.display_name} さんのアイテム図鑑",
            description="所持済み：✅　未所持：❔",
            color=discord.Color.green()
        )

        rarity_dict = {r: [] for r in RARITY_ORDER}
        for item in GACHA_ITEMS:
            name = item["name"]
            rarity = item["rarity"]
            count = user_items.get(name, 0)
            symbol = "✅" if count > 0 else "❔"
            display = f"{symbol} {name if count > 0 else '???'} ×{count}"
            rarity_dict[rarity].append(display)

        for rarity in sorted(RARITY_ORDER, key=lambda r: RARITY_ORDER[r]):
            lines = rarity_dict.get(rarity, [])
            if lines:
                embed.add_field(name=f"{rarity}（{len(lines)}種）", value="\n".join(lines), inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gacha_list", description="ガチャの排出アイテムと確率一覧を表示するきつ")
    async def gacha_list(self, interaction: discord.Interaction):
        await interaction.response.defer()

        rarity_groups = {}
        total_rate = sum(item["rate"] for item in GACHA_ITEMS)

        for item in GACHA_ITEMS:
            rarity = item["rarity"]
            rarity_groups.setdefault(rarity, []).append({
                "name": "❔ ???" if rarity == "Secret" else item["name"],
                "chance": item["rate"] / total_rate * 100
            })

        embed = discord.Embed(
            title="🎁 ガチャ排出一覧",
            description="現在のガチャで出るアイテムと確率：",
            color=discord.Color.teal()
        )

        for rarity in sorted(RARITY_ORDER, key=lambda r: RARITY_ORDER[r]):
            group = rarity_groups.get(rarity, [])
            if not group:
                continue
            total_rarity_chance = sum(item["chance"] for item in group)
            item_lines = [f"{item['name']} - {item['chance']:.2f}%" for item in group]
            embed.add_field(name=f"{rarity}（{len(group)}種 / 合計{total_rarity_chance:.2f}%）", value="\n".join(item_lines), inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gacha_ranking", description="ガチャの回数または図鑑埋まりランキングを表示するきつ")
    @app_commands.describe(mode="times or index")
    async def gacha_ranking(self, interaction: discord.Interaction, mode: str):
        await interaction.response.defer()

        items = load_items()
        stats = load_gacha_stats()
        ranking = []

        if mode == "times":
            ranking = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            title = "🎲 ガチャ回数ランキング"
            lines = [f"{i+1}. <@{uid}>：{count}回" for i, (uid, count) in enumerate(ranking[:10])]
        elif mode == "index":
            for uid, user_items in items.items():
                owned = sum(1 for name in user_items if user_items[name] > 0)
                ranking.append((uid, owned))
            ranking.sort(key=lambda x: x[1], reverse=True)
            title = "📖 図鑑埋まりランキング"
            lines = [f"{i+1}. <@{uid}>：{count}種" for i, (uid, count) in enumerate(ranking[:10])]
        else:
            await interaction.followup.send("`mode` は `times` か `index` のどちらかを指定してください。", ephemeral=True)
            return

        embed = discord.Embed(title=title, description="\n".join(lines), color=discord.Color.gold())
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Gacha(bot))
