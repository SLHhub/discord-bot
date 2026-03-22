import discord
from discord.ext import commands
import requests
import io
import os
from urllib.parse import quote
import time

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

# Headers that bypass Cloudflare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")

@bot.command()
async def l(ctx, url: str):
    try:
        text = None
        
        # Method 1: Try direct with Cloudflare bypass headers
        print("[1] Trying direct with bypass headers...")
        text = await fetch_direct(url)
        if text:
            await send_result(ctx, text)
            return
        
        # Method 2: Try with delay (sometimes helps with rate limiting)
        print("[2] Trying with delay...")
        time.sleep(2)
        text = await fetch_direct(url)
        if text:
            await send_result(ctx, text)
            return
        
        # Method 3: Try proxies
        print("[3] Trying proxies...")
        proxies = [
            lambda url: f"https://api.allorigins.win/raw?url={quote(url)}",
            lambda url: f"https://api.codetabs.com/v1/proxy?quest={quote(url)}",
            lambda url: f"https://corsproxy.io/?{quote(url)}",
        ]
        
        for proxy_func in proxies:
            try:
                proxy_url = proxy_func(url)
                r = requests.get(proxy_url, timeout=20, headers=HEADERS, verify=False)
                if r.status_code == 200 and r.text.strip():
                    text = r.text
                    break
            except:
                continue
        
        if not text:
            await ctx.reply("Cloudflare is blocking the request. Try again later.")
            return
        
        await send_result(ctx, text)
        
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:50]}")

async def fetch_direct(url: str):
    """Fetch with Cloudflare bypass"""
    try:
        session = requests.Session()
        
        # Add retry logic
        for attempt in range(3):
            try:
                r = session.get(
                    url,
                    headers=HEADERS,
                    timeout=25,
                    verify=False,
                    allow_redirects=True
                )
                
                # Check if we got blocked by Cloudflare
                if "429" in str(r.status_code) or "Cloudflare" in r.text:
                    if attempt < 2:
                        time.sleep(3)
                        continue
                    return None
                
                if r.status_code == 200 and r.text.strip():
                    return r.text
                    
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(2)
                    continue
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
        
        return None
    except:
        return None

async def send_result(ctx, text: str):
    """Send the fetched content"""
    try:
        if not text or not text.strip():
            await ctx.reply("Empty content")
            return
        
        # Upload to paste
        try:
            paste = requests.post("https://paste.rs", data=text.encode("utf-8"), timeout=10)
            paste_url = paste.text.strip() if paste.ok else "Failed"
        except:
            paste_url = "Failed"
        
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename="output.txt")
        
        await ctx.author.send(f"Fetched\n\nPaste: {paste_url}", file=file)
        await ctx.reply("Check DMs!")
    except discord.Forbidden:
        await ctx.reply("Cannot send DMs")
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:50]}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: Token not set!")
        exit(1)
    bot.run(TOKEN)
