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
SCREEN_W = 640
SCREEN_H = 480
PADDLE_H = 50
#accept connections on all networks listen to port 5000
Host = "0.0.0.0"
Port = 5000

#Start a match between two connected clients
def start_match(conn1, addr1, conn2, addr2):
    print("Starting match between:", addr1, "and", addr2)

    global ball_x, ball_y, left_score, right_score, sync_val, players, lock, paddle_y
    
    players = {1: conn1, 2: conn2}
    lock = threading.Lock()

    paddle_y = {
        1: (SCREEN_H // 2) - (PADDLE_H // 2),
        2: (SCREEN_H // 2) - (PADDLE_H // 2)
    }
    ball_x = SCREEN_W // 2
    ball_y = SCREEN_H // 2
    left_score = 0
    right_score = 0
    sync_val = 0

    # Send configuration
    players[1].send(f"CONFIG {SCREEN_W} {SCREEN_H} left".encode())
    players[2].send(f"CONFIG {SCREEN_W} {SCREEN_H} right".encode())

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
                        #send update game state to player 1 
                        try:
                            players[1].sendall(msgForP1.encode())
                        except:
                            pass
                        #send updated game state to player 2
                        try:
                            players[2].sendall(msgForP2.encode())
                        except:
                            pass
            except ValueError:
                #if packet cant be parsed ignore and countinue
                continue                      
    except:
        pass
    
    #cleans up after a player disconects 
    print(f"Disconnect Player: {player_id}")
    try:
        players[player_id].close()
    except:
        pass

    # Create threads
    threading.Thread(target=handle_client, args=(conn1, addr1, 1), daemon=True).start()
    threading.Thread(target=handle_client, args=(conn2, addr2, 2), daemon=True).start()

    while True:
        time.sleep(0.01)

#create server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#Bind server to the host and port and listen for 2 connections
server.bind((Host, Port))
server.listen(1)

print(f"Pong server is running on {Host}:{Port}")

waiting = []   # Queue
print ("Waiting for players...")

while True:
    conn, addr = server.accept()
    print("New connection:", addr)
    waiting.append((conn, addr))

    # When 2 players are waiting, start a match
    if len(waiting) >= 2:
        (c1, a1) = waiting.pop(0)
        (c2, a2) = waiting.pop(0)

        threading.Thread(target=start_match, args=(c1, a1, c2, a2), daemon=True).start()
        print("Match started!")


   
