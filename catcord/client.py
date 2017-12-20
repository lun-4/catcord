import asyncio
import logging
import json

import websockets

from .http import CatNip
from .gateway import CatWalk

log = logging.getLogger(__name__)
logging.getLogger('websockets').setLevel(logging.INFO)


class Client:
    """Main client class for CatCord"""
    def __init__(self, **kwargs):
        self.loop = asyncio.get_event_loop()
        self._token = ''

        self.prefix = kwargs.get('prefix', '!')
        self.owner_id = kwargs.get('owner_id')

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
        log.info('Identifying with the gateway..')
        await self.send_op(2, {
            'token': self._token,
            'properties': {
                '$os': 'linux',
                '$browser': 'catcord (luna#4677)',
                '$device': 'linux',
            },
            'compress': False,
            'large_threshold': 250,
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
            await handler(frame)
        else:
            log.warning(f'Unhandled op {op}')

    async def _op_handler_0(self, payload):
        """Handle OP 0 Dispatch"""
        event_type = payload['t']
        self.catwalk._seq = payload['s']

        _evt = event_type.lower()
        handler = getattr(self, f'_h_{_evt}', None)
        if handler:
            await handler(payload)
        else:
            log.warning(f'Unhandled event {event_type}')

    async def _op_handler_10(self, payload: dict):
        log.info('Connected!')
        await self.identify()
        self.catwalk = CatWalk(self, payload['d'])

    async def _op_handler_11(self, payload):
        """Handler for OP 11 Heartbeat ACK"""
        self.catwalk.ack()

    # handlers for events
    def dispatch(self, name, *args):
        evt_handler = getattr(self, f'h_{name.lower()}', None)
        if evt_handler:
            self.loop.create_task(evt_handler(*args))

    async def _h_ready(self, payload):
        """Handle the READY event.
        
        This contains basic data to fill the client's cache
        """
        data = payload['d']
        self._session_id = data['session_id']

        log.info(f'READY! session_id={self._session_id},'
                 f' connected to {data["_trace"]}')

        self.user = data['user']
        self.guilds = data['guilds']

        self.dispatch('ready')

    async def _h_message_create(self, payload):
        data = payload['d']
        self.dispatch('message_create', data)

    async def _h_presence_update(self, payload):
        """dummy handler"""
        log.debug('Ignoring presence update')

    async def h_typing_start(self, payload):
        """dummy handler"""
        log.debug('Ignoring typing start')

    # helper functions
    async def reply(self, message: dict, reply) -> dict:
        reply = str(reply)
        cid = message['channel_id']
        return await self.http.post(f'/channels/{cid}/messages', {
            'content': reply,
        })

    def stop(self):
        """Stop the gateway connection."""
        log.info('Closing...')
        self.loop.run_until_complete(self.ws.close())
        self.loop.close()

    def start(self, token: str):
        """Start the main client class"""
        try:
            self._token = token

            self.loop.run_until_complete(self._gateway())
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.stop()
        except:
            log.exception('error in client start')

