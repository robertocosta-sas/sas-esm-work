from psycopg2 import connect, OperationalError
import matplotlib.pyplot as plt
from pandas import DataFrame
from getpass import getpass
from datetime import datetime
import traceback
import time

timeout_time = 10

def sanitize_input(input_str):
    """Remove embedded null characters and strip leading/trailing whitespaces."""
    return input_str.replace('\0', '').strip()

def query_db():
    user = sanitize_input(input("Enter your username (esm): ") or "esm")
    password = sanitize_input(getpass("Enter your password (Orion123): ") or "Orion123")
    dbname = sanitize_input(input("Enter the database name (esm): ") or "esm")
    host = sanitize_input(input("Enter the host (localhost): ") or "localhost")
    port = sanitize_input(input("Enter the port (15432): ") or "15432")
    first_time = True
    plt.ion()
    fig_size = None

    while True:
        try:
            if len(plt.get_fignums()) > 0:
                fig_size = plt.gcf().get_size_inches()
            plt.show(block=False)
            plt.clf()
            plt.pause(0.1)
            with connect(dbname=dbname, user=user, host=host, password=password, port=port) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
					WITH LatestSessionEntries AS (
					  SELECT
						psam.owner,
						psam.pid,
						psam.session_id,
						psam.timestamp,
						psam.temp_size,
						ROW_NUMBER() OVER (PARTITION BY psam.session_id ORDER BY psam.timestamp DESC) AS rn
					  FROM
						public.process_stats_agg_min psam
					  WHERE
						psam.temp_size IS NOT NULL
					),
					FilteredSessions AS (
					  SELECT
						ls.owner,
						ls.pid,
						ls.session_id,
						ls.timestamp,
						ls.temp_size
					  FROM
						LatestSessionEntries ls
					  JOIN
						public.session s ON ls.session_id = s.id
					  WHERE
						s.end_time IS NULL
						AND ls.rn = 1
					)
					SELECT
					  *
					FROM
					  FilteredSessions
					ORDER BY
					  timestamp DESC;        
					""")
                    records = cur.fetchall()

            if not records:
                print("No sessions found. Sleeping " + str(timeout_time) + " seconds...")
                plt.close(fig)
                time.sleep(timeout_time)
                continue

            df = DataFrame(records, columns=['User', 'PID', 'Session ID', 'Last Timestamp', 'Work Area (MB)'])

            if first_time:
                print(df)
                first_time = False
            else:
                print(df.to_string(index=False, header=False))
            print("***")

            # Calculate total work area and set up the pie chart formatting
            total_work_area = df['Work Area (MB)'].sum()
            total_work_area_str = "{:.2f} GB".format(total_work_area / 1024) if total_work_area > 1024 else "{:.2f} MB".format(total_work_area)

            # Autopct formatting function
            def autopct_format(pct):
                val = int(round(pct * total_work_area / 100.0))
                val_str = "{:.2f} GB".format(val / 1024) if val > 1024 else "{:.1f} MB".format(val)
                return '{p:.1f}%\n({v})'.format(p=pct, v=val_str)

            # Process 'Others' and plot
            work_area_by_user = df.groupby('User')['Work Area (MB)'].sum()
            others = work_area_by_user[work_area_by_user / total_work_area <= 0.05].sum()
            work_area_by_user = work_area_by_user[work_area_by_user / total_work_area > 0.05]
            work_area_by_user['Others'] = others

            if fig_size is not None and len(fig_size)>0:
                work_area_by_user.plot.pie(autopct=autopct_format, startangle=140, figsize=fig_size)
            else:
                work_area_by_user.plot.pie(autopct=autopct_format, startangle=140, figsize=(5, 5))
            current_time = datetime.now().strftime("%H:%M:%S")
            plt.gcf().canvas.manager.set_window_title(f'SAS Work at {current_time}')
            num_users = df['User'].nunique()
            plt.title(f'Work Area - Total: {total_work_area_str}, Users: {num_users} at [{current_time}]')
            plt.ylabel('')
            plt.draw()
            plt.pause(0.1)

        except OperationalError as e:
            print("Please check your database credentials or connection settings.")
            print(f"An error occurred: {e}")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
        finally:
            if 'conn' in locals() and conn is not None:
                conn.close()

        plt.pause(timeout_time)
        if not plt.get_fignums():
            break

if __name__ == "__main__":
    query_db()

