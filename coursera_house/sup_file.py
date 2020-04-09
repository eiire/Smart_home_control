from future import absolute_import, unicode_literals
from celery import task
from django.core.mail import send_mail,get_connection,EmailMessage
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import requests, os, json
from .models import Setting
def check(params)->bool:
    rezult=True
    if not isinstance(params['air_conditioner'],bool): rezult=False
    if not isinstance(params['bedroom_light'],bool): rezult=False
    if not isinstance(params['smoke_detector'],bool): rezult=False
    if not isinstance(params['bedroom_presence'],bool): rezult=False
    if not isinstance(params['bedroom_motion'],bool): rezult=False
    if not isinstance(params['boiler'],bool): rezult=False
    if not isinstance(params['cold_water'],bool): rezult=False
    if not isinstance(params['hot_water'],bool): rezult=False
    if not isinstance(params['bathroom_light'],bool): rezult=False
    if not isinstance(params['bathroom_motion'],bool): rezult=False
    if not isinstance(params['bathroom_presence'],bool): rezult=False
    if not isinstance(params['leak_detector'],bool): rezult=False
    if not params['curtains'] in ['open','close', 'slightly_open']: rezult=False
    if not params['washing_machine'] in ['off','on','broken']: rezult=False
    if not isinstance(params['bedroom_temperature'],int): rezult=False
    elif params['bedroom_temperature']>80 or params['bedroom_temperature']<0: rezult=False
    if not isinstance(params['boiler_temperature'],int) and params['boiler_temperature']!=None: rezult=False
    elif params['boiler_temperature']>100 or params['boiler_temperature']<0: rezult=False
    if not isinstance(params['outdoor_light'],int): rezult=False
    elif params['outdoor_light']>100 or params['outdoor_light']<0: rezult=False
    return rezult

@task()
def smart_home_manager():
    header={'Authorization':'Bearer '+ settings.SMART_HOME_ACCESS_TOKEN}
    try:
        data = requests.get(settings.SMART_HOME_API_URL,headers=header)
    except: return None
    if not data.status_code==200 : return None
    params = { param['name']:param['value'] for param in data.json()['data']}
    if not check(params) : return None
    params_old = { param['name']:param['value'] for param in data.json()['data']}
    connection = get_connection(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=True)
    hotwater_temp=Setting.objects.filter(controller_name='hot_water_target_temperature').get().value
    bedroom_temp_setting=Setting.objects.filter(controller_name='bedroom_target_temperature').get().value
    if params['smoke_detector']:
        params['air_conditioner']=False
        params['bedroom_light']=False
        params['bathroom_light']=False
        params['boiler']=False
        params['washing_machine']='off'

else:
        if params['boiler_temperature']<hotwater_temp-(hotwater_temp*0.1):
            params['boiler']=True
        elif params['boiler_temperature']>=hotwater_temp+(hotwater_temp*0.1):
            params['boiler']=False
        if params['bedroom_temperature']>bedroom_temp_setting+(bedroom_temp_setting*0.1):
            params['air_conditioner']=True
        elif params['bedroom_temperature']<bedroom_temp_setting-(bedroom_temp_setting*0.1):
            params['air_conditioner']=False
    if params['leak_detector']:
        params['cold_water']=False
        params['hot_water']=False
        send_mail('Coursera House - LEAK DETECTION', 'Leak detekted', settings.EMAIL_HOST_USER,[settings.EMAIL_RECEPIENT],connection=connection)
    if not params['cold_water']:
        params['boiler']=False
        params['washing_machine']='off'
    if params['curtains'] != 'slightly_open':
        if params['outdoor_light']<50 and not params['bedroom_light']:
            params['curtains'] = 'open'
        elif params['outdoor_light']>50  or params['bedroom_light']:
            params['curtains'] = 'close'
    if params!=params_old:
        params_post=json.dumps({'controllers':[{'name': param, 'value': params[param]} for param in params if not param=='bedroom_temperature']})
        try:
            data = requests.post(settings.SMART_HOME_API_URL,headers=header,data=params_post)
        except: return None
        if not data.status_code==200 : return None
        if not check(params) : return None
    return params

# Если есть протечка воды (leak_detector=true), закрыть холодную
#   (cold_water=false) и горячую (hot_water=false) воду и отослать
#   письмо в момент обнаружения.
# Если холодная вода (cold_water) закрыта, немедленно выключить бойлер
#   (boiler) и стиральную машину
#   (washing_machine) и ни при каких условиях не
#   включать их, пока холодная вода не будет снова открыта.
# Если горячая вода имеет температуру (boiler_temperature) меньше
#   чем hot_water_target_temperature - 10%,
#   нужно включить бойлер (boiler), и ждать
#   пока она не достигнет температуры hot_water_target_temperature + 10%,
#   после чего в целях экономии энергии бойлер нужно отключить
# Если шторы частично открыты (curtains == “slightly_open”),
#   то они находятся на ручном управлении - это
#   значит их состояние нельзя изменять автоматически ни при каких условиях.
# Если на улице (outdoor_light) темнее 50, открыть шторы (curtains), но только если не горит лампа в спальне
#   (bedroom_light). Если на улице (outdoor_light) светлее 50,
#   или горит свет в спальне (bedroom_light), закрыть шторы.
#   Кроме случаев когда они на ручном управлении
# Если обнаружен дым (smoke_detector), немедленно выключить следующие приборы [air_conditioner, bedroom_light,
#   bathroom_light, boiler, washing_machine],
#   и ни при каких условиях не включать их, пока дым не исчезнет.
# Если температура в спальне (bedroom_temperature) поднялась
#   выше bedroom_target_temperature + 10% - включить
#   кондиционер (air_conditioner), и ждать пока температура
#   не опустится ниже bedroom_target_temperature - 10%,
#   после чего кондиционер отключить.

# 'air_conditioner': False,
# 'bedroom_light': False,
# 'smoke_detector': False,
# 'bedroom_presence': False,
# 'bedroom_motion': False,
# 'boiler': False,
# 'cold_water': False,
# 'hot_water': False,
# 'bathroom_light': False,
# 'bathroom_motion': False,
# 'bathroom_presence': False,
# 'curtains': 'close',
# 'washing_machine': 'off',
# 'bedroom_temperature': 26,
# 'boiler_temperature': None,
# 'leak_detector': False,
# 'outdoor_light': 55

# 'air_conditioner': False,
# 'bedroom_light': False,
# 'boiler': False,
# 'cold_water': False,
# 'hot_water': False,
# 'bathroom_light': False,
# 'curtains': 'close',
# 'washing_machine': 'off',