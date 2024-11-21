import datetime

# timestamp stores time in seconds, 
# while datetime stores it in a specific format
def timestamp_as_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)