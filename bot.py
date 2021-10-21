import discord
import asyncio
import time
import pickle
from functools import partial
from random import shuffle


class Bot(discord.Client):
    async def on_ready(self):
        self.known_guilds = []
        self.settings = ['known_guilds', 'settings_bot', 'settings_general', 'settings_rooms', 'settings_min']
        self.settings_bot = {'default': 'bot'}
        self.settings_general = {'default': 'general'}
        self.settings_rooms = {'default': 'voice-'}
        self.settings_min = {'default': 3}
        self.bot_channel = {}
        self.tutor = {}
        self.general = {}
        self.rooms = {}
        self.started_at = {}
        self.min = {}
        self.minimum_per_room = {}

        for file in self.settings:
            try:
                with open('settings/'+ file + '.pkl', 'rb') as f:
                    setattr(self, file, pickle.load(f))
            except FileNotFoundError:
                pass

        print("------------- Initializations -------------")
        for guild in self.guilds:
            await self.initialize(guild, None, startup=True)

        self.help = (" - `!ping`: Schickt eine Benachrichtigung, wenn du eine Frage hast\n"
                     " - `!rem`: Gibt zurück wie lange der aktuelle Timer noch läuft\n"
                     " - `!help`: Gibt diese Nachricht aus")

        self.help_full = (" - `!init`: Aktualisisert die Einstellungen für den Server\n"
                          " - `!set [bot/general/rooms/min] arg`: Setzt eine Einstellung auf einen neuen Wert, lässt sich chainen\n"
                          " - `!ping`: Schickt eine Benachrichtigung, wenn jemand eine Frage hat\n"
                          " - `!room`: Teilt alle teilnehmenden Studierenden auf die Räume auf\n"
                          " - `!time arg`: Stellt einen Timer für `arg` Minuten, muss ein Integer sein und zwischen 0 und 120 liegen\n"
                          " - `!cancel`: Bricht den aktuellen Timer ab\n"
                          " - `!rem`: Gibt zurück wie lange der aktuelle Timer noch läuft\n"
                          " - `!ann`: Ruft alle in den allgemeinen Channel zurück\n"
                          " - `!help`: Gibt diese Nachricht aus")

        self.save_settings()

        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    def save_settings(self):
        for file in self.settings:
            with open('settings/'+ file + '.pkl', 'wb+') as f:
                pickle.dump(getattr(self, file), f, pickle.HIGHEST_PROTOCOL)

    async def initialize(self, guild, message, startup=False):
        new = False
        if guild.id not in self.known_guilds:
            new = True
            self.known_guilds.append(guild.id)
            if not startup:
                self.save_settings()

        bot     = self.settings_bot[guild.id]     if guild.id in self.settings_bot     else self.settings_bot['default']
        general = self.settings_general[guild.id] if guild.id in self.settings_general else self.settings_general['default']
        rooms   = self.settings_rooms[guild.id]   if guild.id in self.settings_rooms   else self.settings_rooms['default']
        min     = self.settings_min[guild.id]     if guild.id in self.settings_min     else self.settings_min['default']

        self.tutor[guild.id]       = guild.owner
        self.bot_channel[guild.id] = discord.utils.get(guild.channels, name=bot)
        bot_found = self.bot_channel[guild.id] is not None
        self.general[guild.id]     = discord.utils.get(guild.voice_channels, name=general)
        general_found = self.general[guild.id] is not None
        self.rooms[guild.id]       = []
        i = 1
        while True:
            room = discord.utils.get(guild.voice_channels, name=f'{rooms}{i}')
            if room is not None:
                self.rooms[guild.id].append(room)
                i += 1
            else:
                break
        rooms_found = len(self.rooms) > 0
        self.started_at[guild.id]  = None
        self.min[guild.id] = None
        self.minimum_per_room[guild.id] = min

        text =  f'Beep boop, ich habe folgende Einstellungen für "{guild.name}" übernommen:\n'
        text += f'Tutor*in: {self.tutor[guild.id].display_name}\n'
        text += f'Bot Channel: {self.bot_channel[guild.id] if bot_found else "*Nicht gefunden!*"}\n'
        text += f'General Voice Channel: {self.general[guild.id]}\n'
        text += f"Voice Channel: {', '.join(r.name for r in self.rooms[guild.id])}\n"
        text += f"Gruppengröße: {self.minimum_per_room[guild.id]}"
        error = False
        if not bot_found:
            text +=f"\nDu kannst den Bot Channel manuell mit `!set bot channel_name_here` festlegen!"
            error = True
        if not general_found:
            text +=f"\nDu kannst den General Voice Channel manuell mit `!set general channel_name_here` festlegen!"
            error = True
        if not rooms_found:
            text +=f"\nDu kannst die Voice Channel manuell mit `!set rooms channel_name_here` festlegen! Die Channel sollten dann die Namen `channel_name_here-i` haben, wobei i bei 1 anfängt."
            error = True
        if error:
            text +=f"\nNachdem du einen Channel gesetzt hast, musst du `!init` benutzen, um die Einstellungen anzuwenden. Alle commands müssen im Server aufgerufen werden!"

        print()
        print(text)
        print()
        if not message is None:
            await message.reply(text, mention_author=False)
        elif new or error:
            await guild.owner.send(text)

    async def on_guild_join(self, guild):
        await self.initialize(guild)

    async def on_message(self, message):
        cmd = message.content.lower().split()
        if message.author == self.user or len(cmd) == 0 or not cmd[0].startswith('!') or message.guild is None:
            return

        guild = message.guild.id

        if cmd[0].startswith('!init'):
            if message.author != self.tutor[guild]:
                await message.reply(f'Beep boop, du hast keine Berechtigung dafür!', mention_author=False)
                return
            await self.initialize(message.guild, message)

        elif cmd[0].startswith('!set'):
            if message.author != self.tutor[guild]:
                await message.reply(f'Beep boop, du hast keine Berechtigung dafür!', mention_author=False)
                return
            success = False
            i = 1
            while i < len(cmd):
                setting = cmd[i]
                if setting not in ['bot', 'general', 'rooms', 'min']:
                    await message.reply(f'Beep boop, {setting} kenne ich nicht. Benutze bitte `bot`, `general`, `rooms` oder `min`!', mention_author=False)
                    break
                if len(cmd) < i+1:
                    await message.reply(f'Beep boop, du hast keinen Channel Namen für {setting} eingegeben!', mention_author=False)
                    break
                channel = cmd[i+1]
                getattr(self, 'settings_'+setting)[guild] = channel
                if setting == 'min':
                    await message.reply(f'Beep boop, Gruppengröße auf mindestens {channel} gesetzt!', mention_author=False)
                else:
                    await message.reply(f'Beep boop, Channel Name von {setting} auf {channel} gesetzt!', mention_author=False)
                success = True
                i += 2
            if success:
                await message.reply(f'Beep boop, bitte benutze `!init` um zu Einstellungen zu übernehmen!', mention_author=False)
                self.save_settings()


        elif cmd[0].startswith('!hallo'):
            await message.reply(f'Hallo {message.author.display_name}!', mention_author=False)


        elif cmd[0].startswith('!ping'):
            try:
                category = message.author.voice.channel.category
                room = f' in {category if category is not None else message.author.voice.channel}'
            except AttributeError:
                room = ''
            await self.bot_channel[guild].send(f'{self.tutor[guild].mention}: {message.author.display_name} hat eine Frage{room}!')
            await message.reply('Beep boop, ich habe eine Benachrichtigung geschickt!', mention_author=False)


        elif cmd[0].startswith('!time'):
            if message.author != self.tutor[guild]:
                await message.reply(f'Beep boop, du kannst keine Timer stellen! Falls du wissen willst wie lange der aktuelle Timer noch läuft, benutz `!rem`', mention_author=False)
                return

            if not self.started_at[guild] == None:
                await message.reply(f'Beep boop, es läuft schon ein {self.min[guild]}-Minuten Timer!', mention_author=False)
                return

            try:
                self.min[guild] = int(cmd[1])
            except:
                await message.reply('Beep boop, ich hatte Probleme beim parsen der Zeit! Bitte benutze nur natürliche Zahlen!', mention_author=False)
                return

            if self.min[guild] < 0 or self.min[guild] > 120:
                await message.reply('Beep boop, nur Zeiten zwischen 0 und 120 Minuten sind erlaubt!', mention_author=False)
                return

            self.started_at[guild] = time.time()
            self.timer[guild] = Timer(self.min[guild]*60, partial(self.announce, message.guild))
            await message.reply(f'Beep boop, ich habe einen Timer für {self.min[guild]} Minuten gestellt!', mention_author=False)


        elif cmd[0].startswith('!rem'):
            if self.started_at[guild] == None:
                await message.reply('Beep boop, es ist kein Timer gestellt!', mention_author=False)
                return

            await message.reply(f'Beep boop, der Timer läuft noch {int((self.started_at[guild] + self.min[guild]*60 - time.time()) / 60)} Minuten!', mention_author=False)

        elif cmd[0].startswith('!cancel'):
            if message.author != self.tutor[guild]:
                await message.reply(f'Beep boop, du kannst keine Timer abbrechen!', mention_author=False)
                return

            if self.started_at[guild] == None:
                await message.reply('Beep boop, es ist kein Timer gestellt!', mention_author=False)
                return

            self.started_at[guild] = None
            self.timer[guild].cancel()
            await message.reply(f'Beep boop, ich habe den {self.min[guild]}-Minuten Timer abgebrochen!', mention_author=False)


        elif cmd[0].startswith('!ann'):
            if message.author != self.tutor[guild]:
                await message.reply(f'Beep boop, du kannst keine Benachrichtigung schicken lassen!', mention_author=False)
                return

            await self.announce(message.guild)

        elif cmd[0].startswith('!room'):
            if message.author != self.tutor[guild]:
                await message.reply(f'Beep boop, du kannst keine Leute aufteilen lassen!', mention_author=False)
                return

            shuffledMembers = self.general[guild].members
            if len(shuffledMembers) == 0:
                print('WARN: No members to assign found!')
                return
            shuffle(shuffledMembers)

            numberOfRooms = len(self.rooms[guild])
            membersPerRoom = 0
            # check how many rooms will be used (min 3 people per room)
            while membersPerRoom < self.minimum_per_room and numberOfRooms > 1:
                numberOfRooms -= 1
                membersPerRoom = int((len(shuffledMembers) - 1) / numberOfRooms)

            print(f'Assigning {len(shuffledMembers) - 1} people to {numberOfRooms} rooms')

            # add people to the rooms
            i = 0
            for member in shuffledMembers:
                if member != self.tutor[guild]:
                    await member.move_to(self.rooms[guild][i])
                    print(f'Moved {member.display_name} to room {i+1}')
                    i = (i+1) % numberOfRooms
                else:
                    print(f'Skipped {member.display_name}')

            await message.reply('Beep boop, alle Teilnehmer wurden auf die Räume aufgeteilt!', mention_author=False)
            print('Done')


        elif cmd[0].startswith('!help'):
            help = self.help if message.author != self.tutor[guild] else self.help_full
            await message.reply(f'Beep boop, hier sind alle Befehle die ich zur Zeit kann:\n{help}', mention_author=False)

        elif cmd[0].startswith('!'):
            help = self.help if message.author != self.tutor[guild] else self.help_full
            await message.reply(f'Beep boop, den Befehl kenne ich nicht, hier sind alle Befehle die ich zur Zeit kann:\n{help}', mention_author=False)


    async def announce(self, guild):
        self.started_at[guild.id] = None
        await self.bot_channel[guild.id].send('@everyone Die Zeit ist um! Kommt bitte zurück in den allgemeinen Channel!')

        for channel in guild.voice_channels:
            if len(channel.members) == 0:
                continue

            vc = await channel.connect()
            vc.play(discord.FFmpegPCMAudio(executable="D:/Programme/ffmpeg-20200831-4a11a6f-win64-static/bin/ffmpeg.exe", source="timer.mp3"))
            await asyncio.sleep(4)
            await vc.disconnect()


class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        if self._timeout > 0:
            await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.members = True
    intents.reactions = True
    activity = discord.Activity(type=discord.ActivityType.listening, name="!ping")
    client = Bot(activity=activity, intents=intents)
    try:
        with open('token', 'r') as f:
            token = f.read()
    except FileNotFoundError:
        print("Token nicht gefunden! Bitte füge eine Datei 'token' mit dem Discord Bot Token hinzu.")
    client.run(token)
