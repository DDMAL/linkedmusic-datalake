"""
Module containing utility classes for various scripts for the DIAMM database.
"""

import asyncio


class MultipleLimiters:
    """
    A class that allows multiple rate limiters to be used together.
    It allows you to use `async with` on multiple limiters at once,
    ensuring that all limiters are acquired before entering the context
    and released when exiting the context.
    It also can be reused without having to regenerate the object each time,
    unlike contextlib's asynccontextmanager.
    """

    def __init__(self, *limiters):
        """
        Initialize with multiple rate limiters.
        """
        self.limiters = limiters

    async def __aenter__(self):
        """
        Enter the context manager, acquiring all limiters in order.
        """
        for limiter in self.limiters:
            await limiter.__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager, releasing all limiters in reverse order.
        The exit method will return False to indicate that
        exceptions should not be suppressed.
        """
        for limiter in reversed(self.limiters):
            await limiter.__aexit__(exc_type, exc_value, traceback)
        return False


class NotifyingQueue(asyncio.Queue):
    """
    Subclass of asyncio.Queue that allows waiting for the queue size to drop
    below a certain threshold in a non-blocking way.
    This is useful for scenarios where you want specific calls to the queue
    to wait until the queue size is below a certain threshold,
    such as when you want to ensure that the queue is not too large before
    proceeding with further processing, but still want to allow other tasks to run concurrently.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the NotifyingQueue with an asyncio.Event to notify when the queue size
        drops below a certain threshold.
        The threshold will be set later when needed.
        """
        super().__init__(*args, **kwargs)
        self._event = asyncio.Event()
        self._threshold = None  # Will be set later if needed

    async def put(self, item):
        """
        Put an item into the queue and clear the event if the queue size
        is above the threshold.
        """
        await super().put(item)
        # Item added, maybe queue size increased, so clear the event
        if self._threshold and self.qsize() >= self._threshold:
            self._event.clear()

    async def get(self):
        """
        Get an item from the queue and notify if the queue size is below the threshold.
        If the queue size is below the threshold after removing the item,
        it will set the event to notify waiting tasks.
        """
        item = await super().get()
        # Item removed, maybe queue size decreased, set event if below threshold
        if self._threshold and self.qsize() < self._threshold:
            self._event.set()
        return item

    async def wait_below(self, threshold):
        """
        Set the threshold for the queue size and wait until the queue size
        is below the threshold.
        You should ensure that this method is only called by one task at a time,
        otherwise you will get unexpected results.
        """
        self._threshold = threshold
        # Set event initially if below threshold
        if self.qsize() < threshold:
            self._event.set()
        else:
            self._event.clear()
        await self._event.wait()


class HashableDict:
    """
    A hashable dictionary class that allows for easy comparison and hashing.
    This class is used to store dictionaries in a set, allowing for easy
    removal of duplicate relations.

    It is initialized with a dictionary and provides methods for hashing,
    equality comparison, and representation.

    It also includes a static method to convert an iterable of HashableDict objects
    to a list of dictionaries, which is useful for converting the set of relations
    to a DataFrame.
    """

    def __init__(self, d):
        self.d = dict(d)
        self._frozen = frozenset(self.d.items())

    def __hash__(self):
        return hash(self._frozen)

    def __eq__(self, other):
        return isinstance(other, HashableDict) and self._frozen == other._frozen

    def __repr__(self):
        return f"HashableDict({self.d})"

    @staticmethod
    def to_list_of_dicts(lst):
        """
        Takes an iterable object (set, list, etc) containing HashableDict
        objects and returns a list of dictionaries.
        This is useful for converting the set of relations to a DataFrame.
        """
        return [d.d for d in lst]
