import os
import time
import unittest

from server import Server


class Test_server(unittest.TestCase):

    def  test_connection(self):
       s1 = Server('127.0.0.1', 55000)
       self.assertEqual(s1.ip,'127.0.0.1')
       self.assertEqual(s1.port, 55000)





