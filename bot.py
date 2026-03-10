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
from discord.ui import View, Button, Select
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
import urllib.parse
import asyncio
import json
import random
import logging
import matplotlib.pyplot as plt
from collections import Counter
from flask import Flask
from threading import Thread

from datetime import datetime, timedelta, timezone, time

# DIR
BASE_DIR = ""
PLAYER_STATS_FILE = os.path.join(BASE_DIR,"player_stats.json")

try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()

# SERVERS
WARERAVE = discord.Object(id=1370814923122413588)
TEST_SERVER = discord.Object(id=1369374657043501196)

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

# Extra vars
is_updating_stats = False

# UPTIME
app = Flask(__name__)

@app.route('/')
def home():
    return "¡El bot está vivo! 🚀"

@app.route('/ping')  # Opcional, pero algunos lo usan para UptimeRobot
def ping():
    return "Pong!"

def run_flask():
    # Usa el puerto que Render asigna (obligatorio)
    port = int(os.environ.get("PORT", 8080))  # Render pasa PORT por env
    app.run(host='0.0.0.0', port=port)

# Inicia el servidor Flask en un hilo separado (no bloquea el bot)
Thread(target=run_flask, daemon=True).start()


# ------------------------------------------
# UI Components
class GuidesView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Guías", style=discord.ButtonStyle.primary, custom_id="guides_btn")
    async def guides_button(self, interaction: discord.Interaction, button: Button):
        view = GuideDropdownView()
        embed = discord.Embed(
            title="📚 Panel de Guías",
            description="Selecciona una guía del menú desplegable.",
            color=0x00ff88
        )
        await interaction.response.edit_message(embed=embed, view=view, delete_after=600)

    @discord.ui.button(label="Builds", style=discord.ButtonStyle.green, custom_id="builds_btn")
    async def builds_button(self, interaction: discord.Interaction, button: Button):
        view = BuildsView()
        embed = discord.Embed(
            title="⚔️ Builds Recomendadas",
            description=(
                "Elige el tipo de build según la importancia de la batalla y tu nivel aproximado.\n\n"
                "Todas las builds están pensadas para optimizar **daño / costo**."
            ),
            color=0x00aaff
        )
        await interaction.response.edit_message(embed=embed, view=view, delete_after=600)

class BuildsView(View):
    def __init__(self):
        super().__init__(timeout=None)

    # BASICO / NOVATO
    @discord.ui.button(label="NOVATO 1 - Batallas", style=discord.ButtonStyle.green, row=0)
    async def newbie1_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_novato1_embed()
        await interaction.response.edit_message(embed=embed, view=self, delete_after=600)

    @discord.ui.button(label="NOVATO 2 - Batallas", style=discord.ButtonStyle.blurple, row=0)
    async def newbie2_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_novato2_embed()
        await interaction.response.edit_message(embed=embed, view=self, delete_after=600)

    # AVANZADO
    @discord.ui.button(label="AVANZADO 1 - Batallas", style=discord.ButtonStyle.green, row=1)
    async def nre1_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_avanzado1_embed()
        await interaction.response.edit_message(embed=embed, view=self, delete_after=600)

    @discord.ui.button(label="AVANZADO 2 - Batallas", style=discord.ButtonStyle.blurple, row=1)
    async def nre2_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_avanzado2_embed()
        await interaction.response.edit_message(embed=embed, view=self, delete_after=600)

    @discord.ui.button(label="AVANZADO 3 - Batallas críticas", style=discord.ButtonStyle.red, row=1)
    async def nre3_button(self, interaction: discord.Interaction, button: Button):
        embed = self.build_avanzado3_embed()
        await interaction.response.edit_message(embed=embed, view=self, delete_after=600)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.gray, row=2)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        view = GuidesView()
        embed = discord.Embed(
            title="📖 Centro de Ayuda Warera",
            description="Bienvenido al centro de ayuda.\nSelecciona una categoría para comenzar.",
            color=0x4B0082
        )
        await interaction.response.edit_message(embed=embed, view=view, delete_after=600)

    def build_novato1_embed(self):
        return discord.Embed(
            title="🎯 NOVATO 1 – RIFLES (batallas poco importantes)",
            description=(
                "**Arma:** Rifle azul\n"
                "→ ~80 DMG  |  14%+ velocidad\n"
                "→ Balas **verdes**\n\n"
                "**Equipo:** ~14% (azul)\n\n"
                "**Alternativa si no tienes sniper morado:**\n"
                "Pistola verde → ~55 DMG  |  10%+\n\n"
                "→ Ideal para buen daño siendo novato / guerras medias"
            ),
            color=0xaaaaaa
        )
    
    def build_novato2_embed(self):
        return discord.Embed(
            title="🎯 NOVATO 2 – RIFLES (batallas)",
            description=(
                "**Arma:** Rifle azul\n"
                "→ ~80 DMG  |  14%+ velocidad\n"
                "→ Balas **verdes**\n\n"
                "**Equipo:** ~8% (verde)\n\n"
                "**Alternativa si no tienes rifle azul:**\n"
                "Pistola verde → ~55 DMG  |  10%+\n\n"
                "→ Ideal para farmear / guerras secundarias / bajo riesgo"
            ),
            color=0xaaaaaa
        )

    def build_avanzado1_embed(self):
        return discord.Embed(
            title="🎯 AVANZADO 1 – Snipers (batallas poco importantes)",
            description=(
                "**Arma:** Sniper morado\n"
                "→ ~105 DMG  |  17%+ velocidad\n"
                "→ Balas **verdes**\n\n"
                "**Equipo:** ~14% (azul)\n\n"
                "**Alternativa si no tienes sniper morado:**\n"
                "Rifle azul → ~85 DMG  |  14%+\n\n"
                "→ Ideal para farmear / guerras secundarias / bajo riesgo"
            ),
            color=0xaaaaaa
        )

    def build_avanzado2_embed(self):
        return discord.Embed(
            title="🛡️ AVANZADO 2 – Tanque (batallas importantes)",
            description=(
                "**Arma:** Tanque\n"
                "→ ~138 DMG  |  24%+ velocidad\n"
                "→ Balas **azules**\n\n"
                "**Equipo:** 18–20% (morado)\n"
                "**Casco:** 25–30% (azul)\n\n"
                "→ Recomendado para guerras medianas / defensas clave"
            ),
            color=0x2f7df4
        )

    def build_avanzado3_embed(self):
        return discord.Embed(
            title="✨ AVANZADO 3 – Full Dorado (batallas muy importantes)",
            description=(
                "**Arma:** Tanque\n"
                "→ ~150 DMG  |  27%+ velocidad\n"
                "→ Balas **azules**\n\n"
                "**Equipo:** 24–27% (dorado)\n"
                "**Casco:** 35–40% (morado)\n\n"
                "→ Solo para guerras decisivas, torneos, top clans, revenge caras, etc."
            ),
            color=0xffd700
        )

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
                    "**Empresa 2:** Cemento - Automatizar a nivel 4 + 1 Mejora de almacén.\n"
                    "**Nota:** Deben conseguir un trabajador al que puedan pagarle el sueldo mínimo y ustedes trabajarle por el sueldo mínimo.\n"
                    "**Nota2:** De no conseguir trabajador, no contratar ningún trabajador y trabajarle a otra persona por el sueldo promedio (0.139~).\n"
                    "**Nota3:** Sus puntos de emprendimiento deben ser usados en piedra mientras su trabajador genera puntos de producción en cemento.\n\n"
                    "**Empresa 3:** Piedra - Automatizar a nivel 4.\n"
                    "**Empresa 4:** Cemento - Automatizar a nivel 4.\n\n"
                    "**Empresa 5:** Piedra - Automatizar hasta nivel 4.\n"
                    "**Empresa 6:** Acero - Automatizar hasta nivel 4.\n\n"
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
# Ruleta ataque
# Definimos una vista simple para el botón
class BotonRegistro(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []

    @discord.ui.button(label="¡Entrar al ataque!", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            self.participantes.append(interaction.user)
            await interaction.response.send_message(f"⚔️ {interaction.user.display_name}, estás en la lista.", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás registrado.", ephemeral=True)

@tree.command(name="ruleta_ataque", description="Crea una ruleta para elegir a un jugador aleatorio para atacar.")
@app_commands.checks.has_any_role(1432429586880266321, 1398107765250982026)
async def ruletaAtaque(interaction: discord.Interaction): # CAMBIADO: ctx -> interaction
    tiempo = 5
    
    embed = discord.Embed(
        title="⚔️ ¡RULETA DE ATAQUE INICIADA! ⚔️",
        description=f"Hagan clic abajo para registrarse.\nTermina en **{tiempo} segundos**.",
        color=discord.Color.red()
    )
    
    view = BotonRegistro(timeout=tiempo)
    # CAMBIADO: ctx.send -> interaction.response.send_message
    await interaction.response.send_message(embed=embed, view=view)

    await asyncio.sleep(tiempo)

    for child in view.children:
        child.disabled = True

    if view.participantes:
        elegido = random.choice(view.participantes)
        
        embed_final = discord.Embed(
            title="🎯 ¡BLANCO FIJADO! 🎯",
            description=f"El objetivo del ataque es: {elegido.mention}",
            color=discord.Color.dark_red()
        )
        embed_final.set_image(url=elegido.display_avatar.url)
        embed_final.set_footer(text=f"Participantes totales: {len(view.participantes)}")
        
        # CAMBIADO: mensaje.edit -> interaction.edit_original_response
        await interaction.edit_original_response(embed=embed_final, view=view)
        # CAMBIADO: ctx.send -> interaction.followup.send
        await interaction.followup.send(f"🔥 ¡Atención {elegido.mention}, has sido seleccionado! Ganaste contra {len(view.participantes)}")
    else:
        # CAMBIADO: mensaje.edit -> interaction.edit_original_response
        await interaction.edit_original_response(content="Nadie tuvo el valor de unirse al ataque. 💨", embed=None, view=view)

@ruletaAtaque.error
async def ruletaAtaque_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingAnyRole):
        await interaction.response.send_message(
            "🚫 **Acceso denegado:** No tienes los permisos de alto mando para iniciar una ruleta de ataque.", 
            ephemeral=True
        )
    else:
        logging.error(f"Error inesperado en ruletaAtaque: {error}")
        # Solo respondemos si no se ha respondido ya a la interacción
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocurrió un error inesperado al procesar el comando.", ephemeral=True)

# --- RULETA EQUIPO ---
class BotonRegistroEquipo(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.participantes = []

    @discord.ui.button(label="¡Unirse al Equipo!", style=discord.ButtonStyle.green, emoji="🛡️")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participantes:
            self.participantes.append(interaction.user)
            await interaction.response.send_message(f"✅ {interaction.user.display_name}, te has unido a la formación.", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás en la lista de espera.", ephemeral=True)

@tree.command(name="ruleta_equipo", description="Elige a un grupo de personas aleatorias para una misión.")
@app_commands.describe(cantidad="Número de personas que quieres seleccionar para el equipo")
@app_commands.checks.has_any_role(1432429586880266321, 1398107765250982026)
async def ruleta_equipo(interaction: discord.Interaction, cantidad: int):
    if cantidad < 1:
        await interaction.response.send_message("La cantidad debe ser al menos 1.", ephemeral=True)
        return

    tiempo = 5
    embed = discord.Embed(
        title="🛡️ ¡RECLUTAMIENTO DE EQUIPO! 🛡️",
        description=f"Se buscan **{cantidad}** valientes.\n¡Hagan clic abajo para registrarse! (**{tiempo}s**)",
        color=discord.Color.blue()
    )
    
    view = BotonRegistroEquipo(timeout=tiempo)
    await interaction.response.send_message(embed=embed, view=view)

    await asyncio.sleep(tiempo)

    for child in view.children:
        child.disabled = True

    participantes = view.participantes
    num_participantes = len(participantes)

    if num_participantes == 0:
        await interaction.edit_original_response(content="Nadie se registró para el equipo. La misión se cancela. ❌", embed=None, view=view)
        return

    if num_participantes == 1:
        seleccionados = participantes
        mensaje_extra = "\n\n⚠️ *Nota: Solo una persona tuvo el valor de presentarse.*"
    elif num_participantes <= cantidad:
        seleccionados = participantes
        mensaje_extra = f"\n\n⚠️ *Nota: Se buscaban {cantidad} personas, pero solo se registraron {num_participantes}.*"
    else:
        seleccionados = random.sample(participantes, cantidad)
        mensaje_extra = ""

    menciones = ", ".join([user.mention for user in seleccionados])

    embed_final = discord.Embed(
        title="⚔️ ¡EQUIPO FORMADO! ⚔️",
        description=f"Los seleccionados para el ataque son:\n\n{menciones}{mensaje_extra}\n\n📊 Ganaron contra {num_participantes} participantes.",
        color=discord.Color.gold()
    )
    embed_final.set_footer(text=f"Total de voluntarios: {num_participantes}")

    await interaction.edit_original_response(embed=embed_final, view=view)
    # Importante usar followup para que las menciones notifiquen
    await interaction.followup.send(f"🔥 ¡Equipo desplegado! {menciones}, prepárense.")

# ERROR HANDLING
@ruleta_equipo.error
async def ruleta_equipo_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingAnyRole):
        await interaction.response.send_message(
            "🚫 **Acceso denegado:** No puedes reclutar equipos. Contacta con un administrador.", 
            ephemeral=True
        )
    elif isinstance(error, app_commands.errors.CommandInvokeError):
        await interaction.response.send_message("❌ Error al invocar el comando. Revisa los parámetros.", ephemeral=True)
    else:
        logging.error(f"Error inesperado en ruleta_equipo: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Algo salió mal al formar el equipo.", ephemeral=True)

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
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


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

@tree.command(name="muinfo", description="Obtén información de una Unidad Militar.")
@app_commands.describe(mu_name="Nombre de la Unidad Militar")
async def mu_info(interaction: discord.Interaction, mu_name: str):
    await interaction.response.defer()

    # ------------------------------------
    # 1. Getting MU ID by name
    # ------------------------------------
    # We encode the JSON input for the URL
    search_query = urllib.parse.quote(f'{{"searchText":"{mu_name}"}}')
    search_url = f"https://api2.warera.io/trpc/search.searchAnything?input={search_query}"
    headers = {'Content-Type': 'application/json'}

    data, resp = await api_fetch(search_url, headers)
    
    if data is None:
        await interaction.followup.send(f"❌ Error de API: {resp.status}")
        return

    try:
        mu_ids = data["result"]["data"].get("muIds", [])
        if not mu_ids:
            await interaction.followup.send(f"❌ No se encontró ninguna MU con el nombre: {mu_name}")
            return
        mu_id = mu_ids[0]
    except (KeyError, TypeError, IndexError):
        await interaction.followup.send("❌ Error al procesar la búsqueda de la MU.")
        return

    # ------------------------------------
    # 2. Getting MU Details
    # ------------------------------------
    detail_query = urllib.parse.quote(f'{{"muId":"{mu_id}"}}')
    detail_url = f"https://api2.warera.io/trpc/mu.getById?input={detail_query}"

    data, resp = await api_fetch(detail_url, headers)
    if data is None:
        await interaction.followup.send("❌ No se pudo obtener los detalles de la Unidad Militar.")
        return

    try:
        mu = data["result"]["data"]
    except KeyError:
        await interaction.followup.send("❌ Respuesta del servidor malformada.")
        return

    # ------------------------------------
    # 3. Making the Embed
    # ------------------------------------
    embed = discord.Embed(
        title=f"🎖️ {mu.get('name', 'Military Unit')} | Warera",
        description=f"Unidad Militar en Warera",
        color=0xFFD700 # Gold
    )
    
    if mu.get('avatarUrl'):
        embed.set_thumbnail(url=mu.get('avatarUrl'))

    # Basic Stats
    members_count = len(mu.get('members', []))
    created_at = mu.get('createdAt', 'N/A').split('T')[0]
    
    embed.add_field(name="🆔 MU ID", value=f"`{mu_id}`", inline=False)
    embed.add_field(name="👥 Miembros", value=str(members_count), inline=True)
    embed.add_field(name="📅 Fundada el", value=created_at, inline=True)
    embed.add_field(name="🏠 Dormitorios", value=f"Nivel {mu.get('activeUpgradeLevels', {}).get('dormitories', 0)}", inline=True)

    # Rankings & Damage
    rankings = mu.get("rankings", {})
    
    # Weekly Damage
    weekly = rankings.get("muWeeklyDamages", {})
    embed.add_field(
        name="⚔️ Daño Semanal", 
        value=f"**{weekly.get('value', 0):,}**\nRank: #{weekly.get('rank', 'N/A')} ({weekly.get('tier', 'none')})", 
        inline=True
    )

    # Total Damage
    total_dmg = rankings.get("muDamages", {})
    embed.add_field(
        name="💥 Daño Total", 
        value=f"**{total_dmg.get('value', 0):,}**\nRank: #{total_dmg.get('rank', 'N/A')}", 
        inline=True
    )

    # Bounty/Wealth
    wealth = rankings.get("muWealth", {})
    embed.add_field(
        name="💰 Riqueza", 
        value=f"**{wealth.get('value', 0):.2f}**\nRank: #{wealth.get('rank', 'N/A')}", 
        inline=True
    )

    # Leadership
    roles = mu.get("roles", {})
    commanders = len(roles.get("commanders", []))
    managers = len(roles.get("managers", []))
    embed.add_field(name="👑 Liderazgo", value=f"Comandantes: {commanders} | Managers: {managers}", inline=False)

    embed.set_footer(text="Warera Military Intelligence", icon_url="https://warera.io/favicon.ico")

    await interaction.followup.send(embed=embed)

@tree.command(name="niveles", description="Obten una tabla con los niveles y el tiempo que toma llegar a ellos")
async def niveles(interaction: discord.Interaction):
    # 1. El defer avisa a Discord que vas a tardar (opcional si es instantáneo)
    await interaction.response.defer(ephemeral=True) 
    logging.info("Printing niveles embed")

    try:
        embed = discord.Embed(
            title="🏢 Lista de niveles",
            description=(
                "Esta tabla de niveles representa el tiempo que tomaría alcanzar el nivel "
                "si completas absolutamente todas las misiones diarias y semanales.\n\n"
                "╭─── 📊 **PROGRESIÓN INICIAL**\n"
                "│ 🔹 **Lvl 01-08** ➜ 1 día\n"
                "│ 🔹 **Lvl 09-12** ➜ 2 a 8 días\n"
                "│ 🔹 **Lvl 13-16** ➜ 10 a 21 días\n"
                "│ 🔹 **Lvl 17-20** ➜ 25 a 40 días\n"
                "╰─────────────────────────\n\n"
                "╭─── 📈 **NIVELES INTERMEDIOS**\n"
                "│ 🔸 **Lvl 21:** 45-46 días\n"
                "│ 🔸 **Lvl 22:** 51-52 días\n"
                "│ 🔸 **Lvl 23:** 57-58 días\n"
                "│ 🔸 **Lvl 24:** 64-65 días\n"
                "│ 🔸 **Lvl 25:** 71-72 días\n"
                "│ 🔸 **Lvl 26:** 78-79 días\n"
                "│ 🔸 **Lvl 27:** 85-86 días\n"
                "│ 🔸 **Lvl 28:** 92-93 días\n"
                "│ 🔸 **Lvl 29:** 99-100 días\n"
                "│ 🔸 **Lvl 30:** 106-107 días\n"
                "╰─────────────────────────\n\n"
                "╭─── 🏆 **NIVELES DE ÉLITE**\n"
                "│ 👑 **Lvl 31:** 115-116 días\n"
                "│ 👑 **Lvl 32:** 124 días\n"
                "│ 👑 **Lvl 33:** 132-133 días\n"
                "│ 👑 **Lvl 34:** 141-142 días\n"
                "│ 👑 **Lvl 35:** 150-151 días\n"
                "│ 👑 **Lvl 36:** 159 días\n"
                "│ 👑 **Lvl 37:** 167-168 días\n"
                "│ 👑 **Lvl 38:** 176-177 días\n"
                "│ 👑 **Lvl 39:** 185-186 días\n"
                "│ 👑 **Lvl 40:** 193-194 días\n"
                "╰─────────────────────────"
            ),
            color=0x00ff00
        )
        # 2. USA FOLLOWUP si usaste DEFER arriba
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Error niveles embed: {e}")


@tree.command(
    name="active_players_2d",
    description="Obten una grafica con los jugadores activos. 2 Dias")
async def active_players_char_2days(interaction: discord.Interaction):
    await interaction.response.defer()
    logging.info("Making chart")

    if is_updating_stats:
        await interaction.followup.send(
            "⏳ La base de datos se está actualizando en este momento. "
            "Por favor, intenta generar la gráfica en unos instantes.", 
            ephemeral=True
        )
        return

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
        
        if len(players) < 1:
            print("No player data was available in player_stats.json, running data base update.")
            await run_player_stats_funcs()

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
# DATA BASE
def create_progress_bar(current, total, bar_length=20):
    fraction = current / total
    arrow = int(fraction * bar_length - 1) * "█" + "█"
    padding = int(bar_length - len(arrow)) * "░"
    ending = "✅" if current == total else "⏳"
    return f"`|{arrow}{padding}|` {int(fraction * 100)}% {ending}"

async def update_players_stats_database(player_ids, interaction: discord.Interaction = None):
    global is_updating_stats
    is_updating_stats = True
    all_players_data = []
    total = len(player_ids)
    
    # Creamos un mensaje inicial de estado
    status_msg = None
    if interaction:
        status_msg = await interaction.followup.send(
            content=f"🚀 **Iniciando actualización de base de datos...**\n{create_progress_bar(0, total)}",
            wait=True # Necesario para poder editarlo después
        )

    try:
        for index, p_id in enumerate(player_ids, start=1):
            # --- Aquí iría tu lógica actual de Fetch (con su respectivo await) ---
            # data = await fetch_player_data(p_id) 
            # all_players_data.append(data)
            
            # Simulamos el tiempo de espera para no saturar la API
            await asyncio.sleep(0.5) 
            # -------------------------------------------------------------------

            # Actualizamos el mensaje de Discord cada 5 jugadores o al terminar
            if status_msg and (index % 5 == 0 or index == total):
                progress_txt = (
                    f"🔄 **Actualizando estadísticas del servidor...**\n"
                    f"👤 Jugador: `{index}` de `{total}`\n"
                    f"{create_progress_bar(index, total)}"
                )
                try:
                    await status_msg.edit(content=progress_txt)
                except Exception as e:
                    logging.error(f"No se pudo editar el mensaje de progreso: {e}")

        # Guardar el archivo JSON final
        if all_players_data:
            async with aiofiles.open(PLAYER_STATS_FILE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(all_players_data, ensure_ascii=False, indent=2))
        
        if status_msg:
            await status_msg.edit(content=f"✅ **Base de datos actualizada.** Se procesaron `{total}` jugadores.")

    finally:
        is_updating_stats = False

@tree.command(name="update_player_db", description="Actualiza la DB con progreso en tiempo real")
@app_commands.checks.has_any_role(1432429586880266321, 1398107765250982026)
async def update_player_db(interaction: discord.Interaction):
    if is_updating_stats:
        return await interaction.response.send_message("⚠️ Ya hay una actualización en curso.", ephemeral=True)

    # Defer público (no ephemeral) para que todos vean el progreso
    await interaction.response.defer(ephemeral=False)
    
    try:
        player_ids = await load_user_ids("player_ids.json")
        if not player_ids:
            return await interaction.followup.send("❌ No se encontraron IDs para procesar.")

        # Pasamos la interaction para que la función pueda editar el mensaje
        await update_players_stats_database(player_ids, interaction)
        
    except Exception as e:
        logging.error(f"Error en update_player_db: {e}")
        await interaction.followup.send(f"❌ Error crítico: {e}")

# Error handler
@update_player_db.error
async def update_player_db_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingAnyRole):
        await interaction.response.send_message("⛔ No tienes los roles necesarios para ejecutar este comando.", ephemeral=True)

# -------------------
# 12H PLAYER INFO
async def save_all_players_stats(path, players_stats):
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(players_stats, ensure_ascii=False, indent=2))

async def save_player_data(path, player_data):
    """Append individual player data to JSON file"""
    data = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    data.append(player_data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def load_all_players_stats(path):
    if not os.path.exists(path):
        logging.error(f"Error loading players_stats, file not found: {path}")
        return

    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
        return json.loads(text)


async def append_player_data(player_data):
    """Append de forma async y segura"""
    if player_data is None:
        return

    data = []
    if os.path.exists(PLAYER_STATS_FILE):
        async with aiofiles.open(PLAYER_STATS_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            if content.strip():  # evita error si vacío
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON corrupto en {PLAYER_STATS_FILE}: {e}. Reiniciando.")
                    data = []

    data.append(player_data)

    async with aiofiles.open(PLAYER_STATS_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))

async def update_players_stats_database(player_ids):
    headers = {'Content-Type': 'application/json'}
    all_players_data = [] # 1. Guardamos los datos en memoria en lugar del archivo

    for player in player_ids:
        # 2. Codificamos el input exactamente igual que en el script de 'requests'
        payload = json.dumps({"userId": player})
        encoded_input = urllib.parse.quote(payload)
        player_url = f"https://api2.warera.io/trpc/user.getUserLite?input={encoded_input}"
        
        for attempt in range(5):  # max retries por player
            data, resp = await api_fetch(player_url, headers)
            
            if resp.status == 200 and data:
                try:
                    # Usamos .get() por seguridad como en tu script original
                    player_data = data.get("result", {}).get("data")
                    if player_data:
                        logging.info(f"OK → {player}")
                        all_players_data.append(player_data) # Añadimos a la lista
                except Exception as e:
                    logging.error(f"Parse error {player}: {e}")
                break # Salimos del retry loop porque la petición fue exitosa (o falló el parseo irremediablemente)
                
            elif resp.status == 429:
                logging.warning(f"429 en {player}, espera {RETRY_429}s")
                await asyncio.sleep(RETRY_429)
            else:
                logging.error(f"HTTP {resp.status} en {player}")
                break
        else:
            logging.error(f"Falló tras retries: {player}")

        await asyncio.sleep(DELAY)

    # 3. Escribimos TODO el JSON de golpe de forma segura solo si obtuvimos datos
    if all_players_data:
        async with aiofiles.open(PLAYER_STATS_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(all_players_data, ensure_ascii=False, indent=2))
        logging.info(f"Se actualizaron {len(all_players_data)} jugadores en la base de datos.")
    else:
        logging.warning("No se obtuvieron datos de ningún jugador. El archivo original no se ha modificado.")

# En tu función principal / comando del bot:
async def run_player_stats_funcs():
    player_ids = await load_user_ids("player_ids.json")  # tu función existente
    if not player_ids:
        logging.error("No player_ids")
        return

    await update_players_stats_database(player_ids)
    logging.info("Stats actualizadas")


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

    try:
        # USA 'tree' directamente, no 'client.tree'
        # 1. Copiamos los comandos al servidor de pruebas para que sean INSTANTÁNEOS
        tree.copy_global_to(guild=WARERAVE)
        tree.copy_global_to(guild=TEST_SERVER)
        
        # 2. Sincronizamos esos servidores específicos
        await tree.sync(guild=WARERAVE)
        await tree.sync(guild=TEST_SERVER)
        
        print(f"✅ Comandos sincronizados en servidores de prueba.")
        
    except Exception as e:
        print(f"❌ Error al sincronizar: {e}")

    # --- Tus tareas periódicas ---
    if not update_player_ids_database.is_running():
        update_player_ids_database.start()
        print("Tarea periódica iniciada")

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
