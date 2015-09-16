import numpy as np
import argparse
import os
import random as r
import math as m
import ujson

def main():
  print "Two Molecule Image Prep Script v0.1"
  print "===================================="
  print

  parser = argparse.ArgumentParser(description='Generates a list of two-molecule scenarios.', add_help=False)
  parser.add_argument("-?", "--help", action="help", help="show this help message and exit")
  parser.add_argument("-N", "--scenarios", default=1000, help="the number of scenarios to generate")
  parser.add_argument("-w", "--width", default=24, help="the width (px) of the image")
  parser.add_argument("-h", "--height", default=24, help="the height (px) of the image")
  parser.add_argument("-u", "--usable_pixel", default=99.0, help="the size (nm) of the usable pixel")
  parser.add_argument("-g", "--pixel_gap", default=11.0, help="the gap (nm) between the usable pixel")
  parser.add_argument("-I", "--photon_count", default=1000.0, help="the intensity (photon count) of the particle(s)")
  parser.add_argument("-b", "--noise", default=4.0, help="the amount of background noise (photons per pixel)")
  parser.add_argument("-s", "--separation", default=400.0, help="the distance (nm) between the two particles")
  parser.add_argument("-c", "--contrast", default=4.0, help="the contrast (ratio) between the two particles")
  parser.add_argument("output_path", help="file location of the output particle list (json file)")
  args = parser.parse_args()

  scenarios = int(args.scenarios)
  width = int(args.width)
  height = int(args.height)
  usable_pixel = float(args.usable_pixel)
  pixel_gap = float(args.pixel_gap)
  photon_count = float(args.photon_count)
  noise = float(args.noise)
  separation = float(args.separation)
  contrast = float(args.contrast)
  output_path = args.output_path
  
  print "  Number of scenarios:", scenarios
  print "     Image Dimensions:", width, "px by", height, "px"
  print "         Usable Pixel:", usable_pixel
  print "            Pixel Gap:", pixel_gap
  print "         Photon Count:", photon_count, "photons"
  print "                Noise:", noise, "photons per pixel"
  print "    Photon Separation:", separation, "nm"
  print "      Photon Contrast:", contrast, "to 1"
  print " Output File Location:", output_path

  if os.path.exists(output_path):
    response = raw_input("The file '%s' already exists. Overwrite? (y/n):" % (output_path,))
    if response != 'y' and response != 'Y':
      print("Operation canceled.")
      exit()
  elif not os.access(os.path.dirname(output_path), os.W_OK):
    print("Writing privileges not given; operation canceled.")
    exit()
  
  print "Writing to '%s'..." % (output_path,)

  # setup dictionary of settings and particles
  data = {'width': width,
          'height': height,
          'usable': usable_pixel,
          'gap': pixel_gap,
          'noise': noise,
          'scenarios': []}

  # add particles
  for i in xrange(scenarios):

    pixel_size = usable_pixel + pixel_gap
      
    # calculate the positions of the two particles
    angle = r.random() * m.pi / 4.0;

    x_1 = (r.random() + width / 2.0) * pixel_size
    y_1 = (r.random() + height / 2.0) * pixel_size

    x_2 = x_1 + m.cos(angle) * separation
    y_2 = y_1 + m.sin(angle) * separation

    # get two random photon counts
    N_1 = photon_count
    N_2 = N_1 / contrast

    particles = {'particles': 
                 [{'x': x_1, 'y': y_1, 'intensity': N_1, 'width': 1.8666},
                  {'x': x_2, 'y': y_2, 'intensity': N_2, 'width': 1.8666}]}

    data['scenarios'].append(particles)

  print "Writing to file..."
  
  with open(output_path, "w") as f:
    ujson.dump(data, f)

  print "Done!"


if __name__ == '__main__':
  main()