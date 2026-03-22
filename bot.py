import discord
from discord.ext import commands
import requests
import io
import os
from urllib.parse import quote

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")

@bot.command()
async def l(ctx, url: str):
    try:
        text = None
        
        # Try cloudscraper first
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            r = scraper.get(url, timeout=20)
            if r.status_code == 200 and r.text.strip():
                text = r.text
        except:
            pass
        
        # Try proxies if cloudscraper fails
        if not text:
            proxies = [
                lambda url: f"https://api.allorigins.win/raw?url={quote(url)}",
                lambda url: f"https://api.codetabs.com/v1/proxy?quest={quote(url)}",
                lambda url: f"https://corsproxy.io/?{quote(url)}",
            ]
            
            for proxy_func in proxies:
                try:
                    proxy_url = proxy_func(url)
                    r = requests.get(proxy_url, timeout=20, verify=False)
                    if r.status_code == 200 and r.text.strip():
                        text = r.text
                        break
                except:
                    continue
        
        # Try direct as last resort
        if not text:
            try:
                r = requests.get(url, timeout=20, verify=False)
                if r.text.strip():
                    text = r.text
            except:
                pass
        
        if not text:
            await ctx.reply("Cannot fetch URL - Cloudflare blocking")
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
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:50]}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)
