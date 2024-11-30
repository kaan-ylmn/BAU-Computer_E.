import json
import socket
import random
import datetime

print("Welcome to CMP2204 LAN Party! \nWe are going to listen for other users and announce who is online!")
ip_address = input("Please enter the IP Address (simply press 'Enter' for localhost): ")
if ip_address == "":
    ip_address = 'localhost'

sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_udp.bind((ip_address, 6000))  # Listening for UDP broadcast messages on the specified IP address and port
peers = {}  # Dictionary to store peers

with open("online_peers.txt", "w") as peer_file:
    pass

while True:
    message, address = sock_udp.recvfrom(2048)  # Receiving the broadcast message
    message = json.loads(message.decode())
    username = message.get('username', 'Unknown')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    peers[address[0]] = {'port': address[1], 'username': username, 'last_seen': timestamp, 'status': "Online"}  # Storing the peer information
    actions = ["doing their best", "ready", "waiting", "excited", "focused", "working hard", "having fun", "chilling"]
    action = random.choice(actions)  # A little fun idea I had to add small actions to the online message.
    print(f"{username} is online and {action}!")
    with open("online_peers.txt", "w") as peer_file:  # Saving the peer information to a file
        json.dump(peers, peer_file)
