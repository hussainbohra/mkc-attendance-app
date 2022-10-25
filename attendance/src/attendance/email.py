from datetime import datetime
from nylas import APIClient


class Email:
    def __init__(self, client_id, client_secret, access_token):
        self.nylas_obj = APIClient(
            client_id, client_secret, access_token
        )

    def prepare_email(
        self, latest_attendance,
        all_student_data, subject,
        message, student_row, total_row
    ):
        """
        Build email subject and body

        :param latest_attendance: Latest Attendance from all class
        :param all_student_data: Complete Database of all students
        :param subject:
        :param message:
        :param row:
        :return:
        """
        print("[Email]: Preparing Email")
        rows = []
        counts = []
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
                            rows.append(
                                student_row.format(
                                    date,
                                    student_name,
                                    class_name, v,
                                    student_info[0].get('mother_cell') if student_info else '',
                                    student_info[0].get('father_cell') if student_info else '',
                                    student_info[0].get('primary_email') if student_info else '',
                                    "#FA5F55" if str(v).lower() == "absent" else "#FFFF00"
                                ))
                        else:
                            present_count += 1
            counts.append(total_row.format(
                date, class_name, present_count, absent_count
            ))
        subject = subject.format(datetime.now().strftime('%Y-%m-%d'))
        message = message.format(
            datetime.now().strftime('%Y-%m-%d'),
            "\n".join(rows),
            "\n".join(counts)
        )
        message += "\n\n\n"
        return subject, message

    def send_email(self, subject, message, to_recipients, cc_recipients):
        """
        Send an email

        :param subject: Email subject
        :param message: Email message
        :param to_recipients: Email to recipients
        :param cc_recipients: Email cc recipients
        :return:
        """
        print(f"[Email]: Enter Send Email {subject}")
        draft = self.nylas_obj.drafts.create()
        draft.subject = subject
        draft.body = message
        draft.to = list(map(lambda a: {'email': a}, to_recipients))
        draft.cc = list(map(lambda a: {'email': a}, cc_recipients))
        print(f"[Email]: Ready to Send Email {subject}")
        draft.send()
