#!/usr/bin/env python

import rospy
import baxter_interface
from inspector.msg import Update
from inspector.msg import PclData
from inspector.msg import ObjectList
from sensor_msgs.msg import JointState
import roslib; roslib.load_manifest("moveit_python")
from moveit_python import PlanningSceneInterface, MoveGroupInterface
from geometry_msgs.msg import PoseStamped, PoseArray
from moveit_python.geometry import rotate_pose_msg_by_euler_angles
from math import pi, sqrt
from collections import Counter
from operator import itemgetter
import numpy as np

#states 0-startup, 1-train, 2-sort, 3-fetch, 4-shutdown
def state_int(data):
    if data.state == 1:
        train_loop(data)
    elif data.state ==2:
        sort_loop(data)
    elif data.state ==3:
        fetch_loop(data)
    elif data.state ==4:
        shutdown()
    elif data.state ==5:
        standby()
    else:
        rospy.spin()

def startup():
    rospy.loginfo("Begin Startup")
    baxter_interface.RobotEnable().enable()
    head = baxter_interface.Head()
    rightlimb = baxter_interface.Limb('right')
    leftlimb = baxter_interface.Limb('left')
    leftlimb.move_to_neutral()
    rightlimb.move_to_neutral()
    head.set_pan(0.0)

def shutdown():
    rospy.loginfo("Begin Shutdown")
    head = baxter_interface.Head()
    rightlimb = baxter_interface.Limb('right')
    leftlimb = baxter_interface.Limb('left')
    leftlimb.move_to_neutral()
    rightlimb.move_to_neutral()
    head.set_pan(0.0)
    rospy.sleep(1)
    baxter_interface.RobotEnable().disable()

def wait_for_coord():
    left_gripper.calibrate()
    left_gripper.open()
    right_gripper.calibrate()
    right_gripper.open()
    # Clear planning scene
    p.clear()
    # Add table as attached object
    p.attachBox('table', 0.76, 1.22, 0.735, 1.13, 0, -0.5525, 'base', touch_links=['pedestal'])
    #move to start
    g.moveToJointPosition(jts_left, away, plan_only=False)
    a.moveToJointPosition(jts_right, neutral, plan_only=False)
    rospy.loginfo("Moving to neutral pose...")

def standby():
    if prev_state == 1:
        a.moveToJointPosition(jts_all, prev_jts, plan_only=False)
        right_gripper.open()
        a.moveToJointPosition(jts_right, neutral, plan_only=False)
    elif prev_state == 3:
        right_gripper.open()
        a.moveToJointPosition(jts_right, neutral, plan_only=False)
    else:
        return

def train_loop(data):
    #initializations
    done=state()

    #unpack the message (arrays of object positions)
    xpos= data.objects.centroids.x
    ypos=data.objects.centroids.y
    zpos=data.objects.centroids.z
    heights=data.objects.heights
    widths=data.objects.widths
    num=data.obj_index

    if data.next == 1:
        # Move left arm to replace object
        goal = PoseStamped()
        goal.header.frame_id = "base"
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.x = last_obj_x
        goal.pose.position.y = last_obj_y
        goal.pose.position.z = last_obj_z+0.1
        goal.pose.orientation.x = 0.0
        goal.pose.orientation.y = 0.7
        goal.pose.orientation.z = 0.0
        goal.pose.orientation.w = 0.7
        a.moveToPose(goal, "right_gripper", plan_only=False)
        right_gripper.open()
        a.moveToJointPosition(jts_right, neutral, plan_only=False)

    # Clear planning scene
    p.clear()
    # Add table as attached object
    p.attachBox('table', 0.76, 1.22, 0.735, 1.13, 0, -0.5525, 'base', touch_links=['pedestal'])

    xn = xpos[0]
    yn = ypos[0]
    zn = zpos[0]

    last_obj_x=xn
    last_obj_y=yn
    last_obj_z=zn

    #Add all items to collision scene
    objlist = ['obj1', 'obj2', 'obj3']
    for i in range(1,len(xpos)):
        p.addCyl(objlist[i], 0.05, xpos[i], ypos[i], zpos[i])
    p.waitForSync()

    # Move left arm to pick object and pick object
    goal = PoseStamped()
    goal.header.frame_id = "base"
    goal.header.stamp = rospy.Time.now()
    goal.pose.position.x = xn
    goal.pose.position.y = yn
    goal.pose.position.z = zn+0.1
    goal.pose.orientation.x = 0.0
    goal.pose.orientation.y = 0.7
    goal.pose.orientation.z = 0.0
    goal.pose.orientation.w = 0.7
    a.moveToPose(goal, "right_gripper", plan_only=False)

    #here would add gripper information
    a.moveToPose(goal,"right_gripper", plan_only=False)
    right_gripper.close()

    #lift the object up
    a.moveToJointPosition(jts_right, up, plan_only=False)

    done.state=1
    out=pub.publish(done)
    rospy.loginfo("Waiting for master...")
    rospy.spin()

def fetch_loop(data):
    #initializations
    done=state()

    #unpack the message (arrays of object positions)
    xpos= data.objects.centroids.x
    ypos=data.objects.centroids.y
    zpos=data.objects.centroids.z
    heights=data.objects.heights
    widths=data.objects.widths
    num=data.obj_index

    # Clear planning scene
    p.clear()
    # Add table as attached object
    p.attachBox('table',0.76, 1.22, 0.735, 1.13, 0, -0.5525, 'base', touch_links=['pedestal'])

    xn = xpos[0]
    yn = ypos[0]
    zn = zpos[0]

    last_obj_x=xn
    last_obj_y=yn
    last_obj_z=zn

    #Add all items to collision scene
    objlist = ['obj1', 'obj2', 'obj3']
    for i in range(1,len(xpos)):
        p.addCyl(objlist[i], 0.05, xpos[i], ypos[i], zpos[i])
    p.waitForSync()

    # Move left arm to pick object and pick object
    goal = PoseStamped()
    goal.header.frame_id = "base"
    goal.header.stamp = rospy.Time.now()
    goal.pose.position.x = xn
    goal.pose.position.y = yn
    goal.pose.position.z = zn+0.1
    goal.pose.orientation.x = 0.0
    goal.pose.orientation.y = 0.7
    goal.pose.orientation.z = 0.0
    goal.pose.orientation.w = 0.7
    a.moveToPose(goal, "right_gripper", plan_only=False)

    #here would add gripper information
    a.moveToPose(goal,"right_gripper", plan_only=False)
    right_gripper.close()

    #lift the object up
    a.moveToJointPosition(jts_right, up, plan_only=False)
    rospy.sleep(2)
    a.moveToJointPosition(jts_right,neutral,plan_only=False)

    done.state=1
    out=pub.publish(done)
    rospy.loginfo("Waiting for master...")
    rospy.spin()

def sort_loop(data):
    #initializations
    done=state()

    #unpack the message (arrays of object positions)
    xpos= data.objects.centroids.x
    ypos=data.objects.centroids.y
    zpos=data.objects.centroids.z
    heights=data.objects.heights
    widths=data.objects.widths
    num=data.obj_index

    # Clear planning scene
    p.clear()
    # Add table as attached object
    p.attachBox('table', 0.76, 1.22, 0.735, 1.13, 0, -0.5525, 'base', touch_links=['pedestal'])



    place=PoseStamped()
    place.header.frame_id = "base"
    place.pose.position.y= 0.5
    place.pose.orientation.x = 0.0
    place.pose.orientation.y = 0.7
    place.pose.orientation.z = 0.0
    place.pose.orientation.w = 0.7

    for q in range(1,len(xpos)):
        rospy.loginfo(Counter(prev_sort))
        num_items=Counter(prev_sort)
        x_1=num_items['1']
        x_2=num_items['2']
        x_3=num_items['3']

        xn = xpos[q]
        yn = ypos[q]
        zn = zpos[q]

        #Add all items to collision scene
        objlist = ['obj1', 'obj2', 'obj3']
        sortlist=['sort1','sort2','sort3','sort4','sort5','sort6','sort7','sort8','sort9','sort10']
        for i in range(1,len(xpos)):
            p.addCyl(objlist[i], 0.05, xpos[i], ypos[i], zpos[i])
        for i in range(1,len(prev_sort)):
            p.addCyl(sortlist[i], 0.05, prev_sort[1,i], prev_sort[2,i], prev_sort[3,i])
        p.waitForSync()

        # Move left arm to pick object and pick object
        goal = PoseStamped()
        goal.header.frame_id = "base"
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.x = xn
        goal.pose.position.y = yn
        goal.pose.position.z = zn+0.1
        goal.pose.orientation.x = 0.0
        goal.pose.orientation.y = 0.7
        goal.pose.orientation.z = 0.0
        goal.pose.orientation.w = 0.7
        a.moveToPose(goal, "right_gripper", plan_only=False)

        #here would add gripper information
        a.moveToPose(goal,"right_gripper", plan_only=False)
        right_gripper.close()

        place=PoseStamped()
        place.header.frame_id = "base"
        place.pose.position.y= 0.5
        place.pose.orientation.x = 0.0
        place.pose.orientation.y = 0.7
        place.pose.orientation.z = 0.0
        place.pose.orientation.w = 0.7
        place.header.stamp = rospy.Time.now()
        yp=place.pose.position.y

        if data.obj_index[q] == 1:
            place.pose.position.z = 1.0
            place.pose.position.x = 0.5 + x_1*0.5
            zp=place.pose.position.z
            xp=place.pose.position.x
            x_1 = x_1+1
        elif data.obj_index[q]  == 2:
            place.pose.position.z = 2.0
            place.pose.position.x = 0.5 + x_2*0.5
            zp=place.pose.position.z
            xp=place.pose.position.x
            x_2= x_2 +1
        else:
            place.pose.position.z = 3.0
            place.pose.position.x = 0.5 + x_3*0.5
            zp=place.pose.position.z
            xp=place.pose.position.x
            x_3=x_3+1

        #place object
        a.moveToPose(place, "right_gripper", plan_only=False)
        right_gripper.open()

        out=find_first('nan',prev_sort[0,:])
        prev_sort[0,out]=data.obj_index[q]
        prev_sort[1,out]=xp
        prev_sort[2,out]=yp
        prev_sort[3,out]=zp

    done.state=1
    out=pub.publish(done)
    rospy.loginfo("Waiting for master...")
    rospy.spin()

def find_first(item, vec):
    for i in xrange(len(vec)):
        if item == vec[i]:
            return i
    return -1

def test_loop():
    # Clear planning scene
    p.clear()
    # Add table as attached object
    p.attachBox('table',0.76, 1.22, 0.735, 1.13, 0, -0.5525, 'base', touch_links=['pedestal'])


    xn = 1
    yn = -0.3
    zn = -0.1

    p.waitForSync()

    # Move left arm to pick object and pick object
    goal = PoseStamped()
    goal.header.frame_id = "base"
    goal.header.stamp = rospy.Time.now()
    goal.pose.position.x = xn
    goal.pose.position.y = yn
    goal.pose.position.z = zn
    goal.pose.orientation.x = 0.0
    goal.pose.orientation.y = 0.7
    goal.pose.orientation.z = 0.0
    goal.pose.orientation.w = 0.7
    a.moveToPose(goal, "right_gripper", plan_only=False)
    right_gripper.close()
    temp = rospy.wait_for_message("/robot/joint_states", JointState)
    joints=temp.position

    #lift the object up
    a.moveToJointPosition(jts_right, up, plan_only=False)
    goal.header.stamp = rospy.Time.now()
    a.moveToJointPosition(jts_all,joints, plan_only=False)

    right_gripper.open()
    a.moveToJointPosition(jts_right, neutral, plan_only=False)

    xn=1
    yn=-0.2
    zn=-0.1
    goal.header.stamp = rospy.Time.now()
    goal.pose.position.x =xn
    goal.pose.position.y = yn
    goal.pose.position.z = zn
    goal.pose.orientation.x = 0.0
    goal.pose.orientation.y = 0.7
    goal.pose.orientation.z = 0.0
    goal.pose.orientation.w = 0.7
    a.moveToPose(goal,"right_gripper", plan_only=False)
    right_gripper.close()
    temp = rospy.wait_for_message("/robot/joint_states", JointState)
    joints=temp.position

    #lift the object up
    a.moveToJointPosition(jts_right, up, plan_only=False)
    goal.header.stamp = rospy.Time.now()
    a.moveToJointPosition(jts_all,joints, plan_only=False)
    right_gripper.open()
    a.moveToJointPosition(jts_right, neutral, plan_only=False)

    xn=1
    yn=-0.4
    zn=-0.1
    goal.header.stamp = rospy.Time.now()
    goal.pose.position.x =xn
    goal.pose.position.y = yn
    goal.pose.position.z = zn
    goal.pose.orientation.x = 0.0
    goal.pose.orientation.y = 0.7
    goal.pose.orientation.z = 0.0
    goal.pose.orientation.w = 0.7
    a.moveToPose(goal,"right_gripper", plan_only=False)
    right_gripper.close()
    temp = rospy.wait_for_message("/robot/joint_states", JointState)
    joints=temp.position

    #lift the object up
    a.moveToJointPosition(jts_right, up, plan_only=False)
    a.moveToJointPosition(jts_all,joints, plan_only=False)
    right_gripper.open()
    a.moveToJointPosition(jts_right, neutral, plan_only=False)


def hand_off():
    g.moveToJointPosition(jts_left,ho1_l,plan_only=False)
    a.moveToJointPosition(jts_right, ho1_r, plan_only=False)
    g.moveToJointPosition(jts_left,ho2_l,plan_only=False)
    left_gripper.close()
    right_gripper.open()
    g.moveToJointPosition(jts_left,ho1_l,plan_only=False)
    a.moveToJointPosition(jts_right,neutral,plan_only=False)
    g.moveToJointPosition(jts_left,l_neut,plan_only=False)


if __name__=='__main__':
    rospy.init_node("pick_up")
    global neutral
    global up
    global away
    global ho1_r
    global ho1_l
    global ho2_l
    global l_neut
    global shelf1
    global shelf2
    global shelf3
    global pub
    global p
    global g
    global a
    global jts_left
    global jts_right
    global jts_all
    global last_obj_x
    global last_obj_y
    global last_obj_z
    global prev_sort
    global right_gripper
    global left_gripper
    global pos1
    global pos2
    global pos3
    global prev_state
    global prev_jts
    right_gripper=baxter_interface.Gripper('right')
    left_gripper = baxter_interface.Gripper('left')


    #Position initializations
    #neutral = [1.5784662307340906, 1.1270923838988078, -0.08206797215186963, 1.0139613007922585, 1.403975916112125, 0.5971020216843973, -0.7528010716547668]
    neutral =[-0.038733014894106695, 1.3775147475211016, 0.9510680884889565, 0.18062623777350748, 0.14687866044002837, -1.5704128315976924, 0.017257283863710903]
    #up= [2.0992527082211887, 0.6208787238966212, 0.4406359813200851, 0.3604854851530722, 1.0561457724591075, 0.16643691548556738, -0.17602429540985123]
    up=[-0.03528155812136451, -0.014189322287940077, 0.8536603084582327, -0.05675728915176031, 0.1392087565006013, 0.04601942363656241, -0.09395632325798159]
    away = [0.027611654181937447, 0.7466651485032252, -0.008053399136398421, -0.5625874539569755, 0.009587379924283835, 1.2743545395358076, 0.0007669903939427069]
    ho1_r=[0.27074760906177553, 0.9690923627466101, 0.7581700044123657, -0.19059711289476267, -1.9328157927356213, -1.3894030986272135, 0.8160777791550401]
    ho1_l=[-0.03298058693953639, 1.2820244434752346, -0.3079466431679968, -0.2500388684253224, -1.3265098863239115, 1.6198837120069969, -0.5568350260024052]
    ho2_l=[-0.04256796686382023, 1.2536457988993543, -0.4302816110018586, -0.20938837754635897, -1.4093448488697238, 1.6137477888554552, -0.5357427901689807]
    pos1=[0.20478643518270273, 0.9963205217315763, 0.5223204582749834, 0.2124563391221298, -0.44600491407768406, -1.1715778267474848, -0.10661166475803625]
    pos2=[0.32750489821353584, 1.0365875174135684, 0.5959515360934833, 0.2454369260616662, -0.39500005288049406, -1.226034144717417, -0.2346990605464683]
    pos3=[0.19941750242510378, 1.0630486860045918, 0.8854904098068551, 0.1802427425765361, -0.03259709174256504, -1.2183642407779898, -0.2166747862888147]
    l_neut=[-0.019558255045539024, 0.896228275322053, -0.14841264122791378, 0.27228158984966094, -2.657238219814508, 1.28355842426312, -0.298359263243713]
    pub=rospy.Publisher("Inspector/state",state,queue_size=1)
    rospy.Subscriber("Inspector/objlist",objectlist, state_int)
    p = PlanningSceneInterface("base")
    g = MoveGroupInterface("left_arm", "base")
    a= MoveGroupInterface("right_arm", "base")
    jts_left = ['left_e0', 'left_e1', 'left_s0', 'left_s1', 'left_w0', 'left_w1', 'left_w2']
    jts_right = ['right_e0', 'right_e1', 'right_s0', 'right_s1', 'right_w0', 'right_w1', 'right_w2']
    jts_all=['head_nod', 'head_pan', 'left_e0', 'left_e1', 'left_s0', 'left_s1', 'left_w0', 'left_w1', 'left_w2', 'right_e0', 'right_e1', 'right_s0', 'right_s1', 'right_w0', 'right_w1', 'right_w2', 'torso_t0']
    prev_sort = np.zeros((4,10))
    #prev_sort=[float('nan') for x in range(10)] for y in range(4)]
    #Going to neutral and then getting into position
    rospy.loginfo("Getting into position...")
    startup()
    wait_for_coord()
    #test_loop()
    hand_off()
    rospy.spin()