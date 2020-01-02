"""This module supports puzzles that must check sightlines through grids.

A sightline is a straight line through a symbol grid. It may have a stopping
condition, determined based on the symbol encountered in the grid, which, when
satisfied, results in no further symbols along the line being counted. It may
also have a custom counting or accumulation function.

A sightline always stops when it reaches a point not in the grid. So, if the
grid is not convex, a sightline might stop at a hole in the middle of the
grid. If it is desired that a sightline continues through such holes, the
holes should be treated as part of the grid, e.g., as black cells.
"""

from typing import Callable, TypeVar
from z3 import ArithRef, BoolRef, If  # type: ignore

from .geometry import Point, Vector
from .grids import SymbolGrid


def count_cells(
    symbol_grid: SymbolGrid,
    start: Point,
    direction: Vector,
    count: Callable[[int], ArithRef] = lambda c: 1,
    stop: Callable[[int], BoolRef] = lambda c: False
):
  """Returns a count of cells along a sightline through a grid.

  # Arguments
  symbol_grid (SymbolGrid): The SymbolGrid to check against.
  start (Point): The location of the cell where the sightline should begin.
      This is the first cell checked.
  direction (Vector): The direction to advance to reach the next cell in the
      sightline.
  count (Callable[[int], ArithRef]): A function that accepts a symbol as
      an argument and returns the integer value to add to the count when this
      symbol is encountered. By default, each symbol will count with a value of
      one.
  stop (Callable[[int], BoolRef]): A function that accepts a symbol as
      an argument and returns True if we should stop following the sightline
      when this symbol is encountered. By default, the sightline will continue
      to the edge of the grid.
  """
  return reduce_cells(
      symbol_grid,
      start,
      direction,
      0,
      lambda a, c: a + count(c),
      lambda a, c: stop(c)
  )


Accumulator = TypeVar("Accumulator")


def reduce_cells(  # pylint: disable=R0913
    symbol_grid: SymbolGrid,
    start: Point,
    direction: Vector,
    initializer: Accumulator,
    accumulate: Callable[[Accumulator, int], Accumulator],
    stop: Callable[[Accumulator, int], BoolRef] = lambda a, c: False,
):
  """Returns a computation of a sightline through a grid.

  # Arguments
  symbol_grid (SymbolGrid): The SymbolGrid to check against.
  start (Point): The location of the cell where the sightline should begin.
      This is the first cell checked.
  direction (Vector): The direction to advance to reach the next cell in the
      sightline.
  initializer (Accumulator): The initial value for the accumulator.
  accumulate (Callable[[Accumulator, int], Accumulator]): A function that
      accepts an accumulated value and a symbol as arguments, and returns a new
      accumulated value. This function is used to determine a new accumulated
      value for each cell along the sightline, based on the accumulated value
      from the previously encountered cells as well as the symbol in the
      current cell.
  stop (Callable[[Accumulator, int], BoolRef]): A function that accepts an
      accumulated value and a symbol as arguments, and returns True if we
      should stop following the sightline when this symbol is encountered. By
      default, the sightline will continue to the edge of the grid.
  """
  stop_terms = []
  acc_terms = [initializer]
  p = start
  while p in symbol_grid.grid:
    cell = symbol_grid.grid[p]
    acc_term = accumulate(acc_terms[-1], cell)
    acc_terms.append(acc_term)
    stop_terms.append(stop(acc_term, cell))
    p = p.translate(direction)
  expr = acc_terms.pop()
  for stop_term, acc_term in zip(reversed(stop_terms), reversed(acc_terms)):
    expr = If(stop_term, acc_term, expr)
  return expr
