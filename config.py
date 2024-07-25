#User defined variables
connection_url = "http://192.168.20.36/json"
# Data paths and file names
# If default_storage_path = True, the data and image files will be stored in the same directory as the script.
use_default_storage_paths = True
# If default_storage_path = False, the data and image files will be stored in the custom paths below.
custom_linux_drive = '/mnt/d'
custom_windows_drive = 'D:/'
custom_data_storage_path = '1Data/pa_chart'
custom_image_storage_path = '1Data/pa_chart'
#
# Data and image file names
data_file_name = "sensor_data.csv"
image_file_name = "sensor_data.jpg"
# Conversion
use_epa_conversion = False
# How often to get new data from the sensor in seconds
logging_interval = 120 # seconds
# How many days to keep in the log file and plot.
days_to_log = 14
# How often to plot the data in seconds
plotting_interval = 240 # seconds
# Log data between these hours
logging_start_hour = 0
logging_finish_hour = 24
# How often to truncate the earliest data in the log file in hours
truncate_interval = 24 # hours
# Set y-axis limit for the plot to 50, 100, 150, 200, 300, 500 or 'auto'
y_limit = 'auto'
# Chart color mode: 'light', 'dark' or 'greyscale
chart_color_mode = 'light'
# AQI Band Colors
aqi_band_colors = {50: 'palegreen', 100: 'Yellow', 150: 'Orange', 200: 'Red', 250: 'Red', 300: 'Purple', 350: 'Purple', 400: 'Purple', 450: 'Purple', 500: 'Maroon'}
# AQI Band Alphas for color modes 'light'
aqi_band_color_alphas = {50: 0.3, 100: 0.25, 150: 0.25, 200: 0.3, 250: 0.4, 300: 0.3, 350: 0.4, 400: 0.5, 450: 0.6, 500: 0.3}
# AQI Band Alphas for color modes 'dark'
aqi_band_dark_color_alphas = {50: 0.4, 100: 0.4, 150: 0.4, 200: 0.4, 250: 0.3, 300: 0.6, 350: 0.5, 400: 0.4, 450: 0.3, 500: 0.3}
# AQI Band Greyscales
aqi_band_greyscales = {50: 'black', 100: 'black', 150: 'black', 200: 'black', 250: 'black', 300: 'black', 350: 'black', 400: 'black', 450: 'black', 500: 'black'}
aqi_band_greyscale_alphas = {50: 0.1, 100: 0.2, 150: 0.3, 200: 0.4, 250: 0.5, 300: 0.6, 350: 0.7, 400: 0.8, 450: 0.9, 500: 1.0}
# Plot line colors
default_line_color = '#1f77b4'
greyscale_line_color = 'white'
# Include the current EPA AQI text on the plot
include_aqi_text = True
# Include an average line on the plot
include_average_line = True
# Dimensions of the plot jpg in pixels
width_pixels = 800
height_pixels = 600
dpi = 100
# Chart text
chart_title = 'Particulate Sensor Data'
x_axis_label = ' '
epa_conversion_y_axis_label = 'EPA PM 2.5 AQI w/ EPA Conversion'
no_epa_conversion_y_axis_label = 'EPA PM 2.5 AQI'
# Print values to console
debug_print = True