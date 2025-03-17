from abc import ABC, abstractmethod
import argparse
import json
import logging
import os
import re
import sys
from .api import Scryfall
from .parsing import CardParserFactory

#region Command line parsing  # noqa


class ColorLogFormatter(logging.Formatter):
    '''
    Custom formatter that changes the color of logs based on the log level.
    '''

    grey = "\x1b[38;20m"
    green = "\u001b[32m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\u001b[34m"
    cyan = "\u001b[36m"
    reset = "\x1b[0m"

    timestamp = '%(asctime)s - '
    loglevel = '%(levelname)s'
    message = ' - %(message)s'

    FORMATS = {
        logging.DEBUG:    timestamp + blue + loglevel + reset + message,
        logging.INFO:     timestamp + green + loglevel + reset + message,
        logging.WARNING:  timestamp + yellow + loglevel + reset + message,
        logging.ERROR:    timestamp + red + loglevel + reset + message,
        logging.CRITICAL: timestamp + bold_red + loglevel + reset + message
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def _init_logger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = ColorLogFormatter()
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class RawTextArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass


#endregion Command line parsing  # noqa


def dryrun(msg):
    green = "\u001b[32m"
    reset = "\x1b[0m"
    print(f'{green}DRYRUN{reset}: {msg}')


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
        # TODO [ ] refactor to support input format "Card Name (Set Name)"
        # TODO [ ] refactor to support input format "Card Name (Set Name) collector-number"
        # TODO [ ] refactor to support input format "Card Name e:setname cn:number b:block"
        self.parser = argparse.ArgumentParser(prog='scryfall')
        self.parser.add_argument('-v', '--verbosity',
                                 choices=['critical', 'error', 'warning', 'info', 'debug'],
                                 default='info',
                                 help='Set the logging verbosity level.')
        self.parser.add_argument('--server', default='https://api.scryfall.com', help="The Scryfall server URL.")
        self.parser.add_argument('--dryrun', default=False, help='Dry run network and filesystem operations.', action='store_true')
        self.parser.add_argument('-i', '--input',
                                 help='A file of card names. Alternatively, a newline-separated list of card names can be provided via stdin.')
        self.parser.add_argument('-o', '--output', default=os.getcwd(), help='The output directory.')
        self.parser.add_argument('-l', '--list', action='store_true', default=True, help='Searches for cards based on query. Does not download them.')
        self.parser.add_argument('--json', action='store_true', help='Output results in JSON format.')
        self.parser.add_argument('--with-block', action='store_true', help='Include 3-letter block code when listing cards. e.g. ZNR for Zendikar Rising.')
        self.parser.add_argument('--with-cn', action='store_true', help='Include collector number when listing cards. e.g. 1/280.')
        self.parser.add_argument('--with-set', action='store_true', help='Include set name when listing cards. e.g. Zendikar Rising.')
        self.parser.add_argument('cards', nargs='*', help='Names of Magic the Gathering (MTG) cards.')
        self.parser.set_defaults(func=self.default_func)

    def default_func(self, args):
        if args.list:
            list_cards(args)
        else:
            download_cards(args)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()))
        logging.debug(f'command-line args: {self.args}')
        self.args.func(self.args)


def list_cards(args):
    api = Scryfall(args.server)
    query = ' '.join(args.cards) if args.cards else ''
    if query:
        response = api.cards_search(query)
        if response:
            logging.info(f'Found {len(response.json()["data"])} cards.')
            response = response.json()
            if args.json:
                output = json.dumps(response, indent=2)
            elif args.with_block and args.with_cn and args.with_set:
                output = '\n'.join([f"{card['name']} ({card['set']}) {card['collector_number']} {card['set_name']}" for card in response['data']])
            elif args.with_block and args.with_cn:
                output = '\n'.join([f"{card['name']} ({card['set']}) {card['collector_number']}" for card in response['data']])
            elif args.with_block:
                output = '\n'.join([f"{card['name']} ({card['set']})" for card in response['data']])
            else:
                output = '\n'.join([card['name'] for card in response['data']])
            if args.output and not os.path.isdir(args.output):
                with open(args.output, 'w') as f:
                    f.write(output)
                logging.info(f'Results saved to {args.output}')
            else:
                print(output)
    else:
        logging.error('No query provided for listing cards.')


def list_card_names(args):
    if args.cards:
        cards = args.cards
    elif args.input:
        factory = CardParserFactory()
        parser = factory.create_parser(args.input)
        logging.debug(f"Using parser {parser.__class__.__name__}")
        cards = parser.parse_cards(args.input)
    else:
        cards = [line.strip() for line in sys.stdin]
    logging.info(f'Found {len(cards)} cards.')
    return cards


def slugify(card_name):
    card_name = re.sub(r'[/\\<>|"\*\?:]', '_', card_name)
    return card_name


def download_image(file_path, url):
    pass


def download_cards(args):
    api = Scryfall(args.server)
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
    path_prefix = f'{args.output}/' if args.output else ''
    for card_name in list_card_names(args):
        if args.dryrun:
            dryrun(f'Downloading {card_name}')
            continue
        response = api.cards_named(card_name)
        if response:
            response = response.json()
            logging.debug(f'{json.dumps(response)}')
            result = api.cards_image(response['id'])
            png = f'{path_prefix}{slugify(card_name)}.png'
            if len(response['card_faces']) > 1:
                png = f'{path_prefix}{slugify(card_name)}_front.png'
                with open(png, 'wb') as f:
                    logging.info(png)
                    for chunk in result.iter_content(chunk_size=1024):
                        f.write(chunk)
                result = api.cards_image(response['id'], face='back')
                png = f'{path_prefix}{slugify(card_name)}_back.png'
            png = f'{path_prefix}{slugify(card_name)}.png'
            with open(png, 'wb') as f:
                logging.info(png)
                for chunk in result.iter_content(chunk_size=1024):
                    f.write(chunk)


def main():
    App().run()


if __name__ == '__main__':
    main()
