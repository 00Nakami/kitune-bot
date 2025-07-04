import discord
from discord import app_commands
from discord.ui import View, Button
import random
from data import get_coin, update_coin, save_data

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def card_value(rank):
    if rank in ["J", "Q", "K"]:
        return 10
    elif rank == "A":
        return 11
    return int(rank)

class BlackjackGame:
    def __init__(self, player1, player2, bet):
        self.players = [player1, player2]
        self.bet = bet
        self.hands = {player1.id: [], player2.id: []}
        self.deck = [(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)
        self.actions = {}
        self.stood = set()
        self.finished = False

    def draw_card(self):
        return self.deck.pop()

    def hand_value(self, hand):
        value = 0
        aces = 0
        for rank, _ in hand:
            v = card_value(rank)
            value += v
            if rank == "A":
                aces += 1
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    def initial_deal(self):
        for _ in range(2):
            for player in self.players:
                self.hands[player.id].append(self.draw_card())

    def bust(self, player_id):
        return self.hand_value(self.hands[player_id]) > 21

    def both_stand_or_bust(self):
        pids = [p.id for p in self.players]
        for pid in pids:
            if pid not in self.stood and not self.bust(pid):
                return False
        return True

class AcceptView(View):
    def __init__(self, challenger, opponent, bet, start_callback):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.start_callback = start_callback
        self.message = None

    @discord.ui.button(label="はい", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("これはあなた宛の対戦きつ！", ephemeral=True)
            return
        if get_coin(self.challenger.id) < self.bet or get_coin(self.opponent.id) < self.bet:
            await interaction.response.send_message("にゃんにゃんが足りないきつ！", ephemeral=True)
            return
        if self.message:
            await self.message.delete()
        self.stop()
        await self.start_callback(interaction, self.challenger, self.opponent, self.bet)

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("これはあなた宛の対戦きつ！", ephemeral=True)
            return
        await interaction.response.send_message("対戦はキャンセルされたきつ")
        self.stop()
        if self.message:
            await self.message.delete()

class BlackjackView(View):
    def __init__(self, game: BlackjackGame):
        super().__init__(timeout=180)
        self.game = game
        self.message = None

    def get_hand_str(self, user_id):
        return " ".join([f"{r}{s}" for r, s in self.game.hands[user_id]])

    def get_status(self):
        p1, p2 = self.game.players
        lines = []
        for p in [p1, p2]:
            hand_str = self.get_hand_str(p.id)
            value = self.game.hand_value(self.game.hands[p.id])
            bust = self.game.bust(p.id)
            stand = p.id in self.game.stood
            bust_text = "❌ バースト！" if bust else ""
            stand_text = "（スタンド済み）" if stand else ""
            lines.append(f"{p.mention} の手札: {hand_str} (合計: {value}) {bust_text} {stand_text}")
        return "\n".join(lines) + "\n\n行動を選択してきつ"

    def buttons_enabled_for(self, user_id):
        if user_id not in [p.id for p in self.game.players]:
            return False
        if user_id in self.game.stood:
            return False
        if user_id in self.game.actions:
            return False
        return True

    async def finish_game_via_edit(self):
        p1, p2 = self.game.players
        winner = None
        v1 = self.game.hand_value(self.game.hands[p1.id])
        v2 = self.game.hand_value(self.game.hands[p2.id])
        bust1 = self.game.bust(p1.id)
        bust2 = self.game.bust(p2.id)

        if winner := self.determine_winner(p1, p2, v1, v2, bust1, bust2):
            update_coin(winner.id, self.game.bet * 2)
            result = f"🏆 勝者: {winner.mention}！{self.game.bet * 2} にゃんにゃん獲得きつ！"
        else:
            update_coin(p1.id, self.game.bet)
            update_coin(p2.id, self.game.bet)
            result = "🤝 引き分け！にゃんにゃん返却きつ！"

        content = (
            f"🃏 ブラックジャック 結果：\n"
            f"{p1.mention}: {self.get_hand_str(p1.id)} (合計: {v1}) {'❌ バースト！' if bust1 else ''}\n"
            f"{p2.mention}: {self.get_hand_str(p2.id)} (合計: {v2}) {'❌ バースト！' if bust2 else ''}\n\n"
            f"{result}"
        )
        for child in self.children:
            child.disabled = True
        await self.message.edit(content=content, view=self)
        self.stop()

    def determine_winner(self, p1, p2, v1, v2, bust1, bust2):
        if bust1 and bust2:
            return None
        if bust1:
            return p2
        if bust2:
            return p1
        if v1 > v2:
            return p1
        if v2 > v1:
            return p2
        return None

    async def process_turn(self, interaction: discord.Interaction):
        pids = [p.id for p in self.game.players]
        acted_pids = set(self.game.actions.keys())
        stood_pids = self.game.stood

        if not ((acted_pids | stood_pids) == set(pids)):
            return

        for pid, action in self.game.actions.items():
            if action == "hit":
                self.game.hands[pid].append(self.game.draw_card())
            elif action == "stand":
                self.game.stood.add(pid)

        self.game.actions.clear()

        busted_players = [pid for pid in pids if self.game.bust(pid)]
        if busted_players:
            self.game.finished = True
            await self.finish_game_via_edit()
            return

        if self.game.both_stand_or_bust():
            self.game.finished = True
            await self.finish_game_via_edit()
            return

        await self.message.edit(content=self.get_status(), view=self)

    @discord.ui.button(label="ヒット", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        if not self.buttons_enabled_for(user.id):
            await interaction.response.send_message("あなたは既に行動済みか、スタンド済みか、参加者ではないきつ", ephemeral=True)
            return

        self.game.actions[user.id] = "hit"
        await interaction.response.defer()
        await self.process_turn(interaction)

    @discord.ui.button(label="スタンド", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        if not self.buttons_enabled_for(user.id):
            await interaction.response.send_message("あなたは既に行動済みか、スタンド済みか、参加者ではないきつ", ephemeral=True)
            return

        self.game.actions[user.id] = "stand"
        await interaction.response.defer()
        await self.process_turn(interaction)

def setup_bj(bot):
    async def start_game(interaction: discord.Interaction, p1, p2, bet):
        game = BlackjackGame(p1, p2, bet)
        game.initial_deal()
        game_view = BlackjackView(game)
        msg = await interaction.channel.send(content=game_view.get_status(), view=game_view)
        game_view.message = msg

    @bot.tree.command(name="bj", description="ブラックジャックで対戦するきつ！")
    @app_commands.describe(opponent="対戦相手", bet="ベット")
    async def bj(interaction: discord.Interaction, opponent: discord.Member, bet: int):
        challenger = interaction.user
        if challenger.id == opponent.id:
            await interaction.response.send_message("自分と対戦することはできないきつ！", ephemeral=True)
            return
        if opponent.bot:
            await interaction.response.send_message("Botとは対戦できないきつ！", ephemeral=True)
            return
        if get_coin(challenger.id) < bet or get_coin(opponent.id) < bet:
            await interaction.response.send_message("にゃんにゃんが足りないきつ！", ephemeral=True)
            return

        accept_view = AcceptView(challenger, opponent, bet, start_callback=start_game)
        await interaction.response.send_message(
            f"{opponent.mention} さん、{challenger.display_name} さんからブラックジャック対戦（ベット: {bet} にゃんにゃん）のお誘いきつ。承諾するきつか？",
            view=accept_view,
            ephemeral=False
        )
        msg = await interaction.original_response()
        accept_view.message = msg
