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
import datetime
import argparse
import yaml

import os
import io
from os import listdir
from os.path import isfile, join
from os import path
import subprocess

os.environ['GLOG_minloglevel'] = '2' 

reload(sys)
sys.setdefaultencoding("utf-8")

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

rootfolder = ''
default_port = 5000
if 'local' in cfg:
    loc = cfg['local']
    print loc
    if 'folder' in loc:
        rootfolder = loc['folder']
    if 'default_port' in loc:
        default_port = loc['default_port']

app = Flask(__name__)

UPLOAD_FOLDER = rootfolder+'static/input'
ALLOWED_EXTENSIONS = set(['mov', 'mp4', 'png', 'jpg', 'jpeg', 'gif'])
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

procArray = []

# Main template
@app.route('/')
def index(text_input= "", text_output= ""):
    return render_template('hello.html', text_input="", text_output="")

# Start deepdream renderer
@app.route('/api/v1.0/getrender', methods=['POST'])
def api_render():
    global procArray
    print request.json
    presets = request.json['presets'] #low, medium, high
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
    author = request.json['author']
    drop = request.json['sudroptop']
    keep = request.json['sukeep']
    algorithm = request.json['algorithm']
    renderstop(author)

    finalguide = ''
    if len(guide) != 0:
        finalguide = '--guide ' + str(guide)
    
    if True: #'deepdream' in algorithm:
        preview = 96
        if presets == 'low': preview = 20
        elif presets == 'medium': preview = 50

        print "DeepDream Start"
        command = 'python dreamer.py --preview '+str(preview)+' --input '+str(inputdir)+' --output '+str(outputdir)+' --octaves '+str(octaves)+' --octavescale '+str(octavescale)+' --iterations '+str(itterations)+' --jitter '+str(jitter)+' --stepsize '+str(stepsize)+' --blend '+str(blend)+' --layers '+str(layers)+' --gpu '+str(gpu)+' --flow '+str(opticalflow)+' --network '+str(network)+' --drop '+str(drop)+' --keep '+str(keep)+' '+finalguide+''
    else: #stylenet
        print "Stylenet Start"
        gpu -= 1
        imagesize = 900
        numiterations = itterations
        saveiter = itterations
        contentweight = 0.1
        styleweight = 1.0
        command = 'python stylenet.py --content '+str(inputdir)+' --style '+str(guide)+' --output '+str(outputdir)+' --imagesize '+str(imagesize)+' --gpu '+str(gpu)+' --numiterations '+str(numiterations)+' --saveiter '+str(saveiter)+' --contentweight '+str(contentweight)+' --styleweight '+str(styleweight)+''
    print command 
    newproc = subprocess.Popen("exec " + command, stdout=subprocess.PIPE, shell=True)
    newProcEntry = [newproc,author]
    procArray.append(newProcEntry)
    print procArray
    return 'running'

def renderstop(author):
    global procArray

    for proc in procArray:
        if(proc[1] == author):
            proc[0].kill()
            proc[0].terminate();
            procArray.remove(proc)
            print "DeepDream KILL"
    print procArray

# Stop deepdream renderer
@app.route('/api/v1.0/stoprender', methods=['POST'])
def api_renderstop():
    renderstop(request.json['author'])
    return 'killed'

# Start stylenet renderer
@app.route('/api/v1.0/getstyle', methods=['POST'])
def api_style():
    global procArrayStyle

    content = request.json['content'] 
    style = request.json['style'] 
    output = request.json['output']
    imagesize = request.json['imagesize']
    gpu = request.json['gpu']
    numiterations = request.json['numiterations']
    saveiter = request.json['saveiter']
    contentweight = request.json['contentweight']
    styleweight = request.json['styleweight']

    print "StyleNet Start"
    command = 'python stylenet.py --content '+str(preview)+' --style '+str(style)+' --output '+str(output)+' --imagesize '+str(imagesize)+' --gpu '+str(gpu)+' --numiterations '+str(numiterations)+' --saveiter '+str(saveiter)+' --contentweight '+str(contentweight)+' --styleweight '+str(styleweight)+''
    newproc = subprocess.Popen("exec " + command, stdout=subprocess.PIPE, shell=True)
    newProcEntry = [newproc,author]
    procArray.append(newProcEntry)
    print procArrayStyle
    return 'running'

def stylestop(author):
    global procArrayStyle

    for proc in procArrayStyle:
        if(proc[1] == author):
            proc[0].kill()
            proc[0].terminate();
            procArrayStyle.remove(proc)
            print "StyleNet KILL"
    print procArrayStyle

# Stop stylenet renderer
@app.route('/api/v1.0/stopstyle', methods=['POST'])
def api_stylestop():
    stylestop(request.json['author'])
    return 'killed'
 
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

    foundfile.sort()
    founddirs.sort()
    return jsonify({'root': root, 'files': foundfile, 'dirs': founddirs}), 201

# Exctract frames of movie
@app.route('/api/v1.0/extractmovie', methods=['POST'])
def api_extractmovie():
    if not request.json or not 'movie' in request.json or not 'directory' in request.json:
        abort(400)
    mfile = request.json['movie'] #low, medium, high
    mdir = request.json['directory'] 
    command = 'python dreamer.py --input '+str(mfile)+' --output '+str(mdir)+' --extract 1'
    subprocess.Popen("exec " + command, stdout=subprocess.PIPE, shell=True)
    return 'createmovie'

# make movie from frames
@app.route('/api/v1.0/makemovie', methods=['POST'])
def api_makemovie():
    if not request.json or not 'movie' in request.json or not 'directory' in request.json:
        abort(400)
    mfile = request.json['movie']
    mdir = request.json['directory'] 
    command = 'python dreamer.py --framerate 25 --input '+str(mfile)+' --output '+str(mdir) + ' --create 1 '
    subprocess.Popen("exec " + command, stdout=subprocess.PIPE, shell=True)
    return 'createmovie'

# Create new directory
@app.route('/api/v1.0/makefolder', methods=['POST'])
def api_makefolder():
    if not request.json or not 'id' in request.json:
        abort(400)
    foldername = request.json['id']
    command = 'mkdir ' + foldername
    response = subprocess.call(command, shell=True)
    return jsonify({'output': response}), 201

# Create new job
@app.route('/api/v1.0/makejob', methods=['POST'])
def api_makejob():
    if not request.json or not 'job' in request.json or not 'dir' in request.json:
        abort(400)
    newjob = request.json['job']
    newjobtitle = newjob['jobname']
    newjobusername = newjob['author']
    newjobdir = request.json['dir']

    #date = str(time.time())
    newjobdate = newjob['date']
    filename = newjobdir + '/' +newjobtitle+'_'+newjobdate+'_'+newjobusername+'.json'

    with open(filename, 'w+') as outfile:
        json.dump(newjob, outfile)

    response = "job created: " + filename
    return jsonify({'output': response}), 201

# Show jobs
@app.route('/api/v1.0/getjobs', methods=['POST'])
def api_getjobs():
    foundfile = []
    jobspath = 'static/jobs/'

    # found files
    for path, subdirs, files in os.walk(jobspath):
        matches = []
        for name in files:
            found = os.path.join(path, name)
            matches.append(found)
        foundfile = sorted(matches, key=os.path.getmtime,reverse=True)
        break

    return jsonify({'root': jobspath, 'files': foundfile}), 201
 
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

# Upload Files
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    print request
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template('hello.html')



# Start Flask App
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DeepDreamUI')
    parser.add_argument('--port', '-p', default=default_port, type=int)

    args = parser.parse_args()

    app.run(debug=True,port=args.port)
