from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView
from jsonschema import validate
from .models import Setting
from .form import ControllerForm
from django.conf import settings
import requests
from .schemas import CONTROLLERS_SCHEMA


class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')
    headers = {'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN)}
    state_controllers = []

    def get_context_data(self, **kwargs):
        context = super(ControllerView, self).get_context_data()
        context['data'] = val_sensors(self.state_controllers)
        return context

    def get_initial(self):
        response = requests.get(settings.SMART_HOME_API_URL, headers=self.headers)
        if response.status_code == 200:
            self.state_controllers = response.json()["data"]

            return {
                'bedroom_target_temperature':
                    Setting.objects.get(controller_name="bedroom_target_temperature").value,
                'hot_water_target_temperature':
                    Setting.objects.get(controller_name="hot_water_target_temperature").value,
                'bedroom_light':
                    val_sensors(self.state_controllers)['bedroom_light'],
                'bathroom_light':
                    val_sensors(self.state_controllers)['bathroom_light'],
            }
        else:
            return HttpResponse(status=502)

    def form_valid(self, form):
        temp_bedroom = Setting.objects.get(controller_name="bedroom_target_temperature")
        temp_bedroom.value = form["bedroom_target_temperature"].value()
        temp_bedroom.save()

        temp_water = Setting.objects.get(controller_name="hot_water_target_temperature")
        temp_water.value = form["hot_water_target_temperature"].value()
        temp_water.save()

        json = {"controllers": [{"name": "bedroom_light", "value": form['bedroom_light'].value()},
                                {"name": "bathroom_light", "value": form['bathroom_light'].value()}]
                }
        requests.post(settings.SMART_HOME_API_URL, headers=self.headers, json=json)

        return super(ControllerView, self).form_valid(form)


def val_sensors(state_controllers):
    comfort_dict = {}

    for sensor in state_controllers:
        comfort_dict.update({sensor["name"]: sensor["value"]})

    return comfort_dict