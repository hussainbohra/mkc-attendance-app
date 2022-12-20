import argparse

from attendance.report import Report

if __name__ == '__main__':
    print("MKC Attendance Application: Initialize")
    variables = argparse.ArgumentParser()
    variables.add_argument(
        "--config", "-c",
        help="Config file for mkc attendance",
        required=True,
        default=None
    )
    args = variables.parse_args()
    config_file = args.config

    report_obj = Report(config_file)
    report_obj.generate_report()
