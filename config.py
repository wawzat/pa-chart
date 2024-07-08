#User defined variables
connection_url = "http://192.168.20.36/json"
data_file_name = "sensor_data.csv"
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
# Include the current EPA Aqi text on the plot
include_aqi_text = True
# Include an average line on the plot
include_average_line = True
# Dimensions of the plot jpg in pixels
width_pixels = 800
height_pixels = 600
dpi = 100
# Chart text
chart_title = 'Particulate Sensor Data'
y_axis_label = 'EPA PM 2.5 AQI'
x_axis_label = ' '
# Chart color mode: 'light' or 'dark'
chart_color_mode = 'light'
# Print values to console
debug_print = True