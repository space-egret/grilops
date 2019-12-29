"""Castle Wall solver example.

Example puzzle can be found at
https://www.gmpuzzles.com/blog/castle-wall-rules-and-info/.
"""

from z3 import If, Or

import grilops
from grilops.loops import I, O, LoopSymbolSet, LoopConstrainer
import grilops.sightlines
from grilops import Point, Vector


HEIGHT, WIDTH = 7, 7

# Map from (y, x) location of each given cell to:
#     whether the cell is inside or outside of the loop
#     the number of loop segments in the given direction
#     the given direction (+/-1 y, +/-1 x)
GIVENS = {
    (1, 5): (I, 1, (1, 0)),
    (2, 1): (I, 0, (-1, 0)),
    (2, 3): (O, None, None),
    (3, 3): (O, 2, (0, -1)),
    (4, 3): (O, None, None),
    (4, 5): (I, 2, (0, -1)),
    (5, 1): (I, 3, (0, 1)),
}

SYM = LoopSymbolSet()
SYM.append("EMPTY", " ")

# The set of symbols to count as loop segments when traveling in each direction.
DIRECTION_SEGMENT_SYMBOLS = {
    (-1, 0): [SYM.NS, SYM.NE, SYM.NW],
    (0, 1): [SYM.EW, SYM.NE, SYM.SE],
    (1, 0): [SYM.NS, SYM.SE, SYM.SW],
    (0, -1): [SYM.EW, SYM.SW, SYM.NW],
}


def main():
  """Castle Wall solver example."""
  locations = grilops.get_rectangle_locations(HEIGHT, WIDTH)
  sg = grilops.SymbolGrid(locations, SYM)
  lc = LoopConstrainer(sg, single_loop=True)

  for (y, x), (io, expected_count, direction) in GIVENS.items():
    p = Point(y, x)
    # Constrain whether the given cell is inside or outside of the loop. This
    # also prevents these cells from containing loop symbols themselves.
    sg.solver.add(lc.inside_outside_grid[p] == io)

    if expected_count is not None and direction is not None:
      # Count and constrain the number of loop segments in the given direction.
      segment_symbols = DIRECTION_SEGMENT_SYMBOLS[direction]
      dy, dx = direction
      actual_count = grilops.sightlines.count_cells(
          sg, p, Vector(dy, dx),
          lambda c: If(Or(*[c == s for s in segment_symbols]), 1, 0)
      )
      sg.solver.add(actual_count == expected_count)

  def show_cell(p, _):
    if (p.y, p.x) in GIVENS:
      if GIVENS[(p.y, p.x)][0] == I:
        return chr(0x25AB)
      if GIVENS[(p.y, p.x)][0] == O:
        return chr(0x25AA)
    return None

  if sg.solve():
    sg.print(show_cell)
    print()
    if sg.is_unique():
      print("Unique solution")
    else:
      print("Alternate solution")
      sg.print(show_cell)
  else:
    print("No solution")


if __name__ == "__main__":
  main()
