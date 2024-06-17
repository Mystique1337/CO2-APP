from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from PIL import Image
import io
import base64

app = Flask(__name__)
CORS(app)

# Load the dataset
file_path = 'stationary_df.csv'
data = pd.read_csv(file_path)
data.drop('Unnamed: 0', axis=1, inplace=True)

# Convert 'date_surveyed' to datetime and set as index
data['date_surveyed'] = pd.to_datetime(data['date_surveyed'],
                                       format='%Y-%m-%d')
data.set_index('date_surveyed', inplace=True)

# Rename column for clarity
data.rename(
    columns={'daily_co2_emmission_ppm_stationary': 'daily_co2_emmission_ppm'},
    inplace=True)
# Ensure the CO2 emission column is numeric
data['daily_co2_emmission_ppm'] = pd.to_numeric(
    data['daily_co2_emmission_ppm'], errors='coerce')


def resample_data(df, granularity):
    # Only keep numeric columns for resampling
    numeric_cols = df.select_dtypes(include=[np.number])
    return numeric_cols.resample(granularity[0].upper()).mean()


def get_image_as_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


@app.route('/')
def index():
    locations = data['Area_Surveyed'].unique()
    return render_template('index.html', locations=locations)


@app.route('/data', methods=['POST'])
def get_data():
    granularity = request.form['granularity']
    selected_location = request.form['location']

    location_data = data[data['Area_Surveyed'] == selected_location]
    location_data = resample_data(location_data, granularity)

    if not location_data.empty:
        latest_date = location_data.index.max()
        current_co2 = location_data.iloc[-1]['daily_co2_emmission_ppm']
        latest_reading = {
            'date': latest_date.strftime('%Y-%m-%d'),
            'co2': f"{current_co2:.2f}"
        }
    else:
        latest_reading = {'date': None, 'co2': None}

    # Create CO2 emission trends plot
    fig = px.line(location_data,
                  y='daily_co2_emmission_ppm',
                  title='Trend Over Time',
                  labels={'value': 'CO2 Emission (ppm)'})
    graph_html = fig.to_html(full_html=False)

    # Descriptive statistics
    stats_html = location_data.describe().to_html()

    # Forecasting
    forecast_html = ''
    if len(location_data) > 12:
        ets_model = ETSModel(location_data['daily_co2_emmission_ppm'].dropna(),
                             error='add',
                             trend='add',
                             seasonal='add',
                             seasonal_periods=12)
        ets_fit = ets_model.fit()
        forecast_values = ets_fit.forecast(steps=30)
        forecast_df = pd.DataFrame({
            'Forecast': forecast_values,
            'Date': forecast_values.index
        })
        forecast_df.set_index('Date', inplace=True)

        forecast_fig = go.Figure()
        forecast_fig.add_trace(
            go.Scatter(x=location_data.index,
                       y=location_data['daily_co2_emmission_ppm'],
                       mode='lines',
                       name='Observed'))
        forecast_fig.add_trace(
            go.Scatter(x=forecast_df.index,
                       y=forecast_df['Forecast'],
                       mode='lines',
                       name='Forecast',
                       line=dict(color='red')))
        forecast_fig.update_layout(title='Forecast',
                                   xaxis_title='Date',
                                   yaxis_title='CO2 Emission (ppm)')
        forecast_html = forecast_fig.to_html(full_html=False)

    # Image handling
    image_path = f'static/images/{selected_location}.png'  # assuming the file name is the exact location name
    try:
        image_base64 = get_image_as_base64(image_path)
    except FileNotFoundError:
        image_base64 = None

    return jsonify({
        'latest_reading': latest_reading,
        'graph_html': graph_html,
        'stats_html': stats_html,
        'forecast_html': forecast_html,
        'image_base64': image_base64,
        'location': selected_location
    })


@app.route('/download-forecast', methods=['POST'])
def download_forecast():
    selected_location = request.form['location']

    location_data = data[data['Area_Surveyed'] == selected_location]
    location_data = resample_data(location_data, 'M')

    if len(location_data) > 12:
        ets_model = ETSModel(location_data['daily_co2_emmission_ppm'].dropna(),
                             error='add',
                             trend='add',
                             seasonal='add',
                             seasonal_periods=12)
        ets_fit = ets_model.fit()
        forecast_values = ets_fit.forecast(steps=30)
        forecast_df = pd.DataFrame({
            'Forecast': forecast_values,
            'Date': forecast_values.index
        })
        forecast_df.set_index('Date', inplace=True)

        buffer = io.StringIO()
        forecast_df.to_csv(buffer)
        buffer.seek(0)

        return send_file(buffer,
                         as_attachment=True,
                         download_name='forecasted_data.csv',
                         mimetype='text/csv')

    return "Not enough data for forecasting", 400


if __name__ == '__main__':
    app.run(debug=True)
