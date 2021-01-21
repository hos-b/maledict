from ui.main import MainWindow
from datetime import date
from calendar import monthrange
from misc.string_manip import parse_date

def records(task_id: int, sql_query: str, args: list,  main_window: MainWindow):
    if main_window.account is None:
        return ["current account not set"]
    table_name = main_window.account.name
    label = ''
    # show all records
    if task_id == 601:
        sql_query = sql_query.format(table_name)
        label = 'all transactions'
    # show monthly records
    elif task_id == 602:
        if args[0].count('.') != 1:
            return ["use format month.year for monthly queries"]
        m_str, y_str = args[0].split('.')
        try:
            month, year = int(m_str), int(y_str)
            dt_start = date(year=year, month=month, day=1)
            dt_end = date(year=year, month=month, day=monthrange(year, month)[1])
        except ValueError:
            return [f"invalid date {args[0]}, use correct month.year"]
        sql_query = sql_query.format(table_name, dt_start.isoformat(), dt_end.isoformat())
        label = f'transactions from {dt_start.month}'
    # show yearly records
    elif task_id == 603:
        try:
            year = int(args[0])
            dt_start = date(year=year, month=1, day=1)
            dt_end = date(year=year, month=12, day=31)
        except ValueError:
            return [f"invalid year {args[0]}"]
        sql_query = sql_query.format(table_name, dt_start.isoformat(), dt_end.isoformat())
        label = f'transactions from {dt_start.year}'
    # show expenses between two dates
    elif task_id == 604:
        errors = []
        dt_start = parse_date(args[0])
        if dt_start is None:
            errors.append(f'invalid date format. expected day.month.year|month.year, got {args[0]}')
        dt_end = parse_date(args[1])
        if dt_end is None:
            if args[1] != 'now':
                errors.append(f'invalid date format. expected day.month.year|month.year|now, got {args[1]}')
            else:
                dt_end = date.today()
        if dt_start != None and dt_end != None and dt_start >= dt_end:
            errors.append(f'start date cannot be larger than end date')
        if len(errors) > 0:
            return errors
        sql_query = sql_query.format(table_name, dt_start.isoformat(), dt_end.isoformat())
        label = f"transactions from {dt_start.day}.{dt_start.month}.{dt_start.year} to " \
                f"{dt_end.day}.{dt_end.month}.{dt_end.year}"
    # show expenses from last week
    elif task_id == 605:
        sql_query = sql_query.format(table_name)
        label = f'transactions from last week'
    # show expenses from last month
    elif task_id == 606:
        sql_query = sql_query.format(table_name)
        label = f'transactions from last month'
    # show expenses from last year
    elif task_id == 607:
        sql_query = sql_query.format(table_name)
        label = f'transactions from last year'

    main_window.account.query_transactions(sql_query, False)
    main_window.refresh_table_records(label)
    return []
