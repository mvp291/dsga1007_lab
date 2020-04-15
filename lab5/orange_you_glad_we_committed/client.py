import socket
import sys
import time
import random

def receive():
    msg = ''
    while '<EOM>' not in msg:
        chunk = s.recv(1024)
        if not chunk: break
        if chunk == '':
            raise RuntimeError("socket connection broken")
        msg += chunk
    msg = msg[:-5]
    return msg
  
if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', int(sys.argv[1])))
    print receive()
    s.send(str(sys.argv[2]))
    print receive()
    while(1):
        s.send(str(random.randint(0, 4)))
        inc = receive()
        if not inc:
            break
        print inc
 #       time.sleep(1)
