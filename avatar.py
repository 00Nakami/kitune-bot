import discord
from discord import app_commands

def setup_avatar(bot):
    @bot.tree.command(name="avatar", description="ユーザーのアバターを表示するきつ")
    @app_commands.describe(user="アバターを表示したいユーザー（指定しないと自分）")
    async def avatar(interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        avatar_url = target.display_avatar.url  # discord.py v2.0以降の推奨方法
        
        embed = discord.Embed(title=f"{target.display_name} のアバター", color=discord.Color.blurple())
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"ID: {target.id}")

        await interaction.response.send_message(embed=embed)

