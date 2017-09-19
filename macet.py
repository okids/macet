import requests
from datetime import datetime, timedelta
import time
from functools import wraps
import psycopg2

def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except IndexError as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry

@retry(Exception, tries=4)
def get_arrival(time, key):
    return requests.get("https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&departure_time={}&origins=Mangunjaya,+Bekasi,+West+Java,+Indonesia&destinations=Ministry+of+Administrative+and+Bureaucratic+Reform+of+the+Republic+of+Indonesia,+Jl.+Jenderal+Sudirman+Kav.+69,+RT.8%2FRW.2,+Senayan,+Kebayoran+Baru,+RT.8%2FRW.2,+Senayan,+Kby.+Baru,+Kota+Jakarta+Selatan,+Daerah+Khusus+Ibukota+Jakarta+12190,+Indonesia&key={}".format(time, key)).json()
    
@retry(Exception, tries=4) 
def get_departure(time, key):
    return requests.get("https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&departure_time={}&destinations=Mangunjaya,+Bekasi,+West+Java,+Indonesia&origins=Ministry+of+Administrative+and+Bureaucratic+Reform+of+the+Republic+of+Indonesia,+Jl.+Jenderal+Sudirman+Kav.+69,+RT.8%2FRW.2,+Senayan,+Kebayoran+Baru,+RT.8%2FRW.2,+Senayan,+Kby.+Baru,+Kota+Jakarta+Selatan,+Daerah+Khusus+Ibukota+Jakarta+12190,+Indonesia&key={}".format(time, key)).json()
 
def get_duration_in_traffic(google_result):
	return google_result['rows'][0]['elements'][0]['duration_in_traffic']['text']

def get_hour(google_result):
	minute = ' min'
	if ' mins' in google_result:
		minute = ' mins'

	hour = ' hour'
	if ' hours' in google_result:
		hour = ' hours'
	return google_result.split(hour)[0].split(minute)[0]

def get_minutes(google_result):
	minute = ' min'
	if ' mins' in google_result:
		minute = ' mins'

	hour = ' hour'
	if ' hours' in google_result:
		hour = ' hours'
	return google_result.split(minute)[0].split(hour)[1]

GOOGLE_API_KEY = "YOUR GOOGLE API KEY"
dt1 = datetime.now()
r1 = get_departure(int(dt1.timestamp()), GOOGLE_API_KEY)
dt2 = datetime.now()
r2 = get_arrival(int(dt2.timestamp()), GOOGLE_API_KEY)

try:
    dur_dep = get_duration_in_traffic(r1)
    dur_arr = get_duration_in_traffic(r2)
except:
    print("out because API")
    pass

hour_dep = get_hour(dur_dep)
hour_arr = get_hour(dur_arr)
try:
    min_dep = get_minutes(dur_dep)
except:
    min_dep = 0

try:
    min_arr = get_minutes(dur_arr)
except:
    min_arr = 0
dur_dep = int(hour_dep) * 60 + int(min_dep)
dur_arr = int(hour_arr) * 60 + int(min_arr)


conn = psycopg2.connect(
    host='0.0.0.0',
    port=5432)

cur = conn.cursor()

try:
    cur.execute("INSERT INTO macet (time_save, is_departure, duration) VALUES (%s, %s, %s)", (dt1, True, dur_dep))
    cur.execute("INSERT INTO macet (time_save, is_departure, duration) VALUES (%s, %s, %s)", (dt2, False, dur_arr))
except Exception as e:
    print("out because db")
    print(e)
    pass

cur.close()
conn.commit()


