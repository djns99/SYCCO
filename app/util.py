import os
import backend
import cv2
from flask import session
from pathlib import Path

def get_project_dir():
    return os.path.join('static', 'projects', session['hash'])
    
def get_unlabelled_files():
    return os.listdir(os.path.join(get_project_dir(), 'unlabelled'))

def get_labelled_files():
    return filter(lambda name: not name.endswith('.labels'), os.listdir(os.path.join(get_project_dir(), 'labelled')))

def get_prediction_files():
    return os.listdir(os.path.join(get_project_dir(), 'predictions'))

def convert_to_uri(path):
    return Path(path).as_posix()

def get_labels():
    labels_file = open(os.path.join(get_project_dir(), 'labels.txt'), "r")
    labels = labels_file.read().splitlines()
    labels_file.close()
    return labels

def add_label(label):
    if 'labels' not in session:
        session['labels'] = [label]
    else:
        session['labels'] += [label]
    
    labels_file = open(os.path.join(get_project_dir(), 'labels.txt'), "a")
    labels_file.write(label + "\n")
    labels_file.close()

ALLOWED_EXTENSIONS=["jpg", "png"] # Add supported extensions here
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def make_prediction():
    prod_dir = get_project_dir()
    labels = get_labels()
    backend.detect(prod_dir, labels)
