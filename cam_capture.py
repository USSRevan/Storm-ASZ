import cv2
import time



def cam_init(camIndex=1):
    cam = cv2.VideoCapture(camIndex)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    return cam
    
def take_photo(camera):
    #cam = cv2.VideoCapture(1)
    _, im = camera.read()
    #cropped = im[0:720, 0:640]
    cropped = im
    #del(camera)
    return cropped

def cam_del(camera):
    del(camera)
	
def save_photo(im, image_name):
	cv2.imwrite(image_name, im)
	
def capture(cam, image_name="test-1.jpg"):
    image = take_photo(cam)
    save_photo(image, image_name)

def cam_setFocus(cam, val):
    #cam.set(10, val) # I want to change the focus manually myself
    cam.set(21, 1)
    cam.set(39, 1)
    #cam.set(cv2.CAP_PROP_FOCUS,     0)
    #cam.set(cv2.CAP_PROP_EXPOSURE,  255)

if __name__ == '__main__':
    cam = cam_init()
    
    #cam_setFocus(cam, 0)
    time.sleep(1)    
    for focus in range(0, 5):
        #print("focus = " + str(focus))
        #cam_setFocus(cam, focus)
        im = take_photo(cam)
        print(im.shape) 
        save_photo(im, f'cam_capture_test{focus}.png')
    cam_del(cam)