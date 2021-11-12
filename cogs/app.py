import discord
from discord.commands import slash_command, Option
from discord.commands.context import AutocompleteContext
from discord.ext import commands

import time
import json
import aiohttp
import io
import re
from colorthief import ColorThief

async def get_apps_autocompleter():
    res_apps = []
    async with aiohttp.ClientSession() as session:
        async with session.get("https://jailbreaks.app/json/apps.json") as resp:
            if resp.status == 200:
                data = await resp.text()
                apps = json.loads(data)

                # try to find an app with the name given in command
                for d in apps:
                    name = re.sub(r'\((.*?)\)', "", d["name"])
                    # get rid of '[ and ']'
                    name = name.replace('[', '')
                    name = name.replace(']', '')
                    name = name.strip()
                    if name not in res_apps:
                        res_apps.append(name)

    return res_apps


async def apps_autocomplete(ctx: AutocompleteContext):
    apps = await get_apps_autocompleter()
    apps.sort()
    return [app for app in apps if app.lower().startswith(ctx.value.lower())][:25]

async def get_apps():
    res_apps = []
    async with aiohttp.ClientSession() as session:
        async with session.get("https://jailbreaks.app/json/apps.json") as resp:
            if resp.status == 200:
                data = await resp.text()
                res_apps = json.loads(data)
    return res_apps

async def iterate_apps(query) -> dict:
    apps = await get_apps()
    for possibleApp in apps:
        if possibleApp['name'].lower() == query.lower():
            return possibleApp

class App(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refreshTime = int(round(time.time() * 1000))

    @slash_command(guild_ids=[834281087101304873], description="Get info about an app.")
    async def app(self, ctx: discord.ApplicationContext, name: Option(str, description="Name of the app", autocomplete=apps_autocomplete, required=True)) -> None:
        app = await iterate_apps(query=name)
        if app == None:
            await ctx.send_error("That app isn't on Jailbreaks.app.")
            return
        mainDLLink = f"https://api.jailbreaks.app/{name.replace(' ', '')}"
        allVersions = f"[Latest ({app['version']})](https://api.jailbreaks.app/{name.replace(' ', '')})"
        if len(app['other_versions']) != 0:
            for version in app['other_versions']:
                allVersions += f"\n[{version}](https://api.jailbreaks.app/{name.replace(' ', '')}/{version})"
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://jailbreaks.app/{app['icon']}") as icon:
                color = ColorThief(io.BytesIO(await icon.read())).get_color(quality=1)
        embed = discord.Embed(title=app['name'], color=discord.Color.from_rgb(
            color[0], color[1], color[2]), url=mainDLLink, description=app['short-description'])
        embed.set_thumbnail(url=f"https://jailbreaks.app/{app['icon']}")
        embed.add_field(
            name=f"Download{'' if len(app['other_versions']) == 0 else 's'}", value=allVersions, inline=True)
        embed.add_field(
            name="Developer", value=f"{('[' + app['dev'] + '](https://twitter.com/' + app['dev'] + ')') if app['dev'].startswith('@') else possibleApp['dev']}")
        embed.set_footer(text="SignedBot | Made by Jaidan", icon_url="https://avatars.githubusercontent.com/u/37126748")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(App(bot))