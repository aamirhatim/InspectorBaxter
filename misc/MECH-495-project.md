### ME-495 Project proposal - Aamir Hussain, Aaron Weatherly, Hannah Emnett, Peng Peng, Srikanth Kilaru
#### Objective

We want baxter to learn the names of objects placed in front of it via voice interaction and then subsequently respond to a voice command to fetch any object that it has already learnt.   


##### Train Baxter:

1.> Teach Baxter to identiy a limited set of objects with names provided via speech commands

Stretch goal for this part would be to have speech interactionbetween Baxter and human to postively / negatively reinforce Baxter's object identification and grasping

2.> During this training phase Baxter stores object names as text strings (converted from voice via a speech API) as indices to access 3D point clouds of learnt objects.
Example: We say "that is a bottle" when baxter is looking at a bottle. Baxter stores the 3D point cloud of the battle and indexes it with the string "bottle" for future reference and comparison.

Stretch goal for this part would be to make Baxter pick up objects from a pile instead of discretely placed objects  


##### Put Baxter to work:

1.> Baxter is issued a voice command - "get me a bottle" which is translated to a text name "bottle"
2.> Baxter uses this text to access the associated point cloud of a bottle.
3.> Baxter then constructs the point cloud of objects on a table and then grasps the object with the point cloud that best matches the one that it has stored

A stretch goal for this part would be to identify objects that are in a different orientation compared to when it was learnt. For example how about if the bottle was lying on its side when it is issued the command to fetch versus it was standing up right when it learnt the object, etc.
Again as a stretch goal, Baxter could also interact with the operator and ask if the identified object is the object requested and correct itself based on a "Yes" / "No" response.



### Resources:


1.> ROS package that identifies objects using 3D point clouds and also figures out how to grasp them

https://discourse.ros.org/t/gpd-a-ros-package-for-grasping-novel-objects/2116

2.> Speech recognition API -
https://answers.ros.org/question/246247/speech-recognition-packages-for-ros-kinetic-kame/

Google speech API - 12 month free trial (I just signed up for this)
