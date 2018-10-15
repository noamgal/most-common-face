# most-common-face
Python HTTP web service using azure Cognitive Services face API 

https://azure.microsoft.com/en-us/services/cognitive-services/ 

Finds the most common face in a list of images, and return metadata about the best image of this common face.
The list of images are all local file full paths.

### Installing

```
pip install -r requirements.txt
```
## Deployment

In face_detect.py replace YOUR PRIVATE AZURE SUBSCRIPTIrON KEY TO FACE API SERVICE with a valid key given by azure.

run /usr/bin/python2.7 face_detect.py

go to http://127.0.0.1:5000/ and see example of use


## Authors

* **Noam Gal** - noamgal1@gmail.com
