# How to get your data (P. R. China)

## China Merchants Bank 中国招商银行

Website: http://www.cmbchina.com/

Bills of China Merchants Bank (CMB) are availabe in both CSV and PDF files. One
could also request monthly HTML statements delivered to email inbox.
Among all three formats, CSV is the easiest to handle with. Downloading CSV
files requires a 个人银行大众版 or 个人银行专业版 online banking account of
CMB.

CSV files are encoded in GBK and terminated by CRLF. I suggest using `iconv`
and `dos2unix` to properly handle them before feeding them to the importer scripts.

### Debit card

Download links of CSV files could be found in:

账户管理 -> 交易查询 -> 活期交易查询

Only last 13 months of data could be downloaded.

### Credit card

Download links of CSV files could be found in:

账户管理 -> 自助对账

Unlike PDF statements, these CSV files are divided by calendar months instead
of billing cycles. If you made a purchase on 31st Jan, and your card is charged
on 1st Feb, this entry will appear in Feb's CSV file.
