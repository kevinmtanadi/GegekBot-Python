import os
import discord
from discord.ext import commands
import re
from youtube_search import YoutubeSearch
from asyncio import sleep
from dotenv import load_dotenv
import copy

from keep_alive import Keep_alive

import sys

sys.path.append('./pytube')
import pytube
from pytube import YouTube

SPOTIFY_CLIENT_ID = '49d73e178df14889b00512b3b86b7c8a'
SPOTIFY_CLIENT_SECRET = '1c53f0af3bc548d1bc01bab0117f7771'

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

Keep_alive()

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

discord.opus.load_opus("./libopus.so.0.8.0")

client_credentials_manager = SpotifyClientCredentials(
  client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


class Song:

  def __init__(self, title, url, id, length):
    self.id = id
    self.title = title
    self.url = url
    self.length = length


class Looper:

  def __init__(self):
    self.isLooping = False

  def changeLoopStatus(self):
    self.isLooping = not self.isLooping


songQueue = []
filename = "audio.mp3"
looper = Looper()


def makeEmbed(message, color):
  embed = discord.Embed(description=message, color=color)
  return embed


def is_url(url):
  regex = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE)
  if url is not None and regex.search(url):
    return True
  return False


def is_spotify(url):
  return url.startswith("https://open.spotify.com") or url.startswith(
    "open.spotify.com")


def get_spotify_title(url):
  track_id = track_id = url.split('/')[-1].split('?')[0]
  res = 'spotify:track:' + track_id
  track = sp.track(res)
  title = track['name']
  artist = track['artists'][0]['name']

  return title + " - " + artist


def is_connected(ctx):
  voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
  return voice_client and voice_client.is_connected()


def play_music(voice):
  voice.play(discord.FFmpegPCMAudio(source=filename))


intents.voice_states = True


@client.event
async def on_voice_state_update(member, before, after):
  voice_state = member.guild.voice_client
  if voice_state is None:
    # Exiting if the bot it's not connected to a voice channel
    return

  if len(voice_state.channel.members) == 1:
    await voice_state.disconnect()


# @client.command()
# async def help(ctx):
#   embed = makeEmbed("Test help")
#   await ctx.send(embed=embed)

@client.command()
async def spotify(ctx, *, url: str):
  if (is_spotify(url)):
    searchQuery = get_spotify_title(url)
    print(searchQuery)
    result = YoutubeSearch(searchQuery, max_results=1).to_dict()
    for v in result:
      youtube_url = "https://www.youtube.com" + v['url_suffix']
      embed = makeEmbed(youtube_url, discord.Color.blue())
      await ctx.send(embed=embed)

@client.command()
async def add(ctx, *, url: str):
  id = 0
  author = ctx.message.author.voice
  if not author:
    embed = makeEmbed("You have to be in a voice channel to play a song!",
                      discord.Color.red())
    await ctx.send(embed=embed)
  else:
    if looper.isLooping:
      embed = makeEmbed("Stop the loop using /loop before adding any new song",
                        discord.Color.red())
      await ctx.send(embed=embed)
    else:
      if (is_url(url)):
        if (is_spotify(url)):
          searchQuery = get_spotify_title(url)
          print(searchQuery)
          result = YoutubeSearch(searchQuery, max_results=1).to_dict()
          for v in result:
            youtube_url = "https://www.youtube.com" + v['url_suffix']
            yt = YouTube(youtube_url)
            songQueue.append(Song(yt.title, youtube_url, id, yt.length))
        else:
          yt = YouTube(url)
          songQueue.append(Song(yt.title, url, id, yt.length))
      else:
        result = YoutubeSearch(url, max_results=1).to_dict()
        for v in result:
          youtube_url = "https://www.youtube.com" + v['url_suffix']
          yt = YouTube(youtube_url)
          songQueue.append(Song(yt.title, youtube_url, id, yt.length))
      id += 1
      embed = makeEmbed("**" + yt.title + "** added to the queue!",
                        discord.Color.blue())
      await ctx.send(embed=embed)


@client.command()
async def loop(ctx):
  if len(songQueue) > 0:
    looper.changeLoopStatus()
    if looper.isLooping:
      embed = makeEmbed("Currently looping", discord.Color.blue())
      await ctx.send(embed=embed)
    else:
      embed = makeEmbed("Stop looping", discord.Color.blue())
      await ctx.send(embed=embed)

  else:
    embed = makeEmbed(
      "There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue",
      discord.Color.red())
    await ctx.send(embed=embed)


@client.command()
async def queue(ctx):
  if len(songQueue) > 0:
    i = 1
    songList = "Current song queue :\n"
    for songs in songQueue:
      songList += str(i) + ". " + songs.title + "\n"
      i += 1
    embed = makeEmbed(songList, discord.Color.blue())
    await ctx.send(embed=embed)
  else:
    embed = makeEmbed(
      "There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue",
      discord.Color.red())
    await ctx.send(embed=embed)


@client.command()
async def play(ctx):
  if os.path.isfile(filename):
    os.remove(filename)
  if len(songQueue) == 0:
    embed = makeEmbed(
      "There is currently no song in the queue! Use !add [music title or youtube link] to add a song to the queue",
      discord.Color.red())
    await ctx.send(embed=embed)
  else:
    author = ctx.message.author.voice
    if not author:
      embed = makeEmbed("You have to be in a voice channel to play a song!",
                        discord.Color.red())
      await ctx.send(embed=embed)
    channel = author.channel
    try:
      await channel.connect()
    except:
      print("Bot already connected")
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice is None or not voice.is_connected():
      await channel.connect()

    while len(songQueue) > 0:
      currentSong = songQueue[0]
      songLength = copy.deepcopy(currentSong.length)

      success = False
      try:
        yt = YouTube(currentSong.url)
        audio = yt.streams.filter(only_audio=True).first()
        out_file = audio.download(output_path=".")
        success = True

      except pytube.exceptions.RegexMatchError:
        embed = makeEmbed(
          "Cannot download song, need to fix pytube library regex. Hubungi GEGEK",
          discord.Color.red())
        await ctx.send(embed=embed)
        songQueue.clear()
      except pytube.exceptions.AgeRestrictedError:
        embed = makeEmbed(
          "Current song **" + yt.title + "** is age restricted",
          discord.Color.red())
        await ctx.send(embed=embed)

      if success:
        os.rename(out_file, filename)
        embed = makeEmbed("Currently playing **" + yt.title + "**",
                          discord.Color.blue())
        await ctx.send(embed=embed)
        play_music(voice)

        while currentSong.length > 0:
          await sleep(1)
          currentSong.length -= 1

        currentSong.length = songLength

        if looper.isLooping:
          songQueue.append(currentSong)

        songQueue.pop(0)
        os.remove(filename)

    await voice.disconnect()


@client.command()
async def stop(ctx):
  author = ctx.message.author.voice
  songQueue.clear()
  looper.isLooping = False
  if not author:
    embed = makeEmbed("You have to be in a voice channel!",
                      discord.Color.red())
    await ctx.send(embed=embed)
  else:
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if not voice.is_connected():
      embed = makeEmbed("The bot is not connected to a voice channel.",
                        discord.Color.red())
      await ctx.send(embed=embed)
    else:
      voice.stop()
      if voice.is_connected():
        embed = makeEmbed("The audio is stopped.", discord.Color.red())
        await ctx.send(embed=embed)
        await voice.disconnect()
      else:
        embed = makeEmbed("The bot is not connected to a voice channel.",
                          discord.Color.red())
        await ctx.send(embed=embed)
        await voice.disconnect()


@client.command()
async def clear(ctx):
  if len(songQueue) > 1:
    embed = makeEmbed("The song queue is emptied", discord.Color.red())
    await ctx.send(embed=embed)
  else:
    embed = makeEmbed("There is currently no song in the queue!",
                      discord.Color.red())
    await ctx.send(embed=embed)


@client.command()
async def skip(ctx):
  author = ctx.message.author.voice
  if not author:
    embed = makeEmbed("You have to be in a voice channel!",
                      discord.Color.red())
    await ctx.send(embed=embed)
  else:
    currentSong = songQueue[0]
    currentSong.length = 0
    ctx.voice_client.stop()


@client.command()
async def remove(ctx, arg: int):
  if len(songQueue) >= 1:
    if arg > len(songQueue):
      embed = makeEmbed(
        "There are only " + str(len(songQueue)) + "songs in the queue!",
        discord.Color.red())
      await ctx.send(embed=embed)
    else:
      songToDelete = songQueue[arg - 1]
      embed = makeEmbed(
        "Successfully deleted " + str(songToDelete.title) + " from to queue",
        discord.Color.blue())
      await ctx.send(embed=embed)
      songQueue.remove(songToDelete)

  else:
    embed = makeEmbed("There is currently no song in the queue!",
                      discord.Color.blue())
    await ctx.send(embed=embed)


client.run(
  'OTUwMzI2NjU2NTI1MDEzMDgy.GhbrsT.Tbz7ZvPaGNJRjA0ySJVPwpnNPotIqPM04g04Gg')

FFMPEG_PATH = '/home/runner/libopus/node_modules/ffmpeg-static/ffmpeg'

# good luck!

# TO DOWNLOAD FFMPEG:
# ctrl+shift+s
# npm install ffmpeg-static
# node -e "console.log(require('ffmpeg-static'))"
# copy result to variable below:
