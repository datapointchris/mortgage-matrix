import pytest
from mortgage_matrix.mortgage import Mortgage

m = Mortgage(purchase_price=150_000, percent_down=20, interest_rate=.05, months=360)

m.print_summary()

