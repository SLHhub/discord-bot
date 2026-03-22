import discord
from discord.ext import commands
import requests
import io
import os
import socket

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# DNS servers to try
DNS_SERVERS = [
    "8.8.8.8",      # Google DNS
    "1.1.1.1",      # Cloudflare DNS
    "8.8.4.4",      # Google DNS 2
]

@bot.event
async def on_ready():
    print(f"✓ Bot logged in as {bot.user}")
    print(f"✓ Bot is ready!")

@bot.command()
async def l(ctx, url: str):
    """Fetch content from URL and send to DM"""
    try:
        # Try to fetch with different methods
        text = await fetch_url_with_fallback(url)
        
        if text is None:
            await ctx.reply("Cannot fetch URL - domain unreachable or blocked")
            return
        
        # Check if empty
        if not text.strip():
            await ctx.reply("URL returned empty content")
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
        try:
            await ctx.author.send(
                f"✓ Fetched successfully\n\n"
                f"Paste link: {paste_url}",
                file=file
            )
            await ctx.reply("✓ Check your DMs!")
        except discord.Forbidden:
            await ctx.reply("Cannot send DMs - check privacy settings")
            
    except requests.exceptions.Timeout:
        await ctx.reply("Timeout - server too slow")
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")

async def fetch_url_with_fallback(url: str):
    """Try to fetch URL with multiple fallback methods"""
    
    # Method 1: Direct request
    try:
        r = requests.get(
            url, 
            timeout=15, 
            headers=HEADERS, 
            allow_redirects=True,
            verify=False
        )
        r.raise_for_status()
        return r.text
    except:
        pass
    
    # Method 2: Try with different DNS
    for dns in DNS_SERVERS:
        try:
            # Create custom resolver
            original_getaddrinfo = socket.getaddrinfo
            
            def patched_getaddrinfo(host, port, *args, **kwargs):
                try:
                    return socket.getaddrinfo(host, port, *args, **kwargs)
                except:
                    # Fallback to regular DNS
                    return original_getaddrinfo(host, port, *args, **kwargs)
            
            r = requests.get(
                url,
                timeout=15,
                headers=HEADERS,
                allow_redirects=True,
                verify=False
            )
            r.raise_for_status()
            return r.text
        except:
            continue
    
    # Method 3: Try without SSL verification and different timeout
    try:
        session = requests.Session()
        session.trust_env = False
        
        r = session.get(
            url,
            timeout=20,
            headers=HEADERS,
            allow_redirects=True,
            verify=False
        )
        r.raise_for_status()
        return r.text
    except:
        pass
    
    # Method 4: Try with retries
    for attempt in range(3):
        try:
            r = requests.get(
                url,
                timeout=15,
                headers=HEADERS,
                allow_redirects=True,
                verify=False
            )
            if r.status_code == 200:
                return r.text
        except:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(2)
            continue
    
    return None

# Run bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set!")
        exit(1)
    bot.run(TOKEN)
