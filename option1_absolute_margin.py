#!/usr/bin/env python
# Example showing how to add an absolute naira profit margin field

from django.db import models
from decimal import Decimal

class Service(models.Model):
    # ... existing fields ...
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Profit margin percentage (e.g., 15.00 for 15%)")
    
    # NEW FIELD for absolute naira profit margin
    profit_margin_naira = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Fixed profit margin in Naira (e.g., 100.00 for ₦100)")
    
    def get_naira_price(self):
        """Get price in Naira with profit margin - handles both USD and NGN stored prices"""
        from decimal import Decimal
        
        # Detect if price is stored in USD (< 100) or NGN (>= 100)
        if self.price < 100:
            # Price is stored in USD - convert to NGN first
            base_price_naira = Decimal(str(self.price)) * self.USD_TO_NGN_RATE
        else:
            # Price is already stored in NGN
            base_price_naira = Decimal(str(self.price))
        
        # Apply percentage profit margin
        percentage_margin = base_price_naira * (Decimal(str(self.profit_margin)) / Decimal('100'))
        
        # Apply absolute naira profit margin
        absolute_margin = Decimal(str(self.profit_margin_naira))
        
        # Total price = base price + percentage margin + absolute margin
        return base_price_naira + percentage_margin + absolute_margin
