from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def format_currency(value):
    """Format number with commas and 2 decimal places"""
    try:
        if value is None:
            return "0.00"
        
        # Convert to float if it's a Decimal
        if isinstance(value, Decimal):
            value = float(value)
        
        # Format with commas and 2 decimal places
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

@register.filter
def format_naira(value):
    """Format Naira amount with ₦ symbol and commas"""
    try:
        if value is None:
            return "₦0.00"
        
        # Convert to float if it's a Decimal
        if isinstance(value, Decimal):
            value = float(value)
        
        # Format with commas and 2 decimal places
        return f"₦{value:,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"
