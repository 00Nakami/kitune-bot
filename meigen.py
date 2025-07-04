import tempfile
import asyncio
import requests
from PIL import Image, ImageDraw, ImageFont
import discord
from io import BytesIO
import pytz
from datetime import datetime

JP_BOLD_FONT_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"  # Macの場合

def draw_text_with_outline(draw, position, text, font, fill, outline_color="black", outline_width=1):
    x, y = position
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill)

def wrap_text(text, font, max_width):
    chars = list(text)
    lines = []
    current_line = ""
    for ch in chars:
        test_line = current_line + ch
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current_line = test_line
        else:
            if current_line == "":
                lines.append(ch)
                current_line = ""
            else:
                lines.append(current_line)
                current_line = ch
    if current_line:
        lines.append(current_line)
    return lines

def generate_credits_gif(texts, username, user_tag, avatars, message_times, duration=150, size=(600, 400)):
    w, h = size
    frames = []
    font_size_name = 32
    font_size_text = 26
    font_size_time = 20
    text_max_width = w - 140
    icon_size = 60

    font_name = ImageFont.truetype(JP_BOLD_FONT_PATH, font_size_name)
    font_text = ImageFont.truetype(JP_BOLD_FONT_PATH, font_size_text)
    font_time = ImageFont.truetype(JP_BOLD_FONT_PATH, font_size_time)

    wrapped_texts = []
    for text in texts:
        if len(text) > 200:
            text = text[:197] + "..."
        wrapped_lines = wrap_text(text, font_text, text_max_width)
        wrapped_texts.append(wrapped_lines)

    line_height = font_text.getbbox("あ")[3] - font_text.getbbox("あ")[1]
    name_height = font_name.getbbox("あ")[3] - font_name.getbbox("あ")[1]
    time_height = font_time.getbbox("あ")[3] - font_time.getbbox("あ")[1]

    blocks_heights = []
    for wrapped_lines in wrapped_texts:
        block_height = max(icon_size, name_height + 5 + line_height * len(wrapped_lines) + 5 + time_height)
        blocks_heights.append(block_height)

    total_height = sum(blocks_heights) + 40
    start_y = h
    end_y = -total_height
    speed_per_frame = (start_y - end_y) / duration
    JST = pytz.timezone('Asia/Tokyo')

    for frame_idx in range(duration):
        y_offset = int(start_y - speed_per_frame * frame_idx)
        img = Image.new("RGBA", size, "black")
        draw = ImageDraw.Draw(img)
        current_y = y_offset

        for i, wrapped_lines in enumerate(wrapped_texts):
            # アバター
            avatar_img = avatars[i].resize((icon_size, icon_size))
            avatar_y = current_y + (blocks_heights[i] - icon_size) // 2
            img.paste(avatar_img, (10, avatar_y), avatar_img)

            # テキストX位置
            text_x = 10 + icon_size + 10

            # 表示名
            draw_text_with_outline(draw, (text_x, current_y), f"{username}（@{user_tag}）", font_name, fill=(255, 255, 255))

            # テキスト
            for j, line in enumerate(wrapped_lines):
                line_y = current_y + name_height + 5 + j * line_height
                draw_text_with_outline(draw, (text_x, line_y), line, font_text, fill=(255, 255, 255))

            # 日時
            dt = datetime.fromisoformat(message_times[i])
            jst_time = dt.replace(tzinfo=pytz.utc).astimezone(JST)
            time_str = jst_time.strftime("%Y-%m-%d %H:%M:%S JST")
            time_y = current_y + name_height + 5 + line_height * len(wrapped_lines) + 5
            draw_text_with_outline(draw, (text_x, time_y), time_str, font_time, fill=(200, 200, 200))

            current_y += blocks_heights[i]

        frames.append(img)

    tmp_file = tempfile.NamedTemporaryFile(suffix=".gif", delete=False)
    frames[0].save(
        tmp_file.name,
        save_all=True,
        append_images=frames[1:],
        duration=60,
        loop=0,
        disposal=2
    )
    tmp_file.close()
    return tmp_file.name

async def create_credits_gif_and_send(texts, channel: discord.TextChannel, bot_user: discord.User, author: discord.User, message_times, author_message: discord.Message):
    async with channel.typing():
        try:
            avatars = []
            for _ in texts:
                avatar_url = author.avatar.url if author.avatar else author.default_avatar.url
                response = requests.get(avatar_url)
                avatar_img = Image.open(BytesIO(response.content)).convert("RGBA")
                avatars.append(avatar_img)

            gif_path = await asyncio.to_thread(
                generate_credits_gif,
                texts,
                author.display_name,
                author.name,
                avatars,
                message_times
            )

            with open(gif_path, "rb") as f:
                await channel.send(file=discord.File(f, filename="movie_credit_quote.gif"))

        except Exception as e:
            await channel.send(f"GIF生成でエラーが発生したきつ: {e}")
