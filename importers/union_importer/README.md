

## union_importer.py


1.First, use command 

```
./union_importer.py -n 2016-02
```

This command will create a folder

```
- 2016-02/
  - alipay/
  - cmb_credit/
  - cmb_debit/
```

Put your csv files in corresponding folder. Supported csv files is:

- Alipay trading record  ([交易记录](https://consumeprod.alipay.com/record/advanced.htm))
- Alipay ACCLog ([收支明细](https://lab.alipay.com/consume/record/items.htm))
- CMB Credit Card CSV
- CMB Debit Card CSV

Although the script still working if you don't provide all types csv files.
For better results, it's recommended that provide them all, in same date range.


2.after you plcace you csv files, then you can use command 

```
./union_impoter.py 2016-02
```

This command will process all csv files, combine related, filter out all duplicate, and print beancount format contents.

## cmb_credit.py/cmb_debit.py/alipay.py

If you don't need the union feature, `union_importer.py` still working if you only provide one csv file.
But these files are runable, you can use them to import their csv files.

## base.py

This file provide basic csv loading, parser. New source csv parser can import and create subclasses of `Account` and `Transaction`




