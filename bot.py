import discord
from discord.ext import commands
import requests
import io
import os
 
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)
 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
 
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
 
@bot.command()
async def l(ctx, url: str):
    try:
        r = requests.get(
            url, 
            timeout=15, 
            headers=HEADERS, 
            allow_redirects=True,
            verify=False
        )
        r.raise_for_status()
        text = r.text
        
        if not text.strip():
            await ctx.reply("Empty content")
            return
        
        try:
            paste = requests.post(
                "https://paste.rs",
                data=text.encode("utf-8"),
                timeout=10
            )
            paste_url = paste.text.strip() if paste.ok else "Failed"
        except:
            paste_url = "Failed"
        
        file = discord.File(
            io.BytesIO(text.encode("utf-8")),
            filename="output.txt"
        )
        
        try:
            await ctx.author.send(
                f"Fetched successfully\n\nPaste: {paste_url}",
                file=file
            )
            await ctx.reply("Check DMs!")
        except discord.Forbidden:
            await ctx.reply("Cannot send DMs")
            
    except requests.exceptions.Timeout:
        await ctx.reply("Timeout")
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")
 
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set!")
        exit(1)
    bot.run(TOKEN)
