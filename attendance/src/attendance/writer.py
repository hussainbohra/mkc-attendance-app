from datetime import datetime
import xlsxwriter


class Writer:

    def __init__(self, config):
        self.file_prefix = config['email']['filename_prefix']

    def generate_csv_report(self, absentees, total):
        """
        Write an excel file
            Tab1: All students absent on a given day
            Tab2: Consolidated report
        :param absentees:
        :param total:
        :return:
        """
        filename = "{0}-{1}.xlsx".format(self.file_prefix, datetime.now().strftime('%Y-%m-%d'))
        workbook = xlsxwriter.Workbook(filename)
        for data in [
            {"data_type": "absentees", "data": absentees},
            {"data_type": "total", "data": total},
        ]:
            a_worksheet = workbook.add_worksheet(data["data_type"])
            row = 0
            for rows in data["data"]:
                col_num = 0
                for key, val in rows.items():
                    a_worksheet.set_column(row, col_num, 20)
                    if row == 0:
                        a_worksheet.write(row, col_num, key)
                    else:
                        a_worksheet.write(row, col_num, val)
                    col_num += 1
                row += 1
        workbook.close()
        return filename
