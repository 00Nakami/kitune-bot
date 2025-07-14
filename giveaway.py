import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta, timezone
import re
import random

def parse_duration(duration_str: str) -> int:
    pattern = re.compile(
        r"(?:(\d+)\s*d(?:ays?)?)?\s*"
        r"(?:(\d+)\s*h(?:ours?)?)?\s*"
        r"(?:(\d+)\s*m(?:inutes?)?)?\s*"
        r"(?:(\d+)\s*s(?:econds?)?)?\s*$",
        re.I)
    match = pattern.fullmatch(duration_str.strip())
    if match:
        days, hours, minutes, seconds = match.groups(default="0")
        total_seconds = (int(days)*86400)+(int(hours)*3600)+(int(minutes)*60)+int(seconds)
        if total_seconds > 0:
            return total_seconds

    pattern_short = re.compile(
        r"(?:(\d+)d)?"
        r"(?:(\d+)h)?"
        r"(?:(\d+)m)?"
        r"(?:(\d+)s)?"
        r"$",
        re.I)
    match2 = pattern_short.fullmatch(duration_str.strip())
    if match2:
        days, hours, minutes, seconds = match2.groups(default="0")
        total_seconds = (int(days)*86400)+(int(hours)*3600)+(int(minutes)*60)+int(seconds)
        if total_seconds > 0:
            return total_seconds

    raise ValueError("期間の形式が不正です。例: 2d3h4m5s")

class GiveawayButton(discord.ui.Button):
    def __init__(self, giveaway_cog, message_id):
        super().__init__(style=discord.ButtonStyle.primary, label="🎉 エントリー", custom_id=f"giveaway_button_{message_id}")
        self.giveaway_cog = giveaway_cog
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        participants = self.giveaway_cog.active_giveaways.get(self.message_id, set())
        if user_id in participants:
            await interaction.response.send_message("あなたはすでにエントリーしてるきつ！", ephemeral=True)
            return
        participants.add(user_id)
        self.giveaway_cog.active_giveaways[self.message_id] = participants

        message = interaction.message
        embed = message.embeds[0]
        base_desc = self.giveaway_cog.base_descriptions.get(self.message_id, "")
        end_time = self.giveaway_cog.end_times[self.message_id]
        entry_count = len(participants)
        winners = self.giveaway_cog.winners.get(self.message_id, 1)
        hosted_by = self.giveaway_cog.hosts.get(self.message_id, "不明")

        unix_ts = int(end_time.timestamp())

        # JST変換
        jst = timezone(timedelta(hours=9))
        local_end_time = end_time.astimezone(jst)

        embed.description = (
            f"{base_desc}\n\n"
            f"Entries: {entry_count}\n"
            f"Winners: {winners}\n"
            f"Ends: <t:{unix_ts}:R> ({local_end_time.strftime('%Y年%m月%d日 %H:%M JST')})\n"
            f"Hosted by: {hosted_by}"
        )
        embed.set_footer(text="🎉 きつねBot")

        try:
            await message.edit(embed=embed, view=self.giveaway_cog.active_views.get(self.message_id))
        except Exception:
            pass

        await interaction.response.send_message("エントリー完了きつ！当選をお楽しみにきつ！", ephemeral=True)

class GiveawayModal(discord.ui.Modal, title="ギブアウェイ作成フォーム"):
    duration = discord.ui.TextInput(
        label="Duration (例: 2d3h4m5s)",
        placeholder="2days3hours4minutes5seconds",
        required=True,
        max_length=30,
    )
    winners = discord.ui.TextInput(
        label="当選者数",
        placeholder="1",
        required=True,
        max_length=3,
    )
    prize = discord.ui.TextInput(
        label="景品",
        placeholder="景品の内容",
        required=True,
        max_length=100,
    )
    description = discord.ui.TextInput(
        label="説明（任意）",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=300,
    )

    def __init__(self, giveaway_cog, interaction):
        super().__init__()
        self.giveaway_cog = giveaway_cog
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):
        try:
            total_seconds = parse_duration(self.duration.value)
        except Exception as e:
            await interaction.response.send_message(f"❌ 期間の形式エラー: {e}", ephemeral=True)
            return

        try:
            winners = int(self.winners.value)
            if winners <= 0:
                raise ValueError("当選者数は1以上にしてきつ")
        except Exception:
            await interaction.response.send_message("❌ 当選者数は正の整数で入力してきつ", ephemeral=True)
            return

        prize = self.prize.value.strip()
        description = self.description.value.strip() if self.description.value else None

        await self.giveaway_cog.create_giveaway(
            interaction,
            total_seconds,
            winners,
            prize,
            description,
        )

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}  # message.id -> set(user_id)
        self.end_times = {}         # message.id -> datetime
        self.base_descriptions = {} # message.id -> str
        self.active_views = {}      # message.id -> discord.ui.View
        self.update_tasks = {}      # message.id -> asyncio.Task
        self.winners = {}           # message.id -> int
        self.hosts = {}             # message.id -> str (host user mention)

    @app_commands.command(name="giveaway", description="ギブアウェイを作成")
    async def gcreate(self, interaction: discord.Interaction):
        modal = GiveawayModal(self, interaction)
        await interaction.response.send_modal(modal)

    async def create_giveaway(self, interaction, total_seconds, winners, prize, description):
        end_time = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
        base_desc = f"景品: **{prize}**"
        if description:
            base_desc += f"\n説明: {description}"

        unix_ts = int(end_time.timestamp())
        jst = timezone(timedelta(hours=9))
        local_end_time = end_time.astimezone(jst)

        embed = discord.Embed(
            title="🎉 ギブアウェイ開催中きつ！",
            description=(
                f"{base_desc}\n\n"
                f"Entries: 0\n"
                f"Winners: {winners}\n"
                f"Ends: <t:{unix_ts}:R> ({local_end_time.strftime('%Y年%m月%d日 %H:%M JST')})\n"
                f"Hosted by: {interaction.user.mention}"
            ),
            color=0xFF6600,
            timestamp=end_time
        )
        embed.set_footer(text="🎉 きつねBot")

        view = discord.ui.View(timeout=None)
        button = GiveawayButton(self, -1)
        view.add_item(button)

        message = await interaction.channel.send(embed=embed, view=view)

        button.message_id = message.id

        self.active_giveaways[message.id] = set()
        self.end_times[message.id] = end_time
        self.base_descriptions[message.id] = base_desc
        self.active_views[message.id] = view
        self.winners[message.id] = winners
        self.hosts[message.id] = interaction.user.mention

        await interaction.response.send_message(f"ギブアウェイを開始したきつ！ {prize}", ephemeral=True)

        task = self.bot.loop.create_task(self._giveaway_countdown(message, winners))
        self.update_tasks[message.id] = task

    async def _giveaway_countdown(self, message: discord.Message, winners: int):
        while True:
            await asyncio.sleep(10)  # 10秒ごと更新
            if message.id not in self.end_times:
                return
            now = datetime.now(timezone.utc)
            end_time = self.end_times[message.id]
            remaining = end_time - now
            remaining_sec = int(remaining.total_seconds())

            if remaining_sec <= 0:
                break

            participants = self.active_giveaways.get(message.id, set())
            base_desc = self.base_descriptions.get(message.id, "")
            entry_count = len(participants)
            hosted_by = self.hosts.get(message.id, "不明")

            unix_ts = int(end_time.timestamp())
            jst = timezone(timedelta(hours=9))
            local_end_time = end_time.astimezone(jst)

            embed = message.embeds[0]
            embed.description = (
                f"{base_desc}\n\n"
                f"Entries: {entry_count}\n"
                f"Winners: {winners}\n"
                f"Ends: <t:{unix_ts}:R> ({local_end_time.strftime('%Y年%m月%d日 %H:%M JST')})\n"
                f"Hosted by: {hosted_by}"
            )
            embed.set_footer(text="🎉 きつねBot")

            try:
                await message.edit(embed=embed, view=self.active_views.get(message.id))
            except discord.NotFound:
                return
            except discord.HTTPException:
                pass

        participants = list(self.active_giveaways.get(message.id, []))
        if not participants:
            await message.channel.send("参加者がいなかったため、ギブアウェイはキャンセルされたきつ")
            self._cleanup(message.id)
            return

        if winners > len(participants):
            winners = len(participants)

        winners_list = random.sample(participants, winners)
        winner_mentions = []
        for user_id in winners_list:
            user = self.bot.get_user(user_id)
            winner_mentions.append(user.mention if user else f"<@{user_id}>")

        winner_mentions_inline = ", ".join(winner_mentions)
        entry_count = len(participants)
        base_desc = self.base_descriptions.get(message.id, "")
        hosted_by = self.hosts.get(message.id, "不明")
        end_time = self.end_times[message.id]
        unix_ts = int(end_time.timestamp())
        jst = timezone(timedelta(hours=9))
        local_end_time = end_time.astimezone(jst)

        # Embedは開催中のまま、descriptionだけWinnersにメンションリストを入れて更新
        embed = message.embeds[0]
        embed.description = (
            f"{base_desc}\n\n"
            f"Entries: {entry_count}\n"
            f"Winners: {winner_mentions_inline}\n"
            f"Ends: <t:{unix_ts}:R> ({local_end_time.strftime('%Y年%m月%d日 %H:%M JST')})\n"
            f"Hosted by: {hosted_by}"
        )
        embed.set_footer(text="🎉 きつねBot")

        try:
            await message.edit(embed=embed, view=None)
        except Exception:
            pass

        # 景品名抽出
        m = re.search(r"景品:\s*\*\*(.+?)\*\*", base_desc)
        prize_name = m.group(1) if m else "景品"

        # お祝いメッセージをリプライで送信
        await message.reply(f"{winner_mentions_inline} さん、おめでとうきつ！あなたは **{prize_name}** をゲットしたきつ！")

        self._cleanup(message.id)

    def _cleanup(self, message_id):
        self.active_giveaways.pop(message_id, None)
        self.end_times.pop(message_id, None)
        self.base_descriptions.pop(message_id, None)
        self.active_views.pop(message_id, None)
        self.winners.pop(message_id, None)
        self.hosts.pop(message_id, None)
        task = self.update_tasks.pop(message_id, None)
        if task:
            task.cancel()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
