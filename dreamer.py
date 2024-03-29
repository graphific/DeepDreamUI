#!/usr/bin/python
__author__ = 'Samim.io'
__author__ = 'Roelof (graphific)'

# Imports
import argparse
import time
import os
import errno
import subprocess
#import natsort

from cStringIO import StringIO
import numpy as np
import scipy.ndimage as nd
import PIL.Image
from google.protobuf import text_format
import caffe
import math

os.environ['GLOG_minloglevel'] = '2' 
jpg_quality = 95

# a couple of utility functions for converting to and from Caffe's input image layout
def preprocess(net, img):
    return np.float32(np.rollaxis(img, 2)[::-1]) - net.transformer.mean['data']


def deprocess(net, img):
    return np.dstack((img + net.transformer.mean['data'])[::-1])


def objective_L2(dst):
    dst.diff[:] = dst.data


# First we implement a basic gradient ascent step function, applying the first two tricks // 32:
def make_step(net, step_size=1.5, end='inception_4c/output', jitter=32, clip=True, objective=objective_L2, controlUnits=False, dropTop = 0, keep = 1, keepFactor = 1.0, gamma = 4.0, suppressFactor = 0.000001, keepIndices = None):
    #def make_step(net, step_size=1.5, end='inception_4c/output', jitter=32, clip=True, objective=objective_L2):
    '''Basic gradient ascent step.'''

    src = net.blobs['data']  # input image is stored in Net's 'data' blob
    dst = net.blobs[end]

    ox, oy = np.random.randint(-jitter, jitter + 1, 2)
    src.data[0] = np.roll(np.roll(src.data[0], ox, -1), oy, -2)  # apply jitter shift

    net.forward(end=end)
    
    if controlUnits:
        v = []
        if (keepIndices is None):
            for i in range( 0, len(dst.data[0])):
                v.append( np.sum(dst.data[0][i]))
            keepIndices = np.array(np.argpartition(v, -(keep+dropTop))[-(keep+dropTop):][:keep])

        if not (keepIndices is None):
            for i in range( len(dst.data[0])):
                if i in keepIndices:
                    dstmax = dst.data[0][i].max() * keepFactor
                    if dstmax > 0.0:
                        #if invert is True:
                        #    dst.data[0][i] = pow(1.0-dst.data[0][i]/dstmax,gamma) * dstmax
                        #else:
                        dst.data[0][i] = pow(dst.data[0][i]/dstmax,gamma) * dstmax
                else:
                    dstmax = dst.data[0][i].max()
                    if dstmax > 0.0:
                        dst.data[0][i] *= suppressFactor / dstmax
        else:
            for i in range( len(dst.data[0])):
                dstmax = dst.data[0][i].max()
                if dstmax > 0 and gamma != 1.0:
                    #if invert is True:
                    #    dst.data[0][i] = pow(1.0-dst.data[0][i]/dstmax,gamma) * dstmax
                    #else:
                    dst.data[0][i] = pow(dst.data[0][i]/dstmax,gamma) * dstmax
    else:
        keepIndices = "all"

    objective(dst)  # specify the optimization objective
    net.backward(start=end)
    g = src.diff[0]
    # apply normalized ascent step to the input image
    src.data[:] += step_size / np.abs(g).mean() * g
    src.data[0] = np.roll(np.roll(src.data[0], -ox, -1), -oy, -2)  # unshift image

    if clip:
        bias = net.transformer.mean['data']
        src.data[:] = np.clip(src.data, -bias, 255 - bias)
    return keepIndices

def deepdream(net, base_img, iter_n=10, octave_n=4, step_size=1.5, octave_scale=1.4, jitter=32,
              recalculateKeepEachOctave = False, controlUnits = False,
              keep = 2, dropTop=0, keepFactor = 1.0, 
              gamma = 1.0, suppressFactor = 0.0, keepIndices = None,
              end='inception_4c/output', clip=True, **step_params):

    #def deepdream(net, base_img, iter_n=10, octave_n=4, step_size=1.5, octave_scale=1.4, jitter=32,
    #          end='inception_4c/output', clip=True, **step_params):
    # prepare base images for all octaves
    octaves = [preprocess(net, base_img)]
    for i in xrange(octave_n - 1):
        octaves.append(nd.zoom(octaves[-1], (1, 1.0 / octave_scale, 1.0 / octave_scale), order=1))

    src = net.blobs['data']
    detail = np.zeros_like(octaves[-1])  # allocate image for network-produced details
    for octave, octave_base in enumerate(octaves[::-1]):
        h, w = octave_base.shape[-2:]
        if octave > 0:
            # upscale details from the previous octave
            h1, w1 = detail.shape[-2:]
            detail = nd.zoom(detail, (1, 1.0 * h / h1, 1.0 * w / w1), order=1)

        src.reshape(1, 3, h, w)  # resize the network's input image size
        src.data[0] = octave_base + detail
        for i in xrange(iter_n):
            #make_step(net, end=end, step_size=step_size, jitter=jitter, clip=clip, **step_params)

            keepIndices = make_step(net, end=end, step_size=step_size, jitter=jitter, clip=clip, keepFactor = keepFactor, gamma = gamma,
                      keep = keep, dropTop = dropTop, controlUnits = controlUnits,
                      suppressFactor = suppressFactor,
                      keepIndices = keepIndices, **step_params)
            if controlUnits:
                if recalculateKeepEachOctave is True:
                    keepIndices = None
                if i is 2 and math.isnan(vis.mean()):
                    return deprocess(net, src.data[0]),keepIndices
            
            #keepIndices = "all"
            # visualization
            vis = deprocess(net, src.data[0])
            if not clip:  # adjust image contrast if clipping is disabled
                vis = vis * (255.0 / np.percentile(vis, 99.98))
            print octave, i, end, vis.shape

        # extract details produced on the current octave
        detail = src.data[0] - octave_base
    # returning the resulting image
    return deprocess(net, src.data[0]),keepIndices

# utility function that loads an image, optionally limits
# the size and removes an alpha channel in case there is one
def loadImageFromUrlOrLocalPath(pathOrUrl, maxSideLength = 1920, width = -1, height = -1, previewImage = False ):
    if 'http' in pathOrUrl:
        file = cStringIO.StringIO(urllib.urlopen(pathOrUrl).read())
        png = PIL.Image.open(file)
    else: 
        png = PIL.Image.open(pathOrUrl)
    s = png.size
    if width > 0 and height > 0:
    	png = png.resize([width,height], PIL.Image.ANTIALIAS)
    elif ( np.max(s) > maxSideLength ):
        ratio = float(maxSideLength)/float(np.max(s))
        png = png.resize([int(s[0]*ratio), int(s[1]*ratio)], PIL.Image.ANTIALIAS)
    
    if png.mode == 'RGBA':
        src = PIL.Image.new("RGB", png.size, (255, 255, 255))
        src.paste(png, mask=png.split()[3])
    else:
        src = png
        
    #img = np.float32(src)
    if previewImage is True:
        showarray(np.float32(src))
        
    return src
    
# Animaton functions
def resizePicture(image, width):
    img = PIL.Image.open(image)
    basewidth = width
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    return img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)


def morphPicture(filename1, filename2, blend, width):
    img1 = PIL.Image.open(filename1)
    img2 = PIL.Image.open(filename2)
    if width is not 0:
        img2 = resizePicture(filename2, width)
    return PIL.Image.blend(img1, img2, blend)


def make_sure_path_exists(path):
    # make sure input and output directory exist, if not create them. If another error (permission denied) throw an error.
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def writeToLog(msg):
	print msg
	filename = 'static/render.log'
	with open(filename,'ab') as f: f.write(msg)
        

def main(inputdir, outputdir, preview, octaves, octave_scale, iterations, jitter, zoom, stepsize, blend, layers, guide,
         gpu, flow, network, drop, keep):

    # input var setup
    make_sure_path_exists(inputdir)
    make_sure_path_exists(outputdir)
    if preview is None: preview = 0
    if octaves is None: octaves = 4
    if octave_scale is None: octave_scale = 1.5
    if iterations is None: iterations = 10
    if jitter is None: jitter = 32
    if jitter is None: jitter = 32
    if zoom is None: zoom = 1
    if stepsize is None: stepsize = 1.5
    if blend is None: blend = 0.5
    if layers is None: layers = ['inception_4c/output']
    if gpu is None: gpu = 1
    if flow is None: flow = 0
    if network is None: network = 'googlelenet'
    if keep is 0:
        control = False
    else:
        control = True
    # net.blobs.keys()

    writeToLog("DeepDream Start with " + network + '\n'+ '\n')

    # Loading DNN model
    if 'googlelenet' in network:
        model_name = 'bvlc_googlenet'
        model_path = '../../caffe/models/' + model_name + '/'
        net_fn = model_path + 'deploy.prototxt'
        param_fn = model_path + 'bvlc_googlenet.caffemodel'
    else:
        model_name = 'googlenet_places205'
        model_path = '../../caffe/models/' + model_name + '/'
        net_fn = model_path + 'deploy_places205.protxt'
        param_fn = model_path + 'googlelet_places205_train_iter_2400000.caffemodel'
    writeToLog(model_path)
    if gpu > 0:
        caffe.set_mode_gpu()
        caffe.set_device(gpu-1)

    # Patching model to be able to compute gradients.
    # Note that you can also manually add "force_backward: true" line to "deploy.prototxt".
    model = caffe.io.caffe_pb2.NetParameter()
    text_format.Merge(open(net_fn).read(), model)
    model.force_backward = True
    open('tmp.prototxt', 'w').write(str(model))

    net = caffe.Classifier('tmp.prototxt', param_fn,
                           mean=np.float32([104.0, 116.0, 122.0]),  # ImageNet mean, training set dependent
                           channel_swap=(2, 1, 0))  # the reference model has channels in BGR order instead of RGB

    
    # load images & sort them
    vidinput = os.listdir(inputdir)
    vidinput.sort()

    #vidinput = natsort.natsorted(os.listdir(inputdir))
    vids = []
    var_counter = 1

    # create list
    for frame in vidinput:
        if frame.endswith('.png') or frame.endswith('.jpg') or frame.endswith('.jpeg'):
            vids.append(frame)

    fullpath = inputdir + '/' + vids[0]
    img = loadImageFromUrlOrLocalPath(fullpath)

    if preview is not 0:
        img = loadImageFromUrlOrLocalPath(fullpath, maxSideLength=preview)
    frame = np.float32(img)


    # guide
    if guide is not None:
        
        if not preview == 0:
            guideimgresized = loadImageFromUrlOrLocalPath(fullpath, maxSideLength=preview)
        else:
            guideimgresized = loadImageFromUrlOrLocalPath(fullpath, width=224, height=224)
        guide = np.float32(guideimgresized)
        end = layers[0]  # 'inception_3b/output'
        h, w = guide.shape[:2]
        src, dst = net.blobs['data'], net.blobs[end]
        src.reshape(1, 3, h, w)
        src.data[0] = preprocess(net, guide)
        net.forward(end=end)
        guide_features = dst.data[0].copy()

    def objective_guide(dst):
        x = dst.data[0].copy()
        y = guide_features
        ch = x.shape[0]
        x = x.reshape(ch, -1)
        y = y.reshape(ch, -1)
        A = x.T.dot(y)  # compute the matrix of dot-products with guide features
        dst.diff[0].reshape(ch, -1)[:] = y[:, A.argmax(1)]  # select ones that match best

    def getFrame(net, frame, endparam, drop, keep, control):
        # dream frame
        if guide is None:
            return deepdream(net, frame, iter_n=iterations, step_size=stepsize, octave_n=octaves,
                             octave_scale=octave_scale, jitter=jitter, end=endparam, controlUnits=control, keep=keep, dropTop=drop)
        else:
            return deepdream(net, frame, iter_n=iterations, step_size=stepsize, octave_n=octaves,
                             octave_scale=octave_scale, jitter=jitter, end=endparam, objective=objective_guide, controlUnits=control, keep=keep, dropTop=drop)

    def getStats(saveframe, var_counter, vids, difference):
        # Stats
        ret = ''
        ret += 'Saving Image As: ' + saveframe + '\n'
        ret += 'Frame ' + str(var_counter) + ' of ' + str(len(vids)) + '\n'
        ret += 'Frame Time: ' + str(difference) + 's' + '\n'
        timeleft = difference * (len(vids) - var_counter)
        m, s = divmod(timeleft, 60)
        h, m = divmod(m, 60)
        ret += 'Estimated Total Time Remaining: ' + str(timeleft) + 's (' + "%d:%02d:%02d" % (h, m, s) + ')' + '\n'
        ret += '\n'
        writeToLog(ret)

    if flow > 0:
        import cv2

        # optical flow
        if not preview == 0:
            img = loadImageFromUrlOrLocalPath(inputdir + '/' + vids[0], maxSideLength=preview)
        else:
            img = loadImageFromUrlOrLocalPath(inputdir + '/' + vids[0])
        img = np.float32(img)
        h, w, c = img.shape
        hallu,keepIndices = getFrame(net, img, layers[0], drop, keep, control)
        np.clip(hallu, 0, 255, out=hallu)
        PIL.Image.fromarray(np.uint8(hallu)).save(outputdir + '/' + 'frame_000000.jpg',quality=jpg_quality)
        grayImg = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        for v in range(len(vids)):
            if var_counter < len(vids):
                previousImg = img
                previousGrayImg = grayImg
                previoushallu = hallu

                newframe = inputdir + '/' + vids[v + 1]
                writeToLog( 'Processing: ' + str(newframe) + '\n')
                endparam = layers[var_counter % len(layers)]

                if not preview == 0:
                    img = loadImageFromUrlOrLocalPath(newframe, maxSideLength=preview)
                else:
                    img = loadImageFromUrlOrLocalPath(newframe)
                img = np.float32(img)
                grayImg = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                flow = cv2.calcOpticalFlowFarneback(previousGrayImg, grayImg, pyr_scale=0.5, levels=3, winsize=15,
                                                    iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
                flow = -flow
                flow[:, :, 0] += np.arange(w)
                flow[:, :, 1] += np.arange(h)[:, np.newaxis]
                halludiff = hallu - previousImg
                halludiff = cv2.remap(halludiff, flow, None, cv2.INTER_LINEAR)
                hallu = img + halludiff

                now = time.time()
                hallu,keepIndices = getFrame(net, hallu, endparam, drop, keep, control)
                later = time.time()
                difference = int(later - now)
                saveframe = outputdir + '/' + 'frame_%06d.jpg' % (var_counter)
                getStats(saveframe, var_counter, vids, difference)

                np.clip(hallu, 0, 255, out=hallu)
                
                #if not blend == 0:
                #    #print np.uint8(previoushallu).shape
                #    #print np.uint8(previousImg).shape
     
                #    #hallu = PIL.Image.blend(PIL.Image.fromarray(np.uint8(previoushallu)-np.uint8(previousImg)), PIL.Image.fromarray(np.uint8(hallu)-np.uint8(img)), blend)
                #    #hallu = morphPicture(PIL.Image.fromarray(np.uint8(previoushallu-previousImg)), PIL.Image.fromarray(np.uint8(hallu-img)), blend, preview) + img
                #else:
                PIL.Image.fromarray(np.uint8(hallu)).save(saveframe,quality=jpg_quality)
                writeToLog( 'channels used:: ' + str(keepIndices) + '\n') 
                var_counter += 1
            else:
                writeToLog('Finished processing all frames'+ '\n')
    else:
        # process anim frames
        for v in range(len(vids)):
            if var_counter < len(vids):
                vid = vids[v]
                h, w = frame.shape[:2]
                s = 0.05  # scale coefficient  

                writeToLog('Processing: ' + str(inputdir) + '/' + str(vid) + '\n')

                # setup
                now = time.time()
                endparam = layers[var_counter % len(layers)]
                frame,keepIndices = getFrame(net, frame, endparam, drop, keep, control)
                later = time.time()
                difference = int(later - now)
                saveframe = outputdir + '/' + 'frame_%06d.jpg' % (var_counter)
                getStats(saveframe, var_counter, vids, difference)

                # save image
                PIL.Image.fromarray(np.uint8(frame)).save(saveframe,quality=jpg_quality)

                # setup next image
                newframe = inputdir + '/' + vids[v + 1]

                #blend 0.1 is keep 10%, 0.9 = keep 90% of prev picture
                if not blend == 0:
                    #if preview is not 0:
                    #img2 = resizePicture(filename2, preview)
                    frame = PIL.Image.blend(loadImageFromUrlOrLocalPath(newframe), loadImageFromUrlOrLocalPath(saveframe), blend)

                    #frame = morphPicture(newframe, saveframe, blend, preview)
                else:
                    frame = loadImageFromUrlOrLocalPath(newframe)

                #if not blend == 0:
                #    frame = morphPicture(PIL.Image.fromarray(np.uint8(loadImageFromUrlOrLocalPath(newframe))), PIL.Image.fromarray(np.uint8(loadImageFromUrlOrLocalPath(saveframe))), blend, preview)
                #else:
                #    frame = loadImageFromUrlOrLocalPath(newframe)

                # setup next frame
                frame = np.float32(frame)
                writeToLog( 'channels used:: ' + str(keepIndices) + '\n')
                var_counter += 1
            else:
                writeToLog('Finished processing all frames'+ '\n')


def extractVideo(inputdir, outputdir):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    writeToLog("Extracting Video: " + inputdir + " To: " + outputdir)

    command = 'ffmpeg -i ' + inputdir + ' -f image2 ' + outputdir + '/image-%06d.png'
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    while proc.poll() is None:
        line = proc.stdout.readline()
        writeToLog(line + '\n')
    
    writeToLog("Done Extracting: " + inputdir + " To: " + outputdir)


def createVideo(inputdir, outputdir, framerate):
    writeToLog("Creating Video: " + inputdir + " To: " + outputdir)

    command = 'ffmpeg -r ' + str(framerate) + ' -f image2 -i "' + inputdir + '/frame_%6d.jpg" -c:v libx264 -crf 20 -pix_fmt yuv420p -tune fastdecode -tune zerolatency -profile:v baseline ' + outputdir
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    while proc.poll() is None:
        line = proc.stdout.readline()
        writeToLog(line + '\n')
    
    writeToLog("Done Creating Video: " + inputdir + " To: " + outputdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='DeepDreamAnim')
    parser.add_argument('-i', '--input', help='Input directory', required=True)
    parser.add_argument('-o', '--output', help='Output directory', required=True)
    parser.add_argument('-p', '--preview', help='Preview image width. Default: 0', type=int, required=False)
    parser.add_argument('-oct', '--octaves', help='Octaves. Default: 4', type=int, required=False)
    parser.add_argument('-octs', '--octavescale', help='Octave Scale. Default: 1.4', type=float, required=False)
    parser.add_argument('-itr', '--iterations', help='Iterations. Default: 10', type=int, required=False)
    parser.add_argument('-j', '--jitter', help='Jitter. Default: 32', type=int, required=False)
    parser.add_argument('-z', '--zoom', help='Zoom in Amount. Default: 1', type=int, required=False)
    parser.add_argument('-s', '--stepsize', help='Step Size. Default: 1.5', type=float, required=False)
    parser.add_argument('-b', '--blend', help='Blend Amount. Default: 0.5', type=float, required=False)
    parser.add_argument('-l', '--layers', help='Layers Loop. Default: inception_4c/output', nargs="+", type=str,
                        required=False)
    parser.add_argument('-e', '--extract', help='Extract Frames From Video.', type=int, required=False)
    parser.add_argument('-c', '--create', help='Create Video From Frames.', type=int, required=False)
    parser.add_argument('-g', '--guide', help='Guided dream image input.', type=str, required=False)
    parser.add_argument('-flow', '--flow', help='Optical Flow.', type=int, required=False)
    parser.add_argument('-gpu', '--gpu', help='Use GPU (1+) or CPU (0).', type=int, required=False)
    parser.add_argument('-f', '--framerate', help='Video creation Framerate.', type=int, required=False)
    parser.add_argument('-n', '--network', help='Network to use (default googlenet places)', type=str, required=False)
    
    parser.add_argument('-d', '--drop', help='# of top units to drop (default: 0)', type=int, required=False)
    parser.add_argument('-k', '--keep', help='# of units to use (default: 4)', type=int, required=False)

    args = parser.parse_args()

    # clear log
    with open('static/render.log','w') as f: f.write("")

    # parse args
    if args.extract is 1:
        extractVideo(args.input, args.output)
    elif args.create is 1:
        framerate = 25
        if args.framerate is not None: framerate = args.framerate
        createVideo(args.input, args.output, framerate)
    else:
        if not args.preview is None: # len(args.preview) > 1:
            jpg_quality = args.preview
        
        main(args.input, args.output, 0, args.octaves, args.octavescale, args.iterations, args.jitter,
             args.zoom, args.stepsize, args.blend, args.layers, args.guide, args.gpu, args.flow, args.network, args.drop, args.keep)

