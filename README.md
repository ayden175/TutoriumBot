# TutoriumBot

[Der Bot kann mit diesem Link eingeladen werden.](https://discord.com/api/oauth2/authorize?client_id=772877261631783003&permissions=24120336&scope=bot)

Alternativ kann der Bot auch selbst gehostet werden, indem `python bot.py` ausgeführt wird. Hierfür muss zuerst eine App erstellt werden, wie in zum Beispiel [dieser Anleitung](https://www.digitaltrends.com/gaming/how-to-make-a-discord-bot/) gezeigt wird. Der Token muss dann in einer Datei `token` gespeichert werden. Danach muss der Bot aus der selbst erstellten App eingeladen werden.

In der `announce` Methode wird FFmpeg benutzt um eine mp3 Datei abzuspielen. Hier müsste der Link zu der Executable eventuell entsprechend angepasst werden (oder der Code auskommentiert werden), falls der Bot selbst gehostet wird.

### Initialisierung
Beim Joinen auf einen neuen Server und beim Starten des Bots werden automatisch die benötigten Channel gesucht. Beim ersten Mal (oder falls Fehler vorhanden sind) bekommt man eine DM von dem Bot mit Infos. Die Initialisierung kann danach manuell nochmal mit `/init` durchgeführt werden.

- Tutor\*in
  - Ist automatisch immer der Owner des Servers, kann momentan nicht geändert werden
- Bot Channel
  - Default: `bot`
  - Der Channel in den der Bot seine Nachrichten schickt
- General Voice Channel
  - Default: `general`
  - Der normale Voice-Channel außerhalb der Gruppenarbeit
- Voice Channel
  - Default: `voice-`
  - Channel in denen die Studierenden in den Gruppen arbeiten
  - Die Channel müssen ab 1 durchnummeriert sein, also `voice-1, voice-2, ...`
- Gruppengröße
  - Default: `3`
  - Minimale Anzahl an Studierenden pro Voice-Channel

Um eine der Einstellungen zu ändern kann der `/set` command benutzt werden. Wenn die Voice-Channel für die Gruppenarbeit zum Beispiel `group-1, group-2, ...` heißen können diese so eingestellt werden:

```
/set rooms group-
```

### Commands
Hier sind alle Commands auflistet und was sie machen. Bei den Commands handelt es sich um die neuen Slash-Commands, sie werden also beim Eingeben angezeigt und automatisch vervollständigt. Außerdem wird angezeigt, was für Argumente die Commands bekommen.

Studierende können nur die Commands `/ping` und `/remaining` ausführen.

##### `/init`

Aktualisiert die Einstellungen für den Server. Einstellungen werden im Ordner `settings` automatisch gespeichert.

##### `/set [bot/general/rooms/size] value`
Setzt eine Einstellung auf einen neuen Wert, lässt sich chainen. Für Beispiele siehe Initialisierung oben.

##### `/ping`
Schickt eine Benachrichtigung, wenn jemand eine Frage hat. Die pingende Person bekommt eine Antwort als Bestätigung und der Bot schickt eine Nachricht in den Bot-Channel für die Tutor\*in.

###### Beispiele:

Falls Student\*in nicht in einem Voice-Channel ist:\
`@Paul: Sophie hat eine Frage!`\
Falls Student\*in in einem Voice-Channel `voice-x` mit der Kategorie `Raum k` ist:\
`@Paul: Sophie hat eine Frage in Raum k!`\
Falls Student\*in in einem Voice-Channel `voice-x` ohne Kategorie ist:\
`@Paul: Sophie hat eine Frage in voice-x!`

##### `/rooms`
Teilt alle teilnehmenden Studierenden gleichmäßig auf die Räume auf. Alle Personen, die gerade im allgemeinen Voice-Channel sind werden aufgeteilt, wobei der Owner (also die Tutor\*in) übersprungen wird.

Bei der Berechnung wird davon ausgegangen, dass die Tutor\*in ebenfalls im Voice-Channel ist, bei n Leuten wird dann also berechnet wie viele Channel für n-1 Personen bei der eingestellten Gruppengröße gebraucht werden. Bei einer Gruppengröße von 3 und 12 Teilnehmer\*innen werden zum Beispiel zwei 4-er und zwei 3-er Gruppen erstellt.

Weil der Bot nur eine begrenzte bandwidth hat dauert es ein paar Sekunden bis alle Studierenden verschoben wurden. Das Verschieben passiert deshalb auch in Batches.

##### `/time arg`
Stellt einen Timer für `arg` Minuten. `arg` muss ein Integer sein und zwischen 1 und 180 liegen. Es kann nur ein Timer gleichzeitig laufen (pro Server).

Wenn der Timer zuende ist wird folgende Nachricht in den Bot-Channel geschickt:\
`@everyone Die Zeit ist um! Kommt bitte zurück in den allgemeinen Channel!`

Außerdem geht der Bot durch alle Voice-Channel des Servers und spielt die `timer.mp3` ab. Leere Voice-Channel werden dabei übersprungen.

##### `/cancel`
Bricht den aktuellen Timer ab.

##### `/remaining`
Gibt zurück wie lange der aktuelle Timer noch läuft.

##### `/announce`
Ruft alle in den allgemeinen Channel zurück. Das Verhalten ist identisch zu dem, was passiert wenn ein Timer abläuft.

##### `/help`
Gibt eine Hilfsnachricht aus. Für Studierende werden nur `/ping` und `/rem` aufgelistet.
