#!/usr/bin/env python
'''Beancount importer for China Merchants Bank credit cards'''

import sys
import csv
import argparse
import datetime
import glob
import os

from base import Account
from base import Transaction


# 招商银行 信用卡
class CMBCreditCard(Account):
    folder_name = "cmb_credit"

    map_cards = True

    def __init__(self):
        super(CMBCreditCard, self).__init__()
        self.name = "招商银行"
        self.commondity = "Liabilities:Bank:CMB:CreditCards"

    def parser_row(self, row):
        return CMBTransaction(row)


class CMBTransaction(Transaction):
    def __init__(self, row):
        super(CMBTransaction, self).__init__()
        self.row = row

        self.trade_date = row[1].strip()  # 交易日期
        self.payee = row[3].strip().replace('"', '')  # 交易摘要

        self.amount = row[5].strip().strip('"').replace(',', '')  # 人民币金额
        if not self.amount.startswith('-'):
            self.expenses = self.amount
        else:
            self.income = self.amount

        self.settled_date = row[2].strip()  # 记账日期
        self.card_last_digit = row[4].strip()  # 卡号后四位
        self.category = row[6].strip()  # 消费类别
        self.comment = row[7].strip()  # 备注

    def is_assets(self):
        return False

    def description(self):
        return self.payee

    def metadata(self):
        card = self.card_last_digit

        if CMBCreditCard.map_cards:
            card = _map_card(int(card))

        metadata = (
            '  bill: "cmb credit"\n'
            '  settled_date:"{0.settled_date}"\n'
            '  card:"{1}"\n'
        ).format(self, card)

        if CMBCreditCard.show_linked:
            link = (
                '; link: "{0}"\n'
            ).format(self.link)
            metadata += link

        return metadata

    def postings(self):
        if not self.income:
            return (
                '  {1} -{0.amount} CNY\n'
                '  ! Expenses:Uncategorized +{0.amount} CNY'
            ).format(self, self.commondity())
        else:
            return (  # Refunds
                '  {1} +{0.amount} CNY\n'
                '  ! Expenses:Uncategorized -{0.amount} CNY'
            ).format(self, self.commondity())

    def beancount_repr(self):
        metadata = self.metadata()
        flags = Account.beancount_flags
        postings = self.postings()
        return (
            '{0.trade_date} {3} "{0.payee}" {0.comment}\n'
            '{1}'
            '{2}'
            ).format(self, metadata, postings, flags)


def _map_card(last4):
    JCB = (985,)
    VIS = (4197,)
    MCC = (3333,)
    cards = {
        JCB: 'JCB',
        VIS: 'Visa',
        MCC: 'MasterCard'
    }
    card = next((cards[k] for k in cards.keys() if last4 in k), 'Unknown')
    return card


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'csv',
        help=(
            'CSV file of China Merchants Bank credit cards\n'
            'or directory that contains CSV files')
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()
    if args._pass:
        Account.beancount_flags = "*"

    csv = args.csv
    cmb = CMBCreditCard()
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
