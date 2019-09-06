# threaded version of the brightfield controller
# this has support for independent timed operation of the camera and magnet functions

import threading
import Queue
import time
import csv
import numpy as np
import imageio
import brightfield as b
from tqdm import tqdm


def actcam(pic_que, time_que, camera_object, frame0):
    n_frame, pictime = b.takepic(camera_object, frame0)
    pic_que.put(n_frame)
    time_que.put(pictime)

def multiframe(number_of_frames, period, collated_filepath, collated_filename):
    pic_que = Queue.Queue()
    time_que = Queue.Queue()
    vimba_cam, camera_object, frame0 = b.open_camera()
    for i in tqdm(range(number_of_frames)):
        camera = threading.Thread(name='camera', target=actcam, args=(pic_que, time_que, camera_object, frame0))
        camera.start()
        time.sleep(period)
        camera.join()
    b.close_camera(vimba_cam, camera_object)

    with imageio.get_writer(collated_filepath + collated_filename + '.tiff') as stack:
        with open(collated_filepath + collated_filename + '_time.csv', 'ab') as f:
            writer = csv.writer(f)
            while not pic_que.empty():
                stack.append_data(pic_que.get())
                writer.writerow([time_que.get()])
