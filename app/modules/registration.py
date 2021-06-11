from modules import sb_controller, hue_interface, utility
import configparser
import requests 
import json
import os


# Create config file on first run
def create_config():
    config = configparser.RawConfigParser()
    lights = hue_interface.get_lights_list()
    active = {}

    data = hue_interface.get_lights_data()
    for light in data:
        if light['active']:
            active[light['id']] = light['active']

    default_bulb_settings = {}
    for light in lights:
        settings = {
            'max_bri': 254,
            'min_bri': 1
        }
        default_bulb_settings[light] = settings

    config.add_section('Configuration')
    # config.set('Configuration', 'hue_ip', hue_ip)
    # config.set('Configuration', 'username', username)
    config.set('Configuration', 'auto_start', 0)
    config.set('Configuration', 'current_preset', '')

    config.add_section('Light Settings')
    config.set('Light Settings', 'all_lights', ','.join(lights))
    config.set('Light Settings', 'active', json.dumps(active))
    config.set('Light Settings', 'bulb_settings', json.dumps(default_bulb_settings))
    config.set('Light Settings', 'update', '0.7')
    config.set('Light Settings', 'update_buffer', '0')
    config.set('Light Settings', 'default', '')
    config.set('Light Settings', 'max_bri', '254')
    config.set('Light Settings', 'min_bri', '1')
    config.set('Light Settings', 'zones', '[]')
    config.set('Light Settings', 'zone_state', 0)
    config.set('Light Settings', 'display_index', 0)
    config.set('Light Settings', 'sat', 1.0)

    config.add_section('Party Mode')
    config.set('Party Mode', 'running', 0)

    config.add_section('App State')
    config.set('App State', 'running', False)

    directory = utility.get_config_dir()
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(utility.get_config_path(), 'w') as config_file:
        config.write(config_file)

    # Now that the config is created, set initial light setting
    utility.write_config('Light Settings', 'default', json.dumps(utility.get_initial_state()))


def remove_config():
    file_path = utility.get_config_path()
    success = True

    try:
        os.remove(file_path)
    except Exception:
        success = False

    return success


def register_logic(host):
    # if not ip:
    #     # Attempting to grab IP from Philips uPNP app
    #     try:
    #         requests.packages.urllib3.disable_warnings()
    #         url = 'https://www.meethue.com/api/nupnp'
    #         r = requests.get(url, verify=False).json()
    #         ip = str(r[0]['internalipaddress'])
    #     except Exception:
    #         # utility.write_traceback()
    #         error_type = 'manual'
    #         error_description = 'Error grabbing Hue IP, redirecting to manual entry...'
    #         data = {
    #             'success': False,
    #             'error_type': error_type,
    #             'error_description': error_description,
    #             'host': host
    #         }
    #         return data
    # try:
    #     # Send post request to Hue bridge to register new username, return response as JSON
    #     result = register_device(ip)
    #     temp_result = result[0]
    #     result_type = ''
    #     for k, v in temp_result.items():
    #         result_type = str(k)
    #     if result_type == 'error':
    #         error_type = result[0]['error']['type']
    #         error_description = result[0]['error']['description']
    #         data = {
    #             'success': False,
    #             'error_type': str(error_type),
    #             'error_description': str(error_description)
    #         }
    #         return data
    #     else:
    #         # Successfully paired with bridge, create config file
    #         username = temp_result[result_type]['username']
    #         create_config(ip, username)
    #         data = {
    #             'success': True,
    #             'message': 'Success!'
    #         }
    #         return data
    # except requests.exceptions.ConnectionError:
    #     data = {
    #         'success': False,
    #         'error_type': 'Invalid URL',
    #         'error_description': 'Something went wrong with the connection, please try again...'
    #     }
    #     return data
    # except IOError:
    #     data = {
    #         'success': False,
    #         'error_type': 'permission',
    #         'error_description': 'Permission denied, administrator rights needed..'
    #     }
    #     return data
    create_config()
    return { 'success' : True, 'message': 'Sengled App'}


# Add username to bridge whitelist
def register_device(hue_ip):
    url = 'http://%s/api/' % hue_ip
    data = {
        'devicetype': 'ScreenBloom'
    }
    body = json.dumps(data)
    r = requests.post(url, data=body, timeout=5)
    return r.json()
