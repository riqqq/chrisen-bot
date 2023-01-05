# Importing libraries
import discord
import os
import asyncio
import yt_dlp
from discord.ext import commands

voice_clients = {}

# yt_dlp options
yt_dl_opts = {
    'format': 'bestaudio/best'
    }
ytdl = yt_dlp.YoutubeDL(yt_dl_opts)

# ffmpeg options
ffmpeg_options = {
    'options': "-vn",
    'before_options': "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    }

# Music cog
class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # This event happens when bot becomes online, print something to the console to make sure it's working
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot is online as {self.bot.user}")

    # Play command that will take youtube url and play audio from that video
    @commands.command()
    async def play(self, ctx, *, url):
        print("Play command used")
        try:
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[voice_client.guild.id] = voice_client
        except Exception as err:
            print(type(err))
            print(err.args)
            print(err)

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

            song = data.get('url')
            title = data.get('title')
            player = discord.FFmpegPCMAudio(song, **ffmpeg_options, executable="C:\\Program Files\\ffmpeg\\ffmpeg.exe") # I needed to specify executable path to ffmpeg.exe, because PATH variable is not working on my machine for some reason

            voice_clients[ctx.guild.id].play(player)

            embed = discord.Embed(title="Now playing", description=f"[{title}]({song}) [Requested by: {ctx.author.mention}]")
            await ctx.send(embed=embed)

        except Exception as err:
            print(type(err))
            print(err.args)
            print(err)

            x,y = err.args
            print('x =', x)

    # This pauses the audio
    @commands.command()
    async def pause(self, ctx):
        try:
            voice_clients[ctx.guild.id].pause()
            await ctx.send("Paused ⏸️")
        except Exception as err:
            print(err)

    # This resumes the current song playing if it's been paused
    @commands.command()
    async def resume(self, ctx):
        try:
            voice_clients[ctx.guild.id].resume()
            await ctx.send("Resuming ⏯️")
        except Exception as err:
            print(err)

    # This stops the current playing song
    @commands.command()
    async def stop(self, ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await voice_clients[ctx.guild.id].disconnect()
        except Exception as err:
            print(err)

    # This makes sure the client that's requesting to play music is in a voice channel
    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if not ctx.author.voice:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

async def setup(bot):
    await bot.add_cog(music(bot))