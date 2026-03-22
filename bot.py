import discord
from discord.ext import commands
import requests
import io
import os
import re
import subprocess
import tempfile

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")

@bot.command()
async def l(ctx, url: str):
    """Fetch URL"""
    try:
        r = requests.get(url, timeout=15)
        text = r.text
        
        if not text.strip():
            await ctx.reply("Empty")
            return
        
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename="output.txt")
        await ctx.author.send(f"Fetched", file=file)
        await ctx.reply("Check DMs!")
    except:
        await ctx.reply("Error fetching URL")

@bot.command()
async def lua(ctx, *, code: str = None):
    """Deobfuscate Lua code using advanced method"""
    try:
        if code is None:
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                code = await attachment.read()
                code = code.decode('utf-8')
            else:
                await ctx.reply("Usage: `.lua <code>` or attach file")
                return
        
        # Advanced deobfuscation
        deobf = advanced_lua_deobfuscate(code)
        
        if not deobf.strip():
            await ctx.reply("Failed to deobfuscate")
            return
        
        file = discord.File(io.BytesIO(deobf.encode("utf-8")), filename="deobfuscated.lua")
        await ctx.author.send("Deobfuscated:", file=file)
        await ctx.reply("Check DMs!")
    except Exception as e:
        await ctx.reply(f"Error: {str(e)[:50]}")

def advanced_lua_deobfuscate(code: str) -> str:
    """Advanced Lua deobfuscator inspired by wearedevs"""
    try:
        result = code
        
        # Phase 1: Remove extra whitespace but preserve structure
        result = re.sub(r'[ \t]+', ' ', result)
        
        # Phase 2: Identify and format key structures
        # Format function definitions
        result = re.sub(r'function\s*\(', 'function(', result)
        result = re.sub(r'\)\s*{', '){', result)
        
        # Phase 3: Handle string obfuscation patterns
        # Look for common patterns like "\x##" and replace with actual chars
        def decode_hex_escape(match):
            hex_str = match.group(1)
            try:
                return chr(int(hex_str, 16))
            except:
                return match.group(0)
        
        result = re.sub(r'\\x([0-9a-fA-F]{2})', decode_hex_escape, result)
        
        # Phase 4: Handle decimal escapes
        def decode_decimal_escape(match):
            decimal_str = match.group(1)
            try:
                return chr(int(decimal_str))
            except:
                return match.group(0)
        
        result = re.sub(r'\\(\d{1,3})', decode_decimal_escape, result)
        
        # Phase 5: Format with proper indentation
        result = format_lua_code(result)
        
        # Phase 6: Clean up variable names if heavily obfuscated
        result = simplify_obfuscated_names(result)
        
        return result
        
    except Exception as e:
        return code

def format_lua_code(code: str) -> str:
    """Format Lua code with proper indentation"""
    try:
        # Split into meaningful chunks
        code = re.sub(r'\s+', ' ', code)
        
        # Add newlines after keywords
        keywords = ['then', 'do', 'function', 'local', 'if', 'for', 'while', 'repeat', 'else', 'elseif', 'end', 'return']
        for kw in keywords:
            code = re.sub(rf'\b{kw}\b', f'\n{kw}', code)
        
        code = code.replace(';', ';\n')
        code = code.replace('end,', 'end\n')
        
        # Remove multiple newlines
        code = re.sub(r'\n\n+', '\n', code)
        
        # Apply indentation
        lines = code.split('\n')
        formatted = []
        indent = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Decrease indent for closing keywords
            if any(line.startswith(kw) for kw in ['end', 'else', 'elseif']):
                indent = max(0, indent - 1)
            
            formatted.append('  ' * indent + line)
            
            # Increase indent for opening keywords
            if any(line.endswith(kw) or kw in line for kw in ['then', 'do', 'function']):
                if 'end' not in line:
                    indent += 1
        
        return '\n'.join(formatted)
    except:
        return code

def simplify_obfuscated_names(code: str) -> str:
    """Try to simplify variable names that are heavily obfuscated"""
    try:
        # Find patterns like a,b,c = 1,2,3 and format them
        code = re.sub(r',\s*', ', ', code)
        
        # Clean up common obfuscation patterns
        code = code.replace('__', '_')
        
        return code
    except:
        return code

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)
