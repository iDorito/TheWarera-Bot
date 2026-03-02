# ------------------------------------------
# AUTHOR: Ricardo Faria
# Github: https://github.com/iDorito
#
# Script: main.py
# Description: Main controller script for TheWarera bot
# ------------------------------------------

# Dependencies
import os
import datetime
import time
import aiohttp
import aiofiles
import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
import asyncio
import json
import logging
import matplotlib.pyplot as plt
from collections import Counter

from datetime import datetime, timedelta, timezone, time

# DIR
BASE_DIR = ""

try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('debug.log'),
              logging.StreamHandler()])

# API ERRORS
RETRY_429 = 30
DELAY = 0.2

# Loading ENV
load_dotenv()  # Secret stuff, no se toca papu xdxd

# Tokens
TOKEN = os.getenv('BOT_TOKEN')

# Default vars
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# ------------------------------------------
# UI Components
class GuidesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Guías", style=discord.ButtonStyle.primary, custom_id="guides_btn")
    async def guides_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GuideDropdownView()
        embed = discord.Embed(
            title="📚 Panel de Guías",
            description="Selecciona una guía del menú desplegable para ver su contenido.",
            color=0x00ff00
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Builds", style=discord.ButtonStyle.secondary, custom_id="builds_btn")
    async def builds_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚔️ Builds Recomendadas",
            description="Próximamente... Aquí podrás encontrar las mejores builds para cada nivel.",
            color=0x00aaff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GuideDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Empresas inicial", description="Guía óptima para comenzar con tus empresas.", emoji="🏢"),
        ]
        super().__init__(placeholder="Selecciona una guía...", min_values=1, max_values=1, options=options, custom_id="guide_select")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Empresas inicial":
            embed = discord.Embed(
                title="🏢 Guía para empresas óptima (Hecha por Odracir)",
                description=(
                    "**Empresas 1 -> 4:** Cada empresa comprada, subirla a nivel 4 de automatización, una atrás de la otra.\n\n"
                    "**Empresa 1:** Piedra - Automatizar a nivel 4.\n"
                    "**Empresa 2:** Cemento - Automatizar a nivel 4 + 1 Mejora de almacén (contratar trabajador para esta empresa, solo uno).\n"
                    "**Empresa 3:** Piedra - Automatizar a nivel 4.\n"
                    "**Empresa 4:** Cemento - Automatizar a nivel 4.\n\n"
                    "**Nota:** Sus puntos de emprendimiento deben ser usados en piedra mientras su trabajador genera puntos de producción en cemento.\n\n"
                    "Luego de tener las primeras 4 empresas automatizadas a nivel 4, es más rentable pasar directamente a automatizar todas a nivel 5.\n\n"
                    "**Empresas 1 a la 4:** Automatizar a nivel 5.\n\n"
                    "**Empresa 5:** Piedra - Automatizar hasta nivel 5.\n"
                    "**Empresa 6:** Acero - Automatizar hasta nivel 5.\n\n"
                    "En este punto, puedes entrar en el ciclo de producción de acero para automatizar todas a nivel 6 y tener tus empresas listas para mantenerte en eco y producir materiales para empezar a producir balas, comprar equipación, y prepararte generalmente para el modo ataque cuando sea necesario y apropiado según tu nivel, para esto consultar las build de ataque y guías en ⁠『💹』guías-y-manuales\n\n"
                    "**PARA NIVEL 32+:**\n"
                    "Todas las siguientes empresas 7 - 12 deben ser automatizadas hasta nivel 6 apenas compradas."
                ),
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class GuideDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GuideDropdown())
        
    @discord.ui.button(label="Volver", style=discord.ButtonStyle.gray)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GuidesView()
        embed = discord.Embed(
            title="📖 Centro de Ayuda Warera",
            description="Bienvenido al centro de ayuda. Selecciona una categoría para comenzar.",
            color=0x4B0082
        )
        await interaction.response.edit_message(embed=embed, view=view)

# ------------------------------------------
# Api calls
async def api_fetch(url, headers):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None, resp
            data = await resp.json()
    return data, resp


async def api_fetch_post(url, payload, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                print("Error getting data.")
                return None, resp
            data = await resp.json()
    return data, resp


# ------------------------------------------
# Sync
# @client.event
# async def on_ready():
#     print(f'✅ Bot ready: {client.user}')

#     try:
#         synced = await tree.sync()  # Loading command tree for servers
#         print(f"Global commands synched: {len(synced)}!")
#         for cmd in synced:
#             print(f" - {cmd.name}")
#     except Exception as e:
#         print(f"Error sincronizing commands: {e}")


# ------------------------------------------
# User info with ID
@tree.command(name="ayuda", description="Muestra el panel de guías y builds.")
async def ayuda(interaction: discord.Interaction):
    view = GuidesView()
    embed = discord.Embed(
        title="📖 Centro de Ayuda Warera",
        description="Bienvenido al centro de ayuda. Selecciona una categoría para comenzar.",
        color=0x4B0082
    )
    await interaction.response.send_message(embed=embed, view=view)


@tree.command(name="userinfo", description="Obten tu información de usuario.")
@app_commands.describe(user_name="Warera user name")
async def user_info(interaction: discord.Interaction, user_name: str):
    await interaction.response.defer()

    # ------------------------------------
    # Getting user id by name
    # ------------------------------------
    user_info_url = f"https://api2.warera.io/trpc/search.searchAnything?input=%7B%22searchText%22%3A%22{user_name}%22%7D"
    headers = {'Content-Type': 'application/json'}

    data, resp = await api_fetch(user_info_url, headers)
    if data is None:
        await interaction.followup.send(
            f"❌ API error: {resp.status} - User name is needed.")
        return

    try:
        user_search_data = data["result"]["data"]
        user_ids = user_search_data.get("userIds", [])
        if not user_ids or not isinstance(user_ids, list):
            await interaction.followup.send(
                f"❌ No user found with name: {user_name}")
            return
        user_id = user_ids[0]
    except (KeyError, TypeError, IndexError):
        await interaction.followup.send(
            "❌ Couldn't find user or bad server response.")
        return

    # ------------------------------------
    # Getting user info
    # ------------------------------------
    user_info_url = f"https://api2.warera.io/trpc/user.getUserLite?input=%7B%22userId%22%3A%22{user_id}%22%7D"
    headers = {'Content-Type': 'application/json'}

    data, resp = await api_fetch(user_info_url, headers)
    if data is None:
        await interaction.followup.send(
            f"❌ API error: {resp.status} - Could not fetch user details.")
        return

    try:
        user = data["result"]["data"]
    except KeyError:
        await interaction.followup.send(
            "❌ Bad server response while fetching user details.")
        return

    # ------------------------------------
    # Making embed
    # ------------------------------------
    embed = discord.Embed(
        title=f"👤 {user.get('username', 'Usuario')} | Warera",
        description=user.get('bio', 'Warera player'),
        color=0x4B0082)
    embed.set_thumbnail(url=user.get('avatarUrl', ''))

    # Basic Info
    embed.add_field(name="🆔 ID", value=user_id, inline=False)
    embed.add_field(name="🌍 País", value="Venezuela", inline=True)
    embed.add_field(name="📅 Miembro desde",
                    value=user.get('createdAt', 'N/A').split('T')[0],
                    inline=True)

    # Leveling & Experience
    leveling = user.get("leveling", {})
    embed.add_field(name="⚔️ Nivel",
                    value=leveling.get("level", 'N/A'),
                    inline=True)
    embed.add_field(name="✨ EXP Total",
                    value=f"{leveling.get('totalXp', 0):,}",
                    inline=True)
    embed.add_field(name="📊 EXP Diario",
                    value=f"{leveling.get('dailyXpLeft', 0)}/100",
                    inline=True)

    # Military & Combat
    embed.add_field(name="🎖️ Rango Militar",
                    value=user.get("militaryRank", 'N/A'),
                    inline=True)
    stats = user.get("stats", {})
    embed.add_field(name="💥 Daño Total",
                    value=f"{stats.get('damagesCount', 0):,}",
                    inline=True)
    embed.add_field(name="🛡️ Armadura",
                    value=leveling.get('availableSkillPoints', 0),
                    inline=True)

    # Skills Summary
    skills = user.get("skills", {})
    embed.add_field(
        name="⚡ Energía",
        value=
        f"{skills.get('energy', {}).get('currentBarValue', 0)}/{skills.get('energy', {}).get('total', 0)}",
        inline=True)
    embed.add_field(
        name="❤️ Salud",
        value=
        f"{skills.get('health', {}).get('currentBarValue', 0):.2f}/{skills.get('health', {}).get('total', 0):.2f}",
        inline=True)
    embed.add_field(
        name="🍖 Hambre",
        value=
        f"{skills.get('hunger', {}).get('currentBarValue', 0)}/{skills.get('hunger', {}).get('total', 0)}",
        inline=True)

    # Activity
    last_conn = user.get('dates', {}).get('lastConnectionAt', 'N/A')
    last_conn_formatted = 'N/A'
    if last_conn != 'N/A':
        dt = datetime.fromisoformat(last_conn.replace('Z', '+00:00'))
        last_conn_formatted = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    embed.add_field(name="🟢 Última conexión",
                    value=last_conn_formatted,
                    inline=False)
    embed.add_field(name="🏢 Empresas",
                    value=skills.get('companies', {}).get('total', 0),
                    inline=True)
    embed.add_field(name="📈 Puntos de habilidad",
                    value=leveling.get('availableSkillPoints', 0),
                    inline=True)

    embed.set_footer(text="Warera Stats",
                     icon_url="https://warera.io/favicon.ico")

    await interaction.followup.send(embed=embed)


@tree.command(
    name="active_players_2d",
    description="Obten una grafica con los jugadores activos. 2 Dias")
async def active_players_char_2days(interaction: discord.Interaction):
    await interaction.response.defer()
    logging.info("Making chart")

    try:
        # Calculate date from 2 days ago at 00:00:00
        now = datetime.now(timezone.utc)
        two_days_ago = (now - timedelta(days=2)).replace(hour=0,
                                                         minute=0,
                                                         second=0,
                                                         microsecond=0)

        # Load player stats
        player_stats_path = os.path.join(BASE_DIR, "player_stats.json")
        players = await load_all_players_stats(player_stats_path)

        if not players:
            await interaction.followup.send("❌ No player data available.")
            return

        # Filter by date
        filtered_players = [
            p for p in players
            if datetime.fromisoformat(p['dates']['lastConnectionAt'].replace(
                'Z', '+00:00')) >= two_days_ago
        ]

        # Count levels
        level_counts = Counter(player['leveling']['level']
                               for player in filtered_players)

        # Create chart
        min_level = min(level_counts.keys())
        max_level = max(level_counts.keys())
        all_levels = list(range(min_level, max_level + 1))
        counts = [level_counts.get(level, 0) for level in all_levels]

        plt.figure(figsize=(10, 6))
        plt.bar(all_levels, counts, color='indigo', width=0.8)
        plt.xlabel("Nivel de jugador")
        plt.ylabel("Numero de jugadores")
        plt.title("Distribución de jugadores por nivel (Últimos 2 días)")
        plt.xticks(all_levels)

        max_count = max(counts)
        for x, y in zip(all_levels, counts):
            plt.text(x,
                     y + max_count * 0.02,
                     str(y),
                     ha='center',
                     va='bottom',
                     fontsize=8)

        plt.ylim(0, max_count * 1.25)
        plt.tight_layout()

        chart_path = os.path.join(BASE_DIR, "active_players_2d.jpg")
        plt.savefig(chart_path, format='jpeg', dpi=300)
        plt.close()

        # Create embed with chart
        embed = discord.Embed(
            title="📊 Jugadores Activos - Últimos 2 Días",
            description=f"Total de jugadores activos: {len(filtered_players)}",
            color=0x4B0082)
        embed.set_image(url="attachment://active_players_2d.jpg")

        await interaction.followup.send(embed=embed,
                                        file=discord.File(chart_path))
        logging.info("Chart sent successfully")

    except Exception as e:
        logging.error(f"Error creating chart: {e}")
        await interaction.followup.send(f"❌ Error creating chart: {e}")


# -------------------
# HOURLY PLAYER IDS
async def get_all_player_ids():
    # Loop to get all the player ids for Venezuela
    user_ids = []
    URL = "https://api2.warera.io/trpc/user.getUsersByCountry"
    headers = {'Content-Type': 'application/json'}
    payload = {"countryId": "6813b6d546e731854c7ac858", "limit": 100}
    cursor = ""

    print("getting all player ids")

    try:
        print("Trying to fetch all ids...")
        while cursor is not None:
            print("Cursor is not none...")
            data, resp = await api_fetch_post(URL, payload, headers)
            print("Got data for players...")
            if resp.status == 200:
                print("Fetched player ids...")

                result = data.get("result", {})
                response_data = result.get("data", {})
                cursor = response_data.get("nextCursor")

                for user_info in response_data.get("items", []):
                    user_ids.append(user_info.get('_id'))

                payload['cursor'] = cursor
                await asyncio.sleep(0.2)
            elif resp.status == 429:
                print("Rate limited, waiting 30 seconds...")
                await asyncio.sleep(30)
            else:
                print(f"Error: {resp.status}")
                break
    except Exception as e:
        print(f"Connection error: {e}")

    return user_ids


async def save_user_ids(path, ids):
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(ids, ensure_ascii=False, indent=2))


async def load_user_ids(path):
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()  # async read
        return json.loads(text)


@tasks.loop(hours=1)
async def update_player_ids_database():
    # Retrieve the player ids of all the players for Venezuela.
    player_ids = await get_all_player_ids()

    # Dump into cleared json file
    outfile = os.path.join(BASE_DIR, "player_ids.json")

    # Saving
    if player_ids:
        await save_user_ids(outfile, player_ids)


# HOURLY PLAYER IDS
# -------------------


# -------------------
# 12H PLAYER INFO
async def save_all_players_stats(path, players_stats):
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(players_stats, ensure_ascii=False, indent=2))


async def load_all_players_stats(path):
    if not os.path.exists(path):
        logging.error(f"Error loading players_stats, file not found: {path}")
        return

    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
        return json.loads(text)


async def update_players_stats_database(player_ids):
    all_player_stats = []

    for player in player_ids:
        player_url = f"https://api2.warera.io/trpc/user.getUserLite?input=%7B%22userId%22%3A%22{player}%22%7D"
        headers = {'Content-Type': 'application/json'}

        data, resp = await api_fetch(player_url, headers)

        if resp.status == 200:
            try:
                player_data = data["result"]["data"]
                all_player_stats.append(player_data)
                logging.info(f"Fetched stats for player {player}")

            except KeyError:
                logging.error(f"Error parsing data for player {player}")

        elif resp.status == 429:
            logging.warning(f"Rate limited, waiting {RETRY_429}s")
            await asyncio.sleep(RETRY_429)

        await asyncio.sleep(DELAY)

    return all_player_stats


async def run_player_stats_funcs():
    # Load the players json
    player_ids = load_user_ids("player_ids.json")

    # Get player info array
    all_player_stats = update_players_stats_database(player_ids)

    # save
    outfile = os.path.join(BASE_DIR, "player_stats.json")
    await save_all_players_stats(outfile, all_player_stats)


@tasks.loop(time=time(hour=9, minute=0, tzinfo=timezone.utc))
async def morning_update_player_stats():
    await run_player_stats_funcs()


@tasks.loop(time=time(hour=21, minute=0, tzinfo=timezone.utc))
async def evening_update_player_stats():
    await run_player_stats_funcs()


# 12H PLAYER INFO
# -------------------


@client.event
async def on_ready():
    print(f"Conectado como {client.user} (ID: {client.user.id})")

    # Sincronizar comandos slash → muy importante
    try:
        # Global (todos los servidores, tarda más en propagarse ~1 hora máx)
        synced = await tree.sync()
        print(f"Comandos sincronizados globalmente: {len(synced)}")

        # O solo en un servidor para pruebas rápidas (inmediato):
        # synced = await tree.sync(guild=discord.Object(id=TU_SERVER_ID))
        # print(f"Comandos sincronizados en guild: {len(synced)}")
    except Exception as e:
        print(f"Error al sincronizar: {e}")

    # Player_ids
    if not update_player_ids_database.is_running():
        update_player_ids_database.start()
        print("Tarea periódica iniciada")

    # Player_stats
    if not morning_update_player_stats.is_running():
        morning_update_player_stats.start()
        print("Tarea de estadísticas iniciada player_stats")

    if not evening_update_player_stats.is_running():
        evening_update_player_stats.start()
        print("Tarea de estadísticas iniciada player_stats")


# Opcional: para tareas que usan wait_until_ready
@update_player_ids_database.before_loop
async def before_tarea():
    await client.wait_until_ready()
    print(
        "Esperando a que el cliente esté listo antes de la primera ejecución")


# ────────────────────────────────────────────────
# Arrancar el bot
# ────────────────────────────────────────────────
async def main():
    async with client:
        await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
