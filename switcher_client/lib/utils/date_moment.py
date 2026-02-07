from datetime import datetime, timedelta

class DateMoment:
    """
    A utility class for date and time manipulation, similar to moment.js functionality.
    """
    
    def __init__(self, date: datetime):
        self.date = date
    
    def get_date(self) -> datetime:
        return self.date
    
    def add(self, amount: int, unit: str) -> 'DateMoment':
        unit_lower = unit.lower()
        
        if unit_lower == 's':
            self.date += timedelta(seconds=amount)
        elif unit_lower == 'm':
            self.date += timedelta(minutes=amount)
        elif unit_lower == 'h':
            self.date += timedelta(hours=amount)
        else:
            raise ValueError(f"Unit {unit} not compatible - try [s, m or h]")
        
        return self