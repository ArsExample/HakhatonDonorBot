def phone_validation(phone: str) -> str:
    phone = phone.replace(" ", "")
    if len(phone) == 11:
        if phone.isnumeric():
            if phone[0] == "8" or phone[0] == "7":
                return f"+7{phone[1:]}"
    elif len(phone) == 12:
        if phone[1:].isnumeric():
            if phone[1] == "7":
                if phone[0] == "+":
                    return phone
    return "error"
