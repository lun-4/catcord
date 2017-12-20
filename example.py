import logging
import inspect

import catcord

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Kitty(catcord.Client):
    """Example bot to show off CatCord."""
    async def h_ready(self):
        """READY handler"""
        log.info(f'We are READY! {self.user}')

    async def h_message_create(self, message):
        """MESSAGE_CREATE handler"""
        if message['author']['id'] == self.user['id']:
            return

        cnt = message['content']
        if not cnt.startswith(self.prefix):
            return

        cnt = cnt[len(self.prefix):]

        spl = cnt.split(' ')
        command = spl[0]
        args = spl[1:]

        cmd_handler = getattr(self, f'c_{command.lower()}', None)

        if cmd_handler:
            try:
                log.info(f'Executing command {command}')
                await cmd_handler(message, args)
            except Exception:
                log.exception(f'error on command {command}')
        else:
            log.info(f'Command {command!r} not found')

    async def c_help(self, message, args):
        """Show help about commands.

        'help' - list all commands
        'help <cmd>' - specific help
        """
        try:
            command = args[0]
            cmd_handler = getattr(self, f'c_{command}', None)
            if not cmd_handler:
                return await self.reply(message, 'command not found')

            return await self.reply(message, f'`{cmd_handler.__doc__}`')
        except:
            # list all
            res = []
            method_list = dir(self)
            for method in method_list:
                if method.startswith('c_'):
                    res.append(method[2:])
            await self.reply(message, ' '.join(res))

    async def c_args(self, message, args):
        """Show arguments provided by you"""
        await self.reply(message, args)

    async def c_ping(self, message, args):
        """Show the time taken for the last
        heartbeat -> heartbeat ack."""
        await self.reply(message, 'last hb->ack window: '
                                  f'`{self.catwalk.delta}ms`')

    async def c_abc(self, message, args):
        """def"""
        res = ' <:blobcatheart:384394753749417996> '.join(args)
        await self.reply(message, res)

    async def c_eval(self, message, args):
        """evaulate code"""
        if message['author']['id'] != self.owner_id:
            return await self.reply(message, 'nope')

        input_data = ' '.join(args)
        try:
            result = eval(input_data)
            await self.reply(message, result)
        except Exception as exc:
            await self.reply(message, repr(exc))


if __name__ == '__main__':
    nya = Kitty(prefix='cat ',
                api_base='https://discordapp.com/api',
                owner_id=config.owner_id)
    nya.start(config.token)
