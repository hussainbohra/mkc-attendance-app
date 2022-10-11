from datetime import datetime
from nylas import APIClient


class Email:
    def __init__(self, client_id, client_secret, access_token):
        self.nylas_obj = APIClient(
            client_id, client_secret, access_token
        )

    def prepare_email(
        self, latest_attendance,
        subject, message, row
    ):
        """
        Build email subject and body

        :param latest_attendance:
        :return:
        """
        print("[Email]: Preparing Email")
        rows = []
        for attendance in latest_attendance:
            class_name = attendance.get("class_name")
            timestamp = attendance.get("last_attendance", {}).get("Timestamp")
            date = attendance.get("last_attendance", {}).get("Date:")
            if timestamp:
                for k, v in attendance.get("last_attendance", {}).items():
                    if k.strip().startswith('[') and k.strip().endswith(']') and str(v).lower() != "present":
                        rows.append(
                            row.format(
                                date,
                                k.strip().replace('[', '').replace(']', ''),
                                class_name, v,
                                "#FF0000" if str(v).lower() == "absent" else "#FFFF00"
                            ))
        subject = subject.format(datetime.now().strftime('%Y-%m-%d'))
        message = message.format(
            datetime.now().strftime('%Y-%m-%d'),
            "\n".join(rows)
        )
        return subject, message

    def send_email(self, subject, message, recipients):
        """
        Send an email

        :param subject:
        :param message:
        :param recipients:
        :return:
        """
        print(f"[Email]: Enter Send Email {subject}")
        draft = self.nylas_obj.drafts.create()
        draft.subject = subject
        draft.body = message
        draft.to = list(map(lambda a: {'email': a}, recipients))
        print(f"[Email]: Ready to Send Email {subject}")
        draft.send()
