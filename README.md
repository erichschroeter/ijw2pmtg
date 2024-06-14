# Scryfall Scripts

Scripts for downloading stuff from [Scryfall](https://scryfall.com).

## Setup

```bash
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python3 -m scryfall --help
```

## Usage

```bash
cat my_deck.txt | python3 -m scryfall -v info --output 'My Cool Deck'
```
