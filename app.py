#!/usr/bin/env python
# coding: utf-8

from matplotlib import pyplot
from PIL import Image
from numpy import asarray
from scipy.spatial.distance import cosine
from mtcnn import MTCNN
from keras_vggface.vggface import VGGFace
from keras_vggface.utils import preprocess_input
from flask import Flask, render_template, request
 
# extract a single face from a given photograph
def extract_face(filename, required_size=(224, 224)):
	pixels = pyplot.imread(filename)
	detector = MTCNN()
	results = detector.detect_faces(pixels)
	x1, y1, width, height = results[0]['box']
	x2, y2 = x1 + width, y1 + height
	face = pixels[y1:y2, x1:x2]
	image = Image.fromarray(face)
	image = image.resize(required_size)
	face_array = asarray(image)
	return face_array
 
# extract faces and calculate face embeddings for a list of photo files
def get_embeddings(filenames):
	faces = [extract_face(f) for f in filenames]
	samples = asarray(faces, 'float32')
	samples = preprocess_input(samples, version=2)
	model = VGGFace(model='resnet50', include_top=False, input_shape=(224, 224, 3), pooling='avg')
	return model.predict(samples)
 
# determine if the two faces match
# get the cosine distance between them
def match_embeddings(known_embedding, candidate_embedding, thresh=0.5):
	# calculate distance between embeddings
	score = cosine(known_embedding, candidate_embedding) 
	if score <= thresh:
                       return True
	else:
         return False

app = Flask(__name__)

# rendered as the front facing page of the app
@app.route('/')
def load_front_page():
    return render_template('index.html')

# called when you upload images	
@app.route('/index', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        first_file = request.files['original_image']
        second_file = request.files['to_compare_image']
        embeddings_array = [first_file, second_file]
        embeddings = get_embeddings(embeddings_array)
        if match_embeddings(embeddings[0], embeddings[1]):
            return render_template('index.html', message="The two photos are of the same person")
        else:
            return render_template('index.html', message="The two photos are of two different persons")
        
@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html', message="Please upload valid photos having a face")   
		
@app.errorhandler(404)
def not_found(error):
        return render_template('index.html', message="")   

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80', debug=True, threaded=False, use_reloader=False)
