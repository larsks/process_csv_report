from unittest import TestCase, mock
import tempfile
import pandas
import pyarrow
import os
import math

from process_report import process_report, util
from process_report.invoices import lenovo_invoice


class TestGetInstitute(TestCase):
    def test_get_pi_institution(self):
        institute_map = {
            "harvard.edu": "Harvard University",
            "bu.edu": "Boston University",
            "bentley.edu": "Bentley",
            "mclean.harvard.edu": "McLean Hospital",
            "meei.harvard.edu": "Massachusetts Eye & Ear",
            "dfci.harvard.edu": "Dana-Farber Cancer Institute",
            "northeastern.edu": "Northeastern University",
        }

        self.assertEqual(
            process_report.get_institution_from_pi(institute_map, "quanmp@bu.edu"),
            "Boston University",
        )
        self.assertEqual(
            process_report.get_institution_from_pi(
                institute_map, "c@mclean.harvard.edu"
            ),
            "McLean Hospital",
        )
        self.assertEqual(
            process_report.get_institution_from_pi(institute_map, "b@harvard.edu"),
            "Harvard University",
        )
        self.assertEqual(
            process_report.get_institution_from_pi(institute_map, "fake"), ""
        )
        self.assertEqual(
            process_report.get_institution_from_pi(
                institute_map, "pi@northeastern.edu"
            ),
            "Northeastern University",
        )


class TestAlias(TestCase):
    def setUp(self):
        self.alias_dict = {"PI1": ["PI1_1", "PI1_2"], "PI2": ["PI2_1"]}

        self.data = pandas.DataFrame(
            {
                "Manager (PI)": ["PI1", "PI1_1", "PI1_2", "PI2_1", "PI2_1"],
            }
        )

        self.answer = pandas.DataFrame(
            {
                "Manager (PI)": ["PI1", "PI1", "PI1", "PI2", "PI2"],
            }
        )

    def test_validate_alias(self):
        output = process_report.validate_pi_aliases(self.data, self.alias_dict)
        self.assertTrue(self.answer.equals(output))


class TestMonthUtils(TestCase):
    def test_get_month_diff(self):
        testcases = [
            (("2024-12", "2024-03"), 9),
            (("2024-12", "2023-03"), 21),
            (("2024-11", "2024-12"), -1),
            (("2024-12", "2025-03"), -3),
        ]
        for arglist, answer in testcases:
            self.assertEqual(util.get_month_diff(*arglist), answer)
        with self.assertRaises(ValueError):
            util.get_month_diff("2024-16", "2025-03")


class TestCredit0002(TestCase):
    def setUp(self):
        data = {
            "Invoice Month": [
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
            ],
            "Manager (PI)": [
                "PI1",
                "PI2",
                "PI3",
                "PI4",
                "PI4",
                "PI5",
                "PI7",
                "NewPI1",
                "NewPI1",
                "NewPI2",
                "NewPI2",
            ],
            "SU Type": [
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
            ],
            "Project - Allocation": [
                "ProjectA",
                "ProjectB",
                "ProjectC",
                "ProjectD",
                "ProjectE",
                "ProjectF",
                "ProjectG",
                "ProjectH",
                "ProjectI",
                "ProjectJ",
                "ProjectK",
            ],
            "Cost": [10, 100, 10000, 500, 100, 400, 200, 250, 250, 700, 700],
        }
        answer_df_dict = {
            "Invoice Month": [
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
            ],
            "Manager (PI)": [
                "PI1",
                "PI2",
                "PI3",
                "PI4",
                "PI4",
                "PI5",
                "PI7",
                "NewPI1",
                "NewPI1",
                "NewPI2",
                "NewPI2",
            ],
            "SU Type": [
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
                "CPU",
            ],
            "Project - Allocation": [
                "ProjectA",
                "ProjectB",
                "ProjectC",
                "ProjectD",
                "ProjectE",
                "ProjectF",
                "ProjectG",
                "ProjectH",
                "ProjectI",
                "ProjectJ",
                "ProjectK",
            ],
            "Cost": [10, 100, 10000, 500, 100, 400, 200, 250, 250, 700, 700],
            "Credit": [None, None, None, 100, None, 400, 200, 250, 250, 500, None],
            "Credit Code": [
                None,
                None,
                None,
                "0002",
                None,
                "0002",
                "0002",
                "0002",
                "0002",
                "0002",
                None,
            ],
            "Balance": [10, 100, 10000, 400, 100, 0, 0, 0, 0, 200, 700],
        }
        self.dataframe = pandas.DataFrame(data)
        self.answer_dataframe = pandas.DataFrame(answer_df_dict)
        old_pi = [
            "PI,First Invoice Month,Initial Credits,1st Month Used,2nd Month Used",
            "PI1,2023-09,500,200,0",
            "PI2,2024-01,2000,0,0",
            "PI3,2024-01,2000,1000,500",
            "PI4,2024-02,1000,900,0",
            "PI5,2024-02,1000,300,500",
            "PI6,2024-02,1000,700,0",
            "PI7,2024-03,500,300,0",  # This as current month we're testing, new PIs should get $500
            "PI8,2024-04,1000,500,0",
        ]
        self.old_pi_df_answer = (
            pandas.DataFrame(
                {
                    "PI": [
                        "PI1",
                        "PI2",
                        "PI3",
                        "PI4",
                        "PI5",
                        "PI6",
                        "PI7",
                        "NewPI1",
                        "NewPI2",
                        "PI8",
                    ],
                    "First Invoice Month": [
                        "2023-09",
                        "2024-01",
                        "2024-01",
                        "2024-02",
                        "2024-02",
                        "2024-02",
                        "2024-03",
                        "2024-03",
                        "2024-03",
                        "2024-04",
                    ],
                    "Initial Credits": [
                        500,
                        2000,
                        2000,
                        1000,
                        1000,
                        1000,
                        500,
                        500,
                        500,
                        1000,
                    ],
                    "1st Month Used": [200, 0, 1000, 900, 300, 700, 200, 500, 500, 500],
                    "2nd Month Used": [0, 0, 500, 100, 400, 0, 0, 0, 0, 0],
                }
            )
            .astype(
                {
                    "Initial Credits": pandas.ArrowDtype(pyarrow.decimal128(21, 2)),
                    "1st Month Used": pandas.ArrowDtype(pyarrow.decimal128(21, 2)),
                    "2nd Month Used": pandas.ArrowDtype(pyarrow.decimal128(21, 2)),
                },
            )
            .sort_values(by="PI", ignore_index=True)
        )

        # Contains cases with new, one month old, two month old, older PI, and future PI that hasn't appeared in invoices yet
        # For each invoice month, test case where pi has 1 project, >1, and has spare credit
        old_pi_file = tempfile.NamedTemporaryFile(
            delete=False, mode="w+", suffix=".csv"
        )
        for pi in old_pi:
            old_pi_file.write(pi + "\n")
        self.old_pi_file = old_pi_file.name

        self.dataframe_no_gpu = pandas.DataFrame(
            {
                "Invoice Month": [
                    "2024-03",
                    "2024-03",
                    "2024-03",
                    "2024-03",
                    "2024-03",
                ],
                "Manager (PI)": ["PI1", "PI1", "PI1", "PI2", "PI2"],
                "SU Type": [
                    "GPU",
                    "OpenShift GPUA100SXM4",
                    "OpenStack GPUA100SXM4",
                    "OpenShift GPUA100SXM4",
                    "OpenStack GPUA100SXM4",
                ],
                "Cost": [500, 100, 100, 500, 500],
            }
        )
        old_pi_no_gpu = [
            "PI,First Invoice Month,Initial Credits,1st Month Used,2nd Month Used",
            "OldPI,2024-03,500,200,0",
        ]
        old_pi_no_gpu_file = tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=".csv"
        )
        for pi in old_pi_no_gpu:
            old_pi_no_gpu_file.write(pi + "\n")
        self.old_pi_no_gpu_file = old_pi_no_gpu_file.name
        self.no_gpu_df_answer = pandas.DataFrame(
            {
                "Invoice Month": [
                    "2024-03",
                    "2024-03",
                    "2024-03",
                    "2024-03",
                    "2024-03",
                ],
                "Manager (PI)": ["PI1", "PI1", "PI1", "PI2", "PI2"],
                "SU Type": [
                    "GPU",
                    "OpenShift GPUA100SXM4",
                    "OpenStack GPUA100SXM4",
                    "OpenShift GPUA100SXM4",
                    "OpenStack GPUA100SXM4",
                ],
                "Cost": [500, 100, 100, 500, 500],
                "Credit": [500, None, None, None, None],
                "Credit Code": ["0002", None, None, None, None],
                "Balance": [0.0, 100.0, 100.0, 500.0, 500.0],
            }
        )

    def tearDown(self):
        os.remove(self.old_pi_file)
        os.remove(self.old_pi_no_gpu_file)

    def test_apply_credit_0002(self):
        old_pi_df = util.load_old_pis(self.old_pi_file)
        dataframe, updated_old_pi_df = util.apply_credits_new_pi(
            self.dataframe, old_pi_df
        )
        dataframe = dataframe.astype({"Credit": "float64", "Balance": "int64"})
        old_pi_df = old_pi_df.sort_values(by="PI", ignore_index=True)
        self.assertTrue(self.answer_dataframe.equals(dataframe))
        self.assertTrue(self.old_pi_df_answer.equals(updated_old_pi_df))

    def test_no_gpu(self):
        old_pi_df = util.load_old_pis(self.old_pi_no_gpu_file)
        dataframe, _ = util.apply_credits_new_pi(self.dataframe_no_gpu, old_pi_df)
        dataframe = dataframe.astype({"Credit": "float64", "Balance": "float64"})
        self.assertTrue(self.no_gpu_df_answer.equals(dataframe))

    def test_apply_credit_error(self):
        old_pi_df = pandas.DataFrame(
            {"PI": ["PI1"], "First Invoice Month": ["2024-04"]}
        )
        invoice_month = "2024-03"
        with self.assertRaises(SystemExit):
            util.get_pi_age(old_pi_df, "PI1", invoice_month)


class TestBUSubsidy(TestCase):
    def setUp(self):
        data = {
            "Invoice Month": [
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
                "2024-03",
            ],
            "Manager (PI)": ["PI1", "PI1", "PI2", "PI2", "PI3", "PI3", "PI4", "PI4"],
            "Institution": [
                "Boston University",
                "Boston University",
                "Boston University",
                "Boston University",
                "Harvard University",  # Test case for non-BU PIs
                "Harvard University",
                "Boston University",
                "Boston University",
            ],
            "Project - Allocation": [
                "ProjectA-e6413",
                "ProjectA-t575e6",  # Test case for project with >1 allocation
                "ProjectB-fddgfygg",
                "ProjectB-5t143t",
                "ProjectC-t14334",
                "ProjectD",  # Test case for correctly extracting project name
                "ProjectE-test-r25135",  # Test case for BU PI with >1 project
                "ProjectF",
            ],
            "Cost": [1050, 500, 100, 925, 10000, 1000, 1050, 100],
            "Credit": [
                1000,
                0,
                100,
                900,
                0,
                0,
                1000,
                0,
            ],  # Test cases where PI does/dones't have credits alreadys
            "Balance": [
                50,
                500,
                0,
                25,
                10000,
                1000,
                50,
                100,
            ],  # Test case where subsidy does/doesn't cover fully balance
        }
        self.dataframe = pandas.DataFrame(data)
        output_file = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".csv")
        self.output_file = output_file.name
        self.subsidy = 100

    def test_apply_BU_subsidy(self):
        process_report.export_BU_only(self.dataframe, self.output_file, self.subsidy)
        output_df = pandas.read_csv(self.output_file)

        self.assertTrue(
            set(
                [
                    process_report.INVOICE_DATE_FIELD,
                    "Project",
                    process_report.PI_FIELD,
                    process_report.COST_FIELD,
                    process_report.CREDIT_FIELD,
                    process_report.SUBSIDY_FIELD,
                    process_report.BALANCE_FIELD,
                ]
            ).issubset(output_df)
        )

        self.assertTrue(
            set(["PI1", "PI2", "PI4"]).issubset(output_df["Manager (PI)"].unique())
        )
        self.assertFalse("PI3" in output_df["Project"].unique())

        self.assertTrue(
            set(["ProjectA", "ProjectB", "ProjectE-test", "ProjectF"]).issubset(
                output_df["Project"].unique()
            )
        )
        self.assertFalse(
            set(["ProjectC-t14334", "ProjectC", "ProjectD"]).intersection(
                output_df["Project"].unique()
            )
        )

        self.assertEqual(4, len(output_df.index))
        self.assertEqual(1550, output_df.loc[0, "Cost"])
        self.assertEqual(1025, output_df.loc[1, "Cost"])
        self.assertEqual(1050, output_df.loc[2, "Cost"])
        self.assertEqual(100, output_df.loc[3, "Cost"])

        self.assertEqual(100, output_df.loc[0, "Subsidy"])
        self.assertEqual(25, output_df.loc[1, "Subsidy"])
        self.assertEqual(50, output_df.loc[2, "Subsidy"])
        self.assertEqual(50, output_df.loc[3, "Subsidy"])

        self.assertEqual(450, output_df.loc[0, "Balance"])
        self.assertEqual(0, output_df.loc[1, "Balance"])
        self.assertEqual(0, output_df.loc[2, "Balance"])
        self.assertEqual(50, output_df.loc[3, "Balance"])


class TestValidateBillables(TestCase):
    def setUp(self):
        data = {
            "Manager (PI)": ["PI1", math.nan, "PI1", "PI2", "PI2"],
            "Project - Allocation": [
                "ProjectA",
                "ProjectB",
                "ProjectC",
                "ProjectD",
                "ProjectE",
            ],
        }
        self.dataframe = pandas.DataFrame(data)

    def test_validate_billables(self):
        self.assertEqual(
            1, len(self.dataframe[pandas.isna(self.dataframe["Manager (PI)"])])
        )
        validated_df = util.validate_pi_names(self.dataframe)
        self.assertEqual(
            0, len(validated_df[pandas.isna(validated_df["Manager (PI)"])])
        )


class TestExportLenovo(TestCase):
    def setUp(self):
        data = {
            "Invoice Month": [
                "2023-01",
                "2023-01",
                "2023-01",
                "2023-01",
                "2023-01",
                "2023-01",
            ],
            "Project - Allocation": [
                "ProjectA",
                "ProjectB",
                "ProjectC",
                "ProjectD",
                "ProjectE",
                "ProjectF",
            ],
            "Institution": ["A", "B", "C", "D", "E", "F"],
            "SU Hours (GBhr or SUhr)": [1, 10, 100, 4, 432, 10],
            "SU Type": [
                "OpenShift GPUA100SXM4",
                "OpenShift GPUA100",
                "OpenShift GPUA100SXM4",
                "OpenStack GPUA100SXM4",
                "OpenStack CPU",
                "OpenStack GPUK80",
            ],
        }
        self.lenovo_invoice = lenovo_invoice.LenovoInvoice(
            "Lenovo", "2023-01", pandas.DataFrame(data)
        )
        self.lenovo_invoice.process()

    def test_process_lenovo(self):
        output_df = self.lenovo_invoice.data
        self.assertTrue(
            set(
                [
                    process_report.INVOICE_DATE_FIELD,
                    process_report.PROJECT_FIELD,
                    process_report.INSTITUTION_FIELD,
                    process_report.SU_TYPE_FIELD,
                    "SU Hours",
                    "SU Charge",
                    "Charge",
                ]
            ).issubset(output_df)
        )

        for i, row in output_df.iterrows():
            self.assertIn(
                row[process_report.SU_TYPE_FIELD],
                ["OpenShift GPUA100SXM4", "OpenStack GPUA100SXM4"],
            )
            self.assertEqual(row["Charge"], row["SU Charge"] * row["SU Hours"])


class TestUploadToS3(TestCase):
    @mock.patch("process_report.process_report.get_invoice_bucket")
    @mock.patch("process_report.process_report.get_iso8601_time")
    def test_remove_prefix(self, mock_get_time, mock_get_bucket):
        mock_bucket = mock.MagicMock()
        mock_get_bucket.return_value = mock_bucket
        mock_get_time.return_value = "0"

        invoice_month = "2024-03"
        filenames = ["test.csv", "test2.test.csv", "test3"]
        answers = [
            ("test.csv", f"Invoices/{invoice_month}/test {invoice_month}.csv"),
            (
                "test.csv",
                f"Invoices/{invoice_month}/Archive/test {invoice_month} 0.csv",
            ),
            (
                "test2.test.csv",
                f"Invoices/{invoice_month}/test2.test {invoice_month}.csv",
            ),
            (
                "test2.test.csv",
                f"Invoices/{invoice_month}/Archive/test2.test {invoice_month} 0.csv",
            ),
            ("test3", f"Invoices/{invoice_month}/test3 {invoice_month}.csv"),
            ("test3", f"Invoices/{invoice_month}/Archive/test3 {invoice_month} 0.csv"),
        ]

        process_report.upload_to_s3(filenames, invoice_month)
        for i, call_args in enumerate(mock_bucket.upload_file.call_args_list):
            self.assertTrue(answers[i] in call_args)
