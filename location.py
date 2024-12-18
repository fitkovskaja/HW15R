import requests
import json

def get_forecast(api_key, location_key, days=5, language='ru-RU'):

    url = f'http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}'
    params = {
        'api_key': api_key,
        'language': language,
        'metric': 'true',
        'details': 'true'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        forecast_data = response.json()

        # Debugging
        print(f"Response from AccuWeather API: {forecast_data}")
        if 'DailyForecasts' not in forecast_data:
            raise ValueError(f"Unexpected response format: {forecast_data}")

        forecast_list = []
        for day in forecast_data['DailyForecasts']:
            forecast = {
                'date': day['Date'],
                'min_temp': day['Temperature']['Minimum']['Value'],
                'max_temp': day['Temperature']['Maximum']['Value'],
                'humidity': day['Day']['RelativeHumidity'],
                'wind_speed': day['Day']['Wind']['Speed']['Value'],
                'precipitation_probability': day['Day']['PrecipitationProbability']
            }
            forecast_list.append(forecast)

        return forecast_list

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return []
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return []
    except KeyError as ke:
        print(f"KeyError: {ke}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []



def get_location_key_geoposition(api_key, long_lat, language='ru-RU'):

    url = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
    data = {
        'api_key': api_key,
        'q': ','.join(list(map(str, list(long_lat)))),
        'language': language
    }

    response = requests.get(url, params=data).text
    json_response = json.loads(response)

    return json_response['api_key']

def get_location_key_name(api_key, name, language='ru-RU'):

    url = 'http://dataservice.accuweather.com/locations/v1/cities/search'
    data = {
        'api_key': api_key,
        'q': name,
        'language': language,
        'alias': 'Always'
    }

    try:
        response = requests.get(url, params=data).text
        json_response = json.loads(response)

        return json_response[0]['api_key'], json_response[0]['LocalizedName']
    except KeyError:
        raise KeyError('Несуществующий город или превышен лимит запросов')
    except TypeError:
        raise TypeError('Опаньки! Возможно, превышен лимит запросов')
    except IndexError:
        raise IndexError('Опаньки! Возможно, превышен лимит запросов')


def parse_conditions(current_response, forecast_response):

    current_json_response = json.loads(current_response)[0]
    forecast_json_response = json.loads(forecast_response)[0]

    response = dict()

    response['text_conditions'] = current_json_response['WeatherText']
    response['temperature'] = current_json_response['Temperature']['Metric']['Value']
    response['humidity'] = current_json_response['RelativeHumidity']
    response['wind_speed'] = current_json_response['Wind']['Speed']['Metric']['Value']
    response['precipitation_probability'] = forecast_json_response['PrecipitationProbability']

    return response



def get_conditions_by_key(api_key, location_key, language='ru-RU'):

    url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}'
    data = {
        'api_key': api_key,
        'language': language,
        'details': 'true'
    }

    current_response = requests.get(url, params=data).text

    # добываем вероятность осадков
    url = f'http://dataservice.accuweather.com/forecasts/v1/hourly/1hour/{location_key}'
    data = {
        'api_key': api_key,
        'language': language,
        'details': 'true',
        'metric': 'true'
    }

    forecast_response = requests.get(url, params=data).text

    return parse_conditions(current_response, forecast_response)


