from .config import Config
from .sheets import GSheets
from .email import Email

import pandas as pd


class Report:
    def __init__(self, config_file):
        """

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
        subject, message = self.email_obj.prepare_email(
            latest_attendance,
            all_student_data,
            self.config['email']['subject'],
            self.config['email']['message'],
            self.config['email']['student_row'],
            self.config['email']['total_row']
        )
        self.email_obj.send_email(
            subject, message,
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
                    "mother_cell": val['MOTHER CELL'],
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

    def get_absentees(self, class_name, all_students, present_student):
        """

        :param class_name:
        :param all_students:
        :param present_student:
        :return:
        """
        pass
