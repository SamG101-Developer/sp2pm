# SP2MP

SP2MP is a Python package designed to facilitate the conversion of single-player games into multiplayer experiences. It
provides "broadcaster" and "key-mapper" utilities.

The broadcaster utility allows you to stream game data to multiple clients, while the key-mapper utility enables you to
accept other clients keys and map then to teh actual player 2 key mappings. These are then saved per game.

A simple example is the Superfighters game. The host will attach clients, and broadcast to them in parallel. The clients
will see the broadcast, and can send their key presses to the host. The host will then map these keys to the player 2
keys, and the game will be played as if it was a multiplayer game.
