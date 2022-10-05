#Extracted from https://www.thepythoncode.com/article/extract-text-from-images-or-scanned-pdf-python
#Last Modifed by HELKYD 05-10-2022

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


import pdfquery
import pandas as pd

modelo6IVA = ""
modelo6IVA_comprovativo = ""
modelo6IVA_numDeclaracao = ""
modelo6IVA_DataEmissao = ""
modelo6IVA_NomeEmpresa = ""
modelo6IVA_DataSubmissao = ""
modelo6IVA_RegimeIVA_GERA = ""
modelo6IVA_RegimeIVA_SIMP = ""
modelo6IVA_GrupoB = ""
modelo6IVA_RegimeIVA_II = ""
modelo6IVA_NIF = ""

@frappe.whitelist(allow_guest=True)
def pdfscrape_perpage(ficheiropdf = None, empresa = None):


	if not ficheiropdf:
		frappe.throw('Nao tem FICHEIRO em PDF...')
		return


	pdf  = pdfquery.PDFQuery(ficheiropdf)


	#we can get the number of pages using “pdf.doc.catalog[‘Pages’].resolve()[‘Count’]”. To extract data from a specific page, we can use “pdf.load(#)”.
	scrapresult = {}
	pagecount = pdf.doc.catalog['Pages'].resolve()['Count']
	master = pd.DataFrame()
	for p in range(pagecount):
		pdf.load(p)
		page = pdf_scrape(pdf)
		if not scrapresult:
			scrapresult = page
		else:
			scrapresult.update(page)
		master = master.append(page, ignore_index=True)

	print ('GRAVAR FILE')
	print (scrapresult)
	#print (master['datahora'])
	#print (master['datahora'][0])
	#print (master['empresa'][0])

	return scrapresult #master

def pdf_scrape(pdf):


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

	global modelo6IVA
	global modelo6IVA_comprovativo
	global modelo6IVA_numDeclaracao
	global modelo6IVA_DataEmissao
	global modelo6IVA_NomeEmpresa
	global modelo6IVA_DataSubmissao
	global modelo6IVA_RegimeIVA_GERA
	global modelo6IVA_RegimeIVA_SIMP
	global modelo6IVA_GrupoB
	global modelo6IVA_RegimeIVA_II
	global modelo6IVA_NIF


	#Check if PDF is AGT Modelo 6
	if not modelo6IVA_comprovativo:
		modelo6IVA_comprovativo = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("181.813, 728.221, 335.637, 737.741")').text()	#Comprovativo de Entrega de Declara&#231;&#227;o
	if not modelo6IVA:
		modelo6IVA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("227.829, 718.701, 289.621, 728.221")').text()	#Modelo 6 de IVA
	#modelo6IVA_numDeclaracao = ""

	pagamentovia = ""
	mcexpress = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("125.11, 697.043, 473.59, 708.043")').text()
	baidirecto = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("130.58, 714.61, 466.991, 724.57")').text()

	#Pagamento de DCs....Comprovativo de que foi paga a Retencao na Fonte ou outro Imposto.
	pagamentoDC = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("37.6, 13.04, 145.945, 18.04")').text()

	#File is PDF but as image....
	print ('IMAGEM ',pdf.pq('LTFigure'))
	if pdf.pq('LTFigure'):
		pdfasIMAGE = pdf.pq('LTFigure')[0].items()[3][1]
	else:
		pdfasIMAGE = "PDF"

	print ('mcexpress ',mcexpress)
	print ('baidirecto ',baidirecto)
	print ('pagamentoDC ', pagamentoDC)
	print ('pdfasIMAGE ', pdfasIMAGE)

	pagamentovia = "QUEM"

	if ("OBJ2" or "OBJ1") in pdfasIMAGE:
		print ('Ficheiro PDF de IMAGEM....Nao pode extrair')
		return 'Ficheiro PDF de IMAGEM....Nao pode extrair'

	elif "Comprovativo de Entrega de" in modelo6IVA_comprovativo or "Comprovativo de Entrega de Declara&#231;&#227;o" in modelo6IVA_comprovativo or "Modelo 6 de IVA" in modelo6IVA:
		#Modelo 6 IVA
		print ('Modelo 6 IVA')
		if not modelo6IVA_numDeclaracao:
			modelo6IVA_numDeclaracao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("509.0, 735.604, 562.7, 742.54")').text()	#N. Declaracao
		if not modelo6IVA_DataSubmissao:
			modelo6IVA_DataSubmissao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("523.064, 714.17, 548.634, 719.95")').text()	#Data Submissao
		if not modelo6IVA_NomeEmpresa:
			modelo6IVA_NomeEmpresa = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("105.1, 573.698, 184.845, 579.478")').text()	#Nome da Empresa

		#1 - Imposto Industrial (II)
		if not modelo6IVA_RegimeIVA_II:
			modelo6IVA_RegimeIVA_II = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("470.033, 215.232, 473.368, 221.012")').text()	#Regime GERAL IMPOSTO INDUSTRIAL  Selecionado tera um V
		#3 - Imposto sobre rendimento do Trabalho (IRT) GRUPO B
		if not modelo6IVA_GrupoB:
			modelo6IVA_GrupoB = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("572.382, 215.232, 575.717, 221.012")').text()	#Regime GERAL GRUPO B  Selecionado tera um V

		#REGIME DO IVA
		if not modelo6IVA_RegimeIVA_GERA:
			modelo6IVA_RegimeIVA_GERA = "" #Still need to get another PDF with this selected.. # pdf.pq('LTTextBoxHorizontal:overlaps_bbox("246.508, 746.471, 249.843, 752.251")').text()	#Regime GERAL Selecionado tera um V
		if not modelo6IVA_RegimeIVA_SIMP:
			modelo6IVA_RegimeIVA_SIMP = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("246.508, 746.471, 249.843, 752.251")').text()	#Regime SIMPLIFICADO Selecionado tera um V

		if modelo6IVA_DataEmissao == "DDDDDDD":
			print ('DDDDDDD')
			print (pdf.pq('LTTextBoxHorizontal:overlaps_bbox("55.15, 161.701, 80.72, 167.481")').text())
			modelo6IVA_DataEmissao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("55.15, 161.701, 80.72, 167.481")').text()	#

		#Only on Page 2
		if not modelo6IVA_DataEmissao:
			modelo6IVA_DataEmissao = "DDDDDDD" #pdf.pq('LTTextBoxHorizontal:overlaps_bbox("55.15, 161.701, 80.72, 167.481")').text()	#
			print (modelo6IVA_DataEmissao)

		if not modelo6IVA_NIF:
			modelo6IVA_NIF = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("465.499, 661.821, 493.299, 667.601")').text()	#
			print (modelo6IVA_NIF)

	elif "MULTICAIXA Express" in mcexpress:
		print ('MULTICAIXA EXPRESS')
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
		print ('BAIDIRECTO')

		pagamentovia = "BAIDIRECTO"
		origemEMPRESA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 647.947, 357.205, 655.447")').text()
		print ('tem origemEMPRESA')

		origemCONTA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 630.447, 255.55, 637.947")').text()
		print ('tem origemCONTA')
		#05-10-2022
		origemIBAN = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("193.0, 613.447, 301.833, 620.947")').text().replace(' ','')
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
		print ('Pagamento da DC...')

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

	if modelo6IVA_numDeclaracao:
		#PAGAMENTO DC
		page = pd.DataFrame({
			'modelo6IVA_numDeclaracao': modelo6IVA_numDeclaracao,
			'modelo6IVA_DataEmissao': modelo6IVA_DataEmissao,
			'modelo6IVA_NomeEmpresa': modelo6IVA_NomeEmpresa,
			'modelo6IVA_comprovativo': modelo6IVA_comprovativo,
			'modelo6IVA_RegimeIVA_GERA': modelo6IVA_RegimeIVA_GERA,
			'modelo6IVA_RegimeIVA_SIMP': modelo6IVA_RegimeIVA_SIMP,
			'modelo6IVA_DataSubmissao': modelo6IVA_DataSubmissao,
			'modelo6IVA_GrupoB': modelo6IVA_GrupoB,
			'modelo6IVA_RegimeIVA_II': modelo6IVA_RegimeIVA_II,
			'modelo6IVA_NIF': modelo6IVA_NIF
		}, index=[0])

	elif pagamentovia != "PAGAMENTO DC":
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
	print ('printing..... DADOS')
	print (dadospdf)

	dadospdf1 = {}
	for ff,f1 in enumerate(dadospdf):
		print ('ff ' ,ff)
		print ('f1 ',f1)
		print (dadospdf[f1][0])
		dadospdf1[f1] = dadospdf[f1][0]

	#print ('tipo ', type(dadospdf))
	print ('printing..... DADOS 1')
	print (dadospdf1)

	return (dadospdf) #(page.to_json(orient = 'columns'))


	# Extract each relevant information individually
	ssn              = pdf.pq('LTTextLineHorizontal:overlaps_bbox("195, 735,  243, 745")').text()
	employer_name    = pdf.pq('LTTextLineHorizontal:overlaps_bbox("48,  686,  300, 696")').text()
	employer_address = pdf.pq('LTTextLineHorizontal:overlaps_bbox("48,  649,  300, 684")').text()
	first_name       = pdf.pq('LTTextLineHorizontal:overlaps_bbox("48,  590,  150, 601")').text()
	last_name        = pdf.pq('LTTextLineHorizontal:overlaps_bbox("175, 590,  280, 601")').text()
	employee_address = pdf.pq('LTTextLineHorizontal:overlaps_bbox("48,  543,  260, 577")').text()
	medicare_wage_tip= pdf.pq('LTTextLineHorizontal:overlaps_bbox("370, 662,  430, 672")').text()
	# Combined all relevant information into single observation
	page = pd.DataFrame({
						 'ssn': ssn,
						 'employer_name': employer_name,
						 'employer_address': employer_address,
						 'first_name': first_name,
						 'last_name': last_name,
						 'employee_address': employee_address,
						 'medicare_wage_tip': medicare_wage_tip
					   }, index=[0])
	return(page)

@frappe.whitelist(allow_guest=True)
def pdfscrape(ficheiropdf = None, empresa = None, tipodoctype = None):
	#Can be used to read any PDF and extract TEXT from it...
	#Read a PDF from Multicaixa EXPRESS payment and extract
	#Date of Payment, Company paid to, IBAN paid to, Amount paid, Transaction number and IBAN from



	print ('Can be used to read any PDF and extract TEXT from it...')
	print ('Read a PDF from Multicaixa EXPRESS payment and extract')
	print ('Date of Payment, Company paid to, IBAN paid to, Amount paid, Transaction number and IBAN from ')
	print ('Before install pdfquery install pip install cffi==1.12.3')
	print ('STILL NEED TO INSTALL PDFQUERY and PANDAS')
	print ('STILL NEED TO COPY/INSTALL pdfminer and pyquery')

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

	#For creating Purchase Order or Invoice based on PDF from Supplier...
	#Generates the TXT file and after run through
	if tipodoctype.upper() == "COMPRAS":
		print ('Generate the file TXT based on ficheiropdf file..')
		print ('Ficheiropdf ', ficheiropdf[ficheiropdf.find('/files/')+7:len(ficheiropdf)-3])
		filetmp = ficheiropdf[ficheiropdf.find('/files/')+7:len(ficheiropdf)-3] + 'txt'
		pdf.tree.write('/tmp/' + filetmp,pretty_print=True)

		print ('ficheiro ', filetmp)
		return '/tmp/' + filetmp
	else:
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


	#Check if PDF is AGT Modelo 6
	modelo6IVA_comprovativo = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("181.813, 728.221, 335.637, 737.741")').text()	#Comprovativo de Entrega de Declara&#231;&#227;o
	modelo6IVA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("227.829, 718.701, 289.621, 728.221")').text()	#Modelo 6 de IVA
	modelo6IVA_numDeclaracao = ""

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

	elif "Comprovativo de Entrega de" in modelo6IVA_comprovativo or "Comprovativo de Entrega de Declara&#231;&#227;o" in modelo6IVA_comprovativo or "Modelo 6 de IVA" in modelo6IVA:
		#Modelo 6 IVA

		modelo6IVA_numDeclaracao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("509.0, 735.604, 562.7, 742.54")').text()	#N. Declaracao
		modelo6IVA_DataSubmissao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("399.9, 716.78, 444.355, 722.56")').text()	#Data Submissao
		modelo6IVA_NomeEmpresa = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("105.1, 573.698, 184.845, 579.478")').text()	#Nome da Empresa

		#1 - Imposto Industrial (II)
		modelo6IVA_RegimeIVA_GERA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("470.033, 215.232, 473.368, 221.012")').text()	#Regime GERAL IMPOSTO INDUSTRIAL  Selecionado tera um V
		#3 - Imposto sobre rendimento do Trabalho (IRT) GRUPO B
		modelo6IVA_RegimeIVA_GERA = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("572.382, 215.232, 575.717, 221.012")').text()	#Regime GERAL GRUPO B  Selecionado tera um V

		#REGIME DO IVA
		modelo6IVA_RegimeIVA_GERA = "" #Still need to get another PDF with this selected.. # pdf.pq('LTTextBoxHorizontal:overlaps_bbox("246.508, 746.471, 249.843, 752.251")').text()	#Regime GERAL Selecionado tera um V

		modelo6IVA_RegimeIVA_SIMP = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("246.508, 746.471, 249.843, 752.251")').text()	#Regime SIMPLIFICADO Selecionado tera um V

		modelo6IVA_DataEmissao = pdf.pq('LTTextBoxHorizontal:overlaps_bbox("55.15, 161.701, 80.72, 167.481")').text()	#

	if modelo6IVA_numDeclaracao:
		#PAGAMENTO DC
		page = pd.DataFrame({
			'modelo6IVA_numDeclaracao': modelo6IVA_numDeclaracao,
			'modelo6IVA_DataEmissao': modelo6IVA_DataEmissao,
			'modelo6IVA_NomeEmpresa': modelo6IVA_NomeEmpresa,
			'modelo6IVA_comprovativo': modelo6IVA_comprovativo,
			'modelo6IVA_RegimeIVA_GERA': modelo6IVA_RegimeIVA_GERA,
			'modelo6IVA_RegimeIVA_SIMP': modelo6IVA_RegimeIVA_SIMP,
			'modelo6IVA_DataSubmissao': modelo6IVA_DataSubmissao
		}, index=[0])

	elif pagamentovia != "PAGAMENTO DC":
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
