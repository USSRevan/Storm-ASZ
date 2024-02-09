import numpy as np
import cv2 as cv

cameraLeft_index = 2
cameraRight_index = 0

print("Openning left camera...")
camLeft = cv.VideoCapture(cameraLeft_index)
camLeft.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
camLeft.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
camLeft.set(cv.CAP_PROP_AUTOFOCUS, 0)
if not camLeft.isOpened():
    print("Cannot open Left Camera")
    exit()

print("Openning right camera...")
camRight = cv.VideoCapture(cameraRight_index)
camRight.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
camRight.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
camRight.set(cv.CAP_PROP_AUTOFOCUS, 0)
if not camRight.isOpened():
    print("Cannot open Left Camera")
    exit()
    
    
while True:
    l_ret, leftFrame = camLeft.read()
    r_ret, rightFrame = camRight.read()
    
    if ((not l_ret) or (not r_ret)):
        print("Can't receive frame (stream end?). Exiting ...")
        break
    
    cv.imshow('Left Camera', leftFrame)
    cv.imshow('Right Camera', rightFrame)
    if cv.waitKey(1) == ord('q'):
        break

camLeft.release()
camRight.release()

cv.destroyAllWindows()