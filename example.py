import logging

import catcord

import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Kitty(catcord.Client):
    async def evt_message(self, message):
        log.debug(message)
        if message.content == 'cat ping':
            await message.reply('hello')


if __name__ == '__main__':
    nya = Kitty(prefix='cat ',
                api_base='https://discordapp.com/api')
    nya.start(config.token)
