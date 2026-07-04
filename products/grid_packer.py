from typing import List, Tuple, Optional
from products.models import Product


SIZE_CELLS = {
    'featured': (2, 2),
    'wide': (2, 1),
    'wide-image': (2, 1),
    'tall': (1, 2),
    'tall-image': (1, 2),
    'standard': (1, 1),
}


def _cell_size(bento_size: str, columns: int) -> Optional[Tuple[int, int]]:
    if bento_size == 'hero':
        return (columns, 1)
    return SIZE_CELLS.get(bento_size)


def pack_products(
    products: List[Product],
    columns: int = 8,
    filler_pool: Optional[List[Product]] = None,
) -> List[Product]:
    """
    Pack a ranked list of products into the smallest-height grid with the given
    number of columns using a skyline heuristic.

    - Input order is treated as business priority (already sorted by rating,
      review_count, etc. by the caller). We do NOT reorder the list.
    - Each product is placed in the first available position that fits,
      scanning left-to-right and top-to-bottom.
    - Optional `filler_pool` items are placed afterward into remaining empty
      cells. Each filler can be any `bento_size` that physically fits in the
      available space, not only 1x1. This minimizes visual gaps.
    - Returns placements sorted by visual reading order (top-left, then
      left-to-right by row) while preserving relative priority ties.
    """
    if columns <= 0 or not products:
        return list(products)

    items: List[Tuple[int, int, Product]] = []
    for p in products:
        size = _cell_size(getattr(p, 'bento_size', 'standard'), columns)
        if size:
            w, h = size
            if w <= columns:
                items.append((w, h, p))

    if not items:
        return []

    # Sort by decreasing area first to achieve denser packing, while keeping
    # business ranking as tie-breaker so higher-rated items move ahead when
    # they share the footprint.
    items.sort(key=lambda x: (
        -x[0] * x[1],
        -getattr(x[2], 'average_rating', 0),
        -getattr(x[2], 'review_count', 0),
        getattr(x[2], 'created_at', None) or 0,
    ))

    skyline = [0] * columns
    placements: List[Tuple[int, int, int, int, Product]] = []

    for w, h, product in items:
        best_row = None
        best_start = None
        best_height = None

        for start in range(columns - w + 1):
            row = max(skyline[start:start + w])
            fits = all(skyline[c] <= row for c in range(start, start + w))
            if fits:
                height = row + h
                if best_height is None or height < best_height:
                    best_height = height
                    best_row = row
                    best_start = start

        if best_start is not None:
            placements.append((best_start, best_row, w, h, product))
            for c in range(best_start, best_start + w):
                skyline[c] = best_row + h

    # Fill remaining empty cells with any filler product that fits
    if filler_pool:
        occupied: set = set()
        row_max = 0
        for start, row, w, h, product in placements:
            row_max = max(row_max, row + h)
            for r in range(row, row + h):
                for c in range(start, start + w):
                    occupied.add((r, c))

        filler_used = set()
        for r in range(row_max):
            for c in range(columns):
                if (r, c) in occupied:
                    continue
                for idx, filler in enumerate(filler_pool):
                    if idx in filler_used:
                        continue
                    size = _cell_size(getattr(filler, 'bento_size', 'standard'), columns)
                    if not size:
                        continue
                    w, h = size
                    if w > columns:
                        continue
                    fits = True
                    for rr in range(r, r + h):
                        for cc in range(c, c + w):
                            if (rr, cc) in occupied:
                                fits = False
                                break
                        if not fits:
                            break
                    if fits:
                        placements.append((c, r, w, h, filler))
                        filler_used.add(idx)
                        for rr in range(r, r + h):
                            for cc in range(c, c + w):
                                occupied.add((rr, cc))
                        break

    placements.sort(key=lambda x: (x[1], x[0]))
    return placements
