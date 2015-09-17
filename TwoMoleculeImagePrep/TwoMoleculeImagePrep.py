import numpy as np
import argparse
import os
from math import sin, cos, pi
from random import random
import ujson

def cmdline_args():
  parser = argparse.ArgumentParser(
    description='Generates a list of two-molecule scenarios.', add_help=False)
  
  parser.add_argument("-?", "--help", action="help", 
    help="show this help message and exit")

  parser.add_argument("-N", "--scenarios", 
    default=1000, type=int,
    help="the number of scenarios to generate")

  parser.add_argument("-w", "--width", 
    default=24, type=int,
    help="the width (px) of the image")

  parser.add_argument("-h", "--height", 
    default=24, type=int,
    help="the height (px) of the image")

  parser.add_argument("-l", "--wavelength",
    default=550.0, type=float,
    help="the wavelength of light being simulated")

  parser.add_argument("-u", "--usable_pixel", 
    default=99.0, type=float,
    help="the size (nm) of the usable pixel")

  parser.add_argument("-g", "--pixel_gap", 
    default=11.0, type=float, 
    help="the gap (nm) between the usable pixel")

  parser.add_argument("-I", "--photon_count", 
    default=1000.0, type=float, 
    help="the intensity (photon count) of the particle(s)")

  parser.add_argument("-b", "--noise",
    default=4.0, type=float, 
    help="the amount of background noise (photons per pixel)")

  parser.add_argument("-s", "--separation", 
    default=400.0, type=float, 
    help="the distance (nm) between the two particles")

  parser.add_argument("-c", "--contrast", 
    default=4.0, type=float, 
    help="the contrast (ratio) between the two particles")

  parser.add_argument("output_path", 
    help="file location of the output particle list (json file)")

  return parser.parse_args()


def check_path(a):
  # check if output file already exists
  if os.path.exists(a.output_path):
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
  print "Two Molecule Image Prep Script v0.1.0.1 "
  print "========================================"
  print

  a = cmdline_args()
  
  print "  Number of scenarios:", a.scenarios
  print "     Image Dimensions:", a.width, "px by", a.height, "px"
  print "  Wavelength of Light:", a.wavelength
  print "         Usable Pixel:", a.usable_pixel
  print "            Pixel Gap:", a.pixel_gap
  print "         Photon Count:", a.photon_count, "photons"
  print "                Noise:", a.noise, "photons per pixel"
  print "    Photon Separation:", a.separation, "nm"
  print "      Photon Contrast:", a.contrast, "to 1"
  print " Output File Location:", a.output_path
  print 

  check_path(a)

  # create scenario list
  data = {'width': a.width,
         'height': a.height,
         'usable': a.usable_pixel,
            'gap': a.pixel_gap,
          'noise': a.noise,
     'wavelength': a.wavelength,
      'scenarios': []}

  # add scenarios and corresponding particles
  for i in xrange(a.scenarios):

    pixel_size = a.usable_pixel + a.pixel_gap
      
    # choose a random angle from 0 deg to 45 deg
    angle = random() * pi / 4.0;

    # choose a random position
    x1 = (random() + a.width / 2.0) * pixel_size
    y1 = (random() + a.height / 2.0) * pixel_size

    # place the other particle near the first
    x2 = x1 + cos(angle) * a.separation
    y2 = y1 + sin(angle) * a.separation

    # set the photon counts
    N1 = a.photon_count
    N2 = N1 / a.contrast

    particles = {'particles': 
                 [{'x': x1, 'y': y1, 'intensity': N1, 'width': 1.8666},
                  {'x': x2, 'y': y2, 'intensity': N2, 'width': 1.8666}]}

    data['scenarios'].append(particles)

  print "Writing to file '%s'..." % (a.output_path,)
  print
  
  with open(a.output_path, "w") as f:
    ujson.dump(data, f)

  print "Finished!"
  print


if __name__ == '__main__':
  main()