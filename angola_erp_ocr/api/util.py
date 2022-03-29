# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 29/03/2022


from __future__ import unicode_literals

import frappe
import angola_erp_ocr.util.ocr_pdf

@frappe.whitelist(allow_guest=True)
def ping():
    return 'lepdf_ocr'


@frappe.whitelist(allow_guest=True)
def pong(ficheiro):
    return 'lepdf_ocr'
    #return lerPdf_ocr(ficheiro)
