# I Just Want 2 Play Magic the Gathering
*sigh* **I** **J**ust **W**ant **2** **P**lay **M**agic **t**he **G**athering is a set of scripts used to create proxies so I can just play MTG.

- [I Just Want 2 Play Magic the Gathering](#i-just-want-2-play-magic-the-gathering)
  - [Setup](#setup)
  - [Usage](#usage)
    - [List cards](#list-cards)
    - [Download card images](#download-card-images)
    - [Rotate all images 90 degrees](#rotate-all-images-90-degrees)
    - [Stitch images into grid](#stitch-images-into-grid)

Scripts for downloading stuff from [Scryfall](https://scryfall.com) and creating proxies.

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

Download via standard input:
```bash
cat my_deck.txt | python3 -m scryfall --output 'My Cool Deck'
```

Download the example proxy card list via input file:
```bash
python3 -m scryfall -i examples/proxies.txt --output 'Proxies'
```

Download a single card via the command line:
```bash
python3 -m scryfall "Scullclamp (MOC)"
```

### Rotate all images 90 degrees

```bash
python3 -m proxy -v info rotate Nazgul/*.png
```

### Stitch images into grid

```bash
python3 -m proxy -v info stitch -x 2 -y 4 Nazgul/*.png
```
