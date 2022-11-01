# Import socket module
import socket


def Main():
    # local host IP '127.0.0.1'
    host = '127.0.0.1'

    # Define the port on which you want to connect
    port = 12345

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to server on local computer
    s.connect((host, port))
    # message you send to server
    file = open(r"C:\Users\tec05\PycharmProjects\pythonProject4\chucknorris.jpg", "rb")
    image_data = file.read(2048)

    while image_data:
        # message sent to server
        s.send(image_data)
        image_data = file.read(2048)

    file.close()
    # close the connection
    s.close()


if __name__ == '__main__':
    Main()