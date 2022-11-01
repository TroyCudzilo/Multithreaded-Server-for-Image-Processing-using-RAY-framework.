# import socket programming library
import socket
import threading
from PIL import Image, ImageFilter
# import thread module
from _thread import *

print_lock = threading.Lock()


# thread function
def threaded(c):
    file = open('new_image.jpg', "wb")
    image_chunk = c.recv(2048)

    while image_chunk:
        file.write(image_chunk)
        image_chunk = c.recv(2048)
        if not image_chunk:
            break

    with Image.open(file) as im:
        im_blurred = im.filter(filter=ImageFilter.BLUR)



        # if not image_chunk:
        #      with Image.open(file) as im:
        #       im_blurred = im.filter(filter=ImageFilter.BLUR)
        # #     # lock released on exit
        # #     print_lock.release()
        # #     break
        #
        # # # reverse the given string from client
        #
        # # # send back reversed string to client
    c.send(im_blurred)

    file.close()
    # connection closed
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
    s.close()


if __name__ == '__main__':
    Main()
