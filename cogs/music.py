# Importing libraries
import discord
from discord import SelectOption, SelectMenu, Button, Component
from discord.ui import Select
import os
import asyncio
from yt_dlp import YoutubeDL
from discord.ext import commands
from urllib import parse, request
import re
import json

view = discord.ui.View()
button = discord.ui.Button(style=4, custom_id="Cancel", label="Cancel")
globalTest = {}

class MySelect(Select):
    async def callback(self, interaction):
        await interaction.response.send_message(f"You chose: {self.values[0]}")
        token = self.values[0][1:]
        userChannel = interaction.user.voice.channel
        print(userChannel)
        print(token)
        try:
            intents = discord.Intents.all()
            bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
            m = music(bot)
            songRef = m.extract_YT(token)
            print(songRef)
            if type(songRef) == type(True):
                await interaction.response.send_message("Could not download the song. Incorrect format, try different keywords.")
                return
            print(f'Interaction guild id is: {interaction.guild_id}')
            globalTest[interaction.guild_id].append([songRef, userChannel])
            print(globalTest)
            print("should be done")
        except Exception as err:
            print(err)
            print(type(err))

# Music cog
class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_paused = {}
        self.queueIndex = {}

        self.YTDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'options': "-vn",
                                'before_options': "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"}
        
        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51

        self.vc = {}

    # This event happens when bot becomes online, print something to the console to make sure it's working
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot is online as {self.bot.user}")

        for guild in self.bot.guilds:
            id = int(guild.id)
            globalTest[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = self.is_paused[id] = False
                globalTest[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()
    
    def now_playing_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar.url

        embed = discord.Embed(
            title="Now Playing",
            description=f'[{title}]({link})',
            colour=self.embedBlue
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)
        return embed

    def added_song_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar.url

        embed = discord.Embed(
            title="Song Added to Queue!",
            description=f'[{title}]({link})',
            colour=self.embedRed
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)
        return embed

    def removed_song_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar.url

        embed = discord.Embed(
            title="Song Removed from Queue!",
            description=f'[{title}]({link})',
            colour=self.embedRed
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Song removed by: {str(author)}', icon_url=avatar)
        return embed
    
    async def join_VC(self, ctx, channel):
        print("join_VC called")
        id = int(ctx.guild.id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            print("If connecting to vc in join_VC")
            try:
                self.vc[id] = await channel.connect()
            except Exception as err:
                print(err)

            if self.vc[id] == None:
                print("If could not connect to the voice channel")
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            print("Moving to voice channel")
            await self.vc[id].move_to(channel)

    def get_YT_title(self, videoId):
        print("get yt title called")
        try:
            params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % videoId}
            url = "https://www.youtube.com/oembed"
            queryString = parse.urlencode(params)
            url = url + "?" + queryString
            print("url done")
            with request.urlopen(url) as response:
                print("request as response")
                responseText = response.read()
                data = json.loads(responseText.decode())
                print("search yt title done")
                return data['title']
        except Exception as err:
            print(err)

            
    def search_YT(self, search):
        print("Search YT called")
        queryString = parse.urlencode({'search_query': search})
        htmContent = request.urlopen('http://www.youtube.com/results?' + queryString)
        searchResults = re.findall('/watch\?v=(.{11})', htmContent.read().decode())
        print("Search YT done")
        return searchResults[0:10]
    
    def extract_YT(self, url):
        print("Extract YT called")
        with YoutubeDL(self.YTDL_OPTIONS) as ytdl:
            try:
                print("Try in extract YT")
                info = ytdl.extract_info(url, download=False)
            except:
                print("except in extract YT")
                return False
        print("Return in extract YT")
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': 'https://i.ytimg.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
            'source': info.get('url'),
            'title': info['title']
        }
    
    def play_next(self, ctx):
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(globalTest[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1

            song = globalTest[id][self.queueIndex[id]][0]
            message = self.now_playing_embed(ctx, song)
            coro = ctx.send(embed=message)
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS, executable="C:\\Program Files\\ffmpeg\\ffmpeg.exe"), after=lambda e: self.play_next(ctx))
        else:
            self.queueIndex[id] += 1
            self.is_playing[id] = False

    async def play_music(self, ctx):
        print("Play music called")
        id = int(ctx.guild.id)
        if self.queueIndex[id] < len(globalTest[id]):
            print("If in play_music")
            self.is_playing[id] = True
            self.is_paused[id] = False

            print("Before await in play_music")
            await self.join_VC(ctx, globalTest[id][self.queueIndex[id]][1])
            print("After await in play_music")

            song = globalTest[id][self.queueIndex[id]][0]
            print("Set song in play_music")
            print(song)
            message = self.now_playing_embed(ctx, song)
            print("Embed done, sending it from play_music")
            await ctx.send(embed=message)

            print("Begin to play music in play_music")
            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS, executable="C:\\Program Files\\ffmpeg\\ffmpeg.exe"), after=lambda e: self.play_next(ctx))
        else:
            await ctx.send("There are no songs in the queue to be played.")
            self.queueIndex[id] += 1
            self.is_playing[id] = False

    @commands.command(
        name="play",
        aliases=["pl"],
        help="Help for play command there TODO"
    )
    async def play(self, ctx, *args):
        print(f'Args in play: {args}')
        search = " ".join(args)
        print(f'search in play: {search}')
        id = int(ctx.guild.id)
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return
        if not args:
            if len(globalTest[id]) == 0:
                await ctx.send("There are no songs to be played in the queue")
                return
            elif not self.is_playing[id]:
                if globalTest[id] == None or self.vc[id] == None:
                    await self.play_music(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        else:
            print("Searching for music begin")
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                print("Song type boolean")
                await ctx.send("Could not download the song. Incorrect format, try some different keywords.")
            else:
                print("Append to globalTest")
                globalTest[id].append([song, userChannel])

                if not self.is_playing[id]:
                    print("Playing music")
                    await self.play_music(ctx)
                else:
                    print("Adding to queue")
                    message = self.added_song_embed(ctx, song)
                    await ctx.send(embed=message)

    @commands.command(
        name="add",
        aliases=["a"],
        help="Help for add command there TODO"
    )
    async def add(self, ctx, *args):
        search = " ".join(args)
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be in a voice channel.")
            return
        if not args:
            await ctx.send("You need to specify a song to be added.")
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(False):
                await ctx.send("Could not download the song. Incorrect format, try different keywords.")
                return
            else:
                globalTest[ctx.guild.id].append(song, userChannel)
                message = self.added_song_embed(ctx, song)
                await ctx.send(embed=message)

    @commands.command(
        name="remove",
        aliases=["rm"],
        help="Help for add command there TODO"
    )
    async def remove(self, ctx):
        id = int(ctx.guild.id)
        if globalTest[id] != []:
            song = globalTest[id][-1][0]
            removeSongEmbed = self.removed_song_embed(ctx, song)
            await ctx.send(embed=removeSongEmbed)
        else:
            await ctx.send("There are no songs to be removed in the queue.")
        globalTest[id] = globalTest[id][:-1]
        if globalTest[id] == []:
            if self.vc[id] != None and self.is_playing[id]:
                self.is_playing[id] = self.is_paused[id] = False
                await self.vc[id].disconnect()
                self.vc[id] = None
            self.queueIndex[id] = 0
        elif self.queueIndex[id] == len(globalTest[id]) and self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
            await self.play_music(ctx)

    @commands.command(
        name="search",
        aliases=["find", "sr"],
        help="Help for search command there TODO"
    )
    async def search(self, ctx, *args):
        search = " ".join(args)
        dropdown = MySelect(placeholder="Select an option")
        view.add_item(item=dropdown)
        #view.add_item(item=button)

        if not args:
            await ctx.send("You must specify search terms to use this command")
            return
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return
        
        await ctx.send("Fetching search results...")

        songTokens = self.search_YT(search)
        print("songTokens assigned")
        
        for i, token in enumerate(songTokens):
            url = 'https://www.youtube.com/watch?v=' + token
            name = self.get_YT_title(token)
            dropdown.add_option(label=f'{i+1} - {name[:95]}', value=str(i) + token)
            
        print("message making")
        try:
            message = await ctx.send(view=view)
            view.remove_item(dropdown)
        except Exception as err:
            print(err)
        print("message made")
        await self.my_dropdown_callback
    
    @commands.command(
        name="pause",
        aliases=["pa", "stop"],
        help="Help for pause command there TODO"
    )
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("There is no audio to be paused at the moment.")
        elif self.is_playing[id]:
            await ctx.send("Audio paused!")
            self.is_playing[id] = False
            self.is_paused[id] = True
            self.vc[id].pause()

    @commands.command(
        name="resume",
        aliases=["re"],
        help="Help for resume command there TODO"
    )
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("There is no audio to be played at the moment.")
        elif self.is_paused[id]:
            await ctx.send("The audio is now playing.")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()

    @commands.command(
        name="previous",
        aliases=["pre", "pr"],
        help="Help for previous command there TODO"
    )
    async def previous(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] == None:
            await ctx.send("You need to be in a VC to use this command.")
        elif self.queueIndex[id] <= 0:
            await ctx.send("There is no previous song in the queue. Replaying current song.")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
            await self.play_music(ctx)

    @commands.command(
        name="skip",
        aliases=["sk"],
        help="Help for skip command there TODO"
    )
    async def skip(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] == None:
            await ctx.send("You need to be in a VC to use this command.")
        elif self.queueIndex[id] >= len(globalTest[id]) - 1:
            await ctx.send("There is no next song in the queue. Replaying current song.")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] += 1
            await self.play_music(ctx)

    @commands.command(
        name="queue",
        aliases=["q", "list"],
        help="Help for queue command there TODO"
    )
    async def queue(self, ctx):
        print("queue called")
        id = int(ctx.guild.id)
        returnValue = ""
        print("before try")
        if globalTest[id] == []:
            print("inside if")
            try:
                print("no song in queue")
                await ctx.send("There are no songs in the quueue.")
                return
            except Exception as err:
                print(err)
        
        for i in range(self.queueIndex[id], len(globalTest[id])):
            print("for in queue")
            upNextSongs = len(globalTest[id]) - self.queueIndex[id]
            if i > 5 + upNextSongs:
                break
            returnIndex = i - self.queueIndex[id]
            if returnIndex == 0:
                returnIndex = "Playing"
            elif returnIndex == 1:
                returnIndex = "Next"
            returnValue += f"{returnIndex} - [{globalTest[id][i][0]['title']}]({globalTest[id][i][0]['link']})\n"

            if returnValue == "":
                print("if in for")
                await ctx.send("There are no songs in the queue.")
                return

        print("making embed")
        queue = discord.Embed(
            title="Current Queue",
            description=returnValue,
            colour=self.embedGreen
        )
        print("embed ready")
        await ctx.send(embed=queue)

    @commands.command(
        name="clear",
        aliases=["cl"],
        help="Help for clear command there TODO"
    )
    async def clear(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.is_playing[id]:
            self.is_playing[id] = False
            self.is_paused[id] = False
            self.vc[id].stop()
        if globalTest[id] != []:
            await ctx.send("The music queue has been cleared.")
            globalTest[id] = []
        self.queueIndex[id] = 0

    @commands.command(
        name="join",
        aliases=["j"],
        help="Help for join command there TODO"
    )
    async def join(self, ctx):
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            await self.join_VC(ctx, userChannel)
            await ctx.send(f'Chrisen has joined {userChannel}')
        else:
            await ctx.send("You need to be connected to a voice channel.")
    
    @commands.command(
        name="leave",
        aliases=["l"],
        help="Help for leave command there TODO"
    )
    async def leave(self, ctx):
        id = int(ctx.guild.id)
        self.is_playing[id] = self.is_paused[id] = False
        globalTest[id] = []
        self.queueIndex[id] = 0
        if self.vc[id] != None:
            await ctx.send("Chrisen has left the chat")
            await self.vc[id].disconnect()
            self.vc[id] = None

async def setup(bot):
    await bot.add_cog(music(bot))
    print("Setup in music called")