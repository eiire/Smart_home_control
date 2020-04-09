CONTROLLERS_SCHEMA = {
    '$schema': 'http://json-schema.org/schema#',
    'type': 'object',
    'properties': {
        'bedroom_target_temperature': {
            'type': 'integer',
            'minLength': 16,
            'maxLength': 50,
        },
        'hot_water_target_temperature': {
            'type': 'integer',
            'minLength': 24,
            'maxLength': 90,
        },
        'bedroom_light': {
            'type': 'boolean',
        },
        'bathroom_light': {
            'type': 'boolean',
        }
    },
    'required': ['bedroom_target_temperature', 'hot_water_target_temperature', 'bedroom_light', 'bathroom_light'],
}