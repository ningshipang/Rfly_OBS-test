#!/usr/bin/env python
#coding=utf-8

import rospy
import os
import json
import numpy as np
import math
import time
import threading
import Tkinter
from geometry_msgs.msg import *
from std_msgs.msg import Float32MultiArray
from std_srvs.srv import Empty
from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import SetMode
from mavros_msgs.msg import State, RCIn, HomePosition
from mavros_msgs.msg import Thrust
from utils_obs import Utils
from Queue import Queue
from rflysim_ros_pkg.msg import Obj


# Simulation of RealFlight
current_state = State()
ch5, ch6, ch7, ch8, ch9, ch11, ch14 = 0, 0, 0, 0, 1, 1, 1
is_initialize_mav, is_initialize_vel, is_initialize_rc, is_initialize_img = False, False, False, False

ch20 = 0
mav_pos = [0, 0, 0]
mav_original_angle = [0, 0, 0]
# mav_vel = [0, 0, 0]
mav_vel = np.array([0, 0, 0])
mav_yaw = 0
mav_R = np.zeros((3,3))
Initial_pos = [0, 0, 0]
pos_i = [0, 0, 0, 0, 0]
state_name = "InitializeState"
command = TwistStamped()
command_rate = TwistStamped()
command_angle = PoseStamped()
command_thrust = Thrust()
q = Queue()
maxQ = 100
sumQ = 0.0
home_dx, home_dy = 0, 0
depth = -1
original_offset = np.array([0, 0, 0])

sphere_pos_x, sphere_pos_y, sphere_pos_z = -0.1, 7.2, 2.43  #-0.065, 7, 2.43 
sphere_vx, sphere_vy, sphere_vz = -1, 0, 0

sphere_feb_pos = PoseStamped()
# obj_state = ModelState()

def spin():
    rospy.spin()

def state_cb(msg):
    global current_state
    current_state = msg

def mav_pose_cb(msg):
    global mav_pos, mav_yaw, mav_R, is_initialize_mav, mav_pitch, mav_roll
    is_initialize_mav = True
    mav_pos = [msg.pose.position.x, msg.pose.position.y, msg.pose.position.z]
    q0, q1, q2, q3 = msg.pose.orientation.w, msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z
    mav_yaw = math.atan2(2*(q0*q3 + q1*q2), 1-2*(q2*q2 + q3*q3))
    mav_pitch = math.asin(2*(q0*q2 - q1*q3))
    mav_roll = math.atan2(2*(q0*q1+q2*q3), 1-2*(q1*q1 + q2*q2))
    R_ae = np.array([[q0**2+q1**2-q2**2-q3**2, 2*(q1*q2-q0*q3), 2*(q1*q3+q0*q2)],
                      [2*(q1*q2+q0*q3), q0**2-q1**2+q2**2-q3**2, 2*(q2*q3-q0*q1)],
                      [2*(q1*q3-q0*q2), 2*(q2*q3+q0*q1), q0**2-q1**2-q2**2+q3**2]])
    # R_ba = np.array([[0,1,0], [-1,0,0], [0,0,1]]) #mavros_coordinate to body_coordinate
    R_ba = np.array([[0,1,0], [-1,0,0], [0,0,1]]) #mavros_coordinate to baselink_coordinate  // body to enu  # body: right-front-up3rpos_est_body)
    mav_R = R_ae.dot(R_ba)
    # mav_R = R_ae

def mav_vel_cb(msg):
    global mav_vel, is_initialize_vel
    is_initialize_vel = True
    # mav_vel = [msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z]
    mav_vel = np.array([msg.twist.linear.x, msg.twist.linear.y, msg.twist.linear.z])

def rcin_cb(msg):
    global ch5, ch6, ch7, ch8, ch9, ch11, ch14, is_initialize_rc
    is_initialize_rc = True
    last_ch5, last_ch6, last_ch7, last_ch8, last_ch9, last_ch11, last_ch14 = ch5, ch6, ch7, ch8, ch9, ch11, ch14
    chs = msg.channels
    ch5 = 2 if chs[4] < 1300 else 1 if chs[4] < 1700 else 0
    ch6 = 2 if chs[5] < 1300 else 1 if chs[5] < 1700 else 0
    ch7 = 2 if chs[6] < 1300 else 1 if chs[6] < 1700 else 0
    ch8 = 2 if chs[7] < 1300 else 1 if chs[7] < 1700 else 0
    ch9 = 2 if chs[8] < 1300 else 1 if chs[8] < 1700 else 0
    ch11 = 1 if chs[10] < 1500 else 0
    ch14 = 1 if chs[10] < 1500 else 0
    if ch5!=last_ch5 or ch6!=last_ch6 or ch7!=last_ch7 or ch8!=last_ch8 or ch9!=last_ch9 or ch11!=last_ch11 or ch14!=last_ch14:
        print("ch5: {}, ch6: {}, ch7: {}, ch8: {}, ch9: {}, ch11: {}, ch14: {}".format(ch5, ch6, ch7, ch8, ch9, ch11, ch14))

def call(event):
    global ch5, ch6, ch7, ch8, ch9, ch20
    k = event.keysym
    if k == "m":
        ch6 = 0
    elif k == "h":
        ch20 = 1
    elif k == "o":
        ch8 = 1
    elif k == "p":
        ch8 = 0
    elif k == "c":
        ch9 = (ch9 + 1) % 2
    elif k == "a":
        ch7 = 1
    elif k == "b":
        ch7 = 0
    time.sleep(0.02)

def read_kbd_input():
    global is_initialize_rc
    is_initialize_rc = True
    win = Tkinter.Tk()
    frame = Tkinter.Frame(win,width=100,height=60)
    frame.bind("<Key>",call)
    frame.focus_set()
    frame.pack()
    win.mainloop()

def pos_image_cb(msg):
    global is_initialize_img, pos_i
    is_initialize_img = True
    pos_i = msg.data

def sphere_control():
    global sphere_pos_x, sphere_pos_y, sphere_pos_z
    obj_msg = Obj()
    
    obj_msg.id = 100
    obj_msg.type = 152
    obj_msg.position.x = sphere_pos_x
    obj_msg.position.y = sphere_pos_y
    obj_msg.position.z = sphere_pos_z
    obj_msg.size.x = 0.05
    obj_msg.size.y = 0.05
    obj_msg.size.z = 0.05

    sphere_pub.publish(obj_msg)

def minAngleDiff(a, b):
    diff = a - b
    if diff < 0:
        diff += 2*np.pi
    if diff < np.pi:
        return diff
    else:
        return diff - 2*np.pi

def angleLimiting(a):
    if a > np.pi:
        return a - 2*np.pi
    if a < -np.pi:
        return a + 2*np.pi
    return a



if __name__=="__main__":
    setting_file = open(os.path.join(os.path.expanduser('~'),"Rfly_OBS/src","settings.json"))
    setting = json.load(setting_file)
    print(json.dumps(setting, indent=4))

    MODE = setting["MODE"]
    car_velocity = setting["car_velocity"]
    # follow_mode: 0, ll=follow_distance; 1, ll=norm(car_home, mav_home)
    follow_mode = setting["follow_mode"]
    follow_distance = setting["follow_distance"]
    FLIGHT_H = setting["FLIGHT_H"]
    u = Utils(setting["Utils"])

    rospy.init_node('offb_node', anonymous=True)
    spin_thread = threading.Thread(target = spin)
    spin_thread.start()

    rospy.Subscriber("mavros/state", State, state_cb)
    rospy.Subscriber("mavros/local_position/pose", PoseStamped, mav_pose_cb)
    rospy.Subscriber("mavros/local_position/velocity_local", TwistStamped, mav_vel_cb)
    #HIL???????????????????????????
    is_HIL = False
    if MODE == "RealFlight":
        rospy.Subscriber("mavros/rc/in", RCIn, rcin_cb)
    elif MODE == "Simulation":
        sphere_pub = rospy.Publisher("ue4_ros/obj", Obj, queue_size=10)

        if is_HIL == True:
            rospy.Subscriber("mavros/rc/in", RCIn, rcin_cb)
        else:
            inputThread = threading.Thread(target=read_kbd_input)
            inputThread.start()
    else:
        raise Exception("Invalid MODE!", MODE)
    rospy.Subscriber("tracker/pos_image", Float32MultiArray, pos_image_cb)
    local_vel_pub = rospy.Publisher('mavros/setpoint_velocity/cmd_vel', TwistStamped, queue_size=10)
    print("Publisher and Subscriber Created")

    rospy.wait_for_service("mavros/cmd/arming")
    arming_client = rospy.ServiceProxy('mavros/cmd/arming', CommandBool)
    rospy.wait_for_service("mavros/set_mode")
    set_mode_client = rospy.ServiceProxy('mavros/set_mode', SetMode)
    print("Clients Created")
    rate = rospy.Rate(50)#50
    
    # ensure the connection 
    while(not current_state.connected):
        print("connected: {}".format(current_state.connected))
        rate.sleep()

    for i in range(100):
        local_vel_pub.publish(command)
        rate.sleep()
        
    # switch into offboard
    print("Creating Objects for services")
    offb_set_mode = SetMode()
    offb_set_mode.custom_mode = "OFFBOARD"
    arm_cmd = CommandBool()
    arm_cmd.value = True

    last_request = rospy.Time.now()

    # start
    cnt = -1
    while not rospy.is_shutdown():
        cnt += 1
        # sphere_control()
        if MODE == "Simulation" and ch8 != 0 and mav_pos[1] > 6:
            sphere_control()
            rate.sleep()
            
        if ch8 == 0:
            if current_state.mode == "OFFBOARD":
                resp1 = set_mode_client(0, "POSCTL")	# (uint8 base_mode, string custom_mode)
            if cnt % 10 == 0:
                print("Enter MANUAL mode")
            mav_original_angle = [mav_yaw, mav_pitch, mav_roll]
            Initial_pos = mav_pos
            rate.sleep()
            continue
        else:
            if current_state.mode != "OFFBOARD":
                resp1 = set_mode_client( 0,offb_set_mode.custom_mode )
                if resp1.mode_sent:
                    print("Offboard enabled")
                last_request = rospy.Time.now()
        
        pos_info = {"mav_pos": mav_pos, "mav_vel": mav_vel, "mav_R": mav_R, "R_bc": np.array([[0,0,1], [1,0,0], [0,1,0]]), 
                    "mav_original_angle": mav_original_angle, "Initial_pos": Initial_pos}
        cmd = u.DockingControllerFusion(pos_info, pos_i)

        target_distance = 12
        dx = target_distance*np.cos(mav_original_angle[0])
        dy = target_distance*np.sin(mav_original_angle[0])
        # target_pos = np.array([Initial_pos[0] + dx, Initial_pos[1] + dy, Initial_pos[2]])   #initialize pos:[0, 12, 2.5]
        target_pos = np.array([0, 20, 2.5])
        feb_pos = np.array([mav_pos[0], mav_pos[1], mav_pos[2]])
        cmd_vel = u.pos_control(target_pos,feb_pos,1.0,1.5)  #(1,1.5)
        cmd_yaw = u.yaw_control(mav_original_angle[0], mav_yaw, 0.8, 0.8)

        vel_body = np.array([0, 1, 0])
        vel_e = mav_R.dot(vel_body)

        if ch7 == 1:
            #???????????????????????????????????????
            if pos_i[1] != 0: 
                command.twist.linear.x = cmd[0]
                command.twist.linear.y = cmd[1]
                command.twist.linear.z = cmd[2]
                command.twist.angular.z = cmd[3]
            else:
                command.twist.linear.x = cmd_vel[0]
                command.twist.linear.y = cmd_vel[1]
                command.twist.linear.z = cmd_vel[2]
                command.twist.angular.z = cmd_yaw
        else:
            mav_original_angle = [mav_yaw, mav_pitch, mav_roll]
            Initial_pos = mav_pos
            command.twist.linear.x = 0
            command.twist.linear.y = 0
            command.twist.linear.z = 0
            command.twist.angular.z = 0
        obs_pos = np.array([sphere_pos_x, sphere_pos_y, sphere_pos_z]) 
        local_vel_pub.publish(command)
        rate.sleep()
    rospy.spin()