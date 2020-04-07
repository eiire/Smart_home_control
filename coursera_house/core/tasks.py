from __future__ import absolute_import, unicode_literals
from celery import task

from .. import settings
from .models import Setting
import requests

headers = {'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN)}
state_controllers = list
hot_water_target_temperature = Setting.objects.get(controller_name="hot_water_target_temperature").value
bedroom_target_temperature = Setting.objects.get(controller_name="bedroom_target_temperature").value


@task()
def smart_home_manager():
    global state_controllers
    state_controllers = requests.get(settings.SMART_HOME_API_URL, headers=headers).json()["data"]


    if state_controllers[6]['value'] == False:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "washing_machine", "value": 'off'},
            {"name": "boiler", "value": False}
        ]})

    if state_controllers[15]['value'] == True:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "cold_water", "value": False},
            {"name": "hot_water", "value": False}
        ]})

    try:
        if state_controllers[14]['value'] <= hot_water_target_temperature * 0.90 \
                and state_controllers[5]['value'] == False\
                and state_controllers[2]['value'] == False:
            requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
                {"name": "boiler", "value": True}
            ]})

        if state_controllers[14]['value'] >= hot_water_target_temperature * 1.10 \
                and state_controllers[5]['value'] == True\
                and state_controllers[2]['value'] == False:
            requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
                {"name": "boiler", "value": False}
            ]})
    except:
        pass

    if state_controllers[16]['value'] < 50 and state_controllers[11]['value'] != 'slightly_open' and state_controllers[1]["value"] == False:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "curtains", "value": 'open'}
        ]})

    if state_controllers[16]['value'] > 50 and state_controllers[11]['value'] != 'slightly_open' or state_controllers[1]["value"] == True:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "curtains", "value": 'close'}
        ]})

    if state_controllers[2]['value']:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "air_conditioner", "value": False},
            {"name": "bedroom_light", "value": False},
            {"name": "bathroom_light", "value": False},
            {"name": "boiler", "value": False},
            {"name": "washing_machine", "value": 'off'}
        ]})

    if state_controllers[13]['value'] > bedroom_target_temperature * 1.10 and state_controllers[0]['value'] == False\
            and state_controllers[2]['value'] == False:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "air_conditioner", "value": True}
        ]})

    if state_controllers[13]['value'] < bedroom_target_temperature * 0.90 and state_controllers[0]['value'] == True\
            and state_controllers[2]['value'] == False:
        requests.post(settings.SMART_HOME_API_URL, headers=headers, json={"controllers": [
            {"name": "air_conditioner", "value": False}
        ]})





