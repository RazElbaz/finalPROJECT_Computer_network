import hashlib
import os
import pickle
import socket
import threading
import queue
import time
from new_thread_user import new_thread_user
# the standard address for IPv4 loopback traffic
IP = '127.0.0.1'
# use this port for initial HTTP communication between a remote management console and the SEPM to display the login screen
Port = 55000
EPS = 0.01

class Server(threading.Thread):
    def __init__(self, ip, port):
        # The Daemon Thread does not block the main thread from exiting and continues to run in the background
        super().__init__(daemon=True, target=self.listen)
        self.ip = ip
        self.port = port
        self.buffer_size = 2048
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_file = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_file.bind(('127.0.0.1', 1111))
        try:
            self.socket_file.listen(15)
        except:
            pass

        # Socket setup
        self.shutdown = False
        self.lock = threading.Lock()
        try:
            # bind function binds the socket to the address and port number specified in address
            self.sock.bind((ip, port))
            # The listen() function shall mark a connection-mode socket, specified by the socket argument, as accepting connections.
            self.sock.listen(15)
            # setblocking() method to change the blocking flag for a socket
            self.sock.setblocking(False)
            self.start()
        except:
            self.shutdown = True
        # list of queue, for every sock we have a queue of message {sock, queue}
        self.MessageList = {}
        # list of connection
        self.connection_list = []
        # list of the names of the users, the connection {name, sock}
        self.users_list = {}
        self.lock = threading.Lock()
        while not self.shutdown:
            pass


    # listens for new connections
    def listen(self):
        # the server windows before clients conneced
        print('Waiting for connections...')
        while True:
            with self.lock:
                try:
                    # The return value is a pair (conn, address) where conn is a new socket object usable to send and receive data on the connection,
                    # and address is the address bound to the socket on the other end of the connection.
                    conn, address = self.sock.accept()
                except:
                    time.sleep(0.01)
                    continue

            # setblocking() is method to change the blocking flag for a socket
            conn.setblocking(False)
            # if the connected is new connected we add the connected to the list
            if conn not in self.connection_list:
                self.connection_list.append(conn)
            # crate a queue to the connection
            self.MessageList[conn] = queue.Queue()
            # for every connection we rate a thread
            new_thread_user(self, conn, address)

    # update the list of the names of the users
    def update_users_list(self):
        users = 'login'
        # add all the name of the users
        for user in self.users_list:
            users += ';' + user
        # add the More options of dests like send to everyone , or Request things from the server
        users += ';Everyone' + ';server-list' + ';server-file' + '\n'
        # Computers use encoding schemes to store and retrieve meaningful information as data.
        users = users.encode('utf-8')
        for conn, connections in self.MessageList.items():
            # add to the queue
            connections.put(users)

    # send the list of the files that the clients can request from the server
    def send_list_file(self):
        my_file = os.listdir()
        return my_file

    def send_file(self, the_name_of_file):
        start = time.perf_counter()
        try:
            #waiting for message from the client with the name of the file
            message, address =  self.socket_file.recvfrom(5120)
            # counter to Promote in 1
            counter = 1
            # The sequence number is a counter used to keep track of every byte sent outward by a host
            sequence_number = 1
            # Go back N is an implementation of Sliding Window Protocol
            window_size = 7
            # list of bites that gonna send
            window = []
            # the list of all the files
            files = os.listdir()
            # if the file are available
            if the_name_of_file in files:
                # get the size of the file
                file_size = os.path.getsize(the_name_of_file)
                # the file size less then 64KB
                if file_size <= 65536:
                    # send to the client that the size of the file
                    m = "available" + " " + str(file_size)
                    self.socket_file.sendto(m.encode(), address)
                    f = open(the_name_of_file, 'rb')
                    data = f.read(500)
                    # flag to ending send file
                    flag = False
                    time_of_packet = time.time()
                    while not flag or window:
                        # if there is more bites to send in the window
                        if (sequence_number < counter + window_size) and not flag:
                            # Create a package where we will add the UDP layer
                            send_packt = []
                            # add the sequence_number at the first place
                            send_packt.append(sequence_number)
                            # add the data
                            send_packt.append(data)
                            # The MD5, defined in RFC 1321, is a hash algorithm to turn inputs into a fixed 128-bit (16 bytes) length of the hash value
                            hash = hashlib.md5()
                            # The dumps() method of the Python pickle module serializes a python object hierarchy and returns the bytes object of the serialized object
                            hash.update(pickle.dumps(send_packt))
                            # Add the amount of bits of the file to the last location of the list
                            send_packt.append(hash.digest())
                            # send the packet
                            self.socket_file.sendto(pickle.dumps(send_packt), address)
                            # Coefficient for moving to the next package
                            sequence_number = sequence_number + 1
                            if not data:
                                flag = True
                            # Add the package to the sending window plus the information we added
                            window.append(send_packt)
                            data = f.read(500)
                        try:
                            packet, serv_address =  self.socket_file.recvfrom(5120)
                            recv_ACK = []
                            # The pickle module implements binary protocols for serializing and de-serializing a Python object structure.
                            recv_ACK = pickle.loads(packet)
                            # We put the size of the package in the last location
                            packet_size = recv_ACK[-1]
                            del recv_ACK[-1]
                            # The MD5, defined in RFC 1321, is a hash algorithm to turn inputs into a fixed 128-bit (16 bytes) length of the hash value
                            hash = hashlib.md5()
                            # The dumps() method of the Python pickle module serializes a python object hierarchy and returns the bytes object of the serialized object
                            hash.update(pickle.dumps(recv_ACK))
                            # now we will check whether the size of the received package is the size of the package sent
                            if packet_size == hash.digest():
                                # check if there is more bits to send
                                while recv_ACK[0] > counter and window:
                                    time_of_packet = time.time()
                                    # the packet send, so we delete her from the window
                                    del window[0]
                                    counter = counter + 1


                            else:
                              print("EROR!")


                        except:
                            # check the time out
                            if time.time() - time_of_packet > EPS:
                                # if there is time out, we send the window again
                                for i in window:
                                    self.socket_file.sendto(pickle.dumps(i), address)


                    # read the bytes
                    bytes_read = open(the_name_of_file, "rb").read()
                    y = file_size - 1
                    #b'z'
                    last_n_bytes = str(bytes_read[y:])
                    # take the last bit
                    #'z'
                    bit = last_n_bytes[1:]
                    u = "available" + " " + str(bit)
                    self.socket_file.sendto(u.encode(), address)
                    end = time.perf_counter()
                    time_send = end - start
                    print('********the file send, the value of the last byte is: ' + str(bit) + '********')
                    print('The time that take to send: ' + str(time_send) + ' seconds')


                else:
                    # if the file size bigeer than 64KB
                    data = "large" + " " + the_name_of_file
                    self.socket_file.sendto(data.encode(),address)
                    print('the file is large')



            else:
                # if the file is not exist
                data = "not" + " " + the_name_of_file
                self.socket_file.sendto(data.encode(),address)
                print('the file is not exist')


        except:
            pass




# Create new server with (IP, port)
if __name__ == '__main__':
    server = Server(IP, Port)