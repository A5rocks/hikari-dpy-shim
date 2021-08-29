"""A compatability shim between Discord.py and Hikari."""
from __future__ import annotations

import dataclasses
import datetime
import json
import typing
import zlib

import discord
import hikari
import hikari.api.shard as shard_api

__version__ = "1.0.1"

ZLIB_SUFFIX = b"\x00\x00\xff\xff"


@dataclasses.dataclass()
class DummyShard(shard_api.GatewayShard):
    shard_id: int
    bot: discord.Client
    shard_shard_count: int

    @property
    def heartbeat_latency(self) -> float:
        return self.bot.latency

    @property
    def id(self) -> int:
        return self.shard_id

    @property
    def intents(self) -> hikari.Intents:
        return hikari.Intents(self.bot.intents.value)

    @property
    def is_alive(self) -> bool:
        return not self.bot.is_closed()

    @property
    def shard_count(self) -> int:
        return self.shard_count

    async def get_user_id(self) -> hikari.Snowflake:
        app_id = self.bot.application_id

        if not app_id:
            raise ValueError("Bot#application_id is `None`?")

        return hikari.Snowflake(app_id)

    async def close(self) -> None:
        await self.bot.close()

    async def join(self) -> None:
        raise NotImplementedError("join shouldn't be called")

    async def start(self) -> None:
        raise NotImplementedError("start shouldn't be called")

    # TODO: why is this ignore needed?
    async def update_presence(  # type: ignore [override]
        self,
        *,
        idle_since: hikari.UndefinedNoneOr[datetime.datetime],
        # not sure how to handle this?
        afk: hikari.UndefinedOr[bool],
        activity: hikari.UndefinedNoneOr[hikari.Activity],
        status: hikari.UndefinedOr[hikari.Status]
    ) -> None:
        kwargs: typing.Any = {}
        if not isinstance(status, hikari.UndefinedType):
            kwargs["status"] = discord.Status(status.value)

        activity_kwargs: typing.Any = {}

        if activity and not isinstance(activity, hikari.UndefinedType):
            activity_kwargs["name"] = activity.name

            if activity.url:
                activity_kwargs["url"] = activity.url

            if isinstance(activity.type, hikari.ActivityType):
                activity_kwargs["type"] = discord.ActivityType(activity.type.value)
            else:
                activity_kwargs["type"] = discord.ActivityType(activity.type)

        if not isinstance(idle_since, hikari.UndefinedType):
            activity_kwargs["created_at"] = idle_since

        if activity_kwargs:
            kwargs["activity"] = discord.Activity(**activity_kwargs)

        await self.bot.change_presence(**kwargs)

    # TODO: why is this ignore needed?
    async def update_voice_state(  # type: ignore [override]
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        channel: typing.Optional[hikari.SnowflakeishOr[hikari.GuildVoiceChannel]],
        *,
        self_mute: hikari.UndefinedOr[bool],
        self_deaf: hikari.UndefinedOr[bool]
    ) -> None:
        raise NotImplementedError("I've never done voice stuff with Discord.py")

    # TODO: why is this ignore needed?
    async def request_guild_members(  # type: ignore [override]
        self,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild],
        *,
        include_presences: hikari.UndefinedOr[bool],
        query: str,
        limit: int,
        users: hikari.UndefinedOr[hikari.SnowflakeishSequence[hikari.User]],
        nonce: hikari.UndefinedOr[str]
    ) -> None:
        raise NotImplementedError("Not sure how to do this with Discord.py")


def partial_load(dpy: discord.Client, hk: hikari.EventManagerAware) -> None:
    buffer = bytearray()
    inflator = zlib.decompressobj()

    @dpy.event
    async def on_socket_raw_receive(msg: typing.Union[str, bytes]) -> None:
        nonlocal buffer
        if isinstance(msg, bytes):
            buffer.extend(msg)
            if len(msg) < 4 or msg[-4:] != ZLIB_SUFFIX:
                return

            evt = json.loads(inflator.decompress(buffer).decode("utf-8"))
            buffer = bytearray()
        else:
            evt = json.loads(msg)

        if evt["op"] != 0:
            return

        dummy = DummyShard(
            # FIXME: is there a way to find what dpy shard called this event?
            shard_id=0,
            bot=dpy,
            # TODO: when `shard_id` works, this should too.
            shard_shard_count=1,
        )
        hk.event_manager.consume_raw_event(evt["t"], dummy, evt["d"])


class _FullLoadProto(hikari.EventManagerAware, hikari.ShardAware):
    pass


def full_load(dpy: discord.Client, hk: _FullLoadProto) -> None:
    buffer = bytearray()
    inflator = zlib.decompressobj()

    @dpy.event
    async def on_socket_raw_receive(msg: typing.Union[str, bytes]) -> None:
        nonlocal buffer
        if isinstance(msg, bytes):
            buffer.extend(msg)
            if len(msg) < 4 or msg[-4:] != ZLIB_SUFFIX:
                return

            evt = json.loads(inflator.decompress(buffer).decode("utf-8"))
            buffer = bytearray()
        else:
            evt = json.loads(msg)

        if evt["op"] != 0:
            return

        # FIXME: is there a way to find what dpy shard called this event?
        hk.event_manager.consume_raw_event(evt["t"], hk.shards[0], evt["d"])
