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

### Download card images

```bash
cat my_deck.txt | python3 -m scryfall -v info --output 'My Cool Deck'
```

### Rotate all images 90 degrees

```bash
python3 -m proxy -v info rotate Nazgul/*.png
```

### Stitch images into grid

```bash
python3 -m proxy -v info stitch -x 2 -y 4 Nazgul/*.png
```
