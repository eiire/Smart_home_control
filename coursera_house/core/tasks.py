from __future__ import absolute_import, unicode_literals
from celery import task
from django.core.mail import get_connection, send_mail
from django.http import HttpResponse, JsonResponse
# from .. import settings
from django.conf import settings
from .models import Setting
import requests


@task()
def smart_home_manager():
    headers = {'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN)}
    state_controllers = comfort_dict(requests.get(settings.SMART_HOME_API_URL, headers=headers).json()["data"])
    fixed_state_controllers = check_state_controllers(dict(state_controllers))

    if check_change_controllers(state_controllers, fixed_state_controllers):
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json=create_post(fixed_state_controllers))


def check_state_controllers(state_controllers):
    if state_controllers['leak_detector'] == True:
        fix_state_home(1, state_controllers)

    if state_controllers['cold_water'] == False:
        fix_state_home(2, state_controllers)

    if state_controllers['cold_water'] == True and state_controllers["smoke_detector"] == False:
        if state_controllers['boiler_temperature'] < \
                Setting.objects.get(controller_name='hot_water_target_temperature').value * 0.90:
            fix_state_home(3, state_controllers)

        if state_controllers['boiler_temperature'] >= \
                Setting.objects.get(controller_name='hot_water_target_temperature').value * 1.10:
            fix_state_home(4, state_controllers)

    if state_controllers['curtains'] != 'slightly_open':
        if state_controllers["outdoor_light"] < 50 and state_controllers["bedroom_light"] == False:
            fix_state_home(5, state_controllers)

        if state_controllers['outdoor_light'] > 50 or state_controllers["bedroom_light"] == True:
            fix_state_home(6, state_controllers)

    if state_controllers['smoke_detector'] == True:
        fix_state_home(7, state_controllers)

    if state_controllers["smoke_detector"] == False:
        if state_controllers['bedroom_temperature'] > \
                Setting.objects.get(controller_name='bedroom_target_temperature').value * 1.10:
            fix_state_home(8, state_controllers)

        if state_controllers['bedroom_temperature'] < \
                Setting.objects.get(controller_name='bedroom_target_temperature').value * 0.90:
            fix_state_home(9, state_controllers)

    return state_controllers


def fix_state_home(fix_params, fixes):
    if fix_params == 1:
        fixes["cold_water"] = False
        fixes["hot_water"] = False
        fixes["boiler"] = False
        fixes["washing_machine"] = 'off'

        connection = get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=True
        )

        send_mail('Coursera House - LEAK', 'Leak detected', settings.EMAIL_HOST_USER, [settings.EMAIL_RECEPIENT], connection=connection)

    if fix_params == 2:
        fixes["boiler"] = False
        fixes["washing_machine"] = 'off'

    if fix_params == 3:
        fixes["boiler"] = True

    if fix_params == 4:
        fixes["boiler"] = False

    if fix_params == 5:
        fixes["curtains"] = 'open'

    if fix_params == 6:
        fixes["curtains"] = 'close'

    if fix_params == 7:
        fixes["air_conditioner"] = False
        fixes["bedroom_light"] = False
        fixes["bathroom_light"] = False
        fixes["boiler"] = False
        fixes["washing_machine"] = 'off'

    if fix_params == 8:
        fixes["air_conditioner"] = True

    if fix_params == 9:
        fixes["air_conditioner"] = False


def create_post(fixed_state_controllers):
    fixed_answear = {
        'controllers': []
    }

    for key, value in fixed_state_controllers.items():
        if key != 'outdoor_light' \
                and key != 'leak_detector' \
                and key != 'boiler_temperature'\
                and key != 'bedroom_temperature'\
                and key != 'bathroom_presence'\
                and key != 'bathroom_motion'\
                and key != 'bedroom_motion'\
                and key != 'bedroom_presence'\
                and key != 'smoke_detector':
            fixed_answear['controllers'].append({'name': key, 'value': value})

    return fixed_answear


def check_change_controllers(state_controllers, fixed_state_controllers):
    for key, value in fixed_state_controllers.items():
        if state_controllers[key] != value:
            return True

    return False


def comfort_dict(state_controllers):
    controllers = {}

    for sensor in state_controllers:
        controllers.update({sensor["name"]: sensor["value"]})

    return controllers