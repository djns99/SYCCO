import os
import util
import backend
from flask import session
from pathlib import Path

def get_training_lock_file():
    return os.path.join('static', 'projects', 'training_lock')

def acquire_training_lock():
    lock_file = get_training_lock_file()
    if Path(lock_file).exists():
        return False
    with open(lock_file, "w+") as f:
        f.write(session['hash'])
        return True

def release_training_lock():
    lock_file = get_training_lock_file()
    if Path(lock_file).exists():
        os.remove(get_training_lock_file())
        session['training'] = False

def get_training_project():
    lock_file = get_training_lock_file()
    if not Path(lock_file).exists():
        return None

    with open(lock_file, "r") as f:
        return f.read()

def get_checkpoints():
    prod_dir = util.get_project_dir()
    file_names = os.listdir(os.path.join(prod_dir, "backend", "training"))

    checkpoint_names = [x for x in file_names if x.startswith("model.ckpt-")]
    checkpoints = []
    
    for name in checkpoint_names:
        name = ".".join(name.split(".", 2)[:2])
        ckpt = int(filter(str.isdigit, str(name)))
        
        checkpoint = [name, ckpt]
        if checkpoint not in checkpoints:
            checkpoints.append(checkpoint)
            
    checkpoints = sorted(checkpoints, key=lambda x: x[1])
    return checkpoints

def start_training():
    prod_dir = util.get_project_dir()
    obj_list = util.get_labels()
    
    # set up state for training
    backend.generate_labelmap(prod_dir, obj_list)
    backend.generate_config(prod_dir, obj_list)
    backend.generate_tfrecord(prod_dir, obj_list)
    
    # lock the training file
    acquire_training_lock()
    
    print("starting training")
    # train the model
    backend.train(prod_dir)
    
def stop_training():
    print("stoping training")
    backend.stop()
    release_training_lock()
    session['training'] = False
    
    # clean up training files

def export_model(checkpoint):
    prod_dir = util.get_project_dir()
    backend.export_model(prod_dir, checkpoint)
    
