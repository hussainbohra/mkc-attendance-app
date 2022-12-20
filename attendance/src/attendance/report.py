from .config import Config
from .sheets import GSheets
from .email import Email
from .utils import get_prev_saturdays
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
        advance_leave_requests = self.get_advance_leave_requests()
        latest_attendance = []
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
            last_attendance = attendance_df.sort_values(
                by='date', ascending=False
            ).reset_index().loc[0].to_dict()
            latest_attendance.append({
                'class_name': tab,
                'last_attendance': last_attendance
            })
        all_student_data = self.build_school_db()

        absentees, total = self.get_absentees(latest_attendance, all_student_data, advance_leave_requests)
        xlsx_file = self.writer.generate_csv_report(absentees, total)
        subject, message = self.email_obj.prepare_email(
            absentees,
            total,
            self.config['email']
        )
        self.email_obj.send_email(
            subject, message, xlsx_file,
            self.config['email']['to_emails'],
            self.config['email']['cc_emails']
        )

    def build_school_db(self):
        """
        Build a student data in the following format:
            {
                "class_name":{
                    "students" : [
                            {Ejamaat:1111111, 'full_name':xxxxx},
                            {Ejamaat:2222222, 'full_name':yyyyy}
                        ]
                    "teacher" : {Ejamaat:3333333, 'full_name':zzzzzzz}
                    "sub_teacher" : {Ejamaat:4444444, 'full_name':zzzzzzz}
                }
            }
        :param master_sheet_values:
        :param teachers:
        :return:
        """
        master_sheet = self.config['master_student_sheet_id']
        master_student_values = self.gsheet_obj.read_gsheet(
            master_sheet,
            self.config['master_student_sheet_tab'],
        )
        teachers = self.gsheet_obj.read_gsheet(
            master_sheet,
            self.config['master_teacher_sheet_tab'],
        )
        all_student_data = []
        for val in master_student_values:
            try:
                student_data = {
                    "full_name": val['Full Name'],
                    "home_phone": val['HOME PHONE'],
                    "father_cell": val['FATHER CELL'],
                    "father_name": val['FATHER'],
                    "mother_cell": val['MOTHER CELL'],
                    "mother_name": val['MOTHER'],
                    "primary_email": val['Primary Email'],
                    "class_name": val['Class']
                }
            except KeyError:
                continue
            teacher = list(filter(lambda a: a['Class'] == val['Class'], teachers))
            if teacher:
                student_data.update({
                    "teacher_Ejamaat": teacher[0]['Ejamaat'],
                    "teacher_full_name": teacher[0]['Full Name']
                })
            all_student_data.append(student_data)

        return all_student_data

    def get_absentees(self, latest_attendance, all_student_data, advance_leave_requests={}):
        """
        Identifying all Absentees and generate there information
        In addition, also creating a consolidated report

        :param class_name:
        :param all_students:
        :param present_student:
        :return:
        """
        print("[Get Absentees]: Identifying all Absentees")
        absentees = []
        total = []
        print("Iterating over the latest attendance, to identify absentees")
        for attendance in latest_attendance:
            absent_count, present_count, informed_absent_count = 0, 0, 0
            class_name = attendance.get("class_name")
            timestamp = attendance.get("last_attendance", {}).get("Timestamp")
            date = attendance.get("last_attendance", {}).get("Date:")
            if timestamp:
                for k, v in attendance.get("last_attendance", {}).items():
                    if k.strip().startswith('[') and k.strip().endswith(']'):
                        if str(v).lower() != "present":
                            student_name = k.strip().replace('[', '').replace(']', '')
                            leave_applied = list(filter(
                                lambda a: a['Class'] == class_name and a['student_name'] == student_name,
                                advance_leave_requests
                            ))
                            if leave_applied:
                                v = "Informed Absent (By Form)"
                            if v.lower() == "absent":
                                absent_count += 1
                            else:
                                informed_absent_count += 1
                            student_info = list(
                                filter(lambda a: a['full_name'].lower() == student_name.lower(), all_student_data))
                            absentee = {
                                "date": date,
                                "student_name": student_name,
                                "class_name": class_name,
                                "status": v,
                                "mother_info": "",
                                "father_info": "",
                                "primary_email": ""
                            }
                            if student_info:
                                absentee.update({
                                    "mother_info": f"{student_info[0].get('mother_name')} - {student_info[0].get('mother_cell')}",
                                    "father_info": f"{student_info[0].get('father_name')} - {student_info[0].get('father_cell')}",
                                    "primary_email": student_info[0].get('primary_email')
                                })
                            absentees.append(absentee)
                        else:
                            present_count += 1
            total.append({
                "date": date,
                "class_name": class_name,
                "present_count": present_count,
                "absent_count": absent_count,
                "informed_absent_count": informed_absent_count
            })
        print("[Get Absentees]: Exiting")
        return absentees, total

    def get_advance_leave_requests(self):
        """
        Read student leave request form and
        identify students who requested leave in advance

        :return:
        """
        prev_saturdays = get_prev_saturdays()
        print("fetching students who applied for leave in advance from {0} to {1}".format(
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
        student_cols = list(map(lambda a: "Student Name.%s" % str(a), range(0, 22)))
        filtered_df = filtered_df.replace(r'^\s*$', np.nan, regex=True)
        filtered_df['student_name'] = (
            filtered_df[student_cols]
            .bfill(axis=1).iloc[:, 0]
        )
        filtered_df = filtered_df.drop(columns=student_cols)
        filtered_df = filtered_df.loc[filtered_df['Request Type'] == 'Leave']
        filtered_df = filtered_df[['student_name', 'Class']]
        return filtered_df.to_dict("records")
