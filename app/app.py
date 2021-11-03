from flask import Flask, session, render_template, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
#from dash import
from createnew import checkName, createProjectDirectory, pullFolders, generateHash
import labelling_helper
import os
import time
import shutil
import util
import training_helper
app = Flask(__name__)

#All of our routes-----------------------------------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")

# @app.route('/dashboard')
# def dashboard():
#     return render_template('/templates/dashboard/dash_index.html')

## Initialises a project folder
def init_project(name):
    createProjectDirectory(name)
    init_session(name)
    project_dir = util.get_project_dir()
    os.mkdir(os.path.join(project_dir, 'labelled'))
    os.mkdir(os.path.join(project_dir, 'unlabelled'))
    os.mkdir(os.path.join(project_dir, 'predictions'))
    os.mkdir(os.path.join(project_dir, 'backend'))
    os.mkdir(os.path.join(project_dir, 'backend', 'training'))
    os.mkdir(os.path.join(project_dir, 'backend', 'model'))

# Sets up new project session
def init_session(name):
    session['project'] = name
    session['hash'] = generateHash(name)
    if 'labels.txt' in os.listdir(util.get_project_dir()):
        session['labels'] = util.get_labels()
    else:
        session['labels'] = []

    session['training'] = training_helper.get_training_project() == session['hash']

    ## Default to invalidated state
    session['invalidated'] = True
        

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        name = request.form['projectSearch']
        
        # Magic reset code 
        if name == 'Do Some Magic':
            session.clear()
            render_template("/createnew/create_index.html")
            return render_template("/createnew/create_index.html")

        if checkName(name):
            init_session(name)
            return render_template("dashboard/dash_index.html", title=session['project'])
        else:
            flash("Project Not Found", 'danger')
            return redirect("/create_new")
    elif request.method == 'GET':
        if 'project' not in session:
            flash("Please select or create a project", "danger")
            return redirect("/create_new")

    return render_template("dashboard/dash_index.html", title=session['project'])



@app.route("/upload")
def upload():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")
    return render_template("/upload/upload.html",
                           unlabelled=util.get_unlabelled_files(),
                           labelled=util.get_labelled_files(),
                           upload_dir=util.convert_to_uri(util.get_project_dir()))

@app.route('/submit_labels', methods=['POST'])
def submit_label():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return ('', 401)

    request_data = request.get_json()
    filename = labelling_helper.valid_request(request_data)
    if filename == None:
        flash("Failed to create label", 'danger')
        return ('', 400)

    labelling_helper.save_labels(filename, request_data)
    labelling_helper.move_image(filename)

    session['invalidated'] = True
    return ('', 204)

@app.route('/submit_label_file', methods=["GET", "POST"])
def submit_label_file():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")
    if request.method == 'POST':
        # Do something with request
        if not request.files.getlist('uploaded-file'):
            flash("Please provide files")
        else:
            failed= []
            for uploaded_file in request.files.getlist('uploaded-file'):
                # Process JSON File
                message = labelling_helper.process_uploaded_file(uploaded_file) 
                if message != "success":
                    failed += ["{}: {}".format(uploaded_file.filename, message)]
                else:
                    session['invalidated'] = True
            if failed:
                flash("Error Parsing: " + " ".join(failed))
    return redirect("/label")

@app.route('/create_label', methods=['GET', 'POST'])
def create_label():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return ('', 401)

    label_name = request.get_data().decode()
    util.add_label(label_name)
    session['invalidated'] = True
    return ('', 204)

@app.route('/label')
def label():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")
    return render_template("/label/label_index.html",
                           filenames=util.get_unlabelled_files(),
                           upload_dir=util.convert_to_uri(os.path.join(util.get_project_dir(),
                                                                       'unlabelled')),
                           labels=session['labels'] if 'labels' in session else [])

@app.route('/stop_training', methods=['GET', 'POST'])
def stop_training():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")
    if request.method == "POST":
        if session['training']:
            ## TODO Kill process
            training_helper.stop_training()
        else:
            flash("This project does not have training in progress", "danger")

    return redirect('/training')

@app.route('/start_training', methods=['GET', 'POST'])
def start_training():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")
    if request.method == "POST":
        if session['training']:
            flash("This project already has training in progress", "danger")
            session['training'] = False
        else:
            if training_helper.acquire_training_lock():
                session['training'] = True
                session['invalidated'] = False
                training_helper.start_training()
            else:
                flash("Another project is currently training", "danger")
    return redirect('/training')

@app.route('/export_model', methods=['GET', 'POST'])
def export_model():

    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return ('', 401)
        
    if request.method == 'POST':
        checkpoints = [checkpoint[0] for checkpoint in training_helper.get_checkpoints()]
        checkpoint = request.get_data().decode()
        if checkpoint in checkpoints:
            print("exporting")
            training_helper.export_model(checkpoint)

    return ('', 204)

@app.route('/training')
def training():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")

    labelling_complete = len(util.get_unlabelled_files()) == 0
    training_lock_acquired = session['training']
    training_running = training_helper.get_training_project()
    return render_template("/training/train_index.html",
                           run_ids=training_helper.get_checkpoints(),
                           loss=[10, 8, 4, 1, 0.8],
                           accuracy=[0, 0.15, 0.2, 0.19, 0.3],
                           labelling_complete=labelling_complete,
                           training_running=training_running,
                           lock_acquired=training_lock_acquired,
                           checkpoints=training_helper.get_checkpoints())

@app.route('/submit_prediction', methods=['GET', 'POST'])
def submit_prediction():
    if request.method == 'POST':
        # Do something with request
        if not request.files.getlist('uploaded-file'):
            flash("Please provide files")
        
        prod_dir = util.get_project_dir()
        if not os.path.exists(os.path.join(prod_dir, "backend", "tmp")):
            os.mkdir(os.path.join(prod_dir, "backend", "tmp"))
        
        for uploaded_file in request.files.getlist('uploaded-file'):
            if uploaded_file is None or uploaded_file.filename == "":
                flash("Please provide only .jpg or .png files")
            elif not util.allowed_file(uploaded_file.filename):
                flash(uploaded_file.filename + " is not a valid file")
            else:
                uploaded_file.save(os.path.join(prod_dir, "backend", "tmp", uploaded_file.filename))
                
        util.make_prediction()     
        shutil.rmtree(os.path.join(prod_dir, "backend", "tmp"))
    return redirect("/upload")

@app.route('/prediction')
def prediction():
    if 'project' not in session:
        flash("Please select or create a project", "danger")
        return redirect("/create_new")
        
    return render_template("/predictions/pred_index.html", upload_dir=util.get_project_dir(), predictions=util.get_prediction_files())

@app.route('/create_new', methods=['GET', 'POST'])
def create_new():
    if request.method == 'POST':
        #check if a project already exists with that name
        name = request.form['projectName']      
        if not checkName(name):
            init_project(name)
            flash("Successfully created project.", 'success')
            return redirect('/dashboard')
        else:
            flash("Project name already exists.", 'danger')

    return render_template("/createnew/create_index.html")


@app.route('/submit_file', methods=['GET', 'POST'])
def submit_file():
    if request.method == 'POST':
        # Do something with request
        if not request.files.getlist('uploaded-file'):
            flash("Please provide files")

        for i, uploaded_file in enumerate(request.files.getlist('uploaded-file')):
            if uploaded_file == None or uploaded_file.filename == "":
                flash("Please provide only .jpg or .png files")
            elif not util.allowed_file(uploaded_file.filename):
                flash(uploaded_file.filename + " is not a valid file")
            else:
                filename = secure_filename(uploaded_file.filename)
                # Uniquely salt filename
                filename_parts = filename.rsplit('.', 1)
                filename = filename_parts[0] + "-" + str(int(time.time() * 1000000)) + str(i) + "." + filename_parts[1] 
                uploaded_file.save(os.path.join(util.get_project_dir(), 'unlabelled', filename))
                session['invalidated'] = True
    return redirect("/upload")

@app.route("/delete_image/<string:filename>")
def delete_image(filename):
    if filename in util.get_unlabelled_files():
        os.remove(os.path.join(get_project_dir(), 'unlabelled', filename))
        session['invalidated'] = True
    elif filename in util.get_labelled_files():
        label_dir = os.path.join(get_project_dir(), 'labelled')
        os.remove(os.path.join(label_dir, filename))
        os.remove(os.path.join(label_dir, filename + ".labels"))
        session['invalidated'] = True
    return redirect("/upload")

if __name__ == '__main__':
    app.secret_key='sycco' # Make this secure?
    app.run(debug=True, threaded=True)
