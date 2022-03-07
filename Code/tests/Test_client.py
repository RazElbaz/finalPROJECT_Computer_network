import unittest

from client import Client


class Test_client( unittest.TestCase):

    c1 = Client('127.0.0.1', 55000)
    m1 = c1.sock.recv(1024)
    def test_connection(self, c=c1,m=m1):
        curr =m.decode().split(';')[4]
        m1=' b'+'login;'+str(c.login)+';Everyone;server-list;server-file\n'
        curr1 = m1.split(';')[4]
        self.assertEqual(curr1,curr)
        curr = m.decode().split(';')[3]
        curr1 = m1.split(';')[3]
        self.assertEqual(curr1, curr)
        curr = m.decode().split(';')[2]
        curr1 = m1.split(';')[2]
        self.assertEqual(curr1, curr)
        c.sock.close()

    def test_login(self, c=c1,m=m1):
        c.login = m.decode().split(';')[1]
        curr = m.decode().split(';')[1]
        curr1 = c.login
        self.assertEqual(curr1, curr)
        c.sock.close()

    def test_target(self, c=c1,m=m1):
        c.target = m.decode().split(';')[2]
        curr = m.decode().split(';')[2]
        curr1 = c.target
        self.assertEqual(curr1, curr)
        c.sock.close()

    def test_ip(self, c=c1):
        self.assertEqual(c.ip, '127.0.0.1')
        c.sock.close()

    def test_port(self, c=c1):
        self.assertEqual(c.port, 55000)
        c.sock.close()

