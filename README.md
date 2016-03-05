# Awesome Beancount

Awesome Beancount tends to be a collection of various
[Beancount](http://furius.ca/beancount/) tricks and tips, giving new users a
head start when learning command-line double-entry accounting for the first
time. [Inspired by @fantasticfears](https://twitter.com/fantasticfears/status/705839852445683713).


## What do we have here?

Beancount importers. The original author of Beancount used to have a project
"LedgerHub", where all the "dirty code" for importing OFX and stock quotes data
into Beancount live. The project is announced dead and the code has been merged
back into Beancount.

Few banks outside North America support OFX. Banks and financial services in
China, for example, use their own private "bills" format. Users have to write
their own scripts to import these bills. Here we have a collection of importers
contributed by users:

- China Merchants Bank credit cards;
- China Merchants Bank debit cards;
- Alipay online payments.

They are not perfect, many of them have hard-coded values. Pull requests are
welcome to make them more portable and universal.


## Links

- [Beancount](http://furius.ca/beancount/)

- [Plain Text Accounting](http://plaintextaccounting.org/)

- [A Beancount tutorial (Chinese)](https://wzyboy.im/post/1063.html)

