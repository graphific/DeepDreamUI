#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask,jsonify
from flask import render_template, redirect, url_for, request
from flask import abort
from flask.ext.cors import CORS, cross_origin

import json
import sys
import urllib2, urllib
import os
import subprocess
import io
import time
from os import listdir
from os.path import isfile, join

reload(sys)
sys.setdefaultencoding("utf-8")

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/')
def index(text_input= "", text_output= ""):
    return render_template('hello.html', text_input="", text_output="")

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

    finalguide = ''
    if len(guide) != 0:
        finalguide = '--guide ' + str(guide) 

    print "DeepDream Start"
    command = 'python dreamer.py --input static/input/ --output static/output/ --octaves '+str(octaves)+' --octavescale '+str(octavescale)+' --iterations '+str(itterations)+' --jitter '+str(jitter)+' --stepsize '+str(stepsize)+' --blend '+str(blend)+' --layers '+str(layers)+' --gpu '+str(gpu)+' --flow '+str(opticalflow)+' '+finalguide+''
    return subprocess.call(command, shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE).stdout.read()

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
 
@app.route('/api/v1.0/getdirectory', methods=['POST'])
def api_input():
    if not request.json or not 'id' in request.json or not 'type' in request.json:
        abort(400)

    input_directory = request.json['id']
    input_type = request.json['type']

    rootdir = ''
    if input_type == 'input':
        rootdir = 'static/input/'
    if input_type == 'output':
        rootdir = 'static/output/'

    foundfile = []
    founddirs = []

    for root, dirs, files in os.walk(rootdir):
        foundfile += files
        founddirs += dirs

    return jsonify({'root': rootdir, 'files': foundfile, 'dirs': founddirs}), 201
    

if __name__ == '__main__':
    app.run(debug=True)
