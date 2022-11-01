# import socket programming library
import socket
import threading
import io
from PIL import Image, ImageFilter

import pathlib
# import thread module
from _thread import *

print_lock = threading.Lock()


# thread function
def threaded(c):

    BUFFER_SIZE = 4096

    file_stream = io.BytesIO()
    recv_data = c.recv(BUFFER_SIZE)

    while recv_data:
        file_stream.write(recv_data)
        recv_data = c.recv(BUFFER_SIZE)
        if recv_data == b"%IMAGE_COMPLETED%":
            break

    image = Image.open(file_stream)
    image = image.filter(ImageFilter.GaussianBlur(radius=10))

    image.save('server_file.jpg', format='JPEG')

    with open('server_file.jpg', "rb") as file:
        file_data = file.read(BUFFER_SIZE)

        while file_data:
            c.send(file_data)
            file_data = file.read(BUFFER_SIZE)

    #send flag
    c.send(b'%IMAGE_COMPLETED%')

    #close connection
    c.close()

def Main():
    host = ""

    # reserve a port on your computer
    # in our case it is 12345 but it
    # can be anything
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket binded to port", port)

    # put the socket into listening mode
    s.listen(5)
    print("socket is listening")

    # a forever loop until client wants to exit
    while True:
        # establish connection with client
        c, addr = s.accept()

        # lock acquired by client
        print_lock.acquire()
        print('Connected to :', addr[0], ':', addr[1])

        # Start a new thread and return its identifier
        start_new_thread(threaded, (c,))


if __name__ == '__main__':
    Main()
