#!/usr/bin/env python

# pip install requests, Pillow
from collections import namedtuple
import glob

import requests
from flask import (Flask, jsonify, request)
import PIL.Image
# import cognitive_face as az_face

app = Flask(__name__)

# Replace with a your subscription key
AZURE_SUBSCRIPTION_KEY = '<YOUR PRIVATE AZURE SUBSCRIPTION KEY TO FACE API SERVICE>'
# Replace with your regional Base URL
COGNITIVE_FACE_BASE_URL = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/'

FaceIDAttributes = namedtuple('FaceIDAttributes', 'relative_size face_rectangle face_landmarks image_file')

TASKS = {
        'Description': u"Find the most common face in a list of images, and return metadata about the best image of this common face",
        'Example of use': 'http://localhost:5000/most_common_face/?image_files=/home/noam/workspace/faces/2_people.jpeg,/home/noam/workspace/faces/6_people.jpeg',
        'Response': 'json with best_image, face_rectangle and face_landmarks attributes. It may take a while'
    }


def perform_post_request(url_request, headers, data=None, json=None, query_params=None):
    """ Perform POST HTTP request """
    post_response = requests.post(url_request, data=data, json=json, headers=headers, params=query_params)
    post_response.raise_for_status()
    if post_response.status_code == 200:
        return post_response.json()


def group_faces(face_ids):
    """Divide candidate faces into groups based on face similarity.
    Args:
        face_ids: An array of candidate `face_id`s created by `face.detect`.
            The maximum is 1000 faces.
    Returns:
        one or more groups of similar faces (ranked by group size) and a
        messyGroup.
    """
    faces_json = {
        'faceIds': face_ids,
    }
    headers = {'Content-Type': 'application/json',
               'Ocp-Apim-Subscription-Key': AZURE_SUBSCRIPTION_KEY}
    return perform_post_request(COGNITIVE_FACE_BASE_URL + "group", headers=headers, json=faces_json)


def calculate_relative_face_size(face_rectangle, image_file_name):
    """ return face size out of image size """
    face_size = face_rectangle["width"] * face_rectangle["height"]
    image = PIL.Image.open(image_file_name)
    image_size = image.size[0] * image.size[1]
    return face_size / (image_size*1.0)


def detect_face(image_file_name, face_attributes_list=None):
    """ Detect human faces in an image and returns a dictionary {face_id: FaceIDAttributes} """
    print image_file_name
    print "*" * len(image_file_name)
    if face_attributes_list:
        # Separate face attributes from list to comma separated list string
        face_attributes_list = reduce(lambda attr1, attr2: attr1 + "," + attr2, face_attributes_list)
    else:
        face_attributes_list = ""
    headers = {'Content-Type': 'application/octet-stream',
               'Ocp-Apim-Subscription-Key': AZURE_SUBSCRIPTION_KEY}
    params = {
        'returnFaceId': "true",
        'returnFaceLandmarks': "true",
        'returnFaceAttributes': face_attributes_list,
    }

    # Read image file
    with open(image_file_name, 'rb') as image_file_handler:
        image_data = image_file_handler.read()

    try:
        # Call detect azure face api
        faces_response = perform_post_request(COGNITIVE_FACE_BASE_URL + "detect", data=image_data,
                                              headers=headers, query_params=params)
    except Exception as exp:  # Here I got some rate limit exceptions
        print "Exception raised in detect_face", image_file_name, exp
        return {}

    # dict comprehension face_id : face ID attributes
    return {face_found["faceId"]: FaceIDAttributes(relative_size=calculate_relative_face_size(face_found["faceRectangle"], image_file_name),
                                                   face_rectangle=face_found["faceRectangle"],
                                                   face_landmarks=face_found.get("faceLandmarks"),
                                                   image_file=image_file_name)
            for face_found in faces_response}


@app.route('/')
@app.route('/tasks/')
def index():
    """ Please meet the application """
    return jsonify(TASKS)


@app.route('/most_common_face/', methods=['GET'])
def most_common_face_attributes():
    """
    Find the most common face in a list of images, and return metadata about the best image* of this common face.
    *Best Image = The image where the bounding box of the face is largest in relation to the size of the image.

    Expects request contains image_files argument which is a comma separated list of file names

    :returns: dictionary {"best_image": string,
                          "face_rectangle": {},
                          "face_landmarks": {keys: u'width', u'top', u'left', u'height'}}
    """
    image_file_list = request.args.get('image_files', None)
    if not image_file_list:
        return jsonify({"error": "Empty file list"})
    else:
        image_file_list = image_file_list.split(",")
        all_faces = {}
        for image_file_name in image_file_list:
            # Get all faces ids from all image files in one dictionary
            all_faces.update(detect_face(image_file_name))

        # Use Face API group request: Groups are ranked by number of faces.
        try:
            faces_similarity_groups = group_faces(all_faces.keys())
            # print faces_similarity_groups
        except Exception as exp:
            print "Exception raised in group_faces", exp
            return jsonify({"error": "Error while grouping faces"})
        else:
            # Get first group with most common face
            most_common_face_group = faces_similarity_groups.get("groups", [])
            if most_common_face_group:
                most_common_face_group = most_common_face_group[0]

                # Now look for the image with bounding box of the face is largest in relation to the size of the image
                max_size = -1
                best_face_id = None
                for face_id in most_common_face_group:
                    if all_faces[face_id].relative_size > max_size:
                        max_size = all_faces[face_id].relative_size
                        best_face_id = face_id

                best_face_attributes = all_faces[best_face_id]
                return jsonify({"best_image": best_face_attributes.image_file,
                                "face_rectangle": best_face_attributes.face_rectangle,
                                "face_landmarks": best_face_attributes.face_landmarks})
            else:
                print "Didn't find any face more common than others !"
                return jsonify({"warning": "No common face"})


if __name__ == '__main__':
    app.run()

    # pictures = glob.glob("/home/noam/workspace/faces/*.jpeg")
    # print most_common_face_attributes(pictures)
