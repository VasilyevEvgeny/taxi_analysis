from .reader import Reader
from .statistics import StatisticsCalculator
from .plotter import Plotter

from datetime import datetime
from numpy import vectorize, where, linspace, array
from pandas import to_datetime, to_timedelta, Index, Series, DataFrame, Timestamp
from scipy.interpolate import interp1d
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error


class Manager:
    def __init__(self, **kwargs):
        location = kwargs.get('location', ['Moscow'])
        av_interval = kwargs.get('averaging_interval', 'year')
        self.__check(location, av_interval)

        self.__location = location
        self.__averaging_interval = av_interval

        reader = Reader(path_to_data=kwargs.get('path_to_data', 'data'))
        self.__data = reader.readout()

        self.__preprocess()

    @staticmethod
    def __check(location: list, av_interval: str) -> None:
        for e in location:
            if e not in ('Moscow', 'Vladimir'):
                raise Exception('Wrong location! Please, use "Moscow", "Vladimir" or both.')
        if av_interval not in ('year', 'quarter'):
            raise Exception('Wrong averaging interval! Please, use "year" or "quarter".')

    def process(self) -> None:
        self.__analyze(df_initial=self.__data,
                       l_border=datetime(2018, 1, 1, 0, 0, 0),
                       r_border=datetime(2022, 12, 31, 23, 59, 59),
                       location=self.__location,
                       averaging_interval=self.__averaging_interval)

    @staticmethod
    def __is_appropriate(arr, *info: list) -> bool:
        return any(e in info[0] for e in arr) or \
               any(e in info[1] for e in arr) or \
               any(e in info[2] for e in arr)

    def __identify_location(self, *info: list) -> str:
        if self.__is_appropriate(['Znamenskaya', 'Michurinsky', 'Vernadskogo', 'Udaltsova', 'Mos',
                                  'Krasnobogatyrskaya', 'Krasnoselskaya', 'Sokolnicheskaya', 'Burnasyan',
                                  'Mira Avenue, 102с30', 'Kotelnichesky', 'Yerevanskaya'], *info):
            return 'Moscow'
        elif self.__is_appropriate(['Vlad', 'Rastopchina', 'Dvoryanskaya', 'ulitsa 850-letiya'], *info):
            return 'Vladimir'
        else:
            return 'Other'

    @staticmethod
    def __increase(inflation_per_year: dict, inflation_coeff: dict, *info: list) -> list:
        date_obj, rrc = info[0], info[1]
        day = to_datetime(date_obj).dayofyear
        year = to_datetime(date_obj).year
        val = rrc
        if year == 2023:
            val *= 1 + (90 - day) * inflation_coeff[2023] / 100
        else:
            val *= 1 + 90 * inflation_coeff[2023] / 100
            for y in list(inflation_per_year.keys())[::-1][1:]:
                if year < y:
                    val *= 1 + inflation_per_year[y] / 100
                else:
                    val *= 1 + (365 - day) * inflation_coeff[y] / 100
                    break

        return val

    def __add_inflation(self, df: DataFrame) -> DataFrame:
        """
        Information about inflation in 2018-2023
        https://xn----ctbjnaatncev9av3a8f8b.xn--p1ai/%D1%82%D0%B0%D0%B1%D0%BB%D0%B8%D1%86%D1%8B-%D0%B8%D0%BD%D1%84%D0%BB%D1%8F%D1%86%D0%B8%D0%B8
        Using piecewise linear inflation function over years
        """
        inflation_per_year = {2018: 4.27, 2019: 3.05, 2020: 4.91, 2021: 8.39, 2022: 11.92, 2023: 1.68}
        inflation_coeff = dict()
        for year in inflation_per_year.keys():
            factor = 365 if year != 2023 else 90
            inflation_coeff[year] = inflation_per_year[year] / factor

        func = vectorize(self.__increase)
        df['rrc_i, [RUB/km]'] = func(inflation_per_year,
                                     inflation_coeff,
                                     df['date'],
                                     df['rrc, [RUB/km]'])

        return df

    def __preprocess(self) -> None:
        self.__data['rrc, [RUB/km]'] = self.__data['total_sum'] / self.__data['distance, [km]']
        self.__data['datetime'] = to_datetime(self.__data.date.astype(str) + ' ' + self.__data.start_time.astype(str))
        self.__data['year'] = self.__data['datetime'].dt.strftime('%Y').astype(int)
        self.__data['abs_time, [s]'] = to_timedelta(self.__data['datetime'] -
                                                    to_datetime(self.__data['date'][0])).dt.total_seconds()
        self.__data['abs_time, [s]'] -= self.__data.loc[0, 'abs_time, [s]']

        self.__data = self.__data.drop(where(Index(self.__data['abs_time, [s]']).duplicated())[0])

        self.__data['location'] = vectorize(self.__identify_location)(self.__data['start_address'], 
                                                                      self.__data['end_address'], 
                                                                      self.__data['driver_registration'])

    @staticmethod
    def __smooth(ts: list, vals: list) -> tuple:
        ts_full = linspace(ts[0], ts[-1], 1000)
        func = interp1d(ts, vals, kind='quadratic')
        vals_full = func(ts_full)

        return ts_full, vals_full

    @staticmethod
    def __make_group(x: datetime, averaging_interval: str) -> datetime:
        if averaging_interval == 'quarter':
            for year in range(2018, 2024):
                if datetime(year, 1, 1, 0, 0, 0) <= x <= datetime(year, 3, 31, 23, 59, 59):
                    return datetime(year, 2, 15)
                elif datetime(year, 4, 1, 0, 0) <= x <= datetime(year, 6, 30, 23, 59, 59):
                    return datetime(year, 5, 15)
                elif datetime(year, 7, 1, 0, 0) <= x <= datetime(year, 9, 30, 23, 59, 59):
                    return datetime(year, 8, 15)
                elif datetime(year, 10, 1, 0, 0) <= x <= datetime(year, 12, 31, 23, 59, 59):
                    return datetime(year, 11, 15)
        elif averaging_interval == 'year':
            for year in range(2018, 2023):
                if datetime(year, 1, 1, 0, 0, 0) <= x <= datetime(year, 12, 31, 23, 59, 59):
                    return datetime(year, 7, 1)
        else:
            raise Exception('Wrong averaging interval!')

    @staticmethod
    def __calculate_pred(intercept: float, coeffs: list, x_pred: list) -> list:
        return [intercept + sum(coeffs[i] * pow(x, i + 1) for i in range(len(coeffs))) for x in x_pred]

    def __fit_regression(self, df: DataFrame) -> tuple:
        df_regr = df.sort_values(by=['distance, [km]'], ignore_index=True)

        x_min, x_max = 0, 25
        y_min, y_max = 0, 800

        x = array([x_min + e / (x_max - x_min) for e in df_regr['distance, [km]'].to_list()])
        y = [y_min + e / (y_max - y_min) for e in df_regr['total_sum'].to_list()]

        x_pred = linspace(x_min, x_max, 1000)

        predicted = []

        for degree in [1, 2, 3]:
            poly = PolynomialFeatures(degree=degree, include_bias=False)
            poly_features = poly.fit_transform(x.reshape(-1, 1))
            poly_reg_model = LinearRegression()
            poly_reg_model.fit(poly_features, y)
            y_pred_part = poly_reg_model.predict(poly_features)

            res = dict()
            res['y_pred'] = self.__calculate_pred(poly_reg_model.intercept_, poly_reg_model.coef_, x_pred)
            res['rmse'] = mean_squared_error(y, y_pred_part, squared=False)

            predicted.append(res)

        return x, x_pred, y, predicted

    def __analyze(self, **kwargs) -> None:
        df_initial = kwargs['df_initial']
        l_border = kwargs['l_border']
        r_border = kwargs['r_border']
        location = kwargs.get('location', [])
        service_class = kwargs.get('service_class', [])
        averaging_interval = kwargs['averaging_interval']
        df = df_initial[(df_initial['currency'] == 'RUB') & (l_border <= df_initial['datetime']) &
                        (df_initial['datetime'] <= r_border)].reset_index(drop=True)
        df = self.__add_inflation(df)

        location_name = '_'.join(location)
        if len(location):
            df = df[df['location'].isin(location)].reset_index(drop=True)

        if len(service_class):
            df = df[df['service_class'].isin(service_class)].reset_index(drop=True)

        x, x_pred, y, predicted = self.__fit_regression(df)

        plotter = Plotter(df, location_name)
        plotter.plot_regression(x, x_pred, y, predicted)

        if averaging_interval == 'year':
            plotter.plot_violines()

            stats_calc = StatisticsCalculator()
            stats_calc.calculate_statistics(df, location_name)

        df['time_group'] = df['datetime'].apply(lambda x: self.__make_group(x, averaging_interval))
        df_groups = df[['time_group', 'rrc_i, [RUB/km]']].groupby(['time_group']).mean()
        vals = df_groups['rrc_i, [RUB/km]'].to_list()
        ts = df_groups.index.to_list()

        ts_sec = to_timedelta(Series(ts) - to_datetime(ts[0])).dt.total_seconds()
        ts_smoothed, vals_smoothed = self.__smooth(ts_sec.to_list(), vals)

        epoch_time = datetime(1970, 1, 1)
        base_secs = (ts[0] - epoch_time).total_seconds()
        ts_smoothed_datetime = [Timestamp(datetime.fromtimestamp(e + base_secs)) for e in ts_smoothed]

        plotter.plot_smoothed(ts, vals, ts_smoothed_datetime, vals_smoothed, averaging_interval)
