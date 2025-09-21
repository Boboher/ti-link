'''Contains all helper functions to reduce clutter'''

def string_is_valid_number(s):
        if not isinstance(s, str):
            return False

        # Check for a valid float with optional decimal point
        try:
            float(s)
        except ValueError:
            return False  # not a valid float

        # Split into parts to count digits
        parts = s.split(".")

        # Allow at most one dot
        if len(parts) > 2:
            return False

        # Count digits, ignore dot and optional leading minus sign
        digits = ''.join(parts)
        if digits.startswith('-'):
            return False

        if not digits.isdigit():
            return False

        if len(digits) > 10:
            return False

        return True