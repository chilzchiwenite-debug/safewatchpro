def calculate_severity(category):
    if not category:
        return "low"

    category = category.strip()

    high = [
        "Kidnapping",
        "Bandit Attack",
        "Terrorism"
    ]

    medium = [
        "Armed Robbery",
        "Fire Outbreak"
    ]

    if category in high:
        return "high"

    if category in medium:
        return "medium"

    return "low"