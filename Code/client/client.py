import hashlib
import pickle
import socket
import time
import select
import queue
from gui import *

# the standard address for IPv4 loopback traffic
IP = '127.0.0.1'
# use this port for initial HTTP communication between a remote management console and the SEPM to display the login screen
Port = 55000


class Client(threading.Thread):

    def __init__(self, ip, port):
        super().__init__(daemon=True, target=self.run)
        self.ip = ip
        self.port = port
        self.buffer_size = 1024
        # queue of data
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        # the src
        self.login = ''
        # the dest
        self.target = ''
        # the other user that connect to the server
        self.users_list = []

        # try to conectted to the server
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((str(self.ip), int(self.port)))
        except ConnectionRefusedError:
            self.connect_server = False
        self.connect_server = True

        # if the client conected to the server open the client gui
        if self.connect_server:
            self.gui = GUI(self)
            self.start()
            self.gui.start()

    # check the sock and use the select function
    def run(self):
        while [self.sock]:
            try:
                # select() function is a direct interface to the underlying operating system implementation. It monitors sockets, open files, and pipes
                ready_read, ready_write, exceptional = select.select([self.sock], [self.sock], [self.sock])
            except:
                self.sock.close()
                break
            # if we want to send data
            if self.sock in ready_write:
                # if the queue is not empty get the date
                if not self.queue.empty():
                    data = self.queue.get()
                    # send the message
                    with self.lock:
                        try:
                            self.sock.send(data)
                        except:
                            self.sock.close()
                    # We can call this method each time an item is retrieved and processed from the queue.
                    # It'll mark that item as processed internally.
                    # It'll free thread waiting on Queue.join()
                    self.queue.task_done()
                else:
                    # if the queue is empty
                    time.sleep(0.01)

            # if we want to recv data
            if self.sock in ready_read:
                with self.lock:
                    try:
                        # The recv() function of socket module in Python receives data from sockets
                        data = self.sock.recv(self.buffer_size)
                    # close the socket if we cant recv
                    except socket.error:
                        self.sock.close()
                        break

                # process_received_data#
                # if we recv the data
                if data:
                    # The decoding of a message is how an audience member is able to understand
                    message = data.decode('utf-8')
                    message = message.split('\n')
                    for part in message:
                        # if the message is not empty
                        if part != '':
                            # part[0] = about what we notify message / login
                            # part[1]=from where
                            # part[2] = to who
                            # part[3] = the data
                            # we split the message and go through the parts in it, to who, from where, what the message is
                            part = part.split(';')
                            # if the part[0] is a file
                            if part[0] == 'file':
                                self.recv(part[3])
                            # if the part[0] is a list
                            if part[0] == 'list':
                                print('I received the list ')
                            # if the part[0] is a message
                            elif part[0] == 'message':
                                # part[1]=who send and part[3]= the message
                                # print on the chat windows thw message
                                ms = part[1] + ' : ' + part[3] + '\n'
                                self.gui.show(ms)

                                # send to another user (not for myself and not for everyone)
                                if part[2] != self.login and part[2] != 'Everyone':
                                    self.login = part[2]


                            # if that is alarm on user login
                            elif part[0] == 'login':
                                # update users list
                                self.gui.chat_window.update_users_list(part[1:])



            if self.sock in exceptional:
                print('Error!')
                GUI.display_alert('Server error')
                self.sock.close()
                break

    # function that connected to the gui
    def inform(self, action, action_type):
        # notify on the server windows
        self.queue.put(action)
        # close the socket
        if action_type == "logout":
            self.sock.close()

# download the file from the server
    def recv(self, data):
        try:
                sum_size = 0
                self.socket_file = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket_file.settimeout(3)
                message = self.login + " " + data
                the_name_of_file = data
                # The sequence number is a counter used to keep track of every byte sent outward by a host
                sequence_number = 1
                EOF = False
                time_of_packet = time.time()
                # send to the server the name of the client and the name of the file
                self.socket_file.sendto(message.encode(), ('127.0.0.1', 1111))
                # message from the server if the file is available
                size, address = self.socket_file.recvfrom(5120)
                if size.decode().split()[0] == "available":
                    f = open(the_name_of_file, "wb")
                    while not EOF:
                        try:
                            self.rcev_packet = []
                            packet, client_address = self.socket_file.recvfrom(5120)
                            # The pickle module implements binary protocols for serializing and de-serializing a Python object structure.
                            self.rcev_packet = pickle.loads(packet)
                            # We put the size of the package in the last location
                            size_packet = self.rcev_packet[-1]
                            del self.rcev_packet[-1]
                            # The MD5, defined in RFC 1321, is a hash algorithm to turn inputs into a fixed 128-bit (16 bytes) length of the hash value
                            hash = hashlib.md5()
                            # The dumps() method of the Python pickle module serializes a python object hierarchy and returns the bytes object of the serialized object
                            hash.update(pickle.dumps(self.rcev_packet))
                            # now we will check whether the size of the received package is the size of the package sent
                            if size_packet == hash.digest():
                                sum_size = sum_size + (len(self.rcev_packet[1]))
                                # Check whether the number sequence obtained is a number sequence that he expected to receive
                                if self.rcev_packet[0] == sequence_number:
                                    if self.rcev_packet[1]:
                                        f.write(self.rcev_packet[1])
                                    else:
                                        EOF = True
                                    sequence_number = sequence_number + 1
                                    send_packet = []
                                    send_packet.append(sequence_number)
                                    # The MD5, defined in RFC 1321, is a hash algorithm to turn inputs into a fixed 128-bit (16 bytes) length of the hash value
                                    hash = hashlib.md5()
                                    # The dumps() method of the Python pickle module serializes a python object hierarchy and returns the bytes object of the serialized object
                                    hash.update(pickle.dumps(send_packet))
                                    send_packet.append(hash.digest())
                                    # send to the server the ack
                                    self.socket_file.sendto(pickle.dumps(send_packet), (client_address[0], client_address[1]))

                                else:
                                    # Sending the sequence number and then the server will know that this is not the package he wanted to send, and will send the package again
                                    send_packet = []
                                    send_packet.append(sequence_number)
                                    # The MD5, defined in RFC 1321, is a hash algorithm to turn inputs into a fixed 128-bit (16 bytes) length of the hash value
                                    hash = hashlib.md5()
                                    hash.update(pickle.dumps(send_packet))
                                    send_packet.append(hash.digest())
                                    self.socket_file.sendto(pickle.dumps(send_packet), (client_address[0], client_address[1]))

                            else:
                                print("EROR!")

                        except:
                            if EOF:
                                if time.time() - time_of_packet > 3:
                                    break

                    #recv the last byte
                    s, address = self.socket_file.recvfrom(5120)
                    bit = s.decode().split()[1]
                    print('I received the file, the lest byte:' + bit + '')
                    self.socket_file.close()


                # if the file size bigeer than 64KB
                if size.decode().split()[0] == "large":
                    print('the file is too large')
                    pass

                # if the file is not exist
                if size.decode().split()[0] == "not":
                    print('the file does not exist')
                    pass


        except:
            pass


# Create new client
if __name__ == '__main__':
    Client(IP, Port)