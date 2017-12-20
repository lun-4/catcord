import logging

import aiohttp

log = logging.getLogger(__name__)


class CatNip:
    def __init__(self, client, api_base):
        self.client = client
        self.api_base = api_base
        self.sess = aiohttp.ClientSession()

    @property
    def headers(self):
        return {
            'Authorization': f'Bot {self.client._token}'
        }

    def _route(self, route):
        return f'{self.api_base}{route}'

    async def request(self, verb: str, route: str, payload: dict):
        """Request a route from the API."""
        log.info(f'{verb} request to {route}')
        async with self.sess.request(verb, self._route(route),
                                     json=payload,
                                     headers=self.headers) as resp:
            return resp

    async def get(self, route, payload=None):
        """Make a GET request to the API."""
        resp = await self.request('GET', route, payload)
        return await resp.json()

    async def post(self, route, payload=None):
        """Make a POST request to the API."""
        resp = await self.request('POST', route, payload)
        return await resp.json()
