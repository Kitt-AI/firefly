#! /usr/bin/env python

from parsetron import *
from lightcontrol import LightControl
from parsetron.grammars.colored_light import ColoredLightGrammar
import logging

# TODO: dynamically change light name


class LightDemo(object):
    def __init__(self, bridge_username, bridge_ip=None, webport=8085,
                 debug=True):
        self.parser = RobustParser(ColoredLightGrammar())
        self.hue = LightControl(ip=bridge_ip, username=bridge_username)
        self.webport = webport
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)
        self.history = ""

    def execute_cmd(self, cmd, incremental=False, is_final=False):
        tree, result = None, None
        if incremental:
            single_token = cmd[len(self.history):].strip()
            self.history = cmd
            for t in single_token.split():
                tree, result = self.parser.incremental_parse(t, is_final)
            if is_final:
                self.history = ""
                self.parser.clear_cache()
        else:
            tree, result = self.parser.parse(cmd)
        if tree:
            self.logger.debug("best tree")
            self.logger.debug(tree)
            self.logger.debug("parse result")
            self.logger.debug(result)
            # tree_json = str(result)
            tree_json = tree.dict_for_js()
            parses = result.get('one_parse', [])
            api_lists = []
            if incremental and parses and len(parses) > 0:
                parses = [parses[-1]]
                api_lists = self.parses2api(parses, result)
            if is_final:
                api_lists = self.parses2api(parses, result)
            return parses, api_lists, tree_json
        else:
            return None, None, None

    def parse2api(self, parse, result):
        """
        Given a parse result, convert them into API calls.

        Returns a list of literal strings representing actually called APIs.
        """
        which_lights = None
        ret = []

        if 'specific_name' in parse:
            which_lights = self.hue.disambiguate_names(
                parse['specific_name'])
            if 'light_quantifiers' in parse:
                quantifier = parse['light_quantifiers']
                if (quantifier == 'both' and len(which_lights) != 2) or \
                    (quantifier == 'all' and
                     len(which_lights) != self.hue.n_lights):
                    self.logger.warn(
                        "light names (%d) and quantifier (%d) don't match" %
                        " ".join(which_lights), quantifier)

        if which_lights is None or len(which_lights) == 0:
            self.logger.warn("didn't specifiy lights, assuming all lights")
            which_lights = self.hue.light_names

        # ## Turn on/off ###
        turn_on = None
        if 'on' in parse:  # ON/OFF
            turn_on = True
        if 'off' in parse:  # ON/OFF
            turn_on = False
        if turn_on is not None:
            self.hue.turn_on_off_lights(which_lights, turn_on)
            return ["turn_on_off_lights(%s, on = %s)" %
                    (str(which_lights), str(turn_on))]

        # ## Change color ###
        if 'color' in parse:
            self.hue.set_lights_to_color(which_lights, parse.rgb)
            ret.append('set_lights_to_color(%s, %s)' %
                       (str(which_lights), parse.color))

        if 'brightness_more' in parse:
            self.hue.adjust_brightness(which_lights, 2.0)
            ret.append(
                'adjust_brightness(%s, multiply = 2.0)' % str(which_lights))
        if 'brightness_less' in parse:
            self.hue.adjust_brightness(which_lights, 0.5)
            ret.append(
                'adjust_brightness(%s, multiply = 0.5)' % str(which_lights))
        if 'saturation_more' in parse:
            self.hue.adjust_saturation(which_lights, 2.0)
            ret.append(
                'adjust_saturation(%s, multiply = 2.0)' % str(which_lights))
        if 'saturation_less' in parse:
            self.hue.adjust_saturation(which_lights, 0.5)
            ret.append(
                'adjust_saturation(%s, multiply = 0.5)' % str(which_lights))
        if 'theme' in parse:
            # TODO
            pass

        # global result states
        if 'action_blink' in result:
            times = 1
            if 'times' in parse:
                times = parse.times
            self.hue.blink_lights(which_lights, times)
            ret.append(
                'blink_lights(%s, times = %d)' % (str(which_lights), times))
        return ret

    def parses2api(self, parses, result):
        """
        Given a list of parses from RobustChart, convert them into API calls
        """
        api_lists = []
        for parse in parses:
            api_list = self.parse2api(parse, result)
            api_lists.append(api_list)
        return api_lists

    def run_cmdline(self):
        while True:
            try:
                cmd = raw_input("Enter your command: ")
                cmd = cmd.strip()
                if len(cmd) == 0:
                    continue
                if cmd.lower() in ['exit', 'quit']:
                    raise EOFError
                self.execute_cmd(cmd, is_final=True)
            except EOFError:
                print
                break

    def run_webserver(self):
        from bottle import Bottle, run, request, static_file

        app = Bottle()
        app.top_static_file_dir = 'web/'
        print "Init complete"

        @app.route('/')
        def home():
            return static_file("index.html", root=app.top_static_file_dir)

        @app.get('/<filename:re:.*\.(js|html|css|map|jpg|png|gif|ico|eot|'
                 'ttf|woff|svg)>')
        def serveserve(filename):
            return static_file(filename, root=app.top_static_file_dir)

        @app.route('/hello')
        def hello():
            return "Hello World!"

        @app.route('/on')
        def on():
            print "/on: turning lights on..."
            self.hue.turn_on_off_lights(self.hue.light_names, True, 0)

        @app.route('/off')
        def off():
            print "/off: turning lights off..."
            self.hue.turn_on_off_lights(self.hue.light_names, False, 0)

        @app.route('/clearcache')
        def clear_cache():
            print "/clearcache: clear cache of parser..."
            self.parser.clear_cache()

        @app.post('/lightparser')
        def cast_light():
            self.logger.info("received command:")
            self.logger.info(request.params.items())
            cmd = request.json.get('text', '').encode('utf-8')
            if len(cmd.strip()) == 0:
                return None
            incremental = request.json.get('incremental', False)
            is_final = request.json.get('is_final', False)
            self.logger.debug("incremental: %s, final: %s" %
                              (incremental, is_final))
            (parses, apis, tree_json) = self.execute_cmd(
                cmd, incremental, is_final)
            self.logger.info('parses:')
            self.logger.info(parses)
            self.logger.info('api:')
            self.logger.info(apis)
            self.logger.info('tree:')
            self.logger.info(tree_json)

            if tree_json:
                data = zip([str(parse) for parse in parses],
                           ["\n\n".join(ll) for ll in apis])
                return {'data': data, 'tree': tree_json}
            else:
                return {'data': zip(["no parse found"], ["no API calling"]),
                        'tree': ''}

        run(app=app, host='localhost', port=self.webport, debug=self.debug)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Firefly lighting demo')
    parser.add_argument('-b', '--bridge', help='Bridge IP address')
    parser.add_argument(
        '-u', '--user',
        help='Bridge user name, more info: '
             'http://www.developers.meethue.com/documentation/getting-started')
    parser.add_argument('-p', '--port', help='Webserver port', default=8085)
    parser.add_argument('-d', '--debug', help='debug output', default=False)

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.bridge:
        bridge_ip = args.bridge
    else:
        bridge_ip = None

    username = None
    if not args.user:
        import getpass
        if getpass.getuser() == 'xuchen':
            username = 'xuchencolor'
    else:
        username = args.user
    if not username:
        import sys
        print >> sys.stderr, "Error: you must enter bridge user name with -u"
        parser.print_help()
        sys.exit(-1)

    lightdemo = LightDemo(bridge_username=username, bridge_ip=bridge_ip,
                          webport=args.port, debug=args.debug)
    lightdemo.run_webserver()
    # lightdemo.run_cmdline()
