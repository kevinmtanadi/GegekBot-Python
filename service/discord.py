import discord
from discord.ext import commands
import os
from youtube_search import YoutubeSearch 
import copy
from asyncio import sleep
import json
import argparse
import random
from datetime import datetime
import asyncio

import sys
sys.path.append('./pytube')
import pytube
from pytube import YouTube

from helper import *
from service.spotify import Spotify
from service.youtube import Youtube
from model.song import Song
from model.reminder import Reminder

class HelpCommands:
    def __init__(self, commands, helpMessage):
        self.commands = commands
        self.helpMessage = helpMessage

class DiscordBot:

    def __init__(self, isDevelopment):
        self.intents = discord.Intents.all()
        self.intents.voice_states = True
        self.client = commands.Bot(command_prefix=os.getenv("DISCORD_COMMAND_PREFIX"), intents=self.intents)
        self.client.remove_command('help')
        self.isDevelopment = isDevelopment
        if isDevelopment == 0 or isDevelopment == "0":
            discord.opus.load_opus("./libopus.so.0.8.0")
        self.isLooping = False
        self.songQueue = []
        self.spotify = Spotify()
        self.filename = "audio.mp3"
        self.currentSong = None
        self.youtube = Youtube()
    
    def run(self):        
        if self.isDevelopment == 1 or self.isDevelopment == "1":
            self.client.run(os.getenv("DISCORD_BOT_TOKEN"))
        else:
            self.client.run(os.getenv("DISCORD_TEST_TOKEN"))
        
    async def sendEmbed(self, ctx, message, color, author=None, title=None):
        embed = discord.Embed(title=title, description=message, color=color, )
        if author:
            embed.set_footer(text="Requested by {}".format(author.name), icon_url=author.avatar_url)
        await ctx.send(embed=embed)
        
    def isConnected(self, ctx):
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        return voice_client and voice_client.is_connected()
    
    def playMusic(self, voice):
        voice.play(discord.FFmpegPCMAudio(source=self.filename))
        
    async def on_ready(self):
        await self.sendReminder()

    async def help(self, ctx):
        addHelp = HelpCommands(["add", "a"], "Add a new song to the song queue. It can receive title of the song, youtube link, or spotify link")
        playHelp = HelpCommands(["play", "p"], "Play song from the song queue")
        skipHelp = HelpCommands(["skip", "s"], "Skip the current song")
        clearHelp = HelpCommands(["clear", "c"], "Clear the song queue")
        stopHelp = HelpCommands(["stop", "x"], "Stop playing songs, clear the song queue and reset bot status")
        loopHelp = HelpCommands(["loop", "l"], "Loop the song queue. When bot is looping, user cannot add or remove new song")
        queueHelp = HelpCommands(["queue", "q"], "Show the song queue")
        removeHelp = HelpCommands(["remove", "r"], "Remove a song from the song queue. Use index from the **!q** command")
        favoriteHelp = HelpCommands(["favorite", "fav", "f"], "Your own personal favorite song list\nadd\t : Add song to your favorite song list\nplay\t: Play your favorite song list\nlist\t : Show your favorite song list\nremove\t : Remove a song from your favorite song list")
        commands = [addHelp, playHelp, skipHelp, clearHelp, stopHelp, loopHelp, queueHelp, removeHelp, favoriteHelp]
        helpMessage = formatHelpString(commands)
        await self.sendEmbed(ctx, helpMessage, discord.Color.red(), title="GegekBot")

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
        
        song = self.getSong(url)
        song.setData(requester=author)
        self.songQueue.append(song)
        await self.sendEmbed(ctx, successMessage.format(song.title, formatDuration(song.length)), discord.Color.blue(), author=author)
        return 
    
    async def addBulk(self, ctx, songs):
        author = ctx.message.author
        voiceChannel = author.voice

        if self.isLooping:
            await self.sendEmbed(ctx, "Stop the loop using /loop before adding any new song", discord.Color.red())
            return

        try:
            for s in songs:
                yt = YouTube(s['url'])
                song = Song()
                song.setData(title=yt.title, url=s['url'], length=yt.length, requester=author)
                self.songQueue.append(song)
            return True
        except:
            return False

    async def on_voice_state_update(self, member, before, after):
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
    
    # TODO when playing song, set self.currentSong to it and remove it from self.songQueue
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

        if not self.isConnected(ctx):
            await channel.connect()

        while len(self.songQueue) > 0:
            self.currentSong = self.songQueue[0]
            self.songQueue.pop(0)

            out_file, errorCode = self.youtube.download(self.currentSong.url)

            if errorCode == 0:
                os.rename(out_file, self.filename)
                await self.sendEmbed(ctx, "Currently playing **" + self.currentSong.title + "**", discord.Color.blue())
                self.playMusic(voice)
                
                while self.currentSong.length > 0:
                    await sleep(1)
                    self.currentSong.length -= 1

                if self.isLooping:
                    self.songQueue.append(self.currentSong)

                os.remove(self.filename)
            elif errorCode == 1:
                await self.sendEmbed(ctx, "GegekBot lagi rusak, hubungi GEGEK", discord.Color.red())
            else:
                await self.sendEmbed(ctx, "Current song is age restricted", discord.Color.red())

        await voice.disconnect()
    
    async def stop(self, ctx):
        author = ctx.message.author
        voiceChannel = author.voice
        self.songQueue.clear()
        self.isLooping = False

        voiceState = ctx.guild.voice_client

        if not self.isConnected(ctx):
            await self.sendEmbed(ctx, "The bot is not connected to a voice channel.", discord.Color.red())
            return
        
        voiceState.stop()
        await voiceState.disconnect()
        await self.sendEmbed(ctx, "The audio is stopped.", discord.Color.red())
                
    async def clear(self, ctx):
        if len(self.songQueue) > 0:
            self.songQueue.clear()
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
        
        self.currentSong = self.songQueue[0]
        self.currentSong.length = 0
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
                    await self.addBulk(ctx, favoriteDict[author.id])
                    await self.sendEmbed(ctx, "Successfully added all favorite songs from " + author.name + "", discord.Color.blue())
                else :
                    await self.sendEmbed(ctx, "You don't have any favorite song", discord.Color.red())
            else:
                songs = copy.deepcopy(favoriteDict[author.id])
                random.shuffle(songs)
                if author.id in favoriteDict:
                    await self.addBulk(ctx, songs)
                    await self.sendEmbed(ctx, "Successfully added all favorite songs from " + author.name + " randomly", discord.Color.blue())
                else :
                    await self.sendEmbed(ctx, "You don't have any favorite song", discord.Color.red())
            await self.play(ctx)
        if command == "add":
            query = " ".join(args[1:])
            if query == "" or query == " ":
                await self.sendEmbed(ctx, "Please provide a song name", discord.Color.red())
                return
            song = self.getSong(query)

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
            
            songToRemove = favoriteDict[author.id][index - 1]
            favoriteDict[author.id].pop(index - 1)

            data = {"data":[]}
            for requester, songs in favoriteDict.items():
                data["data"].append({"requester": requester, "songs": songs})

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
    
    async def addReminder(self, ctx, *, arg):
        author = ctx.author
        
        args = arg.split(" ")
        if len(args) == 0:
            await self.sendEmbed(ctx, "Please provide a message and a datetime", discord.Color.red())
            return

        try:
            with open('./reminder.json') as f:
                notes = json.load(f)
        except json.decoder.JSONDecodeError:
            notes = {'data': []}

        reminderDict = {}
        for note in notes['data']:
            requester = note['requester']
            reminderDict[requester] = note['contents']
        
        message = " ".join(args[0:len(args)-1])
        dateStr = args[-1]
        date = None
        try:
            date = datetime.strptime(dateStr, "%d/%m/%Y-%H:%M:%S")
        except:
            await self.sendEmbed(ctx, "Please provide a valid date in format [dd/mm/yyyy-hh:mm:ss]", discord.Color.red())
            return

        if author.id in reminderDict:
            reminderDict[author.id].append({"message": message, "datetime": date.strftime("%Y-%m-%d %H:%M:%S")})
        else :
            reminderDict[author.id] = [{"message": message, "datetime": date.strftime("%Y-%m-%d %H:%M:%S")}]
        
        data = {"data":[]}
        for requester, contents in reminderDict.items():
            data["data"].append({"requester": requester, "contents": contents})

        with open('./reminder.json', 'w') as f:
            json.dump(data, f)
        await self.sendEmbed(ctx, "Added new reminder", discord.Color.blue())
    
    def getSong(self, url):
        if isSpotify(url):
            title = self.spotify.getSpotifyTitle(url)
            return self.youtube.search(title)
        elif isUrl(url):
            return self.youtube.getVideoData(url)
        else:
            return self.youtube.search(url)
    
    # async def sendReminder(self):
    #     print("Called")
    #     while True:
    #         with open('./reminder.json', 'r+') as f:
    #             notes = json.load(f)
    #         for note in notes['data']:
    #             requester = note['requester']
    #             contents = note['contents']
    #             for item in contents:
    #                 message = item['message']
    #                 date = item['datetime']
    #                 if timeDifference(date, 300):
    #                     channel = self.client.get_channel(int(os.getenv("REMINDER_CHANNEL_ID")))
    #                     embed = discord.Embed(description="**Reminder for <@" + str(requester) + ">**\n\n**Reminder:** " + message + "\n**Date:** " + date)
    #                     await channel.send(embed=embed)
                        
    #         await asyncio.sleep(60)
    
    async def sendReminder(self):
        while True:
            if os.stat('./reminder.json').st_size == 0:
                await asyncio.sleep(60)
                continue
            with open('./reminder.json', 'r+') as f:
                notes = json.load(f)
            sent_notes = []
            for note in notes['data']:
                requester = note['requester']
                contents = note['contents']
                unsent_contents = []
                for item in contents:
                    message = item['message']
                    date = item['datetime']
                    if timeDifference(date, 300):
                        channel = self.client.get_channel(int(os.getenv("REMINDER_CHANNEL_ID")))
                        embed = discord.Embed(description="**Reminder for <@" + str(requester) + ">**\n\n**Reminder:** " + message + "\n**Date:** " + date)
                        await channel.send(embed=embed)
                    else:
                        unsent_contents.append(item)
                if unsent_contents:
                    sent_notes.append({'requester': requester, 'contents': unsent_contents})
            notes['data'] = sent_notes
            with open('./reminder.json', 'w') as f:
                json.dump(notes, f)
            await asyncio.sleep(60)