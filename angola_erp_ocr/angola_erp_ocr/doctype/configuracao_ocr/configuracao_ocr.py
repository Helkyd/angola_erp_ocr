# -*- coding: utf-8 -*-
# Copyright (c) 2022, Helio de Jesus and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.model.document import Document

class ConfiguracaoOCR(Document):
    def validate(self):
        if not self.resolucao_pdf > 0:
            frappe.throw(
                _("PDF Resolution must be a positive integer eg 300 (high) or 200 (normal)."))
