# =================================================================================================
# Contributing Authors:	    <Ryan Goin, James Parker, Nathan Rink >
# Email Addresses:          <Ryan.Goin@uky.edu, James.Parker@uky.edu, Nathan.Rink@uky.edu>
# Date:                     <11/26/2025>
# Purpose:                  This is the server code for a networked Pong game.  It accepts connections
#                           from two players (and optional spectators), maintains the game state, and
#                           relays updates between the clients to keep their game views synchronized.
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
SCREEN_W = 640
SCREEN_H = 480
PADDLE_H = 50
#accept connections on all networks listen to port 5000
Host = "0.0.0.0"
Port = 5000

players = {}
spectators = []
#lock to ensure players arent modified at same time
lock = threading.Lock()
#server side game state
paddle_y = {
    1: (SCREEN_H // 2) - (PADDLE_H // 2),
    2: (SCREEN_H // 2) - (PADDLE_H // 2)
}
ball_x = SCREEN_W // 2
ball_y = SCREEN_H // 2
left_score = 0
right_score = 0
sync_val = 0
#handles messages from a single client
#each client sends a line of text containing <paddleY> <ballx> <ballY> <lScore> <rScore> <sync>

def handle_client(conn: socket.socket, addr: tuple[str, int], player_id):
    global ball_x, ball_y, left_score, right_score, sync_val
    print(f"New Player: {player_id} : {addr}")
    #set players id
    if player_id == 1:
        other = 2
    else:
        other = 1
    
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            try:
                parts = data.decode().strip().split()
                if len(parts) >= 6:
                    y_val = int(parts[0])
                    with lock:
                        #updates this players paddle position
                        paddle_y[player_id] = y_val
                        #player 1 keeps control of the ball and score
                        if player_id == 1:
                            ball_x = int(parts[1])
                            ball_y = int(parts[2])
                            left_score = int(parts[3])
                            right_score = int(parts[4])
                            sync_val = int(parts[5])
                        else:
                            #player 2 can advance the synv value still
                            their_sync = int(parts[5])
                            if their_sync > sync_val:
                                sync_val = their_sync
                        #build messages to send back
                        msgForP1 = f"{paddle_y[2]} {ball_x} {ball_y} {left_score} {right_score} {sync_val}\n"
                        msgForP2 = f"{paddle_y[1]} {ball_x} {ball_y} {left_score} {right_score} {sync_val}\n"
                        msgForS = f"{paddle_y[1]} {paddle_y[2]} {ball_x} {ball_y} {left_score} {right_score} {sync_val}\n"
                        #send update game state to player 1 
                        if 1 in players:
                            try:
                                players[1].sendall(msgForP1.encode())
                            except OSError:
                                pass
                        #send updated game state to player 2
                        if 2 in players:
                            try:
                                players[2].sendall(msgForP2.encode()) 
                            except OSError:
                                pass
                        #Always send updated game state to spectators
                        try:
                            for spec in spectators:
                                spec.sendall(msgForS.encode())
                        except OSError:
                            pass
            except ValueError:
                #if packet cant be parsed ignore and countinue
                continue                      
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
#Bind server to the host and port and listen for connections
server.bind((Host, Port))
server.listen(3)


print(f"Pong server is running on {Host}:{Port}")
print("Waiting for 2 players")

#keep the main thread alive
while True:
    conn, addr = server.accept()

    with lock:

        #player 1
        if 1 not in players:
            players[1] = conn
            addr1 = addr
            print("Player 1 connected")

        #player 2
        elif 2 not in players:
            players[2] = conn
            addr2 = addr
            print("Player 2 connected")

            players[1].send(f"CONFIG {SCREEN_W} {SCREEN_H} left".encode())
            players[2].send(f"CONFIG {SCREEN_W} {SCREEN_H} right".encode())
            threading.Thread(target=handle_client, args=(players[1], addr1, 1), daemon=True).start()
            threading.Thread(target=handle_client, args=(players[2], addr2, 2), daemon=True).start()
            print("Both player connected, Game is starting")

        #spectators
        else:
            spectators.append(conn)
            conn.send(f"CONFIG {SCREEN_W} {SCREEN_H} spectator".encode())
            threading.Thread(target=handle_client, args=(conn, addr, 3), daemon=True).start()
            print("Spectator connected:", addr)

    time.sleep(0.01)