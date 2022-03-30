# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 29/03/2022


from __future__ import unicode_literals

import frappe
import angola_erp_ocr.util
from angola_erp_ocr.util import ocr_pdf


@frappe.whitelist(allow_guest=True)
def lepdfocr(data):
    import codecs
    #aaa = codecs.decode(data)
    ff = {'input_path': data}
    return ocr_pdf.ocr_pdf(input_path=data)


def ping():
    return 'lepdf_ocr'
