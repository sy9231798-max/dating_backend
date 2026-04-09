import phonenumbers
from fastapi import HTTPException


def validate_phone_number(phone: str, region: str = "IN") -> bool:
    """
    Validates an international phone number using phonenumbers library.

    Args:
        phone (str): The phone number to validate.
        region (str, optional): Region code (like 'US', 'IN'). Used if the number is not in international format.

    Returns:
        str: The formatted international phone number.

    Raises:
        HTTPException: If the phone number is invalid.
    """
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")

    try:
        parsed = phonenumbers.parse(phone, region)
        if not phonenumbers.is_valid_number(parsed):
            raise HTTPException(status_code=400, detail="Invalid phone number")
        # Return E.164 format: +1234567890
        return True
        # return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        raise HTTPException(status_code=400, detail="Invalid phone number format")
