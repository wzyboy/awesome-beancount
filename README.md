# Awesome Beancount [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

Awesome Beancount tends to be a collection of various
[Beancount](http://furius.ca/beancount/) tricks and tips, giving new users a
head start when learning command-line double-entry accounting for the first
time. [Inspired by @fantasticfears](https://twitter.com/fantasticfears/status/705839852445683713).


## What do we have here?

### Beancount importers (`importers` directory)

The original author of Beancount used to have a project
"LedgerHub", where all the "dirty code" for importing OFX and stock quotes data
into Beancount live. The project is announced dead and the code has been merged
back into Beancount.

Few banks outside North America support OFX. Banks and financial services in
China, for example, use their own private "bills" format. Users have to write
their own scripts to import these bills. Here we have a collection of importers
contributed by users.

They are not perfect, many of them have hard-coded values. Pull requests are
welcome to make them more portable and universal.

### How to get your data (`docs` directory)

Instructions on how to download your data suitable for importing from the
website of your banks.

You are welcome to write more.

### Test data (`test_data` directory)

We provide some test data for you to play and test with. For privacy reasons,
some information in the data are censored / modified / faked.

You could also submit your bank bills along with your importers.

## Documentation

- [Beancount documentation index](https://docs.google.com/document/d/1RaondTJCS_IUPBHFNdT8oqFKJjVJDsfsn6JEjBG04eA) - A index documentation
in Google Docs by Martin Blais (the author of Beancount).

### Methodology

- [Command-line Accounting in Context](https://docs.google.com/document/d/1e4Vz3wZB_8-ZcAwIFde8X5CjzKshE4-OXtVVHm4RQ8s/) - Reason why CLI accounting
- [The Double-Entry Counting Method (Working in progress)](https://docs.google.com/document/d/100tGcA4blh6KSXPRGCZpUlyxaRUwFHEvnz_k9DyZFn4/) - Explain accounting method

### For users

- [Get started guides](https://docs.google.com/document/d/1P5At-z1sP8rgwYLHso5sEy3u4rMnIUDDgob9Y_BYuWE/) - First entry for beancount beginner who know CLI.
- [Syntax reference](https://docs.google.com/document/d/1wAMVrKIA2qtRGmoVDSUBJGmYZSygUaR0uOMW1GV3YE0/) - All legitimate syntax and interpretation.
- [Cheat sheet](https://docs.google.com/document/d/1M4GwF6BkcXyVVvj4yXBJMX7YFXpxlxo95W6CpU3uWVc/) - One page cheatsheet for quick questions.
- [Cookbook](https://docs.google.com/document/d/1Tss0IEzEyAPuKSGeNsfNgb0BfiW2ZHyP5nCFBW1uWlk/edit#heading=h.5o43cxhng7b7) - How to manage accounts, how to do accounting in beancount by examples.

## Links

- [Beancount](http://furius.ca/beancount/)
- [Beancount source at Bitbucket](https://bitbucket.org/blais/beancount/overview)
- [Plain Text Accounting](http://plaintextaccounting.org/)
- [A Beancount tutorial (Chinese)](https://wzyboy.im/post/1063.html)
