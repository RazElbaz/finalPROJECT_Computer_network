import tkinter as tk
import threading
from tkinter import scrolledtext
from tkinter import messagebox

class GUI(threading.Thread):

    def __init__(self, client):
        super().__init__(daemon=False, target=self.run)
        self.client = client
        self.enter_window = None
        self.chat_window = None

    def run(self):
        self.enter_window = EnterWindow(self,  ("Ariel", 10))
        self.chat_window = ChatWindow(self,  ("Ariel", 10))
        self.inform(self.enter_window.login, 'login')
        self.chat_window.run()

    def show(self, message):
        self.chat_window.show(message)
    def send_message(self, message):
        self.client.queue.put(message)
    def set_target(self, target):
        self.client.target = target
    def inform(self, message, action):
        data = action + ";" + message
        data = data.encode('utf-8')
        self.client.inform(data, action)



class Window(object):
    def __init__(self, title, font):
        self.root = tk.Tk()
        self.root.title(title)
        self.font = ("Ariel",10)


#the little window - name window
class EnterWindow(Window):
    def __init__(self, g, font):
        super().__init__("Welcome!", font)
        self.gui = g
        self.label = None
        self.button = None
        self.login = None
        self.entry = None
        self.start()

    def start(self):
        self.CreateWindow()
        self.run()

#the window of poot the name
    def CreateWindow(self):
        # client enter window label
        self.label = tk.Label(self.root, text='Enter your name:', width=25, bg ='pink', font="Ariel")
        self.label.pack(expand=tk.YES)
        # client enter window
        self.entry = tk.Entry(self.root, width=22,font="Ariel")
        self.entry.pack(side=tk.LEFT)
        # the ok button (connect to enter in the keyboard)
        self.entry.bind('<Return>', self.enter)
        self.button = tk.Button(self.root, text='Ok', bg ='lightgray', font="Ariel")
        self.button.pack(side=tk.LEFT)
        # the ok button working with the mouse
        self.button.bind('<Button-1>', self.enter)

    def run(self):
        self.root.mainloop()
        self.root.destroy()

    def enter(self, event):
        self.login = self.entry.get()
        self.root.quit()

# the pink window - the chat window
class ChatWindow(Window):
    def __init__(self, g, font):
        super().__init__("Chat",font)
        self.gui = g
        self.messages_list = None
        self.logins_list = None
        self.entry = None
        self.send_button = None
        self.exit_button = None
        self.lock = threading.Lock()
        # the dest
        self.target = ''
        # the src
        self.login = self.gui.enter_window.login
        self.CreateWindow()

    def CreateWindow(self):
        # Size config
        self.root.geometry('900x500')
        s=tk.N + tk.S + tk.W + tk.E
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=s)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=6)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # main_frame.rowconfigure(1, weight=1)
        # main_frame.rowconfigure(2, weight=5)
        # main_frame.columnconfigure(0, weight=1)
        # main_frame.columnconfigure(1, weight=1)

        # the area of the View messages
        list_messages = tk.Frame(main_frame)
        list_messages.grid(column=0, row=0, rowspan=2, sticky=s)
        self.messages_list = scrolledtext.ScrolledText(list_messages, wrap='word', font="Ariel")
        self.messages_list.configure(state='disabled', bg= 'pink')

        # the area of the names of all the users (and the request to the server)
        list_login = tk.Frame(main_frame)
        list_login.grid(column=1, row=0, rowspan=3, sticky=s)
        self.logins_list = tk.Listbox(list_login, selectmode=tk.SINGLE,bg='lightgray', font="Ariel",exportselection=False)
        # bind the the Mouse clicks
        self.logins_list.bind('<<ListboxSelect>>', self.enter_action)

        # the area of the Write down the message
        message_enter = tk.Frame(main_frame)
        message_enter.grid(column=0, row=2, columnspan=1, sticky=s)
        self.entry = tk.Text(message_enter,bg='lightgray', font="Ariel")
        # bind for the enter in the keybord
        self.entry.bind('<Return>', self.SendEntry)

        # Button widget for sending messages
        buttons = (tk.Frame(main_frame))
        buttons.grid(column=0, row=3, columnspan=2, sticky=s)
        self.send_button = tk.Button(buttons, text='Send',bg='gray', font="Ariel")
        self.send_button.bind('<Button-1>', self.SendEntry)
        # Button for exiting
        self.exit_button = tk.Button(buttons, text='Exit',bg='gray', font="Ariel")
        self.exit_button.bind('<Button-1>', self.exit_event)




        #Where everything will be on the windoes and how much size it will take up
        self.messages_list.pack(expand=tk.YES)
        self.logins_list.pack(expand=tk.YES)
        self.entry.pack(expand=tk.YES)
        self.send_button.pack(side=tk.RIGHT, fill=tk.BOTH, expand=tk.YES)
        self.exit_button.pack(side=tk.RIGHT, fill=tk.BOTH, expand=tk.YES)


        # Protocol for closing window using 'x' button
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing_event)

    def run(self):
        self.root.mainloop()
        self.root.destroy()

    def enter_action(self,event):
        self.target = self.logins_list.get(self.logins_list.curselection())
        self.gui.set_target(self.logins_list.get(self.logins_list.curselection()))

    # process of sending a message
    def SendEntry(self, event):
        text = self.entry.get(1.0, tk.END)
        # if the message is empty
        if text == '\n':
            messagebox.showinfo('EROR', 'Please enter some text before sending')
        # if the message is not empty
        else:
            message = 'message;' + self.login + ';' + self.target + ';' + text[:-1]
            # if that a really message and not a request to the server
            if self.target!= 'server-file' and self.target!='server-list':
                # print on the client (bleck) window
                m = 'from '+self.login + ' to ' +self.target+ ' the message is: '+ text[:-1]
                print(m)
                self.gui.send_message(message.encode('utf-8'))
                self.entry.mark_set(tk.INSERT, 1.0)
                self.entry.delete(1.0, tk.END)

            # if that a request to the server
            if self.target == 'server-file':
                # print on the client (bleck) window
                m = 'waiting for the file.....'
                print(m)
                self.gui.send_message(message.encode('utf-8'))
                self.entry.mark_set(tk.INSERT, 1.0)
                self.entry.delete(1.0, tk.END)

            # if that a request to the server
            if self.target == 'server-list':
                # print on the client (bleck) window
                m = 'waiting for the list.....'
                print(m)
                self.gui.send_message(message.encode('utf-8'))
                self.entry.mark_set(tk.INSERT, 1.0)
                self.entry.delete(1.0, tk.END)

        with self.lock:
            curr='break'
            self.messages_list.configure(state='normal')
            if text != '\n':
                self.messages_list.insert(tk.END, text)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)
        return curr


    def exit_event(self, event):
        self.gui.inform(self.login, 'logout')
        self.root.quit()

    def on_closing_event(self):
        self.exit_event(None)

    def show(self, message):
        with self.lock:
            self.messages_list.configure(state='normal')
            self.messages_list.insert(tk.END, message)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)


    def update_users_list(self, active_users):
        self.logins_list.delete(0, tk.END)
        for user in active_users:
            self.logins_list.insert(tk.END, user)
        self.logins_list.select_set(0)
        self.target = self.logins_list.get(self.logins_list.curselection())
