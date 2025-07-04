import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from functools import partial
from data import get_coin, update_coin  # ✅ 共通通貨管理

COLOR_POOL = ["red"] * 49 + ["black"] * 49 + ["green"] * 2
BET_AMOUNTS = [100, 500, 1000, 5000, 10000]

def get_emoji(color):
    return {"red": "🔴", "black": "⚫", "green": "🟢"}.get(color, "❓")

class BetAmount(discord.ui.View):
    def __init__(self, roulette_view, user_id):
        super().__init__(timeout=60)
        self.roulette_view = roulette_view
        self.user_id = user_id

        for amount in BET_AMOUNTS:
            button = discord.ui.Button(label=str(amount), style=discord.ButtonStyle.primary)
            button.callback = partial(self.make_bet_callback, amount=amount)
            self.add_item(button)

        cancel_btn = discord.ui.Button(label="キャンセル", style=discord.ButtonStyle.danger)
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)

    async def make_bet_callback(self, interaction: discord.Interaction, amount: int):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("これはあなた専用のボタンきつ", ephemeral=True)
            return

        if get_coin(interaction.user.id) < amount:
            await interaction.response.send_message("にゃんにゃんが足りないきつ！", ephemeral=True)
            return

        current = self.roulette_view.bet_amounts.get(interaction.user.id, 0)
        await self.roulette_view.set_bet_amount(interaction.user, current + amount)
        await self.roulette_view.update_bet_embed()
        await interaction.response.defer()

        self.stop()
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

    async def cancel_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("これはあなた専用のボタンきつ", ephemeral=True)
            return
        self.roulette_view.bet_amounts.pop(interaction.user.id, None)
        self.roulette_view.bet_colors.pop(interaction.user.id, None)
        await self.roulette_view.update_bet_embed()
        await interaction.response.send_message("ベットをキャンセルしたきつ", ephemeral=True)
        self.stop()
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

class RouletteView(discord.ui.View):
    def __init__(self, host_user):
        super().__init__(timeout=None)
        self.host_user = host_user
        self.bet_colors = {}
        self.bet_amounts = {}
        self.message = None
        self.bot = None

    async def update_bet_embed(self):
        embed = discord.Embed(title="🎰 ルーレットベット受付中", color=discord.Color.gold())
        lines = []
        for uid in self.bet_colors:
            if uid in self.bet_amounts:
                try:
                    user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                    color = self.bet_colors[uid]
                    amount = self.bet_amounts[uid]
                    lines.append(f"{user.mention}：{get_emoji(color)} {color.upper()} | 💰 {amount} にゃんにゃん")
                except:
                    continue
        embed.description = "\n".join(lines) or "まだ誰もベットしてないきつ"
        await self.message.edit(embed=embed, view=self)

    async def set_bet_amount(self, user, amount):
        self.bet_amounts[user.id] = amount

    async def handle_bet(self, interaction, color):
        uid = interaction.user.id
        self.bet_colors[uid] = color
        if uid not in self.bet_amounts:
            await interaction.response.send_message("💰 ベット額を選んできつ", ephemeral=True)
            view = BetAmount(self, uid)
            await interaction.followup.send("金額を選んできつ：", view=view, ephemeral=True)
        else:
            await interaction.response.defer()
            await self.update_bet_embed()

    @discord.ui.button(label="🔴 赤にベット", style=discord.ButtonStyle.danger)
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, "red")

    @discord.ui.button(label="⚫ 黒にベット", style=discord.ButtonStyle.secondary)
    async def black(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, "black")

    @discord.ui.button(label="🟢 緑にベット", style=discord.ButtonStyle.success)
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_bet(interaction, "green")

    @discord.ui.button(label="🎬 スタート", style=discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.host_user.id:
            await interaction.response.send_message("このボタンはホストだけが押せるきつ！", ephemeral=True)
            return
        await interaction.response.defer()
        await self.message.edit(content="🎰 ルーレットスタート！", view=None)
        await self.spin(interaction.channel)

    async def spin(self, channel):
        # 正しい確率で出現するように修正
        display = ["🔴"] * 49 + ["⚫"] * 49 + ["🟢"] * 2
        pattern = ["🔴", "⚫", "🟢", "🔴", "⚫"]
        msg = await channel.send("🎲 ルーレットを回しています...")

        sequence = [0.01] * 10 + [0.02] * 5 + [0.5] * 3 + [1] * 2

        # ✅ 抽選を先に行う
        result_color = random.choice(COLOR_POOL)
        result_emoji = get_emoji(result_color)

        for i, interval in enumerate(sequence):
            if i < len(sequence) - 1:
                pattern = pattern[1:] + [random.choice(display)]
            else:
                pattern = pattern[1:] + [result_emoji]  # 最後は確定色

            display_text = "".join(pattern[:2]) + "|" + pattern[2] + "|" + "".join(pattern[3:])
            await msg.edit(content=f"🎰 {display_text}")
            await asyncio.sleep(interval)

        # 結果判定
        center = pattern[2]
        result_color = {"🔴": "red", "⚫": "black", "🟢": "green"}[center]

        result_lines = []
        for uid, color in self.bet_colors.items():
            if uid in self.bet_amounts:
                amount = self.bet_amounts[uid]
                win = color == result_color
                if win:
                    multiplier = 50 if color == "green" else 2
                    update_coin(uid, amount * (multiplier - 1))
                    outcome = f"✅ 勝利！{multiplier}倍！(+{amount * (multiplier - 1)})"
                else:
                    update_coin(uid, -amount)
                    outcome = f"❌ はずれ (-{amount})"
                balance = get_coin(uid)
                user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                result_lines.append(
                    f"{user.mention}：{get_emoji(color)} {color.upper()} | 💰 {amount} にゃんにゃん → {outcome}\n"
                    f"　　📦 現在の残高：{balance} にゃんにゃん"
                )

        embed = discord.Embed(
            title="🎯 ルーレット結果",
            description="\n".join(result_lines),
            color=discord.Color.red() if result_color == "red" else
                  discord.Color.green() if result_color == "green" else
                  discord.Color.dark_gray()
        )
        embed.add_field(name="🎲 出目", value=f"{center} {result_color.upper()}", inline=False)
        await msg.edit(content="", embed=embed)

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roulette", description="ルーレットにベット！")
    async def roulette(self, interaction: discord.Interaction):
        view = RouletteView(interaction.user)
        view.bot = interaction.client
        embed = discord.Embed(
            title="🎰 ルーレットベット受付中きつ",
            description="🔴 赤 / ⚫ 黒 / 🟢 緑 にベットしてきつ",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(Roulette(bot))
