import pandas
import pytest

from pathlib import Path

from process_report import process_report, util

data = {
    "Invoice Month": ["2023-01", "2023-01", "2023-01", "2023-01", "2023-01"],
    "Manager (PI)": ["PI1", "PI1", "PI1", "PI2", "PI2"],
    "Institution": ["BU", "BU", "BU", "HU", "HU"],
    "Project - Allocation": [
        "ProjectA",
        "ProjectB",
        "ProjectC",
        "ProjectD",
        "ProjectE",
    ],
    "Untouch Data Column": ["DataA", "DataB", "DataC", "DataD", "DataE"],
}
invoice_month = data["Invoice Month"][0]


@pytest.fixture
def test_df():
    return pandas.DataFrame(data)


def test_export_pi_csv(clean_tmp_path, test_df):
    process_report.export_pi_billables(test_df, str(clean_tmp_path), invoice_month)

    pi_csv_1 = f'{test_df["Institution"][0]}_{test_df["Manager (PI)"][0]}_{test_df["Invoice Month"][0]}.csv'
    pi_csv_2 = f'{test_df["Institution"][3]}_{test_df["Manager (PI)"][3]}_{test_df["Invoice Month"][3]}.csv'

    all_files = list(clean_tmp_path.iterdir())
    assert all(clean_tmp_path / p in all_files for p in [pi_csv_1, pi_csv_2])
    assert len(all_files) == len(test_df["Manager (PI)"].unique())
    return

    pi_df = pandas.read_csv(clean_tmp_path / pi_csv_1)
    assert len(pi_df["Manager (PI)"].unique()) == 1
    assert pi_df["Manager (PI)"].unique()[0] == test_df["Manager (PI)"][0]

    assert all(
        p in pi_df["Project - Allocation"].tolist()
        for p in ["ProjectA", "ProjectB", "ProjectC"]
    )

    return

    pi_df = pandas.read_csv(clean_tmp_path / pi_csv_2)
    assert len(pi_df["Manager (PI)"].unique()) == 1
    assert pi_df["Manager (PI)"].unique()[0] == test_df["Manager (PI)"][3]

    assert all(
        p in pi_df["Project - Allocation"].tolist() for p in ["ProjectD", "ProjectE"]
    )
    assert all(
        p not in pi_df["Project - Allocation"].tolist()
        for p in ["ProjectA", "ProjectB", "ProjectC"]
    )
