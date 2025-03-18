# Scryfall Scripts
- [Scryfall Scripts](#scryfall-scripts)
  - [Setup](#setup)
  - [Usage](#usage)
    - [List cards](#list-cards)
    - [Download card images](#download-card-images)
    - [Rotate all images 90 degrees](#rotate-all-images-90-degrees)
    - [Stitch images into grid](#stitch-images-into-grid)

Scripts for downloading stuff from [Scryfall](https://scryfall.com).

## Setup

```bash
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python3 -m scryfall --help
```

## Usage

### List cards

To list land MDFC cards. Equivalent to https://scryfall.com/search?q=is%3Amdfc+t%3Aland.
```bash
python3 -m scryfall -v info --list --name-only is:mdfc t:land
```

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
