import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from queue import Queue
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)

music_queue = Queue();


@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command(name='join')
async def join(ctx):
    # Check if the command author is in a voice channel
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f'Joined voice channel: {channel.name}')
    else:
        await ctx.send('You need to be in a voice channel to use this command.')


@bot.command(name='reduce')
async def reduce_volume(ctx):
    # Check if the bot is in a voice channel
    if ctx.voice_client:
        # Reduce the volume by 10%
        volume = ctx.voice_client.source.volume
        reduced_volume = max(0, volume - 0.1)
        ctx.voice_client.source.volume = reduced_volume
        await ctx.send(f'Reduced volume to {int(reduced_volume * 100)}%')
    else:
        await ctx.send('I need to be in a voice channel. Use the !join command.')

@bot.command(name='resume')
async def resume(ctx):
    # Check if the bot is in a voice channel and currently paused
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send('Playback resumed.')
    else:
        await ctx.send('I am not currently paused.')

@bot.command(name='play')
async def add_to_queue(ctx, query):
    # Check if the bot is in a voice channel
    if ctx.voice_client:
        music_queue.put(query);
        print(music_queue)
 
        while(music_queue.qsize() >= 1 and ctx.voice_client.is_playing() == False):
            await play(ctx);
            print("Checking here")
    else:
        await join(ctx)
        

def on_music_complete_callback(ctx, title):
    asyncio.run_coroutine_threadsafe(on_music_complete(ctx, title), bot.loop)
    
async def on_music_complete(ctx, title):
    print("Finished playing and now checking queue")
    await ctx.send(f'Finished playing {title}')

    if(music_queue.qsize() > 0 and ctx.voice_client.is_playing() == False):
        await play(ctx)

async def play(ctx):
    query = music_queue.get();
    res = search_youtube_videos(query)
    link = res['link']

    print(query , " ",link)
    await download_youtube_video(link)
    file_path = 'music.mp4'
    try:
        voice_channel = ctx.voice_client
        voice_channel.play(discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(file_path), volume=0.5),
            after = lambda e:  bot.loop.create_task(on_music_complete(ctx, res["title"])))
        await ctx.send(f'Now playing {res["title"]}')
    except FileNotFoundError:
        await ctx.send(f'Could not play {query}')

@bot.command(name='pause')
async def pause(ctx):
    # Check if the bot is in a voice channel and currently playing audio
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send('Playback paused.')
    else:
        await ctx.send('I am not currently playing any audio.')

@bot.command(name='stop')
async def stop(ctx):
    # Check if the bot is in a voice channel
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send('Playback stopped.')
    else:
        await ctx.send('I am not currently in a voice channel.')

from pytube import YouTube

async def download_youtube_video(url, output_path='.', file_name = 'music.mp4'):
    try:
        # Create a YouTube object
        yt = YouTube(url)

        # Get the highest resolution stream (you can customize this based on your needs)
        video_stream = yt.streams.get_highest_resolution()

        # Download the video
        video_stream.download(output_path,  filename=file_name)

        print(f"Video downloaded successfully to {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")



def search_youtube_videos(query, max_results=1):
    query = query + " song lyrics"

    videos_search = VideosSearch(query, limit=max_results)
    results = videos_search.result()
    
    if results and 'result' in results and len(results['result']) > 0:
        return results['result'][0]
    else:
        return None
    


bot.run(os.getenv('BOT_TOKEN'))
