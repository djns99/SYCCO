
import subprocess
import io
import json
import os
import cv2
import shutil
import util
import psutil
import numpy as np
import tensorflow as tf
import pandas as pd

from PIL import Image
from utils import label_map_util
from utils import visualization_utils as vis_util
from collections import namedtuple
from object_detection.utils import dataset_util

process = -1

def generate_labelmap(prod_dir, object_names):
    labelmap = open(os.path.join(prod_dir, 'backend', 'model', 'labelmap.pbtxt'), "w")
    
    i = 1
    for object_name in object_names:
        labelmap.write("item {{\n  id: {}\n  name: \'{}\'\n}}\n".format(str(i), str(object_name)))
        i = i + 1
        
    labelmap.close()
    
    
def generate_config(prod_dir, object_names):
    shutil.copyfile(os.path.join("tensorflow", "faster_rcnn_inception_v2_pets.config"),
                    os.path.join(prod_dir, "backend", "model", "tmp.config")) 
                    
    config_file = open(os.path.join(prod_dir, "backend", "model", "tmp.config"), 'r')
    
    new_config_file = open(os.path.join(prod_dir, "backend", "model", "config.config"), 'w')
    
    num_classes = len(object_names)
    cwd = os.getcwd()
    
    for line in config_file:
        if 'num_classes' in line:
            line = "  num_classes: {}\n".format(num_classes)  
            
        elif 'fine_tune_checkpoint' in line:
            line = "  fine_tune_checkpoint: \"{}\"\n".format(os.path.join(cwd, "tensorflow", "faster_rcnn_inception_v2_coco_2018_01_28", "model.ckpt"))  
            
        elif 'input_path: TRAIN' in line:
            line = "    input_path: \"{}\"\n".format(os.path.join(cwd, prod_dir, "backend", "model", "training.record")) 
            
        elif 'input_path: TEST' in line:
            line = "    input_path: \"{}\"\n".format(os.path.join(cwd, prod_dir, "backend", "model", "test.record")) 
        
        elif 'label_map_path' in line:
            line = "  label_map_path: \"{}\"\n".format(os.path.join(cwd, prod_dir, "backend", "model", "labelmap.pbtxt"))  
              
        new_config_file.write(line)
    
    os.remove(os.path.join(prod_dir, "backend", "model", "tmp.config"))

def class_text_to_int(row_label):
    i = 1
    for label in util.get_labels():
        if label == row_label:
            return i
        i = i + 1
    return None

def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]


def create_tf_example(group, path):
    with tf.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = group.filename.encode('utf8')
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for index, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(row['class'].encode('utf8'))
        classes.append(class_text_to_int(row['class']))

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example


def json_to_csv(prod_dir):
    image_dir = os.path.join(prod_dir, "labelled")
    
    csv = open(os.path.join(prod_dir, 'backend', 'model', 'training.csv'), "w")
    csv.write("filename,width,height,class,xmin,ymin,xmax,ymax\n")
    
    files = os.listdir(image_dir)
    image_files = [x for x in files if not x.endswith("labels")]
    
    for img in image_files:
        w, h = Image.open(os.path.join(image_dir, img)).size  
        
        with open(os.path.join(image_dir, img + ".labels")) as f:
            d = json.load(f)
        
        for box in d[1]:
            csv.write("{},{},{},{},{},{},{},{}\n".format(img, w, h, box[4], int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)))     
    csv.close()
   
def generate_tfrecord(prod_dir, object_names):

    json_to_csv(prod_dir)
    
    csv_input = os.path.join(prod_dir, 'backend', 'model', 'training.csv')
    image_dir = os.path.join(prod_dir, "labelled")
    output_path = os.path.join(prod_dir, 'backend', 'model', 'training.record')
    
    writer = tf.python_io.TFRecordWriter(output_path)
    path = os.path.join(os.getcwd(), image_dir)
    examples = pd.read_csv(csv_input)
    grouped = split(examples, 'filename')
    for group in grouped:
        tf_example = create_tf_example(group, path)
        writer.write(tf_example.SerializeToString())

    writer.close()
    output_path = os.path.join(os.getcwd(), output_path)
    print('Successfully created the TFRecords: {}'.format(output_path))
          
         
  
def train(prod_dir):
    global process
    train_dir = os.path.join(prod_dir, "backend", "training")
    pipeline_config_path = os.path.join(prod_dir, "backend", "model", "config.config")
    
    command = "python train.py --train_dir={} --pipeline_config_path={}".format(train_dir, pipeline_config_path)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def stop():
    global process
    if process == -1:
        return
    else:
        kill(process.pid)
        process = -1
   
def export_model(prod_dir, model_num):
    file_names = os.listdir(os.path.join(prod_dir, "backend", "training"))
    newlist = [x for x in file_names if x.startswith("model.ckpt-")]

    pipeline_config_path = os.path.join(prod_dir, "backend", "model", "config.config")
    trained_checkpoint_prefix = os.path.join(prod_dir, "backend", "training", model_num)
    
    new_model_dir = os.path.join(prod_dir, "backend", "output-model")
    if os.path.exists(new_model_dir):
        shutil.rmtree(new_model_dir)
        
    os.makedirs(new_model_dir)
    
    command = "python export_inference_graph.py --input_type image_tensor --pipeline_config_path {} --trained_checkpoint_prefix {} --output_directory {}".format(pipeline_config_path, trained_checkpoint_prefix, new_model_dir)
    
    subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    
    
def detect(prod_dir, object_names):

    ckpt_path = os.path.join(prod_dir, "backend", "output-model", "frozen_inference_graph.pb" )
    num_classes = len(object_names)
    label_map = label_map_util.load_labelmap(os.path.join(prod_dir, "backend", "model", "labelmap.pbtxt"))
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=num_classes, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    # Load the Tensorflow model into memory.
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(ckpt_path, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)

    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
    
    file_names = os.listdir(os.path.join(prod_dir, "backend", "tmp"))
    image_list = [x for x in file_names if x.endswith(".png") or x.endswith(".jpg")]
    
    for image_name in image_list:

        image_path = os.path.join(prod_dir, "backend", "tmp", image_name)
        image = cv2.imread(image_path)
        image_expanded = np.expand_dims(image, axis=0)

        # Perform the actual detection by running the model with the image as input
        (boxes, scores, classes, num) = sess.run(
            [detection_boxes, detection_scores, detection_classes, num_detections],
            feed_dict={image_tensor: image_expanded})

        # Draw the results of the detection (aka 'visulaize the results')
        vis_util.visualize_boxes_and_labels_on_image_array(
            image,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            category_index,
            use_normalized_coordinates=True,
            line_thickness=14,
            min_score_thresh=0.80)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  
        img = Image.fromarray(image, "RGB")  
        img.save(os.path.join(prod_dir, "predictions", image_name))
            
