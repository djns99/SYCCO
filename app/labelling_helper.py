import json
import shutil
import util
import os

def valid_request(data):
    if len(data) != 2:
        return None

    filename = data[0]
    labels = data[1]

    return filename if filename in util.get_unlabelled_files() else None
        
        
def save_labels(filename, request_data):
    label_dir = os.path.join(util.get_project_dir(), 'labelled')
    
    label_file = open(os.path.join(label_dir, filename + ".labels"), "w+")
    label_file.write(str(json.dumps(request_data)))
    label_file.close()
    
def move_image(filename):
    unlabel_file = os.path.join(util.get_project_dir(), 'unlabelled', filename)
    label_file = os.path.join(util.get_project_dir(), 'labelled', filename)
    
    shutil.move(unlabel_file, label_file)

def process_uploaded_file(uploaded_json_file):
    unlabelled_files = util.get_unlabelled_files()
    json_data = json.loads(uploaded_json_file.read().decode())
    
    if len(json_data) != 2:
        return "Invalid JSON format."

    filename = json_data[0]
    labels = json_data[1]
    
    new_labels = []
    
    for label in labels:
        if len(label) != 5:
            return "Invalid bounding box format."
        
        if not isinstance(label[4], str):
            return "Invalid label."
        
        for coord in label[:-1]:
            if not isinstance(coord, float) or coord < 0 or coord > 1:
                return "Invalid coordinates."
        
        if label[4] not in util.get_labels():
            new_labels += [label[4]]
    
    filename_components = filename.rsplit('.', 1)
    
    for unlabelled in unlabelled_files:
        if unlabelled.startswith(filename_components[0]) and unlabelled.endswith(filename_components[1]):
            # Found
            
            save_labels(unlabelled, [unlabelled, labels])
            move_image(unlabelled)

            for new_label in new_labels:
                util.add_label(new_label)

            return "success"
            
    return "No images matching name {}".format(filename)