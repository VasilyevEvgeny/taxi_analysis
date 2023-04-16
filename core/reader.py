from numpy import nan
from datetime import datetime, time
from PyPDF2 import PdfReader
from glob import glob
from tqdm import tqdm
from pandas import set_option, DataFrame, Series

set_option('display.max_columns', 500)
set_option('display.width', 1000)


class Reader:
    def __init__(self, **kwargs):
        self.__path_to_data = kwargs['path_to_data']
        self.__months = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7,
                         'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}

    def __get_date(self, splitted_page: list) -> datetime:
        DATE_INDEX = 0
        date_str = splitted_page[DATE_INDEX].split(' report for ')[-1].replace(',', '').replace('  ', ' ')
        splitted = date_str.split(' ')
        if len(splitted) == 4:
            if splitted[0].isdigit() and splitted[1].isdigit():
                splitted[0] = int(splitted[0] + splitted[1])
                del splitted[1]
        day, month, year = splitted

        return datetime(int(year), self.__months[month], int(day))

    @staticmethod
    def __get_start_address(route: list) -> str:
        START_ADDRESS_INDEX = 0
        return str(route[START_ADDRESS_INDEX])

    @staticmethod
    def __get_start_time(route: list) -> time:
        START_TIME_INDEX = 1
        splitted = route[START_TIME_INDEX].split(':')
        hours, minutes = splitted
        return time(int(hours), int(minutes))

    @staticmethod
    def __get_end_address(route: list) -> str:
        END_ADDRESS_INDEX = 2
        return str(route[END_ADDRESS_INDEX])

    @staticmethod
    def __get_end_time(route: list) -> time:
        END_TIME_INDEX = 3
        splitted = route[END_TIME_INDEX].split(' ')[0].split(':')
        hours, minutes = splitted
        return time(int(hours), int(minutes))

    @staticmethod
    def __parse_sum(raw: str) -> tuple:
        raw_summ = raw.split(' ')[-1].split(r'\u')[0]
        summ = int(raw_summ[1:])
        if raw_summ[0] == '₽':
            currency = 'RUB'
        elif raw_summ[0] == '₸':
            currency = 'KZT'
        else:
            currency = nan
        return summ, currency

    def __get_total_sum(self, payment: list) -> tuple:
        TOTAL_SUM_INDEX = 0
        return self.__parse_sum(payment[TOTAL_SUM_INDEX])

    @staticmethod
    def __get_passenger(splitted_page: list) -> str:
        PASSENGER_INDEX = 2
        splitted = splitted_page[PASSENGER_INDEX].split(' <')[0].split(' ')
        if len(splitted) == 3:
            splitted = [splitted[0], splitted[1] + splitted[2]]

        return ' '.join(splitted)

    @staticmethod
    def __get_service_class(splitted_page: list) -> str:
        SERVICE_CLASS_INDEX = 2
        return str(splitted_page[SERVICE_CLASS_INDEX].split('Service class ')[1])

    @staticmethod
    def __get_driver_registration(splitted_page: list) -> str:
        DRIVER_REGISTRATION_INDEX = -2
        return str(splitted_page[DRIVER_REGISTRATION_INDEX])

    @staticmethod
    def __time_str_to_min(time_str: str) -> int:
        splitted = time_str.split(' ')
        if len(splitted) == 4:
            res = int(splitted[0]) * 60 + int(splitted[2])
        elif len(splitted) == 2:
            res = int(splitted[0])
        else:
            raise Exception('Bad conversion from time string to minutes!')
        return res

    def __get_duration(self, splitted_page: list) -> int:
        RIDE_DURATION_INDEX = 4
        return int(self.__time_str_to_min(splitted_page[RIDE_DURATION_INDEX].split('Ride duration')[1]))

    @staticmethod
    def __get_distance(splitted_page: list) -> float:
        RIDE_DURATION_INDEX = 5
        return float(splitted_page[RIDE_DURATION_INDEX].split(' km')[0])

    @staticmethod
    def __is_route_ok(route: list) -> bool:
        if len(route) != 4:
            return False
        return True

    @staticmethod
    def __is_payment_ok(payment: list) -> bool:
        if len(payment) not in (1, 2):
            return False
        return True

    @staticmethod
    def __is__service_class_ok(splitted_page: list) -> bool:
        SERVICE_CLASS_INDEX = 2
        splitted = splitted_page[SERVICE_CLASS_INDEX].split('Service class ')
        if len(splitted) != 2:
            return False
        return True

    def readout(self) -> DataFrame:
        df = DataFrame({'date': Series(dtype='datetime64[ns]'),
                        'passenger': Series(dtype=str),
                        'start_address': Series(dtype=str),
                        'start_time': Series(dtype='datetime64[ns]'),
                        'end_address': Series(dtype=str),
                        'end_time': Series(dtype='datetime64[ns]'),
                        'total_sum': Series(dtype=int),
                        'currency': Series(dtype=str),
                        'service_class': Series(dtype=str),
                        'duration, [min]': Series(dtype=int),
                        'distance, [km]': Series(dtype=float),
                        'driver_registration': Series(dtype=str)})

        for file in tqdm(glob('{}/*.pdf'.format(self.__path_to_data))):
            reader = PdfReader(file)

            splitted_page_1 = list(dict.fromkeys(reader.pages[0].extract_text().split('\n')))
            splitted_page_2 = reader.pages[1].extract_text().split('\n')

            route = splitted_page_1[splitted_page_1.index('Route') + 1:splitted_page_1.index('Payment')]
            if self.__is_route_ok(route):
                start_address = self.__get_start_address(route)
                start_time = self.__get_start_time(route)
                end_address = self.__get_end_address(route)
                end_time = self.__get_end_time(route)
            else:
                continue

            payment = splitted_page_1[splitted_page_1.index('Payment') + 1:splitted_page_1.index('Payment method')]
            if self.__is_payment_ok(payment):
                total_sum, currency = self.__get_total_sum(payment)
            else:
                continue

            if self.__is__service_class_ok(splitted_page_2):
                service_class = self.__get_service_class(splitted_page_2)
            else:
                continue

            duration = self.__get_duration(splitted_page_2)
            distance = self.__get_distance(splitted_page_2)
            date = self.__get_date(splitted_page_1)
            passenger = self.__get_passenger(splitted_page_1)
            driver_registration = self.__get_driver_registration(splitted_page_2)

            df.loc[len(df)] = [date, passenger, start_address, start_time, end_address, end_time,
                               total_sum, currency, service_class, duration, distance, driver_registration]

        return df.sort_values(by=['date', 'start_time'], ignore_index=True)
