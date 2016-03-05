#!/usr/bin/env python3


import sys
import csv
import argparse
import datetime

def _amount_match(a1,a2):
    d1 = float(a1) if a1 else 0
    d2 = float(a2) if a2 else 0

    if d1+d2 == 0:
        return True

    return False

def _commondity_for_source(source):
    return {
        '支付宝' : 'Assets:Alipay',
        '天弘基金' : 'Assets:Alipay',
        '招商银行' : 'Liabilities:Bank:CMB:CreditCards',
    }.get(source,'Equity:Uncategorized')


class AliTransaction(object):
    """docstring for AliTransaction"""
    def __init__(self, row):
        super(AliTransaction, self).__init__()
        self.row = row

        self.tradeNo = row[0].strip() #流水号
        self.dateString = row[1].strip() #时间
        self.datetime = datetime.datetime.strptime(self.dateString,"%Y-%m-%d %H:%M:%S")
        self.time = self.datetime.strftime("%H:%M:%S")
        self.name = row[2].strip() #名称
        self.comment = row[3].strip() #备注
        self.income =  row[4].strip() #收入
        self.expenses = row[5].strip() #支出
        self.remain = row[6].strip() #账户余额
        self.source = row[7].strip() #资金渠道

    def is_alipay_source(self):
        return self.source == "支付宝"
    def is_yuebao_source(self):
        return self.source == "天弘基金"
    def is_bank_source(self):
        return "银行" in self.source

    def is_expanse(self):
        return len(self.expenses) > 0
    def is_income(self):
        return len(self.income) > 0

    def beancount_date(self):
        return self.datetime.strftime("%Y-%m-%d")

    def postings(self):
        commondity = self.commondity()
        alipayCommondity = _commondity_for_source("支付宝")

        if self.is_income():
            if self.is_alipay_source():
                # alipay => alipay
                return (
                    '  Income:Uncategorized -{1.income} CNY\n'
                    '  {2} +{1.income} CNY'
                    ).format(commondity,self,alipayCommondity)

            # other source => alipay source
            return (
            '  {0} -{1.income} CNY\n'
            '  {2} +{1.income} CNY'
            ).format(commondity,self,alipayCommondity)
        else:
            exp  = '+'+self.expenses.replace('-', '')
            if self.is_alipay_source():
                #  alipay source means expenses
                return (
                '  {0} {1.expenses} CNY\n'
                '  ! Expenses:Uncategorized {3} CNY'
                ).format(alipayCommondity,self,commondity,exp)

            return (
            '  {0} {1.expenses} CNY\n'
            '  ! {2} {3} CNY'
            ).format(alipayCommondity,self,commondity,exp)

            

    def commondity(self):
        return _commondity_for_source(self.source)

    def is_looks_same(self,other):
        dateDelta = self.datetime - other.datetime
        if dateDelta.total_seconds() > 5:
            return False
        if _amount_match(self.income,other.expenses) == False:
            return False
        if _amount_match(self.expenses,other.income) == False:
            return False

        return True

        

class TransactionCombiner(object):
    """docstring for TransactionCombiner"""

    def __init__(self):
        super(TransactionCombiner, self).__init__()
        self.pendingRows = []
    
    def push_row(self,row):
        at = AliTransaction(row)
        self.pendingRows.append(at)

    def resolve(self):
        if len(self.pendingRows) > 1:
            ac1 = self.pendingRows[0]
            ac2 = self.pendingRows[1]
            if ac1.is_looks_same(ac2):
                d = self.combine(ac1,ac2)
                self.pendingRows = []
                return d
            else:
                d= self.single(ac1)
                self.pendingRows.pop(0)
                return d

    def final(self):
        assert len(self.pendingRows) < 2

        if len(self.pendingRows) > 0:
            ac1 = self.pendingRows[0]
            self.pendingRows.pop(0)
            return self.single(ac1)

    def combine(self,ac1,ac2):
        assert ac1 != ac2

        assetFrom = ac1 if ac1.is_income() else ac2
        assetTo = ac1 if ac1.is_expanse() else ac2
        assert assetFrom != assetTo

        d = {}
        d['b_date'] = assetTo.beancount_date()
        d['narration'] = assetTo.name
        d['payee'] = ''

        chain = ""
        if assetTo.is_alipay_source() or assetFrom.is_alipay_source():
            chain = ('{1.source} => {0.source} => ...').format(assetTo,assetFrom,chain)
        else:
            chain = ('{1.source} => 支付宝 => {0.source}').format(assetTo,assetFrom,chain)

        d['metadata'] = (
                '  tradeNo:"{0.tradeNo}"\n'
                '  time:"{0.time}"\n'
                '  comment:"{0.comment}"\n'
                # '  source: "{0.source}"\n'
                '  chain: "{2}"'
                # uncomment to include merged infomation
                # '\n; merged transaction:  \n'
                # ';   tradeNo: "{1.tradeNo}"\n'
                # ';   date:"{1.dateString}"\n'
                # ';   name: "{1.name}"\n'
                # ';   comment: "{1.comment}"\n'
                # ';   income:+{1.income} CNY\n'
                # ';   source:"{1.source}"'
                ).format(assetTo,assetFrom,chain)

        postings = (
            '{2}\n'
            '{3} '
            ).format(assetFrom,assetTo,assetFrom.postings(),assetTo.postings())

        lines = postings.splitlines(True)
        d['postings'] = (
            '{}'
            ';{}'
            ';{}'
            '{}'
            ).format(lines[0],lines[1],lines[2],lines[3])

        return d

    def single(self,ac):
        d = {}
        d['b_date'] = ac.beancount_date()
        d['narration'] = ac.name
        d['payee'] = ''
        d['metadata'] = (
                '  tradeNo:"{0.tradeNo}"\n'
                '  comment:"{0.comment}"\n'
                '  time:"{0.time}"'
                # '\n  source: "{0.source}"'
                ).format(ac)
        d['postings'] = ac.postings()
        return d

# === main ===

def parse_alipay_acclog(csv_data, args):
    reader = csv.reader(csv_data)
    parsed = []
    inHeader = True

    tc = TransactionCombiner()
    for row in reader:
        if len(row) == 0:
            continue

        if row[0].strip().startswith("#"):
            continue

        if row[0].strip() == '流水号':
            inHeader = False
            continue

        if inHeader:
            continue
        
        # start process contents
        tc.push_row(row)
        d = tc.resolve()
        if d:
            d['flag'] = '*' if args._pass else '!'
            parsed.append(d)

    d = tc.final()
    if d:
        d['flag'] = '*' if args._pass else '!'
        parsed.append(d)

    return parsed


def compose_beans(parsed):
    template = (
        '{b_date} {flag} "{payee}" "{narration}"\n'
        '{metadata}\n'
        '{postings}'
    )
    beans = []
    for p in parsed:
        bean = template.format_map(p)
        beans.append(bean)
    return beans


def print_beans(beans, filename=None):
    header = (
        '; vim: ft=beancount nofoldenable:\n'
        '; Imported from {}\n\n'.format(filename)
    )
    sep = '\n' * 2
    print(header)
    print(sep.join(beans))


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'csv', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help='CSV file of Alipay ACCLOG(余额收支明细)'
    )
    argparser.add_argument('-p', '--pass', dest='_pass', action='store_true')
    args = argparser.parse_args()

    parsed = parse_alipay_acclog(args.csv, args)
    beans = compose_beans(parsed)
    print_beans(beans, args.csv.name)


if __name__ == '__main__':
    main()
