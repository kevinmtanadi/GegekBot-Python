import discord
from discord.ext import commands
import os
from youtube_search import YoutubeSearch 
from pytube import YouTube
import copy
import pytube
from asyncio import sleep

from helper import *
from service.spotify import Spotify

class Song:
    def __init__(self):
        self.id = None
        self.title = None
        self.url = None
        self.length = None
        self.requester = None
    
    def setData(self, title=None, url=None, id=None, length=None, requester=None):
        if title != None:
            self.title = title
        
        if url != None:
            self.url = url
        
        if id != None:
            self.id = id
        
        if length != None:
            self.length = length
        
        if requester != None:
            self.requester = requester

class DiscordBot:
    def __init__(self, isDevelopment):
        self.intents = discord.Intents.all()
        self.intents.voice_states = True
        self.client = commands.Bot(command_prefix="!", intents=self.intents)
        if not isDevelopment:
            discord.opus.load_opus("./libopus.so.0.8.0")
        self.isLooping = False
        self.songQueue = []
        self.spotify = Spotify()
        self.filename = "audio.mp3"
        self.currentSong = None
    
    def run(self):
        self.client.run(os.getenv("DISCORD_BOT_TOKEN"))
        
    async def sendEmbed(self, ctx, message, color, author=None):
        embed = discord.Embed(description=message, color=color, )
        if author:
            embed.set_footer(text="Requested by {}".format(author.name), icon_url=author.avatar_url)
        await ctx.send(embed=embed)
        
    def isConnected(self, ctx):
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        return voice_client and voice_client.is_connected()
    
    def playMusic(self, voice, filename):
        voice.play(discord.FFmpegPCMAudio(source=filename))
        
    async def add(self, ctx, *, url: str):
        id = 0
        author = ctx.message.author
        voiceChannel = author.voice
        song = Song()
        song.requester = author
        
        successMessage = "**Added Song**\n\n**Song Title**\n{}\n\n**Song Duration**\n{}"
        
        if not voiceChannel:
            await self.sendEmbed(ctx, "You have to be in a voice channel to play a song!", discord.Color.red())
            return
        
        if self.isLooping:
            await self.sendEmbed(ctx, "Stop the loop using /loop before adding any new song", discord.Color.red())
            return
    
        if not isUrl(url):
            result = YoutubeSearch(url, max_results=1).to_dict()
            for v in result:
                youtube_url = "https://www.youtube.com" + v['url_suffix']
                yt = YouTube(youtube_url)
                song.setData(title=yt.title, url=youtube_url, id=id, length=yt.length)
                self.songQueue.append(song)
            id += 1
            m, s = divmod(yt.length, 60)
            duration = f"{m:02d}:{s:02d}"
            await self.sendEmbed(ctx, successMessage.format(yt.title, duration), discord.Color.blue(), author=author)
            return 
        
        if (isSpotify(url)):
            searchQuery = self.spotify.getSpotifyTitle(url)
            print(searchQuery)
            result = YoutubeSearch(searchQuery, max_results=1).to_dict()
            for v in result:
                youtube_url = "https://www.youtube.com" + v['url_suffix']
                yt = YouTube(youtube_url)
                song.setData(title=yt.title, url=youtube_url, id=id, length=yt.length)
                self.songQueue.append(song)
                m, s = divmod(yt.length, 60)
                duration = f"{m:02d}:{s:02d}"
                await self.sendEmbed(ctx, successMessage.format(yt.title, duration), discord.Color.blue(), author=author)
        else:
            yt = YouTube(url)
            song.setData(title=yt.title, url=youtube_url, id=id, length=yt.length)
            self.songQueue.append(song)
            m, s = divmod(yt.length, 60)
            duration = f"{m:02d}:{s:02d}"
            await self.sendEmbed(ctx, successMessage.format(yt.title, duration), discord.Color.blue(), author=author)
            
    
    async def on_voice_state_update(self, member):
        voice_state = member.guild.voice_client
        if voice_state is None:
            # Exiting if the bot it's not connected to a voice channel
            return

        if len(voice_state.channel.members) <= 1:
            await voice_state.disconnect()
    
    async def loop(self, ctx):
        if len(self.songQueue) > 0:
            self.isLooping = False
            if self.isLooping:
                self.isLooping = False
                await self.sendEmbed(ctx, "Currently looping", discord.Color.blue())
            else:
                self.isLooping = False
                await self.sendEmbed(ctx, "Stopped looping", discord.Color.blue())
        else:
            await self.sendEmbed(ctx, "There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue", discord.Color.red())
    
    async def queue(self, ctx):
        if len(self.songQueue) > 0:
            i = 1
            songList = "Current song queue :\n"
            for songs in self.songQueue:
                songList += str(i) + ". " + songs.title + "\n"
                i += 1
            await self.sendEmbed(ctx, songList, discord.Color.blue())
        else:
            await self.sendEmbed(ctx, "There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue", discord.Color.red())
    
    async def play(self, ctx):
        if len(self.songQueue) == 0:
            await self.sendEmbed(ctx, "There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue", discord.Color.blue())
            return
        
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        
        author = ctx.message.author
        voiceChannel = author.voice
        if not voiceChannel:
            await self.sendEmbed(ctx, "You have to be in a voice channel to play a song!", discord.Color.blue())
            return
        
        channel = voiceChannel.channel
        try:
            await channel.connect()
        except:
            print("Bot already connected")
            
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)

        if voice is None or not voice.is_connected():
            await channel.connect()

        while len(self.songQueue) > 0:
            self.currentSong = self.songQueue[0]

        success = False
        try:
            yt = YouTube(self.currentSong.url)
            audio = yt.streams.filter(only_audio=True).first()
            out_file = audio.download(output_path=".")
            success = True
        except pytube.exceptions.RegexMatchError:
            await self.sendEmbed(ctx, "Cannot download song, need to fix pytube library regex. Hubungi GEGEK", discord.Color.red())
            self.songQueue.clear()
            return
        except pytube.exceptions.AgeRestrictedError:
            await self.sendEmbed(ctx, "Current song **" + yt.title + "** is age restricted", discord.Color.red())

        if success:
            os.rename(out_file, self.filename)
            await self.sendEmbed(ctx, "Currently playing **" + yt.title + "**", discord.Color.blue())
            self.playMusic(voice)
            
            while self.currentSong.length > 0:
                await sleep(1)
                self.currentSong.length -= 1

            if self.isLooping:
                self.songQueue.append(self.currentSong)

            self.songQueue.pop(0)
            os.remove(self.filename)

        await voice.disconnect()
    
    async def stop(self, ctx):
        author = ctx.message.author
        voiceChannel = author.voice
        self.songQueue.clear()
        self.isLooping = False
        
        if not voiceChannel:
            await self.sendEmbed(ctx, "You have to be in a voice channel!", discord.Color.red())
            return

        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if not voice.is_connected():
            await self.sendEmbed(ctx, "The bot is not connected to a voice channel.", discord.Color.red())
            return

        voice.stop()
            
        if voice.is_connected():
            await self.sendEmbed(ctx, "The audio is stopped.", discord.Color.red())
            await voice.disconnect()
        else:
            await self.sendEmbed(ctx, "The bot is not connected to a voice channel.", discord.Color.red())
            await voice.disconnect()
                
    async def clear(self, ctx):
        if len(self.songQueue) > 1:
            await self.sendEmbed(ctx, "The song queue is emptied", discord.Color.blue())
        else:
            await self.sendEmbed(ctx, "There is currently no song in the queue!", discord.Color.red())
    
    async def skip(self, ctx):
        author = ctx.message.author
        voiceChannel = author.voice
        if not voiceChannel:
            await self.sendEmbed(ctx, "You have to be in a voice channel!", discord.Color.red())
            return
        
        if self.currentSong.requester != author:
            await self.sendEmbed(ctx, "Song can only be skipped by the requester : " + self.currentSong.requester, discord.Color.red())
            return
        
        currentSong = self.songQueue[0]
        currentSong.length = 0
        ctx.voice_client.stop()
    
    async def remove(self, ctx, arg: int):
        if len(self.songQueue) == 0:
            await self.sendEmbed(ctx, "There is currently no song in the queue!", discord.Color.red())
            return
        
        if arg > len(self.songQueue):
            await self.sendEmbed(ctx, "There are only " + str(len(self.songQueue)) + "songs in the queue!", discord.Color.red())
        else:
            songToDelete = self.songQueue[arg - 1]
            self.songQueue.remove(songToDelete)
            await self.sendEmbed(ctx, "Successfully deleted " + str(songToDelete.title) + " from to queue", discord.Color.blue())
      