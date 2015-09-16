import numpy as np
import pyopencl as cl
import argparse
import os
import math as m
import random as r
import ujson
import tifffile as tiff
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def gpu():
  ctx = cl.create_some_context()
  queue = cl.CommandQueue(ctx)

  mf = cl.mem_flags

def main():
  #gpu()

  print "Molecule Image Generator v0.1"
  print "===================================="
  print

  parser = argparse.ArgumentParser(description='Generates a stack of images based on the given n-particle scenarios.')
  parser.add_argument("-o", "--overwrite", default=False, help="enable or disable (True/False) automatic overwriting")
  parser.add_argument("-s", "--subsamples", default=100, help="the total number of subsamples to get per pixel")
  parser.add_argument("input_path", help="file location of the input particle list (json file)")
  parser.add_argument("output_path", help="file location of the output images (tiff file)")
  args = parser.parse_args()

  input_path = args.input_path
  output_path = args.output_path

  print "Checking that the input and output paths are valid."

  if not os.access(os.path.dirname(input_path), os.R_OK):
    print("Reading privileges not given; operation canceled.")
    exit()

  if os.path.exists(output_path):
    response = raw_input("The file '%s' already exists. Overwrite? (y/n): " % (output_path,))
    if response != 'y' and response != 'Y':
      print("Operation canceled.")
      exit()
  elif not os.access(os.path.dirname(output_path), os.W_OK):
    print("Writing privileges not given; operation canceled.")
    exit()
    
  print "Loading the scenario json file from '%s'." % (input_path,)

  with open(input_path, "r") as fin: 
    source = ujson.load(fin)

  # get the global properties
  width  = int(source['width'])
  height = int(source['height'])
  ssedge = int(m.sqrt(float(args.subsamples)))
  usable = float(source['usable'])
  gap    = float(source['gap'])
  noise  = float(source['noise'])
  scenarios = source['scenarios']
  len_s = len(scenarios)

  # sample number of particles
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

  print "Estimated Memory Usage:", mem_required / 1024.0 / 1024.0, "MBytes"

  len_p = []
  ptr_p = []
  i_p = 0

  x = []
  y = []
  intensity = []
  p_width = []

  # get scenarios and particles
  print "Restructuring scenario data."
  
  for s in scenarios:
     len_p.append(len(s['particles']))
     ptr_p.append(i_p)

     i_p += len(s['particles'])

     for p in s['particles']:
       x.append(p['x'])
       y.append(p['y'])
       intensity.append(p['intensity'])
       p_width.append(p['width'])

  # convert to numpy arrays
  print "Moving data to numpy arrays."

  ptr_p     = np.array(ptr_p,     dtype=np.int32)
  len_p     = np.array(len_p,     dtype=np.int32)
  
  x         = np.array(x,         dtype=np.float32)
  y         = np.array(y,         dtype=np.float32)
  intensity = np.array(intensity, dtype=np.float32)
  p_width   = np.array(p_width,   dtype=np.float32)
  
  print "Getting the OpenCL context..."
  ctx = cl.create_some_context()

  print "...and retrieving the command queue."
  queue = cl.CommandQueue(ctx)

  mf = cl.mem_flags
  ptr_buf       = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=ptr_p.astype(np.int32))
  len_buf       = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=len_p.astype(np.int32)) 
  
  x_buf         = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=x.astype(np.float32))
  y_buf         = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=y.astype(np.float32))
  intensity_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=intensity.astype(np.float32))
  width_buf     = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=p_width.astype(np.float32))
  
  dest_buf      = cl.Buffer(ctx, mf.WRITE_ONLY, output_size)

  k = 2.0 * m.pi / 550.0

  print "Compiling/building the kernel, running it, ..."
  with open("psfkernel.cl", "r") as f:
    prg = cl.Program(ctx, f.read()).build()

  event = prg.pixelPSF(queue, (len_s, width, height,), None, np.float32(k), np.float32(usable), np.float32(gap), np.int32(width), np.int32(height), np.int32(ssedge), ptr_buf, len_buf, x_buf, y_buf, intensity_buf, width_buf, dest_buf)

  print "...and copying the images from OpenCL (GPU or CPU)."
  event.wait()
  images = np.zeros(len_s * width * height, dtype=np.float32)
  cl.enqueue_copy(queue, images, dest_buf)

  print "Adding simulated noise to the images..."
  images = images + noise
  poisson_image = np.random.poisson(images, (1, len_s * width * height))[0]

  print "...and saving the resulting images."
  final_image = np.empty((len_s, width, height), dtype=np.uint16)
  for i in xrange(0, len_s):
    for j in xrange(0, width):
      for k in xrange(0, height):
        final_image[i, k, j] = int(poisson_image[j + width*k + height*width*i])

  tiff.imsave(output_path, final_image)
  print "TIFF saved to: '%s'" % output_path
                         
if __name__ == '__main__':
  main()