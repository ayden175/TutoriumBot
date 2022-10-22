import discord
from discord import app_commands
import asyncio
import pickle
import traceback
import platform

class Bot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        self.admin = discord.utils.get(self.get_all_members(), name='Ayden', discriminator='7318')
        self.known_guilds = []
        self.sent_update = []
        self.settings = ['known_guilds', 'settings_bot', 'settings_general', 'settings_rooms', 'settings_size', 'sent_update']
        self.settings_bot = {'default': 'bot'}
        self.settings_general = {'default': 'general'}
        self.settings_rooms = {'default': 'voice-'}
        self.settings_size = {'default': 3}
        self.bot_channel = {}
        self.tutor = {}
        self.general = {}
        self.rooms = {}
        self.started_at = {}
        self.min = {}
        self.group_size = {}
        self.timer = {}

        self.update_msg = "Beep boop, ich habe ein Update bekommen! :partying_face: Ich benutze jetzt die neuen Slash-Commands, die du mit `/` benutzen kannst. Dadurch werden die Commands automatisch beim Eingeben angezeigt und sind einfacher zu benutzen. Falls durch das Update irgendwas kaputt gegangen ist, sag bitte Bescheid!"

        for file in self.settings:
            try:
                with open('settings/'+ file + '.pkl', 'rb') as f:
                    setattr(self, file, pickle.load(f))
            except FileNotFoundError:
                pass

        print("------------- Initializations -------------")
        for guild in self.guilds:
            await self.initialize(guild, startup=True)
            try:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
            except:
                print('ERROR: Cannot sync commands for guild ' + guild.name + ' with owner ' + guild.owner.display_name + '!')

        self.help = (" - `/ping`: Schickt eine Benachrichtigung, wenn du eine Frage hast\n"
                     " - `/remaining`: Gibt zurück wie lange der aktuelle Timer noch läuft\n"
                     " - `/help`: Gibt diese Nachricht aus")

        self.help_full = (" - `/init`: Aktualisisert die Einstellungen für den Server\n"
                          " - `/set [bot/general/rooms/size] arg`: Setzt eine Einstellung auf einen neuen Wert, lässt sich chainen\n"
                          " - `/ping`: Schickt eine Benachrichtigung, wenn jemand eine Frage hat\n"
                          " - `/rooms`: Teilt alle teilnehmenden Studierenden auf die Räume auf\n"
                          " - `/timer arg`: Stellt einen Timer für `arg` Minuten, muss ein Integer sein und zwischen 0 und 180 liegen\n"
                          " - `/cancel`: Bricht den aktuellen Timer ab\n"
                          " - `/remaining`: Gibt zurück wie lange der aktuelle Timer noch läuft\n"
                          " - `/announce`: Ruft alle in den allgemeinen Channel zurück\n"
                          " - `/help`: Gibt diese Nachricht aus")

        self.save_settings()

        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    def save_settings(self):
        for file in self.settings:
            with open('settings/'+ file + '.pkl', 'wb+') as f:
                pickle.dump(getattr(self, file), f, pickle.HIGHEST_PROTOCOL)

    async def initialize(self, guild, interaction=None, startup=False):
        new = False
        if guild.id not in self.known_guilds:
            new = True
            self.known_guilds.append(guild.id)
            if not startup:
                self.save_settings()

        bot     = self.settings_bot[guild.id]     if guild.id in self.settings_bot     else self.settings_bot['default']
        general = self.settings_general[guild.id] if guild.id in self.settings_general else self.settings_general['default']
        rooms   = self.settings_rooms[guild.id]   if guild.id in self.settings_rooms   else self.settings_rooms['default']
        size    = self.settings_size[guild.id]    if guild.id in self.settings_size    else self.settings_size['default']

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
        self.group_size[guild.id] = size

        text =  f'Beep boop, ich habe folgende Einstellungen für "{guild.name}" übernommen:\n'
        text += f'Tutor*in: {self.tutor[guild.id].display_name}\n'
        text += f'Bot Channel: {self.bot_channel[guild.id] if bot_found else "*Nicht gefunden!*"}\n'
        text += f'General Voice Channel: {self.general[guild.id]}\n'
        text += f"Voice Channel: {', '.join(r.name for r in self.rooms[guild.id])}\n"
        text += f"Gruppengröße: {self.group_size[guild.id]}"
        error = False
        if not bot_found:
            text +=f"\nDu kannst den Bot Channel manuell mit `!set bot channel_name` festlegen!"
            error = True
        if not general_found:
            text +=f"\nDu kannst den General Voice Channel manuell mit `!set general channel_name` festlegen!"
            error = True
        if not rooms_found:
            text +=f"\nDu kannst die Voice Channel manuell mit `!set rooms channel_name` festlegen! Die Channel sollten dann die Namen `channel_name-i` haben, wobei i bei 1 anfängt."
            error = True
        if error:
            text +=f"\nNachdem du einen Channel gesetzt hast, musst du `!init` benutzen, um die Einstellungen anzuwenden. Alle commands müssen im Server aufgerufen werden!"

        print()
        print(text)
        print()
        if not interaction is None:
            await interaction.response.send_message(text)
        elif new or error:
            await guild.owner.send(text)

        if guild.id not in self.sent_update:
            self.sent_update.append(guild.id)
            if bot_found:
                try:
                    await self.bot_channel[guild.id].send(self.update_msg)
                except:
                    await guild.owner.send(self.update_msg)
            else:
                await guild.owner.send(self.update_msg)

    async def on_guild_join(self, guild):
        await self.initialize(guild)

    async def error(self, interaction, command):
        await interaction.response.send_message(f'Beep boop, es ist leider ein Fehler aufgetreten :sob: Es wurde eine Benachrichtigung geschickt und der Fehler wird so bald wie möglich behoben!')
        excep_traceback = traceback.format_exc()
        except_message = (f"Der Command war: '{command}'\n"
                        f"Hier ist der Stracktrace:\n{excep_traceback}")
        if not self.admin is None:
            await self.admin.send(f"Es ist ein Fehler bei dem Server von {self.tutor[interaction.guild_id].display_name} aufgetreten!\n" + except_message)
        else:
            await self.tutor[interaction.guild_id].send("Es ist ein Fehler aufgetreten! Bitte leite diese Informationen weiter, damit der Fehler behoben werden kann.\n" + except_message)

    async def announce(self, guild):
        self.started_at[guild.id] = None
        await self.bot_channel[guild.id].send('@everyone Die Zeit ist um! Kommt bitte zurück in den allgemeinen Channel!')

        for channel in guild.voice_channels:
            if len(channel.members) == 0:
                continue

            vc = await channel.connect()
            if platform.system() == 'Windows':
                executable_path='C:/Program Files/ffmpeg/bin/ffmpeg.exe'
            else:
                executable_path = '/snap/bin/ffmpeg'
            vc.play(discord.FFmpegPCMAudio(executable=executable_path, source='timer.mp3'))
            await asyncio.sleep(4)
            await vc.disconnect()


class Timer:
    def __init__(self, timeout, callback):
        print('Timer started')
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        if self._timeout > 0:
            await asyncio.sleep(self._timeout)
        print('Timer finished')
        await self._callback()

    def cancel(self):
        self._task.cancel()