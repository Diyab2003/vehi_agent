OBD_CODES = {
    "P0171": {
        "description": "System too lean (Bank 1)",
        "severity": 0.6,
        "action": "DIY",
        "steps": [
            "Check for vacuum leaks",
            "Inspect mass air flow sensor",
            "Check fuel pressure"
        ]
    },
    "P0300": {
        "description": "Random or multiple cylinder misfire detected",
        "severity": 0.8,
        "action": "ESCALATE",
        "steps": [
            "Inspect spark plugs",
            "Check ignition coils",
            "Check fuel injectors"
        ]
    },
    "P0420": {
        "description": "Catalyst system efficiency below threshold",
        "severity": 0.7,
        "action": "ESCALATE",
        "steps": [
            "Inspect catalytic converter",
            "Check oxygen sensors"
        ]
    }
}


def lookup_obd(code: str):
    code = code.upper()
    return OBD_CODES.get(code, None)
