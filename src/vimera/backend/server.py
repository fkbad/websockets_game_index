
# to handle the SIGTERM heroku shutdown signal
from abc import ABC
import time
import os
import signal

# for game id numbering
import secrets

import json

import asyncio
from typing import Set, Tuple, List

import websockets

import logging
# logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p', level=logging.DEBUG)

# id : description
# stores all valid game types and their descriptions
# used to generate urls as well as validate requests sent to server
VALID_GAMES = {
        "p1wins" : "player 1 wins"
        }


class VimeraWebsocketsServer():
    """
    class to wrap functionality of websockets server.
    
    will be handling all connections
    """
    def __init__(self, address, port) -> None:
        """
        given address and port for arguments to websockets.serve()
        eg: 127.0.0.1:8000 --> addr : 127.0.0.1 , port : 8000
        """
        self.address = address
        self.port = port

        # task for the server to work on, where the event loop is stored
        self._server_task = None

        # class attribute to denote that the server is ready
        # to serve requests. 
        # will be a Future() that is finished once websockets.serve() is called
        self._ready = None

        # Future to await for the server to stop
        self._stop = None


        # dictionary that stores which clients are associated with what websockets
        # Clients are classes that are meant to handle messages in some way
        self.clients = {}
        
        # dictionary that maps all valid game id's to their corresponding Game base class object
        # for player 1 wins, not useful yet
        self.games = {}

        # dictionary that maps match-id's to a list of all the websockets
        # associated with  a particular match
        self.matches = {}

        # event loop to handle the creation of Futures
        # preffered way to create futures: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.create_future
        self._event_loop = asyncio.get_running_loop()

    async def start(self):
        """
        method to actually start a server.
        meaning that upon successful completion of this method, the server is ready to accept connections

        start attribute is the future corresponding to the server being ready to start

        stop attribute is the future corresponding to the server being done and shutting down
        """
        self._ready_to_accept_messages = self._event_loop.create_future()
        self._stop = self._event_loop.create_future()

        # schedule a run of the _serve method() 
        # this will contain the actual async for loop accepting messages
        # and serving them with websockets.serve()
        # self._server_task = self._event_loop.create_task(self._serve())
        await self._serve()

        # start will be finished when the future is done
        await self._ready_to_accept_messages

    async def _serve(self):
        """
        method that actually handles requests
        """
        async with websockets.serve(self._handler,self.address,self.port):
            # now that we're able to serve requests, update our futures
            self._ready_to_accept_messages.set_result(True)
            logging.info(f"Vimera Server listening on {self.address} on port {self.port}")

            assert self._stop is not None

            # keep listening for messages until the stop future concludes
            await self._stop

    async def _handler(self,websocket):
        try:
            async for raw_message in websocket:
                print(raw_message)
        except websockets.exceptions.ConnectionClosed as exc:
            LOGGING.info(f"connection closed")
            
        

async def main():
    port = int(os.environ.get("PORT","8001"))
    vs = VimeraWebsocketsServer("",port)
    await vs.start()

if __name__ == "__main__":
    asyncio.run(main())
