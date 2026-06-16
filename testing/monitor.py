import psutil
import time
import sys

duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60 # dalam detik
output_file = "system_resource_metrics.csv"

print(f"Perekam resource VM aktif selama {duration} detik...")
with open(output_file, "w") as f:
    f.write("timestamp,cpu_usage_percent,ram_usage_percent\n")
    
    start_time = time.time()
    while time.time() - start_time < duration:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        f.write(f"{timestamp},{cpu},{ram}\n")
        f.flush()

print(f"Perekaman selesai! Data tersimpan di {output_file}")
