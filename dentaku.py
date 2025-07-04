import discord
from discord.ext import commands

# 表示ラベルと演算子の対応
DISPLAY_TO_EXPR = {"×": "*", "÷": "/"}
EXPR_TO_DISPLAY = {v: k for k, v in DISPLAY_TO_EXPR.items()}

class CalculatorView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.expression = ""
        self.history = []
        self.message = None
        self.build_buttons()

    def _format_for_display(self, expr: str) -> str:
        for op, disp in EXPR_TO_DISPLAY.items():
            expr = expr.replace(op, disp)
        return expr

    def build_buttons(self):
        layout = [
            ["7", "8", "9", "+"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "×"],
            ["0", ".", "=", "÷"]
        ]
        for row_index, row in enumerate(layout):
            for label in row:
                if label == "=":
                    self.add_item(EqualButton(row=row_index))
                else:
                    self.add_item(CalcButton(label=label, row=row_index))
        self.add_item(ClearButton(row=4))
        self.add_item(BackspaceButton(row=4))  # ⌫ ボタン追加

    async def update_display(self, interaction: discord.Interaction):
        display_expr = self._format_for_display(self.expression or "0")
        display_history = "\n".join(self.history[-5:]) if self.history else "*履歴なし*"
        embed = discord.Embed(title="🧮 電卓", color=discord.Color.blurple())
        embed.add_field(name="現在の式", value=f"`{display_expr}`", inline=False)
        embed.add_field(name="履歴", value=display_history, inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

    async def evaluate(self, interaction: discord.Interaction):
        try:
            result = str(eval(self.expression, {"__builtins__": None}, {}))
            disp_expr = self._format_for_display(self.expression)
            self.history.append(f"{disp_expr} = {result}")
            self.expression = result
        except Exception:
            self.expression = "エラー"
        await self.update_display(interaction)

class CalcButton(discord.ui.Button):
    def __init__(self, label, row):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.expr_value = DISPLAY_TO_EXPR.get(label, label)

    async def callback(self, interaction: discord.Interaction):
        view: CalculatorView = self.view
        if interaction.user.id != view.owner_id:
            await interaction.response.send_message("この電卓はあなた専用きつ", ephemeral=True)
            return
        view.expression += self.expr_value
        await view.update_display(interaction)

class EqualButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="=", style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction):
        view: CalculatorView = self.view
        if interaction.user.id != view.owner_id:
            await interaction.response.send_message("この電卓はあなた専用きつ", ephemeral=True)
            return
        await view.evaluate(interaction)

class ClearButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="C", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        view: CalculatorView = self.view
        if interaction.user.id != view.owner_id:
            await interaction.response.send_message("この電卓はあなた専用きつ", ephemeral=True)
            return
        view.expression = ""
        await view.update_display(interaction)

class BackspaceButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="⌫", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        view: CalculatorView = self.view
        if interaction.user.id != view.owner_id:
            await interaction.response.send_message("この電卓はあなた専用きつ", ephemeral=True)
            return
        view.expression = view.expression[:-1]
        await view.update_display(interaction)

def setup_dentaku(bot: commands.Bot):
    @bot.tree.command(name="dentaku", description="電卓きつ")
    async def dentaku(interaction: discord.Interaction):
        view = CalculatorView(owner_id=interaction.user.id)
        embed = discord.Embed(title="🧮 電卓", color=discord.Color.blurple())
        embed.add_field(name="現在の式", value="`0`", inline=False)
        embed.add_field(name="履歴", value="*履歴なし*", inline=False)
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
