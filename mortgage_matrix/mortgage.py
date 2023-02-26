from dataclasses import dataclass, asdict
import argparse
import decimal


@dataclass
class PaymentPeriod:
    period: int
    balance: float
    payment: float
    principle: float
    interest: float
    utilities: float
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
    DOLLAR_QUANTIZE = decimal.Decimal('.01')
    MONTHS_PER_YEAR = 12
    PMI = 0.0058
    HOME_INSURNACE_YEARLY = 2000

    def __init__(
        self,
        purchase_price: int,
        percent_down: int,
        interest_rate: float,
        years: int,
        utility_cost_percentage: float,
        property_tax_percentage: float,
    ):
        self.purchase_amount = self.dollar(purchase_price)
        self.percent_down = self.percentage(percent_down)
        self.down_payment = self.purchase_amount * self.percent_down
        self.loan_amount = self.dollar(purchase_price * (1 - self.percent_down))
        self.interest_rate = self.percentage(interest_rate)
        self.years = decimal.Decimal(years)
        self.months = decimal.Decimal(years * self.MONTHS_PER_YEAR)
        self.utility_cost_percentage = self.percentage(utility_cost_percentage)
        self.property_tax_percentage = self.percentage(property_tax_percentage)

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
        return self.dollar(pre_amt, rounding=decimal.ROUND_CEILING)

    @property
    def monthly_utilities(self):
        return self.monthly_payment * self.utility_cost_percentage

    @property
    def monthly_property_tax(self):
        return self.monthly_payment * self.property_tax_percentage

    @property
    def monthly_home_insurnace(self):
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
        return self.monthly_payment * self.months

    @property
    def payment_schedule(self) -> list[PaymentPeriod]:
        balance = self.dollar(self.loan_amount)
        rate = decimal.Decimal(str(self.interest_rate)).quantize(decimal.Decimal('.000001'))
        schedule = []
        for period in range(1, int(self.months) + 1):
            interest_unrounded = balance * rate * decimal.Decimal(1) / self.MONTHS_PER_YEAR
            interest = self.dollar(interest_unrounded, rounding=decimal.ROUND_HALF_UP)
            principle = self.monthly_payment - interest
            payment = balance + interest if self.monthly_payment >= balance + interest else self.monthly_payment
            utilities = self.monthly_utilities
            property_tax = self.monthly_property_tax
            insurance = self.monthly_home_insurnace
            pmi = self.monthly_pmi if (balance / self.purchase_amount > 0.78) else 0
            total_monthly_payment = payment + utilities + property_tax + insurance + pmi
            schedule.append(
                [
                    PaymentPeriodItem('Period', period, '.0f'),
                    PaymentPeriodItem('Balance', float(balance), '.2f'),
                    PaymentPeriodItem('Payment', float(payment), '.2f'),
                    PaymentPeriodItem('Principle', float(principle), '.2f'),
                    PaymentPeriodItem('Interest', float(interest), '.2f'),
                    PaymentPeriodItem('Utilities', float(utilities), '.2f'),
                    PaymentPeriodItem('Property Tax', float(property_tax), '.2f'),
                    PaymentPeriodItem('Insurance', float(insurance), '.2f'),
                    PaymentPeriodItem('Personal Mortgage Insurance', float(pmi), '.2f'),
                    PaymentPeriodItem('Total Monthly Payment', float(total_monthly_payment), '.2f'),
                ]
            )
            balance = balance - principle
        return schedule

    @property
    def summary(self) -> list[MortgageSummaryItem]:
        return [
            MortgageSummaryItem('Purchase Amount', self.purchase_amount, '.2f'),
            MortgageSummaryItem('Percent Down', self.percent_down, '.2%'),
            MortgageSummaryItem('Down Payment', self.down_payment, '.2f'),
            MortgageSummaryItem('Loan Amount', self.loan_amount, '.2f'),
            MortgageSummaryItem('Rate', self.interest_rate, '.2%'),
            MortgageSummaryItem('APY', self.apy, '.6%'),
            MortgageSummaryItem('Monthly Payment', self.monthly_payment, '.2f'),
            MortgageSummaryItem('Monthly Utility Cost', self.monthly_utilities, '.2f'),
            MortgageSummaryItem('Monthly Property Tax', self.monthly_property_tax, '.2f'),
            MortgageSummaryItem('Monthly Home Insurance', self.monthly_home_insurnace, '.2f'),
            MortgageSummaryItem('Personal Mortgage Insurance', self.monthly_pmi, '.2f'),
            MortgageSummaryItem('Total Monthly Payment', self.total_monthly_payment, '.2f'),
            MortgageSummaryItem('Month Growth', self.month_growth, '.6f'),
            MortgageSummaryItem('Payoff Years', self.loan_years, '.0f'),
            MortgageSummaryItem('Payoff Months', self.months, '.0f'),
            MortgageSummaryItem('Annual Payment', self.annual_payment, '.2f'),
            MortgageSummaryItem('Total Cost', self.total_payout, '.2f'),
        ]

    def to_dict(self) -> dict:
        return {summ_item.name: round(float(summ_item.value), 4) for summ_item in self.summary}

    def print_item(self, items, title, top_border='-', bottom_border='=', label_pad=30, value_pad=12):
        width = label_pad + value_pad + 4
        print()
        print(f'{title:{top_border}^{width}}')
        print('|' + ' ' * (width - 2) + '|')
        for item in items:
            print(f'|  {item.name : <{label_pad}}{item.value : <{value_pad}{item.format}}|')
        print('|' + ' ' * (width - 2) + '|')
        print(bottom_border * width)
        print()

    def print_summary(self):
        title = ' Mortgage Summary '
        self.print_item(self.summary, title=title)

    def print_payment_schedule(self, period=None, range=None):
        title = ' Payment Schedule '
        if period:
            self.print_item(self.payment_schedule[period + -1], title=title)
        elif range:
            for schedule in self.payment_schedule[range[0] - 1 : range[1]]:
                self.print_item(schedule, title=title)
        else:
            for schedule in self.payment_schedule:
                self.print_item(schedule, title=title)


def main():
    parser = argparse.ArgumentParser(description='Mortgage Amortization Tools')
    parser.add_argument('--purchase-price', default=300000, type=int)
    parser.add_argument('--percent-down', default=5, type=int)
    parser.add_argument('--interest-rate', default=5, type=int)
    parser.add_argument('--years', default=30, type=int)
    parser.add_argument('--utility-cost', default=20)
    parser.add_argument('--property-tax', default=1.25)
    args = parser.parse_args()

    m = Mortgage(
        purchase_price=args.purchase_price,
        percent_down=args.percent_down,
        interest_rate=args.interest_rate,
        years=args.years,
        utility_cost_percentage=args.utility_cost,
        property_tax_percentage=args.property_tax,
    )

    m.print_summary()

    # m.print_payment_schedule(period=3)

    # m.print_payment_schedule(range=(300, 304))


if __name__ == '__main__':
    main()
