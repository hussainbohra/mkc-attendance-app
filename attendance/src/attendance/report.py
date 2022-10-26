from .config import Config
from .sheets import GSheets
from .email import Email

from datetime import datetime
import pandas as pd
import xlsxwriter


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

    def generate_report(self):
        attendance_sheet = self.config['attendance_sheet_id']
        all_classes = self.gsheet_obj.get_sheets(attendance_sheet)

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

        absentees, total = self.get_absentees(latest_attendance, all_student_data)
        xlsx_file = self.generate_csv_report(absentees, total)
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

    def get_absentees(self, latest_attendance, all_student_data):
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
            absent_count, present_count = 0, 0
            class_name = attendance.get("class_name")
            timestamp = attendance.get("last_attendance", {}).get("Timestamp")
            date = attendance.get("last_attendance", {}).get("Date:")
            if timestamp:
                for k, v in attendance.get("last_attendance", {}).items():
                    if k.strip().startswith('[') and k.strip().endswith(']'):
                        if str(v).lower() != "present":
                            absent_count += 1
                            student_name = k.strip().replace('[', '').replace(']', '')
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
                "absent_count": absent_count
            })
        print("[Get Absentees]: Exiting")
        return absentees, total

    def generate_csv_report(self, absentees, total):
        """
        Write an excel file
            Tab1: All students absent on a given day
            Tab2: Consolidated report
        :param absentees:
        :param total:
        :return:
        """
        filename = "mkc-attendance-{0}.xlsx".format(datetime.now().strftime('%Y-%m-%d'))
        workbook = xlsxwriter.Workbook(filename)
        a_worksheet = workbook.add_worksheet("absentees")
        row = 0
        for absent in absentees:
            col_num = 0
            for key, val in absent.items():
                a_worksheet.set_column(row, col_num, 20)
                if row == 0:
                    a_worksheet.write(row, col_num, key)
                else:
                    a_worksheet.write(row, col_num, val)
                col_num += 1
            row += 1

        row = 0
        t_worksheet = workbook.add_worksheet("total")
        for t in total:
            col_num = 0
            for key, val in t.items():
                t_worksheet.set_column(row, col_num, 20)
                if row == 0:
                    t_worksheet.write(row, col_num, key)
                else:
                    t_worksheet.write(row, col_num, val)
                col_num += 1
            row += 1

        workbook.close()
        return filename
