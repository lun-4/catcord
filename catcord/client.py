import asyncio
import logging
import json

import websockets

from .http import CatNip
from .gateway import CatWalk

log = logging.getLogger(__name__)


class Client:
    """Main client class for CatCord"""
    def __init__(self, **kwargs):
        self.loop = asyncio.get_event_loop()
        self._token = ''

        self.api_base = kwargs.get('api_base',
                                   'https://discordapp.com/api')

        self.http = CatNip(self, self.api_base)

        # gateway connection
        self.ws = None
        self.catwalk = None

    async def send(self, payload: dict):
        frame = json.dumps(payload)
        await self.ws.send(frame)

    async def recv(self) -> dict:
        frame = await self.ws.recv()
        return json.loads(frame)

    async def send_op(self, code, payload):
        await self.send({
            'op': code,
            'd': payload
        })

    async def identify(self):
        await self.send_op(2, {
            'token': self._token,
            'properties': {
                '$os': 'linux',
                '$browser': 'catcord (luna#4677)',
                '$device': 'linux',
            },
            'compress': False,
            'large_threshold': 50, # TODO: change to 250
            'shard': [0, 1]
        })

    async def _gateway(self):
        payload = await self.http.get('/gateway')
        print(payload)
        gateway_url = payload['url']

        log.info(f'Connecting to {gateway_url!r}')

        async with websockets.connect(gateway_url) as conn:
            self.ws = conn
            await self._infinite_gateway()

    async def _infinite_gateway(self):
        """Enter an infinite loop waiting for packets
        from the gateway."""

        try:
            while True:
                payload = await self.recv()
                await self.dispatch_op(payload)
        except Exception:
            log.exception('error in gateway handler')

    async def dispatch_op(self, frame: dict):
        op = frame['op']

        handler = getattr(self, f'_op_handler_{op}', None)
        if handler:
            log.debug(f'Handling op {op}')
            await handler(frame)
        else:
            log.warning(f'Unhandled op {op}')

    async def _op_handler_0(self, payload):
        """Handle OP 0 Dispatch"""
        print(payload)

    async def _op_handler_10(self, payload: dict):
        # Identify
        await self.identify()
        self.catwalk = CatWalk(self, payload['d'])

    async def _op_handler_11(self, payload):
        """Handler for OP 11 Heartbeat ACK"""
        log.debug('Heartbeat ACK')
        self.catwalk._ack = True

    async def stop(self):
        """Stop the gateway connection."""
        log.info('Closing...')
        await self.ws.close()

    def start(self, token: str):
        """Start the main client class"""
        try:
            self._token = token

            self.loop.run_until_complete(self._gateway())
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.stop())
        except:
            log.exception('error in client start')

