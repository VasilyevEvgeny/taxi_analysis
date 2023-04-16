from scipy.stats import shapiro, ttest_ind, mannwhitneyu
from itertools import combinations
from io import TextIOWrapper
from pandas import DataFrame


class StatisticsCalculator:
    def __init__(self):
        self.__alpha_threshold = 0.05

    def __calculate_year_statistics(self, f: TextIOWrapper, df: DataFrame, all_data=False) -> bool:
        f.write('Rides: {:d}\n'.format(len(df)))
        df_print = df[['total_sum', 'duration, [min]', 'distance, [km]', 'rrc_i, [RUB/km]']].describe() \
            .rename(columns={'total_sum': 'total_sum, [RUB]', 'rrc_i, [RUB/km]': 'RRC_i, [RUB/km]'}) \
            .transpose()[['mean', 'std', '50%', 'min', 'max']]
        f.write('Data description:\n{}\n'.format(df_print))

        shapiro_test = shapiro(df['rrc_i, [RUB/km]'].to_list())
        f.write('Check RRC_i for normality:\nShapiro-Wilk test -> W = {:.4f}, p_value = {:.4f}\n'
                .format(shapiro_test.statistic, shapiro_test.pvalue))

        data_name = 'All RRC_i' if all_data else 'RRC_i for current year'
        if shapiro_test.pvalue < self.__alpha_threshold:
            f.write('{} is NOT distributed normally!\n'.format(data_name))
            return False
        else:
            f.write('{} is distributed normally!\n'.format(data_name))
            return True

    def __calculate_comparative_statistics(self, f: TextIOWrapper, year_l: int, data_year_l: list,
                                           year_r: int, data_year_r: list, is_norm: bool):
        param_name = 'Mean' if is_norm else 'Median'
        if is_norm:
            t_test = ttest_ind(data_year_l, data_year_r)
            f.write('Check if {}(RRC_i, {}) < {}(RRC_i, {}):\n'.format(param_name, year_l, param_name, year_r))
            f.write('T-test -> T = {:.4f}, p_value = {:.4f}\n'
                    .format(t_test.statistic, t_test.pvalue))
            result = 'YES' if t_test.pvalue <= self.__alpha_threshold else 'NO'
        else:
            mannwhitneyu_test = mannwhitneyu(data_year_l, data_year_r)
            f.write('Check if {}(RRC_i, {}) < {}(RRC_i, {}):\n'.format(param_name, year_l, param_name, year_r))
            f.write('Mann-Whitney test -> U = {:.4f}, p_value = {:.4f}\n'
                    .format(mannwhitneyu_test.statistic, mannwhitneyu_test.pvalue))
            result = 'YES' if mannwhitneyu_test.pvalue <= self.__alpha_threshold else 'NO'

        f.write('{}\n'.format(result))

    def calculate_statistics(self, df: DataFrame, location_name: str):
        separator = '=========================================================================================='

        f = open('stats_{}.txt'.format(location_name), 'w')
        f.write('{}\n'.format(separator))
        f.write('LOCATION: {}\n{}\n'.format(location_name, separator))
        f.write('To analyze the change in taxi fare over time, consider parameter\n'
                'RRC_i = total_sum / distance - relative ride cost adjusted for inflation.\n'
                'To keep a sufficient sample only Economy service class is considered.\n'
                'For all used statistical criteria significance level is {}.\n'.format(self.__alpha_threshold))
        f.write('{}\n'.format(separator))
        f.write('Analyze all RRC_i for normality...\n')
        f.write('{}\n'.format(separator))
        self.__calculate_year_statistics(f, df, all_data=True)

        f.write('{}\n'.format(separator))
        f.write('Analyze annular RRC_i for normality...\n')
        is_norm_dists = []
        years = df['year'].unique()
        data = {}
        for year in years:
            f.write('{}\nYEAR = {}\n'.format(separator, year))

            df_year = df[df['year'] == year].reset_index(drop=True)
            data[year] = df_year['rrc_i, [RUB/km]'].to_list()

            is_norm = self.__calculate_year_statistics(f, df_year)
            is_norm_dists.append(is_norm)

        is_norm = all(is_norm_dists)
        if is_norm:
            f.write('{}\n'.format(separator))
            f.write('RRC_i for all years is distributed normally!\n')
        else:
            f.write('{}\n'.format(separator))
            f.write('RRC_i for at least one year is not distributed normally!\n')

        pairs = [comb for comb in combinations(years, 2)]
        for pair in pairs:
            f.write('{}\n'.format(separator))
            self.__calculate_comparative_statistics(f, pair[0], data[pair[0]], pair[1], data[pair[1]], is_norm)
        f.write('{}\n'.format(separator))
        f.close()
