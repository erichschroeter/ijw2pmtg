import argparse
import logging
import os
from PIL import Image, ImageOps

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

class App:
    def __init__(self) -> None:
        self.args = None
        self.parser = argparse.ArgumentParser(prog='proxy')
        self.parser.add_argument('-v', '--verbosity',
                                 choices=['critical', 'error', 'warning', 'info', 'debug'],
                                 default='warning',
                                 help='Set the logging verbosity level.')
        self.parser.add_argument('--dryrun', default=False, help='Dry run network and filesystem operations.', action='store_true')
        self.parser.add_argument('-i', '--input',
                                 help='A file of card names. Alternatively, a newline-separated list of card names can be provided via stdin.')
        self.parser.add_argument('-o', '--output', default=os.getcwd(), help='The output directory.')
        self.subparsers = self.parser.add_subparsers(dest='command', title='Commands')

        resize_parser = self.subparsers.add_parser('resize', help='Resize images to a specific size.')
        resize_parser.add_argument('images', nargs='*', help='The images to resize.')
        resize_parser.add_argument('-s', '--size', default='745x1040', help='The width and height of the resized images.')
        resize_parser.set_defaults(func=resize_images)

        rotate_parser = self.subparsers.add_parser('rotate', help='Rotate images to a specific angle.')
        rotate_parser.add_argument('images', nargs='*', help='The images to rotate.')
        rotate_parser.add_argument('-a', '--angle', default=90.0, type=float, choices=[Range(0.0, 360.0)], help='The angle to rotate the images.')
        rotate_parser.set_defaults(func=rotate_images)

        stitch_parser = self.subparsers.add_parser('stitch', help='Stitch images together.')
        stitch_parser.add_argument('images', nargs='*', help='The images to stitch together.')
        stitch_parser.add_argument('-x', '--width', default=1, type=int, help='The number of images to stitch together horizontally.')
        stitch_parser.add_argument('-y', '--height', default=1, type=int, help='The number of images to stitch together vertically.')
        stitch_parser.set_defaults(func=stitch_images)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()))
        logging.debug(f'command-line args: {self.args}')
        self.args.func(self.args)


class Range:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __eq__(self, other: object) -> bool:
        return self.min <= other <= other.max
    
    def __repr__(self) -> str:
        return f'[{self.min}, {self.max}]'


def arrange_images(images, width=1, height=1):
    logging.debug(f'Arranging {len(images)} as {width}x{height}')
    logging.debug(f'Arranging images: {images}')
    card_pixel_width = 1040
    card_pixel_height = 745
    grid = Image.new('RGBA', (width * card_pixel_width, height * card_pixel_height))
    image_data = []
    for i, image in enumerate(images):
        img = Image.open(image)
        image_data.append(img)
        grid.paste(img, (i % width * card_pixel_width, i // width * card_pixel_height))
    return grid


def stitch_images(args):
    import math
    max_page_count = math.ceil(len(args.images) / (args.width * args.height))
    logging.info(f'Arranging {len(args.images)} images on {max_page_count} pages of {args.width}x{args.height}')
    cards = []
    page_count = 0
    for img in args.images:
        cards.append(img)
        if len(cards) >= max_page_count:
            page = arrange_images(cards, args.width, args.height)
            page_count += 1
            page.save(f'grid_{page_count}.png')
            cards = []
    if cards:  # If there are any cards left over, make a final page
        page = arrange_images(cards, args.width, args.height)
        page_count += 1
        page.save(f'grid_{page_count}.png')


def rotate_image(image, degrees):
    logging.debug(f'Rotating {image} {degrees}°')
    with Image.open(image) as img:
        image = img.rotate(degrees, expand=True).save(image)
    return image


def rotate_images(args):
    for img in args.images:
        rotate_image(img, args.angle)


def resize_image(image, size=(745, 1040)):
    '''
    Keword arguments:
    size -- width x height (e.g. (745, 1040)
    '''
    logging.debug(f'Resizing {image} to {size}')
    with Image.open(image) as img:
        image = ImageOps.contain(img, size).save()
    return image


def resize_images(args):
    for img in args.images:
        resize_image(img, args.size)


def main():
    App().run()


if __name__ == '__main__':
    main()
