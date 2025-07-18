import discord
from discord import app_commands
import random
import asyncio
from data import get_coin, update_coin

SYMBOLS = ["🐵", "🐹", "🐧", "🐺", "🦊"]
PAYOUTS = {
    "🐵": 3,
    "🐹": 3,
    "🐧": 4,
    "🐺": 4,
    "🦊": 5
}

def setup_slot(bot):
    @bot.tree.command(name="slot", description="スロットでにゃんにゃんを賭けるきつ！")
    @app_commands.describe(bet="ベット")
    async def slot(interaction: discord.Interaction, bet: int):
        user = interaction.user

        if bet <= 0:
            await interaction.response.send_message("にゃんにゃんは 1 以上を賭けてきつ", ephemeral=True)
            return

        if get_coin(user.id) < bet:
            await interaction.response.send_message("にゃんにゃんが足りないきつ！", ephemeral=True)
            return

        view = SlotView(user, bet)
        await interaction.response.send_message("🎰 スロットスタート！ にゃんにゃん: {}枚".format(bet), view=view)
        view.message = await interaction.original_response()
        await view.start_spinning()

class SlotView(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=180)
        self.user = user
        self.bet = bet
        self.reels = [[random.choice(SYMBOLS) for _ in range(3)] for _ in range(3)]
        self.stopped = [False, False, False]
        self.running_tasks = [None, None, None]
        self.message = None
        self.last_update_time = 0

    def get_display(self):
        lines = []
        for row in range(3):
            line = [self.reels[col][row] for col in range(3)]
            lines.append("    ".join(line))
        return "🎰 スロット回転中...\n\n" + "\n".join(lines)

    async def start_spinning(self):
        for i in range(3):
            self.running_tasks[i] = asyncio.create_task(self._spin_reel(i))

    async def _spin_reel(self, index: int):
        try:
            while not self.stopped[index]:
                self.reels[index].pop()
                self.reels[index].insert(0, random.choice(SYMBOLS))

                # 1秒ごとにだけ表示更新
                now = asyncio.get_event_loop().time()
                if now - self.last_update_time > 1.0:
                    self.last_update_time = now
                    if self.message:
                        await self.message.edit(content=self.get_display(), view=self)

                await asyncio.sleep(0.1)  # 少し間隔を広げて負荷軽減
        except asyncio.CancelledError:
            return

    async def stop_slot(self, interaction: discord.Interaction, index: int):
        if interaction.user != self.user:
            await interaction.response.send_message("これはあなたのスロットじゃないきつ！", ephemeral=True)
            return

        if self.stopped[index]:
            await interaction.response.send_message("このリールはもう止めているきつ", ephemeral=True)
            return

        self.stopped[index] = True
        if self.running_tasks[index]:
            self.running_tasks[index].cancel()

        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.message.edit(content=self.get_display(), view=self)

        if all(self.stopped):
            await self.finish_game()

    async def on_timeout(self):
        for i in range(3):
            if not self.stopped[i]:
                self.stopped[i] = True
                if self.running_tasks[i]:
                    self.running_tasks[i].cancel()
        if self.message:
            await self.message.edit(content=self.get_display(), view=self)
        await self.finish_game()

    async def finish_game(self):
        for child in self.children:
            child.disabled = True

        lines = [[self.reels[i][row] for i in range(3)] for row in range(3)]

        win = 0
        hit_line = None
        hit_symbol = None
        for idx, line in enumerate(lines):
            if line[0] == line[1] == line[2]:
                symbol = line[0]
                base_multiplier = PAYOUTS.get(symbol, 1)
                multiplier = base_multiplier if idx == 1 else base_multiplier * 0.5
                win = int(self.bet * multiplier)
                hit_line = idx
                hit_symbol = symbol
                break

        if win > 0:
            update_coin(self.user.id, win)
            line_names = ["上段", "中段", "下段"]
            if hit_symbol == "🦊":
                result = (
                    f"🎆🎆🎆 **ジャックポット！！** 🎆🎆🎆\n"
                    f"{line_names[hit_line]}の {hit_symbol}×3 揃いで **{win} にゃんにゃん** を獲得きつ！！"
                )
            else:
                result = f"🎉 **{line_names[hit_line]}の {hit_symbol}×3！ {win} にゃんにゃん獲得きつ！**"
        else:
            update_coin(self.user.id, -self.bet)
            result = f"😿 はずれ！ {self.bet} にゃんにゃん失ったきつ…"

        if self.message:
            await self.message.edit(content=f"{self.get_display()}\n\n{result}", view=self)
        self.stop()

    @discord.ui.button(label="左を止める", style=discord.ButtonStyle.primary)
    async def stop_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.stop_slot(interaction, 0)

    @discord.ui.button(label="真ん中を止める", style=discord.ButtonStyle.primary)
    async def stop_middle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.stop_slot(interaction, 1)

    @discord.ui.button(label="右を止める", style=discord.ButtonStyle.primary)
    async def stop_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.stop_slot(interaction, 2)
