# Chimera + Websockets Sandbox
This repository is to host a small collection of websocket games
that use the Uchicago Chimera Message format: https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#game-specific-actions


## design notes
current idea is to have game urls be at `root/games/game_id/match_id`
forming a new game and opening a websocket connection when you click a link 
and go to the corresponding game home page at `root/games/game_id`

- eg: `localhost:8000/games/p1wins/` will create a websocket connection and start a new match of p1wins

so the server can then parse they want to join a player 1 wins match with id `cool-cats`


## packages:
https://pypi.org/project/wonderwords/
- to generate funny match-id's

## personal message format reference 


