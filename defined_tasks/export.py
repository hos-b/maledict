from data.account import Account
import csv as pcsv

def csv(account: Account, path: str):
    if account is None:
        return ["current account not set"]
    
    try:
        file = open(path, 'w', newline='')
    except:
        return [f"could not write to {file}"]
    csv_writer = pcsv.writer(file, delimiter=',')
    
    query = f'SELECT * FROM {account.name} ORDER BY datetime(datetime) DESC;'
    db_records = account.database.query(query)
    for record in db_records:
        csv_writer.writerow(record)
    file.close()
    return [f"wrote all transactions to {path}"]
    