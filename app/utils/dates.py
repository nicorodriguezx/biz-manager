from datetime import date, datetime, timedelta

def get_date_range(range_type):
    """Returns (start_date, end_date) in ISO format for the given range type"""
    today = date.today()
    
    if range_type == 'today':
        return today.isoformat(), today.isoformat()
        
    if range_type == 'last-7':
        start = today - timedelta(days=6)
        return start.isoformat(), today.isoformat()
        
    if range_type == 'this-month':
        start = date(today.year, today.month, 1)
        return start.isoformat(), today.isoformat()
        
    if range_type == 'last-30':
        start = today - timedelta(days=29)
        return start.isoformat(), today.isoformat()
        
    return None, None

def get_range_type(start_date, end_date):
    """Returns the range type for the given dates, or 'custom' if no match"""
    if not start_date or not end_date:
        return 'today'
        
    today = date.today().isoformat()
    if end_date != today:
        return 'custom'
        
    # Convert dates for comparison
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Today
    if start_date == end_date:
        return 'today'
        
    # Last 7 days
    seven_days_ago = date.today() - timedelta(days=6)
    if start == seven_days_ago:
        return 'last-7'
        
    # This month
    month_start = date(date.today().year, date.today().month, 1)
    if start == month_start:
        return 'this-month'
        
    # Last 30 days
    thirty_days_ago = date.today() - timedelta(days=29)
    if start == thirty_days_ago:
        return 'last-30'
        
    return 'custom' 