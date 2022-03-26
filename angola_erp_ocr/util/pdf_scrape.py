#Extracted from https://www.thepythoncode.com/article/extract-text-from-images-or-scanned-pdf-python
#Last Modifed by HELKYD 26-03-2022

from __future__ import unicode_literals

import frappe



import os
import re
import argparse
import pytesseract
from pytesseract import Output
import cv2
import numpy as np
import fitz
from io import BytesIO
from PIL import Image
import pandas as pd
import filetype

from frappe import throw, _
from frappe.frappeclient import FrappeClient

import csv

#Read CSV
import six
#import requests
from six import StringIO, text_type, string_types
#from frappe.utils import getdate
from frappe.utils.dateutils import parse_date
from six import iteritems



@frappe.whitelist(allow_guest=True)
def pdfscrape(ficheiropdf = None, empresa = None):
	#Can be used to read any PDF and extract TEXT from it...
    #Read a PDF from Multicaixa EXPRESS payment and extract
    #Date of Payment, Company paid to, IBAN paid to, Amount paid, Transaction number and IBAN from

	#we can get the number of pages using “pdf.doc.catalog[‘Pages’].resolve()[‘Count’]”. To extract data from a specific page, we can use “pdf.load(#)”.
	pagecount = pdf.doc.catalog['Pages'].resolve()['Count']
	master = pd.DataFrame()
	for p in range(pagecount):
	    pdf.load(p)
	    page = pdfscrape(pdf)
	    master = master.append(page, ignore_index=True)

	master.to_csv('output.csv', index = False)
	'''

	print ('Can be used to read any PDF and extract TEXT from it...')
	print ('Read a PDF from Multicaixa EXPRESS payment and extract')
	print ('Date of Payment, Company paid to, IBAN paid to, Amount paid, Transaction number and IBAN from ')
	print ('Before install pdfquery install pip install cffi==1.12.3')
	print ('STILL NEED TO INSTALL PDFQUERY and PANDAS')
	print ('STILL NEED TO COPY/INSTALL pdfminer and pyquery')

	'''
	import pdfquery
	import pandas as pd
    #Read a PDF from Multicaixa EXPRESS payment and extract
    #Date of Payment, Company paid to, IBAN paid to, Amount paid, Transaction number and IBAN from

	if not ficheiropdf:
		frappe.throw('Nao tem FICHEIRO em PDF...')
		return

	pdf  = pdfquery.PDFQuery(ficheiropdf)
	print ('carregou file')
	print (pdf)
	pdf.load()

	print ('load completed')

    #This can be removed... this was used to learn where fields are and get extract the TEXT
	pdf.tree.write('/tmp/pdfXML.txt',pretty_print=True)
	print ('generate tree')

	#Needs to know if is PDF from  MULTICAIXA Express
	datahora = ""
	empresa = ""
	iban = ""
	montante = ""
	transacao = ""
	origemIBAN = ""
	origemCONTA = ""
	origemEMPRESA = ""
	numerooperacao = ""
	referenciadestino = ""

	dadoscontribuinte = ""
	dadoscontribuinteNIF = ""
	referenciaANO = ""
	referenciaTIPO = ""
	referenciaPERIODO = ""
	referenciaPAGAMENTO = ""
	referenciadocumento = ""
	nifEmpresa = ""
	nomeEmpresa = ""
	descricaoRECEITA = ""
	impostoRECEITA = ""
	valoraPAGAR = ""
	valorPAGO = ""
	dataEMISSAO = ""
	datadePAGAMENTO = ""
	formadePAGAMENTO = ""



	pagamentovia = ""
	mcexpress = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("125.11, 697.043, 473.59, 708.043")').text()
	baidirecto = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("130.58, 714.61, 466.991, 724.57")').text()

	#Pagamento de DCs....Comprovativo de que foi paga a Retencao na Fonte ou outro Imposto.
	pagamentoDC = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("37.6, 13.04, 145.945, 18.04")').text()

	#File is PDF but as image....
	pdfasIMAGE = pdf.pq('LTFigure')[0].items()[3][1]

	print ('mcexpress ',mcexpress)
	print ('baidirecto ',baidirecto)
	print ('pagamentoDC ', pagamentoDC)
	print ('pdfasIMAGE ', pdfasIMAGE)

	pagamentovia = "QUEM"

	if ("OBJ2" or "OBJ1") in pdfasIMAGE:
		print ('Ficheiro PDF de IMAGEM....Nao pode extrair')
		return 'Ficheiro PDF de IMAGEM....Nao pode extrair'
	elif "MULTICAIXA Express" in mcexpress:
		pagamentovia = "MULTICAIXA Express"

		datahora = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("223.67, 615.843, 325.794, 626.843")').text()
		print ('tem datahora')

		empresa = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("223.67, 571.513, 457.772, 582.513")').text()
		print ('tem Empresa')

		iban = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("223.67, 549.353, 398.581, 560.353")').text()
		print ('tem IBAN')

		montante = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("223.67, 527.183, 288.493, 538.183")').text()
		print ('tem MONTANTE')

		transacao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("223.67, 505.023, 266.482, 516.023")').text()
		print ('tem TRANSACAO')

		origemIBAN = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("204.65, 284.274, 390.858, 292.274")').text()
		print ('tem origemIBAN')
	elif "serviço BAIDirecto" in baidirecto or "servi&#231;o BAIDirecto." in baidirecto:
		pagamentovia = "BAIDIRECTO"
		origemEMPRESA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 647.947, 357.205, 655.447")').text()
		print ('tem origemEMPRESA')

		origemCONTA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 630.447, 255.55, 637.947")').text()
		print ('tem origemCONTA')
		origemIBAN = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 613.447, 301.833, 620.947")').text()
		print ('tem origemIBAN')

		empresa = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 546.947, 232.6, 554.447")').text()
		print ('tem Empresa')
		iban = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 529.447, 299.748, 536.947")').text()
		print ('tem IBAN')

		numerooperacao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 430.447, 234.7, 437.947")').text()
		print ('tem numerooperacao')
		montante = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 394.447, 237.197, 401.947")').text()
		print ('tem MONTANTE')

		datahora = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 324.447, 261.805, 331.947")').text()
		print ('tem datahora')

		referenciadestino = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 359.447, 308.897, 366.947")').text()
		print ('tem referenciadestino')
	elif "EMITIDO EM: RF PORTAL DO CONTRIBUINTE" in pagamentoDC:
		#Pagamento da DC...
		pagamentovia = "PAGAMENTO DC"

		dadoscontribuinte = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("342.7, 680.657, 523.972, 687.657")').text()
		print ('tem dadoscontribuinte')
		dadoscontribuinteNIF = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("342.7, 627.723, 381.62, 634.723")').text()
		print ('tem dadoscontribuinteNIF')

		referenciadocumento = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("80.61, 581.623, 138.99, 588.623")').text()
		print ('tem referenciadocumento')
		referenciaANO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("199.216, 537.673, 214.784, 544.673")').text()
		print ('tem referenciaANO')
		referenciaPERIODO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("291.216, 537.673, 352.284, 544.673")').text()
		print ('tem referenciaPERIODO')

		#Imposto pago Retencao na fonte ou outro
		referenciaTIPO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("290.385, 493.723, 366.615, 500.723")').text()
		print ('tem referenciaTIPO')

		nifEmpresa = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("112.84, 449.773, 151.76, 456.773")').text()
		print ('tem nifEmpresa')
		nomeEmpresa = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("274.786, 449.773, 436.213, 456.773")').text()
		print ('tem nomeEmpresa')

		descricaoRECEITA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("141.351, 405.823, 299.649, 412.823")').text()
		print ('tem descricaoRECEITA')
		valortributavel = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("362.736, 405.823, 397.764, 412.823")').text()
		print ('tem valortributavel')
		impostoRECEITA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("446.523, 405.823, 462.476, 412.823")').text()
		print ('tem impostoRECEITA')
		valoraPAGAR = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("515.882, 405.823, 547.018, 412.823")').text()
		print ('tem valoraPAGAR')

		valorPAGO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("108.982, 192.44, 140.118, 199.44")').text()
		print ('tem valorPAGO')
		dataEMISSAO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("106.651, 167.94, 142.449, 174.94")').text()
		print ('tem dataEMISSAO')
		datadePAGAMENTO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("106.651, 143.44, 142.449, 150.44")').text()
		print ('tem datadePAGAMENTO')
		formadePAGAMENTO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("108.996, 94.565, 140.104, 101.565")').text()
		print ('tem formadePAGAMENTO')
		referenciaPAGAMENTO = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("101.198, 69.94, 147.902, 76.94")').text()
		print ('tem referenciaPAGAMENTO')


	if pagamentovia != "PAGAMENTO DC":
	    #Combined all information
		page = pd.DataFrame({
	        'datahora': datahora,
	        'empresa': empresa,
	        'iban': iban,
	        'montante': montante,
	        'transacao': transacao or numerooperacao,
	        'origemIBAN': origemIBAN or origemIBAN,
			'origemEMPRESA': "" or origemEMPRESA,
			'referenciadestino': "" or referenciadestino,
			'pagamentovia': pagamentovia
	    }, index=[0])
	else:
		#PAGAMENTO DC
		page = pd.DataFrame({
			'dadoscontribuinte': dadoscontribuinte,
			'dadoscontribuinteNIF': dadoscontribuinteNIF,
			'referenciaANO': referenciaANO,
			'referenciaTIPO': referenciaTIPO,
			'referenciaPERIODO': referenciaPERIODO,
			'referenciaPAGAMENTO': referenciaPAGAMENTO,
			'referenciadocumento': referenciadocumento,
			'nifEmpresa': nifEmpresa,
			'nomeEmpresa': nomeEmpresa,
			'descricaoRECEITA': descricaoRECEITA,
			'impostoRECEITA': impostoRECEITA,
			'valoraPAGAR': valoraPAGAR,
			'valorPAGO': valorPAGO,
			'dataEMISSAO': dataEMISSAO,
			'datadePAGAMENTO': datadePAGAMENTO,
			'formadePAGAMENTO': formadePAGAMENTO
	    }, index=[0])


	#print (page)

	dadospdf = page.to_dict()
	print (dadospdf)

	for ff,f1 in enumerate(dadospdf):
		print (ff)
		print (f1)
		print (dadospdf[f1][0])

	return dadospdf
