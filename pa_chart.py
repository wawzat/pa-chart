# Logs readings from a PurpleAir sensor on local LAN, converts to "EPA AQI", saves the log and plots it as a .jpg file.
# James S. Lucas - 20240706
import json
import csv
import requests
from time import sleep
from datetime import datetime, timedelta
import sys
import logging
from conversions import AQI, EPA
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


#User defined variables
connection_url = "http://192.168.20.36/json"
data_file_name = "sensor_data.csv"
#data_file_name = "test_data.csv"
logging_interval = 120 # seconds
days_to_log = 14
plotting_interval = 240 # seconds
logging_start_hour = 0
logging_finish_hour = 24


# Creates a logger
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


def write_data(Ipm25_live, conn_success, filename='sensor_data.csv'):
    """
    This function writes data to a csv file with a consistent datetime format.

    Args:
        Ipm25_live (float): The live PM2.5 value.
        conn_success (bool): A flag indicating if the connection to the sensor was successful.
        filename (str): The name of the CSV file.

    Returns:
        None
    """
    if not conn_success:
        logger.error('write_data() connection error')
        sleep(2)
    print(Ipm25_live)
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
            writer.writerow(['datetime', 'Ipm25_live'])
        # Format the datetime object into a string with a specific format
        formatted_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        writer.writerow([formatted_datetime, Ipm25_live])


def truncate_earliest_data(filename, days_to_log=14):
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


def plot_csv_to_jpg(filename):
    """
    This function opens a CSV file and plots the data to a JPG file.

    Args:
        filename (str): The name of the CSV file.

    Returns:
        None
    """
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
    # Simplify the x-axis labels
    ax = plt.gca()  # Get current axes
    ax.set_xlim(min(dates), max(dates))
    # Adjust the major locator and formatter based on the range of your data
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xlabel('Datetime')
    plt.xticks(rotation=45)  # Rotate labels for better legibility
    #plt.tight_layout()  # Adjust layout to make room for the rotated x-axis labels
     # Set vertical axis ticks from 0 to 200 in increments of 50
    plt.yticks(range(0, 201, 50))
    # Plot colored bands
    ax.fill_between(ax.get_xlim(), 0, 50, color='palegreen', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 50, 100, color='palegoldenrod', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 100, 150, color='peachpuff', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 150, 200, color='lightcoral', alpha=0.5)
    plt.ylabel('Ipm25_live')
    plt.title('Sensor Data', pad=20)
    plt.xticks(rotation=45)
    plt.savefig('sensor_data.jpg', bbox_inches='tight')
    #plt.subplots_adjust(top=1.5, bottom=0.4, left=0.5, right=0.95)
    plt.close()


@retry(max_attempts=4, delay=90, escalation=90, exception=(requests.exceptions.RequestException, requests.exceptions.ConnectionError))
def get_live_reading(connection_url):
    """
    This function gets the live sensor reading from a PurpleAir sensor.

    Parameters:
    connection_url (str): The URL of the PurpleAir sensor.

    Returns:
    Response: A Response object containing the live sensor reading from the PurpleAir sensor.
    """
    live_flag = "?live=true"
    live_connection_string = connection_url + live_flag
    live_response = requests.get(live_connection_string)
    if live_response.ok:
        conn_success = True
    else:
        conn_success = False
    return live_response, conn_success


def process_sensor_reading(live_response):
    """
    This function processes sensor readings from a PurpleAir sensor.

    Parameters:
    connection_url (str): The URL of the PurpleAir sensor.

    Returns:
    tuple: A tuple containing the average PM2.5 reading, live PM2.5 reading, confidence level, and connection success status.
    """
    if live_response.ok:
        conn_success = True
        live_sensor_reading = json.loads(live_response.text)
        pm2_5_reading_live = (live_sensor_reading['pm2_5_atm'] + live_sensor_reading['pm2_5_atm_b']) / 2
        humidity_live = (live_sensor_reading['current_humidity'])
    else:
        logger.error('Error: status code not ok')
        conn_success = False
    return pm2_5_reading_live, humidity_live, conn_success


try:
    # Loop forever
    delay_loop_start = datetime.now()
    while 1:
        if logging_start_hour < datetime.now().hour <= logging_finish_hour:
            live_response, conn_success = get_live_reading(connection_url)
            pm2_5_live, humidity_live, conn_success = process_sensor_reading(live_response)
            if conn_success:
                Ipm25_live = AQI.calculate(EPA.calculate(pm2_5_live, humidity_live))
            sleep(logging_interval)
        write_data(Ipm25_live, conn_success, data_file_name)
        truncate_earliest_data(data_file_name, days_to_log)
        elapsed_time = datetime.now() - delay_loop_start
        if elapsed_time.seconds > plotting_interval:
            plot_csv_to_jpg(data_file_name)
            delay_loop_start = datetime.now()

except KeyboardInterrupt:
    sys.exit()