# SP2MP

SP2MP is a Python package that allows simple multiplayer games usually played on one device, to be played over multiple
devices. The "server" device will run the game, and can select clients to broadcast the game to. The clients will then
press keys, which are sent back to the server.

A simple example is the "SuperFighters" game, which allows 2 players to play on the same device (WASD and arrow keys).
The server may use the arrow keys, while the client uses WASD. The server will then broadcast the game to the client,
and the client will send back the key presses.

Currently, this has only been tested over a LAN, using internal ip addresses, like `192.168.xxx.xxx`. **DO NOT** try to
update the socket code to use external addresses, until key black/white listing is implemented.

## NOTES

- Only tested on Windows (this won't work on Linux or MacOS, due to the way the key events are handled).

## TODO

- The key mapper functionality (allowing a client to bind their own player 1 keys to the server's player 2 keys for
  example) is not implemented yet.
- Blacklist certain keys that would allow the client to control the server.
- Allow the server to whitelist keys that can be sent by the client (like restricting player 2 to player 2 keys).
