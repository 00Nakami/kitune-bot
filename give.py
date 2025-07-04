from discord import app_commands
import discord
from data import get_coin, update_coin

def setup_give(bot):
    @bot.tree.command(name="give", description="他のユーザーににゃんにゃんを渡すきつ")
    @app_commands.describe(user="渡す相手", amount="渡すにゃんにゃんの数")
    async def give(interaction: discord.Interaction, user: discord.Member, amount: int):
        giver = interaction.user

        if user.bot:
            await interaction.response.send_message("Botにはにゃんにゃんを渡せないきつ", ephemeral=True)
            return

        if giver.id == user.id:
            await interaction.response.send_message("自分ににゃんにゃんを渡すことはできないきつ", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("渡すにゃんにゃんの数は1以上で指定してきつ", ephemeral=True)
            return

        giver_coins = get_coin(giver.id)
        if giver_coins < amount:
            await interaction.response.send_message(f"にゃんにゃんが足りないきつ。現在の所持: {giver_coins}", ephemeral=True)
            return

        update_coin(giver.id, -amount)
        update_coin(user.id, amount)

        await interaction.response.send_message(
            f"{giver.mention} さんが {user.mention} さんに {amount} にゃんにゃんを渡したきつ！"
        )
