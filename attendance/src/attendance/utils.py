from datetime import datetime, date, timedelta


def get_prev_saturdays():
    """
    get last saturday date
    :return:
    """
    today = date.today()
    # today = datetime.strptime('2022-12-20', '%Y-%m-%d')
    idx = (today.weekday() + 1) % 7
    if idx == 6:  # today == sat, return today and sat before that
        return (
            today - timedelta(7 + idx - 6),
            today
        )
    else:  # Sat went past, return prev sat and sat before that
        return (
            today - timedelta(7 + idx + 1),
            today - timedelta(7 + idx - 6)
        )


def is_absent(row):
    """
    If value is empty and absent, then returns 1
    :param row:
    :return:
    """
    if type(row['Value']) == str and row['Value'].lower() == 'absent':
        return 1
    else:
        return 0