from modules import sb_controller, startup, utility, view_logic, registration, presets, hue_interface
from flask import Flask, render_template, jsonify, request
# import vendor.rgb_xy as rgb_xy
from config import params
import argparse
import json
import sys
import os

app = Flask(__name__)

if params.ENV == 'prod':
    app = Flask(__name__, static_url_path='', static_folder='', template_folder='')
    app.secret_key = os.urandom(24)
    js_path = None
    css_path = None
    images_path = None
    fonts_path = None
    audio_path = None
elif params.ENV == 'dev':
    app.secret_key = os.urandom(24)
    js_path = '/static/js/'
    css_path = '/static/css/'
    images_path = '/static/images/'
    fonts_path = '/static/fonts/font-awesome/css/'
    audio_path = '/static/audio/'


@app.route('/')
def index():
    multi_screenshots = None
    if params.BUILD == 'win':
        utility.display_check(sb_controller.get_screen_object())
        multi_screenshots = utility.get_multi_monitor_screenshots()

    data = view_logic.get_index_data()
    zones = json.dumps(data['zones']) if data['zones'] else []

    # helper = rgb_xy.ColorHelper()
    white = [0,0,0]
    blue = [0,0,255]

    lightJs = {}
    for light in data['lights']:
      lightJs[light['id']] = light['active']

    return render_template('/home.html',
                           update=data['update'],
                           update_buffer=data['update_buffer'],
                           max_bri=data['max_bri'],
                           min_bri=data['min_bri'],
                           default=data['default'],
                           white=white,
                           blue=blue,
                           lights=data['lights'],
                           lights_number=data['lights_number'],
                           lightsJs=lightJs,
                           icon_size=data['icon_size'],
                           party_mode=data['party_mode'],
                           zones=zones,
                           zones_len=len(zones),
                           zone_state=data['zone_state'],
                           state=data['state'],
                           auto_start_state=int(data['auto_start_state']),
                           screenshot=utility.get_screenshot(int(data['display_index'])),
                           multi_monitor_screens=multi_screenshots,
                           display_index=int(data['display_index']),
                           sat=data['sat'],
                           version=params.VERSION,
                           environment=params.ENV,
                           build=params.BUILD,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path,
                           audio_path=audio_path,
                           presets=data['presets'],
                           current_preset=data['current_preset'],
                           fa_class_names=utility.get_fa_class_names(),
                           title='Home')


@app.route('/start')
def start():
    data = view_logic.start_screenbloom()
    return jsonify(data)


@app.route('/stop')
def stop():
    data = view_logic.stop_screenbloom()
    return jsonify(data)


@app.route('/new-user')
def new_user():
    return render_template('/new_user.html',
                           title='New User',
                           version=params.VERSION,
                           environment=params.ENV,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path)


@app.route('/manual')
def manual():
    return render_template('/new_user_manual.html',
                           title='Manual IP',
                           version=params.VERSION,
                           environment=params.ENV,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # hue_ip = request.args.get('hue_ip', 0, type=str)
    data = registration.register_logic(utility.get_local_host())
    return jsonify(data)


@app.route('/update-bri', methods=['POST'])
def update_bri():
    if request.method == 'POST':
        bri_values = request.json
        max_bri = bri_values[0]
        min_bri = bri_values[1]

        utility.write_config('Light Settings', 'min_bri', min_bri)
        utility.write_config('Light Settings', 'max_bri', max_bri)
        view_logic.restart_check()

        data = {
            'message': 'Brightness Updated',
            'max_bri': max_bri,
            'min_bri': min_bri
        }
        return jsonify(data)


@app.route('/update-update-speed', methods=['POST'])
def update_update_speed():
    if request.method == 'POST':
        transition = float(request.json['transition'])
        update_buffer = float(request.json['buffer'])

        utility.write_config('Light Settings', 'update', transition)
        utility.write_config('Light Settings', 'update_buffer', update_buffer)
        view_logic.restart_check()

        data = {
            'message': 'Settings Updated',
            'value': transition
        }
        return jsonify(data)


@app.route('/update-party-mode', methods=['POST'])
def update_party_mode():
    if request.method == 'POST':
        party_mode_state = request.json
        wording = 'enabled' if int(party_mode_state) else 'disabled'

        utility.write_config('Party Mode', 'running', party_mode_state)
        view_logic.restart_check()

        data = {
            'message': 'Party mode %s' % wording
        }
        return jsonify(data)


@app.route('/update-auto-start', methods=['POST'])
def update_auto_start():
    if request.method == 'POST':
        auto_start_state = request.json
        wording = 'disabled' if auto_start_state else 'enabled'

        new_value = 1
        if auto_start_state == 1:
            new_value = 0

        utility.write_config('Configuration', 'auto_start', new_value)
        view_logic.restart_check()

        data = {
            'message': 'Auto Start %s' % wording
        }
        return jsonify(data)


@app.route('/update-display', methods=['POST'])
def update_display():
    if request.method == 'POST':
        display_index = request.json

        try:
            new_img = utility.get_multi_monitor_screenshots()[int(display_index)]
            utility.write_config('Light Settings', 'display_index', display_index)
            message = 'Updated display'
        except IndexError:
            new_img = utility.get_multi_monitor_screenshots()[0]
            utility.write_config('Light Settings', 'display_index', 0)
            message = 'Display not found, defaulting to Primary'

        view_logic.restart_check()

        data = {
            'message': message,
            'img': new_img
        }
        return jsonify(data)


@app.route('/toggle-zone-state', methods=['POST'])
def toggle_zone_state():
    zone_state = request.json

    on_or_off = 'Off'
    if zone_state == 1:
        on_or_off = 'On'

    utility.write_config('Light Settings', 'zone_state', zone_state)
    view_logic.restart_check()

    data = {
            'message': 'Turned Zone Mode %s' % on_or_off
        }
    return jsonify(data)


@app.route('/update-zones', methods=['POST'])
def update_zones():
    if request.method == 'POST':
        zones = request.json

        utility.write_config('Light Settings', 'zones', zones)
        view_logic.restart_check()

        data = {
            'message': 'Zones Updated',
            'value': zones
        }
        return jsonify(data)


@app.route('/update-bulbs', methods=['POST'])
def update_bulbs():
    if request.method == 'POST':
        bulb_data = request.json
        bulbs = bulb_data['bulbs']
        bulb_settings = bulb_data['bulbSettings']
        sb_config = utility.get_config_dict()

        # lights_data = hue_interface.get_lights_data()
        # for light in lights_data:
        #     bulb = bulb_settings[str(light[0])]
        #     bulb['model_id'] = light[4]
        #     bulb['gamut'] = hue_interface.get_gamut(bulb['model_id'])
        #     bulb['name'] = light[2]

        utility.write_config('Light Settings', 'active', json.dumps(bulbs))
        utility.write_config('Light Settings', 'bulb_settings', json.dumps(bulb_settings))
        view_logic.restart_check()

        data = {
            'message': 'Bulbs updated',
            'bulbs': bulbs
        }
        return jsonify(data)


@app.route('/update-sat-value', methods=['POST'])
def update_sat_value():
    if request.method == 'POST':
        sat_value = request.json
        utility.write_config('Light Settings', 'sat', float(sat_value))
        view_logic.restart_check()

        data = {
            'message': 'Updated saturation value!'
        }
        return jsonify(data)


@app.route('/screenshot', methods=['POST'])
def refresh_screenshot():
    config = utility.get_config_dict()
    display_index = config['display_index']
    base64_data = utility.get_screenshot(display_index)
    data = {
        'message': 'Successfully took a screenshot!',
        'base64_data': base64_data
    }
    return jsonify(data)


@app.route('/regen-config', methods=['POST'])
def regen_config():
    if request.method == 'POST':
        message = 'Failed to remove config file.'
        success = registration.remove_config()
        if success:
            message = 'Successfully removed config file.'

        data = {
            'message': message,
            'success': success
        }
        return jsonify(data)


@app.route('/get-diagnostic-data', methods=['POST'])
def get_diagnostic_data():
    if request.method == 'POST':
        message = 'POOPSOCK'
        config = utility.get_config_dict()
        light_data = hue_interface.get_light_diagnostic_data()

        data = {
            'message': message,
            'data': light_data
        }
        return jsonify(data)


@app.route('/save-preset', methods=['POST'])
def save_preset():
    if request.method == 'POST':
        preset_number = presets.save_new_preset()
        preset = utility.get_preset_by_number(preset_number)
        utility.write_config('Configuration', 'current_preset', preset['preset_name'])
        message = 'Saved preset!'
        data = {
            'message': message,
            'preset_number': preset['preset_number'],
            'icon_class': preset['icon_class']
        }
        return jsonify(data)


@app.route('/delete-preset', methods=['POST'])
def delete_preset():
    if request.method == 'POST':
        preset_number = request.json
        presets.delete_preset(preset_number)
        message = 'Deleted preset!'
        data = {
            'message': message
        }
        return jsonify(data)


@app.route('/update-preset', methods=['POST'])
def update_preset():
    if request.method == 'POST':
        data = request.json

        preset_number = data['presetNumber']
        new_name = data['presetName']
        icon = data['iconClass']

        presets.update_preset(preset_number, new_name, icon)
        message = 'Preset updated!'
        data = {
            'message': message
        }
        return jsonify(data)


@app.route('/apply-preset', methods=['POST'])
def apply_preset():
    if request.method == 'POST':
        preset_number = request.json
        preset = presets.apply_preset(preset_number)

        message = '%s Applied!' % preset['preset_name']
        data = {
            'message': message,
            'preset': preset
        }
        return jsonify(data)


# Error Pages
@app.errorhandler(404)
def page_not_found(e):
    code = e.code
    name = e.name
    return render_template('/error.html',
                           code=code,
                           name=name,
                           version=params.VERSION,
                           environment=params.ENV,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path)


@app.errorhandler(500)
def page_not_found(e):
    error = str(e)
    if error == "No section: 'Configuration'":
        error = 'Looks like your config file doesn\'t exist yet!  ' \
                'You\'ll want to visit /new-user to complete the registration process.'

    return render_template('/error.html',
                           code=500,
                           name='Internal Server Error',
                           error=error,
                           version=params.VERSION,
                           environment=params.ENV,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path)


@app.route('/dll-error')
def dll_error_page():
    return render_template('/dll_error.html',
                           code='DLL',
                           name='DLL Load Error',
                           version=params.VERSION,
                           environment=params.ENV,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path)


@app.route('/update-config')
def update_config_page():
    return render_template('/update_config.html',
                           code='Config Needs Update',
                           name='Your Config File Needs to be Updated',
                           version=params.VERSION,
                           environment=params.ENV,
                           js_path=js_path,
                           css_path=css_path,
                           images_path=images_path,
                           fonts_path=fonts_path)


if __name__ == '__main__':
    # Check arguments
    parser = argparse.ArgumentParser()
    arg_help = 'Start ScreenBloom server without launching a browser. Uses existing config.'
    parser.add_argument('-q', '--silent', help=arg_help, action='store_true')
    args = parser.parse_args()

    local_host = utility.get_local_host()
    startup_thread = startup.StartupThread(local_host, 5000, args, app)
    startup_thread.run()
