#Last Modifed by HELKYD 05-01-2023

from __future__ import unicode_literals
import sys
import frappe

@frappe.whitelist()
def apagar_ficheiros_uploaded():
	'''
		To delete all files after 1 week to avoid confusion...
	'''

	frappe.db.sql(""" DELETE from `tabFile` where is_folder = 0 """,as_dict=False);
	frappe.db.commit()
