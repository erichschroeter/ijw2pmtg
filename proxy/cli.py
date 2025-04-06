import argparse
import logging
import os
from PIL import Image, ImageOps

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


class App:
    def __init__(self) -> None:
        self.args = None
        self.parser = argparse.ArgumentParser(prog="proxy")
        self.parser.add_argument(
            "-v",
            "--verbosity",
            choices=["critical", "error", "warning", "info", "debug"],
            default="info",
            help="Set the logging verbosity level.",
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
        self.subparsers = self.parser.add_subparsers(dest="command", title="Commands")

        resize_parser = self.subparsers.add_parser(
            "resize", help="Resize images to a specific size."
        )
        resize_parser.add_argument("images", nargs="*", help="The images to resize.")
        resize_parser.add_argument(
            "-s",
            "--size",
            default="745x1040",
            help="The width and height of the resized images.",
        )
        resize_parser.set_defaults(func=resize_images)

        rotate_parser = self.subparsers.add_parser(
            "rotate", help="Rotate images to a specific angle."
        )
        rotate_parser.add_argument("images", nargs="*", help="The images to rotate.")
        rotate_parser.add_argument(
            "-a",
            "--angle",
            default=90.0,
            type=float,
            choices=[Range(-360.0, 360.0)],
            help="The angle to rotate the images (between -360 and 360 degrees).",
        )
        rotate_parser.set_defaults(func=rotate_images)

        stitch_parser = self.subparsers.add_parser(
            "stitch", help="Stitch images together."
        )
        stitch_parser.add_argument(
            "images", nargs="*", help="The images to stitch together."
        )
        stitch_parser.add_argument(
            "-x",
            "--width",
            default=1,
            type=int,
            help="The number of images to stitch together horizontally.",
        )
        stitch_parser.add_argument(
            "-y",
            "--height",
            default=1,
            type=int,
            help="The number of images to stitch together vertically.",
        )
        stitch_parser.add_argument(
            "-o", "--output", default=os.getcwd(), help="The output directory."
        )
        stitch_parser.set_defaults(func=stitch_images)

        redact_parser = self.subparsers.add_parser(
            "redact",
            help="Replace sections of images with black rectangles or other images.",
        )
        redact_parser.add_argument("images", nargs="*", help="The images to redact.")
        redact_parser.add_argument(
            "-s",
            "--size",
            default="745x1040",
            help="The width and height to normalize images to before redacting.",
        )
        redact_parser.add_argument(
            "-r",
            "--region",
            action="append",
            required=True,
            help="Region to redact in format 'x,y,width,height'. Use multiple -r flags for multiple regions.",
            dest="regions",
        )
        redact_parser.add_argument(
            "-i",
            "--replacement-images",
            nargs="*",
            help="Optional images to use instead of black rectangles. Must match number of regions.",
        )
        redact_parser.set_defaults(func=redact_images)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()))
        logging.debug(f"command-line args: {self.args}")
        self.args.func(self.args)


class Range:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __eq__(self, other: object) -> bool:
        return self.min <= float(other) <= self.max

    def __repr__(self) -> str:
        return f"[{self.min}, {self.max}]"


def arrange_images(images, width=1, height=1):
    card_pixel_width = 1040
    card_pixel_height = 745
    grid = Image.new("RGBA", (width * card_pixel_width, height * card_pixel_height))
    image_data = []
    for i, image in enumerate(images):
        img = Image.open(image)
        image_data.append(img)
        grid.paste(img, (i % width * card_pixel_width, i // width * card_pixel_height))
    return grid


def stitch_images(args, cards=None, page_count=0):
    if cards is None:
        cards = args.images

    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
    import math

    max_page_count = math.ceil(len(cards) / (args.width * args.height))
    logging.info(
        f"Arranging {len(cards)} images on page {page_count+1} of {max_page_count} pages of {args.width}x{args.height}"
    )

    cards_per_page = args.width * args.height

    if len(cards) >= cards_per_page:
        # If there are enough images to fill a page, create the page and recurse with the remaining images
        page = arrange_images(cards[:cards_per_page], args.width, args.height)
        grid_filename = os.path.join(
            args.output, f"grid_{args.width}x{args.height}_{page_count+1}.png"
        )
        page.save(grid_filename)
        stitch_images(args, cards[cards_per_page:], page_count + 1)
    elif cards:
        # If there are any leftover images, create a final page with them
        page = arrange_images(cards, args.width, args.height)
        grid_filename = os.path.join(
            args.output, f"grid_{args.width}x{args.height}_{page_count+1}.png"
        )
        page.save(grid_filename)


def stitch_images(args):
    IMG_FILENAME_PREFIX = "_grid"
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
    import math

    max_page_count = math.ceil(len(args.images) / (args.width * args.height))
    logging.info(
        f"Arranging {len(args.images)} images on {max_page_count} pages of {args.width}x{args.height}"
    )
    cards_per_page = args.width * args.height
    cards = []
    page_count = 0
    for img in args.images:
        cards.append(img)
        if len(cards) >= cards_per_page:
            logging.info(f"Arranging {len(cards)} images as {args.width}x{args.height}")
            logging.debug(f"Arranging images: {cards}")
            page = arrange_images(cards, args.width, args.height)
            page_count += 1
            grid_filename = os.path.join(
                args.output,
                f"{IMG_FILENAME_PREFIX}{args.width}x{args.height}_{page_count}.png",
            )
            page.save(grid_filename)
            cards = []
    if cards:  # If there are any cards left over, make a final page
        logging.info(f"Arranging {len(cards)} images as {args.width}x{args.height}")
        logging.debug(f"Arranging images: {cards}")
        page = arrange_images(cards, args.width, args.height)
        page_count += 1
        grid_filename = os.path.join(
            args.output,
            f"{IMG_FILENAME_PREFIX}{args.width}x{args.height}_{page_count}.png",
        )
        page.save(grid_filename)


def rotate_image(image, degrees):
    with Image.open(image) as img:
        image = img.rotate(degrees, expand=True).save(image)
    return image


def rotate_images(args):
    for img in args.images:
        logging.info(f'Rotating by {args.angle}° "{img}"')
        rotate_image(img, args.angle)


def resize_image(image, size=(745, 1040)):
    """
    Keword arguments:
    size -- width x height (e.g. (745, 1040)
    """
    logging.debug(f"Resizing {image} to {size}")
    with Image.open(image) as img:
        image = ImageOps.contain(img, size).save()
    return image


def resize_images(args):
    for img in args.images:
        resize_image(img, args.size)


def redact_images(args):
    # Parse size
    width, height = map(int, args.size.split("x"))

    # Parse regions
    regions = []
    for region in args.regions:
        try:
            x, y, w, h = map(int, region.split(","))
            regions.append((x, y, w, h))
        except ValueError:
            logging.error(
                f"Invalid region format: {region}. Expected 'x,y,width,height'"
            )
            return

    # Validate replacement images if provided
    replacements = []
    if args.replacement_images:
        if len(args.replacement_images) != len(regions):
            raise ValueError(
                "Number of replacement images must match number of regions"
            )
        for img_path in args.replacement_images:
            with Image.open(img_path) as img:
                replacements.append(img.copy())

    for img_path in args.images:
        logging.info(f'Redacting regions in "{img_path}"')
        with Image.open(img_path) as img:
            # Resize to standard size
            img = ImageOps.contain(img, (width, height))

            # Process each region
            for i, (x, y, w, h) in enumerate(regions):
                if replacements and i < len(replacements):
                    # Resize replacement image to fit region
                    replacement = replacements[i].resize((w, h))
                    img.paste(replacement, (x, y))
                else:
                    # Create black rectangle
                    black_rect = Image.new("RGBA", (w, h), (0, 0, 0, 255))
                    img.paste(black_rect, (x, y))

            img.save(img_path)


def main():
    App().run()


if __name__ == "__main__":
    main()
