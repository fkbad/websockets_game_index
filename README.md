# Chimera + Websockets Sandbox
This repository is to host a small collection of websocket games
that use the Uchicago Chimera Message format: https://chimera-docs.readthedocs.io/en/latest/reference/message-format.html#game-specific-actions


## design notes
current idea is to have game urls be at:

`root/game_id/match_id`
where `game_id` is the specific game_id as specified by list_games

this way, when a user uses a join link, it would be of format:

`root/p1wins/?join=cool-cats`

so the server can then parse they want to join a player 1 wins match with id `cool-cats`


## packages:
https://pypi.org/project/wonderwords/
- to generate funny match-id's

## personal message format reference 


