#!/usr/bin/env python
'''Beancount importer for Alipay online payments'''

import sys
import csv
import argparse
from datetime import datetime
import os
import base64
import glob

from base import Account
from base import Transaction


def _amount_match(a1, a2):
    d1 = float(a1) if a1 else 0
    d2 = float(a2) if a2 else 0
    if d1+d2 == 0:
        return True
    return False


def _datetime_approximate(t1, t2):
    dateDelta = t1.datetime - t2.datetime
    return (dateDelta.total_seconds() <= 5)


def _amount_equal(t1, t2):
    return (_amount_match(t1.expenses, t2.income) and
            _amount_match(t1.income, t2.expenses))


def _beancount_account_for_source(source):
    return {
        '支付宝': 'Assets:Alipay',
        '天弘基金': 'Assets:Alipay',
        '招商银行': 'Liabilities:Bank:CMB:CreditCards',
    }.get(source, 'Equity:Uncategorized')


class Alipay(Account):
    folder_name = "alipay"

    def __init__(self):
        super(Alipay, self).__init__()
        self.name = "支付宝"
        self.beancount_account = "Assets:Alipay"

        self.is_acclog = False

        self.acclog_transactions = []
        self.record_transactions = []

    # csv processing
    def load_csv_data(self, csv_data):
        self.current_csv_type(csv_data)
        self.parser_csv(csv_data)
        if self.is_acclog:
            self.merge_acclog()
            self.acclog_transactions.extend(self.transactions)
        else:
            self.record_transactions.extend(self.transactions)

    def load_csv_directory(self, path):
        for f in glob.glob(os.path.join(path, "*.csv")):
            self.load_csv_file(f)
            self.transactions = []

        # TODO: mulitple csv with duplicated info
        #  1. never mind just let it go
        #  or 2. filter duplicated record/acclog
        # self.filter_results()

        self.merge_acclog_and_record()
        self.transactions.sort(key=lambda t: t.trade_date)

    def current_csv_type(self, csv_data):
        reader = csv.reader(csv_data)
        for row in reader:
            self.is_acclog = row[0].strip().startswith('#支付宝收支明细')
            break
        csv_data.seek(0)

    def parser_row(self, row):
        if self.is_acclog:
            return AliAcclog(row)
        return AliRecord(row)

    def row_valided(self, row):
        if not row or row[0].strip().startswith('#'):
            return False
        if row[0].strip().startswith('------'):
            return False
        return True

    def row_is_endmark(self, row):
        if not row or row[0].strip().startswith('------'):
            return True
        return False

    # transaction mergering

    def merge_acclog_and_record(self):
        found = []
        for acclog in self.acclog_transactions:
            record = self.record_with_tradeNo(acclog.tradeNo)
            if not record:
                record = self.find_record_with_acclog(acclog)
            acclog.record = record
            found.append(record)

        remainRecord = [x for x in self.record_transactions if x not in found]

        self.transactions = self.acclog_transactions + remainRecord

    def record_with_tradeNo(self, tradeNo):
        for i in self.record_transactions:
            if i.tradeNo == tradeNo:
                return i
        return None

    def find_record_with_acclog(self, acclog):
        source = acclog.source

        for i in self.record_transactions:
            if source in i.payee and \
             _datetime_approximate(acclog, i) and \
             _amount_equal(acclog, i):
                return i
        return None

    def merge_acclog(self):
        tr = []
        tc = TransactionCombiner()
        for t in self.transactions:
            tc.push_trans(t)
            d = tc.resolve()
            if d:
                tr.append(d)
        d = tc.final()
        if d:
            tr.append(d)
        self.transactions = tr

    # output
    def print_bills(self):
        for t in self.transactions:
            print(t.description())
            if t.record:
                print(t.record.description())
            if t.relate:
                print(t.relate.description())
            print("\n")

    # interface with other account


# Record
class AliRecord(Transaction):
    def __init__(self, row):
        super(AliRecord, self).__init__()
        self.row = row

        # csv fields mapping
        self.tradeNo = row[0].strip()  # 交易号
        self.orderNo = row[1].strip()  # 商户订单号
        self.dateString = row[2].strip()  # 交易创建时间
        self.datetime = datetime.strptime(self.dateString, "%Y-%m-%d %H:%M:%S")
        self.time = self.datetime.strftime("%H:%M:%S")
        self.trade_date = self.datetime.strftime("%Y-%m-%d")

        self.paymenDateStr = row[3]  # 付款时间
        self.modifyDateStr = row[4]  # 最近修改时间
        self.trade_from = row[5]     # 交易来源地

        self.type = row[6].strip()      # 类型
        self.payee = row[7].strip()     # 交易对方
        # payee may encoded with base64, decode it
        if self.payee.startswith("[b64]"):
            self.payee = base64.b64decode(self.payee[5:-6]).decode('UTF-8')

        self.name = row[8].strip()      # 商品名称

        self.amount = row[9].strip()    # 金额（元）
        self.is_income = (row[10].strip() == "收入")     # 收/支
        if self.is_income:
            self.income = self.amount
        else:
            self.expenses = '-' + self.amount

        self.success = (row[11].strip().endswith("成功"))   # 交易状态
        self.fee = row[12].strip()      # 服务费（元）
        self.refund = row[13].strip()   # 成功退款（元）
        self.comment = row[14].strip()  # 备注

        self.acclog = None
        self.record = None
        self.relate = None
        self.manager = None

    # output
    def description(self):
        return self.name

    # beancount stuff
    def beancount_repr(self):
        template = (
            '{date} {flag} "{payee}" "{narration}"\n'
            '{metadata}'
            '{postings}'
        )

        d = {}
        d['date'] = self.trade_date
        d['flag'] = Account.beancount_flags
        d['payee'] = self.payee
        d['narration'] = self.name
        d['metadata'] = (
            '  tradeNo:"{0.tradeNo}"\n'
            '  bill:"alipay record"\n'
            ).format(self)
        if self.expenses:
            d['postings'] = (
                '  ! {1} {0.expenses} CNY\n'
                '  ! Expenses:Uncategorized +{0.amount} CNY'
                ).format(self, self.beancount_account())
        else:
            d['postings'] = (
                '  ! Income:Uncategorized -{0.income} CNY\n'
                '  ! {1} +{0.income} CNY'
                ).format(self, self.beancount_account())

        return template.format_map(d)


# ACCLog
class AliAcclog(Transaction):
    def __init__(self, row):
        super(AliAcclog, self).__init__()
        self.row = row

        # csv fields mapping
        self.tradeNo = row[0].strip()  # 流水号
        self.dateString = row[1].strip()  # 时间
        dt = datetime.strptime(self.dateString, "%Y-%m-%d %H:%M:%S")
        self.datetime = dt
        self.time = dt.strftime("%H:%M:%S")
        self.trade_date = dt.strftime("%Y-%m-%d")

        self.name = row[2].strip()  # 名称
        self.comment = row[3].strip()  # 备注
        self.income = row[4].strip()  # 收入
        self.expenses = row[5].strip()  # 支出
        self.remain = row[6].strip()  # 账户余额
        self.source = row[7].strip()  # 资金渠道
        self.going = None

        self.target = self.source
        self.relate = None
        self.record = None
        self.manager = None

    def description(self):
        if self.relate:
            return self.source + self.relate.source
        return self.source

    def is_alipay_source(self):
        return self.source == "支付宝"

    def is_expanse(self):
        return len(self.expenses) > 0

    def is_income(self):
        return len(self.income) > 0

    # combine
    def is_looks_same(self, other):
        if not _datetime_approximate(self, other):
            return False

        if not _amount_match(self.income, other.expenses):
            return False

        if not _amount_match(self.expenses, other.income):
            return False

        return True

    # beancount stuff
    def postings(self):
        chain_target = self.chain_target()
        target_account = _beancount_account_for_source(chain_target)
        beancount_account = self.beancount_account()
        if self.link:
            beancount_account = self.link[0].beancount_account()
        alipay_account = _beancount_account_for_source("支付宝")

        expenses_account = "! Expenses:Uncategorized"
        if chain_target:
            expenses_account = _beancount_account_for_source(chain_target)

        if self.is_income():
            if self.is_alipay_source():
                # alipay => alipay
                return (
                        '  ! Income:Uncategorized -{1.income} CNY\n'
                        '  {2} +{1.income} CNY'
                    ).format(beancount_account, self, alipay_account)

            # other source => alipay source
            if self.manager.link:
                beancount_account = self.manager.link[0].beancount_account()

            return (
                '  {0} -{1.income} CNY\n'
                '  {2} +{1.income} CNY'
            ).format(beancount_account, self, alipay_account)
        else:
            exp = '+'+self.expenses.replace('-', '')
            if self.is_alipay_source():
                #  alipay source means expenses
                return (
                    '  {0} {1.expenses} CNY\n'
                    '  {2} {3} CNY'
                ).format(alipay_account, self, expenses_account, exp)

            return (  # 提现
                '  {0} {1.expenses} CNY\n'
                '  {2} {3} CNY'
            ).format(alipay_account, self, beancount_account, exp)

    def beancount_account(self):
        return _beancount_account_for_source(self.source)

    def chain_target(self):
        if self.record:
            return self.record.payee
        return self.payee

    def chain_info(self):
        if not self.relate:
            return self.source

        ac1 = self
        ac2 = self.relate

        # Is this from/to determine necessary?
        # is ac1 always is assetTo?
        assetFrom = ac1 if ac1.is_income() else ac2
        assetTo = ac1 if ac1.is_expanse() else ac2

        chain = ""
        payee = self.chain_target()
        if not payee:
            payee = "..."
        if assetTo.is_alipay_source() or assetFrom.is_alipay_source():
            chain = (
                '{1.source} => {0.source} => {2}'
            ).format(assetTo, assetFrom, payee)
        else:
            chain = (
                '{1.source} => 支付宝 => {0.source}'
            ).format(assetTo, assetFrom, chain)
        return chain

    def metadata(self):
        chain = self.chain_info()
        metadata = (
            '  tradeNo:"{0.tradeNo}"\n'
            '  bill:"alipay acclog"\n'
            '  time:"{0.time}"\n'
            '  comment:"{0.comment}"\n'
            '  chain: "{1}"\n'
        ).format(self, chain)

        if Alipay.show_merged and self.relate:
            merged = (
                '; merged acclog:  \n'
                ';  tradeNo: "{0.tradeNo}"\n'
                ';  date:"{0.dateString}"\n'
                ';  name: "{0.name}"\n'
                ';  comment: "{0.comment}"\n'
                ';  income:"+{0.income} CNY"\n'
                ';  source:"{0.source}"\n'
            ).format(self.relate)
            metadata += merged

        if Alipay.show_record and self.record:
            record = (
                '; merged record:\n'
                ';  payee:"{0.payee}"\n'
                ';  name:"{0.name}"\n'
            ).format(self.record)
            metadata += record

        if Alipay.show_linked and self.link:
            linked = (
                '; linked transaction\n'
                ';  account:"{0.account.name}"\n'
                ';  income:"{0.income}"\n'
                ';  expenses:"{0.expenses}"\n'
            ).format(self.link[0])
            metadata += linked
        return metadata

    def beancount_repr(self):
        template = (
            '{date} {flag} "{payee}" "{narration}"\n'
            '{metadata}'
            '{postings}'
        )

        d = {}
        d['date'] = self.trade_date
        d['flag'] = Account.beancount_flags
        d['payee'] = self.chain_target() or ''
        d['narration'] = ''
        d['metadata'] = ''
        d['postings'] = ''

        metadata = self.metadata()

        if self.relate:
            ac1 = self
            ac2 = self.relate
            assetFrom = ac1 if ac1.is_income() else ac2
            assetTo = ac1 if ac1.is_expanse() else ac2
            assert(ac1 == assetTo)

            d['narration'] = assetTo.name

            postings = (
                '{0}\n'
                '{1} '
            ).format(assetFrom.postings(), assetTo.postings())
            d['postings'] = postings

            lines = postings.splitlines(True)
            assert(len(lines) == 4)

            if Alipay.show_postings_mid:
                d['postings'] = (
                    '{}'
                    ';{}'
                    ';{}'
                    '{}'
                    ).format(lines[0], lines[1], lines[2], lines[3])
            else:
                d['postings'] = (
                    '{}'
                    '{}'
                    ).format(lines[0], lines[3])
        else:
            d['narration'] = self.name
            d['payee'] = ''
            d['postings'] = self.postings()

        d['metadata'] = metadata
        return template.format_map(d)

    # interface with other account
    def looks_like(self, t):
        if self.trade_date != t.trade_date:
            return False

        if self.source in t.account.name:
            # 提现
            if _amount_equal(self, t):
                return True

        relateMatch = False
        if self.relate:
            relateMatch = self.relate.relate_looks_like(t)

        if relateMatch:
            return True

        recordmatch = False
        if self.record:
            recordmatch = self.record_looks_like(self.record, t)
        if recordmatch:
            return True

        return False

    def relate_looks_like(self, t):
        if self.source == "支付宝":
            return False

        if self.source not in t.account.name:
            return False

        if self.income:
            if t.is_assets():
                if _amount_match(self.income, t.expenses):
                    return True
            else:
                if self.income == t.expenses:
                    return True
        else:
            pass

        return False

    def record_looks_like(self, record, t):
        if record.payee not in t.account.name:
            return False

        if t.is_assets():
            if _amount_equal(t, record):
                return True
        else:
            if t.income == record.expenses and t.expenses == record.income:
                return True

        return False


class TransactionCombiner(object):
    def __init__(self):
        super(TransactionCombiner, self).__init__()
        self.pendingRows = []

    def push_trans(self, trans):
        self.pendingRows.append(trans)

    def resolve(self):
        if len(self.pendingRows) > 1:
            ac1 = self.pendingRows[0]
            ac2 = self.pendingRows[1]
            if ac1.is_looks_same(ac2):
                ac1.relate = ac2
                ac2.manager = ac1
                self.pendingRows = []
                return ac1
            else:
                self.pendingRows.pop(0)
                return ac1

    def final(self):
        assert len(self.pendingRows) < 2

        if len(self.pendingRows) > 0:
            ac1 = self.pendingRows[0]
            self.pendingRows.pop(0)
            return self.single(ac1)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'csv',
        help='CSV file of Alipay bills or directory that contains CSV files'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()

    csv = args.csv
    alipay = Alipay()
    if os.path.isfile(csv):
        alipay.load_csv_file(csv)
    elif os.path.isdir(csv):
        alipay.load_csv_directory(csv)
    else:
        print('Path not exist: ' + csv)
        return 1
    alipay.print_beancount_bills()


if __name__ == '__main__':
    main()
