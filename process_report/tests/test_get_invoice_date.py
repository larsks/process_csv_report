import pandas
from process_report import process_report


def test_get_invoice_date():
    """Assert that the invoice_date is the first item"""

    # The month in sample data is not the same
    data = {"Invoice Month": ["2023-01", "2023-02", "2023-03"]}
    dataframe = pandas.DataFrame(data)
    expected_date = pandas.Timestamp("2023-01")

    invoice_date = process_report.get_invoice_date(dataframe)

    assert isinstance(invoice_date, pandas.Timestamp)
    assert invoice_date == expected_date
