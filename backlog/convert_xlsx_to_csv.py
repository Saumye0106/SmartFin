import os
import pandas as pd

BACKLOG_DIR = os.path.dirname(__file__)

def convert_all():
    files = [f for f in os.listdir(BACKLOG_DIR) if f.lower().endswith(('.xlsx', '.xls'))]
    if not files:
        print('No Excel files found in backlog directory.')
        return

    for f in files:
        src = os.path.join(BACKLOG_DIR, f)
        name, _ = os.path.splitext(f)
        dest = os.path.join(BACKLOG_DIR, name + '.csv')
        print(f'Converting {src} -> {dest}')
        try:
            df = pd.read_excel(src)
            df.to_csv(dest, index=False)
            print('  Done')
        except Exception as e:
            print('  Failed:', e)

if __name__ == '__main__':
    convert_all()
