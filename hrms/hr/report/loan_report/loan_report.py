from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "month",
            "label": _("Month"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "gross_pay",
            "label": _("Gross Pay"),
            "fieldtype": "Currency",
            "width": 140,
            "options": "currency"
        },
        {
            "fieldname": "financial_loan_deduction",
            "label": _("Total Loan Deduction"),
            "fieldtype": "Currency",
            "width": 180,
            "options": "currency"
        },
        {
            "fieldname": "net_pay",
            "label": _("Net Pay"),
            "fieldtype": "Currency",
            "width": 140,
            "options": "currency"
        },
        {
            "fieldname": "posting_date",
            "label": _("Posting Date"),
            "fieldtype": "Date",
            "width": 120
        }
    ]

def get_data(filters=None):
    if not filters:
        filters = {}
    
    # Build filter conditions
    conditions = ["sl.docstatus = 1"]
    params = []
    
    # Fiscal Year filter
    if filters.get("fiscal_year"):
        try:
            fiscal_year = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
            conditions.append("sl.posting_date BETWEEN %s AND %s")
            params.extend([fiscal_year.year_start_date, fiscal_year.year_end_date])
        except:
            pass
    
    # Month filter
    if filters.get("month"):
        conditions.append("sl.month = %s")
        params.append(filters.get("month"))
    
    # Employee filters
    if filters.get("employee"):
        conditions.append("sl.employee = %s")
        params.append(filters.get("employee"))
    
    if filters.get("employee_name"):
        conditions.append("sl.employee_name LIKE %s")
        params.append("%" + filters.get("employee_name") + "%")
    
    # Company filter
    if filters.get("company"):
        conditions.append("sl.company = %s")
        params.append(filters.get("company"))
    
    # Department filter
    if filters.get("department"):
        conditions.append("sl.department = %s")
        params.append(filters.get("department"))
    
    # Branch filter
    if filters.get("branch"):
        conditions.append("sl.branch = %s")
        params.append(filters.get("branch"))
    
    # Build optimized query with subquery for Financial Institution Loan components
    query = """
        SELECT 
            sl.employee,
            sl.employee_name,
            sl.month,
            sl.gross_pay,
            sl.total_deduction,
            sl.net_pay,
            sl.posting_date,
            (
                SELECT COALESCE(SUM(sd.amount), 0)
                FROM `tabSalary Detail` sd
                WHERE sd.parent = sl.name
                AND sd.salary_component IN (
                    SELECT sc.name 
                    FROM `tabSalary Component` sc
                    WHERE sc.salary_component = 'Financial Institution Loan'
                )
            ) as financial_loan_deduction
        FROM `tabSalary Slip` sl
        WHERE {conditions}
        ORDER BY sl.posting_date DESC, sl.employee
    """.format(conditions=" AND ".join(conditions))
    
    # Execute query
    data = frappe.db.sql(query, tuple(params), as_dict=1)
    
    return data