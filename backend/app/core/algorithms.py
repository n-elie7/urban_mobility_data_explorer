"""Custom data structures used by the analytics API.

This module implements a bounded Min-Heap and a `top_k` helper without
using SQL `ORDER BY ... LIMIT`, `heapq`, or `sorted`.

Algorithm
---------
`top_k(items, k, key)` scans the input once while maintaining a min-heap
of at most `k` elements. Items are added until the heap is full. After
that, a new item replaces the heap root only if its key is larger than
the current minimum. The heap therefore stores the largest `k` items
seen so far.

Pseudo-code:

    top_k(items, k, key):
        heap <- empty
        for item in items:
            if size(heap) < k:
                push(heap, item)
            else if key(item) > key(heap[0]):
                heap[0] <- item
                sift_down(heap, 0)
        return heap sorted descending by key

    push(heap, item):
        append item
        sift_up(last_index)

    sift_up(i):
        while parent > current:
            swap with parent

    sift_down(i):
        while a smaller child exists:
            swap with smallest child

Complexity
----------
Let n = number of items and k = heap size.

    sift_up / sift_down : O(log k)
    top_k time          : O(n log k)
    extra space         : O(k)

Compared to sorting all items (`O(n log n)` time, `O(n)` space), this is
more efficient when k is much smaller than n.
"""

from typing import Callable, Generic, Iterable, List, TypeVar

T = TypeVar("T")


class MinHeap(Generic[T]):
    """Binary min-heap stored in a flat list, ordered by an external key."""

    def __init__(self, key: Callable[[T], float]) -> None:
        self._items: List[T] = []
        self._key = key

    def __len__(self) -> int:
        return len(self._items)

    def peek(self) -> T:
        return self._items[0]

    def push(self, item: T) -> None:
        self._items.append(item)
        self._sift_up(len(self._items) - 1)

    def pop(self) -> T:
        root = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._sift_down(0)
        return root

    def replace_root(self, item: T) -> None:
        """Overwrite the minimum and sift the new value down. O(log k)."""
        self._items[0] = item
        self._sift_down(0)

    def to_sorted_list(self, reverse: bool = True) -> List[T]:
        return sorted(self._items, key=self._key, reverse=reverse)

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent_index = (index - 1) // 2
            if self._key(self._items[parent_index]) <= self._key(self._items[index]):
                break
            self._items[parent_index], self._items[index] = (
                self._items[index],
                self._items[parent_index],
            )
            index = parent_index

    def _sift_down(self, index: int) -> None:
        size = len(self._items)
        while True:
            left_child = 2 * index + 1
            right_child = 2 * index + 2
            smallest = index
            if left_child < size and self._key(self._items[left_child]) < self._key(self._items[smallest]):
                smallest = left_child
            if right_child < size and self._key(self._items[right_child]) < self._key(self._items[smallest]):
                smallest = right_child
            if smallest == index:
                break
            self._items[index], self._items[smallest] = (
                self._items[smallest],
                self._items[index],
            )
            index = smallest


def top_k(items: Iterable[T], k: int, key: Callable[[T], float]) -> List[T]:
    """Return the K items with the largest `key` values, sorted descending.

    Time  : O(n log k) — n scanned items, heap bounded at k
    Space : O(k) — heap never grows past k
    """
    if k <= 0:
        return []

    heap: MinHeap[T] = MinHeap(key=key)
    for item in items:
        if len(heap) < k:
            heap.push(item)
        elif key(item) > key(heap.peek()):
            heap.replace_root(item)
    return heap.to_sorted_list(reverse=True)
