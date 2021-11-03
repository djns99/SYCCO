#takes an inputname and returns true or false whether the name can be used
import hashlib
import os

def checkName(name):
    name = name.lower()
    name = name.encode('utf-8')
    h = hashlib.sha256(name).hexdigest()

    folders = os.listdir("static/projects")
    for folder in folders:
        if(h == folder):
            return True
    return False

def generateHash(name):
    name = name.lower().encode('utf-8')
    return hashlib.sha256(name).hexdigest()

#generates an sha256 hash from the name
def createProjectDirectory(name):
    print(name)
    h = generateHash(name)
    os.makedirs("static/projects/" + h)
    file = open('static/projects/' + h + '/title.txt', 'w')
    file.write(name)
    file.close()

def pullFolders():
    return os.listdir("static/projects/")
