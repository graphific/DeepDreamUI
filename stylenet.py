#!/usr/bin/python
__author__ = 'Roelof (graphific)'

#python stylenet.py -s ../../neural-style-jcjohnson/examples/inputs/starry_night_crop.png -c ../../neural-style-jcjohnson/examples/inputs/brad_pitt.jpg -o test.png

# Imports
import argparse
import time
import os
import errno
import subprocess

def main(content, style, output, imagesize, gpu, numiterations, saveiter, contentweight, styleweight):

    if imagesize is None:
        imagesize = 512
    if gpu is None:
        gpu = 0
    if numiterations is None:
        numiterations = 1000
    if saveiter is None:
        saveiter = 100
    if contentweight is None:
        contentweight = 0.1
    if styleweight is None:
        styleweight = 1.0

    command = 'qlua /home/roelof/neural-style-jcjohnson/neural_style.lua -style_image '+str(style)+' -content_image '+str(content)+' -output_image '+str(output)+' -proto_file /home/roelof/neural-style-jcjohnson/models/VGG_ILSVRC_19_layers_deploy.prototxt -model_file /home/roelof/neural-style-jcjohnson/models/VGG_ILSVRC_19_layers.caffemodel -image_size '+str(imagesize)+' -gpu '+str(gpu)+' -num_iterations '+str(numiterations)+' -save_iter '+str(saveiter)+' -content_weight '+str(contentweight)+' -style_weight '+str(styleweight)
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
    parser.add_argument('-z', '--imagesize', help='Maximum height / width of generated image Default: 512', type=int, required=False)
    parser.add_argument('-g', '--gpu', help='Zero-indexed ID of the GPU to use; for CPU mode set --gpu = -1, Default: 0 (1st gpu)', required=False)
    parser.add_argument('-i', '--numiterations', help='Default: 1000', type=int, required=False)
    parser.add_argument('-v', '--saveiter', help='Default: 100', type=int, required=False)
    parser.add_argument('-cw', '--contentweight', help='Default: 0.1', type=float, required=False)
    parser.add_argument('-sw', '--styleweight', help='Default: 1.0', type=float, required=False)
    
    args = parser.parse_args()

    main(args.content, args.style, args.output, args.imagesize, args.gpu, args.numiterations, args.saveiter, args.contentweight, args.styleweight)
