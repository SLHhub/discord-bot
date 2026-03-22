import discord
from discord.ext import commands
import requests
import io
import os
from urllib.parse import quote
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

# Advanced headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

@bot.event
async def on_ready():
    print(f"✓ Bot ready as {bot.user}")

@bot.command()
async def l(ctx, url: str):
    """Fetch URL content with multiple methods"""
    try:
        async with ctx.typing():
            text = None
            
            # Method 1: Direct fetch with retries
            print("[Method 1] Direct fetch...")
            text = await fetch_direct(url)
            if text:
                await send_result(ctx, text)
                return
            
            # Method 2: Proxy 1 (AllOrigins)
            print("[Method 2] AllOrigins proxy...")
            text = await fetch_proxy(f"https://api.allorigins.win/raw?url={quote(url)}")
            if text:
                await send_result(ctx, text)
                return
            
            # Method 3: Proxy 2 (CodeTabs)
            print("[Method 3] CodeTabs proxy...")
            text = await fetch_proxy(f"https://api.codetabs.com/v1/proxy?quest={quote(url)}")
            if text:
                await send_result(ctx, text)
                return
            
            # Method 4: Proxy 3 (CORSProxy)
            print("[Method 4] CORSProxy...")
            text = await fetch_proxy(f"https://corsproxy.io/?{quote(url)}")
            if text:
                await send_result(ctx, text)
                return
            
            # Method 5: Direct with different timeout
            print("[Method 5] Direct with longer timeout...")
            text = await fetch_direct(url, timeout=40)
            if text:
                await send_result(ctx, text)
                return
            
            # Method 6: Session with pooling
            print("[Method 6] Session with connection pooling...")
            text = await fetch_session(url)
            if text:
                await send_result(ctx, text)
                return
            
            # All failed
            await ctx.reply("Failed: URL unreachable from all methods")
            
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:50]}")

async def fetch_direct(url: str, timeout=20):
    """Direct fetch with retry logic"""
    for attempt in range(3):
        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=timeout,
                verify=False,
                allow_redirects=True
            )
            
            if r.status_code == 200 and r.text.strip():
                return r.text
                
        except requests.exceptions.Timeout:
            if attempt < 2:
                await asyncio.sleep(2)
                continue
        except requests.exceptions.ConnectionError:
            if attempt < 2:
                await asyncio.sleep(2)
                continue
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(1)
                continue
    
    return None

async def fetch_proxy(proxy_url: str):
    """Fetch through proxy service"""
    try:
        for attempt in range(2):
            try:
                r = requests.get(
                    proxy_url,
                    headers=HEADERS,
                    timeout=20,
                    verify=False,
                    allow_redirects=True
                )
                
                if r.status_code == 200 and r.text.strip():
                    return r.text
            except:
                if attempt < 1:
                    await asyncio.sleep(1)
                    continue
        
        return None
    except:
        return None

async def fetch_session(url: str):
    """Fetch with session and connection pooling"""
    try:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3)
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        r = session.get(
            url,
            headers=HEADERS,
            timeout=30,
            verify=False,
            allow_redirects=True
        )
        
        if r.status_code == 200 and r.text.strip():
            return r.text
        
        return None
    except:
        return None

async def send_result(ctx, text: str):
    """Send fetched content to user"""
    try:
        if not text or not text.strip():
            await ctx.reply("Empty content")
            return
        
        # Upload to paste.rs
        try:
            paste = requests.post(
                "https://paste.rs",
                data=text.encode("utf-8"),
                timeout=10,
                headers=HEADERS
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
        await ctx.author.send(
            f"✓ Fetched successfully\n\nPaste: {paste_url}",
            file=file
        )
        await ctx.reply("✓ Check DMs!")
        
    except discord.Forbidden:
        await ctx.reply("Cannot send DMs - check privacy settings")
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:50]}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set!")
        exit(1)
    bot.run(TOKEN)
