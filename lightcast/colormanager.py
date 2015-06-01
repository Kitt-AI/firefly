#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json, os, os.path, logging, random
from rgb_cie import color_converter


class ColorManager(object):
    """
    stores color of objects and facilities to fuzzily search these object by names
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.lowercase2color = {}
        self.color_names = []
        self.load()

    def load(self, path=os.path.join(".", 'full_colors.json')):
        with open(path) as f:
            for line in f:
                color = json.loads(line.strip())
                name = color['stripped_name'].lower()
                self.lowercase2color[name] = color
                self.color_names.append(name)

    def get_xy(self, color):
        """
        Given a color, get its xy numbers.
        'color' can be:
          color name that's found in colormanager
          (x,y) tuple or list
          (r,g,b) tuple or list
          '#rrggbb' hex code

        returns a [x,y] list accpeted by the Hue API. If color is not found,
          returns white ([0.33618074375880236, 0.3603696362840742])
        """
        color_type = type(color)
        color_len = len(color)
        if color_type is str:
            if color.startswith('#') and (color_len == 4 or color_len == 7):
                return hex2xy(color)
            elif color.lower() in self.lowercase2color:
                hex_color = self.get_hex(color)
                return hex2xy(hex_color)
        elif color_type is tuple or color_type is list:
            if color_len == 2:  # [x,y]
                return list(color)
            elif color_len == 3:  # r,g,b
                return color_converter.rgbToCIE1931(*color)
        self.logger.warning("color %s not found, returning white" % color)
        return [0.33618074375880236, 0.3603696362840742]

    def get_hexes(self, color_names):
        return [self.get_hex(name) for name in color_names]

    def get_hex(self, color_name):
        if color_name.startswith("#"):
            return color_name
        lower = color_name.lower()
        if lower in self.lowercase2color:
            return self.lowercase2color[lower]['hex']
        else:
            self.logger.warning(
                "color name not found (check your code!) " + color_name)
            return ""

    def random_color_in_hex(self):
        color = self.lowercase2color[self.random_color_name()]
        return color['hex']

    def random_color_in_rgb(self):
        return hex2rgb(self.random_color_in_hex())

    def random_color_in_xy(self):
        return color_converter.rgbToCIE1931(*self.random_color_in_rgb())

    def random_color_name(self):
        # NOTE: potential to speed up: use random.sample() and maintain a buffer
        name = random.choice(self.color_names)
        logging.debug(name)
        return name


def rgb2hex(r, g, b):
    # 5, 50, 250 -> 0532fa
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def rgb_list2hex_list(rgb_list):
    return [rgb2hex(*rgb) for rgb in rgb_list]


def hex2rgb(hex_str):
    """
    #123456 -> (18, 52, 86)
    """
    h = hex_str[hex_str.find('#') + 1:]
    l = len(h)
    if l == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    elif l == 3:
        return (int(h[0], 16), int(h[1], 16), int(h[2], 16))
    else:
        logging.error("hex_str not recognized:" + str(hex_str))
        # return black
        return (0, 0, 0)


def hex_list2rgb_list(hex_str_list):
    return [hex2rgb(hex_str) for hex_str in hex_str_list]


def hex2xy(hex_str):
    (r, g, b) = hex2rgb(hex_str)
    return color_converter.rgbToCIE1931(r, g, b)


if __name__ == "__main__":
    logging.basicConfig()
    manager = ColorManager()
    print manager.get_hex('pinkish')
    print manager.get_xy('white')
    print manager.get_xy('pinkish')
    print manager.get_xy('#000')
    print manager.get_xy('#ffffff')
    print manager.get_xy((1, 1))
    print manager.get_xy((0, 0, 0))
    print manager.get_xy((255, 255, 255))
