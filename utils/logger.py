# logger.py
import os
from datetime import datetime

# Get the absolute path to the directory one level up from this file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define the logs directory inside Main_folder
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Default log path (can be updated by create_new_log)
_log_path = None

def create_new_log(name: str = None):
    """
    Creates a new log file with the current date and time.
    Optionally takes a name to make the log more identifiable.
    Also deletes oldest logs if there are more than 5.
    """
    global _log_path

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    if name:
        safe_name = name.replace(" ", "_").replace("/", "_")
        log_filename = f"{timestamp}-{safe_name}-log.txt"
    else:
        log_filename = f"{timestamp}-log.txt"

    _log_path = os.path.join(log_dir, log_filename)

    # Create an empty file immediately (optional, but helpful)
    with open(_log_path, "w") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Log created.\n")

    # Clean up old log files
    _enforce_log_limit(max_logs=5)

def log(message: str):
    """
    Writes a timestamped log message to the current log file.
    """
    global _log_path

    # Fallback to daily file if no log has been created
    if _log_path is None:
        date_filename = datetime.now().strftime("%Y-%m-%d") + "-log.txt"
        _log_path = os.path.join(log_dir, date_filename)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"

    with open(_log_path, "a") as log_file:
        log_file.write(formatted + "\n")


def _enforce_log_limit(max_logs=5):
    """
    Deletes the oldest log files if there are more than `max_logs` in the directory.
    """
    log_files = [f for f in os.listdir(log_dir) if f.endswith(".txt")]
    if len(log_files) <= max_logs:
        return

    # Sort by creation time (oldest first)
    full_paths = [os.path.join(log_dir, f) for f in log_files]
    full_paths.sort(key=os.path.getctime)

    # Delete oldest files to maintain the limit
    for path in full_paths[:-max_logs]:
        try:
            os.remove(path)
        except Exception as e:
            print(f"Failed to delete log file {path}: {e}")
