import os
import json
import tempfile
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import requests
from collections import deque
import re

VOICEVOX_URL = "http://localhost:50021"
DEFAULT_SPEAKER_ID = 1
DEFAULT_SPEED = 1.0
DEFAULT_PITCH = 0.0

voice_settings = {}
speakers_data = {}

def save_voice_settings():
    with open("voice_settings.json", "w", encoding="utf-8") as f:
        json.dump(voice_settings, f, indent=2, ensure_ascii=False)

def load_voice_settings():
    global voice_settings
    if os.path.exists("voice_settings.json"):
        with open("voice_settings.json", "r", encoding="utf-8") as f:
            voice_settings = json.load(f)

async def fetch_speakers():
    res = requests.get(f"{VOICEVOX_URL}/speakers")
    res.raise_for_status()
    return res.json()

def get_speaker_id(name: str, style: str):
    for speaker in speakers_data:
        if speaker["name"] == name:
            for s in speaker["styles"]:
                if s["name"] == style:
                    return s["id"]
    return DEFAULT_SPEAKER_ID

def text_to_speech(text, speaker_id, speed=1.0, pitch=0.0):
    query = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": speaker_id}
    )
    query.raise_for_status()
    query_data = query.json()
    query_data["speedScale"] = speed
    query_data["pitchScale"] = pitch
    synthesis = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": speaker_id},
        headers={"Content-Type": "application/json"},
        json=query_data
    )
    synthesis.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(synthesis.content)
        return f.name

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.tts_queues = {}
        self.processing = set()
        self.autojoin_enabled = set()

    async def cog_load(self):
        global speakers_data
        speakers_data = await fetch_speakers()
        load_voice_settings()

    async def play_tts(self, guild_id):
        if guild_id in self.processing:
            return
        self.processing.add(guild_id)
        queue = self.tts_queues[guild_id]
        while queue:
            user_id, text = queue.popleft()
            settings = voice_settings.get(str(user_id), {})
            speaker_name = settings.get("character", "ずんだもん")
            style_name = settings.get("style", "ノーマル")
            speed = float(settings.get("speed", DEFAULT_SPEED))
            pitch = float(settings.get("pitch", DEFAULT_PITCH))
            speaker_id = get_speaker_id(speaker_name, style_name)
            try:
                path = text_to_speech(text, speaker_id, speed, pitch)
                voice_client = self.voice_clients[guild_id]
                voice_client.stop()
                voice_client.play(discord.FFmpegPCMAudio(path))
                while voice_client.is_playing():
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"読み上げエラー: {e}")
        self.processing.remove(guild_id)

    async def play_system_tts(self, guild_id, text):
        if guild_id not in self.voice_clients:
            return
        if guild_id not in self.tts_queues:
            self.tts_queues[guild_id] = deque()
        self.tts_queues[guild_id].appendleft((0, text))
        await self.play_tts(guild_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if message.guild.id not in self.voice_clients:
            return
        if message.guild.id not in self.tts_queues:
            self.tts_queues[message.guild.id] = deque()

        # メンションの置換
        content = message.content
        for user in message.mentions:
            content = re.sub(f"<@!?{user.id}>", f"{user.display_name}さん", content)

        self.tts_queues[message.guild.id].append((message.author.id, content))
        await self.play_tts(message.guild.id)

    @app_commands.command(name="join", description="VCに参加")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("VCに参加してから実行してきつ", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        channel = interaction.user.voice.channel
        vc = await channel.connect()
        self.voice_clients[interaction.guild.id] = vc
        await interaction.followup.send(f"{channel.name} に接続したきつ", ephemeral=True)

    @app_commands.command(name="leave", description="VCから退出")
    async def leave(self, interaction: discord.Interaction):
        vc = self.voice_clients.get(interaction.guild.id)
        if vc:
            await vc.disconnect()
            del self.voice_clients[interaction.guild.id]
            await interaction.response.send_message("切断したきつ", ephemeral=True)

    @app_commands.command(name="autojoin", description="自動参加のオンオフを切り替えるきつ")
    async def autojoin(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        if gid in self.autojoin_enabled:
            self.autojoin_enabled.remove(gid)
            await interaction.response.send_message("自動参加をオフにしたきつ", ephemeral=True)
        else:
            self.autojoin_enabled.add(gid)
            await interaction.response.send_message("自動参加をオンにしたきつ", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        guild = member.guild
        guild_id = guild.id

        # 自動参加
        if guild_id in self.autojoin_enabled:
            if before.channel is None and after.channel is not None:
                if guild_id not in self.voice_clients:
                    try:
                        vc = await after.channel.connect()
                        self.voice_clients[guild_id] = vc
                    except Exception as e:
                        print(f"自動参加エラー: {e}")

        vc = self.voice_clients.get(guild_id)
        if vc and vc.channel:
            non_bot_members = [m for m in vc.channel.members if not m.bot]
            if len(non_bot_members) == 0:
                try:
                    await vc.disconnect()
                    del self.voice_clients[guild_id]
                    print(f"👋 {guild.name} から切断したきつ")
                except Exception as e:
                    print(f"自動切断エラー: {e}")
            else:
                if before.channel != after.channel:
                    if after.channel == vc.channel:
                        await self.play_system_tts(guild_id, f"{member.display_name}さんが入室したきつ")
                    elif before.channel == vc.channel:
                        await self.play_system_tts(guild_id, f"{member.display_name}さんが退室したきつ")

    @app_commands.command(name="setvoice", description="話者・スタイル・速度・ピッチを設定")
    @app_commands.describe(character="キャラクター名", style="スタイル名", speed="0.5～2.0", pitch="-0.5～0.5")
    async def setvoice(self, interaction: discord.Interaction, character: str, style: str, speed: float = 1.0, pitch: float = 0.0):
        user_id = str(interaction.user.id)
        voice_settings[user_id] = {
            "character": character,
            "style": style,
            "speed": speed,
            "pitch": pitch
        }
        save_voice_settings()
        await interaction.response.send_message(
            f"✅ 設定を保存したきつ\nキャラ: {character} / スタイル: {style} / 速度: {speed} / ピッチ: {pitch}",
            ephemeral=True
        )

    @setvoice.autocomplete("character")
    async def autocomplete_character(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=s["name"], value=s["name"])
            for s in speakers_data if current.lower() in s["name"].lower()
        ][:25]

    @setvoice.autocomplete("style")
    async def autocomplete_style(self, interaction: discord.Interaction, current: str):
        selected_character = interaction.namespace.character
        styles = []
        for speaker in speakers_data:
            if speaker["name"] == selected_character:
                styles = [s["name"] for s in speaker["styles"]]
                break
        return [
            app_commands.Choice(name=style, value=style)
            for style in styles if current.lower() in style.lower()
        ][:25]

async def setup(bot: commands.Bot):
    cog = TTS(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
