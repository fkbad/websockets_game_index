"""
Module to hold information for handling Matches
"""
from typing import Optional, Dict
from queue import Queue, Empty


class Match:
    """
    Class to represent the state of a match and handle connections for a match

    Goal is to be able to send a notification to a Match object
    then that match will handle all of the sending of notifications and interfacing with game logic

    players:
        list of players in the order they joined a match

    spectators:
        list of spectators in the order they joined a match

    id:
        match-id

    game:
        the actual game that is being played in the match

    status:
        the match status:
            "awaiting-players": The match is still waiting for enough players to join.
            "ready": Enough players have joined that match, and it is ready to start.
            "in-progress: The match is in progress.
            "done": The match has concluded.

            also unknown, for when a match has been instantiated, but nothing has been checked
            against the game logic


    winner:
        whoever the winner is! will be instantiated as None and only updated when
        the game logic 


    notifications:
        queue of all notification sent to the match
        done via a queue since notifications could be sent while 
        the match is processing another, since clients are not bound to one thread
    """
    # https://github.com/uchicago-cs/chimera/blob/e4feef8d35048dc16d7b71d26f88197a0ebcc7db/src/chimera/client/api.py#L107C1-L111C26
    STATUS_AWAITING_PLAYERS = "awaiting-players"
    STATUS_READY = "ready"
    STATUS_IN_PROGRESS = "in-progress"
    STATUS_DONE = "done"
    STATUS_UNKNOWN = None

    def __init__(self,match_id:str,game_id:str) -> None:
        self.players = {}
        self.spectators = {}

        # TODO, change this to a Game object

        self.id = match_id

        self.status = Match.STATUS_UNKNOWN

        self.game = game_id

        # https://docs.python.org/3/library/queue.html
        # Thread aware First-in-First-out (line of people) queue. 
        # allows for safe exchange of information across threads
        
        # takes in `maxsize` argument to determine the maximum size of the queue
        #   if it is <= 0, then the queue is infinitely sized

        # use Queue.get() to wait for something to enter the queue
        #   this is blocking, so the thread that called it will be blocked
        #   until something enters the queue
        # use Queue.get_nowait() to immediately retrieve something 
        #   and if nothing is in the queue it will raise the queue.Empty exception 
        #       (just called `Empty` if doing `from queue import Empty`)
        self.notifications = Queue(maxsize=-1)

    def add_player(self,client):
        """
        takes in a Client class of some kind and adds it as a player if possible

        sends error to client if the game is full and/or started
        """
        pass

    def add_spectator(self,client):
        """
        takes in a Client class of some kind and adds it as a Spectator

        sends error to client if the game done 
        """
        pass

    def process_notification(self,match_notification: MatchNotification):
        """
        process a notification, updating interal attributes and sending
        messages to players and spectators as necesary
        """
        pass

    def broadcast(self,jsoned_message):
        """
        send a message to all players and spectators

        uses websockets.broadcast for spectators 
        """
        pass




class MatchNotification:
    """
    https://github.com/uchicago-cs/chimera/blob/e4feef8d35048dc16d7b71d26f88197a0ebcc7db/src/chimera/client/api.py#L229

    Class for storing information about a match notification received by the server.

    Should never be instantiated directly.
    """

    EVENT_START = "start"
    EVENT_UPDATE = "update"
    EVENT_END = "end"

    _match: Match
    _event: str
    _data: dict

    def __init__(self, match: Match, event: str, data: dict):
        """ Constructor

        Args:
            match: Match this notification pertains to
            event: Event being notified
            data: Notification data
        """
        self._match = match
        self._event = event
        self._data = data

    @property
    def event(self) -> str:
        """Gets the notification event"""
        return self._event

    @property
    def match_status(self) -> Optional[str]:
        """Gets the match status included in the notification"""
        return self._data.get("match-status")

    @property
    def game_state(self) -> Optional[dict]:
        """Gets the game state included in the notification"""
        return self._data.get("game-state")

    @property
    def winner(self) -> Optional[str]:
        """Gets the winner included in the notification"""
        return self._data.get("match-winner")

    def process(self) -> None:
        """ Processes the notification, and updates tha state
        of the match with the information included in the
        notification.

        Returns: None

        """
        self._match.process_notification(self)
