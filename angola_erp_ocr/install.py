# -*- coding: utf-8 -*-
# Copyright (c) 2021, Monogramm and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe


def before_tests():
    """Frappe trigger before application tests."""
    settings = frappe.get_doc("System Settings")
    settings.time_zone = "Africa/Luanda"
    settings.language = "pt"
    settings.save()
    #selling_settings = frappe.get_doc("Selling Settings")
    #selling_settings.allow_multiple_items = 1
    #selling_settings.save()
