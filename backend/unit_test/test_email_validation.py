"""
Test email validation logic
"""
import re

def validate_email(email):
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Test cases
test_emails = [
    # Valid emails
    ("user@example.com", True),
    ("test.user@example.com", True),
    ("user+tag@example.co.uk", True),
    ("user_name@example-domain.com", True),
    ("123@example.com", True),
    ("user@sub.example.com", True),
    
    # Invalid emails
    ("notanemail", False),
    ("@example.com", False),
    ("user@", False),
    ("user@.com", False),
    ("user @example.com", False),
    ("user@example", False),
    ("user@example.", False),
    ("user..name@example.com", False),  # This might pass but is technically invalid
    ("", False),
    ("user@", False),
]

print("=" * 60)
print("Email Validation Tests")
print("=" * 60)

passed = 0
failed = 0

for email, expected in test_emails:
    result = validate_email(email)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} | '{email}' -> {result} (expected {expected})")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 60)
