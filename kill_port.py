import os
import subprocess
import re

port = 8000

# Find process using port
result = subprocess.run(f'netstat -ano | findstr :{port} | findstr LISTENING', 
                        capture_output=True, text=True, shell=True)

if result.stdout:
    lines = result.stdout.strip().split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) >= 5:
            pid = parts[-1]
            print(f"Killing PID: {pid} on port {port}")
            os.system(f"taskkill /PID {pid} /F")
            print(f"✅ Port {port} is now free!")
else:
    print(f"✅ Port {port} is already free!")