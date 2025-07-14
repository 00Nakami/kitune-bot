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
                "`/slot` - スロットで遊べるきつ\n"
                "`/roulette` - ルーレットで遊べるきつ\n"
                "`/janken` - じゃんけんで勝負するきつ！\n"
                "`/kitumikuji` - 1時間に1回きつみくじを引くきつ\n"
                "`/tictactoe` - ○×ゲームで対戦するきつ"
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

        # 🎨 見た目・画像系
        embed.add_field(
            name="🎨 画像・抽選",
            value=(
                "`/avatar` - アイコン画像を表示するきつ\n"
                "`/giveaway` - ギブアウェイを作るきつ"
            ),
            inline=False
        )

        # 🔊 TTS（読み上げ）関連
        embed.add_field(
            name="🔊 VC読み上げ",
            value=(
                "`/join` - VCに接続するきつ\n"
                "`/autojoin` - VCに自動で接続するようにするきつ\n"
                "`/leave` - VCから退出するきつ\n"
                "`/setvoice` - 読み上げの声・話し方を設定するきつ"
            ),
            inline=False
        )

        embed.set_footer(text="⚠️ 一部のコマンドはVCや管理権限が必要な場合があるきつ")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
