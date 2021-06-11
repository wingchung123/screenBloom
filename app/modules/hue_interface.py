# import vendor as rgb_xy
from modules import sb_controller, utility
import requests
import json
import sengled

f = open("cred.txt", 'r')
username, password = f.readline().split(',')
f.close()

api = sengled.api(
    # The username/password that you used to create your mobile account in
    # the Sengled Home app.
    username=username,
    password=password,

    # Optional path to persist the session across multiple process
    # starts and reduce the number of logins.
    session_path="/tmp/sengled.pickle",

    # Prints details of the api request/responses when True, defaults to false.
    debug=True
)


# Return more detailed information about specified lights
def get_lights_data():
    # config = utility.get_config_dict()

    # all_lights = [int(i) for i in config['all_lights'].split(',')]
    # active_bulbs = [int(i) for i in config['active'].split(',')]
    # lights = []

    # for counter, light in enumerate(all_lights):
    #     result = get_light(hue_ip, username, light)

    #     if type(result) is dict:  # Skip unavailable lights
    #         state = result['state']['on']
    #         light_name = result['name']
    #         model_id = result['modelid']
    #         bri = result['state']['bri']

    #         # Setting defaults for non-color bulbs
    #         try:
    #             colormode = result['state']['colormode']
    #         except KeyError:
    #             colormode = None

    #         try:
    #             xy = result['state']['xy']
    #         except KeyError:
    #             xy = []

    #         active = light if int(light) in active_bulbs else 0
    #         light_data = [light, state, light_name, active, model_id, bri, xy, colormode]

    #         lights.append(light_data)

    lights = api.get_device_details()

    data = []
    for bulb in lights:
        data.append({
            'id': bulb.id,
            'name' : bulb.name,
            'active' : bulb.is_online,
            'state' : bulb.onoff,
            'bri' : bulb.brightness,
            'rgb' : bulb.color,
            'max_bri': 254,
            'min_bri': 1,
            'product_code' : bulb.product_code
            })

    return data


# Return list of current Hue addressable light IDs
def get_lights_list():
    lights = api.get_device_details()

    lights_list = []
    for light in lights:
        try:
            lights_list.append(light.id)
        except KeyError:
            continue

    return lights_list


# Send on/off Hue API command to bulbs
def lights_on_off(state):
    _screen = sb_controller.get_screen_object()

    active_lights = _screen.bulbs
    on = True if state == 'on' else False

    for bulb in active_lights:
        get_light(bulb).set_on_off(on)

# Constructs Hue data structure for bulb state change
def get_bulb_state(bulb_settings, rgb_or_xy, bri, update):
    bulb_gamut = bulb_settings['gamut']
    gamut = get_rgb_xy_gamut(bulb_gamut)
    converter = rgb_xy.Converter(gamut)

    state = {
        'bri': int(bri),
        'transitiontime': utility.get_transition_time(update)
    }

    if rgb_or_xy:
        if len(rgb_or_xy) > 2:  # [R, G, B] vs [X, Y]
            try:
                hue_color = converter.rgb_to_xy(rgb_or_xy[0], rgb_or_xy[1], rgb_or_xy[2])
            except ZeroDivisionError:
                return
        else:
            hue_color = (rgb_or_xy[0], rgb_or_xy[1])

        state['xy'] = hue_color

    return json.dumps(state)


# def get_rgb_xy_gamut(bulb_gamut):
#     if bulb_gamut == 'A':
#         return rgb_xy.GamutA
#     elif bulb_gamut == 'B':
#         return rgb_xy.GamutB
#     elif bulb_gamut == 'C':
#         return rgb_xy.GamutC

def get_light(string):
    if ' ' in string:
        # assume name
        bulb = get_light_by_name(string)
    else:
        bulb = get_light_by_id(string)

    return bulb

def get_light_by_id(bulb_id):
    bulb = api.find_by_id(bulb_id)
    return bulb

def get_light_by_name(name):
    bulb = api.find_by_name(name)
    return bulb

def get_all_lights():
    devices = api.get_device_details()
    return devices

def update_all_lights(bulb_ids, rgb, brightness):
    api.set_color(bulb_ids, rgb)
    api.set_brightness(bulb_ids, int(brightness*100/255))


# @func_timer
def update_light(bulb_id, rgb, brightness):
    api.find_by_id(bulb_id).set_color(rgb).set_brightness(int(brightness*100/255))



# def _get_hue_url(hue_ip, username, light_id=None):
#     url = 'http://{bridge_ip}/api/{username}/lights'
#     if light_id:
#         url += '/{light_id}/state'
#         return url.format(bridge_ip=hue_ip,
#                           username=username,
#                           light_id=light_id)

#     return url.format(bridge_ip=hue_ip,
#                       username=username)


# def get_gamut(model_id):
#     try:
#         gamut = GAMUTS[model_id]['gamut']
#     except KeyError:
#         gamut = 'B'
#     return gamut

# # https://developers.meethue.com/documentation/supported-lights
# GAMUTS = {
#     'LCT001': {
#         'name': 'Hue bulb A19',
#         'gamut': 'B'
#     },
#     'LCT007': {
#         'name': 'Hue bulb A19',
#         'gamut': 'B'
#     },
#     'LCT010': {
#         'name': 'Hue bulb A19',
#         'gamut': 'C'
#     },
#     'LCT014': {
#         'name': 'Hue bulb A19',
#         'gamut': 'C'
#     },
#     'LCT002': {
#         'name': 'Hue Spot BR30',
#         'gamut': 'B'
#     },
#     'LCT003': {
#         'name': 'Hue Spot GU10',
#         'gamut': 'B'
#     },
#     'LCT011': {
#         'name': 'Hue BR30',
#         'gamut': 'C'
#     },
#     'LST001': {
#         'name': 'Hue LightStrips',
#         'gamut': 'A'
#     },
#     'LLC010': {
#         'name': 'Hue Living Colors Iris',
#         'gamut': 'A'
#     },
#     'LLC011': {
#         'name': 'Hue Living Colors Bloom',
#         'gamut': 'A'
#     },
#     'LLC012': {
#         'name': 'Hue Living Colors Bloom',
#         'gamut': 'A'
#     },
#     'LLC006': {
#         'name': 'Living Colors Gen3 Iris*',
#         'gamut': 'A'
#     },
#     'LLC007': {
#         'name': 'Living Colors Gen3 Bloom, Aura*',
#         'gamut': 'A'
#     },
#     'LLC013': {
#         'name': 'Disney Living Colors',
#         'gamut': 'A'
#     },
#     'LLM001': {
#         'name': 'Color Light Module',
#         'gamut': 'A'
#     },
#     'LLC020': {
#         'name': 'Hue Go',
#         'gamut': 'C'
#     },
#     'LST002': {
#         'name': 'Hue LightStrips Plus',
#         'gamut': 'C'
#     },
# }
