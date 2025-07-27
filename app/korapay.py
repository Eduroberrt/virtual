import requests
from django.conf import settings

class KoraPayClient:
    def __init__(self):
        self.secret_key = settings.KORAPAY_SECRET_KEY
        self.initialize_url = settings.KORAPAY_INITIALIZE_URL
        self.verify_url = settings.KORAPAY_VERIFY_URL

    def initiate_payment(self, user, amount, currency, redirect_url, reference=None, notification_url=None, narration=None):
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        if not reference:
            import uuid
            reference = f"YPG_{user.id}_{uuid.uuid4().hex[:8]}"
        
        # KoraPay expects amount in base currency (Naira), not kobo
        # Remove the kobo conversion that was causing 100x multiplication
        amount_for_payment = int(amount)  # Keep amount as-is in Naira
        
        payload = {
            "amount": amount_for_payment,  # Amount in Naira (not kobo)
            "currency": currency,
            "reference": reference,
            "redirect_url": redirect_url,
            "customer": {
                "email": user.email,
                "name": user.get_full_name() or user.username
            }
        }
        if notification_url:
            payload["notification_url"] = notification_url
        if narration:
            payload["narration"] = narration
            
        try:
            response = requests.post(self.initialize_url, headers=headers, json=payload, timeout=15)
            data = response.json()
            if data.get("status") and data.get("data", {}).get("checkout_url"):
                return {
                    "success": True,
                    "payment_link": data["data"]["checkout_url"],
                    "tx_ref": reference
                }
            return {"success": False, "error": data.get("message", "Failed to initiate payment")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_payment(self, reference):
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        # Use GET request with reference as query parameter (per Kora Pay docs)
        import logging
        logger = logging.getLogger(__name__)
        try:
            verify_url = f"{self.verify_url}?reference={reference}"
            logger.info(f"KoraPay verify_payment making request to: {verify_url}")
            response = requests.get(verify_url, headers=headers, timeout=15)
            logger.info(f"KoraPay verify_payment response status: {response.status_code}")
            
            # Check if request was successful
            if response.status_code != 200:
                logger.error(f"KoraPay verify_payment HTTP error {response.status_code} for reference {reference}: {response.text}")
                return {
                    "success": False,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "raw_response": response.text
                }
            
            try:
                data = response.json()
            except Exception as json_err:
                logger.error(f"KoraPay verify_payment JSON decode error for reference {reference}: {json_err}. Raw response: {response.text}")
                return {
                    "success": False,
                    "status": "failed",
                    "error": f"JSON decode error: {json_err}",
                    "raw_response": response.text
                }
            
            # Check if data is None
            if data is None:
                logger.error(f"KoraPay verify_payment received None response for reference {reference}")
                return {
                    "success": False,
                    "status": "failed",
                    "error": "Received null response from KoraPay API",
                    "raw_response": None
                }
                
            logger.info(f"KoraPay verify_payment response for reference {reference}: {data}")
            
            # Handle different response structures from KoraPay
            if isinstance(data, dict):
                # Check if the top-level response indicates success
                if data.get("status") == True or data.get("status") == "success":
                    payment_data = data.get("data", {})
                    
                    # Check the payment status in the data section
                    payment_status = payment_data.get("status")
                    if payment_status == "success" or payment_status == "successful":
                        # Amount is already in Naira (no conversion needed)
                        amount_naira = payment_data.get("amount", 0)
                        return {
                            "success": True,
                            "status": "successful",
                            "amount": amount_naira,
                            "tx_ref": reference,
                            "raw_response": data
                        }
                
                # Also check for alternative successful status patterns
                elif data.get("data", {}).get("status") in ["success", "successful", "paid"]:
                    payment_data = data.get("data", {})
                    # Amount is already in Naira (no conversion needed)
                    amount_naira = payment_data.get("amount", 0)
                    return {
                        "success": True,
                        "status": "successful", 
                        "amount": amount_naira,
                        "tx_ref": reference,
                        "raw_response": data
                    }
                
                # Payment was not successful
                return {
                    "success": False,
                    "status": data.get("data", {}).get("status", "failed"),
                    "error": data.get("message", "Payment verification failed"),
                    "raw_response": data
                }
            
            # If data is not a dict or empty
            return {
                "success": False,
                "status": "failed",
                "error": "Invalid response format",
                "raw_response": data
            }
        except Exception as e:
            logger.error(f"KoraPay verify_payment exception for reference {reference}: {str(e)}")
            return {"success": False, "status": "failed", "error": str(e)}

    def verify_webhook_signature(self, payload, signature):
        """Verify webhook signature from KoraPay"""
        import hashlib
        import hmac
        
        # KoraPay uses HMAC-SHA512 for webhook signature verification
        expected_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
