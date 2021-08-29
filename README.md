Usage as a partial shim:

```py
import discord
import hikari
import hikari_shim

dpy_bot = discord.Client(intents=discord.Intents.all(), enable_debug_events=True)
hikari_bot = hikari.GatewayBot("TOKEN")


@dpy_bot.event
async def on_connect():
    # This is required to use REST routes :(
    hikari_bot._rest.start()


@dpy_bot.event
async def on_message(message):
    print("message received on discord.py side!")


@hikari_bot.listen(hikari.MessageCreateEvent)
async def hikari_on_message(evt):
    print("message received on hikari side!")


hikari_shim.partial_load(dpy_bot, hikari_bot)

dpy_bot.run("TOKEN")
```

There's also a full (?) shim, but it runs into loop issues and whatnot. It
requires you to use a hikari client with no intents and start both clients.

### caveat emptor

 - This does not work with `discord.AutoShardedClient`.
 - This has a peer dependency on discord.py, make sure to install that!
 - There are some operations that are not shimmed (voice and chunking guild
   members, to be specific, because I do not know how to do them in dpy).
 - Ratelimiting is not shared.
 - You will have double the CPU usage and double the memory usage. (or
   something in that range).
 - Some components may not have been started yet.
 - More, probably.

### contact me

You can find me in the [Hikari Discord server](https://discord.gg/Jx4cNGG).

Download from PyPI!

`pip install hikari_shim`
