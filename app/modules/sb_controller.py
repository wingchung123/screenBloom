from modules.func_timer import func_timer
from config import params
from time import sleep
from modules import hue_interface, utility, img_proc
import threading
# import urllib2
import random
import json
import ast

# if utility.dll_check():


# Class for running ScreenBloom thread
class ScreenBloom(threading.Thread):
    def __init__(self, update):
        super(ScreenBloom, self).__init__()
        self.stoprequest = threading.Event()
        self.update = float(update)

    def run(self):
        while not self.stoprequest.isSet():
            run()
            sleep(.1)

    def join(self, timeout=None):
        self.stoprequest.set()
        super(ScreenBloom, self).join(timeout)

# Class for Screen object to hold values during runtime
class Screen(object):
    def __init__(self, bulbs, bulb_settings, default,
                 rgb, update, update_buffer, max_bri, min_bri, zones, zone_state,
                 display_index, party_mode, sat, bbox):
        self.bulbs = bulbs
        self.bulb_settings = bulb_settings
        self.default = default
        self.rgb = rgb
        self.update = update
        self.update_buffer = update_buffer
        self.max_bri = max_bri
        self.min_bri = min_bri
        self.zones = zones
        self.zone_state = zone_state
        self.display_index = display_index
        self.party_mode = party_mode
        self.sat = sat
        self.bbox = bbox


def init():
    atr = initialize()
    global _screen
    _screen = Screen(*atr)


def start():
    global t
    screen = get_screen_object()
    t = ScreenBloom(screen.update)
    t.start()

    hue_interface.lights_on_off('on')
    utility.write_config('App State', 'running', True)


def stop():
    global t

    try:
        t.join()
    except NameError:
        pass

    utility.write_config('App State', 'running', False)


def get_screen_object():
    try:
        global _screen
        return _screen
    except NameError:
        init()
        return _screen


# Grab attributes for screen instance
def initialize():
    config_dict = utility.get_config_dict()

    max_bri = config_dict['max_bri']
    min_bri = config_dict['min_bri']

    active_lights = json.loads(config_dict['active'])
    all_lights = [str(i) for i in config_dict['all_lights'].split(',')]

    # # Check selected bulbs vs all known bulbs
    # bulb_list = []
    # for counter, bulb in enumerate(all_lights):
    #     if active_lights[counter]:
    #         bulb_list.append(active_lights[counter])
    #     else:
    #         bulb_list.append(0)

    bulb_settings = json.loads(config_dict['bulb_settings'])

    update = config_dict['update']
    update_buffer = config_dict['update_buffer']

    default = config_dict['default']

    zones = ast.literal_eval(config_dict['zones'])
    zone_state = bool(config_dict['zone_state'])

    party_mode = bool(config_dict['party_mode'])
    display_index = config_dict['display_index']

    sat = config_dict['sat']

    bbox = None
    if params.BUILD == 'win':
        from desktopmagic.screengrab_win32 import getDisplayRects
        bbox = getDisplayRects()[int(display_index)]

    return active_lights, bulb_settings, default, [], \
           update, update_buffer, max_bri, min_bri, zones, zone_state, \
           display_index, party_mode, sat, bbox


# Get updated attributes, re-initialize screen object
def re_initialize():
    # Attributes
    at = initialize()

    global _screen
    _screen = Screen(*at)

    update_bulb_default()


# Updates Hue bulbs to specified RGB/brightness value
def update_bulbs(new_rgb, dark_ratio):
    screen = get_screen_object()
    screen.rgb = new_rgb
    active_bulbs = [bulb for bulb, active in screen.bulbs.items() if active]
    send_light_commands(active_bulbs, new_rgb, dark_ratio)


# Set bulbs to initial color/brightness
def update_bulb_default():
    screen = get_screen_object()
    active_bulbs = [bulb for bulb, active in screen.bulbs.items() if active]

    for bulb in active_bulbs:
        init_state = json.loads(screen.default)[str(bulb)]
        print("this is inital state")
        print(init_state)
        hue_interface.update_light(bulb, init_state['rgb'], init_state['bri'])




        # xy = None
        # if bulb_initial_state['colormode']:
        #     xy = bulb_initial_state['xy']

        # bulb_state = hue_interface.get_bulb_state(bulb_settings, xy, bulb_initial_state['bri'], .8)
        # hue_interface.update_light(screen.ip, screen.devicename, bulb, bulb_state)


# Set bulbs to random RGB
def update_bulb_party():
    config_dict = utility.get_config_dict()
    min_bri = config_dict['min_bri']
    max_bri = config_dict['max_bri']

    screen = get_screen_object()
    active_bulbs = [bulb for bulb, active in screen.bulbs.items() if active]
    party_color = utility.party_rgb()
    hue_interface.update_all_lights(active_bulbs, party_color, random.randrange(int(min_bri), int(max_bri) + 1))


def send_light_commands(bulbs, rgb, dark_ratio, party=False):
    screen = get_screen_object()
    config_dict = utility.get_config_dict()
    min_bri = config_dict['min_bri']
    max_bri = config_dict['max_bri']

    bri = utility.get_brightness(screen, min_bri, max_bri, dark_ratio)
    print("this is bulbs")
    print(bulbs)

    hue_interface.update_all_lights(bulbs, rgb,  bri)

    # for bulb in bulbs:
    #     bulb_settings = screen.bulb_settings[str(bulb)]
    #     bulb_max_bri = bulb_settings['max_bri']
    #     bulb_min_bri = bulb_settings['min_bri']
    #     bri = utility.get_brightness(screen, bulb_max_bri, bulb_min_bri, dark_ratio)

    #     if party:
    #         rgb = utility.party_rgb()
    #         try:
    #             bri = random.randrange(int(screen.min_bri), int(bri) + 1)
    #         except ValueError:
    #             continue

    #     hue_interface.update_light(bulb, rgb, bri)

    #     try:
    #         bulb_settings = screen.bulb_settings[str(bulb)]
    #         bulb_state = hue_interface.get_bulb_state(bulb_settings, rgb, bri, screen.update)
    #         bulb_states[bulb] = bulb_state
    #     except Exception as e:
    #         print(e.message)
    #         continue

    # for bulb in bulb_states:
    #     hue_interface.update_light(screen.ip, screen.devicename, bulb, bulb_states[bulb])


# Main loop
# @func_timer
def run():
    screen = get_screen_object()
    sleep(float(screen.update_buffer))

    if screen.party_mode:
        update_bulb_party()
        sleep(float(screen.update))
    else:
        results = img_proc.screen_avg(screen)
        screenbloom_control_flow(results)


def screenbloom_control_flow(screen_avg_results):
    try:
        # Zone Mode
        if 'zones' in screen_avg_results:
            for zone in screen_avg_results['zones']:
                zone_bulbs = [int(bulb) for bulb in zone['bulbs']]
                send_light_commands(zone_bulbs, zone['rgb'], zone['dark_ratio'])

        # Standard Mode
        else:
            rgb = screen_avg_results['rgb']
            dark_ratio = screen_avg_results['dark_ratio']
            update_bulbs(rgb, dark_ratio)
    except Exception as e:
        pass
