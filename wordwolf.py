import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time

WORD_PAIRS = [
    ("ラーメン", "パン"),
    ("マインクラフト", "フォートナイト"),
    ("ペンギン", "パンダ"),
    ("保冷剤", "冷えピタ"),
    ("イカ", "サーモン"),
    ("木工用ボンド", "カルピスの原液"),
    ("ロバックス", "宿題"),
    ("ハムスター", "ライオン"),
    ("ゼリー", "グミ"),
    ("プリン", "茶碗蒸し"),
    ("セミ", "親"),
    ("AI（人工知能）", "Discord"),
    ("USJ（ユニバ）", "学校"),
    ("うさぎ", "カエル"),
    ("ヘビ", "うなぎ"),
    ("スリッパ", "ぱんつ"),
    ("鍋", "こたつ"),
    ("三輪車", "スケボー"),
    ("日光", "レーザー"),
    ("下水道", "ゴミ箱"),
    ("コンタクト", "目薬"),
    ("スライム", "練り消し"),
    ("仕事", "勉強"),
    ("映画", "YouTube"),
    ("宇宙", "海"),
    ("ノート", "自由帳"),
    ("じゃがりこ", "ポテトチップス"),
    ("オタク", "天才"),
    ("とんかつ", "メンチカツ"),
    ("ネッシー", "ゴジラ"),
    ("日焼け止め", "虫除けクリーム"),
    ("ゴルフ", "ゲートボール"),
    ("涙", "よだれ"),
    ("かき氷", "ガリガリ君"),
    ("ゾンビ", "ヴァンパイア"),
    ("じゃがバター", "フライドポテト"),
    ("歯磨き", "トイレ"),
    ("時計", "ストップウォッチ"),
    ("ポッキー", "とっぽ"),
    ("おにぎり", "サンドイッチ"),
    ("そば", "うどん"),
    ("カレーライス", "麻婆豆腐"),
    ("ハト", "からす"),
    ("お相撲さん", "んだほ"),
    ("ハサミ", "包丁"),
    ("バス", "電車"),
    ("サンダル", "水着"),
    ("観覧車", "ヘリコプター"),
    ("砂浜", "砂漠"),
    ("色鉛筆", "折り紙"),
    ("公園", "遊園地"),
    ("階段", "はしご"),
    ("まくら", "アイマスク"),
    ("とろろ", "納豆"),
    ("消臭スプレー", "ブレスケア"),
    ("トイレットペーパー", "おしりふき"),
    ("ハンカチ", "おしぼり"),
    ("証明写真", "自撮り"),
    ("バスケ", "バレーボール")
]

class WordWolf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}

    @app_commands.command(name="wordwolf", description="ワードウルフを始めるきつ（UI参加）")
    async def wordwolf(self, interaction: discord.Interaction):
        channel = interaction.channel

        if channel.id in self.sessions:
            await interaction.response.send_message("このチャンネルで進行中のゲームがあるきつ！", ephemeral=True)
            return

        session = {
            "host": interaction.user,
            "players": set(),
            "start_message": None,
            "discussion_msg": None,
            "discussion_end": None,
        }
        self.sessions[channel.id] = session

        view = JoinView(self, channel)
        await interaction.response.send_message(
            f"🦊 **ワードウルフ募集きつ！**\n参加者全員が「参加」を押した後、主催者は「開始」を押してきつ！",
            view=view
        )
        sent = await interaction.original_response()
        session["start_message"] = sent

class JoinView(discord.ui.View):
    def __init__(self, cog: WordWolf, channel):
        super().__init__(timeout=300)
        self.cog = cog
        self.channel = channel

    @discord.ui.button(label="参加する！", style=discord.ButtonStyle.primary)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        session = self.cog.sessions.get(self.channel.id)
        if not session:
            await interaction.response.send_message("セッションが無効きつ", ephemeral=True)
            return

        session["players"].add(interaction.user)
        names = '\n'.join(f"- {p.display_name}" for p in session["players"])
        embed = discord.Embed(title="🦊 参加者一覧", description=names, color=discord.Color.green())
        await session["start_message"].edit(embed=embed, view=self)

        await interaction.response.send_message(f"{interaction.user.display_name} が参加したきつ！", ephemeral=True)

    @discord.ui.button(label="開始する", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        session = self.cog.sessions.get(self.channel.id)
        if not session or interaction.user != session["host"]:
            await interaction.response.send_message("主催者しか開始できないきつ！", ephemeral=True)
            return

        players = list(session["players"])
        if len(players) < 3:
            await interaction.response.send_message("3人以上必要きつ！", ephemeral=True)
            return

        word_pair = random.choice(WORD_PAIRS)
        wolf_index = random.randint(0, len(players) - 1)
        session["wolf_index"] = wolf_index
        session["players"] = players

        try:
            await session["start_message"].delete()
        except:
            pass

        for i, player in enumerate(players):
            word = word_pair[1] if i == wolf_index else word_pair[0]
            try:
                await player.send(f"あなたのワードは **「{word}」** きつ！")
            except discord.Forbidden:
                await interaction.channel.send(f"{player.display_name} にDMを送れなかったきつ")
                del self.cog.sessions[self.channel.id]
                return

        self.cog.bot.loop.create_task(wait_discussion(self.cog, session, self.channel))
        await interaction.response.send_message("✅ ワードをDMしたきつ！議論開始きつ！")

async def wait_discussion(cog, session, channel):
    players = session["players"]
    discussion_seconds = 180  # 初期議論時間

    while True:
        skip_votes = set()

        end_time = int(time.time()) + discussion_seconds
        session["discussion_end"] = end_time

        embed = discord.Embed(
            title="🕐 議論タイマー",
            description=f"<t:{end_time}:R> に終了予定きつ！\n全員が ⏭ を押すとスキップ可能きつ！",
            color=discord.Color.orange()
        )
        msg = await channel.send(embed=embed)
        await msg.add_reaction("⏭")

        def check_skip(reaction, user):
            return (
                reaction.message.id == msg.id and
                str(reaction.emoji) == "⏭" and
                user in players
            )

        try:
            while len(skip_votes) < len(players):
                reaction, user = await cog.bot.wait_for("reaction_add", timeout=discussion_seconds, check=check_skip)
                skip_votes.add(user)
        except asyncio.TimeoutError:
            pass

        if len(skip_votes) == len(players):
            break

        now = time.time()
        remaining = end_time - now
        if remaining > 10:
            await asyncio.sleep(remaining - 10)

        prompt = await channel.send(
            embed=discord.Embed(
                title="⏳ 議論終了間近！",
                description="🕐 延長する（+1分）\n🗳️ 投票に進む",
                color=discord.Color.blue()
            )
        )
        await prompt.add_reaction("🕐")
        await prompt.add_reaction("🗳️")

        vote_record = {}

        def check_vote(reaction, user):
            return reaction.message.id == prompt.id and user in players and str(reaction.emoji) in ["🕐", "🗳️"]

        end_vote = time.time() + 10
        while time.time() < end_vote:
            try:
                reaction, user = await cog.bot.wait_for("reaction_add", timeout=end_vote - time.time(), check=check_vote)
                for emoji in ["🕐", "🗳️"]:
                    if emoji != str(reaction.emoji):
                        await prompt.remove_reaction(emoji, user)
                vote_record[user.id] = str(reaction.emoji)
            except asyncio.TimeoutError:
                break

        counts = {"🕐": 0, "🗳️": 0}
        for emoji in vote_record.values():
            counts[emoji] += 1

        if counts["🕐"] > counts["🗳️"]:
            await channel.send("⏱ 延長されたきつ！さらに1分議論するきつ！")
            discussion_seconds = 60
        else:
            break

    await start_vote(cog, channel, session)

class VoteButtonView(discord.ui.View):
    def __init__(self, players, session, channel, cog):
        super().__init__(timeout=30)
        self.players = players
        self.session = session
        self.channel = channel
        self.cog = cog
        self.votes = {}
        self.voted_users = set()

        for i, player in enumerate(players):
            label = player.display_name
            self.add_item(VoteButton(label=label, player=player, parent=self))

class VoteButton(discord.ui.Button):
    def __init__(self, label, player, parent):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.player = player
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in self.parent_view.players:
            await interaction.response.send_message("このゲームに参加していないきつ！", ephemeral=True)
            return

        if interaction.user.id in self.parent_view.voted_users:
            await interaction.response.send_message("すでに投票済みきつ！", ephemeral=True)
            return

        self.parent_view.votes[interaction.user.id] = self.player.id
        self.parent_view.voted_users.add(interaction.user.id)
        await interaction.response.send_message(f"{self.player.display_name} に投票したきつ！", ephemeral=True)

        if len(self.parent_view.votes) == len(self.parent_view.players):
            self.stop()

async def start_vote(cog, channel, session):
    players = session["players"]
    wolf = players[session["wolf_index"]]

    view = VoteButtonView(players, session, channel, cog)

    embed = discord.Embed(
        title="🗳️ 投票タイム！",
        description="ウルフだと思う人にボタンで投票きつ！（1人1票、変更不可）",
        color=discord.Color.gold()
    )
    for i, player in enumerate(players):
        embed.add_field(name=f"{i+1}.", value=player.display_name, inline=False)

    msg = await channel.send(embed=embed, view=view)

    await view.wait()

    count = {}
    for voted_id in view.votes.values():
        count[voted_id] = count.get(voted_id, 0) + 1

    if not count:
        await channel.send("⚠️ 誰も投票してくれなかったきつ……")
        del cog.sessions[channel.id]
        return

    max_votes = max(count.values())
    top_users = [uid for uid, c in count.items() if c == max_votes]

    result_msg = "📊 投票結果きつ！\n"
    for uid, c in count.items():
        name = discord.utils.get(players, id=uid).display_name
        result_msg += f"{name}: {c}票\n"

    if len(top_users) == 1:
        voted = discord.utils.get(players, id=top_users[0])
        result_msg += f"\n🐺 ウルフは **{wolf.display_name}** だったきつ！\n"
        if wolf.id == voted.id:
            result_msg += "🎉 市民の勝ちきつ！"
        else:
            result_msg += "😈 ウルフの勝ちきつ！"
    else:
        result_msg += f"\n😈 投票が割れたきつ…\n🐺 ウルフ **{wolf.display_name}** の勝ちきつ！"

    await channel.send(result_msg)
    del cog.sessions[channel.id]

# setup 関数
async def setup(bot):
    await bot.add_cog(WordWolf(bot))
