#!/usr/bin/env python

import csv
import glob
import os


def guess_header_line(csv_data):
    reader = csv.reader(csv_data)
    minLen = 5
    lineNum = 0
    for row in reader:
        if len(row) >= minLen:
            break
        lineNum += 1

    return lineNum


def csv_seek_to_header(csv_data):
    lineNum = guess_header_line(csv_data)
    csv_data.seek(0)

    if lineNum == 0:
        return

    reader = csv.reader(csv_data)
    while lineNum > 0:
        next(reader)
        lineNum -= 1


class Account(object):
    folder_name = ""

    # output control
    show_merged = False
    show_record = False
    show_linked = False
    show_postings_mid = False
    beancount_flags = "!"

    def __init__(self):
        super(Account, self).__init__()
        self.transactions = []
        self.name = type(self)

    # csv loading
    def parser_csv(self, csv_data):
        csv_seek_to_header(csv_data)
        reader = csv.reader(csv_data)

        next(reader)  # skip header
        for row in reader:
            if self.row_is_endmark(row):
                break
            if not self.row_valided(row):
                continue
            t = self.parser_row(row)
            if t:
                t.account = self
                self.transactions.append(t)

    def load_csv_data(self, csv_data):
        self.parser_csv(csv_data)

    def load_csv_file(self, path):
        csv_data = open(path)
        self.load_csv_data(csv_data)
        csv_data.close()

    def load_csv_directory(self, path):
        for f in glob.glob(os.path.join(path, "*.csv")):
            self.load_csv_file(f)

        self.transactions.sort(key=lambda t: t.trade_date)

    def row_valided(self, row):
        if len(row) == 0:
            return False
        return True

    def row_is_endmark(self, row):
        """If the csv file has addition infomation after table body
        return True to end csv parsering
        """
        return False

    def parser_row(self, row):
        """Override to return Transaction object
        """
        return None

    # output
    def print_beancount_bills(self):
        for t in self.transactions:
            print(t.beancount_repr())
            print("\n")

    # transaction linking
    def search_similar(self, ot):
        lk = []
        for t in self.transactions:
            if t.looks_like(ot) or ot.looks_like(t):
                lk.append(t)

        if len(lk) > 0:
            return lk
        return None


class Transaction(object):
    def __init__(self):
        super(Transaction, self).__init__()
        self.trade_date = None
        self.income = None
        self.expenses = None

        self.comment = None
        self.payee = None
        self.target = None
        self.link = []

    # transaction linking
    def looks_like(self, t):
        """Override to determine if a transaction in other account is same with self
        """
        return False

    def is_assets(self):
        """Subclass can override this method
        return False if it is a credit card
        """
        return True

    def description(self):
        """Provide infomation which contains keywords of other account
        """
        return (
            '{} \t {} {}'
        ).format(self.comment, self.payee, self.target)

    def link_transaction(self, other):
        self.link.append(other)
        other.link.append(self)

    # output
    def commondity(self):
        return self.account.commondity

    def beancount_repr(self):
        amount = 0
        if len(self.income) > 0:
            amount = self.income
        else:
            amount = self.expenses

        commondity = "Liabilities:CMB:CreditCards"
        return (
            '{0.trade_date} ! "{0.payee}" {0.comment}\n'
            ' {1} {2} CNY\n'
            ' ! Expenses:Uncategorized'
            ).format(self, commondity, amount)

    def __repr__(self):
        rep = (
            '{0.account.name} date:{0.trade_date}\t'
            'income:{0.income}\texpense:{0.expenses}\tdesc:{1}'
        ).format(self, self.description())
        if len(self.link) > 0:
            rep = ("{}\n  =>{}").format(rep, self.link)
        return rep
