import discord
from discord.ext import commands
from discord import app_commands
from data import get_coin, update_coin
import random

games = {}

def setup_tictactoe(bot: commands.Bot):
    FOX = "🦊"
    PENGUIN = "🐧"

    @bot.tree.command(name="tictactoe", description="指定した相手と○×ゲーム（🦊 vs 🐧）で対戦するきつ")
    @app_commands.describe(opponent="対戦相手", bet="ベット")
    async def tictactoe(interaction: discord.Interaction, opponent: discord.Member, bet: int):
        player1 = interaction.user
        player2 = opponent

        if player1.id == player2.id:
            await interaction.response.send_message("自分自身とは対戦できないきつ", ephemeral=True)
            return
        if bet <= 0:
            await interaction.response.send_message("ベット額は1以上を指定してきつ", ephemeral=True)
            return

        if get_coin(player1.id) < bet:
            await interaction.response.send_message(f"{player1.display_name}の所持コインが足りないきつ（{bet}にゃんにゃん）。", ephemeral=True)
            return

        embed = discord.Embed(
            title="🦊 vs 🐧 対戦リクエスト",
            description=f"{player1.mention} が {player2.mention} に {bet}にゃんにゃん を賭けて対戦を挑んだきつ！\n「はい」ボタンで承諾、「いいえ」で拒否できるきつ",
            color=discord.Color.orange()
        )
        view = discord.ui.View(timeout=60)
        yes_button = discord.ui.Button(style=discord.ButtonStyle.success, label="はい", emoji="🟢")
        no_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="いいえ", emoji="🔴")

        async def on_accept(inter_btn: discord.Interaction):
            if inter_btn.user.id != player2.id:
                await inter_btn.response.send_message("あなたは招待された対戦相手ではないきつ", ephemeral=True)
                return
            view.stop()

            if get_coin(player2.id) < bet:
                await inter_btn.response.edit_message(content=f"{player2.display_name} の所持コインが足りないきつ", embed=None, view=None)
                return

            # 🦊と🐧をランダムに割り当て
            players = [(FOX, player1), (PENGUIN, player2)]
            random.shuffle(players)
            roles = {players[0][0]: players[0][1], players[1][0]: players[1][1]}
            turn = random.choice([FOX, PENGUIN])

            board = [str(i) for i in range(1, 10)]
            game_state = {
                FOX: roles[FOX],
                PENGUIN: roles[PENGUIN],
                'turn': turn,
                'board': board,
                'bet': bet
            }

            def format_board(b):
                return f"{b[0]} | {b[1]} | {b[2]}\n{b[3]} | {b[4]} | {b[5]}\n{b[6]} | {b[7]} | {b[8]}"

            board_text = format_board(board)
            turn_info = f"現在のターン: **{turn} ({roles[turn].display_name})**"
            game_embed = discord.Embed(
                title=f"🦊 vs 🐧 開始: {roles[FOX].display_name}(🦊) vs {roles[PENGUIN].display_name}(🐧)",
                description=f"```\n{board_text}\n```\n{turn_info}",
                color=discord.Color.blue()
            )
            await inter_btn.response.edit_message(content="", embed=game_embed, view=None)
            msg = inter_btn.message
            games[msg.id] = game_state

            for emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]:
                await msg.add_reaction(emoji)

        async def on_reject(inter_btn: discord.Interaction):
            if inter_btn.user.id != player2.id:
                await inter_btn.response.send_message("あなたは招待された対戦相手ではないきつ", ephemeral=True)
                return
            view.stop()
            await inter_btn.response.edit_message(content=f"{player2.display_name} が対戦を拒否したきつ", embed=None, view=None)

        yes_button.callback = on_accept
        no_button.callback = on_reject
        view.add_item(yes_button)
        view.add_item(no_button)

        await interaction.response.send_message(embed=embed, view=view, content=f"{player2.mention} 対戦を受けるきつ？")

    @bot.event
    async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        msg = reaction.message
        if msg.id not in games:
            return
        game = games[msg.id]
        if user.id not in (game[FOX].id, game[PENGUIN].id):
            await msg.remove_reaction(reaction.emoji, user)
            return

        turn = game['turn']
        if (turn == FOX and user.id != game[FOX].id) or (turn == PENGUIN and user.id != game[PENGUIN].id):
            await msg.remove_reaction(reaction.emoji, user)
            return

        emoji_to_index = {
            "1️⃣": 0, "2️⃣": 1, "3️⃣": 2,
            "4️⃣": 3, "5️⃣": 4, "6️⃣": 5,
            "7️⃣": 6, "8️⃣": 7, "9️⃣": 8
        }
        if str(reaction.emoji) not in emoji_to_index:
            await msg.remove_reaction(reaction.emoji, user)
            return

        idx = emoji_to_index[str(reaction.emoji)]
        board = game['board']
        if board[idx] in [FOX, PENGUIN]:
            await msg.remove_reaction(reaction.emoji, user)
            return

        board[idx] = turn
        await msg.clear_reaction(reaction.emoji)

        winner = None
        win_combos = [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]
        for a, b, c in win_combos:
            if board[a] == board[b] == board[c]:
                winner = game[board[a]]
                break
        is_draw = not winner and all(cell in [FOX, PENGUIN] for cell in board)

        def format_board(b):
            return f"{b[0]} | {b[1]} | {b[2]}\n{b[3]} | {b[4]} | {b[5]}\n{b[6]} | {b[7]} | {b[8]}"
        board_text = format_board(board)

        if winner or is_draw:
            result = ""
            if winner:
                result = f"**{turn} ({winner.display_name}) の勝ち！** 🎉\n{game['bet']}にゃんにゃん獲得きつ！"
                loser = game[PENGUIN] if winner == game[FOX] else game[FOX]
                update_coin(winner.id, +game['bet'])
                update_coin(loser.id, -game['bet'])
            else:
                result = "**引き分け！** 💫 両者にベット返却きつ。"

            end_embed = discord.Embed(
                title=f"🦊 vs 🐧 ゲーム終了",
                description=f"```\n{board_text}\n```\n{result}",
                color=discord.Color.green()
            )
            await msg.edit(content="", embed=end_embed)
            try:
                await msg.clear_reactions()
            except:
                pass
            games.pop(msg.id, None)
        else:
            game['turn'] = PENGUIN if turn == FOX else FOX
            next_p = game[game['turn']]
            next_embed = discord.Embed(
                title=f"{game[FOX].display_name}(🦊) vs {game[PENGUIN].display_name}(🐧)",
                description=f"```\n{board_text}\n```\n現在のターン: **{game['turn']} ({next_p.display_name})**",
                color=discord.Color.blue()
            )
            await msg.edit(content="", embed=next_embed)
