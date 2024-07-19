#User defined variables
connection_url = "http://192.168.20.36/json"
# Data paths and file names
# Use empty stings ('') to store the data and images in the same directory as the script, comment out the following lines
#  to use different paths and file names below
data_storage_path = '' 
image_storage_path = '' 
linux_drive = ''
windows_drive = ''
# To use different paths and file names uncomment the following lines and set the correct paths and file names 
#linux_drive = '/mnt/d'
#windows_drive = 'D:/'
#data_storage_path = '1Data/pa_chart'
#image_storage_path = '1Data/pa_chart'
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
# AQI Band Colors
aqi_band_colors = {50: 'palegreen', 100: 'Yellow', 150: 'Orange', 200: 'Red', 300: 'Purple', 500: 'Maroon'}
aqi_band_alphas = {50: 0.3, 100: 0.25, 150: 0.25, 200: 0.3, 300: 0.3, 500: 0.3}
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
# Chart color mode: 'light' or 'dark'
chart_color_mode = 'light'
# Print values to console
debug_print = True