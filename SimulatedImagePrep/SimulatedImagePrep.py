import numpy as np
import argparse
import os
from random import random
import ujson
from scipy import misc
from PIL import Image

def cmdline_args():
  parser = argparse.ArgumentParser(
    description='Generates a list of two-molecule scenarios.', add_help=False)
  
  parser.add_argument("-?", "--help", action="help", 
    help="show this help message and exit")

  parser.add_argument("-N", "--images", 
    default=10000, type=int,
    help="the number of images to generate")

  parser.add_argument("-w", "--width", 
    default=64, type=int,
    help="the width (px) of the image")

  parser.add_argument("-h", "--height", 
    default=64, type=int,
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
    help="the mean intensity (photon count) of the particle(s)")

  parser.add_argument("-b", "--noise",
    default=4.0, type=float, 
    help="the amount of background noise (photons per pixel)")

  parser.add_argument("source_image_path",
    help="file location of the source image")
  
  parser.add_argument("output_path", 
    help="file location of the output particle list (json file)")

  return parser.parse_args()


def check_path(path, write=False):
  # check if output file already exists
  if write and os.path.exists(path):
    print "Warning: The file '%s' already exists." % (path,)
    response = raw_input("  Overwrite? (y/n): ")
    print

    if response != 'y' and response != 'Y':
      print "Exiting..."
      exit()

  # check access for output file
  if not os.access(os.path.dirname(path), os.W_OK):
    print "Error: You have insufficient access to the file '%s'." % (path,)
    print "Exiting..."
    exit()
  
  
def main():
  print "Simulated Images Prep Script v0.1.0.1 "
  print "======================================"
  print

  a = cmdline_args()
  
  print "  Number of scenarios:", a.images
  print "     Image Dimensions:", a.width, "px by", a.height, "px"
  print "  Wavelength of Light:", a.wavelength
  print "         Usable Pixel:", a.usable_pixel
  print "            Pixel Gap:", a.pixel_gap
  print "         Photon Count:", a.photon_count, "photons"
  print "                Noise:", a.noise, "photons per pixel"
  print "    Source Image File:", a.source_image_path
  print " Output File Location:", a.output_path
  print 

  check_path(a.source_image_path)
  check_path(a.output_path, write=True)

  # create scenario list
  data = {'width': a.width,
         'height': a.height,
         'usable': a.usable_pixel,
            'gap': a.pixel_gap,
          'noise': a.noise,
     'wavelength': a.wavelength,
      'scenarios': []}

  # Open source image
  source = Image.open(a.source_image_path).convert('L')
  source_data = np.asarray(source)
  source_height, source_width = source_data.shape

  print "Source Image Width: ", source_width
  print "Source Image Height:", source_height
  print

  # add scenarios and corresponding particles
  for i in xrange(a.images):

    pixel_size = a.usable_pixel + a.pixel_gap

    particles = {'particles':[]}

    for n in xrange(6):
      # choose a random position
      found = False
      while not found:
        x = random()
        y = random()
        sx = x*source_width
        sy = y*source_height
        if source_data[int(sy), int(sx)] > 128:
          found = True
          x = x * a.width * pixel_size
          y = y * a.height * pixel_size
      #x1 = (random() + a.width / 2.0) * pixel_size
      #y1 = (random() + a.height / 2.0) * pixel_size

      # set the photon counts
      N1 = a.photon_count*np.random.exponential()

      particles['particles'].append({'x': x, 'y': y, 'intensity': N1, 'width': 1.8666})

    data['scenarios'].append(particles)


  print "Writing to file '%s'..." % (a.output_path,)
  print
  
  with open(a.output_path, "w") as f:
    ujson.dump(data, f)

  print "Finished!"
  print


if __name__ == '__main__':
  main()