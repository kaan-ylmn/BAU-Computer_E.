import json
import pyDes
import base64
import socket
import random
import threading
from datetime import datetime, timedelta

peers = {}  # Dictionary to store peers
log = []  # List to store chat history
# Create a global lock
log_lock = threading.Lock()

print("Welcome to CMP2204 LAN Party! \nWe are going to respond to other users' chat messages!")


def load_peers():
    global peers
    with open("online_peers.txt", "r") as peer_file:  # Loading the peers from the file
        peers = json.load(peer_file)
    now = datetime.now()
    for addr, info in list(peers.items()):  # Using list to avoid RuntimeError: dictionary changed size during iteration
        last_seen = datetime.strptime(info['last_seen'], "%Y-%m-%d %H:%M:%S")  # Converting the last_seen to datetime
        difference = now - last_seen
        if difference > timedelta(minutes=15):
            del peers[addr]
        elif difference <= timedelta(seconds=10):
            info['status'] = 'Online'
        else:
            info['status'] = 'Away'


def log_message(username, message, status="SENT"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_address = next((address for address, info in peers.items() if info['username'] == username), 'Unknown')
    log_entry = f"{timestamp} - {ip_address} - {username} - {status} - {message}"  # Creating a log entry
    log.append(log_entry)
    try:
        # Acquire the lock before writing to the file
        log_lock.acquire()
        with open("chat_history.txt", "a") as log_file:  # Appending the log entry to the log file
            log_file.write(log_entry + '\n')
            log_file.flush()  # Flushing the buffer to write the log entry immediately
    except IOError as e:
        print(f"File error: {e}")
    finally:
        # Release the lock after writing to the file
        log_lock.release()


def handle_client(sock_tcp, address):  # Function to handle the client connection
    load_peers()
    cipher_suite = None
    ip_address = address[0]

    while True:
        data = sock_tcp.recv(2048)  # Receiving data from the client
        if not data:
            break

        if isinstance(data, bytes):  # Check if data is bytes
            data = data.decode()

        message = json.loads(data)

        username = next((info['username'] for address, info in peers.items() if address == ip_address), 'Unknown')

        if 'key' in message:  # If the message contains a 'key', we create a shared key
            other_user_shared_key = int(message['key'][2:-1])
            public_divisor = 23
            public_prm = 5
            private_key = random.randint(1, 23)
            shared_key = str((public_prm ** private_key) % public_divisor).encode()
            sock_tcp.send(json.dumps({'key': str(shared_key)}).encode())
            final_key = str((other_user_shared_key ** private_key) % public_divisor).encode()
            final_key = base64.urlsafe_b64encode(final_key)
            cipher_suite = pyDes.triple_des(final_key.ljust(24))

        if 'encrypted message' in message:  # If the message contains an 'encrypted message'
            encrypted_message = message.get('encrypted message')
            encrypted_message = base64.b64decode(encrypted_message)  # Converting bytes to base64 encoded string
            decrypted_message = cipher_suite.decrypt(encrypted_message, padmode=2)  # Decrypting the message
            decrypted_message = decrypted_message.decode()  # Converting bytes to string
            print(decrypted_message)
            log_message(username, decrypted_message, status="SENT")

        elif 'unencrypted message' in message:  # If the message contains an 'unencrypted message'
            print(message['unencrypted message'])
            log_message(username, message['unencrypted message'], status="SENT")

    sock_tcp.close()


def run():
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.bind(('', 6001))
    sock_tcp.listen(1)
    while True:
        client, address = sock_tcp.accept()
        client_handler = threading.Thread(target=handle_client, args=(client, address,))
        client_handler.start()
        client_handler.join()  # Wait for the thread to finish execution
        client.close()  # Close the client socket after use


if __name__ == "__main__":
    run()
