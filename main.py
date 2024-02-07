from cam_capture import capture, cam_init, cam_del
from qr_scanner import scan_qrcode

import time

L_CAM_INDEX = 0
R_CAM_INDEX = 2
l_camera = None
r_camera = None


def DPRINT(msg):
    print(msg)

######################################################################
########################### Serial UART ##############################
######################################################################

import serial

ser = ""

PORT = "COM4"
UART_SPEED = 115200


def uart_init():
    DPRINT("uart init..")
    ser = serial.Serial(PORT, UART_SPEED)
    return ser
    
def uart_print(msg):
    msg += '\n'
    DPRINT(f'UART << {msg}')
    ser.write(msg.encode('utf-8'))


######################################################################
############# COMMANDS and get CMD AND ORDER from MQTT ###############
######################################################################

from mqtt_msg_center import (mqtt_connect,
                            subscribe_and_handler,
                            mqtt_publish_log,
                            mqtt_start,
                            mqtt_stop)

import mqtt_settings


client = ''

NO_CMD = 0
START_CMD = 1
BREAK_CMD = 2
PAUSE_CMD = 3
CH_ORDER_CMD = 4
SAVE_ORDER_CMD = 5

cmd = None

def reset_cmd():
    global cmd
    cmd = NO_CMD

reset_cmd()


commands = [
    {"cmd": NO_CMD,         "text": "no_cmd"},
    {"cmd": START_CMD,      "text": "start_cmd"},
    {"cmd": BREAK_CMD,      "text": "break_cmd"},
    {"cmd": PAUSE_CMD,      "text": "pause_cmd"},
    {"cmd": CH_ORDER_CMD,   "text": "ch_order_cmd"},
    {"cmd": SAVE_ORDER_CMD, "text": "save_order_cmd"}
]

NO_ORDER_MSG = ""
order_msg = NO_ORDER_MSG


MQTT_ORDER_TOPIC = mqtt_settings.MQTT_PREFIX + 'order'
MQTT_CMD_TOPIC = mqtt_settings.MQTT_PREFIX + 'cmd'


def mqtt_print(msg):
    mqtt_publish_log(client, msg)

def mqtt_on_cmdMsg(client, userdata, msg):
    global cmd
    cmd_text = msg.payload.decode('utf-8')
    print(f"Command '{cmd_text}' from '{msg.topic}'")
    cmd = NO_CMD
    
    for command in commands:
        if cmd_text == command["text"]:
            cmd = command["cmd"]
            break
    
     
def mqtt_on_orderMsg(client, userdata, msg):
    global order_msg
    order_msg = msg.payload.decode('utf-8')
    print(f"Order '{order_msg}' from '{msg.topic}'")


def mqtt_init():   
    print("mqtt init..")
    client = mqtt_connect()
    subscribe_and_handler(client, MQTT_ORDER_TOPIC, mqtt_on_orderMsg)
    subscribe_and_handler(client, MQTT_CMD_TOPIC, mqtt_on_cmdMsg)
    mqtt_start(client)
    return client
    
    
######################################################################
######################################################################


def log(msg):
    print(msg)
    mqtt_print(msg)




def wait_for_answer():
    print("Waiting for answer...")
    line = None 
    while (not line):
        line = ser.readline();
        print(line)
    print("Answer was received!")



storage_cells_num = 5

storage_first_cell_pos_mm = 5
storage_cell_size_mm = 55


y_left_pos = -80
y_home_pos = 0
y_right_pos = 170



def device_pause(time_sec):
    log("Pause order collecting!")
    uart_print(f'G4 S{time_sec}')
    wait_for_answer()


def device_move_x(x):
    uart_print(f'G1 X{x}')
    wait_for_answer()

def device_home_x():
    uart_print('G28 X')
    wait_for_answer()
    
    

def device_move_y(y):
    uart_print(f'G1 Y{y}')
    wait_for_answer()

def device_y_left():
    device_move_y(y_left_pos)

def device_y_right():
    device_move_y(y_right_pos)

def device_home_y():
    uart_print('G28 Y')
    wait_for_answer()




#//U - захват, V - Выдвижение
grip_opened_pos = 180
grip_closed_pos = 0

def device_gripper_open():
    uart_print(f'G1 U{grip_opened_pos}')
    wait_for_answer()
    device_pause(1)
    

def device_gripper_close():
    uart_print(f'G1 U{grip_closed_pos}')
    wait_for_answer()
    device_pause(1)




current_cell = 0

def device_reset():
    uart_print('G69')
    wait_for_answer()


def device_home():
    global current_cell
    log("go home...")
    device_gripper_open()
    device_home_y()
    device_home_x()
    current_cell = 0
    


def convert_cell_to_pos(num):
    pos = 0
    if num == 0:
        pos = 0
    elif num >= 1:
        pos = (storage_first_cell_pos_mm +
            (num - 1) * storage_cell_size_mm)
    return pos


def device_current_cell():
    pos = convert_cell_to_pos(current_cell)
    device_move_x(pos)


def device_next_cell():
    global current_cell
    log("Go to next cell")
    current_cell += 1
    device_current_cell()


    
def device_grab_l_obj():
    device_gripper_open()
    device_pause(1)
    device_y_left()
    device_pause(1)
    device_gripper_close()
    device_pause(1)


def device_grab_r_obj():
    device_gripper_open()
    device_pause(1)
    device_r_left()
    device_pause(1)
    device_gripper_close()
    device_pause(1)

def device_pull_object():
    log("Pull the object")
    device_move_y(0)

def device_release_object():
    log("Release the object")
    device_gripper_open()

def device_break():
    pass






#переделать qr коды

warehouse = ["гайки",
             "винты",
             "шайбы",
             "шпильки",
             "подшипники",
             "линейные направляющие",
             "валы",
             "двигатели",
             "датчики"
]

order = []
collected = []

def reset_order():
    global order
    order = []

def reset_collected_order():
    global collected
    collected = []

def orderlist_to_string(items):
    msg = ', '.join(str(item) for item in items)
    return msg
    

def decode_order():
    global order_msg
    if order_msg != NO_ORDER_MSG:
        log("New order was received!")
        reset_order()
        msg = list(set(order_msg.split(", ")))
        correct_fl = True
        for word in msg:
            if word in collected:
                log(f"Warning! Item '{word}' is already picked up!")
            elif word in warehouse:
                order.append(word)
                log(f"Item '{word}' was added to order list")
            else:
                log(f"Error! Incorrect item '{word}'")
                correct_fl = False
        
        if (not correct_fl):
            log("Warning! One or more order positions were incorrect!")
        
        msg = 'Текущий заказ: ' + orderlist_to_string(order)
        log(msg)
        order_msg = NO_ORDER_MSG
        
        



        

def initializing_handler():
    DPRINT(">> Initializing handler")
    global l_camera
    global r_camera
    global client
    global ser
    global state
    client = mqtt_init()
    ser = uart_init()
    device_home()
    print("Start l_camera openning.. it will take some time!")
    l_camera = cam_init(L_CAM_INDEX)
    #r_camera = cam_init(R_CAM_INDEX)
    print("Success! Camera is ready!")
    log("Waiting for commands")
    state = WAITING_ST


def waiting_handler():
    DPRINT(">> Waiting handler")
    DPRINT(f">> Command is '{cmd}'")
    global state
    if cmd == CH_ORDER_CMD: 
        log("Changing order..")
        state = SETTING_ORDER_ST
    elif cmd == START_CMD:
        state = STARTING_ST
    elif cmd == NO_CMD:
        pass
    else:
        log(f'Error! Wrong command - {cmd}')
    reset_cmd()

    
def setting_order_handler():
    DPRINT(">> Setting order handler")
    global state
    decode_order()
    DPRINT(">> decoded order: ")
    DPRINT(order)
    DPRINT(f">> Command is '{cmd}'")
    if cmd == SAVE_ORDER_CMD:
        log("Saving the order")
        state = WAITING_ST
    reset_cmd()
        

def starting_handler():
    DPRINT(">> Starting handler")
    global state
    if (len(order) == 0):
        if (len(collected) > 0):
            log("Order is already picked up!")
            state = FINISH_ST
        else:
            log("Warning! Order is empty!")
            state = WAITING_ST
    else:
        log("Starting order collecting..")
        state = SCANNING_ST



MOVE  = 0
SCAN  = 1
GRAB  = 2
THROW = 3
scanning_stage = MOVE



grab_list = [None, None]
scan_list = [None, None]
    
def reset_scanningStage():
    global current_cell
    global scanning_stage
    grab_list[0] = None
    grab_list[1] = None
    current_cell = 0
    scanning_stage = MOVE



def scanning_handler():
    global l_camera
    global r_camera
    global state
    global current_cell
    global scanning_stage
    DPRINT(">> Scanning handler")
    
    
    DPRINT(f">> Command is '{cmd}'")
    if cmd == PAUSE_CMD:
        if scanning_stage == GRAB:
            scanning_stage = SCAN
        device_pause()
        state = PAUSE_ST
        return
    elif cmd == BREAK_CMD:
        state = BREAK_ST
        return
    reset_cmd()
    
    if scanning_stage == MOVE:
        if (current_cell == storage_cells_num):
            log("The last cell was reached! Scan again from the first cell!")
            current_cell = 0
        DPRINT('Going to the next cell..')
        device_next_cell()
        DPRINT(f'Current cell is #{current_cell}')
        scanning_stage = SCAN
    
    elif scanning_stage == SCAN:
        uart_print(f'G1 U180')
        wait_for_answer()
        if (not l_camera):
            l_camera = cam_init(L_CAM_INDEX)
        if (not r_camera):
            r_camera = cam_init(R_CAM_INDEX)
        DPRINT('Capture img and scan for QR')
        #filename = f'cell-{current_cell}.png'
        
        l_photo_name = f'l_work.png'    
        r_photo_name = f'r_work.png'
        #DPRINT(l_photo_name)
        #DPRINT(r_photo_name)
        
        if (not scan_list[0]):
            capture(l_camera, l_photo_name)
            l_data = scan_qrcode(l_photo_name)
            
            log("Checking left camera QR code..")
            if (not l_data):
                log(f'Cant found QR code. Try again..')
            else:
                DPRINT("Successfully found and read QR code!")
                scan_list[0] = l_data
                log(f"Found '{l_data}' item")
                if (l_data in order):
                    log(f"'{l_data}' is in order! Collecting..")
                    grab_list[0] = l_data
                else:
                    log(f"'{l_data}' is not in order! Continue scanning!")
        if (not scan_list[1]):
            scan_list[1] = "Кака"
        #    capture(r_camera, r_photo_name)
        #    r_data = scan_qrcode(r_photo_name)
        #    
        #    log("Checking right camera QR code..")
        #    if (not r_data):
        #        log(f'Cant found QR code. Try again..')
        #    else:
        #        DPRINT("Successfully found and read QR code!")
        #        scan_list[1] = r_data
        #        log(f"Found '{r_data}' item")
        #        if (r_data in order):
        #            log(f"'{r_data}' is in order! Collecting..")
        #            grab_list[1] = r_data
        #        else:
        #            log(f"'{r_data}' is not in order! Continue scanning!")
        
        if (scan_list[0] and scan_list[1]):
            scan_list[0] = None
            scan_list[1] = None
            if (grab_list[0] or grab_list[1]):
                scanning_stage = GRAB
            else:
                scanning_stage = MOVE
        
    elif scanning_stage == GRAB:
        if (grab_list[0]):
            device_gripper_open()
            device_grab_l_obj()
            device_pull_object()
            device_release_object()
            log(f"'{grab_list[0]}' was collected!")
            index = order.index(grab_list[0])
            collected.append(order.pop(index))
            grab_list[0] = None
        
        if (grab_list[1]):
            device_gripper_open()
            device_grab_r_obj()
            device_pull_object()
            device_release_object()
            log(f"'{grab_list[1]}' was collected!")
            index = order.index(grab_list[1])
            collected.append(order.pop(index))
            grab_list[1] = None
            
        DPRINT("order:") 
        DPRINT(order)
        DPRINT("collected:") 
        DPRINT(collected)
        
        scanning_stage = MOVE
        if (len(order) == 0):
            log("Order is picked up!")
            state = FINISH_ST
    else:
        DPRINT("Error! Wrong scanning stage!")
    
    
    
    
        
def reset_scanning_data():
    reset_scanningStage()
    reset_order()
    reset_collected_order()


def end_scanning():
    if (len(collected) > 0):
        log('Collected: ' + orderlist_to_string(collected))
    if (len(order) > 0):
        log('Not collected: ' +orderlist_to_string(order))
    
    reset_scanning_data()
    device_home()
    log("Waiting for commands")
    device_reset()

    
def finish_handler():
    DPRINT(">> Finish handler")
    global state
    log("Order completed!")
    ### Display finish screen
    end_scanning()
    state = WAITING_ST
    
def break_handler():
    DPRINT(">> Break handler")
    global state
    log("Break order collecting!")
    device_break()
    ### Display break screen
    end_scanning()
    state = WAITING_ST

def pause_handler():
    DPRINT(">> Pause handler")
    global state
    if cmd == CH_ORDER_CMD: 
        state = CH_ORDER_ST
    elif cmd == START_CMD:
        state = STARTING_ST
    elif cmd == BREAK_CMD:
        state = BREAK_ST
    reset_cmd()
    
def ch_order_handler():
    DPRINT(">> Changing order handler")
    global state
    decode_order()
    DPRINT(">> decoded order: ")
    DPRINT(order)
    DPRINT(f">> Command is '{cmd}'")
    if cmd == SAVE_ORDER_CMD:
        state = PAUSE_ST    
    reset_cmd()
    

INITIALIZING_ST     = 0
WAITING_ST          = 1
SETTING_ORDER_ST    = 2
STARTING_ST         = 3
SCANNING_ST         = 4
FINISH_ST           = 5
PAUSE_ST            = 6
CH_ORDER_ST         = 7
BREAK_ST            = 8

state = INITIALIZING_ST

state_handlers = [
        {"state": INITIALIZING_ST,  "func": initializing_handler},
        {"state": WAITING_ST,       "func": waiting_handler},
        {"state": SETTING_ORDER_ST, "func": setting_order_handler},
        {"state": STARTING_ST,      "func": starting_handler},
        {"state": SCANNING_ST,      "func": scanning_handler},
        {"state": FINISH_ST,        "func": finish_handler},
        {"state": PAUSE_ST,         "func": pause_handler},
        {"state": CH_ORDER_ST,      "func": ch_order_handler},
        {"state": BREAK_ST,         "func": break_handler}
]

while True:
    for handler in state_handlers:
        if handler["state"] == state:
            handler["func"]()
            break
    time.sleep(1)
