from dataclasses import asdict

from .config import Config
from .sheets import GSheets
from .email import Email
from .models import Attendance, Total
from .students import StudentDB
from .utils import (
    get_prev_saturdays,
    is_absent
)
from .writer import Writer

import pandas as pd
import numpy as np


class Report:
    def __init__(self, config_file):
        """
        Read all attendance data and prepare report

        :param credentials:
            a json file
        """
        self.config = Config(config_file).get_config()
        self.gsheet_obj = GSheets(
            self.config['credentials_file'],
            self.config['scopes']
        )
        self.email_obj = Email(
            self.config['email']['client_id'],
            self.config['email']['client_secret'],
            self.config['email']['access_token']

        )
        self.writer = Writer(self.config)
        self.all_student_data = StudentDB(self.config, self.gsheet_obj).build_school_db()
        self.advance_leave_requests = self.get_advance_leave_requests()

    def generate_report(self):
        """
        Read attendance sheet, and grab all sheet names (classes)
        Read advance leave request form, and grab leave request in last 7 days.
        Iterate on all classes
            - Grab the latest attendance data
            - Prepare a dict for every class and its latest attendance
        Get all absentees
        Prepare CSV file for all absentees (informed and uninformed)
        Prepare and Send an email

        :return:
        """
        attendance_sheet = self.config['attendance_sheet_id']
        all_classes = self.gsheet_obj.get_sheets(attendance_sheet)
        latest_attendance = []
        appended_data = []
        for tab in all_classes:
            if tab.lower() == "total":
                continue
            attendance_data = self.gsheet_obj.read_gsheet(
                attendance_sheet,
                tab_name=tab
            )
            attendance_df = pd.DataFrame(attendance_data)
            attendance_df["date"] = pd.to_datetime(
                attendance_df['Timestamp']
            )
            appended_data.append(self.generate_attendance_perc(attendance_df, tab))
            print("get latest attendance for a class {0}".format(tab))
            last_attendance = attendance_df.sort_values(
                by='date', ascending=False
            ).reset_index().loc[0].to_dict()
            latest_attendance.append({
                'class_name': tab,
                'latest_attendance': last_attendance
            })

        absentees, total = self.get_absentees(latest_attendance)
        appended_data = pd.concat(appended_data)
        appended_data.sort_values('Absent Percentage', ascending=False).to_excel(
            self.config['email']['student_absent_perc']
        )
        xlsx_file = self.writer.generate_csv_report(absentees, total)
        subject, message = self.email_obj.prepare_email(
            absentees,
            total,
            self.config['email']
        )
        self.email_obj.send_email(
            subject, message,
            [xlsx_file, self.config['email']['student_absent_perc']],
            self.config['email']['to_emails'],
            self.config['email']['cc_emails']
        )

    def get_student_info(self, k):
        """


        :return:
        """

        student_name = k.strip().replace('[', '').replace(']', '')
        student_info = list(
            filter(lambda a: a.full_name.lower() == student_name.lower(), self.all_student_data)
        )
        return student_name, student_info

    def get_absentees(self, latest_attendance):
        """
        Identifying all Absentees and generate there information
        In addition, also creating a consolidated report

        :param class_name:
        :return:
        """
        print("[Get Absentees]: Identifying all Absentees")
        absentees = []
        total = []
        print("Iterating over the latest attendance, to identify absentees")
        for attendance in latest_attendance:
            absent_count, present_count, informed_absent_count = 0, 0, 0
            class_name = attendance.get("class_name")
            timestamp = attendance.get("latest_attendance", {}).get("Timestamp")
            date = attendance.get("latest_attendance", {}).get("Date:")
            if timestamp:
                for k, v in attendance.get("latest_attendance", {}).items():
                    if k.strip().startswith('[') and k.strip().endswith(']'):
                        if type(v) is str and str(v).lower() != "present":
                            student_name, student_info = self.get_student_info(k)
                            # checking if student has applied leave in advance
                            leave_applied = list(filter(
                                lambda a: a['Class'] == class_name and a['student_name'] == student_name,
                                self.advance_leave_requests
                            ))
                            if leave_applied:
                                v = "Informed Absent (By Form)"
                            if v.lower() == "absent":
                                absent_count += 1
                            else:
                                informed_absent_count += 1
                            absentees.append(self.create_absentee_row(
                                date, student_name, class_name, v, student_info
                            ))
                        else:
                            present_count += 1
                    else:
                        # ignore all keys which doesnt start with "[" and ends with "]"
                        continue
            total.append(
                asdict(Total(date, class_name, present_count, informed_absent_count, absent_count))
            )
        print("[Get Absentees]: Exiting")
        return absentees, total

    def create_absentee_row(self, date, student_name, class_name, status, student_info={}):
        """
        Prepare a row for absent students.

        :param date:
        :param student_name:
        :param class_name:
        :param status:
        :param student_info:
        :return:
        """
        absentee = Attendance(date, student_name, class_name, status)
        if student_info:
            absentee.mother_info = f"{student_info[0].mother_name} - {student_info[0].mother_cell}"
            absentee.father_info = f"{student_info[0].father_name} - {student_info[0].father_cell}"
            absentee.primary_email = student_info[0].primary_email
        return asdict(absentee)

    def get_advance_leave_requests(self):
        """
        Read student leave request form and
        identify students who requested leave in advance

        :return:
        """
        prev_saturdays = get_prev_saturdays()
        print("[Read Advance Leave Requests] Reading students applied for advance leave from {0} to {1}".format(
            prev_saturdays[0], prev_saturdays[1])
        )
        student_absence_request = self.config['student_absence_request']
        absence_request = self.gsheet_obj.read_gsheet(
            student_absence_request,
            tab_name=self.config['student_absence_request_tab'],
            repeated_header="Student Name"
        )
        absence_request_df = pd.DataFrame(absence_request)
        absence_request_df['date'] = pd.to_datetime(
            absence_request_df['Timestamp'], format='%m/%d/%Y %H:%M:%S'
        )
        filtered_df = absence_request_df.loc[
            (absence_request_df['date'] >= prev_saturdays[0].strftime('%Y-%m-%d'))
            & (absence_request_df['date'] < prev_saturdays[1].strftime('%Y-%m-%d'))
            ]
        # Read all columns with name "Student Name.x"
        student_cols = list(map(lambda a: "Student Name.%s" % str(a), range(0, 22)))
        # Replace all empty values with the Nan
        filtered_df = filtered_df.replace(r'^\s*$', np.nan, regex=True)
        # Caalesce all cols with name "Student Name.x",
        # and keep the first non-null in student_name col
        filtered_df['student_name'] = (
            filtered_df[student_cols]
            .bfill(axis=1).iloc[:, 0]
        )
        # drop all columns with name "Student Name.x"
        filtered_df = filtered_df.drop(columns=student_cols)
        filtered_df = filtered_df.loc[filtered_df['Request Type'] == 'Leave']
        filtered_df = filtered_df[['student_name', 'Class']]
        return filtered_df.to_dict("records")

    def generate_attendance_perc(self, attendance_df, class_name):
        """
        Google sheets return lot of empty rows, filter the same
        Take the latest attendance for every saturday by adding row_num
        unpivot the rows to columns
        count the number of absent and total attendance for each student
        :return: pandas dataframe
        |Name|Class|Absent Count|Attendance Taken|Absent Percentage|
        ------------------------------------------------------------
        """
        df = attendance_df[attendance_df['Timestamp'].str.len() > 0]
        df['row_num'] = (
            attendance_df
            .sort_values(['Timestamp'], ascending=False)
            .groupby(['Date:'])
            .cumcount() + 1
        )
        df = df[df['row_num'] == 1]
        df = df.drop(
            ['Timestamp', 'Total', 'date', 'row_num'],
            axis=1
        )
        # Unpivot
        df = df.melt(
            id_vars=["Date:"],
            var_name="Name",
            value_name="Value"
        )
        df['is_absent'] = df.apply(lambda row: is_absent(row), axis=1)
        absent_count_df = df[
            ['Name', 'is_absent']
        ].groupby('Name').agg(['sum', 'count']).reset_index()

        absent_count_df.columns = list(map('-'.join, absent_count_df.columns.values))
        absent_count_df = absent_count_df.rename(
            columns={
                "is_absent-sum": "Absent Count",
                "is_absent-count": "Attendance Taken"
            })
        # Calculate the absent percentage
        absent_count_df['Absent Percentage'] = (
            absent_count_df['Absent Count'] * 100 / absent_count_df['Attendance Taken']
        )
        absent_count_df['class'] = class_name
        return absent_count_df
