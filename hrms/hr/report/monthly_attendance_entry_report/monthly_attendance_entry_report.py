import frappe
from frappe import _
from calendar import monthrange
from datetime import date, datetime

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150}
    ]
    
    month = filters.get('month')
    year = int(filters.get('year'))
    
    if isinstance(month, str):
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month = month_map.get(month, 1)
    else:
        month = int(month)
    
    _, num_days = monthrange(year, month)
    
    
    holidays = get_holidays_for_month(year, month)
    
    
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        is_holiday = is_date_holiday(current_date, holidays)
        
        day_label = str(day)
        
        if is_holiday:
            holiday_name = get_holiday_name(current_date, holidays)
            
            
            if holiday_name and 'saturday' in holiday_name.lower():
                day_label = f"{day} (Sat)"
            elif holiday_name and 'sunday' in holiday_name.lower():
                day_label = f"{day} (Sun)"
            else:
                day_label = f"{day} (H)"  
        
        columns.append({
            "label": day_label,
            "fieldname": f"day_{day:02d}",
            "fieldtype": "Data",
            "width": 55,
            "align": "center"
        })
    
    columns.extend([
        {"label": "P", "fieldname": "total_present", "fieldtype": "Int", "width": 40, "align": "center"},
        {"label": "HD", "fieldname": "total_half_day", "fieldtype": "Int", "width": 40, "align": "center"},
        {"label": "L", "fieldname": "total_leave", "fieldtype": "Int", "width": 40, "align": "center"},
        {"label": "T", "fieldname": "total_tour", "fieldtype": "Int", "width": 40, "align": "center"}
    ])
    
    return columns

def get_holidays_for_month(year, month):
    """Get all holidays for the given month and year"""
    holidays = []
    
    # Get all holiday lists
    holiday_lists = frappe.get_all("Holiday List", 
        filters={}, 
        fields=["name"]
    )
    
    for holiday_list in holiday_lists:
        # Get holidays from this holiday list
        holiday_dates = frappe.get_all("Holiday",
            filters={
                "parent": holiday_list.name,
                "parenttype": "Holiday List"
            },
            fields=["holiday_date", "description"]
        )
        
        
        for holiday in holiday_dates:
            holiday_date = holiday.holiday_date
            
            
            if isinstance(holiday_date, date):
                holiday_date_obj = holiday_date
            else:
                
                try:
                    holiday_date_obj = frappe.utils.getdate(holiday_date)
                except:
                    continue
            
            
            if holiday_date_obj.year == year and holiday_date_obj.month == month:
                holidays.append({
                    "holiday_date": holiday_date_obj,
                    "description": holiday.description
                })
    
    return holidays

def is_date_holiday(check_date, holidays):
    """Check if a given date is a holiday"""
    for holiday in holidays:
        holiday_date = holiday["holiday_date"]
        if holiday_date == check_date:
            return True
    return False

def get_holiday_name(check_date, holidays):
    """Get the name/description of holiday for a given date"""
    for holiday in holidays:
        holiday_date = holiday["holiday_date"]
        if holiday_date == check_date:
            return holiday["description"] or "Holiday"
    return "Holiday"

def get_data(filters):
    month = filters.get('month')
    year = int(filters.get('year'))
    
    if isinstance(month, str):
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month = month_map.get(month, 1)
    else:
        month = int(month)
    

    employees = frappe.get_all("Employee", 
        filters={"status": "Active"},
        fields=["name", "employee_name"]
    )
    
    
    holidays = get_holidays_for_month(year, month)
    

    all_dates_data = frappe.db.sql("""
        -- Get data from Attendance
        SELECT 
            employee,
            employee_name,
            attendance_date,
            DAY(attendance_date) as day,
            status,
            'Attendance' as source
        FROM `tabAttendance`
        WHERE MONTH(attendance_date) = %s 
            AND YEAR(attendance_date) = %s
            AND docstatus = 1
            
        UNION ALL
        
        -- Get data from Daily Entry  
        SELECT 
            employee,
            employee_name,
            attendance_date,
            DAY(attendance_date) as day,
            status,
            'Daily Entry' as source
        FROM `tabDaily Attendance Entry`
        WHERE MONTH(attendance_date) = %s 
            AND YEAR(attendance_date) = %s
    """, (month, year, month, year), as_dict=1)
    
    report_data = []
    
    for employee in employees:
        employee_record = {
            "employee": employee.name,
            "employee_name": employee.employee_name,
            "total_present": 0,
            "total_half_day": 0,
            "total_leave": 0,
            "total_tour": 0
        }
        
        
        for day in range(1, 32):
            employee_record[f"day_{day:02d}"] = ""
        
        
        emp_records = [d for d in all_dates_data if d.employee == employee.name]
        
        
        processed_days = {}
        
        for record in emp_records:
            day = record.day
            status_code = get_status_code(record.status)
            
            
            if day not in processed_days or record.source == 'Attendance':
                processed_days[day] = status_code
                employee_record[f"day_{day:02d}"] = status_code
        
        
        for day in range(1, 32):
            try:
                current_date = date(year, month, day)
                if is_date_holiday(current_date, holidays) and not employee_record[f"day_{day:02d}"]:
                    holiday_name = get_holiday_name(current_date, holidays)
                    
                    
                    if holiday_name and 'saturday' in holiday_name.lower():
                        employee_record[f"day_{day:02d}"] = "Sat"
                    elif holiday_name and 'sunday' in holiday_name.lower():
                        employee_record[f"day_{day:02d}"] = "Sun"
                    else:
                        employee_record[f"day_{day:02d}"] = "H"  
            except ValueError:
                
                pass
        
    
        for day, status_code in processed_days.items():
            if status_code == 'P':
                employee_record["total_present"] += 1
            elif status_code == 'HD':
                employee_record["total_half_day"] += 1
            elif status_code == 'L':
                employee_record["total_leave"] += 1
            elif status_code == 'T':
                employee_record["total_tour"] += 1
        
        report_data.append(employee_record)
    
    return report_data

def get_status_code(status):
    status_map = {
        "Present": "P",
        "Half Day": "HD",
        "Tour": "T",
        "On Leave": "L",
        "Leave": "L",
        "Work From Home": "WFH"
    }
    return status_map.get(status, status)