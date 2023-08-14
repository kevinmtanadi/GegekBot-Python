import discord
from discord.ext import commands
import os
from youtube_search import YoutubeSearch 
import copy
from asyncio import sleep
import json
import argparse
import random

import sys
sys.path.append('./pytube')
import pytube
from pytube import YouTube

from helper import *
from service.spotify import Spotify
from model.song import Song
from service.youtube import Youtube

class DiscordBot:
    def __init__(self, isDevelopment):
        self.intents = discord.Intents.all()
        self.intents.voice_states = True
        self.client = commands.Bot(command_prefix="!", intents=self.intents)
        if isDevelopment == 0 or isDevelopment == "0":
            discord.opus.load_opus("./libopus.so.0.8.0")
        self.isLooping = False
        self.songQueue = []
        self.spotify = Spotify()
        self.filename = "audio.mp3"
        self.currentSong = None
        self.youtube = Youtube()
    
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
    
    def playMusic(self, voice):
        voice.play(discord.FFmpegPCMAudio(source=self.filename))
        
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
            song = self.youtube.search(url)
            self.songQueue.append(song)
            id += 1
            m, s = divmod(yt.length, 60)
            duration = f"{m:02d}:{s:02d}"
            await self.sendEmbed(ctx, successMessage.format(yt.title, duration), discord.Color.blue(), author=author)
            return 
        
        if (isSpotify(url)):
            searchQuery = self.spotify.getSpotifyTitle(url)
            print(searchQuery)
            song = self.youtube.search(url)
            self.songQueue.append(song)
            m, s = divmod(yt.length, 60)
            duration = f"{m:02d}:{s:02d}"
            await self.sendEmbed(ctx, successMessage.format(yt.title, duration), discord.Color.blue(), author=author)
        else:
            yt = YouTube(url)
            song.setData(title=yt.title, url=url, id=id, length=yt.length)
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
                print(self.currentSong.url)
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
                duration = copy.deepcopy(self.currentSong.length)
                
                while duration > 0:
                    await sleep(1)
                    duration -= 1

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
            await self.sendEmbed(ctx, "Song can only be skipped by the requester : " + self.currentSong.requester.name, discord.Color.red())
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
            author = ctx.message.author
            songToDelete = self.songQueue[arg - 1]
            if author != songToDelete.requester:
                await self.sendEmbed(ctx, "Song can only be skipped by the requester : " + self.currentSong.requester.name, discord.Color.red())
                return
            
            self.songQueue.remove(songToDelete)
            await self.sendEmbed(ctx, "Successfully deleted " + str(songToDelete.title) + " from to queue", discord.Color.blue())
      
    # TODO HANDLE EMPTY favorite.json
    async def favorite(self, ctx, *, arg: str):
        author = ctx.message.author

        args = arg.split(" ")
        command = args[0]

        try:
            with open('./favorite.json') as f:
                favorites = json.load(f)
        except json.decoder.JSONDecodeError:
            favorites = {'data': []}

        favoriteDict = {}
        for fav in favorites['data']:
            requester = fav['requester']
            favoriteDict[requester] = fav['songs']
        
        if command == "play":
            voiceChannel = author.voice

            if not voiceChannel:
                await self.sendEmbed(ctx, "You have to be in a voice channel to play a song!", discord.Color.red())
                return
            
            query = " ".join(args[1:])
            if query != "random":
                if author.id in favoriteDict:
                    for song in favoriteDict[author.id]:
                        await self.add(ctx, url=song['url'])
                    await self.sendEmbed(ctx, "Successfully added all favorite songs from " + author.name + "", discord.Color.blue())
                else :
                    await self.sendEmbed(ctx, "You don't have any favorite song", discord.Color.red())
            else:
                songs = copy.deepcopy(favoriteDict[author.id])
                random.shuffle(songs)
                if author.id in favoriteDict:
                    for song in songs:
                        await self.add(ctx, url=song['url'])
                    await self.sendEmbed(ctx, "Successfully added all favorite songs from " + author.name + " randomly", discord.Color.blue())
                else :
                    await self.sendEmbed(ctx, "You don't have any favorite song", discord.Color.red())
            await self.play(ctx)
        if command == "add":
            query = " ".join(args[1:])
            if query == "" or query == " ":
                await self.sendEmbed(ctx, "Please provide a song name", discord.Color.red())
                return
            song = self.youtube.search(query)
            if author.id in favoriteDict:
                favoriteDict[author.id].append({"title": song.title, "url": song.url})
            else :
                favoriteDict[author.id] = [{"title": song.title, "url": song.url}]
            
            data = {"data":[]}
            for requester, songs in favoriteDict.items():
                data["data"].append({"requester": requester, "songs": songs})

            with open('./favorite.json', 'w') as f:
                json.dump(data, f)
            await self.sendEmbed(ctx, "Successfully added " + song.title + " to " + author.name + "'s favorites", discord.Color.blue())
        elif command == "remove":
            query = " ".join(args[1:]).strip()
            index = -1
            if query == "" or query == " ":
                await self.sendEmbed(ctx, "Please provide a song index from [!fav list]", discord.Color.red())
                return
            try:
                index = int(query)
            except:
                await self.sendEmbed(ctx, "The song to be removed must be a number", discord.Color.red())
            
            if author.id not in favoriteDict or len(favoriteDict[author.id]) == 0:
                await self.sendEmbed(ctx, "You don't have any favorite song", discord.Color.red())
                return
            
            if len(favoriteDict[author.id]) < index:
                await self.sendEmbed(ctx, "Index doesn't exist", discord.Color.red())
                return
            
            for v in favoriteDict:
                print(v)
            songToRemove = favoriteDict[author.id][index - 1]
            favoriteDict[author.id].pop(index - 1)

            data = {"data":[]}
            for requester, songs in favoriteDict.items():
                data["data"].append({"requester": requester, "songs": songs})

            print(data)
            with open('./favorite.json', 'w') as f:
                json.dump(data, f)
            
            await self.sendEmbed(ctx,"Successfully removed song " + songToRemove['title'] + " from your favorite", discord.Color.blue())
        elif command == "list":
            if author.id not in favoriteDict:
                await self.sendEmbed(ctx, "You don't have any favorite song", discord.Color.red())
                return
            
            songList = author.name + "'s favorite song list :\n"
            for song in favoriteDict[author.id]:
                i = 1
                songList += str(i) + ". " + song['title'] + "\n"
                i += 1
            await self.sendEmbed(ctx, songList, discord.Color.blue())