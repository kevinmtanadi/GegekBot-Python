import os
from asyncio import sleep
from dotenv import load_dotenv

from keep_alive import Keep_alive
from service.discord import DiscordBot

#################################################################################
# import sys
# sys.path.append('./pytube')
# import pytube
# from pytube import YouTube
# yt = YouTube("https://www.youtube.com/watch?v=8_TYFfkc_1U")
# audio = yt.streams.filter(only_audio=True).first()
# out_file = audio.download(output_path=".")
#################################################################################

# import json

# class FavoriteSong:
#     def __init__(self, requester, songs):
#         self.requester = requester
#         self.songs = songs

# with open('./favorite.json') as f:
#     favorites = json.load(f)

# favoriteDict = {}
# for fav in favorites['data']:
#     requester = fav['requester']
#     favoriteDict[requester] = fav['songs']

# print(favoriteDict['Gegek'])
        

#################################################################################

isTesting = 1
if isTesting != 0:
    Keep_alive()

    load_dotenv()
    isDevelopment = os.getenv("IS_DEVELOPMENT")
    bot = DiscordBot(isDevelopment)
    client = bot.client

    @client.command()
    async def add(ctx, *, url: str):
        await bot.add(ctx, url=url)
    @client.command()
    async def a(ctx, *, url: str):
        await bot.add(ctx, url=url)
        
    @client.command()
    async def loop(ctx):
        await bot.loop(ctx)
        
    @client.command()
    async def play(ctx):
        await bot.play(ctx)
    @client.command()
    async def p(ctx):
        await bot.play(ctx)


    @client.command()
    async def queue(ctx):
        await bot.queue(ctx)
    @client.command()
    async def q(ctx):
        await bot.queue(ctx)

    @client.command()
    async def stop(ctx):
        await bot.stop(ctx)
    @client.command()
    async def x(ctx):
        await bot.stop(ctx)
        
    @client.command()
    async def clear(ctx):
        await bot.clear(ctx)
    @client.command()
    async def c(ctx):
        await bot.clear(ctx)
        
    @client.command()
    async def remove(ctx, arg: int):
        await bot.remove(ctx, arg)
    @client.command()
    async def r(ctx, arg: int):
        await bot.remove(ctx, arg)

    @client.command()
    async def skip(ctx):
        await bot.skip(ctx)
    @client.command()
    async def s(ctx):
        await bot.skip(ctx)
    
    @client.command()
    async def favorite(ctx, *, arg: str):
        await bot.favorite(ctx, arg=arg)
    @client.command()
    async def fav(ctx, *, arg: str):
        await bot.favorite(ctx, arg=arg)
    @client.command()
    async def f(ctx, *, arg:str):
        await bot.favorite(ctx, arg=arg)

    @client.event
    async def on_voice_state_update(member, before, after):
        await bot.on_voice_state_update(member)

    bot.run()

    FFMPEG_PATH = '/home/runner/libopus/node_modules/ffmpeg-static/ffmpeg'

