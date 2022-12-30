import time
import asyncio
import logging
import urllib.error
import urllib.parse
import aiohttp
import bs4
import pathlib
import aiofiles

# Create paths for writing into a file
here = pathlib.Path(__file__).parent  # get current directory
outpath = here.joinpath("output")  # create "output" subdirectory
outfile = outpath.joinpath("outfile.txt")  # create "outfile.txt" file in "output" subdirectory

# Formatting logger
class CustomFormatter(logging.Formatter):
    # define colors for log levels
    grey = "\x1b[0;37m"
    light_blue = "\x1b[1;36m"
    yellow = "\x1b[1;33m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[1;32m"
    reset = "\x1b[0m"

    # log message format
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    # mapping of log levels to log message formats
    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Create logger
logger = logging.getLogger("AsyncCrawler")
logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


async def fetch(url, session: aiohttp.ClientSession, **kwargs) -> str:
    """Get HTML-text from the url."""
    response = await session.request(method="GET", url=url, **kwargs)
    response.raise_for_status()
    html_text = await response.text()
    return html_text


async def parse(url: str, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, **kwargs) -> list:
    """Find HREFs in the HTML of `url`."""
    found = set()  # get rid of duplicates initially
    try:
        async with semaphore:
            html = await fetch(url=url, session=session, **kwargs)
    except (
        aiohttp.ClientError,
        aiohttp.http_exceptions.HttpProcessingError,
    ) as e:
        logger.error(
            "aiohttp exception for %s [%s]: %s",
            url,
            getattr(e, "status", None),
            getattr(e, "message", None),
        )
        return list(found)
    except Exception as e:
        logger.exception("Non-aiohttp exception occured:  %s", getattr(e, "__dict__", {}))
        return list(found)
    else:
        soup = bs4.BeautifulSoup(markup=html, features="html.parser")
        for link_element in soup.find_all("a"):
            link = link_element.get("href")
            try:
                abslink = urllib.parse.urljoin(url, link)
            except (urllib.error.URLError, ValueError):
                logger.exception("Error parsing URL: %s", link)
            else:
                found.add(abslink)
    logger.info("Found %d links for %s", len(found), url)
    return list(found)  # convert set to list for easier further processing


async def write_current_depth(file, depth: int) -> None:
    """Write the current crawling depth to `file`."""
    async with aiofiles.open(file, "a") as f:
        await f.write(f"\nCurrent depth is {DEPTH - depth + 1}.\n")


async def write_processed_urls(file, url: list) -> None:
    """Write the processed URLS to `file`."""
    async with aiofiles.open(file, "a") as f:
        await f.write(f"\nProcessed URL:\n {url}")


async def write_found_links(file, urls: list) -> None:
    """Write the found LINKS from `processed URLS` to `file`."""
    async with aiofiles.open(file, "a") as f:
        await f.write("\nFound Links:\n")
        for url in urls:
            await f.write(f"{url}\n")


async def work(
    queue: asyncio.Queue,
    initial_urls: list,
    session: aiohttp.ClientSession,
    depth: int,
    semaphore: asyncio.Semaphore,
    limit: int,
) -> None:
    """Main function which represent a queue. Here is all actions happens."""
    await queue.put(initial_urls)
    logger.warning(f"------Diving into the first depth. Desired depth: {depth}------")
    processed_urls = []
    all_found_links = []
    exitFlag = False
    while depth != 0:
        next_depth_links = []
        await write_current_depth(file=outfile, depth=depth)
        current_depth_links = await queue.get()
        for url in current_depth_links:
            new_links = await parse(
                url=url, session=session, semaphore=semaphore
            )  # Get a set of found links without duplicates
            if len(processed_urls) < limit:
                processed_urls.append(url)
                await write_processed_urls(file=outfile, url=url)
                next_depth_links += new_links
                all_found_links.extend(iter(new_links))
                await write_found_links(file=outfile, urls=new_links)
            else:
                exitFlag = True
                break
        if exitFlag:
            break
        await queue.put(set(next_depth_links))
        depth -= 1
        logger.warning(f"[Transition to the next depth. Remaining depth: {depth}]")
        logger.warning(f"Total processed urls: {len(processed_urls)}")
        logger.warning(f"Total found links: {len(all_found_links)}")
    logger.debug(f"<<<Depth [{DEPTH - depth}] reached>>>")
    logger.debug(f"Total found links: {len(all_found_links)}")
    logger.debug(f"Total processed urls: {len(processed_urls)}")
    logger.debug(f"All links was written to: {outfile}")


async def main():
    # Create the shared queue
    queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(10)
    async with aiohttp.ClientSession() as session:
        await asyncio.create_task(
            work(
                queue=queue,
                initial_urls=initial_urls,
                session=session,
                depth=DEPTH,
                semaphore=semaphore,
                limit=MAX_PROCESSED_URLS,
            )
        )


if __name__ == "__main__":
    DEPTH = 2
    MAX_PROCESSED_URLS = 30
    initial_urls = ["https://en.wikipedia.org/wiki/Main_Page", "https://example.com"]
    logger.debug("Initializing a crawling....")
    start = time.perf_counter()
    # Start the asyncio program (entry-point)
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    logger.debug(f"Program completed in {elapsed:0.5f} seconds.")
