from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import FormView

from .models import Setting
from .form import ControllerForm
from django.conf import settings
import requests


class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')
    headers = {'Authorization': 'Bearer {}'.format(settings.SMART_HOME_ACCESS_TOKEN)}
    list_sensors = requests.get(settings.SMART_HOME_API_URL, headers=headers).json()["data"]

    def get_context_data(self, **kwargs):
        context = super(ControllerView, self).get_context_data()
        context['data'] = val_sensors(self.list_sensors)
        return context

    def get_initial(self):
        return {
            'bedroom_target_temperature':
                Setting.objects.get(controller_name="bedroom_target_temperature").value,
            'hot_water_target_temperature':
                Setting.objects.get(controller_name="hot_water_target_temperature").value,
            'bedroom_light':
                val_sensors(self.list_sensors)['bedroom_light'],
            'bathroom_light':
                val_sensors(self.list_sensors)['bathroom_light'],
        }

    def form_valid(self, form):
        temp_bedroom = Setting.objects.get(controller_name="bedroom_target_temperature")
        temp_bedroom.value = form["bedroom_target_temperature"].value()
        temp_bedroom.save()
        temp_water = Setting.objects.get(controller_name="hot_water_target_temperature")
        temp_water.value = form["hot_water_target_temperature"].value()
        temp_water.save()
        
        return super(ControllerView, self).form_valid(form)


def val_sensors(list_sensors):
    new_dict_sensors = {}

    for sensor in list_sensors:
        new_dict_sensors.update({sensor["name"]: sensor["value"]})

    return new_dict_sensors
