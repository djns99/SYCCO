from flask import Flask, render_template, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)

UPLOAD_DIR="static/upload_dir"
ALLOWED_EXTENSIONS=["jpg", "png"] # Add supported extensions here

app.config['UPLOAD_DIR'] = UPLOAD_DIR

def get_uploaded_files():
    return os.listdir(app.config["UPLOAD_DIR"])

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/show_images')
def show_images():
    return render_template("show_images.html", filenames=get_uploaded_files(), upload_dir=app.config["UPLOAD_DIR"])

@app.route('/list_images')
def list_images():
    return render_template("list_images.html", filenames=get_uploaded_files())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_file', methods=['GET', 'POST'])
def submit_file():
    if request.method == 'POST':
        # Do something with request
        print(request.files)
        uploaded_file = request.files.get('uploaded-file')
        if uploaded_file == None or uploaded_file.filename == "" or not allowed_file(uploaded_file.filename):
            flash("No data provided")
        else:
            flash("Uploaded: " + uploaded_file.filename)
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(os.path.join(app.config["UPLOAD_DIR"], filename))
    return redirect("/")

@app.route("/delete_image/<string:filename>")
def delete_image(filename):
    if filename in get_uploaded_files():
        os.remove(os.path.join(app.config['UPLOAD_DIR'], filename))
    return redirect("/")



if __name__ == '__main__':
    app.secret_key='sycco' # Make this secure?
    app.run(debug=True)