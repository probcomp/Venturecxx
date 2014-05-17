import random
import Image
import ImageFont
import ImageDraw
import ImageFilter
import ImageOps
import math
import value

from time import gmtime, strftime

from scipy import misc
from scipy import ndimage
import scipy
import numpy

global_width = 354
global_height = 133
global_sigma = 2

import sys

loaded_image = Image.open("target.png")

def draw_letter(text, font, colour, font_size, canvas_width, canvas_height, x, y, angle, if_present):
    canvas = Image.new('RGBA', (canvas_width, canvas_height))
    if if_present:
        font = ImageFont.truetype(font, font_size)
        dim = font.getsize(text)
        maxdim = max(dim) * 2
        im = Image.new('RGBA', (maxdim, maxdim))
        draw = ImageDraw.Draw(im)
        draw.text( (maxdim / 2 - dim[0] / 2, maxdim / 2 - dim[1] / 2), text,  font=font, fill=colour)
        im = im.rotate(angle, expand=0)
        # im.paste( ImageOps.colorize(w, (0,0,0), (255,255,84)), (242,60),  w)
        dim_new = [0, 0]
        dim_new[0] = int(math.ceil(abs(math.cos(math.pi * angle) * dim[0] + math.sin(math.pi * angle) * dim[1]) / 2))
        dim_new[1] = int(math.ceil(abs(math.sin(math.pi * angle) * dim[0] + math.cos(math.pi * angle) * dim[1]) / 2))
        canvas.paste(im, (x - dim_new[0], y - dim_new[1]), im)
    return canvas
    
def render_glyph(canvas_width, canvas_height, glyph_id, topleft_x, topleft_y, size, angle, if_present):
    glyph_id = int(round(glyph_id))
    if glyph_id < 10:
        text = str(glyph_id)
    else:
        text = chr(65 + glyph_id - 10)
    canvas_width = int(round(canvas_width))
    canvas_height = int(round(canvas_height))
    size = int(round(size))
    topleft_x = int(round(topleft_x))
    topleft_y = int(round(topleft_y))
    angle = int(round(angle))
    return draw_letter(text, 'arial.ttf', (0, 0, 0), size, canvas_width, canvas_height, topleft_x, topleft_y, angle, if_present)
    
def gaussian_blur(image, radius_parameter):
    # f = ImageFilter.GaussianBlur(radius = radius_parameter)
    # new_canvas = image.filter(f)
    return ndimage.gaussian_filter(numpy.array(image), sigma=radius_parameter)
    
def blur(image, bandwidth):
    return gaussian_blur(image, bandwidth)
    
def composite(width, height, images):
    im = Image.new('RGB', (int(round(width)), int(round(height))), (255, 255, 255))
    for image in images:
        im2 = Image.fromarray(image, "RGBA")
        im.paste(im2, (0, 0), im2)
    return numpy.array(im)

def stochastic_comparer(args):
    image = args.operandValues[0]
    sigma = args.operandValues[1]
    squared = numpy.square(numpy.mean(image, axis=2) - numpy.mean(numpy.array(loaded_image), axis=2))
    logscore = -numpy.sum(squared)
    logscore = logscore / (2 * sigma * sigma)
    logscore = logscore - math.log(sigma * math.sqrt(2 * math.pi)) * squared.size
    return logscore
    # return 1
    
def print_to_file(image, filename):
    # image.save(filename, format="png")
    # print image
    scipy.misc.imsave(filename, image)
    # pass
   
def save_image(image, filename):
    scipy.misc.imsave("outputs/" + str(int(filename)) + ".png", image)
    return True

if __name__ == '__main__':
    for blur in xrange(0, 10, 1):
        im_with_gaussian = []
        
        im_letter = draw_letter("A", "arial.ttf", (0, 0, 0), 45, global_width, global_height, 50, 50, 10, True)
        im_with_gaussian += [gaussian_blur(im_letter, blur)]
        
        im_letter = draw_letter("B", "arial.ttf", (0, 0, 0), 45, global_width, global_height, 90, 50, -10, True)
        im_with_gaussian += [gaussian_blur(im_letter, blur)]
        
        im_letter = draw_letter("C", "arial.ttf", (0, 0, 0), 45, global_width, global_height, 140, 50, 0, True)
        im_with_gaussian += [gaussian_blur(im_letter, blur)]
        
        # print strftime("%Y-%m-%d %H:%M:%S", gmtime())
        print_to_file(composite(global_width, global_height, im_with_gaussian), "test" + str(blur) + ".png")
        
        # print numpy.mean(compose_images(im_with_gaussian, im_with_gaussian2, global_width, global_height), axis=2)
        # logscore = -numpy.sum(numpy.square(numpy.mean(compose_images(im_with_gaussian, im_with_gaussian2, global_width, global_height), axis=2) - numpy.mean(numpy.array(loaded_image), axis=2)))
        # logscore = logscore / (2 * global_sigma * global_sigma)
        # logscore = logscore + math.log(global_sigma * math.sqrt(2 * math.pi))
        # print logscore
        # print compose_images(im_with_gaussian, im_with_gaussian2)
        
