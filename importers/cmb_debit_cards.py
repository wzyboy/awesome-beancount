#!/usr/bin/env python

import sys
import csv
import argparse
from datetime import datetime


class CMBDebitCardParser(object):

    def __init__(self, csv_data, card_name):
        self.reader = csv.reader(csv_data)
        self.card_name = card_name
        self.parsed = []

    def _expand_datetime(self, date):
        orig_date = datetime.strptime(date, '%Y%m%d  %H:%M:%S')
        iso_date = orig_date.date().strftime('%Y-%m-%d')
        iso_time = orig_date.time().strftime('%H:%M:%S')
        return iso_date, iso_time

    def _get_amounts(self, amount):
        _abs = amount.strip('-')
        if amount.startswith('-'):
            return '-' + _abs, '+' + _abs
        else:
            return '+' + _abs, '-' + _abs

    def parse(self, default_pass=True):
        for row in reversed(list(self.reader)):
            # Skip empty lines, comment lines, and table headers
            if not row:
                continue
            if row[0].startswith('#') or row[0].startswith('交易时间'):
                continue

            d = {}
            d['date'], d['time'] = self._expand_datetime(row[0].strip())
            d['flag'] = '*' if default_pass else '!'
            d['narration'] = row[3].strip() + ' ' + row[4].strip()
            d['balance'] = row[2].strip().replace(',', '')
            d['a'], d['e'] = self._get_amounts(
                row[1].strip().replace(',', '')
            )
            d['a_name'] = self.card_name
            self.parsed.append(d)

        return self.parsed


def compose_beans(parsed):
    template = (
        '{date} {flag} "{narration}"\n'
        '  time: "{time}"\n'
        '  balance: "{balance}"\n'
        '  Assets:CMB:{a_name} {a} CNY\n'
        '  Equity:Uncategorized {e} CNY'
    )
    beans = [template.format_map(p) for p in parsed]
    return beans


def print_beans(beans, filename=None):
    header = '\n; Imported from {}'.format(filename)
    sep = '\n' * 2
    print(header)
    print(sep.join(beans))


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'csv', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help='CSV file of China Merchants Bank debit card data'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    argparser.add_argument('-n', '--name', required=True)
    args = argparser.parse_args()

    parser = CMBDebitCardParser(args.csv, args.name)
    parsed = parser.parse(default_pass=args._pass)
    beans = compose_beans(parsed)
    print_beans(beans, args.csv.name)


if __name__ == '__main__':
    main()
