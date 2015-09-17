import numpy as np
from numpy.random import poisson
import pyopencl as cl
import argparse
import os
import math as m
import random as r
import ujson
import tifffile as tiff
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def cmdline_args():
  parser = argparse.ArgumentParser(
    description='Generates a stack of images based on the given n-particle scenarios.')
  
  parser.add_argument("-o", "--overwrite", 
    default=False, type=bool,
    help="enable or disable (True/False) automatic overwriting")

  parser.add_argument("-s", "--subsamples", 
    default=100, type=int,
    help="the total number of subsamples to get per pixel")

  parser.add_argument("input_path", 
    help="file location of the input particle list (json file)")

  parser.add_argument("output_path", 
    help="file location of the output images (tiff file)")

  return parser.parse_args()


def check_paths(a):
  # check access for input file
  if not os.access(os.path.dirname(a.input_path), os.R_OK):
    print "Error: You have insufficient access to the file '%s'." % (a.input_path,)
    print "Exiting..."
    exit()

  # check if output file already exists
  if os.path.exists(a.output_path) and not a.overwrite:
    print "Warning: The file '%s' already exists." % (a.output_path,)
    response = raw_input("  Overwrite? (y/n): ")
    print

    if response != 'y' and response != 'Y':
      print "Exiting..."
      exit()

  # check access for output file
  if not os.access(os.path.dirname(a.output_path), os.W_OK):
    print "Error: You have insufficient access to the file '%s'." % (a.output_path,)
    print "Exiting..."
    exit()


def main():
  #gpu()

  print "Molecule Image Generator v0.1.0.1 "
  print "=================================="
  print

  a = cmdline_args()

  check_paths(a)
  
  # load the json file
  with open(a.input_path, "r") as fin: 
    source = ujson.load(fin)

  # get the global properties
  width  = int(source['width'])
  height = int(source['height'])
  ssedge = int(m.sqrt(float(a.subsamples)))
  usable = float(source['usable'])
  gap    = float(source['gap'])
  noise  = float(source['noise'])
  k      = 2.0 * m.pi / source['wavelength']
  scenarios = source['scenarios']
  scenario_count = len(scenarios)

  """# sample number of particles
  n = float(len_s) / (0.05**2 * (float(len_s) - 1.0) + 1.0)
  len_p_approx = 0
  for i in xrange(int(n)):
    j = r.randint(0, len_s-1)
    len_p_approx += len(scenarios[j]['particles'])
  len_p_approx /= n

  # prepare data
  output_size = 4 * len_s * width * height
  particle_size = len_s * len_p_approx;
  mem_required = 4 * (4 * particle_size + output_size + 2 * len_s) + 7 * 4

  print "Estimated Memory Usage:", mem_required / 1024.0 / 1024.0, "MBytes" """

  current_index = 0
  pointer = []
  count = []
  X = []
  Y = []
  N = []
  W = []
  
  for scenario in scenarios:
    # store the number of particles
    count.append(len(scenario['particles']))

    # store a pointer to the particles
    pointer.append(current_index)

    # increment index
    current_index += len(scenario['particles'])

    # store particle data
    for particle in scenario['particles']:
      X.append(particle['x'])
      Y.append(particle['y'])
      N.append(particle['intensity'])
      W.append(particle['width'])

  # convert to numpy arrays
  pointer = np.array(pointer, dtype=np.int32)
  count   = np.array(count,   dtype=np.int32)
  
  X = np.array(X, dtype=np.float32)
  Y = np.array(Y, dtype=np.float32)
  N = np.array(N, dtype=np.float32)
  W = np.array(W, dtype=np.float32)
  
  expected = np.zeros(scenario_count * width * height, dtype=np.float32)

  context = cl.create_some_context()
  queue = cl.CommandQueue(context)

  mf = cl.mem_flags
  pointer_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=pointer.astype(np.int32))
  count_buf   = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=count.astype(np.int32)) 
  
  X_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=X.astype(np.float32))
  Y_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=Y.astype(np.float32))
  N_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=N.astype(np.float32))
  W_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=W.astype(np.float32))
  
  dest_buf = cl.Buffer(context, mf.WRITE_ONLY, 4 * scenario_count * width * height)

  print "Enqueuing job to OpenCL..."
  print 

  with open("psfkernel.cl", "r") as f:
    prg = cl.Program(context, f.read()).build()

  # call the kernel
  event = prg.pixelPSF(queue, (scenario_count, width, height,), None, 
            np.float32(k), np.float32(usable), np.float32(gap), 
            np.int32(width), np.int32(height), np.int32(ssedge), 
            pointer_buf, count_buf, 
            X_buf, Y_buf, N_buf, W_buf, dest_buf)

  # wait and then grab the data
  event.wait()
  
  cl.enqueue_copy(queue, expected, dest_buf)

  print "Finalizing images..."
  print 

  # add the background noise level
  expected = expected + noise

  # introduce poisson-distributed noise (expected is lambda)
  poisson_image = poisson(expected, (1, scenario_count * width * height))[0]

  print "Writing to file '%s'..." % a.output_path
  print

  # copy over the final image to be saved as a tiff
  final_image = np.empty((scenario_count, width, height), dtype=np.uint16)
  for i in xrange(0, scenario_count):
    for j in xrange(0, width):
      for k in xrange(0, height):
        final_image[i, k, j] = int(poisson_image[j + width*k + height*width*i])

  tiff.imsave(a.output_path, final_image)

  print "Finished!"
  print
  
                         
if __name__ == '__main__':
  main()