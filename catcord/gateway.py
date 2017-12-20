import logging
import asyncio
import time

log = logging.getLogger(__name__)


class CatWalk:
    """Heartbeating handler class"""
    def __init__(self, client, payload):
        self.client = client
        self._seq = None
        self._ack = True

        # metrics
        self.delta = -200
        self.last_hb = 0

        self.client.loop.create_task(self.wrap(payload))

    def ack(self):
        """Acknowledge a heartbeat."""
        self.delta = round((time.monotonic() - self.last_hb) * 1000)
        log.info(f'heartbeat complete, took {self.delta}ms')
        self._ack = True

    async def wrap(self, payload):
        """Wrap the heartbeating task in a try/except
        for logging purposes."""
        try:
            await self._task(payload)
        except Exception:
            log.exception('Heartbeat task failed')

    async def _task(self, payload):
        """Main heartbeating class"""
        while True:
            log.debug(f'Heartbeating with seq {self._seq}')
            if not self._ack:
                log.warning('We did not ACK, should we restart?')

            await self.client.send({
                'op': 1,
                'd': self._seq,
            })
            self.last_hb = time.monotonic()

            await asyncio.sleep(payload['heartbeat_interval'] / 1000)
