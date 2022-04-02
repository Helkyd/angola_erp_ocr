# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 02/04/2022


from __future__ import unicode_literals

import frappe
import angola_erp_ocr.util
from angola_erp_ocr.util import ocr_pdf
from angola_erp_ocr.util import pdf_scrape
import os

from angola_erp_ocr.angola_erp_ocr.doctype.ocr_read import ocr_read

@frappe.whitelist(allow_guest=True)
def lepdfocr(data,action = "SCRAPE"):
	#TODO: add action SCRAPE or OCR
	#default will SCRAPE
	if action == "SCRAPE":
		print ('SCRAPE PDF')
		#print (dict(data))
		#return data.replace('/files','')

		if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
		else:
			filefinal = data

		#If no results... than change to OCR
		temScrape = pdf_scrape.pdfscrape_perpage(filefinal)
		print ('RESULTADO temScrape')
		print (temScrape)
		print ('datahora' in temScrape)
		if 'datahora' in temScrape:
			print (temScrape['datahora'])
			print (temScrape['referenciadestino'])
			if temScrape['datahora'] and temScrape['referenciadestino']:
				if temScrape['datahora'][0] != "" and temScrape['referenciadestino'][0] != "":
					print ('PODE TERMINAR....')
					return temScrape
				else:
					#Podemos fazer OCR with tesseract before trying with pytesseract
					""" File, Language, DPI
					angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document --args="['/home/frappe/pdfs/Modelo6_Teorl.pdf','por', '150']" """
					'''
					ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'por','150')
					print ('OCR TESSERACT')
					print ('OCR TESSERACT')
					print ('OCR TESSERACT')
					print (ocr_tesserac)
					if not ocr_tesserac:
					'''

					print ('TERA DE FAZER O OCR......')
					print ('TERA DE FAZER O OCR......')
					print ('TERA DE FAZER O OCR......')
					return ocr_pdf.ocr_pdf(input_path=data)

		elif 'modelo6IVA_numDeclaracao' in temScrape:
			print (temScrape['modelo6IVA_numDeclaracao'])
			print (temScrape['modelo6IVA_comprovativo'])

			if temScrape['modelo6IVA_numDeclaracao'][0] != "" and temScrape['modelo6IVA_comprovativo'][0] != "":
				#MODELO 6 iva
				print ('MODELO 6 iva')
				return temScrape
			else:
				print ('TERA DE FAZER O OCR......000')
				print ('TERA DE FAZER O OCR......000')
				print ('TERA DE FAZER O OCR......000')
				return ocr_pdf.ocr_pdf(input_path=data)



	elif action == "OCR":
		print ('OCR PDF')
		return ocr_pdf.ocr_pdf(input_path=data)
