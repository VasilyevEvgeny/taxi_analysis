from argparse import ArgumentParser

from core.manager import Manager


def main():
    parser = ArgumentParser(description=
                            'TaxiAnalyzer - utility for quickly obtaining statistics '
                            'of the average taxi ride cost changes over time')
    parser.add_argument('-p', '--path', help='Path to data',
                        required=False, default='data', type=str)
    parser.add_argument('-l', '--location', help='Location(s) to analyze: Moscow, Vladimir or both', nargs='+',
                        required=False, default=['Moscow'], type=str)
    parser.add_argument('-i', '--averaging_interval', help='Averaging time interval: year or quarter',
                        required=False, default='year', type=str)
    args = parser.parse_args()

    manager = Manager(path_to_data=args.path,
                      location=args.location,
                      averaging_interval=args.averaging_interval)
    manager.process()


if __name__ == '__main__':
    main()
