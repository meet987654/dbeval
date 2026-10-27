import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import same

g = lambda *a, **k: same(*a, **k)

assert g([(5,)], [(5.0,)])
assert g([(Decimal("258794.23"),)], [(258794.2299999,)])
assert g([("starter",)], [("starter", 748)])                 # extra column is fine
assert not g([("starter",)], [("growth", 748)])
assert g([("a", 1), ("b", 2)], [(2, "b"), (1, "a")])         # order of rows and columns ignored
assert not g([("a", 1), ("b", 2)], [("a", 2), ("b", 1)])     # values must line up
assert not g([(1,), (2,)], [(1,)])                           # row counts differ
assert g([(1,), (2,)], [(2,), (1,)])
assert not g([(1,), (2,)], [(2,), (1,)], ordered=True)       # ranking matters when asked
assert g([("2026-07-01",)], [("2026-07-01",)])
assert g([(60,)], [("60",)])
print("compare.py: all tests passed")
