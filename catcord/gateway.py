import logging
import asyncio

log = logging.getLogger(__name__)


class CatWalk:
    """Heartbeating handler class"""
    def __init__(self, client, payload):
        self.client = client
        self._seq = None
        self._ack = True

        self.client.loop.create_task(self._task(payload))

    async def _task(self, payload):
        while True:
            log.debug(f'Heartbeating: {self._seq}')
            if not self._ack:
                log.warning('We did not ACK')

            await self.client.send({
                'op': 1,
                'd': self._seq,
            })

            await asyncio.sleep(payload['heartbeat_interval'] / 1000)

