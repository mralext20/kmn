import arrow
import arrow.parser

import discord
from discord.ext.commands import group, command

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.errors import CommandFailure
from kmn.storage import JSONStorage


class Timezone(Cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.storage = JSONStorage('_timezones.json', loop=bot.loop)

    def time_for(self, who):
        timezone = self.storage.get(str(who.id), None)

        if not timezone:
            raise CommandFailure(f'{who} has no timezone set.')

        return timezone, arrow.utcnow().to(timezone)

    def format_arrow(self, time):
        return time.format('MMM ddd YYYY-MM-DD HH:mm:ss (hh:mm:ss a)')

    def check_timezone(self, timezone):
        try:
            arrow.utcnow().to(timezone)
        except arrow.parser.ParserError:
            raise CommandFailure('invalid timezone.')

    @group(aliases=['t'], invoke_without_command=True, brief="shows the time for someone")
    async def time(self, ctx, *, who: discord.User=None):
        """command group about time"""
        who = who or ctx.author
        raw_timezone, time = self.time_for(who)
        await ctx.send(f'`{raw_timezone}`: {self.format_arrow(time)}')

    @command()
    async def sleep(self, ctx, *, who: discord.User=None):
        """tells someone to sleep maybe"""
        who = who or ctx.author

        subject = 'you' if who == ctx.author else 'they'
        subject_external = 'you' if who == ctx.author else 'them'

        # get the time for the person
        raw, time = self.time_for(who)

        # format the time for their timezone
        time_formatted = time.format('hh:mm a') if 'US' in raw else time.format('HH:mm')

        if time.hour in {23, 24, 0, 1, 2, 3, 4, 5}:
            await ctx.send(f"hey {who.mention}, it's {time_formatted}. you should sleep.")
        else:
            await ctx.send(f"{subject} don't need to sleep (it's {time_formatted} for {subject_external}).")

    @time.command(hidden=True)
    @is_bot_admin()
    async def write(self, ctx, who: discord.User, *, timezone):
        """sets someone's timezone"""
        self.check_timezone(timezone)
        await self.storage.put(str(who.id), timezone)
        await ctx.send(f"\N{OK HAND SIGN} set {who}'s timezone to `{timezone}`.")

    @time.command(brief="sets your timezone")
    async def set(self, ctx, *, timezone=None):
        """sets your timezone (interactive)

        if you provide a timezone in the command, it won't be interactive"""

        # confirm overwriting
        if self.storage.get(str(ctx.author.id), None):
            if not await ctx.confirm(title='Overwrite your timezone?', description='You already have one set.'):
                return

        if not timezone:
            # we interactive now
            await ctx.send("what timezone are you in?\n\nyou can send a timezone name (list here: "
                           "<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>) or in ISO-8601 "
                           "style (e.g. `-07:00`). send `cancel` to cancel.")

            while True:
                # wait for a message
                message = await ctx.bot.wait_for('message',
                                                 check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

                # bail
                if message.content == 'cancel':
                    return await ctx.send('ok, bye.')

                try:
                    # check timezone
                    self.check_timezone(message.content)
                except CommandFailure as failure:
                    # don't return, just send it and continue
                    await ctx.send(str(failure))
                    continue

                # store
                timezone = message.content
                break

        # check the timezone
        self.check_timezone(timezone)

        # put into storage
        await self.storage.put(str(ctx.author.id), timezone)

        # ok
        await ctx.send(f'ok, your timezone was set to `{timezone}`.')


def setup(bot):
    bot.add_cog(Timezone(bot))