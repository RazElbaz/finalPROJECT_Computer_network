import threading
import select


class new_thread_user(threading.Thread):
    def __init__(self, serv, conn, address):
        # The Daemon Thread does not block the main thread from exiting and continues to run in the background
        super().__init__(daemon=True, target=self.run)
        # the server
        self.serv = serv
        # the connection
        self.socket = conn
        # the address bound to the socket on the other end of the connection.
        self.address = address
        self.buffer_size = 2048
        self.login = ''
        self.start()

    def run(self):
        print(str(self.address) + ' is connected')
        # print in the server windows the details of the client that connected
        while [self.socket]:
            try:
                # select() function is a direct interface to the underlying operating system implementation. It monitors sockets, open files, and pipes
                ready_read, ready_write, exceptional = select.select([self.socket], [self.socket], [self.socket])
            except:
                self.Disconnect_user()
                break

            # if we want to send data
            if self.socket in ready_write:
                # if the queue is not empty get the data and send
                if not self.serv.MessageList[self.socket].empty():
                    data = self.serv.MessageList[self.socket].get()
                    try:
                        self.socket.send(data)
                    except:
                        self.Disconnect_user()
                        break

            # if we want to recv data
            if self.socket in ready_read:
                try:
                    # The recv() function of socket module in Python receives data from sockets
                    data = self.socket.recv(self.buffer_size)
                except:
                    self.Disconnect_user()
                    break

                # process data received by client's socket#
                shutdown = False
                # if we recv the data
                if data:
                    # The decoding of a message is how an audience member is able to understand
                    message = data.decode('utf-8')
                    # we split the message and go through the parts in it, to who, from where, what the message is
                    message = message.split(';', 3)
                    # part[0] = about what we notify message / login
                    # part[1]=from where
                    # part[2] = to who
                    # part[3] = the data

                    # process of log in
                    if message[0] == 'login':
                        # the name of the user that login
                        curr_name = message[1]
                        # check of the name  already exist
                        while message[1] in self.serv.users_list:
                            # if the name  already exist add * to the name
                            message[1] += '*'
                        if curr_name != message[1]:
                            # alarm in the chat that the name has changed
                            alarm = 'msg;server;' + message[1] + ';name ' + curr_name + ' already exist, your name has changed to: ' + message[1] + '\n'
                            # put the alarm in the queue, the client see the alarm in the chart windows
                            self.serv.MessageList[self.socket].put(alarm.encode('utf-8'))

                        self.login = message[1]
                        # add for the users list the socket
                        self.serv.users_list[message[1]] = self.socket
                        print('The User nickname is ' + message[1])
                        # alarm that new client connected to the server
                        data = 'message;' + 'server' + ';' + 'Everyone' + ';' + self.login + ' is log in' + '\n'
                        # send to everyone the alarm
                        for connect, connection_queue in self.serv.MessageList.items():
                            if connect != self.socket:
                                # add to the queue the alarm
                                connection_queue.put(data.encode('utf-8'))

                        # Update list of users
                        self.serv.update_users_list()


                    # if message[0] is a meassage and the message send to another user
                    elif message[0] == 'message' and message[2] != 'Everyone':
                        msg = data.decode('utf-8') + '\n'
                        # if that a really message and not a request to the server
                        if message[2] != 'server-list' and message[2] != 'server-file':
                            # take the connection of the dest
                            dest = self.serv.users_list[message[2]]
                            # add for the queue the message
                            self.serv.MessageList[dest].put(msg.encode('utf-8'))

                        # if that a request to the server
                        if message[2] == 'server-list':
                            # print on the server windows the request to the list
                            print('********' + message[1] + ':please send me the list of files********')

                            # print on the chat windows
                            text = 'sending the list... ' + '\n'
                            text1 = 'message;' + 'server' + ';' + message[1] + ';' + text
                            dest = self.serv.users_list[message[1]]
                            self.serv.MessageList[dest].put(text1.encode('utf-8'))

                            # print the list on the chat windows
                            names = self.serv.send_list_file()
                            for n in names:
                                file = str(n) + "\n"
                                data = 'message;' + 'server' + ';' + message[1] + ';' + file
                                dest = self.serv.users_list[message[1]]
                                self.serv.MessageList[dest].put(data.encode('utf-8'))
                            print('********the list send ********')
                            data1 = 'list;' + message[1] + ";" + message[2] + ";" + message[3]
                            self.socket.send(data1.encode())

                        # if that a request to the server
                        if message[2] == 'server-file':
                            # print on the server windows the request to the file
                            print('********' + message[1] + ':please send me the file: ' +message[3]+'********')
                            data1 ='file;' + message[1]+";"+ message[2]+";" + message[3]
                            #run the recv function
                            self.socket.send(data1.encode())
                            # run the send file function
                            self.serv.send_file(message[3])


                    # the message send to everyone
                    elif message[0] == 'message' and message[2] == 'Everyone':
                        msg = data.decode('utf-8') + '\n'
                        # send everyone the message
                        for connect, connection_queue in self.serv.MessageList.items():
                            if connect != self.socket:
                                # add to the queue the message
                                connection_queue.put(msg.encode('utf-8'))
                # process of log out
                else:
                    shutdown = True

                # shutdown if the client left
                if shutdown:
                    self.Disconnect_user()
                    break

            if self.socket in exceptional:
                self.Disconnect_user()

    # the function of disconnected
    def Disconnect_user(self):
        # The format() method formats the specified value(s) and insert them inside the string's placeholder.
        # print on the server windows
        print('The User {} has logged out.'.format(self.login))
        # a new alarm that client is log out
        data = 'message;' + 'server' + ';' + 'Everyone' + ';' + self.login + ' is log out' + '\n'
        # send to everyone the alarm
        for connect, connection_queue in self.serv.MessageList.items():
            if connect != self.socket:
                # add tha alarm to the queues
                connection_queue.put(data.encode('utf-8'))
        # remove the connection
        if self.socket in self.serv.connection_list:
            self.serv.connection_list.remove(self.socket)
        # removes the socket(conn) from the MessageList, remove the queue
        if self.socket in self.serv.MessageList:
            del self.serv.MessageList[self.socket]
        # removes the user from the users_list
        if self.login in self.serv.users_list:
            del self.serv.users_list[self.login]
        self.socket.close()
        self.serv.update_users_list()