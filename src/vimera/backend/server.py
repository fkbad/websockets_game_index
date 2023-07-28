
# to handle the SIGTERM heroku shutdown signal
from abc import ABC
from asyncio.futures import Future
import time
import os
import signal

# for game id numbering
import secrets

import json

import asyncio
from typing import Optional, Set, Tuple, List, Dict

import websockets.client
import websockets.server
import websockets.exceptions


import logging
logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p', level=logging.DEBUG)

from enum import Enum


# https://github.com/uchicago-cs/chimera/blob/e4feef8d35048dc16d7b71d26f88197a0ebcc7db/src/chimera/common/__init__.py#L4
class ErrorCode(Enum):
    # General error codes
    PARSE_ERROR = -32700
    INCORRECT_REQUEST = -32600
    NO_SUCH_OPERATION = -32601
    INCORRECT_PARAMS = -32602

    # Operation-specific codes
    UNKNOWN_GAME = -40100
    ALREADY_IN_MATCH = -40101
    UNKNOWN_MATCH = -40102
    DUPLICATE_PLAYER = -40103
    INCORRECT_MATCH = -40104

    # game-action codes
    GAME_NOT_PLAYER_TURN = -50100
    GAME_NO_SUCH_ACTION = -50101
    GAME_INCORRECT_ACTION_DATA = -50102
    GAME_INCORRECT_MOVE = -50103

    def __str__(self):
        return ERROR_MESSAGES[self.value]


ERROR_MESSAGES = {
    # General error codes
    ErrorCode.PARSE_ERROR.value: "Parse error",
    ErrorCode.INCORRECT_REQUEST.value: "Incorrect request",
    ErrorCode.NO_SUCH_OPERATION.value: "No such operation",
    ErrorCode.INCORRECT_PARAMS.value: "Incorrect parameters",

    # Operation-specific codes
    ErrorCode.UNKNOWN_GAME.value: "Unknown game",
    ErrorCode.ALREADY_IN_MATCH.value: "Already in a match",
    ErrorCode.UNKNOWN_MATCH.value: "Unknown match",
    ErrorCode.DUPLICATE_PLAYER.value: "Duplicate player name",
    ErrorCode.INCORRECT_MATCH.value: "Incorrect match",

    # game-action codes
    ErrorCode.GAME_NOT_PLAYER_TURN.value: "Action not allowed outside player's turn",
    ErrorCode.GAME_NO_SUCH_ACTION.value: "Unsupported action in game",
    ErrorCode.GAME_INCORRECT_ACTION_DATA.value: "Incorrect data in game action",
    ErrorCode.GAME_INCORRECT_MOVE.value: "Incorrect move"
}

# id : description
# stores all valid game types and their descriptions
# used to generate urls as well as validate requests sent to server
VALID_GAMES = {
        "p1wins" : "player 1 wins"
        }


class Operation(Enum):
    # class to store all valid operations and their 
    # id strings to be used as fields for messages
    # (ie, what to fill in for message["operation"] == ____ )
    CREATE_MATCH = "create-match"
    JOIN_MATCH = "join-match"
    SPECTATE_MATCH = "spectate-match"
    LIST_GAMES = "list-games"
    GAME_ACTION = "game-action"


class VimeraWebsocketsClient():
    """
    class to wrap the behaviour of a client connecting to the websocket server
    from the web.

    will be the interface through which message are actually sent

    Methods:
        send_message : arbitrarily take any message and send it to the client
        send_error : send an error message
        send_response : send a reponse
        send_notification : send a notification
    """
    def __init__(self,websocket,connection_id=None,player_name=None,match_id=None,) -> None:
        """
        create a new Client

        Attributes:
            match: Optional[Match], which is the match object that a client is currently in, if Any
            player: Optional[str], the player name associated with this connection, used as the "player-name" parameter of:
                    create-match
                    join-match
                    game-action (called "spectator-name" in those messages)

            websocket: the actual websocket connection the client is connecting on
            id : the id used to associate any message sent to or from this client, "id" field of the message

        """
        self.match = match_id
        self.player = player_name
        self.websocket = websocket
        self.id = connection_id



    def __str__(self):
        return str(self.player) + "|" + str(self.id) +  "| "

    async def _send_message(self, non_jsoned_message):
        """
        takes in a python object that is to be turned into a JSON message
        and sends it to the websocket assocated with this client

        Inputs:
            non_jsoned_message : python object to be turned into message

        Returns:
            nothing, side affect is to send whatever message to websocket

        """
        jsoned_message = json.dumps(non_jsoned_message,indent=4)
        logging.info(f"SENDING CLIENT {jsoned_message}")
        await self.websocket.send(jsoned_message)


    async def send_notification(self,scope,scope_event,data):
        """
        sends a notification to the client : https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#notifications

        Inputs:
            scope: 
                the scope of the notification

                valid options are : 
                    "Match"

            scope_event: 
                what event is happening on the particular scope what is valid depends on the scope.

                scope : valid options

                Match : 
                    "start" : match has started,
                     "update" : match has been updated buy it still continuing,
                    "end" : match has finished,

            data:
                the data object associated with a notification
                contents depend on status of the Match

        Notification format:
            "type" : "notification",
            "scope" : "match",
            "event" : "start, update, end"
            "data":
                  {
                    "match-id": "magnificent-platypus",
                    "match-status": "in-progress",
                    "game-id": "tictatoe",
                    "game-state": # returned by game logic, contents to depend on that 
                      {
                        "X": "Alex",
                        "O": "Sam",
                        "turn": "X",
                        "board": [[" ", " ", "X"],
                                  [" ", "O", "X"],
                                  [" ", " ", "O"]]
                      }
                  }
                         
        """
        notification = {}
        notification["type"] = "notification"
        notification["scope"] = scope
        notification["event"] = scope_event
        notification["data"] = data

        await self._send_message(notification)

    async def send_response(self,result):

        """
        send a **successful** response to the client (as errors are sent via send_error)

        **sucessful** responses are of form:
            {
                "type": "response",
                 "id": self.id,
                "result" : JSON-like object containing information about the sucess of an operation
                            who's content depends on what operation this is in response to
            }

        result contents based on operation:
            list-games : https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#list-games
                        a single "games" member, containing an array of objects, 
                            one per game supported in the server. 

                        Each object has two members: 
                            "id", a string identifier for the game which can be used to 
                                  refer to the game in other requests, 

                            "description", a human-readable description.

                        All possible games in this format are listed in the VALID_GAMES dict in this format

                     eg:
                     {
                        "games": [
                            {
                                "id","p1wins"
                                "description":"player 1 wins that's literally it"
                            },
                            {
                                "id":"game2",
                                "description":"second game"
                            }
                            ]
                     }

            create-match: https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#create-a-new-match
                          result contents only include the "match-id" of the successfully created match

                    eg:
                    {
                      "match-id": "abcdef"
                    }

            join-match: https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#join-a-match
                        contains empty object {}, 

                    eg:
                    result = {}

            spectate-match: https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#spectate-a-match
                        contains empty object {}, 

                    eg:
                    result = {}

            game-action: https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#game-specific-actions
                        fully game specific data is provided in the result
        """

        # result must be at least an empty dictionary {}
        assert result is not None

        response = {}
        response["type"] = "response"
        response["id"] = self.id
        response["result"] = result
        await self._send_message(non_jsoned_message=response)
        
    async def send_error(self,error_code: ErrorCode,data=None):
        """
        sends an error to the client

        Inputs:
            error_code : an entry in the ErrorCode Enum. 
                        The code is error_code.value
                        The message is str(error_code)
            data : a JSON-like object, the data corresponding to a particular operation

        Error messages are of format:
            {
                "type": "response",
                "id": self.id,
                "error":
                {
                    "code": numeric code for the error, all defined in ErrorCode enum type
                    "message": brief, concise, error message
                    "data": Optional JSON-like object containing more information about the error
                                content of the dictionary is not strictly defined, and more fields
                                can be added without issue, such as debugging specific information
                        {
                            "details" : more detailed description of the error as a string
                        }
                }
            }
        """
        # contruct just the error portion
        error = {}
        error["code"] = error_code.value
        error["message"] = str(error_code)

        if data is not None:
            error["data"] = data

        # construct message 
        message = {
                "type": "response",
                "id": self.id,
                "error": error
                }

        await self._send_message(message)


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
        self._ready_to_accept_messages: Optional[Future] = None

        # Future to await for the server to stop
        self._stop = None


        # dictionary that stores which clients are associated with what websockets
        # Clients are classes that are meant to handle messages in some way
        # {websocket : Client}
        self.clients = {}
        
        # dictionary that maps all valid game id's to their corresponding Game base class object
        # for player 1 wins, not useful yet
        self.games = {}

        # dictionary that maps match-id's to a list of all the websockets
        # associated with  a particular match

        """
        format is:
            matches["match_id"] = {
                    "playing": [list of websockets playing]
                    "watching": [list of websockets watching]
                    }
        """
        self.matches = {}

        # self.matches["abcdef"] = {
        #         "playing": [1,2],
        #         "watching": [3,4]
        #         }

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

        # unsure about exactly how I want to have the control flow go at this point
        # looking at the chimera example, there is further logic about 
        # server stopping and starting, and the use of the loop.create_task() method
        
        # as of now, this implementation simply calls serve and 
        # has the running process of the server happen there
        await self._serve()

        logging.debug("====================================finished serving")

        # start will be finished when the future is done
        await self._ready_to_accept_messages

    async def _serve(self):
        """
        method that actually handles requests
        """
        async with websockets.server.serve(self._handler,self.address,self.port):
            # now that we're able to serve requests, update our futures
            self._ready_to_accept_messages.set_result(True)
            logging.info(f"Vimera Server listening on {self.address} on port {self.port}")

            assert self._stop is not None

            # keep listening for messages until the stop future concludes
            await self._stop

    async def _handler(self,websocket):
        try:
            # register client
            client = VimeraWebsocketsClient(websocket)
            self.clients[websocket] = client

            # accept messages until connection is closed
            try:
                async for raw_message in websocket:
                    # FOR DEBUG PRINTING PURPOSES
                    # ADDS INDENTS FOR SIGNIFICANTLY BETTER PRINTING
                    raw_message = json.dumps(json.loads(raw_message),indent=2)

                    logging.info(f"FROM {client} RCVD : {raw_message}")
                    await self.parse(client,raw_message)

            except websockets.exceptions.ConnectionClosed as exc:
                logging.info(f"connection closed")

        finally:
            # unregister client
            del self.clients[websocket]

            # not sure what to do with client struct for unregistering
            # right now trust that the garbage collector does its job
            # however, https://www.evanjones.ca/memoryallocator/, 
            # and https://stackoverflow.com/questions/31089451/force-python-to-release-objects-to-free-up-memory
            # makes me unsure
            

    async def parse(self,client: VimeraWebsocketsClient,raw_message):
        """
        method to take in any raw message, parse it down the correct path, 
        and validate that it fits any format of valid message

        Inputs:
            client: the VimeraWebsocketsClient that sent the message to the server
                    
            raw_message : a JSON message sent to the server from the web client
                        should always have  "type" : "request", 
                        as the server should never be receiving
                        notifications nor responses

        Returns:
            nothing, instead will send the appropriate 
            response / notification / alert based on what message
            was recieved in what context.

            eg: 
                if we recieve a "join-match" request for a match-id that doesn't exist
                we then return an alert to the user saying the match they wanted to join DNE
        """

        # First, validate the message has all correct fields
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError as json_exc:
            error_details = f"Incorrect JSON (parsing failed at line {json_exc.lineno} column {json_exc.colno})"
            await client.send_error(
                                    error_code=ErrorCode.PARSE_ERROR,
                                    data={"details": error_details}
                                    )
            return


        # https://github.com/uchicago-cs/chimera/blob/e4feef8d35048dc16d7b71d26f88197a0ebcc7db/src/chimera/backend/server.py#L160
        try:
            msg = json.loads(raw_message)
        except json.JSONDecodeError as json_exc:
            error_details = f"Incorrect JSON (parsing failed at line {json_exc.lineno} column {json_exc.colno})"
            await client.send_error(
                                    error_code=ErrorCode.PARSE_ERROR,
                                    data={"details": error_details}
                                    )
            return

        # Check that a type member has been included
        message_type = msg.get("type")
        if message_type is None:
            await client.send_error(
                                    error_code=ErrorCode.INCORRECT_REQUEST,
                                    data={"details": "Message has no 'type' member"}
                                    )
            return

        # Check that we've received a request message
        if message_type != "request":
            await client.send_error(
                                    error_code=ErrorCode.INCORRECT_REQUEST,
                                    data={"details": f"Incorrect message type: {msg['type']}"}
                                    )
            return

        # Check that the request includes an id
        msg_id = msg.get("id")
        if msg_id is None:
            await client.send_error(
                                    error_code=ErrorCode.INCORRECT_REQUEST,
                                    data={"details": f"No id specified"}
                                    )
            return

        # at this point, there is a message ID associated with the client's message
        # so we assign the client an ID 
        client.id = msg_id
        # logging.debug(f"assigned client : {client} with id {msg_id}")

        # Check that the operation is correct (i.e., an operation
        # has been specified, and we have a handler for that operation)
        operation = msg.get("operation")
        if operation is None:
            await client.send_error(
                                    error_code=ErrorCode.INCORRECT_REQUEST,
                                    data={"details": f"No operation specified"}
                                    )
            return


        # at this point, message is guarenteed to have some operation

        # OPERATION TYPES:
        # list-games
        # spectate-match
        # game-action

        # create-match
        # join-match

        # sanity check 
        assert isinstance(operation,str)

        try:
            logging.debug(f"\n\ngot to operation parsing with operation: {operation}")
            match operation.strip():
                case Operation.CREATE_MATCH.value:
                    logging.debug(f"{client} trying to Create Match")

                case Operation.JOIN_MATCH.value:
                    logging.debug(f"{client} trying to Join Match")

                case Operation.SPECTATE_MATCH.value:
                    logging.debug(f"{client} trying to Spectate Match")

                case Operation.LIST_GAMES.value:
                    logging.debug(f"{client} trying to List Games")

                case Operation.GAME_ACTION.value:
                   logging.debug(f"{client} trying to perform a Game Action")

                case _:
                    await client.send_error(
                                            error_code=ErrorCode.NO_SUCH_OPERATION,
                                            data={"details": f"No operation specified"}
                                            )
                    return
                    

        except Exception as err:
            # Handle any errors that may occur
            logging.error(f"Exception [{err}] raised during operation parsing")

        

async def main():
    port = int(os.environ.get("PORT","8001"))
    vs = VimeraWebsocketsServer("",port)
    await vs.start()

if __name__ == "__main__":
    asyncio.run(main())
