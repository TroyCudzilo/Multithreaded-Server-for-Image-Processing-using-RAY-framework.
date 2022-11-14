# Import socket module
import socket
import os
import io
from PIL import Image, ImageFilter, ImageFile, ImageGrab


def Main():
    # IP of host
    host = '127.0.0.1'

    # Define the port on which you want to connect
    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # prompt client for IP address of server
    ip_input = input('What is the IP address of the server?: ')
    host = ip_input

    # connect to server on local computer
    s.connect((host, port))

    # set buffer size for reading in image and choice
    BUFFER_SIZE = 4096
    BUFFER_SIZE_CHOICE = 1024

    # prompt client for path to image
    file_path = input('Please enter full path to image: ')

    # open client image that they wish to have edited and read binary into stream.
    with open(file_path, "rb") as file:
        file_data = file.read(BUFFER_SIZE)

        while file_data:
            s.send(file_data)
            file_data = file.read(BUFFER_SIZE)

    # flag to let the server know the image has finished sending.
    s.send(b"%IMAGE_COMPLETED%")

    # prompt client to choose a filter to apply to image.
    filter_choice = input('Please choose filter choice: 1) Blur 2) Invert 3) Random: ')
    # Encode the choice. This way we can successfully send to server.
    s.send(filter_choice.encode())

    # # prompt client for parallel (fast) or serial (meh) computation.
    # time_choice = input('Do you want this done fast ... or meh: 3) Fast 4) Meh: ')
    # # Encode the choice. This way we can successfully send to server.
    # s.send(time_choice.encode())

    # Write in the binary being received from server for edited image.
    with open('client_file_edited.jpg', "wb") as file:
        recv_data = s.recv(BUFFER_SIZE)

        # loop to write all bytes in.
        while recv_data:
            file.write(recv_data)
            recv_data = s.recv(BUFFER_SIZE)

            # flag to let client know to stop reading and breaks from loop.
            if recv_data == b"%IMAGE_COMPLETED%":
                break

    # close the connection
    s.close()


if __name__ == '__main__':
    Main()
