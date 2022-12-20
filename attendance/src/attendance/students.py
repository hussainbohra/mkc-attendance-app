from .models import Student


class StudentDB:
    def __init__(self, config, gsheet_obj):
        self.master_sheet = config['master_student_sheet_id']
        self.master_sheet_tab = config['master_student_sheet_tab']

        self.gsheet_obj = gsheet_obj

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
        print("[Build School DB]: Read master student sheet")
        all_student_data = []
        master_student_values = self.gsheet_obj.read_gsheet(
            self.master_sheet,
            self.master_sheet_tab,
        )
        teachers = self.gsheet_obj.read_gsheet(
            self.master_sheet,
            self.master_sheet_tab,
        )
        for val in master_student_values:
            try:
                student = Student(
                    val['Full Name'], val['HOME PHONE'], val['FATHER CELL'], val['FATHER'],
                    val['MOTHER CELL'], val['MOTHER'], val['Primary Email'], val['Class']
                )
                teacher = list(filter(lambda a: a['Class'] == val['Class'], teachers))
                if teacher:
                    student.teacher_id = teacher[0]['Ejamaat']
                    student.teacher_full_name = teacher[0]['Full Name']
                all_student_data.append(student)
            except KeyError:
                continue

        return all_student_data
