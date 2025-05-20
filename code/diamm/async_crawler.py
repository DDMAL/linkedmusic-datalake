"""
This script is an asynchronous web crawler that fetches JSON data from the DIAMM website.
It is highly recommended to use the async version of the crawler instead of the sync version.
The script will output to a logfile in the working directory, and will also print errors to stderr.
Change the file handler to log to a different file if needed.
If you want to revisit pages that have already been visited by previous executions of the crawler,
set the REVISIT variable to True. This will not prevent it from visiting the same page twice during an execution.
The script is set to rate limit itself to 40 requests per second, or 1 request every 25ms on average,
to avoid overwhelming the server.
"""

import os
import asyncio
import aiohttp
import aiofiles
import json
import re
import logging
from aiolimiter import AsyncLimiter

BASE_URL = "https://www.diamm.ac.uk/"
BASE_PATH = "../../data/diamm/raw/"

# Regex pattern to match DIAMM URLs, and capture the type and ID
REGEX_MATCH = re.compile(r"https:\/\/www\.diamm\.ac\.uk\/([a-z]+)\/([0-9]+)\/?")

# Set this to True if you want to revisit pages visited during previous executions of the crawler
REVISIT = False

MAX_CONCURRENT_VISITS = 8
MAX_CONCURRENT_WRITES = 2
RATE_LIMIT = 40 # 40 requests per second, or 1 requests every 25ms on average

# These pages will be ignored, and neither visited nor saved
BAD_PAGES = [
    "documents",
    "cover",
    "admin",
    "cms",
    "authors",
]

# These pages will be visited and scraped, but not saved to disk
LOAD_DONT_SAVE = [
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

visited = set() # tuple (str, str) representing (type, id), example is ("compositions", "117")

to_visit = [("sources", "117")]  # Starting point

async def fetch(session, url, limiter):
    """
    Fetches the content of a URL using an aiohttp session.
    Returns None if there is an error or if the content type is not JSON.
    """
    try:
        async with limiter:
            async with session.get(url, timeout=10, headers={"Accept": "application/json"}) as response:
                if response.status != 200:
                    logger.warning("Failed to fetch %s: %d", url, response.status)
                    return None
                if response.headers["Content-Type"] != "application/json":
                    logger.warning("Unexpected content type for %s: %s", url, response.headers['Content-Type'])
                    return None
                logger.info("Fetched %s", url)
                return await response.text()
    except aiohttp.ClientError:
        logger.error("Exception while trying to parse %s", url, exc_info=True)
        return None
    except asyncio.TimeoutError:
        logger.error("Timeout while trying to fetch %s", url, exc_info=True)
        return None
    except Exception:
        logger.critical("Unexpected exception while trying to fetch %s", url, exc_info=True)
        return None

async def visit_worker(name, session, visit_queue, write_queue, visited, limiter):
    """
    Worker function that fetches pages from the DIAMM website, schedules them for writing,
    and adds new pages to the visit queue.
    """
    logger.info("Visit worker %s started", name)
    try:
        while True:
            page = await visit_queue.get()
            if page in visited:
                visit_queue.task_done()
                continue
            visited.add(page)
            if not REVISIT:
                if os.path.exists(os.path.join(BASE_PATH, page[0], f"{page[1]}.json")):
                    visited.add(page)
                    visit_queue.task_done()
                    continue
            url = f"{BASE_URL}{page[0]}/{page[1]}/"
            received = await fetch(session, url, limiter)
            if received is None:
                visit_queue.task_done()
                continue
            try:
                data = json.loads(received)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON for %s", url)
                visit_queue.task_done()
                continue
            text = json.dumps(data, ensure_ascii=False, indent=4)
            if page[0] not in LOAD_DONT_SAVE:
                await write_queue.put((page, text))
            matches = REGEX_MATCH.findall(text)
            for match in matches:
                if match[0] in BAD_PAGES:
                    continue
                if (match[0], match[1]) not in visited:
                    await visit_queue.put((match[0], match[1]))
            visit_queue.task_done()
    except asyncio.CancelledError:
        pass
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
            async with aiofiles.open(os.path.join(BASE_PATH, page[0], f"{page[1]}.json"), "w", encoding="utf-8") as f:
                await f.write(data)
                logger.info("Saved %s/%s.json", page[0], page[1])
            write_queue.task_done()
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.critical("Unexpected exception in write worker %s", name, exc_info=True)
    finally:
        while not write_queue.empty():
            page, data = await write_queue.get()
            os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
            async with aiofiles.open(os.path.join(BASE_PATH, page[0], f"{page[1]}.json"), "w", encoding="utf-8") as f:
                await f.write(data)
                logger.info("Saved %s/%s.json", page[0], page[1])
            write_queue.task_done()
        logger.info("Write worker %s finished", name)

async def main(to_visit, visited):
    """
    Main function that initializes the visit and write queues, creates the worker tasks,
    and waits for all tasks to complete.
    """
    visit_queue = asyncio.Queue()
    write_queue = asyncio.Queue()
    for item in to_visit:
        await visit_queue.put(item)

    limiter = AsyncLimiter(RATE_LIMIT, 1)  # Rate limiter to control the number of requests per second

    async with aiohttp.ClientSession() as session:
        # Start the workers
        crawl_tasks = [
            asyncio.create_task(visit_worker(f"crawl-{i}", session, visit_queue, write_queue, visited, limiter))
            for i in range(MAX_CONCURRENT_VISITS)
        ]
        write_tasks = [
            asyncio.create_task(write_worker(f"write-{i}", write_queue))
            for i in range(MAX_CONCURRENT_WRITES)
        ]

        # Wait for the queues to be empty
        await visit_queue.join()
        await write_queue.join()

        # Cancel the workers once the queues are empty
        for task in crawl_tasks+write_tasks:
            task.cancel()

        # Wait for all tasks to finish
        await asyncio.gather(*crawl_tasks, *write_tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main(to_visit, visited))
