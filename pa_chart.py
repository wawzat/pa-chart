# Logs readings from a PurpleAir sensor on local LAN, converts to "EPA AQI", saves the logto a csv file
#  and plots the data as a .jpg file.
# James S. Lucas - 20240707
import json
import csv
import requests
from time import sleep
from datetime import datetime, timedelta
import sys
import logging
from conversions import AQI, EPA
import config
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Create an error logger
logger = logging.getLogger(__name__)  
# set log level
logger.setLevel(logging.WARNING)
# define file handler and set formatter
file_handler = logging.FileHandler('log_exception_pa_chart.log')
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
# add file handler to logger
logger.addHandler(file_handler)


def retry(max_attempts=3, delay=2, escalation=10, exception=(Exception,)):
    """
    A decorator function that retries a function call a specified number of times if it raises a specified exception.

    Args:
        max_attempts (int): The maximum number of attempts to retry the function call.
        delay (int): The initial delay in seconds before the first retry.
        escalation (int): The amount of time in seconds to increase the delay by for each subsequent retry.
        exception (tuple): A tuple of exceptions to catch and retry on.

    Returns:
        The decorated function.

    Raises:
        The same exception that the decorated function raises if the maximum number of attempts is reached.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exception as e:
                    adjusted_delay = delay + escalation * attempts
                    attempts += 1
                    logger.exception(f'Error in {func.__name__}(): attempt #{attempts} of {max_attempts}')
                    if attempts < max_attempts:
                        sleep(adjusted_delay)
            logger.exception(f'Error in {func.__name__}: max of {max_attempts} attempts reached')
            sys.exit()
        return wrapper
    return decorator


@retry(max_attempts=4, delay=90, escalation=90, exception=(requests.exceptions.RequestException, requests.exceptions.ConnectionError))
def get_live_reading(connection_url):
    """
    This function gets the live sensor reading from a PurpleAir sensor.

    Parameters:
    connection_url (str): The URL of the PurpleAir sensor.

    Returns:
    Response: A Response object containing the live sensor reading from the PurpleAir sensor.
    conn_success (bool): A flag indicating if the connection was successful.
    """
    live_flag = "?live=true"
    live_connection_string = connection_url + live_flag
    live_response = requests.get(live_connection_string)
    if live_response.ok:
        conn_success = True
    else:
        conn_success = False
    return live_response, conn_success


def write_data(pm25_epa_aqi, conn_success, filename='sensor_data.csv'):
    """
    This function writes data to a csv file with a consistent datetime format.

    Args:
        pm25_epa_aqi (float): The live PM2.5 value.
        conn_success (bool): A flag indicating if the connection to the sensor was successful.
        filename (str): The name of the CSV file.

    Returns:
        None
    """
    if not conn_success:
        logger.error('write_data() connection error')
        sleep(2)
    # Check if the file is empty to decide on writing the header
    try:
        with open(filename, 'r', newline='') as file:
            first_char = file.read(1)
            file_empty = not bool(first_char)
    except FileNotFoundError:
        file_empty = True
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if file_empty:
            # Write the header if the file is empty
            writer.writerow(['datetime', 'pm25_epa_aqi'])
        # Format the datetime object into a string with a specific format
        formatted_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        writer.writerow([formatted_datetime, pm25_epa_aqi])


def truncate_earliest_data(filename, days_to_log=14):
    """
    Truncates the earliest data in a CSV file based on a specified number of days.

    Args:
        filename (str): The path to the CSV file.
        days_to_log (int, optional): The number of days to keep in the file. Defaults to 14.

    Returns:
        None

    Raises:
        FileNotFoundError: If the specified file does not exist.

    """
    with open(filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    for row in data:
        row['datetime'] = datetime.strptime(row['datetime'], '%Y-%m-%dT%H:%M:%S')
    latest_date = max(row['datetime'] for row in data)
    cutoff_date = latest_date - timedelta(days=days_to_log)
    filtered_data = [row for row in data if row['datetime'] >= cutoff_date]
    if len(filtered_data) == len(data):
        # No data needs to be truncated, exit the function
        return
    # Convert datetime objects back to strings for CSV output
    for row in filtered_data:
        row['datetime'] = row['datetime'].strftime('%Y-%m-%dT%H:%M:%S')
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(filtered_data)


def process_sensor_reading(live_response):
    """
    Process the sensor reading from the live response.

    Args:
        live_response (Response): The live response object.

    Returns:
        tuple: A tuple containing the processed PM2.5 reading, humidity reading, and connection success status.

    Raises:
        None
    """
    if live_response.ok:
        conn_success = True
        live_sensor_reading = json.loads(live_response.text)
        pm2_5_cf1 = (live_sensor_reading['pm2_5_cf_1'] + live_sensor_reading['pm2_5_cf_1_b']) / 2
        humidity = (live_sensor_reading['current_humidity']) + 4
    else:
        logger.error('Error: status code not ok')
        conn_success = False
    return pm2_5_cf1, humidity, conn_success


def plot_csv_to_jpg(filename, width_pixels=800, height_pixels=600, dpi=100, include_aqi_text=True, chart_title='Particulate Sensor Data', y_axis_label='EPA PM 2.5 AQI', x_axis_label=' '):
    """
    Plot the data from a CSV file and save it as a JPG image.

    Parameters:
    - filename (str): The path to the CSV file.
    - width_pixels (int): The width of the output image in pixels (default: 800).
    - height_pixels (int): The height of the output image in pixels (default: 600).
    - dpi (int): The resolution of the output image in dots per inch (default: 100).
    - include_aqi_text (bool): Whether to include the AQI text on the chart (default: True).
    - chart_title (str): The title of the chart (default: 'Particulate Sensor Data').
    - y_axis_label (str): The label for the y-axis (default: 'EPA PM 2.5 AQI').
    - x_axis_label (str): The label for the x-axis (default: ' ').

    Returns:
    None
    """
    # Calculate figure size in inches
    width_inches = width_pixels / dpi
    height_inches = height_pixels / dpi
    # Set figure size
    plt.figure(figsize=(width_inches, height_inches))
    # Read the CSV file
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        dates = []
        values = []
        for row in reader:
            try:
                # Attempt to parse the datetime with the expected format
                parsed_date = datetime.strptime(row[0],'%Y-%m-%dT%H:%M:%S')
            except ValueError:
                # If parsing fails, print the problematic datetime string and skip this row
                print(f"Could not parse datetime: {row[0]}")
                continue
            dates.append(parsed_date)
            values.append(float(row[1]))
    # Plot the data
    plt.plot(dates, values)
    ax = plt.gca()  # Get current axes
    ax.set_xlim(min(dates), max(dates))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xlabel(x_axis_label)
    plt.xticks(rotation=45)
    plt.yticks(range(0, 201, 50))
    ax.fill_between(ax.get_xlim(), 0, 50, color='palegreen', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 50, 100, color='palegoldenrod', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 100, 150, color='peachpuff', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 150, 200, color='lightcoral', alpha=0.5)
    plt.ylabel(y_axis_label)
    plt.title(chart_title, pad=20)
    if include_aqi_text:
        # First part: "EPA AQI as of DATE" with font size 8 and not bold'%Y-%m-%dT%H:%M:%S'
        plt.text(0.94, 0.05, 'EPA AQI as of ' + dates[-1].strftime('%m/%d/%Y %H:%M') + ': ', fontsize=8, ha='right', va='bottom', transform=ax.transAxes)
        # Second part: "value" with font size 12 and bold
        plt.text(0.99, 0.05, str(int(values[-1])), fontsize=12, fontweight='bold', ha='right', va='bottom', transform=ax.transAxes)
    plt.savefig('sensor_data.jpg', dpi=dpi, bbox_inches='tight')
    plt.close()


try:
    log_delay_loop_start = plot_delay_loop_start = truncate_delay_loop_start = datetime.now()
    # Loop forever
    while 1:
        if config.logging_start_hour < datetime.now().hour <= config.logging_finish_hour:
            elapsed_time = (datetime.now() - log_delay_loop_start).total_seconds()
            if elapsed_time > config.logging_interval:
                live_response, conn_success = get_live_reading(config.connection_url)
                pm2_5_cf1, humidity, conn_success = process_sensor_reading(live_response)
                if conn_success:
                    pm2_5_epa = EPA.calculate(humidity, pm2_5_cf1)
                    pm2_5_epa_aqi = AQI.calculate(pm2_5_epa)
                    if config.debug_print:
                        print(f'humidity: {humidity}, pm2_5_cf1: {pm2_5_cf1}, pm2_5_epa: {pm2_5_epa}, pm2_5_epa_aqi: {pm2_5_epa_aqi}')
                    write_data(pm2_5_epa_aqi, conn_success, config.data_file_name)
                log_delay_loop_start = datetime.now()
            elapsed_time = (datetime.now() - plot_delay_loop_start).total_seconds()
            if elapsed_time > config.plotting_interval:
                plot_csv_to_jpg(config.data_file_name, config.width_pixels, config.height_pixels, config.dpi, config.include_aqi_text, config.chart_title, config.y_axis_label, config.x_axis_label)
                plot_delay_loop_start = datetime.now()
            elapsed_time = (datetime.now() - truncate_delay_loop_start).total_seconds() / 3600
            if elapsed_time > config.truncate_interval:
                truncate_earliest_data(config.data_file_name, config.days_to_log)
                truncate_delay_loop_start = datetime.now()
        sleep(1)

except KeyboardInterrupt:
    sys.exit()