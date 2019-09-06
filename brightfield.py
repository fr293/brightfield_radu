from pymba import *
import numpy as np
#import matplotlib.pyplot as plt
import time


def open_camera():
    vimba_cam = Vimba()
    vimba_cam.startup()
    camera_ids = vimba_cam.getCameraIds()
    camera_object = vimba_cam.getCamera(camera_ids[0])
    camera_object.openCamera()
    frame0 = camera_object.getFrame()
    frame0.announceFrame()
    return vimba_cam, camera_object, frame0


def set_exposure(camera_object, exposure_time):
    static_write_register = "10000010000000000000"
    cam1_exp_time_base_no_new = int(np.floor((exposure_time / 0.02)))
    cam1_exp_time_base_no_new_bin = '{0:012b}'.format(cam1_exp_time_base_no_new)
    write_register = hex(int(static_write_register + cam1_exp_time_base_no_new_bin, 2))[2:-1]
    camera_object.writeRegister("F0F0081C", write_register)
    return


def takepic(camera_object, frame0):
    camera_object.startCapture()
    frame0.queueFrameCapture()
    camera_object.runFeatureCommand('AcquisitionStart')
    camera_object.runFeatureCommand('AcquisitionStop')
    frame0.waitFrameCapture()
    camera_object.endCapture()
    n_frame = np.ndarray(buffer=frame0.getBufferByteData(), dtype=np.uint8, shape=(frame0.height, frame0.width))
    # fig, ax = plt.subplots(1, 1)
    # ax.imshow(n_frame, cmap='gray', vmin=0, vmax=255)
    pictime = time.time()
    return n_frame, pictime


def close_camera(vimba_cam, camera_object):
    camera_object.revokeAllFrames()
    camera_object.closeCamera()
    vimba_cam.shutdown()
