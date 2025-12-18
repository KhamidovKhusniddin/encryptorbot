import qrcode
from io import BytesIO
from PIL import Image

def generate_qr_code(data: str) -> BytesIO:
    """
    Generate QR code from data and return as BytesIO object
    
    Args:
        data: String data to encode in QR code
        
    Returns:
        BytesIO object containing PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to BytesIO
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    return bio

def generate_password_qr(password: str, filename: str = None) -> BytesIO:
    """
    Generate QR code for password with optional filename
    
    Args:
        password: Password to encode
        filename: Optional filename to include in QR data
        
    Returns:
        BytesIO object containing PNG image
    """
    if filename:
        data = f"Password: {password}\nFile: {filename}"
    else:
        data = f"Password: {password}"
    
    return generate_qr_code(data)
