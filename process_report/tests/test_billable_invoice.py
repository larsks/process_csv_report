import pandas
import uuid

from process_report import util


def test_remove_nonbillables():
    pis = [uuid.uuid4().hex for _ in range(10)]
    projects = [uuid.uuid4().hex for _ in range(10)]
    nonbillable_pis = pis[:3]
    nonbillable_projects = projects[7:]
    billable_pis = pis[3:7]
    data = pandas.DataFrame({"Manager (PI)": pis, "Project - Allocation": projects})
    data = util.remove_nonbillables(data, nonbillable_pis, nonbillable_projects)

    assert data[data["Manager (PI)"].isin(nonbillable_pis)].empty
    assert data[data["Project - Allocation"].isin(nonbillable_projects)].empty
    assert data.equals(data[data["Manager (PI)"].isin(billable_pis)])
