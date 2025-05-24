import discord
from discord import app_commands
import sys
import os

# Agregar el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DISCORD_TOKEN, intents
from commands.owner_commands import setup as setup_owner_commands
from commands.user_commands import setup as setup_user_commands
from commands.general_commands import setup as setup_general_commands
from commands.category_commands import setup as setup_category_commands
from utils import setup_error_handlers
from chatgpt_chat import chat_manager

# Inicializar cliente y árbol de comandos
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Configurar los comandos y manejadores de errores
async def setup():
    setup_owner_commands(tree, client)
    setup_user_commands(tree, client)
    setup_general_commands(tree, client)
    setup_category_commands(tree, client)
    await setup_error_handlers(tree)

# La configuración se ejecutará en la función main

@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")
    activity = discord.Activity(type=discord.ActivityType.playing, name="ia")
    await client.change_presence(activity=activity)
    try:
        synced = await tree.sync()
        print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(e)

# Diccionario para almacenar el último mensaje procesado por usuario
last_processed_messages = {}

@client.event
async def on_message(message):
    # Ignorar mensajes del propio bot
    if message.author == client.user:
        return

    # Obtener el ID del usuario y el contenido del mensaje
    user_id = str(message.author.id)
    content = message.content.lower()

    # Palabras clave para detectar
    keywords = {
        'ayuda': ['ayuda', 'help', 'comandos', 'qué haces', 'que haces'],
        'compra': ['comprar', 'adquirir', 'precio', 'costo', 'cuánto', 'cuanto', 'ticket'],
        'admin': ['admin', 'administrador', 'moderador', 'staff'],
        'productos': ['productos', 'catálogo', 'catalogo', 'qué vendes', 'que vendes']
    }

    # Verificar si el mensaje contiene palabras clave
    for category, words in keywords.items():
        if any(word in content for word in words):
            try:
                response = await chat_manager.get_response(user_id, content)
                await message.reply(response)
                return
            except Exception as e:
                print(f'Error al procesar mensaje con palabra clave: {str(e)}')
                await message.reply(
                    'Lo siento, ha ocurrido un error al procesar tu mensaje. '
                    'Por favor, inténtalo de nuevo más tarde.'
                )
                return

    # Si no hay palabras clave, verificar si el bot fue mencionado
    if client.user.mentioned_in(message):
        content = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        # Verificar si es un mensaje vacío
        if not content:
            await message.reply('¡Hola! ¿En qué puedo ayudarte?')
            return
        
        # Verificar si es un mensaje duplicado
        if user_id in last_processed_messages:
            last_message, last_time = last_processed_messages[user_id]
            if content == last_message and (message.created_at - last_time).total_seconds() < 5:
                # Ignorar mensajes duplicados enviados en menos de 5 segundos
                return
        
        # Actualizar el último mensaje procesado
        last_processed_messages[user_id] = (content, message.created_at)

        # Mostrar indicador de escritura
        async with message.channel.typing():
            try:
                # Obtener respuesta del ChatManager
                response = await chat_manager.get_response(user_id, content)
                
                # Enviar la respuesta
                await message.reply(response)
            except Exception as e:
                print(f'Error al procesar mensaje: {str(e)}')
                await message.reply(
                    'Lo siento, ha ocurrido un error al procesar tu mensaje. '
                    'Por favor, inténtalo de nuevo más tarde.'
                )
# Verificar que el token no esté vacío
if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN está vacío. Por favor, coloca tu token en la variable DISCORD_TOKEN.")
    exit(1)

async def main():
    await setup()
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())