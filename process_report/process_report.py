import argparse
import os

import pandas


def main():
    """Remove non-billable PIs and projects"""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "csv_files",
        nargs="+",
        help="One or more CSV files that need to be processed",
    )
    parser.add_argument(
        "--pi-file",
        required=True,
        help="File containing list of PIs that are non-billable",
    )
    parser.add_argument(
        "--projects-file",
        required=True,
        help="File containing list of projects that are non-billable",
    )
    parser.add_argument(
        "--timed-projects-file",
        required=True,
        help="File containing list of projects that are non-billable within a specified duration",
    )
    parser.add_argument(
        "--output-file",
        required=False,
        default="filtered_output.csv",
        help="Name of output file",
    )
    parser.add_argument(
        "--output-folder",
        required=False,
        default="pi_invoices",
        help="Name of output folder containing pi-specific invoice csvs"
    )
    args = parser.parse_args()
    merged_dataframe = merge_csv(args.csv_files)

    pi = []
    projects = []
    with open(args.pi_file) as file:
        pi = [line.rstrip() for line in file]
    with open(args.projects_file) as file:
        projects = [line.rstrip() for line in file]

    invoice_date = get_invoice_date(merged_dataframe)
    print("Invoice date: " + str(invoice_date))

    timed_projects_list = timed_projects(args.timed_projects_file, invoice_date)
    print("The following timed-projects will not be billed for this period: ")
    print(timed_projects_list)

    projects = list(set(projects + timed_projects_list))

    billable_projects = remove_non_billables(merged_dataframe, pi, projects, args.output_file)
    remove_billables(merged_dataframe, pi, projects, "non_billable.csv")
    export_pi_billables(billable_projects, args.output_folder)


def merge_csv(files):
    """Merge multiple CSV files and return a single pandas dataframe"""
    dataframes = []
    for file in files:
        dataframe = pandas.read_csv(file)
        dataframes.append(dataframe)

    merged_dataframe = pandas.concat(dataframes, ignore_index=True)
    merged_dataframe.reset_index(drop=True, inplace=True)
    return merged_dataframe


def get_invoice_date(dataframe):
    """Returns the invoice date as a pandas timestamp object

    Note that it only checks the first entry because it should
    be the same for every row.
    """
    invoice_date_str = dataframe['Invoice Month'][0]
    invoice_date = pandas.to_datetime(invoice_date_str, format='%Y-%m')
    return invoice_date


def timed_projects(timed_projects_file, invoice_date):
    """Returns list of projects that should be excluded based on dates"""
    dataframe = pandas.read_csv(timed_projects_file)

    # convert to pandas timestamp objects
    dataframe['Start Date'] = pandas.to_datetime(dataframe['Start Date'], format="%Y-%m")
    dataframe['End Date'] = pandas.to_datetime(dataframe['End Date'], format="%Y-%m")

    mask = (dataframe['Start Date'] <= invoice_date) & (invoice_date <= dataframe['End Date'])
    return dataframe[mask]['Project'].to_list()


def remove_non_billables(dataframe, pi, projects, output_file):
    """Removes projects and PIs that should not be billed from the dataframe"""
    filtered_dataframe = dataframe[~dataframe['Manager (PI)'].isin(pi) & ~dataframe['Project - Allocation'].isin(projects)]
    filtered_dataframe.to_csv(output_file, index=False)
    return filtered_dataframe


def remove_billables(dataframe, pi, projects, output_file):
    """Removes projects and PIs that should be billed from the dataframe

    So this *keeps* the projects/pis that should not be billed.
    """
    filtered_dataframe = dataframe[dataframe['Manager (PI)'].isin(pi) | dataframe['Project - Allocation'].isin(projects)]
    filtered_dataframe.to_csv(output_file, index=False)

def export_pi_billables(dataframe: pandas.DataFrame, output_folder):
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    invoice_month = dataframe['Invoice Month'].iat[0]
    pi_list = dataframe['Manager (PI)'].unique()

    for pi in pi_list:
        pi_projects = dataframe[dataframe['Manager (PI)'] == pi]
        pi_instituition = pi_projects['Institution'].iat[0]
        pi_projects.to_csv(output_folder + f"/{pi_instituition}_{pi}_{invoice_month}.csv")
        

if __name__ == "__main__":
    main()
