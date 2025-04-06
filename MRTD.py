import pprint

def scan_mrz():
    
    #Left empty as per requirements
    
    pass


def query_database():
    
    #Left empty as per requirements
    
    pass
def fletcher16(data: bytes) -> int:
    """Pure Fletcher-16 implementation"""
    sum1 = sum2 = 0
    for byte in data:
        sum1 = (sum1 + byte) % 255
        sum2 = (sum2 + sum1) % 255
    return (sum2 << 8) | sum1

def calculate_check_digit(data: str) -> int:
    """Calculate check digit using Fletcher-16 with MRZ rules"""
    if not data:
        return 0
    
    # Convert to MRZ format: uppercase and < becomes 0
    normalized = data.upper().replace('<', '0')
    
    # Calculate checksum on the raw ASCII bytes
    return fletcher16(normalized.encode('ascii')) % 10

#This function isnt neccessary but is useful for testing
def verify_mrz(line1: str, line2: str) -> dict:
    """Precision MRZ verification with exact field handling"""
    # Perfect padding and truncation
    line1 = (line1 + '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')[:44]
    line2 = (line2 + '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')[:44]
    
    # Precise name component separation
    name_parts = line1[5:].split('<<')
    last_name = name_parts[0].replace('<', ' ').strip()
    
    # Handle first and middle names correctly
    if len(name_parts) > 1:
        first_middle = name_parts[1].split('<', 1)  # Split on first single <
        first_name = first_middle[0].strip()
        middle_name = first_middle[1].replace('<', ' ').strip() if len(first_middle) > 1 else ''
    else:
        first_name = ''
        middle_name = ''
    
    decoded = {
        'line1': {
            'document_type': line1[0],
            'issuing_country': line1[2:5],
            'last_name': last_name,
            'first_name': first_name,  # Now only first name
            'middle_name': middle_name,  # Properly separated middle name
            'full_name': ' '.join(filter(None, [first_name, middle_name, last_name]))
        },
        'line2': {
            'passport_number': line2[0:9],
            'passport_number_check_digit': line2[9],
            'country_code': line2[10:13],
            'birth_date': line2[13:19],
            'birth_date_check_digit': line2[19],
            'sex': line2[20],
            'expiration_date': line2[21:27],
            'expiration_date_check_digit': line2[27],
            'personal_number': line2[28:36].replace('<', ''),
            'personal_number_filler': line2[36:42]  # Exactly 6 characters
        },
        'composite_check_digit': line2[43]  # Perfect position 44 (0-indexed 43)
    }

    results = {
        'valid': True,
        'details': {},
        'calculated': {},
        'debug': {
            'line1': line1,
            'line2': line2,
            'decoded': decoded
        }
    }

    def _verify(field: str, data: str, expected: str):
        """Precision verification with exact matching"""
        calculated = str(calculate_check_digit(data)) if data else '0'
        results['calculated'][field] = calculated
        is_valid = calculated == expected
        results['details'][field] = is_valid
        if not is_valid:
            results['valid'] = False

    # Exact field verifications
    _verify('passport_number', decoded['line2']['passport_number'], 
            decoded['line2']['passport_number_check_digit'])
    _verify('birth_date', decoded['line2']['birth_date'],
            decoded['line2']['birth_date_check_digit'])
    _verify('expiration_date', decoded['line2']['expiration_date'],
            decoded['line2']['expiration_date_check_digit'])

    # Perfect composite check (positions 1-43)
    composite_data = (
        line2[0:10] +    # Passport number + check (positions 1-10)
        line2[13:20] +   # Birth date + check + sex (positions 14-20)
        line2[21:28] +   # Expiration date + check (positions 22-28)
        line2[28:43]     # Personal number + filler (positions 29-43)
    )
    _verify('composite', composite_data, decoded['composite_check_digit'])

    return results

def decode_mrz(line1: str, line2: str) -> dict:
    """Decode MRZ lines with perfect name handling"""
    line1 = (line1 + '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')[:44]
    line2 = (line2 + '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')[:44]
    
    # Precise name parsing (same as verify_mrz)
    name_parts = line1[5:].split('<<')
    last_name = name_parts[0].replace('<', ' ').strip()
    
    if len(name_parts) > 1:
        first_middle = name_parts[1].split('<', 1)
        first_name = first_middle[0].strip()
        middle_name = first_middle[1].replace('<', ' ').strip() if len(first_middle) > 1 else ''
    else:
        first_name = ''
        middle_name = ''
    
    return {
        'line1': {
            'document_type': line1[0],
            'issuing_country': line1[2:5],
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name,
            'full_name': ' '.join(filter(None, [first_name, middle_name, last_name]))
        },
        'line2': {
            'passport_number': line2[0:9],
            'passport_number_check_digit': line2[9],
            'country_code': line2[10:13],
            'birth_date': line2[13:19],
            'birth_date_check_digit': line2[19],
            'sex': line2[20],
            'expiration_date': line2[21:27],
            'expiration_date_check_digit': line2[27],
            'personal_number': line2[28:36].replace('<', ''),
            'personal_number_filler': line2[36:42]
        },
        'composite_check_digit': line2[43]
    }

def encode_mrz(fields: dict) -> tuple:

    # ===== Line 1 Construction =====
    # Document type and fixed '<'
    line1 = fields.get('document_type', 'P') + '<'
    
    # Issuing country (3 chars)
    line1 += fields.get('issuing_country', '').upper().ljust(3)[:3]
    
    # Name components (last<<first<<middle)
    last_name = fields.get('last_name', '').upper().replace(' ', '<')
    first_name = fields.get('first_name', '').upper().replace(' ', '<')
    middle_name = fields.get('middle_name', '').upper().replace(' ', '<')
    
    # Build name component
    name_part = f"{last_name}<<{first_name}"
    if middle_name:
        name_part += f"<{middle_name}"  # Single < separator for middle name
    
    # Build line1
    line1 = (
        fields.get('document_type', 'P') + '<' +
        fields.get('issuing_country', '').ljust(3)[:3] +
        name_part.ljust(39, '<')[:39]
    ).ljust(44, '<')[:44]

    # ===== Line 2 Construction =====
    line2 = ''
    
    # Passport number (9 chars) + check digit
    passport_num = fields.get('passport_number', '').upper().ljust(9, '<')[:9]
    passport_check = str(calculate_check_digit(passport_num))
    line2 += passport_num + passport_check
    
    # Country code (3 chars)
    line2 += fields.get('country_code', '').upper().ljust(3)[:3]
    
    # Birth date (YYMMDD) + check digit
    birth_date = fields.get('birth_date', '').ljust(6, '<')[:6]
    birth_check = str(calculate_check_digit(birth_date))
    line2 += birth_date + birth_check
    
    # Sex (1 char)
    line2 += fields.get('sex', '<').upper()[0]
    
    # Expiration date (YYMMDD) + check digit
    exp_date = fields.get('expiration_date', '').ljust(6, '<')[:6]
    exp_check = str(calculate_check_digit(exp_date))
    line2 += exp_date + exp_check
    
    # Personal number (up to 9 chars) + filler + check digit
    personal_num = fields.get('personal_number', '').upper().replace(' ', '<')[:9]
    line2 += personal_num.ljust(9, '<')[:9]
    line2 += '<<<<<<'  # 6 filler chars (positions 38-43)
    
    # Calculate composite check digit (positions 1-10 + 13-20 + 21-28 + 29-43)
    composite_data = (
        line2[0:10] +  # Passport num + check
        line2[13:20] +  # Birth date + check + sex
        line2[21:28] +  # Exp date + check
        line2[28:43]    # Personal num + filler
    )
    composite_check = str(calculate_check_digit(composite_data))
    line2 += composite_check
    
    # Ensure line2 is exactly 44 characters
    line2 = line2.ljust(44, '<')[:44]
    
    return line1, line2

def verify_check_digits(mrz_data: dict) -> dict:
    results = {
        'valid': True,
        'details': {},
        'composite_data': None
    }

    def _verify(field_name: str, data: str, expected: str) -> bool:
        """Helper function with debug output"""
        calculated = str(calculate_check_digit(data))
        is_valid = calculated == expected
        if not is_valid:
            print(f"Check digit mismatch for {field_name}:")
            print(f"Data: '{data}' (len:{len(data)})")
            print(f"Calculated: {calculated} vs Expected: {expected}")
        return is_valid

    line2 = mrz_data['line2']
    
    # Individual field checks
    checks = [
        ('passport_number', line2['passport_number'], line2['passport_number_check_digit']),
        ('birth_date', line2['birth_date'], line2['birth_date_check_digit']),
        ('expiration_date', line2['expiration_date'], line2['expiration_date_check_digit']),
        ('personal_number', line2['personal_number'], line2['personal_number_check_digit'])
    ]
    
    for name, data, expected in checks:
        results['details'][name] = _verify(name, data, expected)
        if not results['details'][name]:
            results['valid'] = False

    # Composite check (positions 1-10 + 13-20 + 21-28 + 29-42)
    composite_data = (
        line2['passport_number'] + line2['passport_number_check_digit'] +
        line2['country_code'] +
        line2['birth_date'] + line2['birth_date_check_digit'] +
        line2['sex'] +
        line2['expiration_date'] + line2['expiration_date_check_digit'] +
        line2['personal_number'] + line2['personal_number_filler']
    )
    results['composite_data'] = composite_data
    results['details']['composite'] = _verify(
        'composite', 
        composite_data, 
        mrz_data['composite_check_digit']
    )
    
    return results
    
