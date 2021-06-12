from config import params
from modules import hue_interface, icon_names
import configparser
import traceback
import requests
import io
import socket
import shutil
import random
import json
import sys
import os
import base64

def dll_check():
    try:
        from desktopmagic.screengrab_win32 import getDisplaysAsImages
    except ImportError:
        return False
    return True

if dll_check():
    import img_proc

if params.ENV == 'prod':
    current_path = ''
elif params.ENV == 'dev':
    current_path = os.path.dirname(os.path.abspath(__file__)) + '\\'


# Ping Google's DNS server to reveal IP
def get_local_host():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    local_host = (s.getsockname()[0])
    s.close()
    return local_host


def config_check():
    try:
        # Grab config variables, will throw an error if there is a mismatch
        test = get_config_dict()
        return True
    except configparser.NoOptionError:
        return False
    except configparser.NoSectionError:
        return False

def get_config_dir(old_check=False):
    config_path = ''

    if params.BUILD == 'win':
        config_path = os.getenv('APPDATA') + '\\screenBloom' if not old_check else os.getenv('APPDATA')
    elif params.BUILD == 'mac':
        config_path = ''
        if getattr(sys, 'frozen', False):
            config_path = os.path.dirname(sys.executable)
        elif __file__:
            config_path = os.path.dirname(__file__)
    else:
        config_path = os.getcwd() + '/screenBloom' if not old_check else os.getcwd()
        return config_path


    return config_path 

def get_config_path(old_check=False):
    config_path = ''

    if params.BUILD == 'win':
        config_path = os.getenv('APPDATA') + '\\screenBloom' if not old_check else os.getenv('APPDATA')
    elif params.BUILD == 'mac':
        config_path = ''
        if getattr(sys, 'frozen', False):
            config_path = os.path.dirname(sys.executable)
        elif __file__:
            config_path = os.path.dirname(__file__)
    else:
        config_path = os.getcwd() + '/screenBloom' if not old_check else os.getcwd()
        return config_path + '/screenBloom_config.cfg'


    return config_path + '\\screenBloom_config.cfg'


def move_files_check():
    new_dir = os.getenv('APPDATA') + '\\screenBloom'

    if os.path.isfile(get_config_path(True)):
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        shutil.move(get_config_path(True), get_config_path())

    if os.path.isfile(get_json_filepath(True)):
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        shutil.move(get_json_filepath(True), get_json_filepath())


# Check server status
def check_server(host, port):
    try:
        r = requests.get('http://%s:%d/new-user' % (host, port))
        response = r.status_code
    except requests.ConnectionError:
        response = 404
    if response == 200:
        return True
    else:
        return False


# Rewrite config file with given arguments
def write_config(section, item, value):
    config = configparser.RawConfigParser()
    config.read(get_config_path())
    config.set(section, item, value)

    with open(get_config_path(), 'w') as config_file:
        config.write(config_file)


# Write traceback to logfile
def write_traceback():
    with open('log.txt', 'a+') as f:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, file=f)


# Generate random RGB
def party_rgb():
    r = lambda: random.randint(0, 255)
    rgb = (r(), r(), r())
    return rgb


def get_screenshot(display_index):
    # Win version
    if params.BUILD == 'win':
        # from desktopmagic.screengrab_win32 import getDisplaysAsImages
        # imgs = getDisplaysAsImages()
        # try:
        #     img = imgs[int(display_index)]
        # except IndexError:
        #     img = imgs[0]
        from PIL import ImageGrab
        img = ImageGrab.grab()  
    # Mac version
    elif params.BUILD == 'mac':
        from PIL import ImageGrab
        img = ImageGrab.grab()
    elif params.BUILD == 'linux':
        import pyscreenshot as ImageGrab
        img = ImageGrab.grab()

    tmp = io.BytesIO()
    img.save(tmp, format="PNG")
    return base64.b64encode(tmp.read())


def get_multi_monitor_screenshots():
    imgs = img_proc.get_monitor_screenshots()
    screenshots = []

    for img in imgs:
        tmp = io.BytesIO()
        img.save(tmp, format="PNG")
        b64_data = base64.b64encode(tmp.read())
        screenshots.append(b64_data)

    return screenshots


def display_check(_screen):
    displays = img_proc.get_monitor_screenshots()
    try:
        displays[int(_screen.display_index)]
    except IndexError as e:
        write_config('Light Settings', 'display_index', 0)
        _screen.display_index = 0
    return


# Return modified Hue brightness value from ratio of dark pixels
def get_brightness(_screen, max_bri, min_bri, dark_pixel_ratio):
    max_bri = int(max_bri)
    min_bri = int(min_bri)

    normal_range = max(1, max_bri - 1)
    new_range = max_bri - min_bri

    brightness = max_bri - (dark_pixel_ratio * max_bri) / 100
    scaled_brightness = (((brightness - 1) * new_range) / normal_range) + float(min_bri) + 1

    # Global brightness check
    if int(scaled_brightness) < int(_screen.min_bri):
        scaled_brightness = int(_screen.min_bri)
    elif int(scaled_brightness) > int(_screen.max_bri):
        scaled_brightness = int(_screen.max_bri)

    return int(scaled_brightness)


# Convert update speed to ms, check lower bound
def get_transition_time(update_speed):
    update_speed = int(float(update_speed) * 10)
    return update_speed if update_speed > 2 else 2


def get_config_dict():
    config = configparser.RawConfigParser()
    config.read(get_config_path())

    autostart = config.getboolean('Configuration', 'auto_start')
    current_preset = config.get('Configuration', 'current_preset')

    all_lights = config.get('Light Settings', 'all_lights')
    active = config.get('Light Settings', 'active')
    bulb_settings = config.get('Light Settings', 'bulb_settings')
    update = config.get('Light Settings', 'update')
    update_buffer = config.get('Light Settings', 'update_buffer')
    default = config.get('Light Settings', 'default')
    max_bri = config.get('Light Settings', 'max_bri')
    min_bri = config.get('Light Settings', 'min_bri')
    zones = config.get('Light Settings', 'zones')
    zone_state = config.getboolean('Light Settings', 'zone_state')
    display_index = config.get('Light Settings', 'display_index')
    sat = config.get('Light Settings', 'sat')

    party_mode = config.getboolean('Party Mode', 'running')

    app_state = config.getboolean('App State', 'running')

    return {
        'autostart': autostart,
        'current_preset': current_preset,
        'all_lights': all_lights,
        'active': active,
        'bulb_settings': bulb_settings,
        'update': update,
        'update_buffer': update_buffer,
        'default': default,
        'max_bri': max_bri,
        'min_bri': min_bri,
        'zones': zones,
        'zone_state': zone_state,
        'display_index': display_index,
        'sat': sat,
        'party_mode': party_mode,
        'app_state': app_state
    }


def get_json_filepath(old_check=False):
    path = os.getenv('APPDATA') if os.getenv('APPDATA') is not None else os.getcwd()
    if old_check:
        filepath = path+ '\\screenBloom_presets.json'
    else:
        filepath = path + '\\screenBloom\\screenBloom_presets.json'
    return filepath


def get_all_presets():
    filepath = get_json_filepath()
    presets = []
    if os.path.isfile(filepath):
        with open(filepath) as data_file:
            presets = json.load(data_file)
    return presets


def get_preset_by_number(preset_number):
    with open(get_json_filepath()) as data_file:
        presets = json.load(data_file)
        key = 'preset_' + str(preset_number)
        return presets[key]


# Quickly get Python list of ~500 Font Awesome icon names
def get_fa_class_names():
    return icon_names.preset_icon_names


# Will continue to expand this function as the bulb_settings JSON gets added to
def get_current_light_settings():
    config_dict = get_config_dict()
    lights_data = hue_interface.get_lights_data()
    light_settings = {}
    for light in lights_data:
        light_settings[str(light['id'])] = {
            'name': light['name'],
            'model_id': light['product_code'],
            'rgb': light['rgb']
        }
    return light_settings


def get_initial_state():
    light_data = hue_interface.get_lights_data()

    initial_lights_state = {}
    for light in light_data:
        initial_lights_state[light['id']] = light
    return initial_lights_state


def write_light_data_to_file():
    config = get_config_dict()
    light_data = hue_interface.get_all_lights()
    with open('LIGHT_DATA.txt', 'w') as f:
        json.dump(light_data, f)

    input('Data written to LIGHT_DATA.txt.  Press any key to contiue...')
