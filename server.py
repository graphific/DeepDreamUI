#!/usr/bin/python
# -*- coding: utf-8 -*-

import flask
from flask import Flask,jsonify
from flask import render_template, redirect, url_for, request
from flask import abort
from flask.ext.cors import CORS, cross_origin
from werkzeug import secure_filename

import json
import sys
import urllib2, urllib
import time

import os
import io

from os import listdir
from os.path import isfile, join
from os import path
import subprocess

from shelljob import proc
import eventlet
eventlet.monkey_patch()


reload(sys)
sys.setdefaultencoding("utf-8")

UPLOAD_FOLDER = '/Users/samim/sites/DeepDreamUi/static/input'
ALLOWED_EXTENSIONS = set(['mov', 'mp4', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index(text_input= "", text_output= ""):
    return render_template('hello.html', text_input="", text_output="")

# Start deepdream renderer
@app.route('/api/v1.0/getrender', methods=['POST'])
def api_render():
    network = request.json['network'] 
    layers = request.json['layers']
    octaves = request.json['octaves']
    octavescale = request.json['octavescale']
    itterations = request.json['itterations']
    jitter = request.json['jitter']
    stepsize = request.json['stepsize']
    blend = request.json['blend']
    opticalflow = request.json['opticalflow']
    gpu = request.json['gpu']
    guide = request.json['guide']
    inputdir = request.json['input']
    outputdir = request.json['output']

    finalguide = ''
    if len(guide) != 0:
        finalguide = '--guide ' + str(guide) 

    print "DeepDream Start"
    command = 'python dreamer.py --preview 0 --input '+str(inputdir)+' --output '+str(outputdir)+' --octaves '+str(octaves)+' --octavescale '+str(octavescale)+' --iterations '+str(itterations)+' --jitter '+str(jitter)+' --stepsize '+str(stepsize)+' --blend '+str(blend)+' --layers '+str(layers)+' --gpu '+str(gpu)+' --flow '+str(opticalflow)+' '+finalguide+''
    return subprocess.call(command, shell=True)

# Show console
@app.route('/api/v1.0/getconsole', methods=['POST'])
def api_console():
    if not request.json or not 'id' in request.json:
        abort(400)

    text_input = request.json['id']
    response = ''
    with open('render.log', 'r') as fin:
        response = fin.read()
        print response
    return jsonify({'output': response}), 201
 
# Show directories
@app.route('/api/v1.0/getdirectory', methods=['POST'])
def api_input():
    if not request.json or not 'id' in request.json or not 'type' in request.json:
        abort(400)

    root = request.json['id']
    input_type = request.json['type']

    foundfile = []
    founddirs = []

    # found files
    for path, subdirs, files in os.walk(root):
        for name in files:
            found = os.path.join(path, name)
            foundfile.append(found)
        break

    # found sub-directories
    for path, subdirs, files in os.walk(root):
        for name in subdirs:
            found = os.path.join(path, name)
            founddirs.append(found)
        break

    return jsonify({'root': root, 'files': foundfile, 'dirs': founddirs}), 201
  
# Create new directory
@app.route('/api/v1.0/makefolder', methods=['POST'])
def api_makefolder():
    if not request.json or not 'id' in request.json:
        abort(400)
    foldername = request.json['id'] 


    command = 'mkdir ' + foldername
    response = subprocess.call(command, shell=True)

    return jsonify({'output': response}), 201


# Delete Files/Folders
@app.route('/api/v1.0/delete', methods=['POST'])
def api_delete():
    if not request.json or not 'id' in request.json:
        abort(400)
    files = request.json['id'] 
    
    filestodelete = ''
    for file in files:
        filestodelete += file + ' '

    print filestodelete
    command = 'rm -rf ' + filestodelete
    response = subprocess.call(command, shell=True)
    return jsonify({'output': response}), 201





# UPLOAD FILES
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template('hello.html')





# STREAM Console Output / Start Sub-Process
@app.route( '/stream' )
def stream():
    g = proc.Group()
    #p = g.run( [ "bash", "-c", "for ((i=0;i<100;i=i+1)); do echo $i; sleep 1; done" ] )
    p = g.run( [ "python", "dreamer.py", "-i", "static/input", "-o", "static/output" ] )

    def read_process():
        while g.is_pending():   
            lines = g.readlines()
            for proc, line in lines:
                yield "data:" + line + "\n\n"
                #p.kill()

    return flask.Response( read_process(), mimetype= 'text/event-stream' )

@app.route('/s')
def get_page():
    return flask.send_file('console.html')






# Start Flask App
if __name__ == '__main__':
    app.run(debug=True)
