from datetime import datetime
from seaborn import violinplot
from matplotlib import pyplot as plt
from matplotlib import rc
from warnings import filterwarnings

filterwarnings('ignore')
rc('font', **{'family': 'serif', 'serif': ['Computer Modern Roman']})
rc('text', usetex=True)
rc('text.latex', preamble=r'\usepackage[utf8]{inputenc}')
rc('text.latex', preamble=r'\usepackage[russian]{babel}')


class Plotter:
    def __init__(self, df, location_name):
        self.__df = df
        self.__location_name = location_name

        self.__figsize = self.__cm2inch(15, 5)
        self.__xlabel = 'Year'
        self.__ylabel = r'RRC$_i$, [\textpeso /km]'

    @staticmethod
    def __cm2inch(length: float, height: float) -> tuple:
        cm_in_inch = 2.54
        return length / cm_in_inch, height / cm_in_inch

    def plot_regression(self, x: list, x_pred: list, y: list, predicted: dict) -> None:
        plt.figure(figsize=self.__figsize)
        plt.scatter(x, y, s=5, marker='o', c='black', alpha=1.0, label='original')
        plt.plot(x_pred, predicted[0]['y_pred'], c='red', alpha=1.0,
                 label='linear, RMSE = {:.3f}'.format(predicted[0]['rmse']))
        plt.plot(x_pred, predicted[1]['y_pred'], c='green', alpha=1.0,
                 label='quadratic, RMSE = {:.3f}'.format(predicted[1]['rmse']))
        plt.plot(x_pred, predicted[2]['y_pred'], c='blue', alpha=1.0,
                 label='cubic, RMSE = {:.3f}'.format(predicted[2]['rmse']))
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.xlabel('Distance, a.u.', fontsize=10)
        plt.ylabel('Total sum, a.u.', fontsize=10)
        plt.grid(ls=':', lw=0.5, c='gray', alpha=0.5)
        plt.legend(bbox_to_anchor=(0.0, 1.1, 1., 0.1), handlelength=3.0,
                   fontsize=10, loc='center', ncol=2, frameon=False)
        plt.savefig('regression_{}.png'.format(self.__location_name), bbox_inches='tight', dpi=500)
        plt.close()

    def plot_violines(self) -> None:
        plt.figure(figsize=self.__figsize)
        ax = violinplot(x='year', y='rrc_i, [RUB/km]', data=self.__df.sort_values('year'))
        fig = ax.get_figure()
        plt.ylim([0, 210])
        plt.xlabel(self.__xlabel, fontsize=10)
        plt.ylabel(self.__ylabel, fontsize=10)
        plt.grid(ls=':', lw=0.5, c='gray', alpha=0.5)
        fig.savefig('violines_{}.png'.format(self.__location_name), bbox_inches='tight', dpi=500)
        plt.close()

    def plot_smoothed(self, ts: list, vals: list, ts_smoothed_datetime: list, vals_smoothed: list,
                      averaging_interval: str) -> None:
        plt.figure(figsize=self.__figsize)
        plt.plot(self.__df['datetime'], self.__df['rrc_i, [RUB/km]'], markersize=1, marker='o', ls='-', lw=1,
                 c='black', alpha=1.0, label='original')
        plt.bar(ts, vals, width=50 if averaging_interval == 'quarter' else 150, color='blue', alpha=0.5, label='mean')
        plt.plot(ts_smoothed_datetime, vals_smoothed, ls='-', lw=1,
                 c='red', alpha=1.0, label='smoothed')
        plt.xticks([datetime(2018, 1, 1), datetime(2019, 1, 1), datetime(2020, 1, 1),
                    datetime(2021, 1, 1), datetime(2022, 1, 1), datetime(2023, 1, 1)],
                   ['{}'.format(i) for i in range(2018, 2024)])
        plt.xlim([datetime(2017, 10, 1), datetime(2023, 6, 1)])
        plt.ylim([0, 210])
        plt.xlabel(self.__xlabel, fontsize=10)
        plt.ylabel(self.__ylabel, fontsize=10)

        plt.grid(ls=':', lw=0.5, c='gray', alpha=0.5)
        plt.legend(frameon=False, loc='upper left')
        plt.savefig('smoothed_{}.png'.format(self.__location_name), bbox_inches='tight', dpi=500)
        plt.close()
