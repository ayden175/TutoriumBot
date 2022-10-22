import discord
from discord import app_commands
import time
from functools import partial
from random import shuffle
from typing import Literal

from client import Bot, Timer


intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True
activity = discord.Activity(type=discord.ActivityType.listening, name="/ping")
bot = Bot(activity=activity, intents=intents, help_command=None)

@bot.tree.command(name='init', description='Aktualisisert die Einstellungen für den Server.')
async def cmd_init(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        if interaction.user != bot.tutor[interaction.guild_id]:
            await interaction.response.send_message(f'Beep boop, du hast keine Berechtigung dafür!')
            return
        await bot.initialize(interaction.guild, interaction)
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='set', description='Setzt eine Einstellung auf einen neuen Wert.')
@app_commands.describe(
    setting='Die Einstellung, die angepasst werden soll',
    value='Der neue Wert der Einstellung',
)
async def cmd_set(interaction, setting: Literal['bot', 'general', 'rooms', 'size'], value: str):
    command = f"{interaction.user.display_name}: {interaction.command.name} {setting} {value}"
    print(command)
    try:
        if interaction.user != bot.tutor[interaction.guild_id]:
            await interaction.response.send_message(f'Beep boop, du hast keine Berechtigung dafür!')
            return

        if setting == 'size':
            getattr(bot, 'settings_'+setting)[interaction.guild_id] = int(value)
            await interaction.response.send_message(f'Beep boop, Gruppengröße auf mindestens {value} gesetzt! Bitte benutze `/init` um zu Einstellungen zu übernehmen!')
        else:
            getattr(bot, 'settings_'+setting)[interaction.guild_id] = value
            await interaction.response.send_message(f'Beep boop, Channel Name von {setting} auf {value} gesetzt! Bitte benutze `/init` um zu Einstellungen zu übernehmen!')

        bot.save_settings()
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='hallo', description='Sagt Hallo!')
async def cmd_hallo(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        await interaction.response.send_message(f'Hallo {interaction.user.display_name}!')
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='ping', description='Schickt eine Benachrichtigung, wenn jemand eine Frage hat.')
async def cmd_ping(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        try:
            category = interaction.user.voice.channel.category
            room = f' in {category if category is not None else interaction.user.voice.channel}'
        except AttributeError:
            room = ''
        await bot.bot_channel[interaction.guild_id].send(f'{bot.tutor[interaction.guild_id].mention}: {interaction.user.display_name} hat eine Frage{room}!')
        await interaction.response.send_message('Beep boop, ich habe eine Benachrichtigung geschickt!')
    except Exception:
        await bot.error(interaction, command)


@bot.tree.command(name='timer', description='Stellt einen Timer für die angegebenen Minuten.')
@app_commands.describe(
    minutes='Die Anzahl der Minuten. Muss zwischen 1 und 180 liegen.'
)
async def cmd_time(interaction, minutes: app_commands.Range[int, 1, 180]):
    command = f"{interaction.user.display_name}: {interaction.command.name} {minutes}"
    print(command)
    try:
        if interaction.user != bot.tutor[interaction.guild_id]:
            await interaction.response.send_message(f'Beep boop, du kannst keine Timer stellen! Falls du wissen willst wie lange der aktuelle Timer noch läuft, benutz `/remaining`!')
            return

        if not bot.started_at[interaction.guild_id] == None:
            await interaction.response.send_message(f'Beep boop, es läuft schon ein {bot.min[interaction.guild_id]}-Minuten Timer!')
            return

        try:
            bot.min[interaction.guild_id] = minutes
        except:
            await interaction.response.send_message('Beep boop, ich hatte Probleme beim parsen der Zeit! Bitte benutze nur natürliche Zahlen!')
            return

        if bot.min[interaction.guild_id] < 1 or bot.min[interaction.guild_id] > 180:
            await interaction.response.send_message('Beep boop, nur Zeiten zwischen 0 und 180 Minuten sind erlaubt!')
            return

        bot.started_at[interaction.guild_id] = time.time()
        bot.timer[interaction.guild_id] = Timer(bot.min[interaction.guild_id]*60, partial(bot.announce, interaction.guild))
        await interaction.response.send_message(f'Beep boop, ich habe einen Timer für {bot.min[interaction.guild_id]} Minuten gestellt!')
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='remaining', description='Gibt zurück wie lange der aktuelle Timer noch läuft.')
async def cmd_rem(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        if bot.started_at[interaction.guild_id] == None:
            await interaction.response.send_message('Beep boop, es ist kein Timer gestellt!')
            return

        remaining_min = int((bot.started_at[interaction.guild_id] + bot.min[interaction.guild_id]*60 - time.time()) / 60)
        if remaining_min == 0:
            time_text = "weniger als eine Minute"
        elif remaining_min == 1:
            time_text = "eine Minute"
        else:
            time_text = f"{remaining_min} Minuten"
        await interaction.response.send_message(f'Beep boop, der Timer läuft noch {time_text}!')
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='cancel', description='Bricht den aktuellen Timer ab.')
async def cmd_cancel(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        if interaction.user != bot.tutor[interaction.guild_id]:
            await interaction.response.send_message(f'Beep boop, du kannst keine Timer abbrechen!')
            return

        if bot.started_at[interaction.guild_id] == None:
            await interaction.response.send_message('Beep boop, es ist kein Timer gestellt!')
            return

        bot.started_at[interaction.guild_id] = None
        bot.timer[interaction.guild_id].cancel()
        await interaction.response.send_message(f'Beep boop, ich habe den {bot.min[interaction.guild_id]}-Minuten Timer abgebrochen!')
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='announce', description='Ruft alle in den allgemeinen Channel zurück.')
async def cmd_announce(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        if interaction.user != bot.tutor[interaction.guild_id]:
            await interaction.response.send_message(f'Beep boop, du kannst keine Benachrichtigung schicken lassen!')
            return
        await interaction.response.send_message(f'Beep boop, ich benachrichte alle!')
        await bot.announce(interaction.guild)
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='rooms', description='Teilt alle teilnehmenden Studierenden auf die Räume auf.')
async def cmd_rooms(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        if interaction.user != bot.tutor[interaction.guild_id]:
            await interaction.response.send_message(f'Beep boop, du kannst keine Leute aufteilen lassen!')
            return

        shuffledMembers = bot.general[interaction.guild_id].members
        if len(shuffledMembers) <= 1:
            await interaction.response.send_message(f'Beep boop, ich habe niemanden zum Aufteilen gefunden!')
            print('WARN: No members to assign found!')
            return
        shuffle(shuffledMembers)

        numberOfRooms = len(bot.rooms[interaction.guild_id])
        membersPerRoom = 0
        # check how many rooms will be used
        while membersPerRoom < bot.group_size[interaction.guild_id] and numberOfRooms > 1:
            numberOfRooms -= 1
            membersPerRoom = int((len(shuffledMembers) - 1) / numberOfRooms)

        print(f'Assigning {len(shuffledMembers) - 1} people to {numberOfRooms} rooms')

        # add people to the rooms
        i = 0
        for member in shuffledMembers:
            if member != bot.tutor[interaction.guild_id]:
                try:
                    await member.move_to(bot.rooms[interaction.guild_id][i])
                    print(f'Moved {member.display_name} to room {i+1}')
                    i = (i+1) % numberOfRooms
                except discord.errors.HTTPException:
                    print(f'Error while assigning {member.display_name} to room {i+1}, skipping')
            else:
                print(f'Skipped {member.display_name}')

        await interaction.response.send_message('Beep boop, alle Teilnehmer wurden auf die Räume aufgeteilt!')
        print('Done')
    except Exception:
        await bot.error(interaction, command)

@bot.tree.command(name='help', description='Zeigt eine Liste aller Befehle an.')
async def cmd_help(interaction):
    command = f"{interaction.user.display_name}: {interaction.command.name}"
    print(command)
    try:
        help = bot.help if interaction.user != bot.tutor[interaction.guild_id] else bot.help_full
        await interaction.response.send_message(f'Beep boop, hier sind alle Befehle die ich zur Zeit kann:\n{help}')
    except Exception:
        await bot.error(interaction, command)

try:
    with open('token', 'r') as f:
        token = f.read()
except FileNotFoundError:
    print("Token nicht gefunden! Bitte füge eine Datei 'token' mit dem Discord Bot Token hinzu.")
bot.run(token)
