import requests
from datetime import datetime

DOWNLOAD_URL = 'https://raw.githubusercontent.com/makebit/bonds-data/refs/heads/main/data_end_of_day.csv'

# Download data from a URL and save it to a file
def download_file(url, filename, extension):
    response = requests.get(url)
    with open(filename + '.' + extension, 'wb') as file:
        file.write(response.content)
    # Save the file with date-time backup
    with open(filename + '_' + datetime.now().strftime("%Y%m%d") + '.' + extension, 'wb') as file:
        file.write(response.content)

download_file(DOWNLOAD_URL, 'data/data', 'csv')