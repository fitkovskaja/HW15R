import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
import plotly.express as px
import pandas as pd
from location import get_location_key_name, get_conditions_by_key, get_forecast, get_location_key_geoposition
import folium
from folium import IFrame

app = dash.Dash(__name__, external_stylesheets=["styles.css", "https://codepen.io/chriddyp/pen/bWLwgP.css"], prevent_initial_callbacks='initial_duplicate')

app.layout = html.Div(className='container', children=[
    html.H1("Прогноз погоды на маршруре, сравнение погоды в разных городах", className='title'),

    dcc.Input(id="api_key", type="text", placeholder="Введите API ключ AccuWeather", style={'display': 'none'}, value='xyX7TRj3NthraNT2fM1ApdgGjL9lH7Q1'),

 
    html.Div(id='city-input-container', className='city-inputs', children=[
        html.Div(className='input-group', children=[
            html.Label("Первый город:", className='label'),
            dcc.Input(id="namecity1", type="text", className='input-field'),
        ]),

        html.Div(className='input-group', children=[
            html.Label("Второй город:", className='label'),
            dcc.Input(id="namecity2", type="text", className='input-field'),
        ]),

        # Кнопка для добавления городов
        html.Button('Добавить город', id='add-city', n_clicks=0, className='add-city-button'),
        html.Div(id='intermediate-stops-container')
    ]),

    html.I('Прогноз погоды доступен на ближайшие 5 дней', className='info-text'),

    # кнопка сравнения
    html.Div(html.Button('Сравнить', id='submit-val', n_clicks=0, className='submit-button'), className='submit-container'),

    # Сравнение
    html.H3(id="weather-output", className='output-text'),

    html.Div(className='graphs-container', children=[
        dcc.Graph(id="temp-graph", className='graph'),
        dcc.Graph(id="humidity-graph", className='graph'),
    ]),

    html.Div(className='graphs-container', children=[
        dcc.Graph(id="wind-graph", className='graph'),
        dcc.Graph(id="rain-graph", className='graph'),
    ]),

    html.I('GRAFICS', className='info-text'),

    html.H3('Прогноз погоды', className='forecast-title'),

    # Графики прогноза по дням для всех городов
    html.Div(id='forecast-graphs-container', className='forecast-graphs'),

    html.H3('Карта маршрута', className='map-title'),

    html.Div(id='map-container', className='map-container'),

    # число городов
    dcc.Store(id='num-stops', data=0)
])

# Callback для добавления городов
@app.callback(
    Output('intermediate-stops-container', 'children'),
    Output('num-stops', 'data'),
    Input('add-city', 'n_clicks'),
    State('num-stops', 'data')
)
def add_stop_fields(n_clicks, num_stops):
    if n_clicks == 0:
        return None, 0
    stops = num_stops + 1
    stop_fields = [
        html.Div([
            html.Label(f"Промежуточный пункт назначения {i + 1}:"),
            dcc.Input(id={'type': 'namecity', 'index': i}, type="text", placeholder=f"Город {i + 1}"),
        ], style={'margin-bottom': '20px'}) for i in range(stops)
    ]
    return stop_fields, stops



@app.callback(
    [
        Output('weather-output', 'children'),
        Output('temp-graph', 'figure'),
        Output('humidity-graph', 'figure'),
        Output('wind-graph', 'figure'),
        Output('rain-graph', 'figure'),
        Output('forecast-graphs-container', 'children'),
    ],
    Input('submit-val', 'n_clicks'),
    [
        State('namecity1', 'value'),
        State('namecity2', 'value'),
        State({'type': 'namecity', 'index': ALL}, 'value'),
        State('api_key', 'value'),
    ]
)
def update_output(n_clicks, namecity1, namecity2, intermediate_cities, api_key):
    if n_clicks == 0 or not api_key:
        return "", {}, {}, {}, {}, ""

    all_cities = [namecity1] + intermediate_cities + [namecity2]
    weather_data = []

    for city in all_cities:
        try:
            location_key, localized_name = get_location_key_name(api_key, city)
            conditions = get_conditions_by_key(api_key, location_key)
            weather_data.append({
                'City': localized_name,
                'Temperature': conditions['temperature'],
                'Humidity': conditions['humidity'],
                'Wind Speed': conditions['wind_speed'],
                'Rain Probability': conditions['precipitation_probability']
            })
        except Exception as e:
            return f"Ошибка для города {city}: {str(e)}", {}, {}, {}, {}, ""

    df = pd.DataFrame(weather_data)

    # Создание графиков с указанными цветами
    temp_fig = px.bar(df, x='City', y='Temperature', title="Температура (°C)", color_discrete_sequence=['#d5006d'])
    humidity_fig = px.bar(df, x='City', y='Humidity', title="Влажность (%)", color_discrete_sequence=['#ab47bc'])
    wind_fig = px.bar(df, x='City', y='Wind Speed', title="Скорость ветра (км/ч)", color_discrete_sequence=['#6200ea'])
    rain_fig = px.bar(df, x='City', y='Rain Probability', title="Вероятность осадков (%)", color_discrete_sequence=['#9c27b0'])

    output_text = f"Сравнение погоды для: {' - '.join([data['City'] for data in weather_data])}"

    forecast_data = []

    for city in all_cities:
        try:
            location_key, localized_name = get_location_key_name(api_key, city)
            city_forecast = get_forecast(api_key, location_key, days=5)
            for day in city_forecast:
                day['city'] = localized_name
            forecast_data.extend(city_forecast)
        except Exception as e:
            return [html.Div(f"Ошибка для города {city}: {str(e)}")]

    df = pd.DataFrame(forecast_data)
    try:
        # Построение графиков для каждого параметра
        graphs = []
        graphs.append(dcc.Graph(
            figure=px.line(df, x='date', y='max_temp', color='city', title="Максимальная температура в ближайшие 5 дней (°C)")
        ))
        graphs.append(dcc.Graph(
            figure=px.line(df, x='date', y='min_temp', color='city', title="Минимальная температура в ближайшие 5 днейм (°C)")
        ))
        graphs.append(dcc.Graph(
            figure=px.line(df, x='date', y='precipitation_probability', color='city', title="Вероятность осадков в ближайшие 5 дней (%)")
        ))
        graphs.append(dcc.Graph(
            figure=px.line(df, x='date', y='wind_speed', color='city', title="Скорость ветра в ближайшие 5 дней (м/с)")
        ))
    except Exception as e:
        return [html.Div(f"Ошибка для города {city}: {str(e)}")]

    return output_text, temp_fig, humidity_fig, wind_fig, rain_fig, graphs



@app.callback(
    Output('map-container', 'children'),
    Input('submit-val', 'n_clicks'),
    [
        State('namecity1', 'value'),
        State('namecity2', 'value'),
        State({'type': 'namecity', 'index': ALL}, 'value'),
        State('api_key', 'value')
    ]
)
def update_map(n_clicks, start_city, end_city, intermediate_cities, api_key):
    if n_clicks == 0:
        return []

    all_cities = [start_city] + intermediate_cities + [end_city]
    map_center = (55.751244, 37.618423)  # Центр в Москве по умолчанию
    m = folium.Map(location=map_center, zoom_start=5)

    # Парсинг каждого города, добавление прогноза
    for city in all_cities:
        try:
            location_key, localized_name = get_location_key_name(api_key, city)
            city_forecast = get_forecast(api_key, location_key, days=5)
            city_coord = get_location_key_geoposition(api_key, location_key)
            coordinates = (float(city_coord[0]), float(city_coord[1]))

            # Всплывающее окно
            forecast_html = "<h4>Прогноз погоды</h4>"
            for day in city_forecast:
                forecast_html += f"<b>{day['date']}</b><br>"
                forecast_html += f"Максимальная температура: {day['max_temp']} °C<br>"
                forecast_html += f"Минимальная температура: {day['min_temp']} °C<br>"
                forecast_html += f"Вероятность осадков: {day['precipitation_probability']}%<br>"
                forecast_html += f"Скорость ветра: {day['wind_speed']} км/ч<br><br>"

            iframe = IFrame(forecast_html, width=200, height=200)
            popup = folium.Popup(iframe, max_width=200)

            # Добавление маркера на карте
            folium.Marker(
                location=coordinates,
                popup=popup,
                tooltip=localized_name
            ).add_to(m)

        except Exception as e:
            raise
            return [html.Div(f"Ошибка для города {city}: {str(e)}")]

    map_html = m._repr_html_()

    return html.Iframe(srcDoc=map_html, width="100%", height="500px")

if __name__ == '__main__':
    app.run_server(debug=True)
