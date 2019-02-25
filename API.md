## Blender API

Ros wrapper for Blender to control Virtual Avatars
Install as `roscom` endpoint for python in order to be found by blender.

#### ROS Topics
* **/blender_api/available_arm_animations** (message: [AvailableGestures](msg/AvailableGestures.msg)):  
publishes list of available arm gestures
* **/blender_api/available_emotion_states** (message: [AvailableEmotionStates](msg/AvailableEmotionStates.msg)):  
publishes list of available expressions(poses) 
* **/blender_api/available_gestures** (message: [AvailableGestures](msg/AvailableGestures.msg)):   
publishes list of available face gestures
* **/blender_api/available_soma_states** (message: [AvailableSomaStates](msg/AvailableSomaStates.msg)): 
publishes available cyclic animations
* **/blender_api/available_visemes** (message: [AvailableVisemes](msg/AvailableVisemes.msg)):  
publishes available visime poses
* **/blender_api/get_animation_mode** (message: `std_msgs/UInt8`): 
Returns animation mode.topic Determines which parts can be directly controlled by set_pau  topic.
* **/blender_api/get_api_version** (message: [GetAPIVersion](msg/GetAPIVersion.msg)):  
Current API version
* **/blender_api/get_arm_animations** (message: [Gestures](blender_api_msgs/Gestures.msg)): 
Currently playing arm animations 
* **/blender_api/get_emotion_states** (message: [EmotionStates](msg/EmotionStates.msg)): 
Currently active expressions (poses)
* **/blender_api/get_gestures** (message: [Gestures](msg/Gestures.msg)):  
currently playing gestures
* **/blender_api/get_pau** (message: `hr_msgs/pau`): 
Publishes current pose of head (including blendshapes), arms, body and neck. Used to control motors
* **/blender_api/get_som_states** (message: [SomaStates](msg/SomaStates.msg)):  
currently active cyclic animations
* **/blender_api/queue_viseme** (message: [Viseme](msg/Viseme.msg)): 
Add viseme for playback 
* **/blender_api/set_animation_mode** (message: `std_msgs/UInt8`):
Sets the animation mode which determines which part of the face will be controlled by /set_pau 
* **/blender_api/set_arm_animation** (message: [SetGesture](msg/SetGesture.msg)):  
Starts arm animation
* **/blender_api/set_blink_randomly** (message: [BlinkCycle](msg/BlinkCycle.msg)):  
Adjust blinking
* **/blender_api/set_emotion_state** (message: [EmotionState](msg/EmotionState.msg)):  
Sets current expressions (poses). 
* **/blender_api/set_face_target** (message: [Target](msg/Target.msg)):  
Adjust (moves) target for head in 3d coordinates
* **/blender_api/set_gaze_target** (message: [Target](msg/Target.msg)):   
Adjust(moves) eye target based on 3d coordinates
* **/blender_api/set_gesture** (message: [SetGesture](msg/SetGesture.msg)):  
Plays gesture  
* **/blender_api/set_head_rotation** (message: `std_msgs/Float32`): 
Sets head rotation (head roll)
* **/blender_api/set_neck_rotation** (message: `geometry_msgs/Vector3`): 
Sets Neck rotation (neck pitch and roll). Neck yaw controlled by head target.
* **/blender_api/set_pau** (message: `hr_msgs/pau`): 
* **/blender_api/set_saccade** (message: [SaccadeCycle](msg/SaccadeCycle.msg)):  
Adjust saccade settings
* **/blender_api/set_soma_state** (message: [SomaState](msg/SomaState.msg)):  
Sets cyclic animations

#### Ros services
* **/blender_api/get_animation_length** [GetAnimationLength](srv/GetAnimationLength.srv) : Get gesture length in seconds
* **/blender_api/get_arm_animation_length** [GetAnimationLength](srv/GetAnimationLength.srv): Get arm animation length in seconds
* **/blender_api/get_arms_mode** [GetMode](srv/GetMode.srv): Checks if arms mode (standing/sitting)
* **/blender_api/get_param** [GetParam](srv/GetParam.srv): Return string from python expression executed in blender
* **/blender_api/set_arms_mode** [SetMode](srv/SetMode.srv): Sets arm animation mode (standing/sitting)
* **/blender_api/set_param** [SetetParam](srv/SetParam.srv) : Sets any blender variable using eval. Should be used with caution.


