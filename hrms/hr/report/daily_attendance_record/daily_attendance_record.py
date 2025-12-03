from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate, add_days

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    #chart = get_chart_data(data)
    report_summary = get_report_summary(data, filters)
    
    return columns, data, None, report_summary

def get_columns():
    return [
        {
            "fieldname": "employee",
            "label": _("Employee ID"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "attendance_date",
            "label": _("Attendance Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "sign_in_time",
            "label": _("Sign In Time"),
            "fieldtype": "Time",
            "width": 100
        },
        {
            "fieldname": "sign_out_time",
            "label": _("Sign Out Time"),
            "fieldtype": "Time",
            "width": 100
        },
        {
            "fieldname": "working_hours",
            "label": _("Working Hours"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 120
        }
       
    ]

def get_data(filters=None):
    if not filters:
        filters = {}
    
    # Set today as default if no dates provided
    if not filters.get("from_date"):
        filters["from_date"] = nowdate()
    if not filters.get("to_date"):
        filters["to_date"] = nowdate()
    
    conditions = get_conditions(filters)
    
    query = """
        SELECT 
            employee,
            employee_name,
            attendance_date,
            sign_in_time,
            sign_out_time,
            TIMEDIFF(sign_out_time, sign_in_time) as raw_working_hours,
            status
        FROM `tabDaily Attendance Entry`
        WHERE docstatus < 2
        {conditions}
        ORDER BY attendance_date DESC, employee_name
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, filters, as_dict=1)
    
    # Calculate working hours properly
    for row in data:
        if row.get('sign_in_time') and row.get('sign_out_time'):
            if row.get('raw_working_hours'):
                # Convert timedelta to hours
                total_seconds = row.raw_working_hours.seconds
                row.working_hours = total_seconds / 3600
            else:
                row.working_hours = 0
        else:
            row.working_hours = 0
        
        # Remove the temporary field
        if 'raw_working_hours' in row:
            del row['raw_working_hours']
    
    return data

def get_conditions(filters):
    conditions = []
    
    if filters.get("employee"):
        conditions.append("employee = %(employee)s")
    
    if filters.get("employee_name"):
        filters["employee_name"] = "%" + filters["employee_name"] + "%"
        conditions.append("employee_name LIKE %(employee_name)s")
    
    if filters.get("from_date"):
        conditions.append("attendance_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("attendance_date <= %(to_date)s")
    
    if filters.get("department"):
        conditions.append("department = %(department)s")
    
    if filters.get("status"):
        conditions.append("status = %(status)s")
    
    return " AND " + " AND ".join(conditions) if conditions else ""

def get_chart_data(data):
    if not data:
        return None
    
    # Prepare data for chart
    status_count = {}
    for row in data:
        status = row.get('status', 'Unknown')
        status_count[status] = status_count.get(status, 0) + 1
    
    labels = list(status_count.keys())
    values = list(status_count.values())
    
    chart = {
        "data": {
            "labels": labels,
            "datasets": [{
                "name": "Attendance Status",
                "values": values
            }]
        },
        "type": "pie",
        "colors": ["#28a745", "#dc3545", "#ffc107", "#6c757d", "#007bff"],
        "height": 300,
        "title": "Attendance Distribution"
    }
    
    return chart

def get_report_summary(data, filters):
    if not data:
        return []
    
    total_employees = len(set([d.employee for d in data]))
    total_records = len(data)
    
    # Calculate totals by status
    present_count = len([d for d in data if d.get('status') == 'Present'])
    absent_count = len([d for d in data if d.get('status') == 'Absent'])
    half_day_count = len([d for d in data if d.get('status') == 'Half Day'])
    leave_count = len([d for d in data if d.get('status') == 'On Leave'])
    
    # Calculate average working hours
    working_data = [d for d in data if d.get('working_hours') and d.get('working_hours') > 0]
    total_hours = sum([d.get('working_hours', 0) for d in working_data])
    avg_hours = total_hours / len(working_data) if working_data else 0
    
    return [
        {
            "value": total_employees,
            "label": _("Employees"),
            "indicator": "blue",
            "datatype": "Int"
        },
        {
            "value": present_count,
            "label": _("Present"),
            "indicator": "green",
            "datatype": "Int"
        },
        {
            "value": absent_count,
            "label": _("Absent"),
            "indicator": "red",
            "datatype": "Int"
        },
        {
            "value": half_day_count,
            "label": _("Half Day"),
            "indicator": "yellow",
            "datatype": "Int"
        },
        {
            "value": f"{avg_hours:.1f}",
            "label": _("Avg Hours"),
            "indicator": "orange",
            "datatype": "Float"
        }
    ]

# Optional: Add this function if you want to show a message when no data
def no_data_message(filters):
    return f"No attendance records found for {filters.get('from_date')} to {filters.get('to_date')}"