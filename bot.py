import discord
from discord.ext import commands
import requests
import io
import os
from urllib.parse import quote

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Proxy services
PROXY_SERVICES = [
    {
        "name": "AllOrigins",
        "buildUrl": lambda url: f"https://api.allorigins.win/raw?url={quote(url)}"
    },
    {
        "name": "CodeTabs",
        "buildUrl": lambda url: f"https://api.codetabs.com/v1/proxy?quest={quote(url)}"
    },
    {
        "name": "CORSProxy",
        "buildUrl": lambda url: f"https://corsproxy.io/?{quote(url)}"
    },
    {
        "name": "TextProxies",
        "buildUrl": lambda url: f"https://textproxyapi.herokuapp.com/?url={quote(url)}"
    }
]

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.command()
async def l(ctx, url: str):
    """Fetch content from URL"""
    try:
        async with ctx.typing():
            text = None
            
            # Method 1: Direct fetch
            print(f"[Method 1] Trying direct fetch...")
            text = await fetch_direct(url)
            if text:
                await send_result(ctx, text)
                return
            
            # Method 2: Try with proxies
            print(f"[Method 2] Trying proxies...")
            for proxy in PROXY_SERVICES:
                print(f"[Proxy] Trying {proxy['name']}...")
                text = await fetch_with_proxy(url, proxy)
                if text:
                    await send_result(ctx, text)
                    return
            
            # All methods failed
            await ctx.reply("Cannot fetch URL from any method")
            
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")

async def fetch_direct(url: str):
    """Try direct fetch"""
    try:
        for attempt in range(3):
            try:
                r = requests.get(
                    url, 
                    timeout=20, 
                    headers=HEADERS, 
                    allow_redirects=True,
                    verify=False
                )
                r.raise_for_status()
                if r.text and r.text.strip():
                    return r.text
            except requests.exceptions.Timeout:
                if attempt < 2:
                    continue
            except Exception:
                if attempt < 2:
                    continue
        return None
    except:
        return None

async def fetch_with_proxy(url: str, proxy: dict):
    """Fetch URL through a proxy service"""
    try:
        proxy_url = proxy["buildUrl"](url)
        
        r = requests.get(
            proxy_url,
            timeout=20,
            headers=HEADERS,
            allow_redirects=True,
            verify=False
        )
        
        if r.status_code == 200 and r.text.strip():
            return r.text
        
        return None
    except Exception as e:
        print(f"Proxy {proxy['name']} failed: {e}")
        return None

async def send_result(ctx, text: str):
    """Send the fetched content to user"""
    try:
        if not text or not text.strip():
            await ctx.reply("Empty content")
            return
        
        # Upload to paste
        try:
            paste = requests.post(
                "https://paste.rs",
                data=text.encode("utf-8"),
                timeout=10
            )
            paste_url = paste.text.strip() if paste.ok else "Paste failed"
        except:
            paste_url = "Paste failed"
        
        # Create file
        file = discord.File(
            io.BytesIO(text.encode("utf-8")),
            filename="output.txt"
        )
        
        # Send DM
        try:
            await ctx.author.send(
                f"Fetched successfully\n\nPaste: {paste_url}",
                file=file
            )
            await ctx.reply("Check DMs!")
        except discord.Forbidden:
            await ctx.reply("Cannot send DMs")
            
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")

# Run bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set!")
        exit(1)
    bot.run(TOKEN)
