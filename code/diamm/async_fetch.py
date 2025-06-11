"""
This script is an asynchronous web crawler that fetches JSON data from the DIAMM website.
It will use the search endpoint to get a list of all pages, and then fetch each page's data.
It will also scan every page for links to cities, countries, and regions,
and add those to the visit queue as well.

It is highly recommended to use the async version of the crawler instead of the sync version.

The script will output to a logfile in the working directory, and will also print errors to stderr.
Change the file handler to log to a different file if needed.

If you want to revisit pages that have already been visited by previous executions of the crawler,
set the REVISIT variable to True. This will not prevent it from visiting the same page twice during an execution.

The script is rate limited to 10 requests per second for the main pages,
and 1 request per second for the search endpoint, to avoid overwhelming the server.

The script implements retry logic for requests that fail due to network issues or timeouts.
The script will retry requests up to 3 times before giving up, waiting 10 seconds between retries.
"""

import os
import json
import re
import logging
import asyncio
import aiohttp
import aiofiles
from aiolimiter import AsyncLimiter
from utils import MultipleLimiters, NotifyingQueue


BASE_URL = "https://www.diamm.ac.uk/"
BASE_SEARCH_URL = f"{BASE_URL}search/?type=all"
BASE_PATH = "../../data/diamm/raw/"

# Regex pattern to match DIAMM URLs, and capture the type and ID
REGEX_MATCH = re.compile(r"https:\/\/www\.diamm\.ac\.uk\/([a-z]+)\/([0-9]+)\/?")
# Regex pattern to match DIAMM URLs for cities and countries only
REGEX_CITY_COUNTRY_REGION = re.compile(
    r"https:\/\/www\.diamm\.ac\.uk\/(cities|countries|regions)\/([0-9]+)\/?"
)

# Set this to True if you want to revisit pages visited during previous executions of the crawler
REVISIT = False

MAX_CONCURRENT_VISITS = 2
MAX_CONCURRENT_WRITES = 2
RATE_LIMIT = 10  # 10 requests per second, or 1 request every 100ms on average
SEARCH_RATE_LIMIT = 1  # 1 request per second
RATE_LIMIT_DELAY = 10  # Delay in seconds before retrying a failed request

# The maximum number of elements in the visit queue before the search worker will pause
MAX_ELEMENTS_IN_VISIT_QUEUE = 200  # 10 pages of data

# These pages will be saved, and the rest will be ignored
SAVED_TYPES = [
    "archives",
    "compositions",
    "organizations",
    "people",
    "sets",
    "sources",
    "cities",
    "countries",
    "regions",
]

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for logging to a file
# This will create a log file named diamm_crawler.log in the current directory
file_handler = logging.FileHandler("diamm_crawler.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# Console handler for logging to stderr
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_format = logging.Formatter("%(levelname)s - %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

logger.info("DIAMM Crawler started")


async def fetch(session, url, limiter, max_retries=3):
    """
    Fetches the content of a URL using an aiohttp session.
    Returns None if there is an error or if the content type is not JSON.
    """
    try:
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                async with limiter:
                    async with session.get(
                        url, timeout=10, headers={"Accept": "application/json"}
                    ) as response:
                        if response.status != 200:
                            logger.warning(
                                "Failed to fetch %s: %d", url, response.status
                            )
                            return None
                        if response.headers["Content-Type"] != "application/json":
                            logger.warning(
                                "Unexpected content type for %s: %s",
                                url,
                                response.headers["Content-Type"],
                            )
                            return None
                        logger.info("Fetched %s", url)
                        return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < max_retries:
                    logger.error(
                        "Error fetching %s (attempt %d/%d): %s %s",
                        url,
                        attempt,
                        max_retries,
                        type(e).__name__,
                        e,
                    )
                    await asyncio.sleep(RATE_LIMIT_DELAY)
                else:
                    raise
    except aiohttp.ClientError:
        logger.error("Exception while trying to parse %s", url, exc_info=True)
        return None
    except asyncio.TimeoutError:
        logger.error("Timeout while trying to fetch %s", url)
        return None
    except Exception:
        logger.critical(
            "Unexpected exception while trying to fetch %s", url, exc_info=True
        )
        return None


async def search_worker(name, session, visit_queue, limiter, search_limiter):
    """
    Worker function that fetches search results from the DIAMM website
    and schedules them for visiting. It uses both the global and
    search rate limiters to control the number of requests per second,
    loading both limiters at once.
    """
    logger.info("Search worker %s started", name)
    url = BASE_SEARCH_URL
    try:
        while url:
            received = await fetch(
                session, url, MultipleLimiters(limiter, search_limiter)
            )
            if received is None:
                logger.error("Failed to fetch search data from %s", url)
                break

            try:
                data = json.loads(received)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON search data for %s", url)
                break

            url = data["pagination"].get("next")

            for res in data["results"]:
                if match := REGEX_MATCH.match(res["url"]):
                    page = (match.group(1), match.group(2))
                    if page[0] not in SAVED_TYPES:
                        continue
                    if not REVISIT and os.path.exists(
                        os.path.join(BASE_PATH, page[0], f"{page[1]}.json")
                    ):
                        continue
                    await visit_queue.wait_below(MAX_ELEMENTS_IN_VISIT_QUEUE)
                    await visit_queue.put(match.group(0))
                else:
                    logger.warning(
                        "Failed to match URL %s in search results", res["url"]
                    )
    except asyncio.CancelledError:
        return
    except Exception:
        logger.critical("Unexpected exception in search worker %s", name, exc_info=True)
    finally:
        logger.info("Search worker %s finished", name)


async def visit_worker(name, session, visited, visit_queue, write_queue, limiter):
    """
    Worker function that fetches pages from the DIAMM website, schedules them for writing,
    and adds new pages to the visit queue.
    """
    logger.info("Visit worker %s started", name)
    try:
        while True:
            url = await visit_queue.get()

            page = REGEX_MATCH.match(url)
            if page is None:
                logger.error("Failed to match URL %s", url)
                visit_queue.task_done()
                continue
            page = (page.group(1), page.group(2))

            if page in visited:
                logger.info("Already visited %s/%s", page[0], page[1])
                visit_queue.task_done()
                continue
            visited.add(page)

            if page[0] not in SAVED_TYPES:
                logger.info("Skipping page %s/%s, not in saved types", page[0], page[1])
                visit_queue.task_done()
                continue

            received = await fetch(session, url, limiter)
            if received is None:
                logger.warning("Failed to fetch data for %s", url)
                visit_queue.task_done()
                continue

            try:
                data = json.loads(received)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON data for %s", url)
                visit_queue.task_done()
                continue

            text = json.dumps(data, ensure_ascii=False, indent=4)
            await write_queue.put((page, text))

            for match in REGEX_CITY_COUNTRY_REGION.finditer(text):
                new_page = (match.group(1), match.group(2))
                if not REVISIT and os.path.exists(
                    os.path.join(BASE_PATH, new_page[0], f"{new_page[1]}.json")
                ):
                    continue
                if new_page not in visited:
                    await visit_queue.put(match.group(0))

            visit_queue.task_done()
    except asyncio.CancelledError:
        return
    except Exception:
        logger.critical("Unexpected exception in visit worker %s", name, exc_info=True)
    finally:
        logger.info("Visit worker %s finished", name)


async def write_worker(name, write_queue):
    """
    Writer worker function that saves the fetched JSON data to files.
    It ensures that all data is written even if the worker is cancelled.
    It also handles any exceptions that occur during the writing process.
    """
    logger.info("Write worker %s started", name)
    try:
        while True:
            page, data = await write_queue.get()
            os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
            async with aiofiles.open(
                os.path.join(BASE_PATH, page[0], f"{page[1]}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                await f.write(data)
                logger.info("Saved %s/%s.json", page[0], page[1])
            write_queue.task_done()
    except asyncio.CancelledError:
        return
    except Exception:
        logger.critical("Unexpected exception in write worker %s", name, exc_info=True)
    finally:
        while not write_queue.empty():
            page, data = await write_queue.get()
            os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
            async with aiofiles.open(
                os.path.join(BASE_PATH, page[0], f"{page[1]}.json"),
                "w",
                encoding="utf-8",
            ) as f:
                await f.write(data)
                logger.info("Saved %s/%s.json", page[0], page[1])
            write_queue.task_done()
        logger.info("Write worker %s finished", name)


async def main(visited):
    """
    Main function that initializes the visit and write queues, creates the worker tasks,
    and waits for all tasks to complete.
    """
    visit_queue = NotifyingQueue()
    write_queue = asyncio.Queue()

    # Rate limiter to control the number of requests per second
    limiter = AsyncLimiter(RATE_LIMIT, 1)
    search_limiter = AsyncLimiter(SEARCH_RATE_LIMIT, 1)

    # Create a TCP connector with a limit on the number of concurrent connections
    # This is to prevent overwhelming the server with too many requests at once
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_VISITS)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Start the workers
        search_task = asyncio.create_task(
            search_worker(
                "search-worker", session, visit_queue, limiter, search_limiter
            )
        )
        crawl_tasks = [
            asyncio.create_task(
                visit_worker(
                    f"visit-{i}", session, visited, visit_queue, write_queue, limiter
                )
            )
            for i in range(MAX_CONCURRENT_VISITS)
        ]
        write_tasks = [
            asyncio.create_task(write_worker(f"write-{i}", write_queue))
            for i in range(MAX_CONCURRENT_WRITES)
        ]

        # Wait for the search worker to finish
        await asyncio.gather(search_task)

        # Wait for the queues to be empty
        await visit_queue.join()
        await write_queue.join()

        # Cancel the workers once the queues are empty
        for task in crawl_tasks + write_tasks:
            task.cancel()

        # Wait for all tasks to finish
        await asyncio.gather(*crawl_tasks, *write_tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main(set()))
