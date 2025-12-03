// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Attendance Entry Report"] = {
    "filters": [
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Select",
            "options": "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
            "default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1,
            "reqd": 1
        },
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Select",
            "options": "2023\n2024\n2025\n2026",
            "default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getFullYear(),
            "reqd": 1
        }
        
    ]
};