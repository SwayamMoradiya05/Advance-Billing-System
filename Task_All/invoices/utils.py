import json
import re
from io import BytesIO
import numpy as np
import cv2
from django.template.loader import get_template
from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict=None):
    """
    Renders a Django HTML template with context into a PDF binary string using xhtml2pdf (pisa).
    Returns binary PDF data if successful, or None if an error occurs.
    """
    if context_dict is None:
        context_dict = {}

    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()

    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def decode_qr_image(image_bytes):
    """
    Decodes a QR code from raw image bytes using OpenCV.
    Applies multi-stage image preprocessing (grayscale, adaptive thresholding, resizing)
    for high accuracy across varying lighting, orientations, and resolutions.

    Returns a dictionary:
    {
        'success': bool,
        'raw_data': str or None,
        'parsed_data': dict or None,
        'error': str or None
    }
    """
    if not image_bytes:
        return {
            'success': False,
            'raw_data': None,
            'parsed_data': None,
            'error': 'No image data provided for decoding.'
        }

    try:
        # Convert bytes to NumPy array and decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {
                'success': False,
                'raw_data': None,
                'parsed_data': None,
                'error': 'Invalid image format or corrupted file.'
            }

        detector = cv2.QRCodeDetector()
        decoded_text = None

        # Strategy 1: Direct detection on color image
        val, points, _ = detector.detectAndDecode(img)
        if val:
            decoded_text = val

        # Strategy 2: Grayscale conversion
        if not decoded_text:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            val, points, _ = detector.detectAndDecode(gray)
            if val:
                decoded_text = val

        # Strategy 3: Otsu Thresholding for contrast enhancement
        if not decoded_text:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            val, points, _ = detector.detectAndDecode(thresh)
            if val:
                decoded_text = val

        # Strategy 4: Rescale image if small or high-res
        if not decoded_text:
            h, w = img.shape[:2]
            for scale in [1.5, 2.0, 0.5]:
                resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
                val, points, _ = detector.detectAndDecode(resized)
                if val:
                    decoded_text = val
                    break

        if not decoded_text:
            return {
                'success': False,
                'raw_data': None,
                'parsed_data': None,
                'error': 'No QR code detected in the uploaded image. Please ensure the QR code is clear and unobstructed.'
            }

        # Parse the decoded content (JSON payload or structured invoice text)
        parsed_data = parse_qr_content(decoded_text)

        return {
            'success': True,
            'raw_data': decoded_text,
            'parsed_data': parsed_data,
            'error': None
        }

    except Exception as e:
        return {
            'success': False,
            'raw_data': None,
            'parsed_data': None,
            'error': f'QR code decoding failed: {str(e)}'
        }


def parse_qr_content(text):
    """
    Parses decoded QR text into structured fields.
    Handles JSON payloads (Advance Billing System invoice format) and key-value formats.
    """
    text = text.strip()

    # Try JSON parsing first
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {
                'type': 'json_invoice',
                'invoice_number': data.get('invoice') or data.get('invoice_number') or '',
                'customer_name': data.get('customer') or data.get('customer_name') or '',
                'invoice_date': data.get('date') or data.get('invoice_date') or '',
                'due_date': data.get('due_date') or '',
                'items_count': data.get('items_count'),
                'subtotal': data.get('subtotal'),
                'tax': data.get('tax') or data.get('tax_amount'),
                'total': data.get('total') or data.get('grand_total'),
                'status': data.get('status'),
                'verified': data.get('verified', True),
                'hash': data.get('hash') or '',
                'raw_json': data
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Try regex extraction for plain text invoices (e.g. "Invoice: INV-2026-001 | Total: 5000")
    inv_match = re.search(r'INV[-\w]+', text, re.IGNORECASE)
    total_match = re.search(r'(?:total|amount|rs\.?|₹)\s*[:=]?\s*([\d,]+(?:\.\d{2})?)', text, re.IGNORECASE)

    return {
        'type': 'plain_text',
        'invoice_number': inv_match.group(0) if inv_match else '',
        'total': total_match.group(1) if total_match else '',
        'content': text
    }
