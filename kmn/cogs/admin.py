import logging

from discord.ext.commands import command

from kmn.checks import is_bot_admin
from kmn.cog import Cog
from kmn.utils import timed

log = logging.getLogger(__name__)


class Admin(Cog):
    @command()
    @is_bot_admin()
    async def die(self, ctx):
        """kills me"""
        await ctx.send('ok, bye.')
        await ctx.bot.logout()

    @command()
    @is_bot_admin()
    async def reload(self, ctx):
        """reloads all extensions"""
        progress = await ctx.send('reloading...')

        with timed() as t:
            for name, ext in ctx.bot.extensions.copy().items():
                try:
                    ctx.bot.unload_extension(name)
                    ctx.bot.load_extension(name)
                except Exception:
                    log.exception('Failed to load %s:', name)
                    return await progress.edit(content=f'failed to load `{name}`.')
        await progress.edit(content=f'reloaded in `{round(t.interval, 2)}ms`.')


def setup(bot):
    bot.add_cog(Admin(bot))
