def calculate_severity(category):

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