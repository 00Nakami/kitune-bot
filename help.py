import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Botの使い方を表示するきつ")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            title="📖 Botの使い方ガイド",
            description="各カテゴリごとにコマンドをまとめたきつ！\n`/コマンド名`で使ってきつ",
            color=discord.Color.blurple()
        )

        # 🎮 ゲームカテゴリ
        embed.add_field(
            name="🎮 ゲーム",
            value=(
                "`/bj` - ブラックジャックで対戦するきつ\n"
                "`/roulette` - ルーレットで遊べるきつ\n"
                "`/janken` - じゃんけんで勝負するきつ\n"
                "`/kitumikuji` - 1時間に1回きつみくじを引くきつ\n"
                "`/tictactoe` - ○×ゲームで対戦するきつ\n"
                "`/wordwolf` - みんなでワードウルフで遊ぶきつ"
            ),
            inline=False
        )

        # 🎮 投資カテゴリ
        embed.add_field(
            name="📈 投資",
            value=(
                "`/invest_buy` - 欲しい銘柄の株を買うきつ\n"
                "`/invest_sell` - 所有している株を売るきつ\n"
                "`/invest_portfolio` - 現在所有している株を表示するきつ\n"
                "`/invest_chart` - 株価の履歴チャートを見るきつ\n"
                "`/invest_market` - 現在の株価を一覧で見るきつ"
            ),
            inline=False
        )

        # 📚 学習・計算カテゴリ
        embed.add_field(
            name="📚 算数・計算",
            value=(
                "`/sansuu_easy` - やさしい算数問題きつ\n"
                "`/sansuu_normal` - ふつうの算数問題きつ\n"
                "`/sansuu_hard` - 難しい算数問題きつ\n"
                "`/dentaku` - 電卓きつ"
            ),
            inline=False
        )

        # 💰 にゃんにゃん通貨関連
        embed.add_field(
            name="💰 にゃんにゃん通貨",
            value=(
                "`/nyan` - 所持にゃんにゃんを確認するきつ\n"
                "`/give` - にゃんにゃんを他の人に渡すきつ\n"
                "`/nyan_ranking` - 所持金ランキングを表示するきつ"
            ),
            inline=False
        )

        # 🎨 画像・抽選
        embed.add_field(
            name="🎨 画像・抽選",
            value=(
                "`/avatar` - アイコン画像を表示するきつ\n"
                "`/giveaway` - ギブアウェイを作るきつ"
            ),
            inline=False
        )

        # ❓ ガチャ関連
        embed.add_field(
            name="❓ ガチャ",
            value=(
                "`/gacha` - ガチャを引くきつ\n"
                "`/gacha_list` - ガチャの確率一覧を表示するきつ\n"
                "`/gacha_index` - ガチャで出たアイテムの図鑑を表示するきつ\n"
                "`/gacha_ranking` - ガチャを回した回数・埋まっている図鑑の数でランキングを表示するきつ"
            ),
            inline=False
        )

        embed.set_footer(text="きつねBotで遊んでくれてありがとうきつ")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
