#!/usr/bin/env python3
'''Beancount importer for China Merchants Bank debit cards'''

import sys
import csv
import argparse
from datetime import datetime
import glob
import os

from base import Account
from base import Transaction


# 招商银行借记卡
class CMBDebitCard(Account):
    folder_name = "cmb_debit"

    def __init__(self):
        super(CMBDebitCard, self).__init__()
        self.name = "招商银行"
        self.beancount_account = "Assets:CMB:DebitCard"

    # csv processing
    def load_csv(self):
        for f in glob.glob(os.path.join(self.path, "*.csv")):
            csv_data = open(f)
            self.parser_csv(csv_data)
            csv_data.close()

        self.transactions.sort(key=lambda t: t.trade_date)

    def parser_row(self, row):
        if row[0].strip().startswith('#'):
            return None
        return CMBDebitTransaction(row)


class CMBDebitTransaction(Transaction):
    """docstring for CMBDebitTransaction"""
    def __init__(self, row):
        super(CMBDebitTransaction, self).__init__()
        self.row = row
        if len(row) == 5:
            self.csv_5_fields_type(row)
        elif len(row) == 7:
            self.csv_7_fields_type(row)
        else:
            print("Unknow CMB debit csv file\nrow:" + str(row))
            sys.exit(1)

    def csv_7_fields_type(self, row):
        bd = row[0].strip()  # 交易日期
        self.trade_date = bd[:4] + '-' + bd[4:-2] + '-' + bd[6:]
        self.trade_time = row[1].strip()  # 交易时间
        self.expenses = row[2].strip()  # 支出
        if len(self.expenses) > 0:
            self.amount = self.expenses
            self.expenses = '-' + self.expenses
        self.income = row[3].strip()  # 存入
        if self.income:
            self.amount = self.income

        self.balance = row[4].strip()  # 余额
        self.category = row[5].strip()  # 交易类型
        self.comment = row[6].strip()  # 交易备注

    def csv_5_fields_type(self, row):
        date = row[0].strip()  # 交易时间
        self.datetime = datetime.strptime(date, '%Y%m%d  %H:%M:%S')
        self.trade_date = self.datetime.date().strftime('%Y-%m-%d')
        self.trade_time = self.datetime.time().strftime('%H:%M:%S')

        amount = row[1].strip().replace(',', '')  # 收支
        if amount.startswith('-'):
            self.expenses = amount
            self.amount = amount.strip('-')
        else:
            self.income = amount
            self.amount = amount

        self.balance = row[2].strip().replace(',', '')  # 余额
        self.category = row[3].strip()  # 交易类型
        self.comment = row[4].strip()  # 交易备注

    def description(self):
        return self.category

    def beancount_postings(self):
        if self.income:
            return (
                '  ! Income:Uncategorized -{0.income} CNY\n'
                '  {1} +{0.income} CNY'
            ).format(self, self.beancount_account())
        else:
            return (
                '  {1} {0.expenses} CNY\n'
                '  ! Expenses:Uncategorized +{0.amount} CNY'
            ).format(self, self.beancount_account())

    def beancount_repr(self):
        date = self.beancount_transaction_date()
        return (
            '{3} {2} "" "{0.comment}"\n'
            '  bill:"cmb debit"\n'
            '  time:"{0.trade_time}"\n'
            '  type:"{0.category}"\n'
            '  balance:"{0.balance}"\n'
            '{1}'
            ).format(self, self.beancount_postings(), Account.beancount_flags, date)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'csv',
        help=(
            'CSV file of China Merchants Bank debit cards\n'
            'or directory that contains CSV files')
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()
    if args._pass:
        Account.beancount_flags = "*"

    csv = args.csv
    cmb = CMBDebitCard()
    if os.path.isfile(csv):
        cmb.load_csv_file(csv)
    elif os.path.isdir(csv):
        cmb.load_csv_directory(csv)
    else:
        print('Path not exist: ' + csv)
        return 1
    cmb.print_beancount_bills()


if __name__ == '__main__':
    main()
