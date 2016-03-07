#!/usr/bin/env python

import sys
import csv
import argparse
import datetime
import base64
import os

from base import Account
from base import Transaction

from alipay import Alipay
from cmb_credit import CMBCreditCard
from cmb_debit import CMBDebitCard


class Resolver(object):
    """docstring for Resolver"""
    def __init__(self, accounts):
        super(Resolver, self).__init__()
        self.accounts = accounts

    def possible_accounts(self, t):
        others = list(self.accounts)
        others.remove(t.account)

        desc = t.description()
        a = [x for x in others if x.name in desc]
        return a

    def find_similar(self, t):
        possibles = self.possible_accounts(t)
        if not possibles:
            return None

        similar = []
        for a in possibles:
            results = a.search_similar(t)
            if results:
                similar.extend(results)

        # any similar?
        if not similar:
            return None

        if len(similar) > 1:
            print("more than one matched")
            return None

        return similar[0]

    def resolve(self):

        alltransactions = []
        for account in self.accounts:
            alltransactions.extend(account.transactions)

        matched = []
        exclude = []

        for account in self.accounts:
            for t in account.transactions:
                if t in exclude:
                    continue

                similar = self.find_similar(t)
                if not similar:
                    continue

                t.link_transaction(similar)
                matched.append(t)

                exclude.append(t)
                exclude.append(similar)

        remain = [x for x in alltransactions if x not in exclude]

        final = matched + remain
        final.sort(key=lambda t: t.sort_key())
        return final


def _create_bills_subfolder(directory):
    for a in Account.__subclasses__():
        if a.folder_name:
            path = os.path.join(directory, a.folder_name)
            os.makedirs(path)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'directory',
        help='A directory contains bills'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    argparser.add_argument(
        '-n', '--new', dest='_new', action='store_true',
        help='create directory structure'
    )
    argparser.add_argument(
        '--more_metadata', dest='more_metadata', action='store_true',
        help='show verbose metadata'
    )
    argparser.add_argument(
        '--more_postings', dest='more_postings', action='store_true',
        help='show postins change detail'
    )

    args = argparser.parse_args()
    if args._pass:
        Account.beancount_flags = "*"

    if args.more_metadata:
        Account.show_linked = True
        Account.show_merged = True
        Account.show_record = True
    if args.more_postings:
        Account.show_postings_mid = True

    directory = args.directory

    if not os.path.exists(directory):
        if args._new:
            _create_bills_subfolder(directory)
            return 0
        else:
            print("directory not exists: " + directory)
            return 1

    if args._new:
        print(
            "Could not create directory at",
            directory, ":path already exists."
        )

    accounts = []
    for a in Account.__subclasses__():
        if a.folder_name:
            path = os.path.join(directory, a.folder_name)
            if os.path.exists(path):
                account = a()
                account.load_csv_directory(path)
                accounts.append(account)

    r = Resolver(accounts)
    results = r.resolve()
    for t in results:
        print(t.beancount_repr())
        print("\n")


if __name__ == '__main__':
    main()
