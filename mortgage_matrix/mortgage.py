import argparse
import decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentPeriod:
    period: int
    balance: float
    payment: float
    principle: float
    interest: float
    pmi: float
    utilities: float
    home_insurance: float
    property_tax: float
    total_monthly_payment: float


@dataclass
class PaymentPeriodItem:
    name: str
    value: int | float
    format: str


@dataclass
class MortgageSummaryItem:
    name: str
    value: int | float
    format: str


class Mortgage:
    DOLLAR_QUANTIZE = decimal.Decimal(".01")
    MONTHS_PER_YEAR = 12
    PMI = 0.0058
    HOME_INSURNACE_YEARLY = decimal.Decimal(2000)

    def __init__(
        self,
        purchase_price: int,
        percent_down: int,
        interest_rate: float,
        loan_years: int,
        utility_cost_percentage: float,
        property_tax_percentage: float,
    ):
        self.purchase_price = self.dollar(purchase_price)
        self.percent_down = self.percentage(percent_down)
        self.down_payment = self.purchase_price * self.percent_down
        self.loan_amount = self.dollar(purchase_price * (1 - self.percent_down))
        self.interest_rate = self.percentage(interest_rate)
        self.years = decimal.Decimal(loan_years)
        self.months = decimal.Decimal(loan_years * 12)
        self.utility_cost_percentage = self.percentage(utility_cost_percentage)
        self.property_tax_percentage = self.percentage(property_tax_percentage)
        self.payment_schedule = self._create_payment_schedule()

    @staticmethod
    def percentage(number):
        """Return decimal percentage from integer"""
        return decimal.Decimal(float(number) / 100)

    def dollar(self, amount, rounding=decimal.ROUND_CEILING):
        """
        This function rounds the passed float to 2 decimal places.
        """
        if not isinstance(amount, decimal.Decimal):
            amount = decimal.Decimal(str(amount))
        return amount.quantize(self.DOLLAR_QUANTIZE, rounding=rounding)

    @property
    def apy(self):
        return (self.month_growth**12) - 1

    @property
    def loan_years(self):
        return self.years

    @property
    def monthly_payment(self):
        interest = self.loan_amount * self.interest_rate
        pre_amt = interest / (self.MONTHS_PER_YEAR * (1 - (1 / self.month_growth) ** self.months))
        return self.dollar(pre_amt)

    @property
    def monthly_utilities(self):
        return self.monthly_payment * self.utility_cost_percentage

    @property
    def monthly_property_tax(self):
        return self.monthly_payment * self.property_tax_percentage

    @property
    def monthly_home_insurance(self):
        return self.HOME_INSURNACE_YEARLY / self.MONTHS_PER_YEAR

    @property
    def monthly_pmi(self):
        return self.loan_amount * decimal.Decimal(self.PMI) / self.MONTHS_PER_YEAR

    @property
    def total_monthly_payment(self):
        return self.monthly_payment + self.monthly_utilities + self.monthly_property_tax + self.monthly_pmi

    @property
    def month_growth(self):
        return 1 + self.interest_rate / self.MONTHS_PER_YEAR

    @property
    def total_value(self):
        return (self.monthly_payment / self.interest_rate) * (
            self.MONTHS_PER_YEAR * (1 - (1 / self.month_growth) ** self.months)
        )

    @property
    def annual_payment(self):
        return self.monthly_payment * self.MONTHS_PER_YEAR

    @property
    def total_payout(self):
        return self.monthly_payment * self.months + self.down_payment

    @property
    def cost_over_purchase_amount(self):
        return self.total_payout - self.purchase_price

    @property
    def percent_over_purchase_amount(self):
        return self.cost_over_purchase_amount / self.purchase_price

    def _print_payment_period(self, period: PaymentPeriod):

        print(f"Period {period.period:,.0f}")
        print(f"Balance {float(period.balance):,.2f}")
        print(f"Payment {float(period.payment):,.2f}")
        print(f"Principle {float(period.principle):,.2f}")
        print(f"Interest {float(period.interest):,.2f}")
        print(f"Utilities {float(period.utilities):,.2f}")
        print(f"Property Tax {float(self.monthly_property_tax):,.2f}")
        print(f"Insurance {float(period.home_insurance):,.2f}")
        print(f"Personal Mortgage Insurance {float(period.pmi):,.2f}")
        print(f"Total Monthly Payment {float(period.total_monthly_payment):,.2f}")

    def _create_payment_schedule(self) -> list[PaymentPeriod]:
        balance = self.dollar(self.loan_amount)
        rate = decimal.Decimal(str(self.interest_rate)).quantize(decimal.Decimal(".000001"))
        schedule = []
        for period in range(1, int(self.months) + 1):
            interest_unrounded = balance * rate * decimal.Decimal(1) / self.MONTHS_PER_YEAR
            interest = self.dollar(interest_unrounded, rounding=decimal.ROUND_HALF_UP)
            principle = self.monthly_payment - interest
            payment = min(balance + interest, self.monthly_payment)
            utilities = self.monthly_utilities
            property_tax = self.monthly_property_tax
            insurance = self.monthly_home_insurance
            pmi = self.monthly_pmi if (balance / self.purchase_price > 0.78) else 0
            total_monthly_payment = payment + utilities + property_tax + insurance + pmi
            schedule.append(
                PaymentPeriod(
                    period=period,
                    balance=float(balance),
                    payment=float(payment),
                    principle=float(principle),
                    interest=float(interest),
                    pmi=float(pmi),
                    utilities=float(utilities),
                    home_insurance=float(insurance),
                    property_tax=float(property_tax),
                    total_monthly_payment=float(total_monthly_payment),
                )
            )
            balance = balance - principle
        return schedule

    @property
    def summary(self) -> list[MortgageSummaryItem]:
        return [
            MortgageSummaryItem("Purchase Amount", float(self.purchase_price), ",.2f"),
            MortgageSummaryItem("Percent Down", float(self.percent_down), ".2%"),
            MortgageSummaryItem("Down Payment", float(self.down_payment), ",.2f"),
            MortgageSummaryItem("Loan Amount", float(self.loan_amount), ",.2f"),
            MortgageSummaryItem("Rate", float(self.interest_rate), ".2%"),
            MortgageSummaryItem("APY", float(self.apy), ".6%"),
            MortgageSummaryItem("Monthly Payment", float(self.monthly_payment), ",.2f"),
            MortgageSummaryItem("Monthly Utility Cost", float(self.monthly_utilities), ".2f"),
            MortgageSummaryItem("Monthly Property Tax", float(self.monthly_property_tax), ".2f"),
            MortgageSummaryItem("Monthly Home Insurance", float(self.monthly_home_insurance), ".2f"),
            MortgageSummaryItem("Personal Mortgage Insurance", float(self.monthly_pmi), ".2f"),
            MortgageSummaryItem("Total Monthly Payment", float(self.total_monthly_payment), ",.2f"),
            MortgageSummaryItem("Month Growth", float(self.month_growth), ".6f"),
            MortgageSummaryItem("Payoff Years", float(self.loan_years), ".0f"),
            MortgageSummaryItem("Payoff Months", float(self.months), ".0f"),
            MortgageSummaryItem("Annual Payment", float(self.annual_payment), ",.2f"),
            MortgageSummaryItem("Total Cost", float(self.total_payout), ",.2f"),
            MortgageSummaryItem("Cost Over Purchase Price", float(self.cost_over_purchase_amount), ",.2f"),
            MortgageSummaryItem(
                "Percent Over Purchase Price",
                float(self.percent_over_purchase_amount),
                ".2%",
            ),
        ]

    def to_dict(self) -> dict:
        return {summ_item.name: round(float(summ_item.value), 4) for summ_item in self.summary}

    def _print_item(
        self,
        items,
        title,
        top_border="-",
        bottom_border="=",
        label_pad=30,
        value_pad=12,
    ):
        width = label_pad + value_pad + 4
        print()
        print(f"{title:{top_border}^{width}}")
        print("|" + " " * (width - 2) + "|")
        for item in items:
            print(f"|  {item.name : <{label_pad}}{item.value : <{value_pad}{item.format}}|")  # noqa
        print("|" + " " * (width - 2) + "|")
        print(bottom_border * width)
        print()

    def print_summary(self):
        title = " Mortgage Summary "
        self._print_item(self.summary, title=title)

    def print_payment_schedule(
        self,
        period: Optional[int] = None,
        period_range: Optional[tuple[int, int]] = None,
    ):
        title = " Payment Schedule "
        if period:
            self._print_item(self._create_payment_schedule()[period - 1], title=title)
        elif period_range:
            start = period_range[0] - 1
            end = period_range[1]
            for schedule in self._create_payment_schedule()[start:end]:
                self._print_item(schedule, title=title)
        else:
            for schedule in self._create_payment_schedule():
                self._print_item(schedule, title=title)


def main():
    parser = argparse.ArgumentParser(description="Mortgage Amortization Tools")
    parser.add_argument("--purchase-price", default=300000, type=int)
    parser.add_argument("--percent-down", default=5, type=int)
    parser.add_argument("--interest-rate", default=5, type=int)
    parser.add_argument("--years", default=30, type=int)
    parser.add_argument("--utility-cost", default=20)
    parser.add_argument("--property-tax", default=1.25)
    args = parser.parse_args()

    m = Mortgage(
        purchase_price=args.purchase_price,
        percent_down=args.percent_down,
        interest_rate=args.interest_rate,
        loan_years=args.years,
        utility_cost_percentage=args.utility_cost,
        property_tax_percentage=args.property_tax,
    )

    m.print_summary()

    # m.print_payment_schedule(period=3)

    # m.print_payment_schedule(range=(300, 304))


if __name__ == "__main__":
    main()
