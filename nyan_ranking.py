import discord
from discord.ext import commands
from discord import app_commands
from data import get_all_coins
import asyncio

class NyanRanking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nyan_ranking", description="にゃんにゃんの所持金ランキングを表示するきつ")
    async def nyan_ranking(self, interaction: discord.Interaction):
        all_coins = get_all_coins()

        if not all_coins:
            await interaction.response.send_message("ランキングデータがないきつ", ephemeral=True)
            return

        sorted_coins = sorted(all_coins.items(), key=lambda x: x[1], reverse=True)[:10]

        embed = discord.Embed(
            title="🏆 にゃんにゃんランキング TOP10",
            color=discord.Color.orange()
        )

        async def get_user_name(uid: int):
            user = self.bot.get_user(uid)
            if user:
                return user.name
            try:
                user = await self.bot.fetch_user(uid)
                return user.name
            except:
                return f"不明なユーザー({uid})"

        # ユーザー名の取得を並列処理（最大10件なので問題なし）
        user_names = await asyncio.gather(*(get_user_name(int(uid)) for uid, _ in sorted_coins))

        description = ""
        for i, ((uid, amount), name) in enumerate(zip(sorted_coins, user_names), 1):
            description += f"**{i}位** {name}：💰 {amount} にゃんにゃん\n"

        embed.description = description
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(NyanRanking(bot))
