# =================================================================================================
# Contributing Authors:	    <Ryan Goin, James Parker, Nathan Rink >
# Email Addresses:          <Ryan.Goin@uky.edu, James.Parker@uky.edu, Nathan.Rink@uky.edu>
# Date:                     <11/19/2025>
# Purpose:                  <How this file contributes to the project>
# Misc:                     <Not Required.  Anything else you might want to include>
# =================================================================================================

import socket
import threading
import time

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

#accept connections on all networks listen to port 5000
Host = "0.0.0.0"
Port = 5000

players = {}
#lock to ensure players arent modified at same time
lock = threading.Lock()
def handle_client(conn, addr, player_id):
    print(f"New Player: {player_id} : {addr}")
    #set players id
    if player_id == 1:
        other = 2
    else:
        other = 1
    #while true: try recieing data from the player. If the client disconnects break the loop.
    #When data is recieved, we acquire the lock to ensure  we access the players dictionary safely. 
    #If the other player is still connected we forward the data to them using sendall
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            with lock:
                if other in players:
                    players[other].sendall(data)
    except OSError:
        pass
    
    #cleans up after a player disconects 
    print(f"Disconnect Player: {player_id}")
    with lock:
         if player_id in players:
            players[player_id].close()
            del players[player_id]
#create server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#Bind server to the host and port and listen for 2 connections
server.bind((Host, Port))
server.listen(2)


print(f"Pong server is running on {Host}:{Port}")
print("Waiting for 2 players")
#accept player one
conn1, addr1 = server.accept()
players[1] = conn1
print(f"Player 1 connected")
#accept player two
conn2, addr2 = server.accept()
players[2] = conn2
print(f"Player 2 connected")
#config window
screen_w = 640
screen_h = 480
#player 1 is left, while player 2 is on the right
players[1].send(f"CONFIG {screen_w} {screen_h} left".encode())
players[2].send(f"CONFIG {screen_w} {screen_h} right".encode())
#Start seperate threads to handle each players msgs
threading.Thread(target=handle_client, args=(conn1, addr1, 1), daemon=True).start()
threading.Thread(target=handle_client, args=(conn2, addr2, 2), daemon=True).start()

print("Both player connected, Game is starting")
#keep the main thread alive
while True:
   time.sleep(0.01)


   
