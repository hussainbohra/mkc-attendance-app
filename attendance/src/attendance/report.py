from .config import Config
from .sheets import GSheets


class Report:
    def __init__(self, config_file):
        """

        :param credentials:
            a json file
        """
        self.config = Config(config_file).get_config()

    def generate_report(self):
        gsheet_obj = GSheets(
            self.config['credentials_file'],
            self.config['scopes']
        )
        attendance_sheet = self.config['attendance_sheet_id']
        master_sheet = self.config['attendance_sheet_id']
        all_classes = gsheet_obj.get_sheets(self.config['master_student_sheet_id'])
        print(all_classes)
        # master_list = gsheet_obj.read_gsheet(self.config['master_student_sheet_id'])
        for tab in all_classes:
            data = gsheet_obj.read_gsheet(
                attendance_sheet,
                tab_name=tab
            )
            print(tab)
            print(data)
