
def check_weather(conditions, mode='center'):

    # Определяем границы погодных условий
    thresholds = {
        'warm weather': {'temp': (20, 45), 'humidity': 90, 'wind_speed': 40, 'precipitation_probability': 80},
        'moderate weather': {'temp': (-15, 25), 'humidity': 80, 'wind_speed': 50, 'precipitation_probability': 80},
        'cool weather': {'temp': (-30, 20), 'humidity': 70, 'wind_speed': 20, 'precipitation_probability': 80}
    }

    if mode not in thresholds:
        raise ValueError('Ошибка: несуществующий режим')

    result = True
    reasons = []

    # Проверяем реальные погодные условия
    for key, value in thresholds[mode].items():
        if key == 'temp':
            if conditions['temperature'] < value[0] or conditions['temperature'] > value[1]:
                result = False
                reasons.append('temperature')
        else:
            if conditions[key] > value:
                result = False
                reasons.append(key)

    return result, tuple(reasons)
