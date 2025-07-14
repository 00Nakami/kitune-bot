import discord
from discord import app_commands
from discord.ext import commands
import random
from data import get_coin, update_coin
from typing import Optional

def setup_janken(bot: commands.Bot):
    @bot.tree.command(name="janken", description="他の人とPvPじゃんけん！")
    @app_commands.describe(opponent="対戦相手", bet="ベット額（にゃんにゃん）")
    async def janken(interaction: discord.Interaction, opponent: discord.Member, bet: int):
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message("相手はボット以外かつ自分以外を選んできつ！", ephemeral=True)
            return

        p1 = interaction.user
        p2 = opponent

        if get_coin(p1.id) < bet or get_coin(p2.id) < bet:
            await interaction.response.send_message("どちらかのにゃんにゃんが足りないきつ！", ephemeral=True)
            return

        view = AcceptView(p1, p2, bet)
        await interaction.response.send_message(
            f"{p2.mention} さん、{p1.display_name} さんから PvPじゃんけん（ベット: {bet} にゃんにゃん）の申し込みきつ。承諾するきつか？",
            view=view
        )
        view.message = await interaction.original_response()

class AcceptView(discord.ui.View):
    def __init__(self, p1, p2, bet):
        super().__init__(timeout=30)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        self.message: Optional[discord.Message] = None

    @discord.ui.button(label="はい", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.p2:
            await interaction.response.send_message("あなたは対戦相手ではないきつ", ephemeral=True)
            return

        try:
            await self.message.delete()
        except discord.NotFound:
            pass

        view = JankenView(self.p1, self.p2, self.bet)
        msg = await interaction.channel.send("対戦開始きつ！手を選んできつ：", view=view)
        view.ui_message = msg
        self.stop()

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.message.delete()
        except discord.NotFound:
            pass

        await interaction.response.send_message("対戦が拒否されたきつ", ephemeral=False)
        self.stop()

class JankenView(discord.ui.View):
    def __init__(self, p1, p2, bet):
        super().__init__(timeout=30)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        self.hands = {}
        self.result_shown = False
        self.ui_message: Optional[discord.Message] = None

    @discord.ui.button(label="グー ✊", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.choose_hand(interaction, "グー")

    @discord.ui.button(label="チョキ ✌️", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.choose_hand(interaction, "チョキ")

    @discord.ui.button(label="パー ✋", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.choose_hand(interaction, "パー")

    async def choose_hand(self, interaction: discord.Interaction, hand: str):
        user = interaction.user
        if user != self.p1 and user != self.p2:
            await interaction.response.send_message("あなたは対戦者ではないきつ", ephemeral=True)
            return

        if user.id in self.hands:
            await interaction.response.send_message("すでに選択済みきつ！", ephemeral=True)
            return

        self.hands[user.id] = hand
        await interaction.response.send_message(f"{user.display_name} が選んだきつ！", ephemeral=True)

        if len(self.hands) == 2 and not self.result_shown:
            self.result_shown = True  # ここで2回出るのを防ぐ
            h1 = self.hands[self.p1.id]
            h2 = self.hands[self.p2.id]

            result = f"{self.p1.display_name}: {h1}\n{self.p2.display_name}: {h2}\n"

            if h1 == h2:
                result += "**あいこ！もう1試合始めるきつ！**"

                if self.ui_message:
                    try:
                        await self.ui_message.delete()
                    except discord.NotFound:
                        pass

                await interaction.followup.send(result)

                new_view = JankenView(self.p1, self.p2, self.bet)
                new_msg = await interaction.channel.send("再試合！手を選んできつ：", view=new_view)
                new_view.ui_message = new_msg
                self.stop()
                return

            # 勝敗処理
            if (
                (h1 == "グー" and h2 == "チョキ") or
                (h1 == "チョキ" and h2 == "パー") or
                (h1 == "パー" and h2 == "グー")
            ):
                update_coin(self.p1.id, self.bet)
                update_coin(self.p2.id, -self.bet)
                result += f"**{self.p1.display_name} の勝ちきつ！ {self.bet} にゃんにゃん獲得きつ！**"
            else:
                update_coin(self.p1.id, -self.bet)
                update_coin(self.p2.id, self.bet)
                result += f"**{self.p2.display_name} の勝ちきつ！ {self.bet} にゃんにゃん獲得きつ！**"

            if self.ui_message:
                try:
                    await self.ui_message.delete()
                except discord.NotFound:
                    pass

            await interaction.followup.send(result)
            self.stop()
