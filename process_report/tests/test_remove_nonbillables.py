import pandas
import pytest

from process_report.invoices import nonbillable_invoice


@pytest.fixture
def invoice():
    data = {
        "Manager (PI)": ["PI1", "PI2", "PI3", "PI4", "PI5"],
        "Project - Allocation": [
            "ProjectA",
            "ProjectB",
            "ProjectC",
            "ProjectD",
            "ProjectE",
        ],
        "Untouch Data Column": ["DataA", "DataB", "DataC", "DataD", "DataE"],
    }
    df = pandas.DataFrame(data)

    pi_to_exclude = ["PI2", "PI3"]
    projects_to_exclude = ["ProjectB", "ProjectD"]
    return nonbillable_invoice.NonbillableInvoice(
        "Foo", "Foo", df, pi_to_exclude, projects_to_exclude
    )


def test_remove_billables(invoice):
    invoice.process()
    result_df = invoice.data

    assert all(pi in result_df["Manager (PI)"].tolist() for pi in ["PI2", "PI3", "PI4"])
    assert all(
        proj in result_df["Project - Allocation"].tolist()
        for proj in ["ProjectB", "ProjectC", "ProjectD"]
    )

    assert all(pi not in result_df["Manager (PI)"].tolist() for pi in ["PI1", "PI5"])
    assert all(
        proj not in result_df["Project - Allocation"].tolist()
        for proj in ["ProjectA", "ProjectE"]
    )
