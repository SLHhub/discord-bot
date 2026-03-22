import discord
from discord.ext import commands
import requests
import io
import os
import asyncio
import ssl
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.util.ssl_ import create_urllib3_context

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

class HTTPSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

@bot.event
async def on_ready():
    print(f"✓ Bot logged in as {bot.user}")
    print(f"✓ Bot is ready!")

@bot.command()
async def l(ctx, url: str):
    """Fetch content from URL and send to DM"""
    try:
        async with ctx.typing():
            text = await fetch_url_ultimate(url)
            
            if text is None:
                await ctx.reply("Failed to fetch - trying alternative methods...")
                text = await fetch_with_fallback(url)
            
            if text is None:
                await ctx.reply("Cannot fetch URL - all methods failed")
                return
            
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
                
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")

async def fetch_url_ultimate(url: str):
    """Ultimate fetch with all workarounds"""
    
    # Method 1: Session with retries and custom SSL
    try:
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPSAdapter(max_retries=retry)
        session.mount('http://', HTTPAdapter(max_retries=retry))
        session.mount('https://', adapter)
        
        response = session.get(
            url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True,
            verify=False
        )
        
        if response.status_code == 200 and response.text.strip():
            return response.text
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Direct request with different timeout
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=45,
            allow_redirects=True,
            verify=False
        )
        if r.status_code == 200 and r.text.strip():
            return r.text
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Method 3: urllib3 direct
    try:
        import urllib3
        urllib3.disable_warnings()
        http = urllib3.PoolManager(
            cert_reqs='CERT_NONE',
            ca_certs=None
        )
        response = http.request(
            'GET',
            url,
            headers=HEADERS,
            timeout=30,
            retries=urllib3.Retry(5)
        )
        if response.status == 200:
            data = response.data.decode('utf-8', errors='ignore')
            if data.strip():
                return data
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    # Method 4: Try with curl-like behavior
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        session.verify = False
        
        r = session.get(url, timeout=60, stream=False)
        if r.status_code in [200, 201, 202]:
            text = r.content.decode('utf-8', errors='ignore')
            if text.strip():
                return text
    except Exception as e:
        print(f"Method 4 failed: {e}")
    
    # Method 5: DNS-over-HTTPS via Cloudflare
    try:
        host = url.split('//')[1].split('/')[0]
        import json
        
        dns_url = f"https://1.1.1.1/dns-query?name={host}&type=A"
        dns_headers = {"accept": "application/dns-json"}
        
        dns_response = requests.get(dns_url, headers=dns_headers, timeout=10, verify=False)
        if dns_response.status_code == 200:
            data = dns_response.json()
            if 'Answer' in data and data['Answer']:
                r = requests.get(url, headers=HEADERS, timeout=30, verify=False)
                if r.text.strip():
                    return r.text
    except Exception as e:
        print(f"Method 5 failed: {e}")
    
    return None

async def fetch_with_fallback(url: str):
    """Last resort fallback methods"""
    
    # Try with simple requests
    for timeout in [30, 45, 60]:
        try:
            r = requests.get(url, timeout=timeout, verify=False, headers=HEADERS)
            if r.text.strip():
                return r.text
        except:
            await asyncio.sleep(1)
    
    return None

# Run bot
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set!")
        exit(1)
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings()
    
    bot.run(TOKEN)
