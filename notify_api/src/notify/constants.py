import re
from datetime import timedelta

from .choices import DelayChoices

# Константы значений
DELAY_MAPPING = {
    DelayChoices.IMMEDIATE: timedelta(0),
    DelayChoices.ONE_HOUR: timedelta(hours=1),
    DelayChoices.ONE_DAY: timedelta(days=1),
}
MIN_LENGTH_MESSAGE = 1
MAX_LENGTH_MESSAGE = 1024
MAX_LENGTH_ADDRESS = 150
MIN_VALUE_DELAY = 0
MAX_VALUE_DELAY = 2

# Константы для валидации
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
TELEGRAM_ID_REGEX = re.compile(r"^\d+$")
