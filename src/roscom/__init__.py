# Copyright (c) 2013-2018 Hanson Robotics, Ltd. 
# Implements ROS node to convert from ROS messages to the
# blender API defined in rigAPI.py.  The actual commands
# are transmitted to blender using the CommandListener.
#
import queue

import rospy
#import blender_api_msgs.msg as msg
import blender_api_msgs.srv as srv
from blender_api_msgs.cfg import AnimationModeConfig, ParallaxConfig

import hr_msgs.msg as hrmsg
import std_msgs.msg as stdmsg
import geometry_msgs.msg as geomsg
from dynamic_reconfigure.server import Server

import logging
import math
from mathutils import *
import time

import os
run_id = rospy.get_param('/run_id', None)
if run_id and 'ROS_LOG_DIR' in os.environ:
    os.environ['ROS_LOG_DIR'] = os.path.join(
        os.path.expanduser(os.environ['ROS_LOG_DIR']), run_id)

api = None
logger = logging.getLogger('hr.blender_api_msgs.roscom')

# This is called by __init__.py
# rigapi should be a (non-abstract-base-class) instance of RigAPI
def build(rigapi):
    global api
    api = rigapi
    return RosNode()

# RosNode duck types the virtual class rigAPI.CommandSource that blender_api
# expects us to use as the API to the rig.
class RosNode():
    '''All of class state is stored in self.incoming_queue and self.topics '''

    def __init__(self):
        self.incoming_queue = queue.Queue()
        rospy.init_node('blender_api')

        # Collect all public methods in CommandWrappers class.
        # Note that, because of the applied decorators, the methods are actually
        # CommandDecorator objects.
        self.topics = [
            getattr(CommandWrappers, name) for name in dir(CommandWrappers)
            if name[0] != '_'
        ]
        # Advertise the publishers and subscribers.
        for topic in self.topics:
            # Direct '@subscribe' decorated topics to our queue.
            if isinstance(topic, subscribe):
                topic.callback = self._enqueue
            topic.register()

    def init(self):
        for topic in self.topics:
            topic.paused = False
        return True

    def poll(self):
        '''Incoming cmd getter '''
        try:
            return self.incoming_queue.get_nowait()
        except queue.Empty:
            return None

    def push(self):
        '''Create and publish messages to '@publish_live' decorated topics '''
        live_topics = [topic for topic in self.topics if isinstance(topic, publish_live)]
        try:
            for topic in live_topics:
                topic.publish()
        except rospy.ROSException as ex:
            logger.error(ex)
            return False
        return True

    # After this is called, blender will not ever poll us again.
    def drop(self):
        '''Disable communication'''
        # We don't shutdown the actual ROS node, because restarting a
        # ROS node after shutdown is not supported in rospy.
        for topic in self.topics:
            topic.drop()
        return True

    def _enqueue(self, incoming_cmd):
        self.incoming_queue.put(incoming_cmd)


class IncomingCmd:
    ''' a function (command) prepared for delayed execution '''
    def __init__(self, func, arg):
        self.func, self.arg = func, arg
    def execute(self):
        self.func(self.arg)


# Decorators for CommandWrappers methods

class CommandDecorator:
    def __init__(self, topic, dataType):
        self.topic = topic
        self.dataType = dataType
        self.paused = False
    def __call__(self, cmd_func):
        self.cmd_func = cmd_func
        return self
    def register(self): raise NotImplementedError
    def drop(self):
        self.paused = True

class publish_once(CommandDecorator):
    def register(self):
        self.pub = rospy.Publisher(self.topic, self.dataType, queue_size=1, latch=True)
        self.pub.publish(self.cmd_func())

class publish_live(CommandDecorator):
    def register(self):
        self.pub = rospy.Publisher(self.topic, self.dataType, queue_size=1)
    def publish(self):
        if self.paused: return
        self.pub.publish(self.cmd_func())

class subscribe(CommandDecorator):
    def register(self):
        self.sub = rospy.Subscriber(self.topic, self.dataType, self._handle)
    def _handle(self, msg):
        # XXX ??? Now that ROS is not initialized twice, the
        # self.callback thing is not working.  I cannot tell what
        # it was supposed to do ???
        # self.callback(IncomingCmd(self.cmd_func, msg))
        if self.paused: return
        self.cmd_func(msg)



class service(CommandDecorator):
    def register(self):
        self.serv = rospy.Service(self.topic, self.dataType, self._handle)
    def _handle(self, msg):
        return self.cmd_func(msg)


class configure(CommandDecorator):
    def register(self):
        self.serv = Server(self.dataType, self._handle, self.topic)

    def _handle(self, cfg, level):
        return self.cmd_func(cfg, level)

class CommandWrappers:
    '''
    These methods shouldn't be called directly.
    They define topics the rosnode will publish and subscribe to.

    These methods must be decorated with a CommandDecorator subclass.
    The decorators take two arguments: a topicname and a message type they are
    meant to send or receive.
    '''

    @publish_once("~get_api_version", hrmsg.GetAPIVersion)
    def getAPIVersion():
        return hrmsg.GetAPIVersion(api.getAPIVersion())
    # ROS interfaces to listen to blendshape topics

    @publish_live("~get_animation_mode", stdmsg.UInt8)
    def getAnimationMode():
        return stdmsg.UInt8(api.getAnimationMode())

    @subscribe("~set_animation_mode", stdmsg.UInt8)
    def setAnimationMode(mesg):
        mode= mesg.data
        api.setAnimationMode(mode)

    # Somatic states  --------------------------------
    # awake, asleep, breathing, drunk, dazed and confused ...
    @publish_once("~available_soma_states", hrmsg.AvailableSomaStates)
    def availableSomaStates():
        return hrmsg.AvailableSomaStates(api.availableSomaStates())


    @subscribe("~set_soma_state", hrmsg.SomaState)
    def setSomaState(mesg):
        if api.pauAnimationMode & api.PAU_ACTIVE:
            return
        state = {
            'name': mesg.name,
            'magnitude': mesg.magnitude,
            'rate': mesg.rate,
            'ease_in': mesg.ease_in.to_sec()
        }
        api.setSomaState(state)

    @publish_live("~get_soma_states", hrmsg.SomaStates)
    def getSomaStates():
        return hrmsg.SomaStates([
            hrmsg.SomaState(name,
                vals['magnitude'],
                vals['rate'],
                rospy.Duration(vals['ease_in']))
            for name, vals in api.getSomaStates().items()
        ])


    # Emotion expressions ----------------------------
    # smiling, frowning, bored ...
    @publish_once("~available_emotion_states", hrmsg.AvailableEmotionStates)
    def availableEmotionStates():
        return hrmsg.AvailableEmotionStates(api.availableEmotionStates())


    @publish_live("~get_emotion_states", hrmsg.EmotionStates)
    def getEmotionStates():
        return hrmsg.EmotionStates([
            # Emotion state has no current duration
            hrmsg.EmotionState(name, vals['magnitude'], 0)
            for name, vals in api.getEmotionStates().items()
        ])

    # Message is a single emotion state
    @subscribe("~set_emotion_state", hrmsg.EmotionState)
    def setEmotionState(mesg):
        # if api.pauAnimationMode & (api.PAU_ACTIVE > api.PAU_FACE) == api.PAU_ACTIVE | api.PAU_FACE:
        #     return
        emotion = str({
            mesg.name: {
                'magnitude': mesg.magnitude,
                'duration': mesg.duration.to_sec()
            }
        })
        api.setEmotionState(emotion)

    # Message is a single emotion state
    # In contrast to set_emotion_state, this function sets the value
    # of a particular emotion directly and leaves it at that value.
    # It can be used to mix and manually drive emotion states.
    @subscribe("~set_emotion_value", hrmsg.EmotionState)
    def setEmotionValue(mesg):
        if api.pauAnimationMode & (api.PAU_ACTIVE > api.PAU_FACE) == api.PAU_ACTIVE | api.PAU_FACE:
            return
        emotion = str({
            mesg.name: {
                'magnitude': mesg.magnitude,
                'duration': mesg.duration.to_sec()
            }
        })
        api.setEmotionValue(emotion)


    # Gestures --------------------------------------
    # blinking, nodding, shaking...
    @publish_once("~available_gestures", hrmsg.AvailableGestures)
    def availableGestures():
        return hrmsg.AvailableGestures(api.availableGestures())


    @publish_live("~get_gestures", hrmsg.Gestures)
    def getGestures():
        return hrmsg.Gestures([
            hrmsg.Gesture(
                name,
                vals['speed'],
                vals['magnitude'],
                rospy.Duration(vals['duration'])
            ) for name, vals in api.getGestures().items()
        ])


    @subscribe("~set_gesture", hrmsg.SetGesture)
    def setGesture(msg):
        # if api.pauAnimationMode & api.PAU_ACTIVE > 0:
        #     return
        try:
            api.setGesture(msg.name, msg.repeat, msg.speed, msg.magnitude)
        except TypeError:
            logger.error('Unknown gesture: {}'.format(msg.name))


    # Visemes --------------------------------------
    @publish_once("~available_visemes", hrmsg.AvailableVisemes)
    def availableVisemes():
        return hrmsg.AvailableVisemes(api.availableVisemes())

    @subscribe("~queue_viseme", hrmsg.Viseme)
    def queueViseme(msg):
        if api.pauAnimationMode & (api.PAU_ACTIVE | api.PAU_FACE) == api.PAU_ACTIVE | api.PAU_FACE:
            return
        try:
            api.queueViseme(msg.name, msg.start.to_sec(),
                msg.duration.to_sec(),
                msg.rampin, msg.rampout, msg.magnitude)
        except TypeError:
            logger.error('Unknown viseme: {}'.format(msg.name))


    # Look-at and turn-to-face targets ---------------------
    # Location that Eva will look at and face.
    @subscribe("~set_face_target", hrmsg.Target)
    def setFaceTarget(msg):
        if api.pauAnimationMode & (api.PAU_ACTIVE | api.PAU_HEAD_YAW) == api.PAU_ACTIVE | api.PAU_HEAD_YAW:
            return
        flist = [msg.x, msg.y, msg.z]
        api.setFaceTarget(flist, msg.speed)

    # Location that Eva will look at (only).
    @subscribe("~set_gaze_target", hrmsg.Target)
    def setGazeTarget(msg):
        if api.pauAnimationMode & (api.PAU_ACTIVE | api.PAU_EYE_TARGET) == api.PAU_ACTIVE | api.PAU_EYE_TARGET:
            return
        flist = [msg.x, msg.y, msg.z]
        api.setGazeTarget(flist, msg.speed)

    @subscribe("~set_head_rotation", stdmsg.Float32)
    def setHeadRotation(msg):
        if api.pauAnimationMode & (api.PAU_ACTIVE | api.PAU_HEAD_ROLL) == api.PAU_ACTIVE | api.PAU_HEAD_ROLL:
            return
        #sets only pitch and roll
        api.setHeadRotation(msg.data)

    # Pau messages --------------------------------
    @publish_live("~get_pau", hrmsg.pau)
    def getPau():
        msg = hrmsg.pau()

        head = api.getHeadData()
        msg.m_headRotation.x = head['x']
        msg.m_headRotation.y = head['y']
        msg.m_headRotation.z = -head['z']
        msg.m_headRotation.w = head['w']

        neck = api.getNeckData()
        msg.m_neckRotation.x = neck['x']
        msg.m_neckRotation.y = neck['y']
        msg.m_neckRotation.z = -neck['z']
        msg.m_neckRotation.w = neck['w']

        eyes = api.getEyesData()
        msg.m_eyeGazeLeftPitch = eyes['l']['p']
        msg.m_eyeGazeLeftYaw = eyes['l']['y']
        msg.m_eyeGazeRightPitch = eyes['r']['p']
        msg.m_eyeGazeRightYaw = eyes['r']['y']

        shapekeys = api.getFaceData()
        msg.m_coeffs = shapekeys.values()

        angles = api.getArmsData()
        msg.m_angles = angles.values()

        # Manage timeout for set_pau
        if api.pauTimeout < time.time():
            api.setAnimationMode(api.pauAnimationMode & ~api.PAU_ACTIVE)
        return msg

    # Set Pau messages -----------------------------
    @subscribe("~set_pau", hrmsg.pau)
    def setPau(msg):
        # Ignore if no animations are enabled by PAU
        if api.pauAnimationMode == 0:
            return
        # Active mode expires
        api.pauTimeout = time.time()+api.PAU_ACTIVE_TIMEOUT
        # PAU animation is active
        api.setAnimationMode(api.pauAnimationMode | api.PAU_ACTIVE)
        # Calculate head and eyes targets
        pitch = 0
        yaw = 0
        roll = 0
        if api.pauAnimationMode & (api.PAU_HEAD_YAW | api.PAU_HEAD_ROLL):
            q = msg.m_headRotation
            q = Quaternion([q.w,q.x,q.y,q.z])
            try:
                e = q.to_euler('XZY')
                pitch = e.x
                yaw = e.y
                roll = e.z
            except:
                pitch = 0
                yaw = 0
                roll = 0
            az = math.sin(pitch)
            ay = math.sin(yaw)*math.cos(pitch)
            # Target one meter away
            ax = math.cos(yaw)*math.cos(pitch)
            # Sets Face target
            if api.pauAnimationMode & api.PAU_HEAD_YAW:
                api.setFaceTarget([ax, ay, -az])
            if api.pauAnimationMode & api.PAU_HEAD_ROLL:
                api.setHeadRotation(roll)

        if api.pauAnimationMode & api.PAU_EYE_TARGET:
            pitch += math.radians(msg.m_eyeGazeLeftPitch)
            yaw += math.radians(msg.m_eyeGazeLeftYaw)
            az = math.sin(pitch)
            ay = math.sin(yaw)*math.cos(pitch)
            # Target one meter away
            ax = math.cos(yaw)*math.cos(pitch)
            # Sets Face target
            api.setGazeTarget([ax, ay, -az])
        if api.pauAnimationMode & api.PAU_FACE:
            # Set Face shapekeys
            shapekeys = dict(zip(msg.m_shapekeys, msg.m_coeffs))
            api.setShapeKeys(shapekeys)
        if api.pauAnimationMode & api.PAU_ARMS:
            # Set Arm angles
            joints = dict(zip(msg.m_joints, msg.m_angles))
            api.setArmsJoints(joints)


    @subscribe("~set_neck_rotation", geomsg.Vector3)
    def setNeckRotation(msg):
        #sets only pitch and roll
        api.setNeckRotation(msg.y, msg.x)

    @subscribe("~set_blink_randomly",hrmsg.BlinkCycle)
    def setBlinkRandomly(msg):
        api.setBlinkRandomly(msg.mean,hrmsg.variation)

    @subscribe("~set_saccade",hrmsg.SaccadeCycle)
    def setSaccade(msg):
        api.setSaccade(msg.mean,msg.variation,msg.paint_scale,msg.eye_size,msg.eye_distance,msg.mouth_width,msg.mouth_height,msg.weight_eyes,msg.weight_mouth)

    @service("~set_param", srv.SetParam)
    def setParam(msg):
        return srv.SetParamResponse(api.setParam(msg.key, msg.value))

    @service("~get_param", srv.GetParam)
    def getParam(msg):
        return srv.GetParamResponse(api.getParam(msg.param))

    @service("~get_animation_length", srv.GetAnimationLength)
    def getAnimationLength(req):
        return srv.GetAnimationLengthResponse(api.getAnimationLength(req.animation))

    @service("~get_arm_animation_length", srv.GetAnimationLength)
    def getArmAnimationLength(req):
        return srv.GetAnimationLengthResponse(api.getArmAnimationLength(req.animation))

    @publish_live("~get_current_frame", hrmsg.CurrentFrame)
    def getCurrentFrame():
        _msg = hrmsg.CurrentFrame()
        data = api.getCurrentFrame()
        if data is not None:
            _msg.name = data[0]
            _msg.frame = data[1]
        return _msg


    # Arm animations --------------------------------------
    @publish_once("~available_arm_animations", hrmsg.AvailableGestures)
    def availableArmAnimations():
        # Using available gestures seems to be fine
        return hrmsg.AvailableGestures(api.availableArmAnimations())


    @publish_live("~get_arm_animations", hrmsg.Gestures)
    def getArmAnimations():
        return hrmsg.Gestures([
            hrmsg.Gesture(
                name,
                vals['speed'],
                vals['magnitude'],
                rospy.Duration(vals['duration'])
            ) for name, vals in api.getArmAnimations().items()
        ])


    @subscribe("~set_arm_animation", hrmsg.SetGesture)
    def setArmAnimation(msg):
        try:
            api.setArmAnimation(msg.name, msg.repeat, msg.speed, msg.magnitude)
        except TypeError:
            logger.error('Unknown gesture: {}'.format(msg.name))

    @service("~get_arms_mode", srv.GetMode)
    def getArmsMode(req):
        return srv.GetModeResponse(api.getArmsMode())

    @service("~set_arms_mode", srv.SetMode)
    def setArmsMode(req):
        return srv.SetModeResponse(api.setArmsMode(req.mode))

    @configure("/blender_api/override_mode", AnimationModeConfig)
    def setAnimationModeCfg(cfg, level):
        mode = 0
        if cfg.head:
            mode += 3
        if cfg.head_roll:
            mode += 4
        if cfg.eyes:
            mode += 8
        if cfg.face:
            mode += 16
        if cfg.arms:
            mode += 32
        api.setAnimationMode(mode)
        return cfg


    @configure("/blender_api/parallax", ParallaxConfig)
    def setParallaxCfg(cfg, level):
        api.parallax['eye_distance'] = cfg.eye_distance
        api.parallax['scale'] = cfg.parallax_scale
        return cfg

