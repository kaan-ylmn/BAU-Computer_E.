import os
import json
import pyDes
import base64
import socket
import threading
from datetime import datetime, timedelta

peers = {}  # Dictionary to store peers
log = []  # List to store chat history
# Create a global lock
log_lock = threading.Lock()

print("Welcome to CMP2204 LAN Party! \nWe are going to initiate chat sessions with other users!")

with open("chat_history.txt", "w"):
    pass


def get_valid_input(prompt, valid_options, lower=True):  # Function to get a valid input from the user
    while True:
        response = input(prompt)
        if lower:
            response = response.lower()
        if response in valid_options:
            return response
        print(f"Invalid answer. Please choose one of the following options: {', '.join(valid_options)}")


def load_peers():
    global peers
    with open("online_peers.txt", "r") as peer_file:  # Loading the peers from the file
        peers = json.load(peer_file)
    now = datetime.now()
    for address, info in list(peers.items()):  # Using list to avoid RuntimeError: dictionary changed size during iteration
        last_seen = datetime.strptime(info['last_seen'], "%Y-%m-%d %H:%M:%S")
        difference = now - last_seen
        if difference > timedelta(minutes=15):
            del peers[address]
        elif difference <= timedelta(seconds=10):
            info['status'] = 'Online'
        else:
            info['status'] = 'Away'


def log_message(username, message, status="RECEIVED"):
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


def initiate_chat():  # Function to initiate a chat session with another user
    load_peers()
    online_users = [info['username'] for info in peers.values() if info['status'] == 'Online']
    selected_user = get_valid_input("Enter the name of the user to chat with: ", online_users, lower=False)

    secure = get_valid_input("Would you like to make this chat more secure (yes/no)? ", ["yes", "no"])
    secure = secure == "yes"

    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    for address, info in peers.items():
        if secure:  # If the chat is secure
            public_divisor = 23
            public_prm = 5
            while True:
                try:
                    private_key = int(input("Enter a number between 1 and 23: "))
                    if 1 <= private_key <= 23:
                        break
                    else:
                        print("Invalid number. Please enter a number between 1 and 23.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            shared_key = str((public_prm ** private_key) % public_divisor).encode()
            try:
                sock_tcp.bind(('', 0))
                sock_tcp.connect((address, 6001))
                sock_tcp.send(json.dumps({'key': str(shared_key)}).encode())
                response = json.loads(sock_tcp.recv(2048).decode())
                other_user_shared_key = int(response['key'][2:-1])
                final_key = str((other_user_shared_key ** private_key) % public_divisor).encode()
                final_key = base64.urlsafe_b64encode(final_key)
                cipher_suite = pyDes.triple_des(final_key.ljust(24))

                message = input("Enter your message: ")
                encrypted_message = cipher_suite.encrypt(message.encode(), padmode=2)
                encrypted_message = base64.b64encode(encrypted_message).decode()
                sock_tcp.send(json.dumps({'encrypted message': encrypted_message}).encode())
                log_message(selected_user, encrypted_message, status="RECEIVED")

            except socket.error as e:
                print("Error: Could not establish a connection with the specified user. Exception:", e)
                print("Local port:", sock_tcp.getsockname()[1])
            finally:
                sock_tcp.close()

        else:  # If the chat is not secure
            message = input("Enter your message: ")
            try:
                sock_tcp.bind(('', 0))
                sock_tcp.connect((address, 6001))
                sock_tcp.send(json.dumps({'unencrypted message': message}).encode())
                log_message(selected_user, message, status="RECEIVED")
            except socket.error as e:
                print("Error: Could not establish a connection with the specified user. Exception:", e)
                print("Local port:", sock_tcp.getsockname()[1])
            finally:
                sock_tcp.close()
        break


def run():
    while True:
        action = get_valid_input("What would you like to see? (Users, Chat, History, Exit): ", ["users", "chat", "history", "exit"])

        if action == 'users':
            load_peers()
            for info in peers.values():
                print(f"{info['username']} ({info['status']})")
        elif action == 'chat':
            initiate_chat()
        elif action == 'history':
            if not os.path.exists("chat_history.txt"):
                open("chat_history.txt", 'w').close()
            with open("chat_history.txt", "r") as log_file:
                print(log_file.read())
        elif action == 'exit':
            print("Thank you for using our code, see you later!")
            break


if __name__ == "__main__":
    run()
