from datetime import datetime
from nylas import APIClient


class Email:
    def __init__(self, client_id, client_secret, access_token):
        self.nylas_obj = APIClient(
            client_id, client_secret, access_token
        )

    def prepare_email(
        self,
        absentees,
        total,
        config
    ):
        """
        Build email subject and body

        :param absentees:
        :param total:
        :param config:
        :return:
        """
        print("[Email]: Preparing Email")
        absentees_data = ""
        for absent in absentees:
            absentees_data += config["student_row"].format(
                absent["date"],
                absent["student_name"],
                absent["class_name"],
                absent["status"],
                absent["mother_info"],
                absent["father_info"],
                absent["primary_email"],
                "#FA5F55" if str(absent["status"]).lower() == "absent" else "#FFFF00",
            ) + "\n"
        total_data = ""
        total_present, total_informed_absent, total_uninformed_absent = 0, 0, 0
        for t in total:
            total_data += config["total_row"].format(
                t["date"],
                t["class_name"],
                t["present_count"],
                t["informed_absent_count"],
                t["absent_count"]
            ) + "\n"
            total_present += t["present_count"]
            total_informed_absent += t["informed_absent_count"]
            total_uninformed_absent += t["absent_count"]
        total_data += config["total_row"].format(
            t["date"],
            "Total",
            total_present,
            total_informed_absent,
            total_uninformed_absent
        ) + "\n"
        subject = config["subject"].format(datetime.now().strftime('%Y-%m-%d'))
        message = config["message"].format(
            datetime.now().strftime('%Y-%m-%d'),
            absentees_data,
            total_data
        )
        message += "\n\n\n"
        return subject, message

    def send_email(self, subject, message, filename, to_recipients, cc_recipients):
        """
        Send an email

        :param subject: Email subject
        :param message: Email message
        :param filename: File to attach
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
        draft.attach(self.attach_file(filename))
        print(f"[Email]: Ready to Send Email {subject}")
        draft.send()

    def attach_file(self, filename):
        """
        open and attach a file

        :param filename:
        :return:
        """
        attachment = open(filename, 'rb')
        file = self.nylas_obj.files.create()
        file.filename = filename
        file.stream = attachment
        file.save()
        attachment.close()
        return file
