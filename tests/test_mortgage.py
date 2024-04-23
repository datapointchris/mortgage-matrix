from mortgage_matrix.mortgage import Mortgage

m = Mortgage(
    purchase_price=150_000,
    percent_down=20,
    interest_rate=0.05,
    loan_years=30,
    utility_cost_percentage=20,
    property_tax_percentage=1.25,
)

m.print_summary()
