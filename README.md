Usage:

```py
import discord
import hikari
import hikari_shim

dpy_bot = discord.Client(intents=discord.Intents.all(), enable_debug_events=True)
hikari_bot = hikari.GatewayBot("TOKEN")


@dpy_bot.event
async def on_message(message):
    if message.content == "discord.py is cool":
        await message.channel.send("yes it is!")


@hikari_bot.listen(hikari.MessageCreateEvent)
async def hikari_on_message(evt):
    if evt.content == "hikari is cool":
        await evt.message.respond("yes it is!")


hikari_shim.partial_load(dpy_bot, hikari_bot)

dpy_bot.run("TOKEN")
```

There's also a full (?) shim, but it runs into loop issues and whatnot. It
requires you to use a Hikari client with no intents and start both clients.

### caveat emptor

 - This does not work with `discord.AutoShardedClient`.
 - This has a peer dependency on discord.py, make sure to install that!
 - There are some operations that are not shimmed (voice and chunking guild
   members, to be specific, because I do not know how to do them in dpy).
 - Ratelimiting is not shared.
 - You will have double the CPU usage and double the memory usage. (or
   something in that range).
 - Some components may not have been started yet. (if you're using a non-
   standard client).
 - You will get all the incompatibilities Discord.py gives. This means, for
   example, you cannot get thread events on dpy 1.7 even if Hikari has those.
 - More, probably.

### why though?

Incrementally rewrite your bot in a whole library. This means that you can
have a total rewrite without people ever noticing (though they will,
probably). Also, this lets you stick with discord.py while the Hikari
community matures for some parts (though caveats still apply, so you'll want
to have the entire bot in Hikari eventually).

### contact me

You can find me in the [Hikari Discord server](https://discord.gg/Jx4cNGG).

Download from PyPI!

`pip install hikari_shim`
