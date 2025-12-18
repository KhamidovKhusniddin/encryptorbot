import psutil
import os

def get_system_stats():
    """
    Get current system resource usage
    
    Returns:
        dict with CPU, RAM, and Disk usage statistics
    """
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # RAM usage
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
    ram_used_gb = ram.used / (1024 ** 3)
    ram_total_gb = ram.total / (1024 ** 3)
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_used_gb = disk.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)
    
    return {
        'cpu': {
            'percent': cpu_percent
        },
        'ram': {
            'percent': ram_percent,
            'used_gb': ram_used_gb,
            'total_gb': ram_total_gb
        },
        'disk': {
            'percent': disk_percent,
            'used_gb': disk_used_gb,
            'total_gb': disk_total_gb
        }
    }

def format_system_stats(stats):
    """
    Format system stats for display
    
    Args:
        stats: Dictionary from get_system_stats()
        
    Returns:
        Formatted string
    """
    return f"""💻 **Tizim Monitoring**

🔹 **CPU:** {stats['cpu']['percent']:.1f}%
🔹 **RAM:** {stats['ram']['percent']:.1f}% ({stats['ram']['used_gb']:.1f} GB / {stats['ram']['total_gb']:.1f} GB)
🔹 **Disk:** {stats['disk']['percent']:.1f}% ({stats['disk']['used_gb']:.1f} GB / {stats['disk']['total_gb']:.1f} GB)
"""
