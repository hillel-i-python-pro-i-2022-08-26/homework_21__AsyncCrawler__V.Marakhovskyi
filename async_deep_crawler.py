import time
from urllib.parse import urljoin
import asyncio
import logging
import urllib.error
import urllib.parse
import aiohttp
import bs4


class CustomFormatter(logging.Formatter):

    grey = "\x1b[0;37m"
    light_blue = "\x1b[1;36m"
    yellow = "\x1b[1;33m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[1;32m"
    reset = "\x1b[0m"

    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# create logger
logger = logging.getLogger("AsyncCrawler")
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)



async def fetch(url, session: aiohttp.ClientSession, **kwargs):  # ОДНА ССЫЛКА
    response = await session.request(method="GET", url=url, **kwargs)
    html_text = await response.text()
    return html_text

async def parse(url: str, session: aiohttp.ClientSession, **kwargs) -> list:
    """Find HREFs in the HTML of `url`."""                      # С ОДНОЙ ССЫЛКИ ПОЛУЧАЕМ ВНУТРЕННИЙ СЭТ
    found = set()
    try:
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
        logger.exception(
            "Non-aiohttp exception occured:  %s", getattr(e, "__dict__", {})
        )
        return list(found)
    else:
        soup = bs4.BeautifulSoup(markup=html, features='html.parser')
        for link_element in soup.find_all('a'):
            link = link_element.get('href')
            try:
                abslink = urllib.parse.urljoin(url, link)
            except (urllib.error.URLError, ValueError):
                logger.exception("Error parsing URL: %s", link)
            else:
                found.add(abslink)
    logger.info("Found %d links for %s", len(found), url)
    return list(found)

async def work(queue, initial_urls, session: aiohttp.ClientSession, depth, semaphore):
    async with semaphore:
        await queue.put(initial_urls)
        logger.warning(f'------Diving into the first depth. Desired depth: {depth}------')
        processed_urls = 0
        all_found_links = []
        while depth != 0:
            next_depth_set = []
            current_depth_set = await queue.get()
            for url in current_depth_set:
                new_links = await parse(url=url, session=session)           # Get a set of found links
                processed_urls += 1
                next_depth_set += new_links
                all_found_links.extend(iter(new_links))   # Sourcery suggestion
            await queue.put(set(next_depth_set))
            depth -= 1
            logger.warning(f'[Transition to the next depth. Remaining depth: {depth}]')
            logger.warning(f'Total processed urls: {processed_urls}')
            logger.warning(f'Total found links: {len(all_found_links)}')
        logger.debug(f'<<<Required depth [{DEPTH}] reached>>>')
        logger.debug(f'Total processed urls: {processed_urls}')
        logger.debug(f'Total found links: {len(all_found_links)}')


async def main():
    # create the shared queue
    queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(5)
    async with aiohttp.ClientSession() as session:
        await asyncio.create_task(work(queue, initial_urls, session=session, depth=DEPTH, semaphore=semaphore))
    # wait for all items to be processed
    # await queue.join()



if __name__ == "__main__":
    DEPTH = 2
    initial_urls = ['https://www.godina-worldwide.com/#', 'https://example.com']
    logger.debug("Initializing a crawling....")
    # start the asyncio program
    start = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    logger.debug(f"Program completed in {elapsed:0.5f} seconds.")