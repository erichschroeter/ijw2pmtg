from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass
import json
import logging
import os
import re
import sys
import time
from .api import Scryfall
from .parsing import CardParserFactory
from .api import Card
from .api import IMAGE_FILENAME_FORMAT  # Add this import at the top

# region Command line parsing  # noqa


class ColorLogFormatter(logging.Formatter):
    """
    Custom formatter that changes the color of logs based on the log level.
    """

    grey = "\x1b[38;20m"
    green = "\u001b[32m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\u001b[34m"
    cyan = "\u001b[36m"
    reset = "\x1b[0m"

    timestamp = "%(asctime)s - "
    loglevel = "%(levelname)s"
    message = " - %(message)s"

    def __init__(self, with_timestamp=False):
        super().__init__()
        if with_timestamp:
            self.FORMATS = {
                logging.DEBUG: (
                    self.timestamp
                    + self.blue
                    + self.loglevel
                    + self.reset
                    + self.message
                ),
                logging.INFO: (
                    self.timestamp
                    + self.green
                    + self.loglevel
                    + self.reset
                    + self.message
                ),
                logging.WARNING: (
                    self.timestamp
                    + self.yellow
                    + self.loglevel
                    + self.reset
                    + self.message
                ),
                logging.ERROR: (
                    self.timestamp
                    + self.red
                    + self.loglevel
                    + self.reset
                    + self.message
                ),
                logging.CRITICAL: (
                    self.timestamp
                    + self.bold_red
                    + self.loglevel
                    + self.reset
                    + self.message
                ),
            }
        else:
            self.FORMATS = {
                logging.DEBUG: (self.blue + self.loglevel + self.reset + self.message),
                logging.INFO: (self.green + self.loglevel + self.reset + self.message),
                logging.WARNING: (
                    self.yellow + self.loglevel + self.reset + self.message
                ),
                logging.ERROR: (self.red + self.loglevel + self.reset + self.message),
                logging.CRITICAL: (
                    self.bold_red + self.loglevel + self.reset + self.message
                ),
            }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def _init_logger(level=logging.INFO, timestamp=False):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = ColorLogFormatter(with_timestamp=timestamp)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class RawTextArgumentDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter
):
    pass


# endregion Command line parsing  # noqa


def dryrun(msg):
    green = "\u001b[32m"
    reset = "\x1b[0m"
    print(f"{green}DRYRUN{reset}: {msg}")


class App:
    def __init__(self) -> None:
        self.args = None
        # TODO [x] refactor to support -l or --list to list cards
        # TODO [x] refactor to support -d or --download to download cards
        # TODO [x] refactor to default to --list
        # TODO [x] refactor to support --with-set
        # TODO [x] refactor to support --with-cn
        # TODO [x] refactor to support --with-block
        # TODO [x] refactor to support --json
        # TODO [x] refactor to support input format "Card Name (Set Name)"
        # TODO [x] refactor to support input format "Card Name (Set Name) collector-number"
        # TODO [x] refactor to support input format "Card Name e:setname cn:number b:block"
        # TODO [ ] implement download if not in download directory
        # TODO [x] implement --timestamp to include timestamp in logs
        self.parser = argparse.ArgumentParser(prog="scryfall")
        self.parser.add_argument(
            "-v",
            "--verbosity",
            choices=["critical", "error", "warning", "info", "debug"],
            default="info",
            help="Set the logging verbosity level.",
        )
        self.parser.add_argument(
            "--server",
            default="https://api.scryfall.com",
            help="The Scryfall server URL.",
        )
        self.parser.add_argument(
            "--cache",
            default="cache",
            help="The cache directory for Scryfall data and images.",
        )
        self.parser.add_argument(
            "--timestamp",
            default=False,
            help="Include timestamp in log messages.",
            action="store_true",
        )
        self.parser.add_argument(
            "--dryrun",
            default=False,
            help="Dry run network and filesystem operations.",
            action="store_true",
        )
        self.parser.add_argument(
            "-i",
            "--input",
            help="A file of card names. Alternatively, a newline-separated list of card names can be provided via stdin.",
        )
        self.parser.add_argument(
            "-o", "--output", default=os.getcwd(), help="The output directory."
        )
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument(
            "-l",
            "--list",
            action="store_true",
            help="Searches for cards based on query. Does not download them.",
        )
        group.add_argument(
            "-d",
            "--download",
            action="store_true",
            help="Downloads card images based on query.",
        )
        self.parser.add_argument(
            "--json", action="store_true", help="Output results in JSON format."
        )
        self.parser.add_argument(
            "--with-block",
            action="store_true",
            help="Include 3-letter block code when listing cards. e.g. ZNR for Zendikar Rising.",
        )
        self.parser.add_argument(
            "--with-cn",
            action="store_true",
            help="Include collector number when listing cards. e.g. 1/280.",
        )
        self.parser.add_argument(
            "--with-set",
            action="store_true",
            help="Include set name when listing cards. e.g. Zendikar Rising.",
        )
        self.parser.add_argument(
            "cards", nargs="*", help="Names of Magic the Gathering (MTG) cards."
        )
        self.parser.set_defaults(func=self.default_func)

    def default_func(self, args):
        if not args.list and not args.download:
            logging.error("You must specify either --list (-l) or --download (-d)")
            self.parser.print_help()
            sys.exit(1)

        if args.download:
            download_cards(args)
        else:
            list_cards(args)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()), self.args.timestamp)
        logging.debug(f"command-line args: {self.args}")
        self.args.func(self.args)


def list_cards(args):
    api = Scryfall(args.server)
    query = " ".join(args.cards) if args.cards else ""
    if query:
        cards = api.cards_search(query)
        if cards:
            logging.info(f"Found {len(cards)} cards.")
            if args.json:
                output = json.dumps([vars(card) for card in cards], indent=2)
            elif args.with_block and args.with_cn and args.with_set:
                output = "\n".join(
                    [
                        f"{c.name} ({c.block}) {c.collector_number} {c.set_name}"
                        for c in cards
                    ]
                )
            elif args.with_block and args.with_cn:
                output = "\n".join(
                    [f"{c.name} ({c.block}) {c.collector_number}" for c in cards]
                )
            elif args.with_block:
                output = "\n".join([f"{c.name} ({c.block})" for c in cards])
            else:
                output = "\n".join([c.name for c in cards])
            if args.output and not os.path.isdir(args.output):
                with open(args.output, "w") as f:
                    f.write(output)
                logging.info(f"Results saved to {args.output}")
            else:
                print(output)
    else:
        logging.error("No query provided for listing cards.")


@dataclass
class Card:
    name: str
    uuid: str = None
    block: str = None
    set_name: str = None
    collector_number: str = None
    is_double_faced: bool = False
    quantity: int = 1


def parse_card_input(card_input):
    # Match comments starting with "#" or "//"
    if card_input.startswith("#") or card_input.startswith("//"):
        return None
    # Match formats like "1x Card Name (set code) Set Name" or "10 Card Name (set code)"
    match = re.match(r"(\d+)?[x\s]?(.+?)(?:\s*\((.+?)\)\s*(.+)?)?$", card_input)
    if match:
        quantity, card_name, block, set_name = match.groups()
        quantity = int(quantity) if quantity else 1
        card_name = card_name.strip()
        block = block.strip() if block else None
        set_name = set_name.strip() if set_name else None
        return Card(quantity=quantity, name=card_name, block=block, set_name=set_name)
    return Card(name=card_input.strip())


def list_card_names(args, scryfall_api: Scryfall):
    card_inputs = []
    if args.cards:
        card_inputs = args.cards
    elif args.input:
        with open(args.input) as f:
            card_inputs = [line.strip() for line in f]
    else:
        card_inputs = [line.strip() for line in sys.stdin]
    cards = []
    for card_input in card_inputs:
        card = parse_card_input(card_input)
        if not card:
            logging.debug(f"Skipping comment line: {card_input}")
            continue
        if args.dryrun:
            dryrun(f"GET {scryfall_api._endpoint_get_url(card.name, set=card.block)}")
            cards.append(card)
            continue
        response = scryfall_api.cards_named(card.name, set=card.block)
        if response:
            cards.append(response)
            logging.debug(f"{json.dumps(vars(response))}")
        else:
            logging.error(f"Card not found: {card.name}")
            continue
    logging.info(f"Found {len(cards)} cards.")
    return cards


def slugify(card_name):
    card_name = re.sub(r'[/\\<>|"\*\?:]', "_", card_name)
    return card_name


def download_card(card: Card, filename: str, api: Scryfall, face="front"):
    image_data = api.cards_image(card, face=face)
    with open(filename, "wb") as f:
        logging.info(f'Saving "{filename}"')
        f.write(image_data)


def download_cards(args):
    api = Scryfall(server_url=args.server, cache_dir=args.cache)
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)

    path_prefix = f"{args.output}/" if args.output else ""
    downloaded = []

    for card in list_card_names(args, api):
        set_code = f".{card.block.upper()}" if card.block else ""
        filepath = f"{path_prefix}{slugify(card.name)}{IMAGE_FILENAME_FORMAT['front'].format(set_code)}"

        if args.dryrun:
            if os.path.exists(filepath):
                dryrun(f"Already downloaded: {filepath}")
            else:
                dryrun(f"Downloading: {filepath}")
                downloaded.append(card)
            continue

        download_card(card, filepath, api)
        downloaded.append(card)

        if card.is_double_faced:
            filepath = f"{path_prefix}{slugify(card.name)}{IMAGE_FILENAME_FORMAT['back'].format(set_code)}"
            download_card(card, filepath, api, face="back")
            downloaded.append(card)

    logging.info(f"Downloaded {len(downloaded)} cards.")


def main():
    App().run()


if __name__ == "__main__":
    main()
