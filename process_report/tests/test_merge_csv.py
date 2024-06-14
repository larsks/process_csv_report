import pandas
import pytest

from process_report import process_report

header = ["ID", "Name", "Age"]
data = [
    [1, "Alice", 25],
    [2, "Bob", 30],
    [3, "Charlie", 28],
]


@pytest.fixture
def csv_files(clean_tmp_path):
    files = []
    for i in range(3):
        with (clean_tmp_path / f"csv_file_{i}.csv").open("w") as fd:
            files.append(fd.name)
            dataframe = pandas.DataFrame(data, columns=header)
            dataframe.to_csv(fd, index=False)

    return files


def test_merge_csv(csv_files):
    merged_dataframe = process_report.merge_csv(csv_files)
    expected_rows = len(data) * len(csv_files)

    assert len(merged_dataframe) == expected_rows

    # Assert that the headers in the merged DataFrame match the expected headers
    assert merged_dataframe.columns.tolist() == header
