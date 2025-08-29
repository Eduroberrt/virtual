"""
DEPRECATED: Windows Service for automatically cancelling expired SMS rentals

This service is no longer needed since we now sync expiration status with DaisySMS API
instead of time-based expiration.

If this service is installed, you can remove it with:
python rental_service.py remove
"""

print("⚠️  DEPRECATED SERVICE ⚠️")
print("")
print("This auto-cancel service is no longer needed.")
print("We now sync expiration status with DaisySMS API instead of time-based expiration.")
print("")
print("If this service is installed, you can remove it with:")
print("python rental_service.py remove")
print("")
# This file has been deprecated and disabled to prevent any old functionality from running
