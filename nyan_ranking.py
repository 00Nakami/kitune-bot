import discord
from discord.ext import commands
from discord import app_commands
from data import coins  # 所持にゃんにゃんデータ（辞書）

class NyanRanking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nyan_ranking", description="にゃんにゃんの所持金ランキングを表示するきつ")
    async def nyan_ranking(self, interaction: discord.Interaction):
        # 上位10名を取得
        sorted_coins = sorted(coins.items(), key=lambda x: x[1], reverse=True)[:10]
        description = ""

        for i, (uid, amount) in enumerate(sorted_coins, 1):
            try:
                user = self.bot.get_user(int(uid)) or await self.bot.fetch_user(int(uid))
                name = user.name if user else f"不明なユーザー({uid})"
                description += f"**{i}位** {name}：💰 {amount} にゃんにゃん\n"
            except Exception:
                description += f"**{i}位** 不明なユーザー({uid})：💰 {amount} にゃんにゃん\n"

        if not description:
            description = "ランキングデータがないきつ"

        embed = discord.Embed(
            title="🏆 にゃんにゃんランキング TOP10",
            description=description,
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

# ✅ setup関数でCogを登録
async def setup(bot):
    await bot.add_cog(NyanRanking(bot))
