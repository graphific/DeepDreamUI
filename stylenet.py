#!/usr/bin/python
__author__ = 'Roelof (graphific)'

#python stylenet.py -s ../../neural-style-jcjohnson/examples/inputs/starry_night_crop.png -c ../../neural-style-jcjohnson/examples/inputs/brad_pitt.jpg -o test.png

# Imports
import argparse
import time
import os
import errno
import subprocess

def main(content, style, output):

    command = 'qlua /home/roelof/neural-style-jcjohnson/neural_style.lua -style_image '+str(style)+' -content_image '+str(content)+' -output_image '+str(output)+' -proto_file /home/roelof/neural-style-jcjohnson/models/VGG_ILSVRC_19_layers_deploy.prototxt -model_file /home/roelof/neural-style-jcjohnson/models/VGG_ILSVRC_19_layers.caffemodel'
    print command
    writeToLog("starting "+str(command))
    subprocess.call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    writeToLog("Stylenet Done")


def writeToLog(msg):
    print msg
    filename = 'static/render.log'
    with open(filename,'ab') as f: f.write(msg)

if __name__ == "__main__":
    writeToLog("running Stylenet")
    parser = argparse.ArgumentParser(description='StyleNet')
    parser.add_argument('-c', '--content', help='content file', required=True)
    parser.add_argument('-s', '--style', help='style file', required=True)
    parser.add_argument('-o', '--output', help='place to output file', required=True)
    
    args = parser.parse_args()

    main(args.content, args.style, args.output)
