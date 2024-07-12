# Logs readings from a PurpleAir sensor on local LAN, saves the log to a csv file
#  and plots the data as a .jpg file.
# James S. Lucas - 20240711
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


@retry(max_attempts=8, delay=90, escalation=160, exception=(requests.exceptions.RequestException, requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.Timeout))
def get_live_reading(connection_url: str) -> tuple[requests.models.Response, bool]:
    """
    This function gets the live sensor reading from a PurpleAir sensor.

    Parameters:
    connection_url (str): The URL of the PurpleAir sensor.

    Returns:
    Response: A Response object containing the live sensor readings from the PurpleAir sensor.
    conn_success (bool): A flag indicating if the connection was successful.
    """
    live_flag = "?live=true"
    live_connection_string = connection_url + live_flag
    live_response = requests.get(live_connection_string)
    if live_response.ok:
        conn_success = True
    else:
        conn_success = False
        logger.error('get_live_reading() connection error, live response not 200 ok')
    return live_response, conn_success


def write_data(pm25_epa_aqi: float, conn_success: bool, filename: str = 'sensor_data.csv') -> None:
    """
    This function writes data to a csv file.

    Args:
        pm25_epa_aqi (float): The live PM2.5 value.
        conn_success (bool): A flag indicating if the connection to the sensor was successful.
        filename (str): The name of the CSV file.

    Returns:
        None
    """
    if not conn_success:
        logger.error('write_data() connection error')
        return
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


def truncate_earliest_data(filename: str, days_to_log: int = 14) -> None:
    """
    Truncates the earliest data in a CSV file based on a specified number of days.

    Args:
        filename (str): The path to the CSV file.
        days_to_log (int, optional): The number of days to keep in the file. Defaults to 14.

    Returns:
        None

    """
    try:
        with open(filename, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            data = list(reader)
    except FileNotFoundError:
        # If the file is not found, just return without doing anything
        logger.error(f"truncate_earliest_data() File not found: {filename}")
        return
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


def process_sensor_reading(live_response: str) -> tuple[float, float, float]:
    """
    Process the sensor reading from the live response.

    Args:
        live_response (str): The live response from the sensor.

    Returns:
            - pm25_cf1 (float): The average PM2.5 CF1 value.
            - pm25_atm (float): The average PM2.5 ATM value.
            - humidity (float): The adjusted humidity value.
    """

    live_sensor_reading = json.loads(live_response.text)
    pm25_cf1 = (live_sensor_reading['pm2_5_cf_1'] + live_sensor_reading['pm2_5_cf_1_b']) / 2
    pm25_atm = (live_sensor_reading['pm2_5_atm'] + live_sensor_reading['pm2_5_atm_b']) / 2
    humidity = (live_sensor_reading['current_humidity']) + 4
    return pm25_cf1, pm25_atm, humidity


def plot_csv_to_jpg(filename: str, width_pixels: int = 800, height_pixels: int = 600,
                    dpi: int = 100, include_aqi_text: bool = True,
                    include_average_line: bool = True,
                    chart_title: str = 'Particulate Sensor Data',
                    x_axis_label: str = ' ',
                    chart_color_mode: str = 'light',
                    use_epa_conversion: bool = False) -> None:
    """
    Plots data from a CSV file and saves the plot as a JPG image.

    Args:
        filename (str): The path to the CSV file.
        width_pixels (int, optional): The width of the plot in pixels. Defaults to 800.
        height_pixels (int, optional): The height of the plot in pixels. Defaults to 600.
        dpi (int, optional): The resolution of the plot in dots per inch. Defaults to 100.
        include_aqi_text (bool, optional): Whether to include the AQI text on the plot. Defaults to True.
        include_average_line (bool, optional): Whether to include the average line on the plot. Defaults to True.
        chart_title (str, optional): The title of the plot. Defaults to 'Particulate Sensor Data'.
        y_axis_label (str, optional): The label for the y-axis. Defaults to 'EPA PM 2.5 AQI'.
        x_axis_label (str, optional): The label for the x-axis. Defaults to ' '.
        chart_color_mode (str, optional): The color mode of the plot ('light' or 'dark'). Defaults to 'light'.

    Returns:
        None
    """
    if use_epa_conversion:
        y_axis_label = config.epa_conversion_y_axis_label
    else:
        y_axis_label = config.no_epa_conversion_y_axis_label
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
                logger.error(f"Could not parse datetime: {row[0]}")
                print(f"Could not parse datetime: {row[0]}")
                continue
            dates.append(parsed_date)
            values.append(float(row[1]))
    average = int(sum(values) / len(values))
    # Plot the data
    if chart_color_mode == 'dark':
        plt.style.use('dark_background')
    elif chart_color_mode == 'light':
        plt.style.use('default')
    plt.plot(dates, values)
    ax = plt.gca()  # Get current axes
    ax.set_xlim(min(dates), max(dates))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xlabel(x_axis_label)
    plt.xticks(rotation=45)
    plt.yticks(range(0, 201, 50))
    ax.fill_between(ax.get_xlim(), 0, 50, color='palegreen', alpha=0.5)
    ax.fill_between(ax.get_xlim(), 50, 100, color='palegoldenrod', alpha=0.6)
    ax.fill_between(ax.get_xlim(), 100, 150, color='orange', alpha=0.3)
    ax.fill_between(ax.get_xlim(), 150, 200, color='red', alpha=0.3)
    plt.ylabel(y_axis_label)
    plt.title(chart_title, pad=20, fontsize=12, fontweight='bold')
    if include_aqi_text:
        # First part: "EPA AQI as of DATE" with font size 8 and not bold'%Y-%m-%dT%H:%M:%S'
        plt.text(0.94, 0.05, 'EPA AQI as of ' + dates[-1].strftime('%m/%d/%Y %H:%M') + ': ', fontsize=8, ha='right', va='bottom', transform=ax.transAxes)
        # Second part: "value" with font size 12 and bold
        plt.text(0.99, 0.05, str(int(values[-1])), fontsize=12, fontweight='bold', ha='right', va='bottom', transform=ax.transAxes)
    if include_average_line:
        plt.axhline(y=average, color='grey', linestyle='--')
        # Get the x-axis limits to position the label on the right side of the plot horizontally
        xlim = ax.get_xlim()
        # Position the label on the right, slightly left to avoid being too close to the edge
        right_x = xlim[1] - (xlim[1] - xlim[0]) * 0.02  # Adjust the 0.02 as needed for your plot's scale
        # Position the label slightly above the average line
        plt.text(right_x, average + 0.5, f'{average}', ha='right', va='bottom', color='grey', fontsize=8)
    plt.savefig('sensor_data.jpg', dpi=dpi, bbox_inches='tight')
    plt.close()


def main() -> None:
    try:
        log_delay_loop_start = plot_delay_loop_start = truncate_delay_loop_start = datetime.now()
        # Loop forever
        while 1:
            if config.logging_start_hour < datetime.now().hour <= config.logging_finish_hour:
                elapsed_time = (datetime.now() - log_delay_loop_start).total_seconds()
                if elapsed_time > config.logging_interval:
                    live_response, conn_success = get_live_reading(config.connection_url)
                    pm25_cf1, pm25_atm, humidity = process_sensor_reading(live_response)
                    if conn_success:
                        if config.use_epa_conversion:
                            pm25 = EPA.calculate(humidity, pm25_cf1)
                        else:
                            pm25 = pm25_atm
                        pm25_epa_aqi = AQI.calculate(pm25)
                        if config.debug_print:
                            if config.use_epa_conversion:
                                pm25_txt = 'PM 2.5 w/ EPA Conversion'
                                pm25_aqi_txt = 'PM 2.5 EPA AQI w/ EPA Conversion'
                            else:
                                pm25_txt = 'PM 2.5 ATM'
                                pm25_aqi_txt = 'PM 2.5 EPA AQI'
                            print(f'Humidity: {humidity}, PM 2.5 cf1: {pm25_cf1}, PM 2.5 atm: {pm25_atm}, {pm25_txt}: {pm25}, {pm25_aqi_txt}: {pm25_epa_aqi}')
                        write_data(pm25_epa_aqi, conn_success, config.data_file_name)
                    log_delay_loop_start = datetime.now()
                elapsed_time = (datetime.now() - plot_delay_loop_start).total_seconds()
                if elapsed_time > config.plotting_interval:
                    plot_csv_to_jpg(
                                    config.data_file_name, 
                                    config.width_pixels, 
                                    config.height_pixels, 
                                    config.dpi, 
                                    config.include_aqi_text, 
                                    config.include_average_line, 
                                    config.chart_title, 
                                    config.x_axis_label, 
                                    config.chart_color_mode,
                                    config.use_epa_conversion
                                    )
                    plot_delay_loop_start = datetime.now()
                elapsed_time = (datetime.now() - truncate_delay_loop_start).total_seconds() / 3600
                if elapsed_time > config.truncate_interval:
                    truncate_earliest_data(config.data_file_name, config.days_to_log)
                    truncate_delay_loop_start = datetime.now()
            sleep(1)

    except KeyboardInterrupt:
        sys.exit()

if __name__ == '__main__':
    main()