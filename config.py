#User defined variables
connection_url = "http://192.168.20.36/json"
data_file_name = "sensor_data.csv"
use_epa_conversion = False
#data_file_name = "test_data.csv"
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
aqi_band_alphas = {50: 0.3, 100: 0.25, 150: 0.4, 200: 0.3, 300: 0.3, 500: 0.3}
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