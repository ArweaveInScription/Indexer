# Indexer

Indexer for arweave inscription prc-20 token

## Set up

1. install redis first

2. install python package
```
pip install -r requirements.txt
```

3. run indexer syncer
```
python syncer.py
```

## API

```
python api.py
```

default url: http://127.0.0.1:5000

- /info

indexer info

- /token/{tick}

prc-20 token info

eg: /token/aris

- /balance/{tick}/{address}

user balance

- /block/{height}

block info

- /tx/{everhash}

tx info