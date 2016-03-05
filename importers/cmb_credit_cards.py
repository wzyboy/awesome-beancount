#!/usr/bin/env python

import sys
import csv
import argparse


class CMBCreditCardParser(object):

    def __init__(self, csv_data):
        self.reader = csv.reader(csv_data)
        self.parsed = []

    def _map_card(self, last4):
        CUP = (1111,)
        VIS = (2222,)
        MCC = (3333,)
        cards = {
            CUP: 'China UnionPay',
            VIS: 'Visa',
            MCC: 'MasterCard'
        }
        card = next((cards[k] for k in cards.keys() if last4 in k), 'Unknown')
        return card

    def _map_amount(self, amount):
        _abs = amount.replace('-', '').replace(',', '')
        if not amount.startswith('-'):  # Expenses
            return '-' + _abs, '+' + _abs
        else:  # Refunds
            return '+' + _abs, '-' + _abs

    def parse(self, default_pass=True):
        for row in self.reader:
            if row[0].strip() == '对账标志':
                continue
            d = {}
            d['b_date'] = row[2].strip()
            d['flag'] = '*' if default_pass else '!'
            d['payee'] = row[3].strip().replace('"', '')
            d['c_date'] = row[1].strip()
            d['card'] = self._map_card(int(row[4].strip()))
            d['l'], d['e'] = self._map_amount(row[5].strip().strip('"'))
            self.parsed.append(d)
        return self.parsed


def compose_beans(parsed):
    template = (
        '{b_date} {flag} "{payee}" ""\n'
        '  date: {c_date}\n'
        '  card: "{card}"\n'
        '  Liabilities:CMB:CreditCards {l} CNY\n'
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
        help='CSV file of China Merchants Bank credit card bill'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()

    parser = CMBCreditCardParser(args.csv)
    parsed = parser.parse(default_pass=args._pass)
    beans = compose_beans(parsed)
    print_beans(beans, args.csv.name)


if __name__ == '__main__':
    main()
