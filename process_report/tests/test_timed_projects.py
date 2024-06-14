import pandas
import pytest
from process_report import process_report


@pytest.fixture
def csv_file(clean_tmp_path):
    csv_data = (
        "Project,Start Date,End Date\n"
        "ProjectA,2022-09,2023-08\n"
        "ProjectB,2022-09,2023-09\n"
        "ProjectC,2023-09,2024-08\n"
        "ProjectD,2022-09,2024-08\n"
    )

    with (clean_tmp_path / "csv_file.csv").open("w") as fd:
        fd.write(csv_data)

    return fd


def test_timed_projects(csv_file):
    invoice_date = pandas.Timestamp("2023-09")
    excluded_projects = process_report.timed_projects(csv_file.name, invoice_date)
    expected_projects = ["ProjectB", "ProjectC", "ProjectD"]

    assert excluded_projects == expected_projects
