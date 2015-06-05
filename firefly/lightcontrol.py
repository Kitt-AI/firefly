#! /usr/bin/env python

import logging, time

from phue import Bridge
import colormanager
from colormanager import ColorManager
from rgb_cie import Converter

# docs:
# https://github.com/studioimaginaire/phue
#
# also check out:
# https://github.com/allanbunch/beautifulhue

# TODO: UPnP discovery of Hue Bridge (actually use get_ip)
# use: https://www.meethue.com/api/nupnp
# http://www.developers.meethue.com/documentation/hue-bridge-discovery
# https://gist.github.com/dankrause/6000248
# https://github.com/peter-murray/node-hue-api
# TODO: properly define black and grey

class LightControl(object):
    """
    Control Philips Hue.

    There are 3 methods available to set the color of the light -
    hue and saturation (hs), xy or color temperature (ct).
    If multiple methods are used then a priority is used: xy > ct > hs

    Reference:
      http://www.developers.meethue.com/documentation/lights-api
    """

    def __init__(self, ip=None, username=None):
        self.hue = Bridge(ip, username)
        self.lights = self.hue.lights
        self.light_names = [light.name for light in self.lights]
        self.lower2light_names = {name.lower(): name for name in
                                  self.light_names}
        self.n_lights = len(self.lights)
        self.converter = Converter()
        self.turn_on_all_lights()
        self.colormanager = ColorManager()
        self.logger = logging.getLogger(__name__)

    def turn_on_all_lights(self, bri=122):
        for light in self.lights:
            self.hue.set_light(light.name, {'on': True, 'bri': bri})

    def turn_on_off_lights(self, lights, on, bri=122, transitiontime=4):
        if type(lights) is not list:
            lights = [lights]
        for light in lights:
            self.hue.set_light(light, {'on': on, 'bri': bri,
                                       'transitiontime': transitiontime})

    def random_color_in_xy(self):
        # NOTE: potential to speed up: just generate random x,y floats
        # in the hue range (needs care though)
        # http://www.developers.meethue.com/documentation/core-concepts
        return self.colormanager.random_color_in_xy()

    def adjust_brightness(self, lights, percent):
        """
        Adjust the current brigtness by 'percent':
          0.5: reduce to half;
          2.0: double brightness.

          brightness is bounded in [0, 255]
        """
        if type(lights) is not list:
            lights = [lights]
        for light in lights:
            bri = self.hue.get_light(light, 'bri')
            bri = int(bri * percent)
            if bri < 0: bri = 0
            if bri > 255: bri = 255
            self.hue.set_light(light, 'bri', bri)

    def adjust_saturation(self, lights, percent):
        """
        Adjust the current saturation by 'percent':
          0.5: reduce to half;
          2.0: double saturation.

          saturation is bounded in [0, 255]
        """
        if type(lights) is not list:
            lights = [lights]
        for light in lights:
            sat = self.hue.get_light(light, 'sat')
            sat = int(sat * percent)
            if sat < 0: sat = 0
            if sat > 255: sat = 255
            self.hue.set_light(light, 'sat', sat)

    def blink_lights(self, lights, times=1):
        """
        Blink 'lights' with the current color. If 'times' > 1, then blink with
        an interval of 0.5 seconds.

        For now this is implemented with the {"alert":"select"} message.
        This works when light is on.

        TODO for future: if lights are off, then turn on and off to blink.
        """
        if type(lights) is not list:
            lights = [lights]

        for _ in range(times):
            for light in lights:
                self.hue.set_light(light, {"alert": "select"})
            if times != 1:
                time.sleep(0.5)

    def set_lights_to_color(self, lights, color):
        """
        'lights' can be either a light name/id, or a list;
        'color' can be:
          color name that's found in colormanager
          (x,y) tuple
          (r,g,b) tuple
          '#rrggbb' hex code
        """
        xy = self.colormanager.get_xy(color)
        if type(lights) is not list:
            lights = [lights]
        for light in lights:
            self.hue.set_light(light, {'on': True, 'xy': xy})

    def set_all_lights_to_color(self, hex_color_list):

        rgb_list = colormanager.hex_list2rgb_list(hex_color_list)
        rgb_list = filter(lambda rgb: list(rgb) != [0, 0, 0], rgb_list)
        xy_list = [self.converter.rgbToCIE1931(*rgb) for rgb in rgb_list]

        n_color = len(xy_list)
        if n_color == 0:
            logging.warning("no color to set from", hex_color_list)
        elif n_color >= self.n_lights:
            for i, light in enumerate(self.lights):
                self.hue.set_light(light.name, {'xy': xy_list[i]})
        else:
            # more lights than colors:
            # suppose we want to display [red, blue] on four lights,
            # then we display [red, red, red, blue]
            diff = self.n_lights - n_color
            for i, light in enumerate(self.lights):
                i_color = 0 if i <= diff else i - diff
                self.hue.set_light(light.name, {'xy': xy_list[i_color]})

    def set_group_to_single_color(self, hex_color_str, group_id=0):
        rgb = colormanager.hex2rgb(hex_color_str)
        xy = self.converter.rgbToCIE1931(*rgb)
        self.hue.set_light_by_group(group_id, {'xy': xy})

    def disambiguate_names(self, names):
        """
        Given a list of light names, such as ['top', 'kitchen'],
        return the true light names registered with the system
        """
        true_names = []
        for name in names:
            name = {"kitchen": "top", "living room": "middle",
                    "bedroom": "bottom"}.get(name, name)
            if name in self.lower2light_names:
                true_names.append(self.lower2light_names[name])
            else:
                self.logger.warn("name not found: " + name)
                self.logger.warn(
                    "registered names: " + str(self.lower2light_names.values()))
        return true_names


if __name__ == "__main__":
    logging.basicConfig()
    control = LightControl(ip = None, username = 'xuchencolor')
    # control.set_all_lights_to_color(["#241773", "#000000", "#9e7c0c", "#FFFFFF"])
    control.set_group_to_single_color("#FF0000")
