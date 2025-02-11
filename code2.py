import pandas as pd
import dask.dataframe as dd
import psutil
import time
import os
import threading

def read_parquet(file_path):
    start_time = time.time()
    process = psutil.Process(os.getpid())

    # Monitor CPU and memory usage
    cpu_percentages = []
    memory_usages = []
    monitoring = True

    def monitor_resources():
        while monitoring:
            cpu_percentages.append(process.cpu_percent(interval=None))
            memory_usages.append(process.memory_info().rss / (1024 * 1024))  # Convert to MB
            time.sleep(0.1)

    monitor_thread = threading.Thread(target=monitor_resources)
    monitor_thread.start()

    # Read the Parquet file using Dask for parallel processing
    try:
        columns = ['line_item_blended_cost', 'line_item_line_item_description']
        ddf = dd.read_parquet(file_path, engine='pyarrow', columns=columns)
    except Exception as e:
        print(f"Error reading Parquet file: {e}")
        monitoring = False
        monitor_thread.join()
        return

    # Calculate cost details with Dask
    try:
        total_cost = ddf['line_item_blended_cost'].sum().compute()
        tax_cost = ddf[ddf['line_item_line_item_description'].str.contains('Tax', case=False, na=False)]['line_item_blended_cost'].sum().compute()
        usage_cost = total_cost - tax_cost
    except KeyError as e:
        print(f"Column not found: {e}")
        return

    cost_details = {
        "cost_details": {
            "total_cost": f"{total_cost:.2f}",
            "tax_cost": f"{tax_cost:.2f}",
            "usage_cost": f"{usage_cost:.2f}"
        }
    }

    # Stop monitoring
    monitoring = False
    monitor_thread.join()

    end_time = time.time()

    # Calculate average CPU and memory usage
    avg_cpu = sum(cpu_percentages) / len(cpu_percentages) if cpu_percentages else 0
    avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 0

    print("Output:")
    print(cost_details)

    print("\nSystem Configuration and Resource Usage:")
    print(f"Elapsed time: {end_time - start_time:.2f} seconds")
    print(f"Average CPU usage: {avg_cpu:.2f}%")
    print(f"Average Memory usage: {avg_memory:.2f} MB")
    print(f"System configuration: {psutil.virtual_memory().total / (1024 * 1024):.2f} MB RAM")

# Replace with the path to your Parquet file
file_path = r"D:\Valuebound-Training\projects\Parquet-Project\CUR10MB (1).parquet"

read_parquet(file_path)

# Output:
# {'cost_details': {'total_cost': '3123.76', 'tax_cost': '476.32', 'usage_cost': '2647.44'}}

# System Configuration and Resource Usage:
# Elapsed time: 0.81 seconds
# Average CPU usage: 56.55%
# Average Memory usage: 193.76 MB
# System configuration: 14157.50 MB RAM
