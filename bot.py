import discord
from discord.ext import commands
import requests
import io
import os
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")

@bot.command()
async def l(ctx, url: str):
    """Fetch URL content"""
    try:
        r = requests.get(url, timeout=20, verify=False)
        text = r.text
        
        if not text.strip():
            await ctx.reply("Empty content")
            return
        
        # Paste to paste.rs
        try:
            paste = requests.post("https://paste.rs", data=text.encode("utf-8"), timeout=10)
            paste_url = paste.text.strip() if paste.ok else "Paste failed"
        except:
            paste_url = "Paste failed"
        
        # Send file
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename="output.txt")
        await ctx.author.send(f"Fetched\n\nPaste: {paste_url}", file=file)
        await ctx.reply("Check DMs!")
    except Exception as e:
        await ctx.reply(f"Error: Cannot fetch URL")

@bot.command()
async def deobfuscator(ctx, *, code: str = None):
    """Deobfuscate JavaScript code"""
    try:
        # Get code from message or attachment
        if code is None:
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                code = await attachment.read()
                code = code.decode('utf-8')
            else:
                await ctx.reply("Usage: `.deobfuscator <code>` or attach a file")
                return
        
        # Deobfuscate
        deobfuscated = deobfuscate_js(code)
        
        if not deobfuscated.strip():
            await ctx.reply("Empty code after deobfuscation")
            return
        
        # Send file
        file = discord.File(
            io.BytesIO(deobfuscated.encode("utf-8")),
            filename="deobfuscated.js"
        )
        await ctx.author.send(f"Deobfuscated JavaScript:", file=file)
        await ctx.reply("Check DMs!")
        
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")

@bot.command()
async def lua(ctx, *, code: str = None):
    """Deobfuscate Lua code"""
    try:
        # Get code from message or attachment
        if code is None:
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                code = await attachment.read()
                code = code.decode('utf-8')
            else:
                await ctx.reply("Usage: `.lua <code>` or attach a file")
                return
        
        # Deobfuscate
        deobfuscated = deobfuscate_lua(code)
        
        if not deobfuscated.strip():
            await ctx.reply("Empty code after deobfuscation")
            return
        
        # Send file
        file = discord.File(
            io.BytesIO(deobfuscated.encode("utf-8")),
            filename="deobfuscated.lua"
        )
        await ctx.author.send(f"Deobfuscated Lua:", file=file)
        await ctx.reply("Check DMs!")
        
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:100]}")

def deobfuscate_js(code: str) -> str:
    """Deobfuscate JavaScript code"""
    try:
        # Remove extra spaces and newlines
        deobf = re.sub(r'\s+', ' ', code)
        
        # Split by semicolons and format nicely
        deobf = deobf.replace(';', ';\n')
        deobf = deobf.replace('{', '{\n')
        deobf = deobf.replace('}', '\n}')
        deobf = deobf.replace(',', ',\n')
        
        # Remove multiple newlines
        deobf = re.sub(r'\n\n+', '\n', deobf)
        
        # Clean up
        lines = deobf.split('\n')
        cleaned = []
        indent = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle closing braces
            if line.startswith('}'):
                indent = max(0, indent - 1)
            
            # Add indentation
            cleaned.append('  ' * indent + line)
            
            # Handle opening braces
            if line.endswith('{'):
                indent += 1
            elif line.endswith('}'):
                indent = max(0, indent - 1)
        
        return '\n'.join(cleaned)
        
    except Exception as e:
        return f"Error deobfuscating: {str(e)}"

def deobfuscate_lua(code: str) -> str:
    """Deobfuscate Lua code"""
    try:
        deobf = code
        
        # Remove extra spaces
        deobf = re.sub(r'\s+', ' ', deobf)
        
        # Split by common delimiters
        deobf = deobf.replace('then', '\nthen\n')
        deobf = deobf.replace('do', '\ndo\n')
        deobf = deobf.replace('end', '\nend\n')
        deobf = deobf.replace('function', '\nfunction\n')
        deobf = deobf.replace('local', '\nlocal\n')
        deobf = deobf.replace('if', '\nif\n')
        deobf = deobf.replace('else', '\nelse\n')
        deobf = deobf.replace('elseif', '\nelseif\n')
        deobf = deobf.replace('for', '\nfor\n')
        deobf = deobf.replace('while', '\nwhile\n')
        deobf = deobf.replace('repeat', '\nrepeat\n')
        deobf = deobf.replace('until', '\nuntil\n')
        deobf = deobf.replace('return', '\nreturn\n')
        deobf = deobf.replace('break', '\nbreak\n')
        
        # Format semicolons and commas
        deobf = deobf.replace(';', ';\n')
        deobf = deobf.replace(',', ', ')
        
        # Remove multiple newlines
        deobf = re.sub(r'\n\n+', '\n', deobf)
        
        # Add proper indentation
        lines = deobf.split('\n')
        cleaned = []
        indent = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Decrease indent for 'end', 'else', 'elseif'
            if line.startswith('end') or line.startswith('else') or line.startswith('elseif'):
                indent = max(0, indent - 1)
            
            # Add indentation
            cleaned.append('  ' * indent + line)
            
            # Increase indent for keywords
            if line.endswith('then') or line.endswith('do') or line.startswith('function'):
                indent += 1
            elif line.startswith('repeat'):
                indent += 1
            
            # Decrease indent after certain keywords
            if line.startswith('until'):
                indent = max(0, indent - 1)
        
        return '\n'.join(cleaned)
        
    except Exception as e:
        return f"Error deobfuscating: {str(e)}"

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)
