from datetime import datetime
from zoneinfo import ZoneInfo

def get_wib_time():
    return datetime.now(ZoneInfo("Asia/Jakarta"))