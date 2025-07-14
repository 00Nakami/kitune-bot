import discord
from discord import app_commands
from data import get_coin

def setup_nyan(bot):
    @bot.tree.command(name="nyan", description="にゃんにゃんの所持金を表示するきつ")
    @app_commands.describe(user="確認したいユーザー（指定しないと自分）")
    async def nyan(interaction: discord.Interaction, user: discord.User = None):
        """指定したユーザー、または自分の所持にゃんにゃんを表示する"""
        target = user or interaction.user
        coin = get_coin(target.id)
        await interaction.response.send_message(
            f"{target.display_name} さんの所持にゃんにゃん：**{coin}** にゃんにゃん 💰"
        )
