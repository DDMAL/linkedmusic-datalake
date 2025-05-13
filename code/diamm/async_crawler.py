"""
This script is an asynchronous web crawler that fetches JSON data from the DIAMM website.
It is highly recommended to use the async version of the crawler instead of the sync version.
It is set up with the assumption that you will pipe stdout o a logfile.
"""

import os
import asyncio
import aiohttp
import aiofiles
import json
import re
import sys

BASE_URL = "https://www.diamm.ac.uk/"
BASE_PATH = "../../data/diamm/"

REGEX_MATCH = re.compile(r"https:\/\/www\.diamm\.ac\.uk\/([a-z]+)\/([0-9]+)\/?")

REVISIT = False

MAX_CONCURRENT_VISITS = 8
MAX_CONCURRENT_WRITES = 2

BAD_PAGES = [
    "documents",
    "cover",
    "admin",
    "cms"
]

visited = set() # tuple (str, str) representing (type, id), example is ("compositions", "117")

to_visit = [("sources", "117")]  # Starting point

def print_stdout_stderr(message):
    print(message)
    print(message, file=sys.stderr)

async def fetch(session, url):
    try:
        async with session.get(url, timeout=10, headers={"Accept": "application/json"}) as response:
            if response.status != 200:
                print(f"Failed to fetch {url}: {response.status}")
                return None
            if response.headers["Content-Type"] != "application/json":
                print(f"Unexpected content type for {url}: {response.headers['Content-Type']}")
                return None
            print(f"Fetched {url}")
            return await response.text()
    except aiohttp.ClientError as e:
        print(f"Exception while trying to parse {url}: {e}")
        return None
    except asyncio.TimeoutError:
        print_stdout_stderr(f"Timeout while trying to fetch {url}")
        return None
    except Exception as e:
        print(f"Unexpected exception while trying to fetch {url}: {e}")
        return None

async def visit_worker(name, session, visit_queue, write_queue, visited):
    print(f"Visit worker {name} started")
    try:
        while True:
            page = await visit_queue.get()
            if page is None:
                break
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
            received = await fetch(session, url)
            if received is None:
                visit_queue.task_done()
                continue
            try:
                data = json.loads(received)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON for {url}")
                visit_queue.task_done()
                continue
            text = json.dumps(data, ensure_ascii=False, indent=4)
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
    except Exception as e:
        print_stdout_stderr(f"Unexpected exception in visit worker {name}: {e}")
    finally:
        print_stdout_stderr(f"Visit worker {name} finished")

async def write_worker(name, write_queue):
    print(f"Write worker {name} started")
    try:
        while True:
            page, data = await write_queue.get()
            os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
            async with aiofiles.open(os.path.join(BASE_PATH, page[0], f"{page[1]}.json"), "w", encoding="utf-8") as f:
                await f.write(data)
                print(f"Saved {page[0]}/{page[1]}.json")
            write_queue.task_done()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print_stdout_stderr(f"Unexpected exception in write worker {name}: {e}")
    finally:
        while not write_queue.empty():
            page, data = await write_queue.get()
            os.makedirs(os.path.join(BASE_PATH, page[0]), exist_ok=True)
            async with aiofiles.open(os.path.join(BASE_PATH, page[0], f"{page[1]}.json"), "w", encoding="utf-8") as f:
                await f.write(data)
                print(f"Saved {page[0]}/{page[1]}.json")
            write_queue.task_done()
        print_stdout_stderr(f"Write worker {name} finished")

async def main(to_visit, visited):
    visit_queue = asyncio.Queue()
    write_queue = asyncio.Queue()
    for item in to_visit:
        await visit_queue.put(item)
    
    async with aiohttp.ClientSession() as session:
        crawl_tasks = [
            asyncio.create_task(visit_worker(f"crawl-{i}", session, visit_queue, write_queue, visited))
            for i in range(MAX_CONCURRENT_VISITS)
        ]
        write_tasks = [
            asyncio.create_task(write_worker(f"write-{i}", write_queue))
            for i in range(MAX_CONCURRENT_WRITES)
        ]
        await visit_queue.join()
        await write_queue.join()

        await asyncio.gather(*(crawl_tasks+write_tasks), return_exceptions=True)

        for task in crawl_tasks+write_tasks:
            task.cancel()

if __name__ == "__main__":
    asyncio.run(main(to_visit, visited))