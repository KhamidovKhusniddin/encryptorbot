import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO

def create_stats_graph(data, title, xlabel, ylabel):
    """
    Create a line graph from statistics data
    
    Args:
        data: List of tuples (date, value)
        title: Graph title
        xlabel: X-axis label
        ylabel: Y-axis label
        
    Returns:
        BytesIO object containing PNG image
    """
    if not data:
        # Create empty graph
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Ma\'lumot yo\'q', 
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=20)
        ax.set_title(title)
    else:
        dates = [item[0] for item in data]
        values = [item[1] for item in data]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=8)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save to BytesIO
    bio = BytesIO()
    plt.savefig(bio, format='png', dpi=100)
    bio.seek(0)
    plt.close(fig)
    
    return bio

def create_daily_users_graph(registrations_data):
    """Create graph for daily user registrations"""
    return create_stats_graph(
        registrations_data,
        'Kunlik Foydalanuvchilar',
        'Sana',
        'Foydalanuvchilar soni'
    )

def create_file_operations_graph(operations_data):
    """
    Create graph for file operations (encrypt/decrypt)
    
    Args:
        operations_data: List of tuples (date, action, count)
    """
    if not operations_data:
        return create_stats_graph([], 'Fayl Operatsiyalari', 'Sana', 'Operatsiyalar soni')
    
    # Separate encrypt and decrypt operations
    encrypt_data = {}
    decrypt_data = {}
    
    for date, action, count in operations_data:
        if action == 'encrypt':
            encrypt_data[date] = encrypt_data.get(date, 0) + count
        elif action == 'decrypt':
            decrypt_data[date] = decrypt_data.get(date, 0) + count
    
    # Get all unique dates
    all_dates = sorted(set(list(encrypt_data.keys()) + list(decrypt_data.keys())))
    
    encrypt_values = [encrypt_data.get(date, 0) for date in all_dates]
    decrypt_values = [decrypt_data.get(date, 0) for date in all_dates]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(all_dates, encrypt_values, marker='o', linestyle='-', linewidth=2, markersize=8, label='Shifrlash')
    ax.plot(all_dates, decrypt_values, marker='s', linestyle='-', linewidth=2, markersize=8, label='Deshifrlash')
    ax.set_title('Fayl Operatsiyalari', fontsize=16, fontweight='bold')
    ax.set_xlabel('Sana', fontsize=12)
    ax.set_ylabel('Operatsiyalar soni', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    bio = BytesIO()
    plt.savefig(bio, format='png', dpi=100)
    bio.seek(0)
    plt.close(fig)
    
    return bio
