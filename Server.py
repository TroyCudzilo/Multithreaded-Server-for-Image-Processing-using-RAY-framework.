import io
import os
import socket
import numpy as np
import psutil
import scipy
from scipy.ndimage import gaussian_filter
import ray
from _thread import *
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import time
import cv2 as cv

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 12345
ThreadCount = 0
try:
    s.bind(('', port))
except socket.error as e:
    print(str(e))
print('Socket is listening..')
s.listen(5)

# Count number of cpu cores available to work and print.
num_cpus = psutil.cpu_count(logical=False)
print('Using {} cores.'.format(num_cpus))

# Initialize Ray for all relevant processes. Ray workers are separate processes
# as opposed to thread because support for multi-threading in Python
# is very limited due to the global interpreter lock.
ray.init(num_cpus=num_cpus)


def multi_threaded_client(c):
    # initialize buffer size for image bytes and string bytes. 4096 for Image, 1024 for client choice.
    BUFFER_SIZE = 4096
    BUFFER_SIZE_CHOICE = 1024

    # initialize byte stream and receive image data from client.
    file_stream = io.BytesIO()
    recv_data = c.recv(BUFFER_SIZE)

    # loop to write image bytes being received to stream.
    while recv_data:
        file_stream.write(recv_data)
        recv_data = c.recv(BUFFER_SIZE)

        # flag to let server know that all bytes as been sent.
        if recv_data == b"%IMAGE_COMPLETED%":
            break

    # Initialize byte stream for client choice of filter. Decodes in order to be interpreted.`
    filter_choice = io.BytesIO()
    filter_choice = c.recv(BUFFER_SIZE_CHOICE)
    filter_choice = filter_choice.decode()

    # Fun magic starts here.
    if filter_choice == '3':
        # Parallelism with tasks. f is a "remote function" (a function that can be executed remotely and asynchronously)
        # Takes in image array and any filter as arguments and returns the convolved (joint, merge)
        # of the two 2-dimensional arrays
        @ray.remote
        def f(im, random_filter):
            # Do image processing. Need more random filters than just blur
            gaussian_filter(im, sigma=7)
            return scipy.signal.convolve2d(im, random_filter)[::5, ::5]

        # store image file into numpy array
        arr_image = np.asarray(file_stream)

        # Time the code below. By calling ray.put(arr_image), the large array is stored in shared memory and can be
        # accessed by all the worker processes without creating copies. This works not just with arrays but
        # also with objects that contain arrays (like lists of arrays). When the workers execute the f task,
        # the results are again stored in shared memory. Then, when the script calls ray.get([...]), it creates
        # numpy arrays backed by shared memory without having to deserialize or copy the values.

        filters = [np.random.normal(size=(4, 4)) for _ in range(num_cpus)]

        durations1 = []
        start_time = time.time()
        for _ in range(10):
            arr_image = np.zeros((3000, 3000))
            image_id = ray.put(arr_image)

            # Say you are using multiprocessing with 2 workers, and you do pool.map(f, range(10000)). Then
            # multiprocessing will assign one task to each worker for a total of two tasks. The first worker will
            # execute f on range(5000), and the second worker will execute f on range(5000, 10000). In contrast,
            # with Ray, if you do ... ray.get([f.remote(i) for i in range(10000)]), Ray will submit 1000 separate
            # tasks. The equivalent in Ray to pool.map is to instead create one task per worker,
            # where each task executes a batch of work. In this case, 2.
            ray.get([f.remote(image_id, filters[i]) for i in range(num_cpus)])

        duration1 = time.time() - start_time
        durations1.append(duration1)
        print('Numerical computation workload took {} seconds.'.format(duration1))

        image = Image.fromarray(arr_image.astype('uint8'), 'RGB')
        image.save('server_file.jpg', format='JPEG')

    if filter_choice == '1':
        # Using PIL, perform blur on image
        start_time = time.time()

        image_blur = Image.open(file_stream)
        image_blur = image_blur.filter(ImageFilter.GaussianBlur(radius=10))
        image_blur.save('server_file.jpg', format='JPEG')

        durations1 = []
        duration1 = time.time() - start_time
        durations1.append(duration1)
        print('Numerical computation workload took {} seconds.'.format(duration1))

        # Using PIL, perform invert an image.
    if filter_choice == '2':
        start_time = time.time()

        image_invert = Image.open(file_stream)
        image_invert = ImageOps.invert(image_invert)
        image_invert.save('server_file.jpg', format='JPEG')

        durations1 = []
        duration1 = time.time() - start_time
        durations1.append(duration1)
        print('Numerical computation workload took {} seconds.'.format(duration1))

    # Open edited image on server side and read binary to send to client.
    with open('server_file.jpg', "rb") as file:
        file_data = file.read(BUFFER_SIZE)

        while file_data:
            c.send(file_data)
            file_data = file.read(BUFFER_SIZE)

    # send client flag to let them know image has completed sending.
    c.send(b'%IMAGE_COMPLETED%')
    # unlink the original image from the server so more can be sent.
    os.unlink('server_file.jpg')
    # close connection
    c.close()


while True:
    c, address = s.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(multi_threaded_client, (c,))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
s.close()
