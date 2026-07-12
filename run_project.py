import subprocess
import os
import sys
import time
import webbrowser
import threading
import signal
import socket
import re

# ============================================
# COLORS
# ============================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ============================================
# CONFIG
# ============================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
processes = []
# ============================================
# CONFIG
# ============================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
AUTH_TOKEN = "test_token"  # <-- YEH ADD KARO
processes = []

# ============================================
# BANNER
# ============================================
def print_banner():
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🧠  ENTERPRISE RAG SYSTEM - LAUNCHER                              ║
║                                                                      ║
║   Starting Backend + Frontend Services...                            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)

# ============================================
# CHECK PORTS - AUTO KILL
# ============================================
def is_port_in_use(port):
    """Check if port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_pid_using_port(port):
    """Get PID of process using a port"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port} | findstr LISTENING',
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit():
                        return pid
    except Exception as e:
        print(f"Error finding PID: {e}")
    return None

def kill_port(port):
    """Auto kill process using a port"""
    print(f"{Colors.YELLOW}🔍 Checking port {port}...{Colors.RESET}")
    
    pid = get_pid_using_port(port)
    
    if pid:
        print(f"{Colors.YELLOW}🔪 Killing process with PID: {pid}{Colors.RESET}")
        try:
            os.system(f"taskkill /PID {pid} /F")
            time.sleep(1)
            print(f"{Colors.GREEN}✅ Process {pid} killed successfully!{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to kill process: {e}{Colors.RESET}")
            return False
    else:
        print(f"{Colors.GREEN}✅ Port {port} is free!{Colors.RESET}")
        return True

def kill_all_python_processes():
    """Kill all Python processes (emergency)"""
    print(f"{Colors.YELLOW}🔪 Killing all Python processes...{Colors.RESET}")
    try:
        os.system("taskkill /F /IM python.exe 2>nul")
        time.sleep(1)
        print(f"{Colors.GREEN}✅ All Python processes killed!{Colors.RESET}")
        return True
    except:
        return False

# ============================================
# START SERVICES
# ============================================
def start_backend():
    print(f"{Colors.BLUE}🚀 Starting Backend Server...{Colors.RESET}")
    
    # Auto kill if port in use
    if is_port_in_use(BACKEND_PORT):
        kill_port(BACKEND_PORT)
    
    python = os.path.join(PROJECT_DIR, "venv", "Scripts", "python")
    backend_cmd = [
        python, "-m", "uvicorn", "app.main:app",
        "--reload", "--host", "127.0.0.1", "--port", str(BACKEND_PORT)
    ]
    
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    processes.append(("Backend", backend_process))
    return backend_process

def start_frontend():
    print(f"{Colors.BLUE}🚀 Starting Frontend Server...{Colors.RESET}")
    
    # Auto kill if port in use
    if is_port_in_use(FRONTEND_PORT):
        kill_port(FRONTEND_PORT)
    
    streamlit = os.path.join(PROJECT_DIR, "venv", "Scripts", "streamlit")
    frontend_cmd = [
        streamlit, "run", "app/frontend.py",
        "--server.port", str(FRONTEND_PORT),
        "--server.address", "127.0.0.1",
        "--server.headless", "true"
    ]
    
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    
    processes.append(("Frontend", frontend_process))
    return frontend_process

def open_browser():
    """Open browser after delay"""
    time.sleep(5)
    url = f"http://127.0.0.1:{FRONTEND_PORT}"
    print(f"{Colors.CYAN}🌐 Opening browser at: {url}{Colors.RESET}")
    webbrowser.open(url)

def shutdown_all():
    """Shutdown all services"""
    print(f"{Colors.YELLOW}🛑 Stopping all services...{Colors.RESET}")
    for name, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
            print(f"{Colors.GREEN}✅ {name} stopped{Colors.RESET}")
        except:
            try:
                proc.kill()
                print(f"{Colors.GREEN}✅ {name} killed{Colors.RESET}")
            except:
                pass

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    shutdown_all()
    sys.exit(0)

# ============================================
# MAIN
# ============================================
def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print_banner()
    
    # Check venv
    venv_path = os.path.join(PROJECT_DIR, "venv")
    if not os.path.exists(venv_path):
        print(f"{Colors.RED}❌ Virtual environment not found!{Colors.RESET}")
        print(f"{Colors.YELLOW}📌 Please run: .\\setup.bat{Colors.RESET}")
        input("Press Enter to exit...")
        return
    
    # Check requirements
    print(f"{Colors.CYAN}📌 Checking environment...{Colors.RESET}")
    
    # Start services
    backend = start_backend()
    time.sleep(2)
    frontend = start_frontend()
    time.sleep(2)
    
    # Open browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"{Colors.GREEN}✅ All services started!{Colors.RESET}")
    print(f"{Colors.CYAN}📌 Backend: http://127.0.0.1:{BACKEND_PORT}{Colors.RESET}")
    print(f"{Colors.CYAN}📌 Frontend: http://127.0.0.1:{FRONTEND_PORT}{Colors.RESET}")
    print(f"{Colors.YELLOW}📌 Press Ctrl+C to stop all services{Colors.RESET}")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_all()

if __name__ == "__main__":
    main()