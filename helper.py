import re
from datetime import datetime, timedelta
import os

def isUrl(url):
  regex = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE)
  if url is not None and regex.search(url):
    return True
  return False


def isSpotify(url):
  return url.startswith("https://open.spotify.com") or url.startswith("open.spotify.com")

def formatDuration(length):
  m, s = divmod(length, 60)
  duration = f"{m:02d}:{s:02d}"

  return duration

def formatHelpString(function):
  message = ""
  for func in function:
    for i, opt in enumerate(func.commands):
      message += "**" + opt + "**"
      if i < len(func.commands)-1:
        message += " | "
    message += "\n"
    message += "*" + func.helpMessage + "*"
    message += "\n"
  
  return message

def timeDifference(target_time, second):
    target_time = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    if os.getenv("IS_DEVELOPMENT") == "0":
      current_time = current_time + timedelta(hours=7)
    time_difference = target_time - current_time
    return time_difference.total_seconds() < second

def formatDatetime(dateStr):
  return datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y %H:%M:%S")
  