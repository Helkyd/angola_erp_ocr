# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 02/10/2023


from __future__ import unicode_literals

import frappe
import angola_erp_ocr.util
from angola_erp_ocr.util import ocr_pdf
from angola_erp_ocr.util import pdf_scrape
import os

from angola_erp_ocr.angola_erp_ocr.doctype.ocr_read import ocr_read
import re

import xml.etree.ElementTree as ET

from pprint import pprint
from io import StringIO

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from lxml import html

import csv

import ast
import json

#PyCountry ISO TESTE
import pycountry

import bs4
from bs4 import BeautifulSoup as bs

#Timeout requests to try again
import requests
from requests.adapters import HTTPAdapter
import urllib3
from urllib3 import Retry
import time

@frappe.whitelist(allow_guest=True)
def lepdfocr(data,action = "SCRAPE",tipodoctype = None, lingua = None, resol = None):
	#FIX 19-09-2023; Added LANG and resolution for MCX DEBIT OCR
	#default is SCRAPE
	#tipodoctype if Compras means will create a Purchase Order or Invoice.
	start_time = time.monotonic()

	if tipodoctype != None and tipodoctype.upper() == "COMPRAS":
		print ('Gerar TXT from PDF file to Purchase Order or Invoice...')
		print ('Gerar TXT from PDF file to Purchase Order or Invoice...')

		if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = data

		#If no results... than change to OCR
		if ".pdf" in filefinal:
			#temScrape = pdf_scrape.pdfscrape(filefinal,None,'COMPRAS')
			#print ('RESULTADO COMPRAS')
			#print (temScrape)


			#print ('Now check the TXT generated and return the info required for creating the Invoice...')
			#print ('Now check the TXT generated and return the info required for creating the Invoice...')
			#ficheiro = temScrape
			#print ('ficheiro ', ficheiro)

			print ('Verify if file exists ....')
			#print (frappe.get_site_path() + ficheiro)

			if os.path.isfile(filefinal):
				#tree = ET.parse(ficheiro)
				print ('Running pdf_scrape_txt....')
				#To check if returned ITems... 14-10-2022
				scrapeTXT = pdf_scrape_txt(filefinal)
				print ('scrapeTXT')
				print (scrapeTXT)
				print (len(scrapeTXT))
				if scrapeTXT and len(scrapeTXT) >= 6:
					#Check if Items created...
					print (scrapeTXT[7])

					#FIX 21-12-2022; Check if has Invoice number..
					if scrapeTXT[1] == '':
						#TESTING....15-10-2022
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return aprender_OCR (filefinal,"COMPRAS")

					elif scrapeTXT[7]:
						print (scrapeTXT[7][0])
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return scrapeTXT
					else:
						#TESTING....15-10-2022
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return aprender_OCR (filefinal,"COMPRAS")

						print ('FAZ OCR COMPRAS')
						print ('FAZ OCR COMPRAS')
						print ('=================')
						facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS")

						'''
							TODO: Get MUST fields from OCR
						'''
						empresaSupplier = ''
						invoiceNumber = ''
						invoiceDate = ''
						moedaInvoice = ''
						supplierAddress = ''
						supplierEmail = ''
						supplierNIF = ''
						supplierCountry = ''
						supplierMoeda = ''

						#Items
						itemsSupplierInvoice = []
						itemCode = ''
						itemDescription = ''
						itemRate = ''
						itemQtd = ''
						itemTotal = ''
						itemIVA = ''

						cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)'
						#FIX 22-09-2023
						nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

						filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}


						print ("facturaSupplier")
						#print (facturaSupplier)
						#print (type(facturaSupplier))
						#print (json.loads(facturaSupplier))
						print (facturaSupplier.split('\n'))
						#frappe.throw(porra)

						palavrasexiste_header = False

						for fsup in facturaSupplier.split('\n'):
							print ('=====')
							print (fsup)

							if fsup.strip() != None and fsup.strip() != "":
								if not empresaSupplier:
									'''
									EVITA palavras:
										Original
										2!Via
										2ºVia
									'''
									evitapalavras =['Original','2!Via','2ºVia','Duplicado']
									palavraexiste = False
									for ff in fsup.split(' '):
										#print (ff)
										if ff in evitapalavras:
											#print ('TEM palavra ', ff)
											palavraexiste = True
									if palavraexiste == False:
										#print (fsup)
										#print ('Pode ser NOME DA EMPRESA')
										#Remove if startswith /
										if fsup.strip().startswith('/'):
											empresaSupplier = fsup.strip()[1:]
										else:
											empresaSupplier = fsup.strip()

								if not supplierAddress:
									'''
									TER palavras:
										RUA, AVENIDA
									'''
									terpalavras = ['RUA', 'AVENIDA']
									ADDRpalavraexiste = False
									for ff in fsup.split(' '):
										#print (ff)
										if ff in terpalavras:
											#print ('TEM palavra ', ff)
											ADDRpalavraexiste = True
									if ADDRpalavraexiste:
										supplierAddress = fsup.strip()

								if not supplierEmail:
									if "EMAIL:" in fsup.upper():
										#print ('Ainda por fazer....')
										supplierEmail = 'Ainda por fazer....'
								if not supplierNIF:
									if "NIF" in fsup.upper() or "NIF:" in fsup.upper():
										#FIX 22-09-2023
										tmp_supplierNIF = fsup.replace('NIF:','').replace('NIF','').strip()
										print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
										if re.match(nif_pattern,tmp_supplierNIF.strip()):
											supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
											nifvalido = validar_nif (supplierNIF)
											print (nifvalido)
											if nifvalido and nifvalido[2]:
												print ('Empresa CORRECTA5 ', nifvalido[2])
												empresaSupplier = nifvalido[2]
												supplierNIF = nifvalido[0]

								if not supplierMoeda:
									terpalavras = ['Moeda','AOA','AKZ']
									Moedapalavraexiste = False
									for ff in terpalavras:
										if ff in fsup.strip():
											Moedapalavraexiste = True
									if Moedapalavraexiste:
										#Check for AOA and AKZ first...
										if "AOA" in fsup.strip():
											supplierMoeda = 'KZ'
										elif "AKZ" in fsup.strip():
											supplierMoeda = 'KZ'
										else:
											supplierMoeda = fsup.strip().replace('Moeda','')
											#TODO: Remove CAMBIO and Numbers if exist on the same line...

								if not invoiceDate:
									terpalavras = ['Data Doc.','Data Doc']
									Datepalavraexiste = False
									for ff in terpalavras:
										if ff in fsup.strip():
											Datepalavraexiste = True
									if Datepalavraexiste:
										invoiceDate1 = fsup.strip()[fsup.strip().find('Data Doc'):] #fsup.replace('Data Doc.','').replace('Data Doc','').strip()
										invoiceDate = invoiceDate1.replace('Data Doc.','').replace('Data Doc','').strip()
										print (invoiceDate)
										print (fsup.replace('Data Doc.','').replace('Data Doc','').strip())

									#if "ESTE DOCUMENTO NÃO SERVE DE FACTURA" in fsup:
									#	frappe.throw(porra)

								if not invoiceNumber:
									#Search for PP FT FR
									seriesDocs_pattern = r"^([P][P]|[F][T]|[F][R])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}"
									#print (re.match(seriesDocs_pattern,fsup.upper().strip()))
									if re.match(seriesDocs_pattern,fsup.upper().strip()):
										invoiceNumber = fsup.upper().strip()
									else:
										if "FT" in fsup.upper().strip() or "PP" in fsup.upper().strip() or "FR" in fsup.upper().strip():
											if "FT" in fsup.upper().strip():
												tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FT'):]
											elif "PP" in fsup.upper().strip():
												tmpseries = fsup.upper().strip()[fsup.upper().strip().find('PP'):]
											elif "FR" in fsup.upper().strip():
												tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FR'):]

											#print ('tmpseries ',tmpseries)
											#print (re.match(seriesDocs_pattern,tmpseries))
											if re.match(seriesDocs_pattern,tmpseries):
												#Match series
												invoiceNumber = tmpseries
											#frappe.throw(porra)

								if not itemsSupplierInvoice:
									#Items
									itemsSupplierInvoice = []
									itemCode = ''
									itemDescription = ''
									itemRate = ''
									itemQtd = ''
									itemTotal = ''
									itemIVA = ''

									tmprate = ''

									'''
									TER palavras Para saber que ITEM TABLES DESCRIPTION:
										UN, UNIDADE, CAIXA, CX, Artigo, Descrição, Qtd., Pr.Unit, Cód. Artigo, V.Líquido
									'''
									contapalavras_header = 0
									#terpalavras_header = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qtd.', 'Pr.Unit', 'Cód. Artigo', 'V.Líquido', 'V. Líquido']
									terpalavras_header = ['VALOR UN', 'VALOR TOTAL LIQ', 'UNIDADE', 'UNI', 'UN', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'QUANT', 'Qtd.', 'PREÇO', 'Pr.Unit', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', 'DESC', 'DEC', 'TAXA', 'IVA']



									#palavrasexiste_header = False
									for pp in terpalavras_header:
										if pp.upper() in fsup.strip().upper():
											contapalavras_header += 1

									'''
									TER palavras Para saber que ITEM TABLES:
										UN, UNIDADE, CAIXA, CX
									'''

									terpalavras_item = ['UN', 'UNIDADE', 'CAIXA', 'CX']
									palavraexiste_item = False
									if palavrasexiste_header:
										#Tem HEADER entao ve os ITENS...
										for pp in terpalavras_item:
											if pp in fsup.strip():
												#IS an ITEMS so add
												palavraexiste_item = True
										if palavraexiste_item:
											for ii in fsup.split(' '):
												print ('----')
												print ('ii ', ii)
												print (re.match(cash_pattern,ii))
												print (ii.strip().isnumeric())
												#Itemcode
												if not itemCode:
													itemCode = ii.strip()
												elif not itemDescription:
													itemDescription = ii.strip()
												elif itemCode and itemDescription and not ii.strip().isnumeric():
													#Deal with Numbers
													if not ii.find(',') != -1: #re.match(cash_pattern,ii): # and ii.find(',') != -1:
														#Deal with Unit
														if not ii.strip() in terpalavras_item:
															itemDescription = itemDescription + " " + ii.strip()
												if ii.strip().isnumeric():
													print ('number')
													if not itemQtd:
														itemQtd = ii.strip()
													elif not itemRate:
														print ('tamanho')
														print (len(ii))

														if len(ii) == 2:
															tmprate = ii.strip()
														else:
															if tmprate != '':
																itemRate = str(tmprate) + str(ii.strip())
																print ('aqui0 ',itemRate)
															else:
																itemRate = ii.strip()
																tmprate = ''
																print ('OUaqui1 ',itemRate)
													elif not itemTotal:
														print ('aqui total')
														itemTotal = ii.strip()
													elif not itemIVA:
														itemIVA = ii.strip()
												elif re.match(cash_pattern,ii) and ii.find(',') != -1:
													#Tem Decimais...
													if not itemQtd:
														itemQtd = ii.strip()
													elif not itemRate:
														if tmprate != '':
															itemRate = str(tmprate) + str(ii.strip())
															tmprate = ''
															print ('aqui ',itemRate)
														else:
															itemRate = ii.strip()
															tmprate = ''
															print ('OUaqui ',itemRate)

														#itemRate = ii.strip()
													elif not itemTotal:
														print ('OUaqui total')
														if ii.strip() != '0,00':
															itemTotal = ii.strip()
													elif not itemIVA:
														itemIVA = ii.strip()

											print ('Items')
											print ('itemCode ',itemCode)
											print ('itemDescription ',itemDescription)
											print ('itemQtd ',itemQtd)
											print ('itemRate ',itemRate)
											print ('itemTotal ',itemTotal)
											print ('itemIVA ',itemIVA)

											filtered_divs['ITEM'].append(itemCode)
											filtered_divs['DESCRIPTION'].append(itemDescription)
											filtered_divs['QUANTITY'].append(itemQtd)
											filtered_divs['RATE'].append(itemRate)
											filtered_divs['TOTAL'].append(itemTotal)
											filtered_divs['IVA'].append(itemIVA)

										#frappe.throw(porra)



									if contapalavras_header >= 5:
										palavrasexiste_header = True

								#if itemsSupplierInvoice:
								#Already has list of list... to Append

								if "aaaaaPROFORMA" in fsup:
									print ('empresaSupplier ',empresaSupplier)
									print ('supplierAddress ',supplierAddress)
									print ('email ', supplierEmail)
									print ('supplierNIF ', supplierNIF)
									print ('invoiceNumber ', invoiceNumber)

									frappe.throw(porra)
								#print ('///////////')
								#print (filtered_divs)
								#print ('///////////')
						print ('empresaSupplier ',empresaSupplier)
						print ('supplierAddress ',supplierAddress)
						print ('email ', supplierEmail)
						print ('supplierNIF ', supplierNIF)
						print ('invoiceNumber ', invoiceNumber)

						print ('!!!!!!!!!!')
						print (filtered_divs)
						print ('!!!!!!!!!!')
						data = []
						for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['IVA']):
							if 'ITEM' in row[0]:
								continue

							data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5]}
							data.append(data_row)

						print('Supplier ', empresaSupplier)
						print ('supplieraddre ', supplierAddress)
						print ('supplierNIF ', supplierNIF)
						if supplierMoeda == 'AOA' or supplierMoeda == 'AKZ' or supplierMoeda == 'KZ':
							empresaPais = 'Angola'
						else:
							empresaPais = 'DESCONHECIDO'
							#TODO: GET COUNTRY FROM INVOICE...
							print ('TODO: GET COUNTRY FROM INVOICE...')

						print ('supplierPais ', empresaPais)

						print('Invoice', invoiceNumber)
						print('Date ', invoiceDate)
						print('Moeda ', supplierMoeda)


						pprint(data)

						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return (empresaSupplier,invoiceNumber,invoiceDate,supplierMoeda,supplierAddress,supplierNIF,empresaPais,data)


				else:
					stop_time = time.monotonic()
					print(round(stop_time-start_time, 2), "seconds")

					return scrapeTXT
				#return pdf_scrape_txt(filefinal)

			else:
				print ('Ficheiro nao existe.. ' + filefinal)
				return ('Ficheiro nao existe.. ' + filefinal)

			'''
			NOT NEEDED ANY MORE.....
			'''



	elif action != None and action.upper() == "SCRAPE":
		print ('SCRAPE PDF')
		#print (dict(data))
		#return data.replace('/files','')

		if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)
		elif os.path.isfile(frappe.get_site_path('public','files') + data.replace('/public/files','')):
			filefinal = frappe.get_site_path('public','files') + data.replace('/public/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = data

		#If no results... than change to OCR
		if ".pdf" in filefinal:
			temScrape = pdf_scrape.pdfscrape_perpage(filefinal)
			print ('RESULTADO temScrape')
			print (temScrape)
			if temScrape == None:
				#FIX 14-02-2023
				return "INVALIDO"

			print ('datahora' in temScrape)

			if 'datahora' in temScrape or 'dataEMISSAO' in temScrape or 'datadePAGAMENTO' in temScrape:
				#print (temScrape['datahora'])
				#print (temScrape['referenciadestino'])
				#print (temScrape['iban'])
				podeterminar = False
				if 'datahora' in temScrape:
					if temScrape['datahora'] and (temScrape['referenciadestino'] or temScrape['iban']):
						if temScrape['datahora'][0] != "" and (temScrape['referenciadestino'][0] != "" or temScrape['iban'][0] != ""):
							print ('PODE TERMINAR....')
							podeterminar = True
							return temScrape
						else:
							print ('CORRER ocr_pytesseract....')
							return ocr_pytesseract (filefinal)

				elif 'dataEMISSAO' in temScrape or 'datadePAGAMENTO' in temScrape:
					if temScrape['dataEMISSAO'] and temScrape['nifEmpresa']:
						if temScrape['dataEMISSAO'][0] != "" and temScrape['nifEmpresa'][0] != "":
							print ('PODE TERMINAR....')
							return temScrape
						else:
							return ocr_pytesseract (filefinal)
							'''
							#Podemos fazer OCR with tesseract before trying with pytesseract
							# File, Language, DPI

							ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'eng',False,200) #'por',False,200) #180) #200)
							print ('OCR TESSERACT')
							print ('OCR TESSERACT')
							print ('OCR TESSERACT')
							print (ocr_tesserac)
							print (type(ocr_tesserac))
							print (ocr_tesserac.split('\n'))
							print ('=====================')
							print (ocr_tesserac.split(':'))
							#Check RECIBO DE PAGAMENTO e EMITIDO EM: RF PORTAL DO CONTRIBUINTE tp be RETENCAO na FONTE
							print ('*********************')
							print ("RECIBO DE PAGAMENTO" in ocr_tesserac)
							print ("EMITIDO EM: RF PORTAL DO CONTRIBUINTE" in ocr_tesserac)

							referenciadocumento = ""

							if ("RECIBO DE PAGAMENTO" in ocr_tesserac and "EMITIDO EM: RF PORTAL DO CONTRIBUINTE" in ocr_tesserac) or "MCX DEBIT" in ocr_tesserac:
								#MCX DEBIT -> Multicaixa Express

								print ('RECIBO RETENCAO NA FONTE...')
								Temdadoscontribuinte = False
								TemdadoscontribuinteNIF = False

								mcexpress = False

								dadoscontribuinte = ""
								dadoscontribuinteNIF = ""
								descricaoRECEITA = ""
								referenciaANO = ""
								referenciaPERIODO = ""
								datadePAGAMENTO = ""
								dataEMISSAO = ""



								#print ('CASH ',re.match(cash_pattern,b[0]))

								for dd in ocr_tesserac.split('\n'):
									print ('dd ', dd)
									print ('ddsplit ', dd.split(' '))
									print ('ddsplit ', len(dd.split(' ')))
									dd0 = dd.split(' ')
									print ('dd0 ', len(dd0))
									print ('DATAS ', re.match(date_pattern,dd0[0].strip()))
									print ('DATAS ', re.match(date_pattern,dd.strip()))

									if "LIQUIDAÇÃO GENÉRICA DE TRIBUTO" in dd:
										print ('Numero Referencia..')
										print (dd[0:dd.find(' ')])
										print (dd[0:dd.find(' ')].strip().isnumeric())
										referenciadocumento = dd[0:dd.find(' ')].strip()
										print (referenciadocumento)
									elif "DADOS DO CONTRIBUINTE:" in dd:
										Temdadoscontribuinte = True
									elif Temdadoscontribuinte and not dadoscontribuinte:
										dadoscontribuinte = dd.strip()
									elif "LUANDA - ANGOLA" in dd:
										#Might be different on other... with time will be added more or changed...
										TemdadoscontribuinteNIF = True
									elif TemdadoscontribuinteNIF and not dadoscontribuinteNIF:
										dadoscontribuinteNIF = dd.strip()
									elif "MENSAL" in dd:
										#Ano, Periodo
										if dd[0:dd.find(' ')].strip().isnumeric():
											referenciaANO = dd[0:dd.find(' ')].strip()
											referenciaPERIODO = dd[dd.find(' '):dd.find(' LUANDA')-2].strip()
											print ('referenciaANO ', referenciaANO)
											print ('referenciaPERIODO ', referenciaPERIODO)
											#frappe.throw(porra)
									elif len(dd0) == 10:
										print (dd.split(' ')[8])
										print (dd.split(' ')[7])
										print (dd.split(' ')[9])
										if dd.split(' ')[8].strip() == '65%':
											#Retencao 6.5
											descricaoRECEITA = "IMPOSTO INDUSTRIAL - RETENÇÃO NA FONTE"
											#Check valortributavel
											tmpvalorPagar = dd.split(' ')[9]
											print ('tmpvalorPagar ', tmpvalorPagar)
											tmpTAXA = dd.split(' ')[8]
											print ('tmpTaxa ', tmpTAXA)
											Tmpvalortributavel = dd.split(' ')[7]
											print ('Tmpvalortributavel ', Tmpvalortributavel)

									elif "INDUSTRIAL" in dd or "A28" in dd:
										if not Tmpvalortributavel:
											descricaoRECEITA = "IMPOSTO INDUSTRIAL - RETENÇÃO NA FONTE"
											#Check valortributavel
											print (dd)
											tmpvalorPagar = dd[dd.rfind(' '):].strip()
											print ('tmpvalorPagar ', tmpvalorPagar)
											dd1 = dd[0:dd.rfind(' ')].strip()
											tmpTAXA = dd[find_second_last(dd,' '):dd.rfind(' ')]
											print ('tmpTaxa ', tmpTAXA)
											dd2 = dd1[find_second_last(dd1,' '):dd1.rfind(' ')]
											print ('dd2 ', dd2)
											Tmpvalortributavel = dd2[0:len(dd2)-dd2.rfind(' ')].strip()
											print ('Tmpvalortributavel ', Tmpvalortributavel)

									elif "VALOR TOTAL PAGO" in dd:
										print (dd.split(' ')[3])
										if len(dd.split(' ')) == 5:
											valorPAGO = dd.split(' ')[3]
											print ('valorPAGO ', valorPAGO)
									elif "N.CAIXA:" in dd:
										print ('N. Caixa e Num Transacao')
										mcexpress = True
										numeroTransacao = dd[dd.rfind(' '):].strip()
										if not numeroTransacao.strip().isnumeric():
											numeroTransacao = ""
										print ('numeroTransacao ',numeroTransacao)
										#frappe.throw(porra)
									elif "CONTA:" in dd:
										print ('mcexpress', mcexpress)
										print ('Conta e Data')
										contaOrigem = dd[dd.find(' '):find_second_last(dd, ' ')].strip()
										print ('contaOrigem ',contaOrigem)
										datadePAGAMENTO = dd[find_second_last(dd, ' '):len(dd)].strip()
										print ('datadePAGAMENTO ',datadePAGAMENTO)


										#frappe.throw(porra)

									elif dd[0:dd.find(' ')].strip().isnumeric():
										#Can be NIF for Benificiario...
										#5417537802 TEOR LOGICO-PRESTACAO DE SERVICOS LDA.
										if len(dd[0:dd.find(' ')].strip()) == 10:
											#NIF
											BeneficiarioNIF = dd[0:dd.find(' ')].strip()
										print ('NUMEROSSSSSSS')

									elif re.match(iban_pattern,dd.strip()):
										print ('IBAN DEST. ',re.match(iban_pattern,dd.strip()))
										if mcexpress:
											#IBAN Destinatario
											ibanDestino = dd.strip()
											print ('ibanDestino ',ibanDestino)
										#frappe.throw(porra)
									elif re.match(cash_pattern,dd.strip()):
										print ('VALOR PAGO. ',re.match(cash_pattern,dd.strip()))
										if mcexpress:
											#IBAN Destinatario
											valorPAGO = dd.strip()
											print ('valorPAGO ',valorPAGO)
										#frappe.throw(porra)

									elif re.match(date_pattern,dd.strip()):
										print ('DATAAAAAAASSSS')
										#DATA....Pagamento ou EMISSAO
										if not datadePAGAMENTO and not dataEMISSAO:
											datadePAGAMENTO = dd.strip()
											dataEMISSAO = dd.strip()
											print ('dataEMISSAO ', dataEMISSAO)
											print ('datadePAGAMENTO ', datadePAGAMENTO)




								if referenciadocumento and valorPAGO and BeneficiarioNIF:
									return {
										'referenciadocumento':referenciadocumento,
										'dadoscontribuinte':dadoscontribuinte,
										'dadoscontribuinteNIF':dadoscontribuinteNIF,
										'referenciaANO':referenciaANO,
										'referenciaPERIODO': referenciaPERIODO,
										'BeneficiarioNIF': BeneficiarioNIF,
										'descricaoRECEITA': descricaoRECEITA,
										'tmpvalorPagar': tmpvalorPagar,
										'tmpTAXA': tmpTAXA,
										'Tmpvalortributavel': Tmpvalortributavel,
										'valorPAGO': valorPAGO,
										'datadePAGAMENTO': datadePAGAMENTO,
										'dataEMISSAO': dataEMISSAO
									}
								elif mcexpress and valorPAGO and ibanDestino:
									#Multicaixa EXPRESS
									return {
										"mcexpress": mcexpress,
										"numeroTransacao": numeroTransacao,
										"datadePAGAMENTO": datadePAGAMENTO,
										"contaOrigem": contaOrigem,
										"ibanDestino": ibanDestino,
										"valorPAGO": valorPAGO
									}


								#Resumo dos DADOS
								print ('====================')
								print ('referenciadocumento ',referenciadocumento)
								print ('dadoscontribuinte ',dadoscontribuinte)
								print ('dadoscontribuinteNIF ',dadoscontribuinteNIF)
								print ('referenciaANO ',referenciaANO)
								print ('referenciaPERIODO ', referenciaPERIODO)
								print ('BeneficiarioNIF ', BeneficiarioNIF)
								print ('descricaoRECEITA ',descricaoRECEITA)
								print ('tmpvalorPagar ', tmpvalorPagar)
								print ('tmpTAXA ', tmpTAXA)
								print ('Tmpvalortributavel ', Tmpvalortributavel)
								print ('valorPAGO ',valorPAGO)
								print ('datadePAGAMENTO ',datadePAGAMENTO)
								print ('dataEMISSAO ', dataEMISSAO)

							elif "Modelo 6 de IVA" in ocr_tesserac:
								print ('AINDA POR FAZER.... Modelo 6 de IVA')
								print ('AINDA POR FAZER.... Modelo 6 de IVA')
								print ('AINDA POR FAZER.... Modelo 6 de IVA')

								#procura pelo REG if not run again with 180 DPI or 300
								#REG19007009587X

								datasubmissaoTEMP = ""
								NIFContribuinte = ""
								temREG = False

								for aa in ocr_tesserac.split('\n'):
									if aa.find('REG') != -1 and len(aa) == 15:
										#Pode ser o Numero de Declaracao... if has 11 numbers
										print ('REGNumbers ', aa[3:len(aa)-1])
										temREG = True

								if not temREG: #not "REG" in ocr_tesserac:
									ocr_tesserac1 = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'por',False,180)
									print (ocr_tesserac1.split('\n'))
									for aa in ocr_tesserac1.split('\n'):
										if aa.find('REG') != -1 and len(aa) == 15:
											#Pode ser o Numero de Declaracao... if has 11 numbers
											print ('REGNumbers ', aa[3:len(aa)-1])
											referenciadocumento = aa.strip()
											temREG = True
										elif re.match(date_pattern,aa.strip()):
											if not datasubmissaoTEMP:
												datasubmissaoTEMP = aa.strip()
												print ('datasubmissaoTEMP ', datasubmissaoTEMP)
										elif len(aa.strip()) == 10:
											#Might be NIF
											if aa.strip().isnumeric() and not NIFContribuinte:
												NIFContribuinte = aa.strip()
												print ('NIFContribuinte ', NIFContribuinte)
									if referenciadocumento and datasubmissaoTEMP and NIFContribuinte:
										#Still missing to find what REGIME is it on....
										return {
											'referenciadocumento': referenciadocumento,
											'datasubmissaoTEMP': datasubmissaoTEMP,
											'NIFContribuinte': NIFContribuinte
										}



							if not ocr_tesserac or not ocr_tesserac1 or not referenciadocumento:
								print ('TERA DE FAZER O OCR......')
								print ('TERA DE FAZER O OCR......')
								print ('TERA DE FAZER O OCR......')
								return ocr_pdf.ocr_pdf(input_path=data)
							'''
				else:
					print ('FAZ ocr_pytesseract')
					print ('FAZ ocr_pytesseract')
					print ('FAZ ocr_pytesseract')
					return ocr_pytesseract (filefinal)

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
		else:
			print ('IMAGE FILE111')
			print ('IMAGE FILE111')
			print ('DO OCR_READ and OCR_PDF')
			return ocr_pytesseract (filefinal)



	elif action == "OCR":
		print ('OCR IMAGE/PDF...')
		if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = data

		print ('IMAGE FILE')
		print ('IMAGE FILE')
		print ('DO OCR_READ and OCR_PDF')
		#FIX 19-09-2023; Added Lingua and Resol for MCX DEBIT...
		print ('lingua ', lingua)
		print ('resol ', resol)
		return ocr_pytesseract (filefinal,None,lingua,resol)

		#Might use after if no results from above..
		#return ocr_pdf.ocr_pdf(input_path=data)

def find_second_last(text, pattern):
	return text.rfind(pattern, 0, text.rfind(pattern))

def ocr_pytesseract (filefinal,tipodoctype = None,lingua = 'por',resolucao = 200):
	#Podemos fazer OCR with tesseract before trying with pytesseract
	# File, Language, DPI
	#cash to include . and , ex. 44.123,00 / 44.123,97

	#FIX 25-09-2023
	if lingua == None and resolucao == None:
		lingua = 'por'
		resolucao = 200

	start_time = time.monotonic()

	#cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'
	cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)|(?:\d*\,\d+)'

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

	ocr_tesserac = ""
	ocr_tesserac1 = ""

	#Added to OCR COMPRAS...; 14-10-2022
	if tipodoctype != None and tipodoctype.upper() == "COMPRAS":
		print ('Tenta ocr_pytesseract.... but reading all Lines and checking for the required fields...')
		return angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,lingua,False,resolucao) #250) #ocr_tesserac
		#frappe.throw(porra)

	print ('lingua00 ', lingua)
	print ('resolucao ', resolucao)
	print ('filefinal', filefinal)
	#FIX 26-09-2023; added INT to resolucao
	ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,lingua,False,int(resolucao)) #200) #180) #200)
	print ('OCR TESSERACT')
	print ('OCR TESSERACT')
	print ('OCR TESSERACT')
	print (ocr_tesserac)
	print (type(ocr_tesserac))
	print (ocr_tesserac.split('\n'))
	print ('=====================')
	#print (ocr_tesserac.split(':'))
	#Check RECIBO DE PAGAMENTO e EMITIDO EM: RF PORTAL DO CONTRIBUINTE tp be RETENCAO na FONTE
	print ('*********************')
	print ("RECIBO DE PAGAMENTO" in ocr_tesserac)
	print ("EMITIDO EM: RF PORTAL DO CONTRIBUINTE" in ocr_tesserac)

	print ('TESTA BAI')
	print ("através do serviço BAlDirecto." in ocr_tesserac)
	print ("através do serviço BAIDirecto." in ocr_tesserac)

	referenciadocumento = ""

	#FIX 16-09-2023; Added to check if RUPE (IVA, INSS, IRT) and ZAP FIBRA payments
	if ("MCX DEBIT" in ocr_tesserac or "MCX DÉBIT" in ocr_tesserac) and ("ZAP FIBRA" in ocr_tesserac or "ZP EIBRA " in ocr_tesserac or "ZAP  FIBRA" in ocr_tesserac):
		print ('Pagamento ZAP FIBRA.....')
		print ('Pagamento ZAP FIBRA.....')

		pag_zapfibra = False
		nif_zapfibra = ""
		cliente_zapfibra = ""

		mcxdebit = True

		tmp_numcaixa = ""
		numeroTransacao = ""
		dataTransacao = ""
		descricaoPagamento = ""

		for dd in ocr_tesserac.split('\n'):
			print ('size dd ',len(dd))
			print (dd == "")
			print (dd == " ")
			if dd !='' and dd != ' ':
				print ('-----')
				print ('dd ', dd)
				print ('ddsplit ', dd.split(' '))
				print ('ddsplit ', len(dd.split(' ')))
				dd0 = dd.split(' ')
				print ('dd0 ', len(dd0))
				print ('DATAS ', re.match(date_pattern,dd0[0].strip()))
				print ('DATAS ', re.match(date_pattern,dd.strip()))


				#FIX 02-10-2023 added W.CAIXA:
				if "N.CAIXA:" in dd or "N-UAIXA:" in dd or "N.CATNA:" in dd or "W.CAIXA:" in dd:
					#FIX 19-09-2023; get N. CAIXA
					if not tmp_numcaixa:
						tmp_numcaixa = dd[8:21].strip()
					#Get Transaction Number...
					tmp_trans = dd.strip()
					if not numeroTransacao:
						numeroTransacao = tmp_trans[tmp_trans.rfind(":")+1:].strip()
				elif "CONTA:" in dd:
					#Get Date and time
					tmp_data = dd.split(' ')[2]
					if not dataTransacao:
						dataTransacao = tmp_data
				elif "NIF:" in dd or "NIEF:" in dd:
					#NIF da ZAP FIBRA
					if "5417231126" in dd.split(' ')[1] or "5417231125" in dd.split(' ')[1] or "5417231120" in dd.split(' ')[1]:
						#Due to system ORC the last digit wrong ...5417231125
						nif_zapfibra = "5417231126"
				elif "N DE CLIENTE:" in dd or "N° DE CLIENTE:" in dd or "W° DE CLIENTE:" in dd:
					cliente_zapfibra = dd[dd.find(":")+1:].replace('‘','').strip()

				elif "ZAP FIBRA" in dd or "ZP EIBRA" in dd or "ZAP  FIBRA" in dd:
					if "ZP EIBRA" in dd:
						descricaoPagamento = "ZAP FIBRA " + dd[dd.find('ZP EIBRA')+8:].strip()
					elif "ZAP  FIBRA" in dd:
						descricaoPagamento = "ZAP FIBRA " + dd[dd.find('ZAP  FIBRA')+10:].strip()
					else:
						descricaoPagamento = dd.strip()
				elif "MONTANTE:" in dd or "MONTANTE :" in dd:
					#Pagamento feito
					if "MONTANTE :" in dd:
						dd0 = dd[10:].split(' ')

					if len(dd0) >= 3:
						print ('CASH')
						print (re.match(cash_pattern,dd0[1].strip()))
						if re.match(cash_pattern,dd0[1].strip()):
							#Check if COMMA bcs ANG uses COMMA as DECIMALS
							if not ',' in dd0[1].strip():
								#remove the DOT
								valorPAGO = dd0[1].replace('.','').strip()
							else:
								valorPAGO = dd0[1].strip()
					elif len(dd0) == 2:
						print ('CASH - remove Akz')
						print (re.match(cash_pattern,dd0[1].replace('Akz','').strip()))
						if re.match(cash_pattern,dd0[1].replace('Akz','').strip()):
							valorPAGO = dd0[1].replace('Akz','').strip()


		print ('================ ENDDDDDD')
		print ('DDDDDDd')
		print ('numeroTransacao ',numeroTransacao)
		print ('dataTransacao ', dataTransacao)
		print ('nif zapfibra ', nif_zapfibra)
		print ('cliente_zapfibra ', cliente_zapfibra)
		print ('descricaoPagamento ', descricaoPagamento)
		print ('valorPAGO ', valorPAGO)



		if descricaoPagamento and valorPAGO and nif_zapfibra:
			return {
				"mcxdebit": True,
				"numCaixa": tmp_numcaixa,
				"numeroTransacao": numeroTransacao,
				"datadePAGAMENTO": dataTransacao,
				"nifZAPFIBRA": nif_zapfibra,
				"cliente_ZAPFIBRA": cliente_zapfibra,
				"descricaoPagamento": descricaoPagamento,
				"valorPAGO": valorPAGO
			}
		#frappe.throw(porra)


	elif ("MCX DEBIT" in ocr_tesserac or "MCX DÉBIT" in ocr_tesserac) and "RUPE" in ocr_tesserac and ("PAG. AO ESTADO" in ocr_tesserac or "PAG. RO ESTADO" in ocr_tesserac or "PAG. RO ESTANO" in ocr_tesserac or "PAG.' RO ES'TANO" in ocr_tesserac or "PAG, AO ESTADO" in ocr_tesserac):
		print ('Pagamento RUPE... IVA INSS OR IRT')
		print ('Pagamento RUPE... IVA INSS OR IRT')
		#Check if IVA... MUST HAVE 600 022 301 0
		pag_iva = False
		rupe_iva = ""

		pag_inss = False
		rupe_inss = ""

		pag_irt = False
		rupe_irt = ""

		mcxdebit = True

		if "600 022 301 0" in ocr_tesserac or "6060 G22 301" in ocr_tesserac or "600 C22 351" in ocr_tesserac:
			print ('DEVE TER Pagamento IVA....')
			pag_iva = True
		elif "600 012 308 0" in ocr_tesserac or "600 012 398 0" in ocr_tesserac:
			#FIX 19-09-2023; OCR might get 398 instead of 308
			print ('DEVE TER Pagamento IRT....')
			pag_irt = True
		elif "603 002 309 0" in ocr_tesserac or "603 002 304 0" in ocr_tesserac:
			print ('DEVE TER Pagamento INSS....')
			pag_inss = True

		tmp_numcaixa = ""
		numeroTransacao = ""
		dataTransacao = ""
		descricaoPagamento = ""

		for dd in ocr_tesserac.split('\n'):
			print ('size dd ',len(dd))
			print (dd == "")
			print (dd == " ")
			if dd !='' and dd != ' ':
				print ('-----')
				print ('dd ', dd)
				print ('ddsplit ', dd.split(' '))
				print ('ddsplit ', len(dd.split(' ')))
				dd0 = dd.split(' ')
				print ('dd0 ', len(dd0))
				print ('DATAS ', re.match(date_pattern,dd0[0].strip()))
				print ('DATAS ', re.match(date_pattern,dd.strip()))


				#FIX 02-10-2023;
				if "N.CAIXA:" in dd or "N.CATNA:" in dd or "N,CAIXA:" in dd or "W.CAIXA:" in dd:
					#FIX 19-09-2023; get N. CAIXA
					if not tmp_numcaixa:
						tmp_numcaixa = dd[8:21].strip()

					#Get Transaction Number...
					tmp_trans = dd.strip()
					if not numeroTransacao:
						numeroTransacao = tmp_trans[tmp_trans.rfind(":")+1:].strip()
				elif "CONTA:" in dd:
					#Get Date and time
					tmp_data = dd.split(' ')[2]
					if not dataTransacao:
						dataTransacao = tmp_data
				elif "PAG. RO ESTADO" in dd or "PAG. AO ESTADO" in dd or "PAG. RO ESTANO" in dd or "PAG.' RO ES'TANO" in dd or "PAG, AO ESTADO" in dd:
					#descricao Pagamento
					descricaoPagamento = "PAG. AO ESTADO"
				elif "RUPE" in dd:
					descricaoPagamento += ": RUPE"
				elif len(dd) >= 22 and len(dd0) >= 7:
					#RUPE NUMBER
					print (dd.replace(" ","").isnumeric())
					print ('pag_iva ',pag_iva)
					print ('pag_irt ',pag_irt)
					print ('pag_inss ', pag_inss)
					#FIX 26-029-2023
					if "6060 G22 301" in dd.strip() or "600 C22 351" in ocr_tesserac:
						tmp_dd = dd.replace('6060 G22 301','600 022 301').replace('600 C22 351','600 022 301').strip()
						dd = tmp_dd

					if dd.replace(" ","").isnumeric():
						if pag_iva:
							rupe_iva = dd.strip()
							tiporupe = "IVA"
						elif pag_irt:
							if "600 012 398 0" in dd.strip():
								#FIX as OCR changed from 308 to 398
								rupe_irt = dd.replace('398','308').strip()
							else:
								rupe_irt = dd.strip()
							tiporupe = "IRT"
						elif pag_inss:
							rupe_inss = dd.strip()
							tiporupe = "INSS"
				elif "MONTANTE:" in dd:
					#Pagamento feito
					if len(dd0) >= 3:
						print ('CASH')
						print (re.match(cash_pattern,dd0[1].strip()))
						if re.match(cash_pattern,dd0[1].strip()):
							valor_rupe = dd0[1].strip()


		print ('================ ENDDDDDD')
		print ('DDDDDDd')
		print ('numeroTransacao ',numeroTransacao)
		print ('dataTransacao ', dataTransacao)
		print ('descricaoPagamento ', descricaoPagamento)
		print ('rupe iva/irt/inss')
		print (rupe_iva)
		print (rupe_irt)
		print (rupe_inss)
		print ('valor_rupe ', valor_rupe)



		if descricaoPagamento and valor_rupe and (rupe_iva or rupe_irt or rupe_inss):
			return {
				"mcxdebit": True,
				"numCaixa": tmp_numcaixa,
				"numeroTransacao": numeroTransacao,
				"datadePAGAMENTO": dataTransacao,
				"descricaoPagamento": descricaoPagamento,
				"rupe": rupe_iva or rupe_inss or rupe_irt,
				"tipo_RUPE": tiporupe,
				"valorRUPE": valor_rupe
			}
		#frappe.throw(porra)

	elif "RECIBO DE PAGAMENTO" in ocr_tesserac or "EMITIDO EM: RF PORTAL DO CONTRIBUINTE" in ocr_tesserac or "EMITIDO EM: RF PORTAL BO CONTRIBUINTE" in ocr_tesserac \
		or ("MCX DEBIT" in ocr_tesserac or "MCX DÉBIT" in ocr_tesserac) or "COMPROVATIVO DA OPERACAO" in ocr_tesserac or "COMPROVATIVO DA OPERAÇÃO" in ocr_tesserac or "Comprovativo Digital" in ocr_tesserac \
		or "MULTICAIXA Express." in ocr_tesserac: # or "através do serviço BAlDirecto." in ocr_tesserac or "através do serviço BAIDirecto." in ocr_tesserac:
		#MCX DEBIT -> Multicaixa Express
		#COMPROVATIVO DA OPERACAO BFA

		print ('RECIBO RETENCAO NA FONTE...')
		Temdadoscontribuinte = False
		TemdadoscontribuinteNIF = False

		mcexpress = False
		bfatransferencia = False

		temreferenciaDar = False

		nextlinha = False

		dadoscontribuinte = ""
		dadoscontribuinteNIF = ""
		descricaoRECEITA = ""
		referenciaANO = ""
		referenciaPERIODO = ""
		datadePAGAMENTO = ""
		dataEMISSAO = ""

		BeneficiarioNIF = ""
		tmpvalorPagar = ""
		tmpTAXA = ""
		Tmpvalortributavel = ""
		valorPAGO = ""
		ibanDestino = ""
		contaOrigem = ""
		contaCreditada = ""
		numeroOperacao = ""
		referenciaDAR = ""

		ibanOrigem = ""

		multiexpress = False

		numeroTransacao = ""

		descricaoPagamento = ""

		mcxdebit = False

		empresaOrigem0 = ""

		if ("MCX DEBIT" in ocr_tesserac or "MCX DÉBIT" in ocr_tesserac) or "Comprovativo Digital" in ocr_tesserac:
			#Check if TRANSACÇÃO
			#FIX 04-01-2023
			if "TRANSACÇÃO:" in ocr_tesserac or "TRANSACGAO:" in ocr_tesserac or "TRANSACÇÃD:" in ocr_tesserac:
				print ('Transacao MCX DEBIT')
				print ('Transacao MCX DEBIT')
				if ("MCX DEBIT" in ocr_tesserac or "MCX DÉBIT" in ocr_tesserac):
					mcxdebit = True


			else:
				#Redo the OCR with eng, 200
				print ('Redo the OCR with eng, 200')
				ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'eng',False,200)

			print ('=====================')
			print (ocr_tesserac)
			print (type(ocr_tesserac))
			print (ocr_tesserac.split('\n'))
			print ('=====================')
			#frappe.throw(porra)

		#FIX 21-09-2023; Better in PT for this case
		#if "AUTOLIQUPAGRO RETENÇAO A FONTE" in ocr_tesserac.strip():
		#	ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'eng',False,200)

		#print ('CASH ',re.match(cash_pattern,b[0]))

		for dd in ocr_tesserac.split('\n'):
			print ('size dd ',len(dd))
			print (dd == "")
			print (dd == " ")
			if dd !='' and dd != ' ':
				print ('-----')
				print ('dd ', dd)
				print ('ddsplit ', dd.split(' '))
				print ('ddsplit ', len(dd.split(' ')))
				dd0 = dd.split(' ')
				print ('dd0 ', len(dd0))
				print ('DATAS ', re.match(date_pattern,dd0[0].strip()))
				print ('DATAS ', re.match(date_pattern,dd.strip()))

				print ('Net Empresas por in dd ', "Net Empresas por" in dd)
				print ('bfatransferencia ',bfatransferencia)

				print (len(dd.strip()[dd.strip().rfind(' '):].strip()))
				print (len(dd.strip()[dd.strip().rfind(' '):].strip()) == 14)
				print (dd.strip()[dd.strip().rfind(' '):].strip())

				print ('CASH')
				print (re.match(cash_pattern,dd.strip()))
				#print ('.' in dd and ',' in dd)
				#for ff in dd.split(' '):
				#	print (re.match(cash_pattern,ff.strip()))
				print ('IBAns CHECK')
				print (dd.startswith("ACO6"))
				print (dd.startswith("ACO6.0006.0000.6671.9425"))
				print (dd.startswith("ADOG.0006.0000.6671.9425"))
				#frappe.throw(porra)

				#FIX 21-09-2023; Check if has the Reference Number and search online ....
				if "AUTOLIQUIDAÇÃO RETENÇÃO NA FONTE" in dd.strip() or "AUTOLIQUPAGRO RETENÇAO A FONTE" in dd.strip():
					print ('Verify is Number is visible and VALID')
					print (dd[0:dd.rfind(' ')])
					print (dd.strip()[dd.strip().rfind(' '):].strip())
					#230104899092230

					if "AUTOLIQUPAGRO RETENÇAO A FONTE =" in dd.strip():
						#FRENCH OCR....
						print (dd[dd.find("A FONTE =")+10+4:].strip().replace(' ',''))
						print (len(dd[dd.find("A FONTE =")+10+4:].strip().replace(' ','')) == 15)
					else:
						print (len(dd.strip()[dd.strip().rfind(' '):].strip()) == 15)
					print ('search online.... https://portaldocontribuinte.minfin.gov.ao/imprimir-verificar-nf-nl')

					#Try SCAN FOR OCR
					rr = qrcode_scan_decode(filefinal)
					print (rr)
					if rr != False:
						return rr

					frappe.throw(porra)
				elif "230" in dd.strip() or "2310" in dd.strip():
					print (dd)
					frappe.throw(porra)


				elif "LIQUIDAÇÃO GENÉRICA DE TRIBUTO" in dd.strip():
					print ('Numero Referencia..')
					print (dd[0:dd.find(' ')])
					print (dd[0:dd.find(' ')].strip().isnumeric())
					if dd[0:dd.find(' ')].strip().isnumeric():
						referenciadocumento = dd[0:dd.find(' ')].strip()
						print (referenciadocumento)
					#frappe.throw(porra)
				elif "COMPROVATIVO DA OPERACAO" in dd or "COMPROVATIVO DA OPERAÇÃO" in dd:
					bfatransferencia = True
				elif "Comprovativo Digital" in dd or "MULTICAIXA Express." in dd:
					multiexpress = True
				elif "Data-Hora" in dd or "Data - Hora" in dd:
					#FIX 02-10-2023
					if multiexpress:
						if "Data - Hora" in dd:
							tmpdata = dd.replace("Data - Hora",'').strip().split(' ')
							if len(tmpdata) == 2:
								datadePAGAMENTO = str(dd.split(' ')[0]) + " " + str(dd.split(' ')[1])
						else:
							datadePAGAMENTO = str(dd.split(' ')[2]) + " " + str(dd.split(' ')[3])
						print ('datadePAGAMENTO ',datadePAGAMENTO)
				elif "Destinatário" in dd or "Destinatario" in dd:
					if multiexpress:
						nomeDestinatario = dd[dd.find('|')+1:len(dd)].strip()
						print ('nomeDestinatario ',nomeDestinatario)

				elif "Montante" in dd and multiexpress:
					#FIX 02-10-2023
					if len(dd.split(' ')) == 2:
						print ('Montante ',re.match(cash_pattern,dd.split(' ')[1].strip()))
						if not valorPAGO:
							valorPAGO = dd.split(' ')[1].strip()
							print ('valorPAGO ',valorPAGO)
							#frappe.throw(porra)
					elif len(dd.split(' ')) >= 3:
						print ('Montante ',re.match(cash_pattern,dd.split(' ')[2].strip()))
						if not valorPAGO:
							valorPAGO = dd.split(' ')[2].strip()
							print ('valorPAGO ',valorPAGO)
							#frappe.throw(porra)
				elif ("Transacção".upper() in dd.upper() or "Transacgao".upper() in dd.upper() or "TRANSACÇÃD:" in dd.upper()) and multiexpress:
					#FIX 02-10-2023
					if not numeroOperacao:
						if len(dd.split(' ')) == 2:
							numeroOperacao = dd.split(' ')[1]
							print ('numeroTransacao ',numeroOperacao)
						elif len(dd.split(' ')) > 2:
							numeroOperacao = dd.split(' ')[2]
							print ('numeroTransacao ',numeroOperacao)
					#frappe.throw(porra)
				elif ("IBAN:" in dd or "BAN:" in dd) and multiexpress:
					print ('ibanOrigem ',ibanOrigem)
					#frappe.throw(porra)
					if not ibanOrigem:
						print ('IBAN ORIGEM.... ',re.match(iban_pattern,dd.split(' ')[1].strip()))
						ibanOrigem = dd.split(' ')[1]
						print ('ibanOrigem ',ibanOrigem)

				elif "IBAN" in dd and multiexpress:
					if len(dd.split(' ')) > 2:
						print ('IBAN DEST. ',re.match(iban_pattern,dd.split(' ')[2].strip()))
						if not ibanDestino:
							if re.match(iban_pattern,dd.split(' ')[2].strip()):
								ibanDestino = dd.split(' ')[2].strip()
								print ('ibanDestino ',ibanDestino)
					elif len(dd.split(' ')) == 2:
						print ('IBAN DEST. ',re.match(iban_pattern,dd.split(' ')[1].strip()))
						if not ibanDestino:
							tmp_iban = dd.split(' ')[1]
							if dd.split(' ')[1].startswith('AOQ06'):
								tmp_iban = dd.split(' ')[1].replace('AOQ06','AO06')

							if re.match(iban_pattern,tmp_iban.strip()):
								ibanDestino = tmp_iban.strip()
								print ('ibanDestino ',ibanDestino)

					#frappe.throw(porra)

				elif "Net Empresas por" in dd and bfatransferencia or "Nect Empresas por" in dd and bfatransferencia or "Netrt Empresas por" in dd and bfatransferencia:
					print ('dd ', dd)
					print (dd.strip()[dd.strip().find('Net Empresas por')+16:])
					print ('find ', dd.strip().find('Net Empresas por'))
					empresaOrigem0 = dd.strip()[dd.strip().find('Net Empresas por')+16:]
					if dd.strip().find('Net Empresas por') == -1:
						empresaOrigem0 = dd.strip()[dd.strip().find('Nect Empresas por')+17:]
					print ('empresaOrigem0 ',empresaOrigem0)

					Datapagamento = dd[0:dd.find('foi realizada')].strip()
					dia = Datapagamento[3:5]
					mes0 = Datapagamento[Datapagamento.find('de ')+2:len(Datapagamento)].strip()
					mes = mes0[0:mes0.find('de')].strip()
					ano = Datapagamento[len(Datapagamento)-5:].strip()
					print ('Datapagamento ',Datapagamento)
					print ('dia ', dia)
					print ('mes ', mes)
					print ('ano ', ano)
					mes0 = mes.strip().replace('janeiro','01').replace('fevereiro','02').replace('margo','03').replace('março','03').replace('marco','03').replace('abril','04').replace('maio','05') \
					.replace('junho','06').replace('julho','07').replace('agosto','08').replace('setembro','09').replace('serembro','09').replace('outubro','10').replace('novembro','11').replace('dezembro','12')

					mes = mes0

					Datapagamento = dia.strip() + "-" + mes.strip() + "-" + ano.strip()
					print ('Datapagamento ',Datapagamento)

					datadePAGAMENTO = Datapagamento


				elif ", sobre a conta n°" in dd or ", sobre a conta nº" in dd and bfatransferencia:
					if ", sobre a conta nº" in dd:
						empresaOrigem1 = dd.strip()[0:dd.strip().find(", sobre a conta nº")]
						tmpconta =  dd.strip()[dd.strip().find(", sobre a conta nº")+18:]
					else:
						empresaOrigem1 = dd.strip()[0:dd.strip().find(', sobre a conta n°')]
						tmpconta =  dd.strip()[dd.strip().find(', sobre a conta n°')+18:]
					#print ('empresaOrigem0 ',empresaOrigem0)
					print ('empresaOrigem1 ',empresaOrigem1)
					if empresaOrigem0:
						if empresaOrigem1:
							empresaOrigem0 = empresaOrigem0 + empresaOrigem1

					#tmpconta =  dd.strip()[dd.strip().find(', sobre a conta n°')+18:]
					print ('tmpconta ',tmpconta)
					contaOrigem = tmpconta[0:tmpconta.find(',')]
					print ('contaOrigem ',contaOrigem)

					#frappe.throw(porra)
				elif len(dd.strip()[dd.strip().rfind(' '):].strip()) == 14:
					#16671942530001
					print ('ORIGEM OU DESTINO CONTA')
					if contaOrigem and contaOrigem.strip() != dd.strip()[dd.strip().rfind(' '):].strip():
						#Conta DESTINO
						if not contaCreditada:
							contaCreditada = dd.strip()[dd.strip().rfind(' '):].strip()
						print ('contaCreditada0 ',contaCreditada)
					elif not contaOrigem:
						contaOrigem = dd.strip()[dd.strip().rfind(' '):].strip()
						print ('contaOrigem ',contaOrigem)

					#frappe.throw(porra)

				elif bfatransferencia and len(dd.split(' ')) >=13:
					#Conta numero Origem ou DESTINO
					print ('origem/destino ',dd.split(' ')[12])
					if len(dd.split(' ')[12]) == 14 and contaOrigem and contaOrigem.strip() != dd.split(' ')[12].strip():
						#Conta DESTINO
						if not contaCreditada:
							contaCreditada = dd.split(' ')[12].strip()
						print ('contaCreditada1 ',contaCreditada)
					elif len(dd.split(' ')[12]) == 14 and not contaOrigem:
						contaOrigem = dd.split(' ')[12].strip()
						print ('contaOrigem ',contaOrigem)

						#frappe.throw(porra)
				elif "Descritivo da Operacdo" in dd or "Descritivo da " in dd and bfatransferencia:
					#descricao da Operacao...
					tmpdescricao = dd[23:]
					if not descricaoPagamento:
						descricaoPagamento = tmpdescricao.strip()
						print ('descricaoPagamento ',descricaoPagamento)
				elif "N.º da Operação" in dd and bfatransferencia:
					if dd.strip()[dd.strip().rfind(' '):].strip().isnumeric():
						numeroOperacao = dd.strip()[dd.strip().rfind(' '):].strip()
					print ('numeroOperacao ',numeroOperacao)
					#frappe.throw(porra)

				elif "DADOS DO CONTRIBUINTE:" in dd:
					Temdadoscontribuinte = True
					print('Temdadoscontribuinte ', Temdadoscontribuinte)

				elif Temdadoscontribuinte and not dadoscontribuinte:
					dadoscontribuinte = dd.strip()
					print ('dadoscontribuinte')
					print (dadoscontribuinte)
					#frappe.throw(porra)
				elif "LUANDA - ANGOLA" in dd:
					#Might be different on other... with time will be added more or changed...
					TemdadoscontribuinteNIF = True
				elif TemdadoscontribuinteNIF and not dadoscontribuinteNIF:
					dadoscontribuinteNIF = dd.strip()
				elif "MENSAL" in dd:
					#Ano, Periodo
					if dd[0:dd.find(' ')].strip().isnumeric():
						referenciaANO = dd[0:dd.find(' ')].strip()
						referenciaPERIODO = dd[dd.find(' '):dd.find(' LUANDA')].strip()
						print ('referenciaANO ', referenciaANO)
						print ('referenciaPERIODO ', referenciaPERIODO)
						#frappe.throw(porra)
				elif len(dd0) == 10:
					print ('IMPOSTO!!!!!')
					print (dd.split(' ')[8])
					print (dd.split(' ')[7])
					print (dd.split(' ')[9])
					if dd.split(' ')[8].strip() == '65%' or dd.split(' ')[8].strip() == '6.5%':
						#Retencao 6.5
						descricaoRECEITA = "IMPOSTO INDUSTRIAL - RETENÇÃO NA FONTE"
						#Check valortributavel
						tmpvalorPagar = dd.split(' ')[9]
						print ('tmpvalorPagar ', tmpvalorPagar)
						tmpTAXA = dd.split(' ')[8]
						print ('tmpTaxa ', tmpTAXA)
						Tmpvalortributavel = dd.split(' ')[7]
						print ('Tmpvalortributavel ', Tmpvalortributavel)
					#frappe.throw(porra)

				elif ("INDUSTRIAL - RETENGAO NA FONTE" in dd.strip() or "INDUSTRIAL - RETENÇÃO NA FONTE" in dd.strip()): #and ("A28" in dd.strip() or "03C" in dd.strip()):
					#FIX 21-09-2023; Removed A28 and Removed 03C as a check and changed from OR to AND
					print ('descricao receita')
					if not Tmpvalortributavel:
						descricaoRECEITA = "IMPOSTO INDUSTRIAL - RETENÇÃO NA FONTE"
						#Check valortributavel
						print (dd)
						tmpvalorPagar = dd[dd.rfind(' '):].strip()
						print ('tmpvalorPagar ', tmpvalorPagar)
						dd1 = dd[0:dd.rfind(' ')].strip()
						tmpTAXA = dd[find_second_last(dd,' '):dd.rfind(' ')]
						print ('tmpTaxa ', tmpTAXA)
						dd2 = dd1[find_second_last(dd1,' '):dd1.rfind(' ')]
						print ('dd2 ', dd2)
						Tmpvalortributavel = dd2[0:len(dd2)-dd2.rfind(' ')].strip()
						print ('Tmpvalortributavel ', Tmpvalortributavel)
					frappe.throw(porra)

				elif "VALOR TOTAL PAGO" in dd:
					print ("VALOR TOTAL PAGO")
					print (dd.split(' ')[3])
					if len(dd.split(' ')) == 5:
						valorPAGO = dd.split(' ')[3]
						print ('valorPAGO ', valorPAGO)
						frappe.throw(porra)
				elif "VALOR PAGO" in dd:
					#next line will have paidvalue
					nextlinha = True
				elif nextlinha:
					print ('qqqq', dd)
					if "," in dd.strip() and "." in dd.strip():
						print ('VALOR PAGO. ',re.match(cash_pattern,dd.strip()))
						if not valorPAGO:
							valorPAGO = dd.strip()
					nextlinha = False
					#frappe.throw(porra)

				elif "TRANSACCAI" in dd and len(dd.split(' ')) == 2:
					#Caso unico where N.CAIXA numbers are first and TEXT Will be after...
					ncaixa_pattern = r'^([0-9][0-9][0-9][0-9])\/([0-9][0-9][0-9][0-9])\/([0-9][0-9])'
					print (len(dd.split(' ')[0].strip()))
					print (len(dd.split(' ')[0]))
					print (dd.split(' ')[0].strip())
					if len(dd.split(' ')[0].strip()) == 12:
						ncaixa_tmp = dd.split(' ')[0].strip()
						print ('N.Caixa. ',re.match(ncaixa_pattern,ncaixa_tmp))
						mcexpress = True
						numeroTransacao = ncaixa_tmp

				elif "N.CAIXA:" in dd or "N.CATXA:" in dd or "W.CAIXA:" in dd:
					#Fix to check W.CAIXA as scan was not good...
					print ('N. Caixa e Num Transacao')
					if not numeroTransacao:
						mcexpress = True
						numeroTransacao = dd[dd.rfind(' '):].strip()
						if not numeroTransacao.strip().isnumeric():
							numeroTransacao = ""
						if not numeroTransacao:
							#get NCaixa instead...
							if len(dd.split(' ')) == 4:
								numeroTransacao = dd.split(' ')[1].strip()

						print ('numeroTransacao ',numeroTransacao)
						#frappe.throw(porra)
				elif "CONTA:" in dd:
					print ('mcexpress', mcexpress)
					print ('Conta e Data')
					contaOrigem = dd[dd.find(' '):find_second_last(dd, ' ')].strip()

					if len(dd.split(' ')) == 9:
						#User might Scanned the payment together with main INVOICE sent to him... mixed numbers from FT and payment done when scanned.
						print (dd.split(' ')[3].strip())
						if dd.split(' ')[3].strip().startswith('OO'):
							contaOrigem = dd.split(' ')[3].strip().replace('OO','00')
							print ('contaOrigem0 ',contaOrigem)
							print (contaOrigem.isnumeric())
						else:
							contaOrigem = dd.split(' ')[3].strip()
							print ('contaOrigem0 ',contaOrigem)
							print (contaOrigem.isnumeric())

						#Data pagamento
						datadePAGAMENTO = str(dd.split(' ')[4].strip()) + ' ' + str(dd.split(' ')[5].strip())

					elif len(dd.split(' ')) == 4:
						#Case len 4
						#0 Conta:, 1 IBAN, 2 Date, 3 Hour
						print (dd.split(' ')[1].strip())
						if dd.split(' ')[1].strip().startswith('OO') or dd.split(' ')[1].strip().startswith('O0'):
							contaOrigem = dd.split(' ')[1].strip().replace('OO','00').replace('O0','00')
							print ('contaOrigem0 ',contaOrigem)
							print (contaOrigem.isnumeric())
						else:
							contaOrigem = dd.split(' ')[1].strip()
							print ('contaOrigem0 ',contaOrigem)
							print (contaOrigem.isnumeric())

						#Data pagamento
						datadePAGAMENTO = str(dd.split(' ')[2].strip()) + ' ' + str(dd.split(' ')[3].strip())


					elif not contaOrigem:
						#try again...
						print ('try again...')
						if len(dd.split(' ')) == 3:
							print (dd.split(' ')[1].strip())
							if dd.split(' ')[1].strip().startswith('OO'):
								contaOrigem = dd.split(' ')[1].strip().replace('OO','00')
								print ('contaOrigem0 ',contaOrigem)
								print (contaOrigem.isnumeric())
							elif dd.split(' ')[1].strip().isnumeric():
								contaOrigem = dd.split(' ')[1].strip()

							if "2q22/" in dd.split(' ')[2]:
								#for sure is 2022
								datadePAGAMENTO = dd.split(' ')[2].strip().replace('2q22','2022')



					print ('contaOrigem0000 ',contaOrigem)
					if not datadePAGAMENTO:
						datadePAGAMENTO = dd[find_second_last(dd, ' '):len(dd)].strip()
					if not datadePAGAMENTO:
						#try again...
						if len(dd.split(' ')) == 3:
							if "2q22/" in dd.split(' ')[2]:
								#for sure is 2022
								datadePAGAMENTO = dd.split(' ')[2].strip().replace('2q22','2022')

					print ('datadePAGAMENTO ',datadePAGAMENTO)


					#frappe.throw(porra)

				elif dd[0:dd.find(' ')].strip().isnumeric():
					#Can be NIF for Benificiario...
					#5417537802 TEOR LOGICO-PRESTACAO DE SERVICOS LDA.

					print ('contaOrigem ',contaOrigem)
					print (dd.strip())
					print ('ibanDestino ',ibanDestino)
					print ('ibanDestino ',ibanDestino == None)
					print ('ibanDestino ',ibanDestino == '')
					print (dd[0:dd.find(' ')].strip())
					print (dd.find(' '))
					print (len(dd[0:dd.find(' ')].strip()))

					#Check for Numeroperacao...
					if not numeroOperacao:
						if dd.find(' ') == -1:
							if len(dd.strip()) == 9:
								numeroOperacao = dd.strip()

						elif len(dd[0:dd.find(' ')].strip()) == 9:
							numeroOperacao = dd.strip()
					if not contaOrigem:
						if len(dd[0:dd.find(' ')].strip()) == 14:
							contaOrigem = dd.strip()
					if contaOrigem and ibanDestino == '':
						#To prevent removing last digit...
						if contaOrigem.strip() != dd.strip():
							if dd.find(' ') == -1:
								if len(dd.strip()) == 14:
									ibanDestino = dd.strip()
									print ('ibanDestino1 ', ibanDestino)

							elif len(dd[0:dd.find(' ')].strip()) == 14:
								ibanDestino = dd.strip()
								print ('ibanDestino ', ibanDestino)
							if not contaCreditada:
								contaCreditada = ibanDestino
								print ('contaCreditada2 ', contaCreditada)


					if len(dd[0:dd.find(' ')].strip()) == 10:
						#NIF
						BeneficiarioNIF = dd[0:dd.find(' ')].strip()
					print ('NUMEROSSSSSSS')

					#Check for Referencia Pagamento
					if temreferenciaDar and not referenciaDAR:
						if dd.isnumeric() and len(dd) == 12:
							referenciaDAR = dd.strip()

				elif re.match(iban_pattern,dd.strip()):
					print ('IBAN DEST. ',re.match(iban_pattern,dd.strip()))
					if mcexpress:
						#IBAN Destinatario
						ibanDestino = dd.strip()
						print ('ibanDestino ',ibanDestino)
					frappe.throw(porra)
				elif temreferenciaDar:
					tmprefedar = dd
					print ('tmprefedar ',tmprefedar)
					if len(tmprefedar) == 13:
						#remove T
						print ('remove T ')
						tmprefedar1 = tmprefedar.replace('T','')
						print ('tmprefedar1 ',tmprefedar1)
						if tmprefedar1.isnumeric():
							if not referenciaDAR:
								referenciaDAR = tmprefedar1.strip()
								print ('referenciaDAR ',referenciaDAR)
					if dd.startswith('467'):
						frappe.throw(porra)


				elif re.match(cash_pattern,dd.strip()):
					print ('VALOR PAGO3 . ',re.match(cash_pattern,dd.strip()))
					#if len(re.match(cash_pattern,dd.strip())) > 3:
					print (mcexpress)
					print (bfatransferencia)
					print ('valorPAGO ',valorPAGO)

					if mcexpress:
						#IBAN Destinatario
						if not valorPAGO:
							valorPAGO = dd.replace(' ,',',').strip()
							print ('valorPAGO mcexpress ',valorPAGO)
					elif bfatransferencia:
						if not valorPAGO:
							valorPAGO = dd.strip().replace('AKRZ','AKZ')
							print ('valorPAGO bfatransferencia ',valorPAGO)
					#elif not valorPAGO:
					#	valorPAGO = dd.strip()
					#	print ('valorPAGO ',valorPAGO)
					#	frappe.throw(porra)


					#frappe.throw(porra)

				elif re.match(date_pattern,dd.strip()):
					print ('DATAAAAAAASSSS')
					#DATA....Pagamento ou EMISSAO
					if not datadePAGAMENTO and not dataEMISSAO:
						datadePAGAMENTO = dd.strip()
						dataEMISSAO = dd.strip()
						print ('dataEMISSAO ', dataEMISSAO)
						print ('datadePAGAMENTO ', datadePAGAMENTO)

				elif "Nº REFERÊNCIA DO PAGAMENTO" in dd or "N° REFERÉNCIA DO PAGAMENTO" in dd:
					temreferenciaDar = True
					#frappe.throw(porra)
				elif dd.startswith("AO06") or dd.startswith("A006") or dd.startswith("AONE") or dd.startswith("ACO6") or dd.startswith("ADOG") or dd.startswith("ADO6"):
					print ('IBAN....')
					print (len(dd))
					print (dd)
					print (dd.replace(',','.').replace(' ','').strip())
					tmpiban = dd.replace(',','.').replace(' ','').replace('AONE','AO06').replace('C006','0006').replace('ACO6','AO06').replace('ADOG','AO06').replace('ADO6','AO06').strip()
					#Check if two or more DOTS together...
					tmpiban1 = tmpiban.replace('..','.')
					tmpiban = tmpiban1
					#Check if all have 4 digits minus the last one.... if missing a ZERO just add
					novotmpiban = ""
					for a in tmpiban.split('.'):
						if len(a.strip()) > 1 and len(a.strip()) < 4:
							#just add a ZERO
							novotmpiban = str(novotmpiban) + "0" + str(a.strip())  + "."
						elif len(a.strip()) == 4:
							novotmpiban = str(novotmpiban) + str(a.strip()) + "."
						elif len(a.strip()) == 1:
							#last Digit
							novotmpiban = str(novotmpiban) + str(a.strip())
					if novotmpiban:
						tmpiban = novotmpiban
					print ("novotmpiban ",novotmpiban)
					print ('IBAN DEST. ',re.match(iban_pattern,tmpiban.strip()))
					if re.match(iban_pattern,tmpiban.strip()):
						if mcexpress and not ibanDestino:
							#IBAN Destinatario
							ibanDestino = tmpiban.strip()
							print ('ibanDestino ',ibanDestino)

					#frappe.throw(porra)

				elif '.' in dd and ',' in dd:
					for ff in dd.split(' '):
						print ('ff ', ff.strip())
						print (re.match(cash_pattern,ff.strip()))
						print ('bfatransferencia ', bfatransferencia)
						print (re.match(cash_pattern,ff.strip()))
						print ('Numerico ', ff.strip().isnumeric())
						print ('Numerico ', ff.strip().replace('.','').replace(',','').isnumeric())
						print ('valorPAGO ',valorPAGO)

						if re.match(cash_pattern,ff.strip()):
							#if len(ff.strip()) > 1:
							print ("Contribuínte")
							print ("Contribuínte" in dd)
							if ff.strip().isnumeric() and "Contribuínte" not in dd:
								if bfatransferencia and not valorPAGO:
									valorPAGO = ff.strip()
									frappe.throw(porra)
							elif ff.strip().replace('.','').replace(',','').isnumeric() and "Contribuínte" not in dd:
								if bfatransferencia and not valorPAGO:
									valorPAGO = ff.strip()

				elif 'FT ' in dd or 'PP ' in dd:
					#Tem Factura ou Proforma como descricao...
					print (dd)
					if 'FT ' in dd:
						print ('Descricao do Pagamento...')
						print (descricaoPagamento)
						if descricaoPagamento == "":
							descricaoPagamento = dd[dd.find('FT '):]

					elif 'PP ' in dd:
						print (' POR FAZER PARA PROFORMAS....')


				#frappe.throw(porra)
		print ('bfatransferencia ', bfatransferencia)
		print ('valorPAGO ', valorPAGO)
		print ('contaCreditada ', contaCreditada)
		print ('ibanDestino ', ibanDestino)
		print ('contaOrigem ', contaOrigem)

		if referenciaDAR and valorPAGO: # and BeneficiarioNIF:
			return {
				'referenciadocumento':referenciadocumento,
				'dadoscontribuinte':dadoscontribuinte,
				'dadoscontribuinteNIF':dadoscontribuinteNIF,
				'referenciaANO':referenciaANO,
				'referenciaPERIODO': referenciaPERIODO,
				'BeneficiarioNIF': BeneficiarioNIF,
				'descricaoRECEITA': descricaoRECEITA,
				'tmpvalorPagar': tmpvalorPagar,
				'tmpTAXA': tmpTAXA,
				'Tmpvalortributavel': Tmpvalortributavel,
				'valorPAGO': valorPAGO,
				'datadePAGAMENTO': datadePAGAMENTO,
				'dataEMISSAO': dataEMISSAO,
				'referenciaDAR': referenciaDAR
			}
		elif mcexpress and valorPAGO and ibanDestino:
			#Multicaixa EXPRESS
			return {
				"mcexpress": mcexpress,
				"numeroTransacao": numeroTransacao,
				"datadePAGAMENTO": datadePAGAMENTO,
				"contaOrigem": contaOrigem or ibanOrigem,
				"ibanDestino": ibanDestino,
				"valorPAGO": valorPAGO
			}
		elif bfatransferencia and valorPAGO and contaCreditada:
			#Multicaixa EXPRESS
			print ('#Multicaixa EXPRESS')
			#frappe.throw(porra)
			#missing Numero Operacao .. do OCR again por por,300
			if not numeroOperacao:
				ocr_tesserac1 = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'por',False,300)
				for aa in ocr_tesserac1.split('\n'):
					print (aa)
					print (aa[aa.rfind(' '):])
					tmpnumero = aa[aa.rfind(' '):].strip()
					if len(tmpnumero) == 10 and tmpnumero.strip().isnumeric():
						numeroTransacao = aa[aa.rfind(' '):].strip()
						break
			else:
				numeroTransacao = numeroOperacao
			return {
				"bfatransferencia": bfatransferencia,
				"numeroTransacao": numeroTransacao,
				"datadePAGAMENTO": datadePAGAMENTO,
				"contaOrigem": contaOrigem,
				"contaCreditada": contaCreditada,
				"valorPAGO": valorPAGO,
				"descricaoPagamento": descricaoPagamento
			}
		elif multiexpress and valorPAGO and ibanDestino:
			#Multicaixa EXPRESS PHONE; IMAGEM
			return {
				"multiexpress": multiexpress,
				"numeroTransacao": numeroOperacao,
				"datadePAGAMENTO": datadePAGAMENTO,
				"contaOrigem": ibanOrigem,
				"ibanDestino": ibanDestino,
				"valorPAGO": valorPAGO
			}



		#Resumo dos DADOS
		print ('====================')
		print ('referenciadocumento ',referenciadocumento)
		print ('dadoscontribuinte ',dadoscontribuinte)
		print ('dadoscontribuinteNIF ',dadoscontribuinteNIF)
		print ('referenciaANO ',referenciaANO)
		print ('referenciaPERIODO ', referenciaPERIODO)
		print ('BeneficiarioNIF ', BeneficiarioNIF)
		print ('descricaoRECEITA ',descricaoRECEITA)
		print ('tmpvalorPagar ', tmpvalorPagar)
		print ('tmpTAXA ', tmpTAXA)
		print ('Tmpvalortributavel ', Tmpvalortributavel)
		print ('valorPAGO ',valorPAGO)
		print ('datadePAGAMENTO ',datadePAGAMENTO)
		print ('dataEMISSAO ', dataEMISSAO)
		print ('referenciaDAR ', referenciaDAR)


	elif "Modelo 6 de IVA" in ocr_tesserac:
		print ('AINDA POR FAZER.... Modelo 6 de IVA')
		print ('AINDA POR FAZER.... Modelo 6 de IVA')
		print ('AINDA POR FAZER.... Modelo 6 de IVA')

		#procura pelo REG if not run again with 180 DPI or 300
		#REG19007009587X

		datasubmissaoTEMP = ""
		NIFContribuinte = ""
		temREG = False

		for aa in ocr_tesserac.split('\n'):
			if aa.find('REG') != -1 and len(aa) == 15:
				#Pode ser o Numero de Declaracao... if has 11 numbers
				print ('REGNumbers ', aa[3:len(aa)-1])
				temREG = True

		if not temREG: #not "REG" in ocr_tesserac:
			ocr_tesserac1 = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'por',False,180)
			print (ocr_tesserac1.split('\n'))
			for aa in ocr_tesserac1.split('\n'):
				if aa.find('REG') != -1 and len(aa) == 15:
					#Pode ser o Numero de Declaracao... if has 11 numbers
					print ('REGNumbers ', aa[3:len(aa)-1])
					referenciadocumento = aa.strip()
					temREG = True
				elif re.match(date_pattern,aa.strip()):
					if not datasubmissaoTEMP:
						datasubmissaoTEMP = aa.strip()
						print ('datasubmissaoTEMP ', datasubmissaoTEMP)
				elif len(aa.strip()) == 10:
					#Might be NIF
					if aa.strip().isnumeric() and not NIFContribuinte:
						NIFContribuinte = aa.strip()
						print ('NIFContribuinte ', NIFContribuinte)
			if referenciadocumento and datasubmissaoTEMP and NIFContribuinte:
				#Still missing to find what REGIME is it on....
				return {
					'referenciadocumento': referenciadocumento,
					'datasubmissaoTEMP': datasubmissaoTEMP,
					'NIFContribuinte': NIFContribuinte
				}

	if not ocr_tesserac or not ocr_tesserac1 or not referenciadocumento:
		#frappe.throw(porra)
		print ('///////////////////////////')
		print ('Redo the OCR with eng, 200')
		print ('Redo the OCR with eng, 200')
		print ('Redo the OCR with eng, 200')
		print ('///////////////////////////')

		contaOrigem = ''
		ibanDestino = ''
		numeroTransacao = ''
		dataEMISSAO = ''
		valorPAGO = ''


		ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'eng',False,250)
		print (ocr_tesserac)
		print ('CALL lerdocumento 1111111....')
		mcexpress,numeroTransacao,dataEMISSAO,contaOrigem,ibanDestino,valorPAGO = lerdocumento(ocr_tesserac)

		print (mcexpress)
		print (numeroTransacao)
		print (dataEMISSAO)
		print (contaOrigem)
		print (ibanDestino)
		print (valorPAGO)

		#frappe.throw(porra)
		'''
		print (ocr_tesserac.split('\n'))
		for aa in ocr_tesserac.split('\n'):
			#271462936
			print ('=======')
			print ('aa ', aa)
			if aa != "" and aa != None:
				print (re.match(cash_pattern,aa.strip()))

				#Cliente anexou Nossa Factura + Pagamento via ATM MULTICAIXA
				if (aa.find('TRANSACGAO: ') != -1 or aa.find('TRANSACGAD: ') != -1 or aa.find('TRANSACÇÃO: ') != -1) and aa.find('Exmo(s) Senhor(es)') != -1 :
					if aa.find('TRANSACGAO:') != -1:
						tmpnumeroTrans = aa[aa.find('TRANSACGAO:')+12:aa.find('Exmo(s) Senhor(es)')]
					elif aa.find('TRANSACGAD:') != -1:
						tmpnumeroTrans = aa[aa.find('TRANSACGAD:')+12:aa.find('Exmo(s) Senhor(es)')]
					elif aa.find('TRANSACÇÃO:') != -1:
						tmpnumeroTrans = aa[aa.find('TRANSACÇÃO:')+12:aa.find('Exmo(s) Senhor(es)')]

					print ('tmpnumeroTrans ',tmpnumeroTrans)
					numeroTransacao = tmpnumeroTrans
				elif aa.find('CONTA: ') != -1:
					#assuming Conta and Date of payment...
					print (aa[aa.find('CONTA: ')+7:])
					tmpconta = aa.split(' ')[1] # aa[aa.find('CONTA: ')+7:]
					if contaOrigem == '':
						contaOrigem = tmpconta.replace('OO','00')
					print ('tmpconta ', tmpconta)
					if len(aa.split(' ')) == 4:
						dataEMISSAO = aa.split(' ')[2]
						print ('dataEMISSAO ', dataEMISSAO)
				elif aa.find('TRANSFERENCIA BANCARTA') != -1 or aa.find('TRANSFERENCIA BANCARIA') != -1 or aa.find('TRANSFERÈNCIA BANCÁRIA') != -1:
					mcexpress = True

				elif re.match(cash_pattern,aa.strip()):
					print ('PAGAMENTO....')
					print (re.match(cash_pattern,aa.strip()).string.replace('ka',''))
					if valorPAGO == '':
						valorPAGO1 = re.match(cash_pattern,aa.strip()).string
						print (valorPAGO1)
						print (valorPAGO1.split(' '))
						#print (' Ka' in valorPAGO1)
						valorPAGO = valorPAGO1.replace(' Ka','')
						print ('valor Pago ', valorPAGO)
					#frappe.throw(porra)

				# +++++  FIM Cliente anexou Nossa Factura + Pagamento via ATM MULTICAIXA

				if aa.find(' foi realizada Transferéncia Interna no BFA Net') != -1:
					#Get DATA EMISSAO
					print (aa)
					datatmp = aa[0:aa.find(' foi realizada Transferéncia Interna no BFA Net')]
					print ('datatmp ', datatmp)
					#TODO: Format DATA to YYYY-MM-DD

				if aa.find(', sobre a conta n° ') != -1:
					#IBAN Origem
					print (aa)
					tmpcontaOrigem = aa[aa.find(', sobre a conta n° ')+20:]
					tmpconta = tmpcontaOrigem[0:tmpcontaOrigem.find(', ')]
					print ('tmpconta ',tmpconta)
					contaOrigem = tmpconta

				if aa.find('REG') != -1 and len(aa) == 15:
					#Pode ser o Numero de Declaracao... if has 11 numbers
					print ('REGNumbers ', aa[3:len(aa)-1])
					referenciadocumento = aa.strip()
					temREG = True
				elif re.match(date_pattern,aa.strip()):
					if not datasubmissaoTEMP:
						datasubmissaoTEMP = aa.strip()
						print ('datasubmissaoTEMP ', datasubmissaoTEMP)
				elif len(aa.strip()) == 10:
					#Might be NIF
					if aa.strip().isnumeric() and not NIFContribuinte:
						NIFContribuinte = aa.strip()
						print ('NIFContribuinte ', NIFContribuinte)
		'''
		#Check if contaOrigem is only Numbers....
		if len(contaOrigem) == 15 and contaOrigem.isnumeric():
			if dataEMISSAO and contaOrigem and valorPAGO:
				return {
					"mcexpress": mcexpress,
					"numeroTransacao": numeroTransacao,
					"datadePAGAMENTO": dataEMISSAO,
					"contaOrigem": contaOrigem,
					"ibanDestino": ibanDestino,
					"valorPAGO": valorPAGO
				}
		else:
			#Try scan again FRA
			print ('Tentar FRA')
			ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'fra',False,250)
			print (ocr_tesserac)
			print ('CALL lerdocumento....')
			#print (lerdocumento(ocr_tesserac))
			mcexpress,numeroTransacao,dataEMISSAO,contaOrigem,ibanDestino,valorPAGO = lerdocumento(ocr_tesserac)

		if len(contaOrigem) == 15 and contaOrigem.isnumeric():
			print ('Segunda Tentativa.....!!!!!!')
			print (dataEMISSAO)
			print (contaOrigem)
			print (valorPAGO)

			if dataEMISSAO and contaOrigem and valorPAGO:
				return {
					"mcexpress": mcexpress,
					"numeroTransacao": numeroTransacao,
					"datadePAGAMENTO": dataEMISSAO,
					"contaOrigem": contaOrigem,
					"ibanDestino": ibanDestino,
					"valorPAGO": valorPAGO
				}

		#return "403 Forbidden"	#Because if IMAGE.... FOR NOW 04-10-2022
		#frappe.throw(porra)
		print ('Tentar FRA')
		ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'fra',False,250)
		print (ocr_tesserac)

		#Try to lerPdf_ocr as CSV to extract TEXT
		#FIX 25-09-2023
		if lingua:
			print ('Testa lerPDF_OCR com lingua ', lingua)
			lerpdfocr = ocr_pdf.lerPdf_ocr(filefinal,6,lingua)
		else:
			lerpdfocr = ocr_pdf.lerPdf_ocr(filefinal,6,'por')
		print ('////// lerpdfocr \\\\\\\\')
		print (lerpdfocr)
		if lerpdfocr and ".pdf" in filefinal: # lerpdfocr:
			bancoBic = False
			contaOrigem = ''
			dataEMISSAO = ''
			numeroDocumento = ''
			numeroOperacao = ''
			descricaoPagamento = ''
			valorPAGO = ''
			ibanDestino = ''
			ibanOrigem = ''

			bancoBAIDIRECTO = False

			'''
				TODO:
				After running below if nothing returns...
				Trying to read any PDF and apply the following rules
					From lines 1 to 10
						Get Company/Supplier name, Address, NIF
							if got NIF can get Original companyname
					From lines 11 to
			'''
			print ('-------')
			with open(lerpdfocr, "rb") as fileobj:
				filedata = fileobj.read()

			for row in csv.reader(ocr_pdf.ang_read_csv_content(filedata),delimiter=','):
				r = []
				for val in row:
					val = val.strip()
					#print (val)
					#print ("val", val.split(','))
					#print (len(val.split(',')))

					#Check if BAIDIRECTO
					if "através do serviço BAIDirecto" in val:
						bancoBAIDIRECTO = True

					if bancoBAIDIRECTO:
						if "Conta" in val:
							contaOrigem = val[val.find('Conta ')+6:].strip().replace(' ','')
						if "IBAN " in val:
							if not ibanOrigem:
								tmpiban = val[val.find('IBAN ')+5:].strip().replace(' ','').replace('—','')
								ibanOrigem = tmpiban.replace('AOO6','AO06')
						if "Nümero de operaçäo" in val or "Número de operaçäo" in val or "Número de Operação" in val:
							if not numeroOperacao:
								if "Nümero de operaçäo" in val:
									numeroOperacao = val[val.find('Nümero de operaçäo')+19:].strip()
								elif "Número de operaçäo" in val:
									numeroOperacao = val[val.find('Número de operaçäo')+19:].strip()
								elif "Número de Operação" in val:
									numeroOperacao = val[val.find('Número de Operação')+19:].strip()
						if "Montante Kz" in val:
							if not valorPAGO:
								valorPAGO = val[val.find('Montante Kz')+12:].strip().replace('"','')
						if "Referencia Pessoal" in val:
							if not descricaoPagamento:
								descricaoPagamento = val[val.find('Referencia Pessoal')+19:].strip()
						if "Data de Execução -" in val:
							if not dataEMISSAO:
								dataEMISSAO = val[val.find('Data de Execução -')+18:].strip().replace("'","")
					else:
						#Check IF Designaçäo: Conta BIC Empresas - Moeda Nacional
						#Check fo Conta de Origem:
						print (val)
						print ('Designação: Deposito a Ordem - Moeda Nacional')
						print ('Designação: Deposito a Ordem - Moeda Nacional' in val)
						if "Conta de Origem:" in val:
							contaOrigem = val[val.find('Conta de Origem:')+17:].strip().replace(' ','')
						if "Data do movimento" in val:
							dataEMISSAO = val[val.find('Data do movimento')+18:].strip()
						if "Designaçäo: Conta BIC Empresas - Moeda Nacional" in val or "Designação: Conta BIC Empresas - Moeda Nacional" in val or "Designação: Deposito a Ordem - Moeda Nacional" in val:
							#BANCO BIC TRANSFERENCIA
							bancoBic = True
						if "Número do documento" in val:
							numeroDocumento =  val[val.find('Número do documento')+20:].strip()
						if "Nümero de operaçäo" in val or "Número de operaçäo" in val:
							if not numeroOperacao:
								if "Nümero de operaçäo" in val:
									numeroOperacao = val[val.find('Nümero de operaçäo')+19:].strip()
								else:
									numeroOperacao = val[val.find('Número de operaçäo')+19:].strip()
						if "Descrição do movimento" in val or "Descriçäo do movimento" in val:
							if "Descriçäo do movimento" in val:
								descricaoPagamento = val[val.find('Descriçäo do movimento')+23:].strip()
							else:
								descricaoPagamento = val[val.find('Descrição do movimento')+23:].strip()

						if "Valor a debitar" in val:
							valorPAGO = val[val.find('Valor a debitar')+16:].strip()

						#FIX 25-09-2023
						if "IBAN " in val:
							if not ibanDestino:
								#if val[val.find('AO06')] != -1 or val[val.find('AOO6')] != -1 or val[val.find('AOC06')] != -1:
								if val.find('IBAN da conta a creditar') != -1:
									tmpiban = val[val.find('IBAN da conta a creditar')+25:].strip().replace(' ','').replace('—','')
								else:
									tmpiban = val[val.find('IBAN ')+5:].strip().replace(' ','').replace('—','')
								ibanDestino = tmpiban.replace('AOO6','AO06').replace('AOC06','AO06')



			stop_time = time.monotonic()
			print(round(stop_time-start_time, 2), "seconds")

			#Return values if
			if bancoBAIDIRECTO:
				if dataEMISSAO and contaOrigem and valorPAGO:
					return {
						"bancoBAIDIRECTO": bancoBAIDIRECTO,
						"numeroTransacao": numeroDocumento or numeroOperacao,
						"datadePAGAMENTO": dataEMISSAO,
						"contaOrigem": contaOrigem,
						"ibanOrigem": ibanOrigem,
						"ibanDestino": ibanDestino,
						"valorPAGO": valorPAGO
					}

			else:
				print ('dataEMISSAO ',dataEMISSAO)
				print ('contaOrigem ',contaOrigem  )
				print ('valorPAGO ',valorPAGO)
				if dataEMISSAO and contaOrigem and valorPAGO:
					return {
						"bancoBic": bancoBic,
						"numeroTransacao": numeroDocumento or numeroOperacao,
						"datadePAGAMENTO": dataEMISSAO,
						"contaOrigem": contaOrigem,
						"ibanDestino": ibanDestino,
						"valorPAGO": valorPAGO,
						"descricaoPagamento": descricaoPagamento
					}

		print ('TODO: Tenta ocr_pytesseract.... but reading all Lines and checking for the required fields...')
		#TODO:Tenta ocr_pytesseract.... but reading all Lines and checking for the required fields...
		#if tipodoctype != None and tipodoctype.upper() == "COMPRAS":
		#	print ('Tenta ocr_pytesseract.... but reading all Lines and checking for the required fields...')
		#	print (ocr_tesserac)
		#	frappe.throw(porra)

		return "403 Forbidden"	#Because if IMAGE.... FOR NOW 12-10-2022
		#frappe.throw(porra)

		print ('TERA DE FAZER O OCR......')
		print ('TERA DE FAZER O OCR......')
		print ('TERA DE FAZER O OCR......')
		return ocr_pdf.ocr_pdf(input_path=filefinal)

def lerdocumento(dados):
	print ('===== lerdocumento ======= ')
	print ('===== lerdocumento ======= ')
	print ('===== lerdocumento ======= ')

	start_time = time.monotonic()

	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'
	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

	contaOrigem = ''
	ibanDestino = ''
	numeroTransacao = ''
	dataEMISSAO = ''
	valorPAGO = ''
	mcexpress = False

	NIFContribuinte = ''

	datasubmissaoTEMP = ''

	if dados:
		print (dados.split('\n'))
		for aa in dados.split('\n'):
			#271462936
			print ('=======')
			print ('aa ', aa)
			if aa != "" and aa != None:
				print (re.match(cash_pattern,aa.strip()))
				print ('IBAN')
				print (re.match(iban_pattern,aa.strip()))

				#Cliente anexou Nossa Factura + Pagamento via ATM MULTICAIXA
				if (aa.find('TRANSACGAO: ') != -1 or aa.find('TRANSACGAD: ') != -1 or aa.find('TRANSACÇÃO: ') != -1) and aa.find('Exmo(s) Senhor(es)') != -1 :
					if aa.find('TRANSACGAO:') != -1:
						tmpnumeroTrans = aa[aa.find('TRANSACGAO:')+12:aa.find('Exmo(s) Senhor(es)')]
					elif aa.find('TRANSACGAD:') != -1:
						tmpnumeroTrans = aa[aa.find('TRANSACGAD:')+12:aa.find('Exmo(s) Senhor(es)')]
					elif aa.find('TRANSACÇÃO:') != -1:
						tmpnumeroTrans = aa[aa.find('TRANSACÇÃO:')+12:aa.find('Exmo(s) Senhor(es)')]

					print ('tmpnumeroTrans ',tmpnumeroTrans)
					numeroTransacao = tmpnumeroTrans
				elif aa.find('N.CATXA: ') != -1 and aa.find('TRANSACCAO: ') != -1:
					if numeroTransacao == '':
						tmpnumeroTrans = aa[aa.find('TRANSACCAO: ')+12:]
						print ('tmpnumeroTrans ',tmpnumeroTrans)
						numeroTransacao = tmpnumeroTrans

				elif aa.find('CONTA: ') != -1 or aa.find('CONTA : ') != -1:
					#assuming Conta and Date of payment...
					print (aa[aa.find('CONTA: ')+7:])
					tmpconta = aa.split(' ')[1] # aa[aa.find('CONTA: ')+7:]
					if contaOrigem == '':
						if len(tmpconta) == 15 and tmpconta.replace('OO','00').isnumeric():
							contaOrigem = tmpconta.replace('OO','00')
					print ('tmpconta ', tmpconta)
					if len(aa.split(' ')) == 4:
						dataEMISSAO = aa.split(' ')[2]
						print ('dataEMISSAO ', dataEMISSAO)
					if aa.find('CONTA : ') != -1:
						print ('Conta SPLIT')
						print (aa.split(' '))
						print (len(aa.split(' ')))
						print (contaOrigem)
						if len(aa.split(' ')) == 6 and contaOrigem == '':
							tmpconta = aa.split(' ')[2] + aa.split(' ')[3]
							contaOrigem = tmpconta[0:15]
							print ('contaOrigem ',contaOrigem)

							dataEMISSAO = aa.split(' ')[4]
							print ('dataEMISSAO ', dataEMISSAO)

				elif aa.find('TRANSFERENCIA BANCARTA') != -1 or aa.find('TRANSFERENCIA BANCARIA') != -1 or aa.find('TRANSFERÈNCIA BANCÁRIA') != -1 or aa.find('TRENSFERENCTA BANCARTA') != -1:
					mcexpress = True

				elif re.match(cash_pattern,aa.strip()):
					print ('PAGAMENTO....')
					print (re.match(cash_pattern,aa.strip()).string.replace('ka',''))
					if valorPAGO == '':
						valorPAGO1 = re.match(cash_pattern,aa.strip()).string
						print (valorPAGO1)
						print (valorPAGO1.split(' '))
						if len(valorPAGO1.split(' ')) >=2:
							valorPAGO = valorPAGO1.split(' ')[0]
						else:
							valorPAGO = valorPAGO1.replace(' Ka','')
						print ('valor Pago ', valorPAGO)
					#frappe.throw(porra)
				elif aa.startswith('AD06. 0606') or aa.startswith('AO06.0006'):
					tmpiban = aa.strip().replace('AD06. 0606','AO06.0006').replace(',','.').replace(' ','.')
					print ('tmpiban ',tmpiban)
					print (re.match(iban_pattern,tmpiban.strip()))
					if re.match(iban_pattern,tmpiban.strip()):
						ibanDestino = tmpiban.strip()
				elif re.match(iban_pattern,aa.strip()):
					print ('IBAN DESTINO....')
					frappe.throw(porra)

				# +++++  FIM Cliente anexou Nossa Factura + Pagamento via ATM MULTICAIXA

				if aa.find(' foi realizada Transferéncia Interna no BFA Net') != -1:
					#Get DATA EMISSAO
					print (aa)
					datatmp = aa[0:aa.find(' foi realizada Transferéncia Interna no BFA Net')]
					print ('datatmp ', datatmp)
					#TODO: Format DATA to YYYY-MM-DD

				if aa.find(', sobre a conta n° ') != -1:
					#IBAN Origem
					print (aa)
					tmpcontaOrigem = aa[aa.find(', sobre a conta n° ')+20:]
					tmpconta = tmpcontaOrigem[0:tmpcontaOrigem.find(', ')]
					print ('tmpconta ',tmpconta)
					contaOrigem = tmpconta

				if aa.find('REG') != -1 and len(aa) == 15:
					#Pode ser o Numero de Declaracao... if has 11 numbers
					print ('REGNumbers ', aa[3:len(aa)-1])
					referenciadocumento = aa.strip()
					temREG = True
				elif re.match(date_pattern,aa.strip()):
					if not datasubmissaoTEMP:
						datasubmissaoTEMP = aa.strip()
						print ('datasubmissaoTEMP ', datasubmissaoTEMP)
				elif len(aa.strip()) == 10:
					#Might be NIF
					if aa.strip().isnumeric() and not NIFContribuinte:
						NIFContribuinte = aa.strip()
						print ('NIFContribuinte ', NIFContribuinte)
		'''
		return {
			"mcexpress": mcexpress,
			"numeroTransacao": numeroTransacao,
			"datadePAGAMENTO": dataEMISSAO,
			"contaOrigem": contaOrigem,
			"ibanDestino": ibanDestino,
			"valorPAGO": valorPAGO
		}
		'''
		stop_time = time.monotonic()
		print(round(stop_time-start_time, 2), "seconds")

		return mcexpress,numeroTransacao,dataEMISSAO,contaOrigem,ibanDestino,valorPAGO


@frappe.whitelist(allow_guest=True)
def pdf_scrape_txt(ficheiro):
	'''
		Initially created to scrape item from Sales Invoice of a Supplier and create as Purchase Order or Invoice
		Format used is from TMJ for other suppliers might need some changes...
	'''

	ID_LEFT_BORDER = 40 #56
	ID_RIGHT_BORDER = 50 #156

	#AO Modelo Factura
	IDx_LEFT_BORDER = 48 #56
	IDx_RIGHT_BORDER = 54 #156

	DESC_LEFT_BORDER = 65 #69 #56
	DESC_RIGHT_BORDER = 80 #156

	#EN Invoices
	INVNUM_LEFT_BORDER = 210
	INVNUM_RIGHT_BORDER = 215

	#AO Modelo Factura
	INVNUMx_LEFT_BORDER = 497
	INVNUMx_RIGHT_BORDER = 499

	INVDATE_LEFT_BORDER = 310
	INVDATE_RIGHT_BORDER = 315

	QTY_LEFT_BORDER = 320
	QTY_RIGHT_BORDER = 350

	#AO MODELO FACTURA
	QTYx_LEFT_BORDER = 254 #256
	QTYx_RIGHT_BORDER = 261

	#FIX 30-07-203; Europe MODEL QUOTATION
	QTYy_LEFT_BORDER = 392
	QTYy_RIGHT_BORDER = 400

	RATE_LEFT_BORDER = 400
	RATE_RIGHT_BORDER = 450

	#AO Modelo Factura
	RATEx_LEFT_BORDER = 303 #305
	RATEx_RIGHT_BORDER = 318


	TOTAL_LEFT_BORDER = 449 #500
	TOTAL_RIGHT_BORDER = 550

	#AO Modelo Factura
	TOTALx_LEFT_BORDER = 449 #500
	TOTALx_RIGHT_BORDER = 510


	empresaSupplier = ""
	empresaSupplierEndereco = ""
	empresaSupplierNIF = ""
	empresaPais = ""

	invoicenumber = ""
	invoicedate = ""
	moedainvoice = ""

	# Read PDF file and convert it to HTML
	output = StringIO()
	#with open('/tmp/SINV-2022-00021-1.pdf', 'rb') as pdf_file:
	with open(ficheiro, 'rb') as pdf_file:
		extract_text_to_fp(pdf_file, output, laparams=LAParams(), output_type='html', codec=None)
	raw_html = output.getvalue()
	# Extract all DIV tags
	tree = html.fromstring(raw_html)
	divs = tree.xpath('.//div')
	# Sort and filter DIV tags
	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': []}
	filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}
	temitems = False

	contador = 1

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|^([0-9][0-9])\-([0-9][0-9])\-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'
	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

	oldIDXDescription = 0;

	ultimo_header = ['TOTAL PRICE']
	ultimoheader = False
	ultimacoluna = False

	dataproforma = False

	for div in divs:
		# extract styles from a tag
		div_style = div.get('style')
		print ('+++++++++')
		print(div_style)
		print (div.text_content().strip('\n').upper())

		#if div.text_content().strip('\n').upper().endswith('AOA'):
		if div.text_content().strip('\n').upper().endswith('AOA'):
			print ('contador ', contador)
			print(div_style)
			print (div.text_content().strip('\n').upper())
			print ('rate_LEFT_BORDER ',TOTAL_LEFT_BORDER)
			print ('ratex_LEFT_BORDER ',TOTALx_LEFT_BORDER)
			contador +=1

		# position:absolute; border: textbox 1px solid; writing-mode:lr-tb; left:292px; top:1157px; width:27px; height:12px;
		# get left position
		try:
			left = re.findall(r'left:([0-9]+)px', div_style)[0]
		except IndexError:
			continue

		if INVNUM_LEFT_BORDER < int(left) < INVNUM_RIGHT_BORDER:
			#Invoice Number
			#print (div.text_content().strip('\n').upper())
			if 'INVOICE NO:' in div.text_content().strip('\n').upper():
				#print (div.text_content().split('\n'))
				tmpinv = div.text_content().strip('\n').upper()
				invoicenumber = tmpinv[tmpinv.find('INVOICE NO:')+12:]
				#print ('invoicenumber ',invoicenumber)
		elif INVNUMx_LEFT_BORDER < int(left) < INVNUMx_RIGHT_BORDER:
			#AO Modelo Factura
			if div.text_content().strip('\n') != '':
				#Check if starts with FT
				if div.text_content().strip('\n').startswith('FT'):
					tmpinv = div.text_content().strip('\n').upper()
					invoicenumber = tmpinv



		if INVDATE_LEFT_BORDER < int(left) < INVDATE_RIGHT_BORDER:
			#Invoice DATE
			#print (div.text_content().strip('\n').upper())
			if 'DATE' in div.text_content().strip('\n').upper():
				#print (div.text_content().split('\n'))
				tmpinv = div.text_content().split('\n')[1]
				invoicedate = tmpinv
				#print ('invoicedate ',invoicedate)

		# div contains ID if div's left position between ID_LEFT_BORDER and ID_RIGHT_BORDER
		#print (div.text_content().strip('\n').upper())
		if div.text_content().strip('\n') != '':
			print ('ID_LEFT_BORDER ',ID_LEFT_BORDER)
			print ('temitems ',temitems)
			print ('div.text_content()')
			print (div.text_content())
			print ('left ', left)

			if ID_LEFT_BORDER < int(left) < ID_RIGHT_BORDER:
				if div.text_content().strip('\n') == 'ITEM':
					temitems = True
				elif 'AMOUNT IN WORDS' in div.text_content().strip('\n').upper():
					temitems = False
				if temitems and div.text_content().strip('\n') != 'ITEM'  and 'CONSIGNEE NAME:' not in div.text_content().strip('\n').upper(): # and div.text_content().strip('\n') != '':
					if div.text_content().strip('\n').isnumeric():
						filtered_divs['ITEM'].append(div.text_content().strip('\n'))

				elif 'THANK YOU FOR YOUR BUSINESS' in div.text_content().strip('\n').upper():
					#For this specific case Company name is after Thank you for you...
					#print ('Get Empresa/Supplier...')
					#print (div.text_content().split('\n')[1].strip('\n').upper())
					empresaSupplier = div.text_content().split('\n')[1].strip('\n').upper()
					#print (empresaSupplier)
				elif ', LDA' in div.text_content().strip('\n').upper() or ',LDA' in div.text_content().strip('\n').upper():
					#Pode ser o Forneceodr/EMPRESA
					#print ('Pode ser o Forneceodr/EMPRESA')
					#print ('Get Empresa/Supplier...')
					#print (div.text_content().strip('\n').upper())
					empresaSupplier = div.text_content().strip('\n').upper()
					#print (empresaSupplier)
				elif div.text_content().strip('\n').upper().startswith('RUA'):
					empresaSupplierEndereco = div.text_content().strip('\n').upper()
				elif div.text_content().strip('\n').upper().startswith('NIF'):
					print ('Get Empresa/Supplier NIF...')
					print (div.text_content().strip('\n').upper())
					print (div.text_content().split())
					print (div.text_content().split()[1])
					print ('len ', len(div.text_content().split()))
					if len(div.text_content().split()) == 2:
						empresaSupplierNIF = div.text_content().split()[1].strip().upper()
						print ('empresaSupplierNIF ', empresaSupplierNIF)
					else:
						print (div.text_content().split(' ')[1].strip('\n').upper())
						empresaSupplierNIF = div.text_content().split(' ')[1].strip('\n').upper()
				elif 'DATA:' in div.text_content().strip('\n').upper():
					#print (div.text_content().split('\n'))
					tmpinv = div.text_content().split(' ')[1]
					invoicedate = tmpinv
				elif ('LUANDA' in div.text_content().strip('\n').upper() or 'ANGOLA' in div.text_content().strip('\n').upper()) and 'CONSIGNEE NAME:' not in div.text_content().strip('\n').upper():
					empresaPais = 'Angola'

			if 'QUOTATION #' in div.text_content().strip('\n').upper():
				#FIX 28-07-2023
				if not invoicenumber:
					invoicenumber = div.text_content().strip('\n').upper().replace('QUOTATION #','').strip()

			#print ('IDx_LEFT_BORDER ',IDx_LEFT_BORDER)
			#print ('IDx_RIGHT_BORDER ',IDx_RIGHT_BORDER)
			#print ('left ', int(left))
			#print (IDx_LEFT_BORDER < int(left) < IDx_RIGHT_BORDER)

			if IDx_LEFT_BORDER < int(left) < IDx_RIGHT_BORDER:
				#AO Modelo Factura
				if div.text_content().strip('\n').isnumeric():
					filtered_divs['ITEM'].append(div.text_content().strip('\n'))


			if DESC_LEFT_BORDER < int(left) < DESC_RIGHT_BORDER:
				#print ('descricao...')
				#print (div.text_content().strip('\n').upper())
				filtered_divs['DESCRIPTION'].append(div.text_content().strip('\n'))

			if QTY_LEFT_BORDER < int(left) < QTY_RIGHT_BORDER:
				#print ('QTY...')
				#print (div.text_content().strip('\n').upper())
				if div.text_content().strip('\n').isnumeric():
					filtered_divs['QUANTITY'].append(div.text_content().strip('\n'))
			elif QTYx_LEFT_BORDER < int(left) < QTYx_RIGHT_BORDER:
				#print ('QTY...')
				#print (div.text_content().strip('\n').upper())
				if div.text_content().strip('\n').upper().endswith('UNIDADE') or div.text_content().strip('\n').upper().endswith('UNIT'):
					if div.text_content().split(' ')[0].strip('\n').isnumeric():
						filtered_divs['QUANTITY'].append(div.text_content().split(' ')[0].strip('\n'))
			elif QTYy_LEFT_BORDER < int(left) < QTYy_RIGHT_BORDER:
				#FIX 30-07-2023
				print ('QTDYYYYYYY ')
				if div.text_content().strip('\n').isnumeric():
					filtered_divs['QUANTITY'].append(div.text_content().strip('\n'))
				elif div.text_content().strip('\n').replace('.00','').isnumeric():
					filtered_divs['QUANTITY'].append(div.text_content().strip('\n').replace('.00',''))

			if RATE_LEFT_BORDER < int(left) < RATE_RIGHT_BORDER:
				#print ('RATE...')
				#print (div.text_content().strip('\n').upper())
				#print ('TRANSPORTED VALUE' not in div.text_content().strip('\n'))
				if 'TRANSPORTED VALUE' not in div.text_content().strip('\n').upper() and 'TRANSPORTING VALUE' not in div.text_content().strip('\n').upper():
					print ('preco ',div.text_content().strip('\n'))
					print (div.text_content().strip('\n').isnumeric())
					print (re.match(cash_pattern,div.text_content().strip('\n').replace(',','')))

					if div.text_content().strip('\n').isnumeric():
						filtered_divs['RATE'].append(div.text_content().strip('\n'))
					elif re.match(cash_pattern,div.text_content().strip('\n').replace(',','')):
						#FIX 30-07-2023 added .replace(',','')
						filtered_divs['RATE'].append(div.text_content().strip('\n').replace(',',''))

				elif 'TRANSPORTING VALUE' in div.text_content().strip('\n').upper():
					#Get the Currency of the PDF....
					if not moedainvoice:
						#Check if has $ €
						if "€" in div.text_content().strip('\n'):
							moedainvoice = "Eur"
						elif "$" in div.text_content().strip('\n'):
							moedainvoice = "Usd"

						#print (div.text_content().strip('\n').upper())
						#moedainvoice = div.text_content().strip('\n').upper()
						#print (moedainvoice)
						#frappe.throw(porra)
			if RATEx_LEFT_BORDER < int(left) < RATEx_RIGHT_BORDER:
				#AO Modelo Factura
				if div.text_content().strip('\n').upper().startswith('AOA'):
					tmprate = div.text_content().split(' ')[1]
					filtered_divs['RATE'].append(tmprate)
					#print ('NAO ADDED RATEX ',div.text_content().strip('\n'))
					#print (tmprate)

				if not moedainvoice:
					#Check if has $ €
					if "€" in div.text_content().strip('\n'):
						moedainvoice = "Eur"
					elif "$" in div.text_content().strip('\n'):
						moedainvoice = "Usd"
					elif "AOA" in div.text_content().strip('\n') or "KZ" in div.text_content().strip('\n'):
						moedainvoice = "AOA"


			if TOTAL_LEFT_BORDER < int(left) < TOTAL_RIGHT_BORDER:
				#print ('TOTAL...')
				#print (div.text_content().strip('\n').upper())
				if "14.0%" not in div.text_content().strip('\n'):
					print (div.text_content().strip('\n').isnumeric())
					print (re.match(cash_pattern,div.text_content().strip('\n').replace(',','')))

					if div.text_content().strip('\n').isnumeric():
						filtered_divs['TOTAL'].append(div.text_content().strip('\n'))
						print ('AQUI AQUI ', div.text_content().strip('\n'))
					elif div.text_content().strip('\n').upper().endswith('AOA'):
						tmptotal = div.text_content().split(' ')[0]
						print ('total ', re.match(cash_pattern,tmptotal.replace(',','')))
						if re.match(cash_pattern,tmptotal.replace(',','')):
							filtered_divs['TOTAL'].append(tmptotal)

						#print ('TOTAL TOTAL ', div.text_content().strip('\n'))
						#print (tmptotal)
					elif re.match(cash_pattern,div.text_content().strip('\n').replace(',','')):
						#FIX 30-07-2023; check if 5% and $
						if "5%" in div.text_content().strip('\n') and "$" in div.text_content().strip('\n'):
							print ('TEM IVA ', div.text_content().strip('\n')[:div.text_content().strip('\n').find('5% ')+2])
							filtered_divs['IVA'].append(div.text_content().strip('\n')[:div.text_content().strip('\n').find('5% ')+2])
							filtered_divs['TOTAL'].append(div.text_content().strip('\n').replace('5%','').replace('$','').replace(',','').strip())
							ultimacoluna = True
						else:
							filtered_divs['TOTAL'].append(div.text_content().strip('\n'))
						print ('AQUI1 AQUI1 X ', div.text_content().strip('\n'))


					#Check if has $ €
					if "€" in div.text_content().strip('\n'):
						moedainvoice = "Eur"
					elif "$" in div.text_content().strip('\n'):
						moedainvoice = "Usd"

				#if "149,719.53 AOA" in div.text_content().strip('\n'):
				#	frappe.throw(porra)
			if empresaSupplier == "":
				if "PAGE" not in div.text_content().strip('\n').upper():
					empresaSupplier = div.text_content().strip('\n').upper()

			if "INVOICE DATE:" in div.text_content().strip('\n').upper():
				if invoicedate == "":
					print('INVOICE DATE:')
					print (div.text_content().upper())
					print (div.text_content().upper().split('\n'))
					for ii in div.text_content().upper().split('\n'):
						print (ii)
						print (len(ii))
						if "INVOICE DATE:" in ii.upper():
							if len(ii) > 13:
								invoicedate = ii[ii.find('INVOICE DATE:')+13:].strip()
						if "INVOICE NO:" in ii.upper():
							if len(ii) > 11:
								invoicenumber = ii[ii.find('INVOICE NO:')+11:].strip()

			if "P.O BOX:" in div.text_content().strip('\n').upper():
				#Address Supplier
				if empresaSupplierEndereco == "":
					empresaSupplierEndereco = div.text_content().strip('\n').upper()

			if "SL" in div.text_content().strip('\n').upper():
				#Some Suppliers; Order Number
				print ('TEM SL')
				print (div.text_content().strip('\n'))
				if 85 < int(left) < 87:
					#Check if has split
					print (div.text_content().split('\n'))
					print (len(div.text_content().split('\n')))
					if div.text_content().split('\n')[1].isnumeric():
						filtered_divs['ITEM'].append(div.text_content().split('\n')[1])
					#temitems = True
			if "DESCRIPTION" in div.text_content().strip('\n').upper():
				#Supplier Description + Item name + Serial Number if has...
				print ('000 TEM Description + Item name + Serial Number if has')
				print (div.text_content().strip('\n'))
				if 100 < int(left) < 102:
					#Check if has split
					print (div.text_content().split('\n'))
					print (len(div.text_content().split('\n')))
					print ('STILL NEED TO CHECK IF MORE THAN 1 SERIAL NUMBER...')
					if len(div.text_content().split('\n')) >= 3:
						if div.text_content().split('\n')[2] != "":
							filtered_divs['DESCRIPTION'].append(div.text_content().split('\n')[1] + " SN: " + div.text_content().split('\n')[2])
						else:
							filtered_divs['DESCRIPTION'].append(div.text_content().split('\n')[1])
						oldIDXDescription = len(filtered_divs['DESCRIPTION'])
			if temitems == False and div.text_content().strip('\n')[:2].strip().isdigit():
				#Starts with a Number... might be OrderNumber + Item Description
				if 86 < int(left) < 88:
					print (div.text_content().split('\n'))
					print (div.text_content()[:div.text_content().find(' ')].strip())
					print (div.text_content()[div.text_content().find(' '):].strip())

					filtered_divs['ITEM'].append(div.text_content()[:div.text_content().find(' ')].strip())
					filtered_divs['DESCRIPTION'].append(div.text_content()[div.text_content().find(' '):].strip())
					print (len(filtered_divs['DESCRIPTION']))
					oldIDXDescription = len(filtered_divs['DESCRIPTION'])
					#frappe.throw(porra)


			if "Y/M COLOR" in div.text_content().strip('\n').upper():
				#print ('TO DO LATER')
				#will or might contain Y COLOR and FUEL: 2022 black Petrol
				print (div.text_content().split('\n'))
				if filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:') == -1:
					#Append at the end
					filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + ' ' + div.text_content().split('\n')[1]
				else:
					print (filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:'))
					print (filtered_divs['DESCRIPTION'][oldIDXDescription-1][:filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:')])
					tmpdesc = filtered_divs['DESCRIPTION'][oldIDXDescription-1]
					filtered_divs['DESCRIPTION'][oldIDXDescription-1] = tmpdesc.replace('SN:', div.text_content().split('\n')[1] + ' SN:')
					#print (filtered_divs['DESCRIPTION'])


			if "FUEL QTY" in div.text_content().strip('\n').upper():
				print ('GET QTY FUEL WILL BE LATER...')
				print (div.text_content().split('\n'))
				#frappe.throw(porra)


			if 360 < int(left) < 362:
				#Qty Column
				print ('Qty Column')
				if div.text_content().strip('\n').isnumeric():
					filtered_divs['QUANTITY'].append(div.text_content().strip('\n'))

			if 394 < int(left) < 396:
				#RATE Column
				print ('RATE Column')
				print (div.text_content())
				print (div.text_content().strip('\n'))
				print ('REMOVED FOR NOW...GIVING ERRROR')
				if len(div.text_content().split('\n')) >= 2:
					#if re.match(cash_pattern,div.text_content().strip('\n').replace(',','')) != None:
					t = div.text_content().strip('\n')[1].replace(',','')
					if re.match(cash_pattern,t) != None:
						filtered_divs['RATE'].append(t)

			if 469 < int(left) < 471:
				#TOTAL Column
				print ('TOTAL Column ERRRRRRRRRR')
				print (div.text_content().split('\n'))
				if "TOTAL" in div.text_content().strip('\n'):
					print (len(div.text_content().split('\n')))
					if len(div.text_content().split('\n')) >= 2:
						print (div.text_content().split('\n')[1])
						print (re.match(cash_pattern,div.text_content().split('\n')[1].replace(',','')))
						if re.match(cash_pattern,div.text_content().split('\n')[1].replace(',','')):
							filtered_divs['TOTAL'].append(div.text_content().split('\n')[1])
			if 100 < int(left) < 102:
				#Serial Numbers....
				#JTGCBAB8906725029
				print ('Serial Numbers.... ')
				print (div.text_content().strip('\n').replace(' ',''))
				print (len(div.text_content().strip('\n').replace(' ','')))
				if len(div.text_content().strip('\n')) >= 17:
					if div.text_content().strip('\n').find(' ') == -1:
						print ('PODE SER Serial Numbers.... ')
						print (oldIDXDescription)
						print (filtered_divs['DESCRIPTION'][oldIDXDescription-1])
						if filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:') == -1:
							filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + " SN: " + div.text_content().strip('\n')
						else:
							filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + div.text_content().strip('\n')

						print ('ADDICIONOU SERIAL ')
						print (filtered_divs['DESCRIPTION'][oldIDXDescription-1])

			if 252 < int(left) < 254:
				#will or might contain Y COLOR and FUEL: 2022 black Petrol
				print (div.text_content().split('\n'))
				print (div.text_content().strip('\n'))
				#check if starts with 4 digits for YEAR
				if div.text_content().strip('\n')[:5].strip().isdigit():
					print ('oldIDXDescription ',oldIDXDescription)
					if oldIDXDescription >= 1:
						if filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:') == -1:
							#Append at the end
							filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + ' ' + div.text_content().strip('\n')
						else:
							print (filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:'))
							print (filtered_divs['DESCRIPTION'][oldIDXDescription-1][:filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:')])
							tmpdesc = filtered_divs['DESCRIPTION'][oldIDXDescription-1]
							filtered_divs['DESCRIPTION'][oldIDXDescription-1] = tmpdesc.replace('SN:', div.text_content().strip('\n') + ' SN:')
							#print (filtered_divs['DESCRIPTION'])


			if "AED" in div.text_content().strip('\n'):
				if moedainvoice == "":
					moedainvoice = "AED"

				#if "149,719.53 AOA" in div.text_content().strip('\n'):
				#	frappe.throw(porra)

			print ('TESTE')
			print (ultimo_header[0] in div.text_content().strip('\n'))
			print (ultimo_header[0])
			print (div.text_content().strip('\n'))
			if ultimo_header[0] in div.text_content().strip('\n').upper():
				#FIX 30-07-2023
				ultimoheader = True
				temitems = True
			if int(left) == 32 and temitems and ultimoheader:
				#FIX 30-07-2023
				print ('FIX 30-07-2023')
				if ultimacoluna and len(div.text_content().strip('\n')) <= 18:
					print ('Add REST of DESCRIPTION to Previous.....')
					ultimacoluna = False
					tmpdesc = filtered_divs['DESCRIPTION'][oldIDXDescription-1]
					filtered_divs['DESCRIPTION'][oldIDXDescription-1] = tmpdesc + " " + div.text_content().strip('\n')
					filtered_divs['ITEM'][oldIDXDescription-1] = tmpdesc + " " + div.text_content().strip('\n')


				else:
					filtered_divs['ITEM'].append(div.text_content().strip('\n'))  #append(div.text_content()[:div.text_content().find(' ')].strip())
					filtered_divs['DESCRIPTION'].append(div.text_content().strip('\n'))  #append(div.text_content()[div.text_content().find(' '):].strip())
					print (len(filtered_divs['DESCRIPTION']))
					oldIDXDescription = len(filtered_divs['DESCRIPTION'])
			elif "UNIT" in div.text_content().strip('\n').upper() and ultimacoluna:
				print ('SET FALSE ULTIMA COLUNA')
				ultimacoluna = False

			elif int(left) == 379 and "UNITS" in div.text_content().strip('\n').upper() and not ultimacoluna:
				#FIX 30-07-2023; Special case... bcs it has Qtd units and Price
				print ('tamanho ', len(div.text_content().strip('\n').split()))
				if len(div.text_content().strip('\n').split()) == 3:
					print ('QTD ', div.text_content().strip('\n').split()[0].replace('.00','').strip())
					filtered_divs['QUANTITY'].append(div.text_content().strip('\n').split()[0].replace('.00','').strip())
					filtered_divs['RATE'].append(div.text_content().strip('\n').split()[2].replace(',',''))
			elif "QUOTATION DATE:" in  div.text_content().strip('\n').upper():
				dataproforma = True
			elif dataproforma:
				#Assuming next is DATE FORMAT...
				invoicedate = div.text_content().strip('\n').upper()
				dataproforma = False


	# Merge and clear lists with data
	print ('ITEMs')
	print (filtered_divs['ITEM'])
	print (len(filtered_divs['ITEM']))

	print ('DESCRIPTIONs')
	print (filtered_divs['DESCRIPTION'])
	print (len(filtered_divs['DESCRIPTION']))
	print ('QUANTITY')
	print (filtered_divs['QUANTITY'])
	print (len(filtered_divs['QUANTITY']))
	print ('RATE')
	print (filtered_divs['RATE'])
	print (len(filtered_divs['RATE']))
	print ('TOTAL')
	print (filtered_divs['TOTAL'])
	print (len(filtered_divs['TOTAL']))

	data = []
	if filtered_divs['IVA']:
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['IVA']):
			if 'ITEM' in row[0]:
				continue
			#data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4]}
			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5]}
			data.append(data_row)
	else:
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL']):
			if 'ITEM' in row[0]:
				continue

			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4]}
			#data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5]}
			data.append(data_row)


	print('Supplier ', empresaSupplier)
	print ('supplieraddre ', empresaSupplierEndereco)
	print ('supplierNIF ', empresaSupplierNIF)
	print ('supplierPais ', empresaPais)

	print('Invoice', invoicenumber)
	print('Date ', invoicedate)
	print('Moeda ', moedainvoice)


	pprint(data)

	return (empresaSupplier,invoicenumber,invoicedate,moedainvoice,empresaSupplierEndereco,empresaSupplierNIF,empresaPais,data)

@frappe.whitelist(allow_guest=True)
def pdf_scrape_txt_v1(ficheiro,tipodoctype = None):
	'''
		Modified 23-12-2022
		Initially created to scrape item from Sales Invoice of a Supplier and create as Purchase Order or Invoice
		Format used is from TMJ for other suppliers might need some changes...
	'''
	start_time = time.monotonic()

	ID_LEFT_BORDER = 40 #56
	ID_RIGHT_BORDER = 50 #156

	#AO Modelo Factura
	IDx_LEFT_BORDER = 48 #56
	IDx_RIGHT_BORDER = 54 #156

	DESC_LEFT_BORDER = 65 #69 #56
	DESC_RIGHT_BORDER = 80 #156

	#EN Invoices
	INVNUM_LEFT_BORDER = 210
	INVNUM_RIGHT_BORDER = 215

	#AO Modelo Factura
	INVNUMx_LEFT_BORDER = 497
	INVNUMx_RIGHT_BORDER = 499

	INVDATE_LEFT_BORDER = 310
	INVDATE_RIGHT_BORDER = 315

	QTY_LEFT_BORDER = 320
	QTY_RIGHT_BORDER = 350

	#AO MODELO FACTURA
	QTYx_LEFT_BORDER = 254 #256
	QTYx_RIGHT_BORDER = 261


	RATE_LEFT_BORDER = 400
	RATE_RIGHT_BORDER = 450

	#AO Modelo Factura
	RATEx_LEFT_BORDER = 303 #305
	RATEx_RIGHT_BORDER = 318


	TOTAL_LEFT_BORDER = 449 #500
	TOTAL_RIGHT_BORDER = 550

	#AO Modelo Factura
	TOTALx_LEFT_BORDER = 449 #500
	TOTALx_RIGHT_BORDER = 510


	empresaSupplier = ""
	empresaSupplierEndereco = ""
	empresaSupplierNIF = ""
	empresaPais = ""

	invoicenumber = ""
	invoicedate = ""
	moedainvoice = ""

	# Read PDF file and convert it to HTML
	output = StringIO()
	#with open('/tmp/SINV-2022-00021-1.pdf', 'rb') as pdf_file:
	with open(ficheiro, 'rb') as pdf_file:
		extract_text_to_fp(pdf_file, output, laparams=LAParams(), output_type='html', codec=None)
	raw_html = output.getvalue()
	# Extract all DIV tags
	tree = html.fromstring(raw_html)

	#TESTING
	print (raw_html)
	print ('\\\\\\\\\\\\\\\\')
	print ('\\\\\\\\\\\\\\\\')
	#frappe.throw(porra)

	divs = tree.xpath('.//div')
	# Sort and filter DIV tags
	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': []}
	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}

	filtered_divs = {'COUNTER': [], 'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}
	temitems = False

	contador = 1

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|^([0-9][0-9])\-([0-9][0-9])\-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'
	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

	oldIDXDescription = 0;

	master_headers = ['ITEM','CODE','DESCRIPTION','QUANTITY','UNIT PRICE (EUR)','TOTAL PRICE (EUR)']
	headers_no_file = []
	conta_headers_no_file = 0
	fim_headers_no_file = False

	#to reset...
	oldquantity = 0
	oldrate = 0
	oldtotal = 0

	for div in divs:

		# extract styles from a tag
		div_style = div.get('style')
		print ('+++++++++')
		print(div_style)
		print (div.text_content().strip('\n').upper())

		#Find headers...
		if div.text_content().strip('\n').upper() in master_headers:
			if div.text_content().strip('\n').upper() not in headers_no_file:
				headers_no_file.append(div.text_content().strip('\n').upper())
				conta_headers_no_file += 1
				if div.text_content().strip('\n').upper() == "TOTAL PRICE" or div.text_content().strip('\n').upper() == "TOTAL":
					fim_headers_no_file = True

		#if div.text_content().strip('\n').upper().endswith('AOA'):
		if div.text_content().strip('\n').upper().endswith('AOA'):
			print ('contador ', contador)
			print(div_style)
			print (div.text_content().strip('\n').upper())
			print ('rate_LEFT_BORDER ',TOTAL_LEFT_BORDER)
			print ('ratex_LEFT_BORDER ',TOTALx_LEFT_BORDER)
			contador +=1

		# position:absolute; border: textbox 1px solid; writing-mode:lr-tb; left:292px; top:1157px; width:27px; height:12px;
		# get left position
		try:
			left = re.findall(r'left:([0-9]+)px', div_style)[0]
		except IndexError:
			continue

		if INVNUM_LEFT_BORDER < int(left) < INVNUM_RIGHT_BORDER:
			#Invoice Number
			#print (div.text_content().strip('\n').upper())
			if 'INVOICE NO:' in div.text_content().strip('\n').upper():
				#print (div.text_content().split('\n'))
				tmpinv = div.text_content().strip('\n').upper()
				invoicenumber = tmpinv[tmpinv.find('INVOICE NO:')+12:]
				#print ('invoicenumber ',invoicenumber)
		elif INVNUMx_LEFT_BORDER < int(left) < INVNUMx_RIGHT_BORDER:
			#AO Modelo Factura
			if div.text_content().strip('\n') != '':
				#Check if starts with FT
				if div.text_content().strip('\n').startswith('FT'):
					tmpinv = div.text_content().strip('\n').upper()
					invoicenumber = tmpinv



		if INVDATE_LEFT_BORDER < int(left) < INVDATE_RIGHT_BORDER:
			#Invoice DATE
			#print (div.text_content().strip('\n').upper())
			if 'DATE' in div.text_content().strip('\n').upper():
				#print (div.text_content().split('\n'))
				tmpinv = div.text_content().split('\n')[1]
				invoicedate = tmpinv
				#print ('invoicedate ',invoicedate)

		# div contains ID if div's left position between ID_LEFT_BORDER and ID_RIGHT_BORDER
		#print (div.text_content().strip('\n').upper())
		if div.text_content().strip('\n') != '':
			print ('ID_LEFT_BORDER ',ID_LEFT_BORDER)
			print ('temitems ',temitems)
			print ('headers_no_file ',headers_no_file)
			print ('left ',left)
			print ('ID_RIGHT_BORDER ',ID_RIGHT_BORDER)

			if ID_LEFT_BORDER < int(left) < ID_RIGHT_BORDER or "CODE" in headers_no_file:
				if div.text_content().strip('\n') == 'ITEM':
					temitems = True
				elif 'AMOUNT IN WORDS' in div.text_content().strip('\n').upper():
					temitems = False
				if temitems and div.text_content().strip('\n') != 'ITEM'  and 'CONSIGNEE NAME:' not in div.text_content().strip('\n').upper(): # and div.text_content().strip('\n') != '':
					print ('Numero ', div.text_content().strip('\n').isnumeric())
					if "CODE" in headers_no_file:
						#Might be same line ITEM and ITEMCODE
						print (div.text_content().strip().split())
						print (len(div.text_content().strip().split()))
						if len(div.text_content().strip().split()) == 2:
							if div.text_content().strip().split()[0].isnumeric():
								filtered_divs['COUNTER'].append(div.text_content().strip().split()[0])
								filtered_divs['ITEM'].append(div.text_content().strip().split()[1])

								#print ('Counter and ITEM')
								#print (filtered_divs['COUNTER'])
								#print (filtered_divs['ITEM'])

						elif len(div.text_content().strip().split()) == 3:
							#assuming numbers separated by space like Qtd Price Total
							print ('AQUI')
							print ('numer ', div.text_content().strip().split()[0].isnumeric())
							print ('numer1 ', div.text_content().strip().split()[1].isnumeric())
							print ('numer2 ', div.text_content().strip().split()[2].isnumeric())

							#Can be Counter, CODE and CODE or QTD, RATE, TOTAL
							if div.text_content().strip().split()[0].isnumeric() and re.match(cash_pattern,div.text_content().strip().split()[1].replace(',','')) and re.match(cash_pattern,div.text_content().strip().split()[2].replace(',','')):
								print ('AQUI FAZ NADA!!!!')
							elif div.text_content().strip().split()[0].isnumeric() and not div.text_content().strip().split()[1].isnumeric() and not div.text_content().strip().split()[2].isnumeric():
								filtered_divs['COUNTER'].append(div.text_content().strip().split()[0])
								filtered_divs['ITEM'].append(div.text_content().strip().split()[1] + ' ' + div.text_content().strip().split()[2])

							elif div.text_content().strip().split()[0].isnumeric() and not div.text_content().strip().split()[1] and div.text_content().strip().split()[2]:
								filtered_divs['COUNTER'].append(div.text_content().strip().split()[0])
								filtered_divs['ITEM'].append(div.text_content().strip().split()[1] + ' ' + div.text_content().strip().split()[2])


						elif len(div.text_content().strip().split()) == 4:
							#assuming numbers separated by space like Qtd Price Total
							print ('OU AQUI')
							print ('numer ', div.text_content().strip().split()[0].isnumeric())
							print ('numer1 ', div.text_content().strip().split()[1].isnumeric())
							print ('numer2 ', div.text_content().strip().split()[2].isnumeric())
							print ('numer3 ', div.text_content().strip().split()[3].isnumeric())

							#Can be Counter, CODE and CODE
							if div.text_content().strip().split()[0].isnumeric() and not div.text_content().strip().split()[1].isnumeric() and div.text_content().strip().split()[2].isnumeric() and not div.text_content().strip().split()[3].isnumeric():
								filtered_divs['COUNTER'].append(div.text_content().strip().split()[0])
								filtered_divs['ITEM'].append(div.text_content().strip().split()[1] + ' ' + div.text_content().strip().split()[2] + ' ' + div.text_content().strip().split()[3])

						elif len(div.text_content().strip().split()) == 1:
							#Single Number... can be Counter or ITEMCODE
							if div.text_content().strip('\n').isnumeric() and len(div.text_content().strip('\n')) <= 3:
								filtered_divs['COUNTER'].append(div.text_content().strip('\n'))
							elif len(div.text_content().strip('\n')) > 3:
								#Assuming itemCODE
								if div.text_content().strip('\n').upper() not in headers_no_file and not re.match(cash_pattern,div.text_content().strip('\n').replace(',','')) and div.text_content().strip('\n').upper() not in ["INCIDENCE"]:
									podeadicionar = True
									for fff in headers_no_file:
										print ('fff  ', fff)
										print (div.text_content().strip('\n').upper())
										print (fff.find(div.text_content().strip('\n').upper()))
										if fff.find(div.text_content().strip('\n').upper()) != -1:
											podeadicionar = False
											break
									if podeadicionar:
										filtered_divs['ITEM'].append(div.text_content().strip('\n'))
									print (div.text_content().strip('\n').upper())
									#print (headers_no_file)
									#print (div.text_content().strip('\n').upper() not in headers_no_file)
									#print (div.text_content().strip('\n'))
									#if "TOTAL" not in div.text_content().strip('\n').upper():
									#	frappe.throw(porra)
									#if podeadicionar or "3,000.00" in div.text_content().strip('\n').upper():
									#	frappe.throw(porra)

					elif div.text_content().strip('\n').isnumeric():
						filtered_divs['ITEM'].append(div.text_content().strip('\n'))


				elif 'THANK YOU FOR YOUR BUSINESS' in div.text_content().strip('\n').upper():
					#For this specific case Company name is after Thank you for you...
					#print ('Get Empresa/Supplier...')
					#print (div.text_content().split('\n')[1].strip('\n').upper())
					empresaSupplier = div.text_content().split('\n')[1].strip('\n').upper()
					#print (empresaSupplier)
				elif ', LDA' in div.text_content().strip('\n').upper() or ',LDA' in div.text_content().strip('\n').upper():
					#Pode ser o Forneceodr/EMPRESA
					#print ('Pode ser o Forneceodr/EMPRESA')
					#print ('Get Empresa/Supplier...')
					#print (div.text_content().strip('\n').upper())
					empresaSupplier = div.text_content().strip('\n').upper()
					#print (empresaSupplier)
				elif div.text_content().strip('\n').upper().startswith('RUA'):
					empresaSupplierEndereco = div.text_content().strip('\n').upper()
				elif div.text_content().strip('\n').upper().startswith('NIF'):
					#print ('Get Empresa/Supplier NIF...')
					#print (div.text_content().split(' ')[1].strip('\n').upper())
					empresaSupplierNIF = div.text_content().split(' ')[1].strip('\n').upper()
				elif 'DATA:' in div.text_content().strip('\n').upper():
					#print (div.text_content().split('\n'))
					tmpinv = div.text_content().split(' ')[1]
					invoicedate = tmpinv
				elif ('LUANDA' in div.text_content().strip('\n').upper() or 'ANGOLA' in div.text_content().strip('\n').upper()) and 'CONSIGNEE NAME:' not in div.text_content().strip('\n').upper():
					empresaPais = 'Angola'

			#print ('IDx_LEFT_BORDER ',IDx_LEFT_BORDER)
			#print ('IDx_RIGHT_BORDER ',IDx_RIGHT_BORDER)
			#print ('left ', int(left))
			#print (IDx_LEFT_BORDER < int(left) < IDx_RIGHT_BORDER)

			if IDx_LEFT_BORDER < int(left) < IDx_RIGHT_BORDER:
				#AO Modelo Factura
				if div.text_content().strip('\n').isnumeric():
					filtered_divs['ITEM'].append(div.text_content().strip('\n'))


			if DESC_LEFT_BORDER < int(left) < DESC_RIGHT_BORDER:
				#print ('descricao...')
				#print (div.text_content().strip('\n').upper())
				filtered_divs['DESCRIPTION'].append(div.text_content().strip('\n'))

			if QTY_LEFT_BORDER < int(left) < QTY_RIGHT_BORDER:
				#print ('QTY...')
				#print (div.text_content().strip('\n').upper())
				if div.text_content().strip('\n').isnumeric():
					if "CODE" in headers_no_file:
						print ('tem CODE... verifica se QTD')
					else:
						filtered_divs['QUANTITY'].append(div.text_content().strip('\n'))
			elif QTYx_LEFT_BORDER < int(left) < QTYx_RIGHT_BORDER:
				#print ('QTY...')
				#print (div.text_content().strip('\n').upper())
				if div.text_content().strip('\n').upper().endswith('UNIDADE') or div.text_content().strip('\n').upper().endswith('UNIT'):
					if div.text_content().split(' ')[0].strip('\n').isnumeric():
						filtered_divs['QUANTITY'].append(div.text_content().split(' ')[0].strip('\n'))


			if RATE_LEFT_BORDER < int(left) < RATE_RIGHT_BORDER:
				#print ('RATE...')
				#print (div.text_content().strip('\n').upper())
				#print ('TRANSPORTED VALUE' not in div.text_content().strip('\n'))
				if 'TRANSPORTED VALUE' not in div.text_content().strip('\n').upper() and 'TRANSPORTING VALUE' not in div.text_content().strip('\n').upper():
					print ('preco ',div.text_content().strip('\n'))
					print (div.text_content().strip('\n').isnumeric())
					print (re.match(cash_pattern,div.text_content().strip('\n').replace(',','')))

					if div.text_content().strip('\n').isnumeric():
						filtered_divs['RATE'].append(div.text_content().strip('\n'))
					elif re.match(cash_pattern,div.text_content().strip('\n').replace(',','')):
						filtered_divs['RATE'].append(div.text_content().strip('\n'))

				elif 'TRANSPORTING VALUE' in div.text_content().strip('\n').upper():
					#Get the Currency of the PDF....
					if not moedainvoice:
						#Check if has $ €
						if "€" in div.text_content().strip('\n'):
							moedainvoice = "Eur"
						elif "$" in div.text_content().strip('\n'):
							moedainvoice = "Usd"

						#print (div.text_content().strip('\n').upper())
						#moedainvoice = div.text_content().strip('\n').upper()
						#print (moedainvoice)
						#frappe.throw(porra)
			if RATEx_LEFT_BORDER < int(left) < RATEx_RIGHT_BORDER:
				#AO Modelo Factura
				if div.text_content().strip('\n').upper().startswith('AOA'):
					tmprate = div.text_content().split(' ')[1]
					filtered_divs['RATE'].append(tmprate)
					#print ('NAO ADDED RATEX ',div.text_content().strip('\n'))
					#print (tmprate)

				if not moedainvoice:
					#Check if has $ €
					if "€" in div.text_content().strip('\n'):
						moedainvoice = "Eur"
					elif "$" in div.text_content().strip('\n'):
						moedainvoice = "Usd"
					elif "AOA" in div.text_content().strip('\n') or "KZ" in div.text_content().strip('\n'):
						moedainvoice = "AOA"


			if TOTAL_LEFT_BORDER < int(left) < TOTAL_RIGHT_BORDER:
				#print ('TOTAL...')
				#print (div.text_content().strip('\n').upper())
				if "14.0%" not in div.text_content().strip('\n'):
					print (div.text_content().strip('\n').isnumeric())
					print (re.match(cash_pattern,div.text_content().strip('\n').replace(',','')))

					if div.text_content().strip('\n').isnumeric():
						if "CODE" in headers_no_file and div.text_content().strip().isnumeric() and oldquantity == 0:
							filtered_divs['QUANTITY'].append(div.text_content().strip())
							oldquantity = div.text_content().strip()
							oldrate = 0
							print ('aqui QTD')
						else:
							filtered_divs['TOTAL'].append(div.text_content().strip('\n'))
						print ('AQUI AQUI TOTAL ', div.text_content().strip('\n'))
					elif div.text_content().strip('\n').upper().endswith('AOA'):
						tmptotal = div.text_content().split(' ')[0]
						print ('total ', re.match(cash_pattern,tmptotal.replace(',','')))
						if re.match(cash_pattern,tmptotal.replace(',','')):
							filtered_divs['TOTAL'].append(tmptotal)

						#print ('TOTAL TOTAL ', div.text_content().strip('\n'))
						#print (tmptotal)
					elif re.match(cash_pattern,div.text_content().strip('\n').replace(',','')):
						if len(div.text_content().strip().split()) == 3:
							#assuming numbers separated by space like Qtd Price Total
							print ('assuming numbers separated by space like Qtd Price Total')
							print ('numer ', div.text_content().strip().split()[0].isnumeric())
							print ('numer1 ', re.match(cash_pattern,div.text_content().strip().split()[1].replace(',','')))
							print ('numer2 ', re.match(cash_pattern,div.text_content().strip().split()[2].replace(',','')))

							if div.text_content().strip().split()[0].isnumeric() and re.match(cash_pattern,div.text_content().strip().split()[1].replace(',','')) and re.match(cash_pattern,div.text_content().strip().split()[2].replace(',','')):
								filtered_divs['QUANTITY'].append(div.text_content().strip().split()[0])
								filtered_divs['RATE'].append(div.text_content().strip().split()[1])
								filtered_divs['TOTAL'].append(div.text_content().strip().split()[2])

								oldquantity = 0 # div.text_content().strip().split()[0]
								oldrate = div.text_content().strip().split()[1]
								oldtotal = div.text_content().strip().split()[2]

						else:
							print ('numeric ', div.text_content().strip().isnumeric())
							print ('oldquantity ',oldquantity)
							print ('oldrate ',oldrate)
							print ('oldtotal ',oldtotal)

							print ('tem CODE in headers')
							print ("CODE" in headers_no_file)
							if "CODE" in headers_no_file and div.text_content().strip().isnumeric() and oldquantity == 0:
								filtered_divs['QUANTITY'].append(div.text_content().strip())
								oldquantity = div.text_content().strip()
							elif "CODE" in headers_no_file and oldrate == 0:
								filtered_divs['RATE'].append(div.text_content().strip())
								oldrate = div.text_content().strip()
								#Reset so next loop will be TOTAL
								oldtotal = 0

							elif "CODE" in headers_no_file and oldrate == 0:
								filtered_divs['TOTAL'].append(div.text_content().strip())
								oldtotal = div.text_content().strip()
							else:
								filtered_divs['TOTAL'].append(div.text_content().strip('\n'))
							#frappe.throw(porra)
						print ('AQUI1 AQUI1 ', div.text_content().strip('\n'))


					#Check if has $ €
					if "€" in div.text_content().strip('\n'):
						moedainvoice = "Eur"
					elif "$" in div.text_content().strip('\n'):
						moedainvoice = "Usd"

				#if "149,719.53 AOA" in div.text_content().strip('\n'):
				#	frappe.throw(porra)
			if empresaSupplier == "":
				if "PAGE" not in div.text_content().strip('\n').upper():
					empresaSupplier = div.text_content().strip('\n').upper()

			if "INVOICE DATE:" in div.text_content().strip('\n').upper():
				if invoicedate == "":
					print('INVOICE DATE:')
					print (div.text_content().upper())
					print (div.text_content().upper().split('\n'))
					for ii in div.text_content().upper().split('\n'):
						print (ii)
						print (len(ii))
						if "INVOICE DATE:" in ii.upper():
							if len(ii) > 13:
								invoicedate = ii[ii.find('INVOICE DATE:')+13:].strip()
						if "INVOICE NO:" in ii.upper():
							if len(ii) > 11:
								invoicenumber = ii[ii.find('INVOICE NO:')+11:].strip()

			if "P.O BOX:" in div.text_content().strip('\n').upper():
				#Address Supplier
				if empresaSupplierEndereco == "":
					empresaSupplierEndereco = div.text_content().strip('\n').upper()

			if "SL" in div.text_content().strip('\n').upper():
				#Some Suppliers; Order Number
				print ('TEM SL')
				print (div.text_content().strip('\n'))
				if 85 < int(left) < 87:
					#Check if has split
					print (div.text_content().split('\n'))
					print (len(div.text_content().split('\n')))
					if div.text_content().split('\n')[1].isnumeric():
						filtered_divs['ITEM'].append(div.text_content().split('\n')[1])
					#temitems = True
			if "DESCRIPTION" in div.text_content().strip('\n').upper():
				#Supplier Description + Item name + Serial Number if has...
				print ('TEM Description + Item name + Serial Number if has')
				print (div.text_content().strip('\n'))
				if 100 < int(left) < 102:
					#Check if has split
					print (div.text_content().split('\n'))
					print (len(div.text_content().split('\n')))
					print ('STILL NEED TO CHECK IF MORE THAN 1 SERIAL NUMBER...')
					if len(div.text_content().split('\n')) >= 3:
						if div.text_content().split('\n')[2] != "":
							filtered_divs['DESCRIPTION'].append(div.text_content().split('\n')[1] + " SN: " + div.text_content().split('\n')[2])
						else:
							filtered_divs['DESCRIPTION'].append(div.text_content().split('\n')[1])
						oldIDXDescription = len(filtered_divs['DESCRIPTION'])
			if temitems == False and div.text_content().strip('\n')[:2].strip().isdigit():
				#Starts with a Number... might be OrderNumber + Item Description
				if 86 < int(left) < 88:
					print (div.text_content().split('\n'))
					print (div.text_content()[:div.text_content().find(' ')].strip())
					print (div.text_content()[div.text_content().find(' '):].strip())

					filtered_divs['ITEM'].append(div.text_content()[:div.text_content().find(' ')].strip())
					filtered_divs['DESCRIPTION'].append(div.text_content()[div.text_content().find(' '):].strip())
					print (len(filtered_divs['DESCRIPTION']))
					oldIDXDescription = len(filtered_divs['DESCRIPTION'])
					#frappe.throw(porra)


			if "Y/M COLOR" in div.text_content().strip('\n').upper():
				#print ('TO DO LATER')
				#will or might contain Y COLOR and FUEL: 2022 black Petrol
				print (div.text_content().split('\n'))
				if filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:') == -1:
					#Append at the end
					filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + ' ' + div.text_content().split('\n')[1]
				else:
					print (filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:'))
					print (filtered_divs['DESCRIPTION'][oldIDXDescription-1][:filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:')])
					tmpdesc = filtered_divs['DESCRIPTION'][oldIDXDescription-1]
					filtered_divs['DESCRIPTION'][oldIDXDescription-1] = tmpdesc.replace('SN:', div.text_content().split('\n')[1] + ' SN:')
					#print (filtered_divs['DESCRIPTION'])


			if "FUEL QTY" in div.text_content().strip('\n').upper():
				print ('GET QTY FUEL WILL BE LATER...')
				print (div.text_content().split('\n'))
				#frappe.throw(porra)


			if 360 < int(left) < 362:
				#Qty Column
				print ('Qty Column')
				if div.text_content().strip('\n').isnumeric():
					if "CODE" in headers_no_file:
						print ('tem CODE... verifica se QTD')
					else:
						filtered_divs['QUANTITY'].append(div.text_content().strip('\n'))

			if 394 < int(left) < 396:
				#RATE Column
				print ('RATE Column')
				print (div.text_content().strip('\n'))
				if re.match(cash_pattern,div.text_content().strip('\n').replace(',','')):
					filtered_divs['RATE'].append(div.text_content().strip('\n'))


			if 469 < int(left) < 471:
				#TOTAL Column
				print ('TOTAL Column')
				print (div.text_content().split('\n'))
				if "TOTAL" in div.text_content().strip('\n'):
					print (len(div.text_content().split('\n')))
					if len(div.text_content().split('\n')) >= 2:
						print (div.text_content().split('\n')[1])
						print (re.match(cash_pattern,div.text_content().split('\n')[1].replace(',','')))
						if re.match(cash_pattern,div.text_content().split('\n')[1].replace(',','')):
							filtered_divs['TOTAL'].append(div.text_content().split('\n')[1])
			if 100 < int(left) < 102:
				#Serial Numbers....
				#JTGCBAB8906725029
				print ('Serial Numbers.... ')
				print (div.text_content().strip('\n').replace(' ',''))
				print (len(div.text_content().strip('\n').replace(' ','')))
				if len(div.text_content().strip('\n')) >= 17:
					if div.text_content().strip('\n').find(' ') == -1:
						print ('PODE SER Serial Numbers.... ')
						print (oldIDXDescription)
						print (filtered_divs['DESCRIPTION'][oldIDXDescription-1])
						if filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:') == -1:
							filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + " SN: " + div.text_content().strip('\n')
						else:
							filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + div.text_content().strip('\n')

						print ('ADDICIONOU SERIAL ')
						print (filtered_divs['DESCRIPTION'][oldIDXDescription-1])

			if 252 < int(left) < 254:
				#will or might contain Y COLOR and FUEL: 2022 black Petrol
				print (div.text_content().split('\n'))
				print (div.text_content().strip('\n'))
				#check if starts with 4 digits for YEAR
				if div.text_content().strip('\n')[:5].strip().isdigit():
					if filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:') == -1:
						#Append at the end
						filtered_divs['DESCRIPTION'][oldIDXDescription-1] = filtered_divs['DESCRIPTION'][oldIDXDescription-1] + ' ' + div.text_content().strip('\n')
					else:
						print (filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:'))
						print (filtered_divs['DESCRIPTION'][oldIDXDescription-1][:filtered_divs['DESCRIPTION'][oldIDXDescription-1].find('SN:')])
						tmpdesc = filtered_divs['DESCRIPTION'][oldIDXDescription-1]
						filtered_divs['DESCRIPTION'][oldIDXDescription-1] = tmpdesc.replace('SN:', div.text_content().strip('\n') + ' SN:')
						#print (filtered_divs['DESCRIPTION'])


			if "AED" in div.text_content().strip('\n'):
				if moedainvoice == "":
					moedainvoice = "AED"

				#if "149,719.53 AOA" in div.text_content().strip('\n'):
				#	frappe.throw(porra)

	# Merge and clear lists with data
	print ('ITEMs')
	print (filtered_divs['ITEM'])
	print (len(filtered_divs['ITEM']))

	print ('DESCRIPTIONs')
	print (filtered_divs['DESCRIPTION'])
	print (len(filtered_divs['DESCRIPTION']))
	print ('QUANTITY')
	print (filtered_divs['QUANTITY'])
	print (len(filtered_divs['QUANTITY']))
	print ('RATE')
	print (filtered_divs['RATE'])
	print (len(filtered_divs['RATE']))
	print ('TOTAL')
	print (filtered_divs['TOTAL'])
	print (len(filtered_divs['TOTAL']))

	data = []
	if filtered_divs['IVA']:
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['IVA']):
			if 'ITEM' in row[0]:
				continue
			#data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4]}
			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5]}
			data.append(data_row)
	else:
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL']):
			if 'ITEM' in row[0]:
				continue

			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4]}
			#data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5]}
			data.append(data_row)


	print('Supplier ', empresaSupplier)
	print ('supplieraddre ', empresaSupplierEndereco)
	print ('supplierNIF ', empresaSupplierNIF)
	print ('supplierPais ', empresaPais)

	print('Invoice', invoicenumber)
	print('Date ', invoicedate)
	print('Moeda ', moedainvoice)


	pprint(data)
	stop_time = time.monotonic()
	print(round(stop_time-start_time, 2), "seconds")

	return (empresaSupplier,invoicenumber,invoicedate,moedainvoice,empresaSupplierEndereco,empresaSupplierNIF,empresaPais,data)

def aprender_OCR(data,action = "SCRAPE",tipodoctype = None):
	'''
	Last modified: 22-09-2023
	Using to Train or LEARN OCR from PDF files not configurated on the System....
	'''
	start_time = time.monotonic()

	#terpalavras_header = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qtd.', 'Pr.Unit', 'Cód. Artigo', 'V.Líquido', 'V. Líquido']
	#terpalavras_header = ['VALOR UN', 'VALOR TOTAL LIQ', 'UNIDADE', 'UNI', 'UN', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'QUANT', 'Qtd.', 'PREÇO', 'Pr.Unit', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', 'DESC', 'DEC', 'TAXA', 'IVA']

	#FIX 22-09-2023; Added words to HEADER
	#terpalavras_header = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qtd.', 'Pr.Unit', 'Cód. Artigo', 'V.Líquido', 'V. Líquido']
	#terpalavras_header = ['VALOR UN', 'VALOR TOTAL LIQ', 'UNIDADE', 'UNI', 'UN', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'QUANT', 'Qtd.', 'PREÇO', 'Pr.Unit', 'Pr. Unitário', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', 'DESC', 'DEC', 'TAXA', 'IVA', 'Total c/ IVA']
	terpalavras_header = ['Total c/ IVA','Totalc/IVA','VALOR UN', 'VALOR TOTAL LIQ', 'UNIDADE', 'UNI', 'UN', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qotd.', 'QUANT', 'Qtd.', 'PREÇO', 'Pr. Unitário', 'Pr.Unit', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', 'DESC.', 'DESC', 'DEC', 'TAXA', 'IVA', ' VA ', 'Arm']


	#terpalavras_header_EN = ['CODE NO','CODE', 'DESCRIPTION', 'Y/M', 'COLOR', 'FUEL',' QTY', 'ITEM', 'QUANTITY', 'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL AMOUNT', 'AMOUNT', 'TOTAL', 'VAT', 'PRICE']
	#FIX 27-07-2023
	terpalavras_header_EN = ['CODE NO','CODE', 'DESCRIPTION', 'Y/M', 'COLOR', 'FUEL',' QTY', 'ITEM', 'QUANTITY', 'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'UNIT', 'TOTAL AMOUNT', 'TOTAL PRICE', 'AMOUNT', 'TOTAL', 'VAT', 'TAXES', 'PRICE']

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])\s([1-9]{1,2}):([1-9]{2}):[0-9]{2}\s(AM|PM)|([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	#cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)'

	#cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'
	cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)|(?:\d*\,\d+)'

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'


	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}
	filtered_divs = {'COUNTER': [], 'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}

	palavras_no_header = []
	palavras_no_header_ultimoHeader = ['VALOR LIQ.','VALOR TOTAL']

	supplierMoeda = ''

	if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
		filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)

	else:
		filefinal = data

	#If no results... than change to OCR
	if ".pdf" in filefinal:

		print ('FAZ OCR COMPRAS 000')
		print ('FAZ OCR COMPRAS 000')
		print ('=================')
		en_scan = False
		#Check if Document is in PT or ENG...
		#FIX 27-07-2023
		en_terpalavras = ['PROFORMA INVOICE','PROFORMA INVOCIE','SALES INVOICE','INVOICE','QUOTATION']
		#FIX 14-12-2022
		#en_palavras_fim_item = ['INCIDENCE','TAXABLE AMT'] #['INCIDENCE','TAX','TAXABLE AMT'] #['INCIDENCE','VAT','TAX']
		#FIX 27-07-2023
		en_palavras_fim_item = ['INCIDENCE','TAXABLE AMT','UNTAXED AMOUNT', 'VAT 5%']

		fim_items = False

		palavras_serialnumbers = ['SN:','SN ']

		contapalavras_header = 0

		#Check first if EN or PT Document...
		import pdfquery
		tmppdf  = pdfquery.PDFQuery(filefinal)
		tmppdf.load(0)
		for engpalav in en_terpalavras:
			print ('engpalav ',engpalav)
			#print (pdf.pq(':contains("{}")'.format(engpalav)).text())
			tt = tmppdf.pq(':contains("{}")'.format(engpalav)).text()
			if tt:
				#print (tt)
				en_scan = True
				print ('TEM INGLES')

		#FIX 27-07-2023; Convert to UPPER to check for HEADER
		if not en_scan:
			facturaSupplier = tmppdf.pq.text().upper()
			for engpalav in en_terpalavras:
				if engpalav in facturaSupplier:
					print ('FIX 27-07-2023')
					print ('DOC is ENGLISH....SCAN again ')
					en_scan = True

					#print ('PARA VER SE MOSTRA QUOTATION')
					#facturaSupplier1 = ocr_pytesseract (filefinal,"COMPRAS",'por',200)
					#print (facturaSupplier1)


		if not en_scan:
			facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'por',250)
			print (facturaSupplier.split('\n'))

			for engpalav in en_terpalavras:
				if engpalav in facturaSupplier:
					print ('DOC is ENGLISH....SCAN again ')
					en_scan = True

		palavras_header_counted = False
		Qtd_isnot_number = False	#To control if needs to OCR again as 260

		if en_scan:

			#Check if needs Scan lower 260 to get all Numbers
			#palavras_header_counted = False
			#Qtd_isnot_number = False	#To control if needs to OCR again as 260

			#Scan in ENGLISH
			facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'eng',270) #270) #180) #150) retuns line counter but not the rest...

			#Scan 260 and checks for HEADERs more than 2
			for fsup in facturaSupplier.split('\n'):
				if palavras_header_counted == False:
					palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
					palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE
					print (fsup.strip().upper())

					#FIX 27-07-2023; Check if words not in en_palavras_fim_item
					print (en_palavras_fim_item)
					ignora_header = False
					for ppp in en_palavras_fim_item:
						if ppp.upper() in fsup.strip().upper():
							ignora_header = True
							break

					if ignora_header:
						print ('NAO POE NO HEADER WORDS from FIM ITEM....')
					else:
						for pp in terpalavras_header_EN:
							if pp.upper() in fsup.strip().upper():
								print ('Palavaheader ', pp.upper())
								if pp.upper() == 'UNIT PRICE' or pp.upper() == 'TOTAL':
									if palavra_preco:
										print ('NAO CONTA HEADER PRECO ', pp.upper())
									if palavra_total:
										print ('NAO CONTA HEADER TOTAL ', pp.upper())

								if not palavra_preco or not palavra_total:
									#To avoid TOTAL AMOUNT and TOTAL being added
									if 'TOTAL AMOUNT' in palavras_no_header and pp.upper() == 'TOTAL':
										print ('SKIP TOTAL')
									elif 'TOTAL PRICE' in palavras_no_header and pp.upper() == 'TOTAL':
										#FIX 27-07-2023
										print ('SKIP TOTAL 000')

									elif 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and pp.upper() == 'CODE':
										print ('SKIP CODE and CODE NO')
									else:
										if not palavra_preco and pp.upper() == "UNIT":
											#FIX 27-07-2023
											print ('Pode acrescentar UNIT or UNIT PRICE ao HEADER')
										elif not palavra_preco and pp.upper() == "PRICE":
											print ('Pode acrescentar PRICE ao HEADER')
										elif palavra_preco and pp.upper() == "PRICE":
											print ('SKIP ADDING PRICE TO HEADER')
										else:
											contapalavras_header += 1
											print ('pode contar HEADER ', pp.upper())
											print ('contapalavras_header ', contapalavras_header)
											palavras_no_header.append(pp.upper())
								if contapalavras_header >= 6:
									palavras_header_counted = True
								#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
								if pp.upper() == 'UNIT PRICE (EUR)': # or pp.upper() == 'PRICE':
									palavra_preco = True
								if pp.upper() == 'TOTAL PRICE (EUR)' or pp.upper() == 'TOTAL AMOUNT':
									palavra_total = True
					if contapalavras_header <= 3:
						print ('Scan HEADER AGAIN.... ')

			print ("palavras_no_header ",palavras_no_header)
			print (contapalavras_header)

			#FIX 22-01-2023; Scan table using pd2txt.comecar ...
			print ('Scan table using pd2txt.comecar ...')
			print ('TEXTO ',facturaSupplier.upper())

			if contapalavras_header <= 4 and 'Description of Goods'.upper() in facturaSupplier.upper(): # or contapalavras_header <= 4 and 'Description'.upper() in facturaSupplier.upper():
				palavras_header_counted = False
				palavras_no_header = []
				print ('Scan table using pd2txt.comecar ...')
				from angola_erp_ocr.api.pdf2txt import extrair_texto
				print ('FILEFINAL')
				print (filefinal)
				textotabela = extrair_texto(filefinal)
				print ('Read file generated....')

				#print (textotabela)
				#print (textotabela[0].split('\n'))
				facturaSupplier_tmp = textotabela
				terpalavras_header_EN = ['CODE NO','CODE', 'DESCRIPTION OF GOODS', 'DESCRIPTION', 'Y/M', 'COLOR', 'FUEL',' QTY', 'ITEM', 'QUANTITY', 'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL AMOUNT', 'AMOUNT', 'TOTAL', 'VAT', 'PRICE', 'CARTON', 'PICTURE', 'SUM', 'UNIT']
				print ('facturaSupplier')
				print (facturaSupplier_tmp)
				for fsup in facturaSupplier_tmp:
					print ('1- TEXTOOOOOOaaaa *********')
					print (fsup.strip())

					print ('00000000')
					print ('TEXTO LINHA: ', fsup)
					for fi in en_palavras_fim_item:
						print ('HEADRE ',fsup.strip().upper())
						print ('fi ', fi.upper())
						if fi.upper() in fsup.strip().upper():
							fim_items = True

					if fsup.strip == "ITEM CODE DESCRIPTION QUANTITY —_ UNIT PRICE TOTAL":
						frappe.throw(porra)

					if not fsup.strip().startswith('SN:'):
						print ('conta PALAVRAS HEADER ', contapalavras_header)
						print ('fim items ', fim_items)
						if contapalavras_header >= 5 and not fim_items:
							#Now check if all Columns for Items are correct ....
							#ITEM| DESCRIPTION| QUANTITY| UNIT PRICE (EUR)| TOTAL PRICE (EUR)
							#this case must have 5 columns with TEXTs...
							totalgeral = ''
							precounitario = ''
							quantidade = ''


							for idx,cc in reversed(list(enumerate(fsup.split()))):
								print ('contapalavras_header ',contapalavras_header)
								print (len(fsup.split()))
								if len(fsup.split()) > contapalavras_header:
									print ('TEM ESPACO nos ITENS.... ')
									print ('TODO: IDX: last must be Number, LAST-1 also, last-2 also')
									print ('TODO: IDX: First can be Number or TEXT')
									print ('TODO: if NOT IDX: First and not LAST-1 and not LAST-2 than is DESCRIPTION')
									#frappe.throw(porra)
								elif len(fsup.split()) <= 3:
									print ('PODE SER SNs.... CANCEL QTD CHECK')
									break



								print ('===== FIRST IDX00 ======')
								print ('idx ',idx)
								print ('cc ',cc)

								#Check if cash
								print (re.match(cash_pattern,cc))
								print (cc.strip().isnumeric())
								#If startswith SN: skip


								if re.match(cash_pattern,cc):
									if not totalgeral:
										totalgeral = cc
									elif not precounitario:
										precounitario = cc
								elif contapalavras_header == 5:
									#Check QTD is a Number...
									if len(fsup.split()) > 1:
										print ('size fsup ',len(fsup.split()))
										#FIX 21-12-2022; Check if Currency Symbol...
										if cc.strip() == "€":
											if not supplierMoeda:
												supplierMoeda = 'EUR'

										elif not cc.strip().isnumeric():
											#Gera novamente o OCR bcs QTD is not a Number...
											if quantidade == '':
												#Qtd_isnot_number = True
												print ('QTD is not a NUMBER ', cc)
												#frappe.throw(porra)
												#break
												#SET to ZERO and after Rate and Total added divide to find the QTD
												quantidade = 0

								if cc.strip().isnumeric():
									if contapalavras_header == 5:
										#Assuming that 5 is Total, 4 is Unit Price, 3 is Qtd
										if not idx == 0:
											if not quantidade:
												quantidade = cc
												Qtd_isnot_number = False

							print ('totalgeral ', totalgeral)
							print ('precounitario ', precounitario)
							print ('quantidade ', quantidade)

							#if "0.15065" in fsup:
							#	frappe.throw(porra)

						#Must be last to avoid running on the top first and still on the HEADER TEXT...
						print ('VERIFICAR palavras_header_counted ', palavras_header_counted)
						if palavras_header_counted == False:
							palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
							palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE

							for pp in terpalavras_header_EN:
								if pp.upper() in fsup.strip().upper():
									print ('fsup.strip')
									print (fsup.strip().upper())
									print ('Palavaheader ', pp.upper())
									if pp.upper() == 'UNIT PRICE' or pp.upper() == 'TOTAL' or pp.upper() == 'PRICE':
										if palavra_preco:
											print ('NAO CONTA HEADER PRECO ', pp.upper())
										if palavra_total:
											print ('NAO CONTA HEADER TOTAL ', pp.upper())
										if pp.upper() == 'PRICE':
											print (palavras_no_header)
											print ('palavra_preco ', palavra_preco)
											print ('+++++ AAAAAAAA +++++ ')

										#if ('UNIT PRICE' in palavras_no_header  or 'PRICE' in palavras_no_header or 'UNIT' in palavras_no_header) and (pp.upper() == 'UNIT PRICE' or pp.upper() == 'UNIT' or pp.upper() == 'PRICE'):
										if ('UNIT PRICE' in palavras_no_header  or 'PRICE' in palavras_no_header) and (pp.upper() == 'UNIT PRICE' or pp.upper() == 'PRICE'):
											palavra_preco = True
											print ('Skip Unit Price or Unit')

									if not palavra_preco or not palavra_total:
										#To avoid TOTAL AMOUNT and TOTAL being added
										if 'TOTAL AMOUNT' in palavras_no_header and pp.upper() == 'TOTAL':
											print ('SKIP TOTAL')
										elif 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and pp.upper() == 'CODE':
											print ('SKIP CODE and CODE NO')
										elif ('DESCRIPTION OF GOODS' in palavras_no_header  or 'DESCRIPTION' in palavras_no_header) and (pp.upper() == 'DESCRIPTION OF GOODS' or pp.upper() == 'DESCRIPTION'):
											print ('SKIP DESCRIPTION OF GOODS and DESCRIPTION')
											print (palavras_no_header)

										else:
											if pp.upper() == 'PRICE':
												print ('palavras no header ', palavras_no_header)
											if not palavra_preco:
												palavras_no_header.append(pp.upper())
												contapalavras_header += 1
												print ('pode contar HEADER ', pp.upper())
												print ('contapalavras_header ', contapalavras_header)

											#frappe.throw(porra)

									#palavras_header_counted = True
									if contapalavras_header >= 9:
										#palavras_header_counted = True
										print ('palavras_header_counted SET FALSE')
										print ('contapalavras_header')
										print (palavras_no_header)
									if 'PICTURE' in palavras_no_header:
										palavras_header_counted = True
										print ('PICTURE no HEADER COUNT')
									#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
									if pp.upper() == 'UNIT PRICE (EUR)': # or pp.upper() == 'PRICE':
										palavra_preco = True
									if pp.upper() == 'TOTAL PRICE (EUR)' or pp.upper() == 'TOTAL AMOUNT':
										palavra_total = True
							if contapalavras_header <= 3:
								print ('Scan HEADER AGAIN22222.... ')
						if Qtd_isnot_number:
							break

				print ('palavras_no_header')
				print (palavras_no_header)
				print ('CALLED OCR_OCR_OCR')
				print ('Qtd_isnot_number ',Qtd_isnot_number)

				return ocr_ocr_ocr (facturaSupplier_tmp,en_palavras_fim_item,en_scan,supplierMoeda,terpalavras_header_EN,palavras_no_header)

				#frappe.throw(porra)
			else:
				print ('AQUI PORQUE !!!!!')
				print ('facturaSupplier')
				print (facturaSupplier)


				proxima_linha = False	#FIX 28-07-2023

				#frappe.throw(porra)
				for fsup in facturaSupplier.split('\n'):
					print ('00000000')
					print ('TEXTO LINHA: ', fsup)
					for fi in en_palavras_fim_item:
						print ('HEADRE ',fsup.strip().upper())
						print ('fi ', fi.upper())
						if fi.upper() in fsup.strip().upper():
							print ('FIM TABELA ITENS....')
							fim_items = True

					if fsup.strip == "ITEM CODE DESCRIPTION QUANTITY —_ UNIT PRICE TOTAL":
						frappe.throw(porra)

					print ('palavras_no_header')
					print (palavras_no_header)
					is_palavras_no_header = False

					print (len(fsup.strip().upper()))
					print (len(palavras_no_header))

					if len(fsup.strip().upper()) >= len(palavras_no_header):
						print ('verificar.....')
						is_palavras_no_header = True
						for p1 in palavras_no_header:
							if p1 not in fsup.strip().upper():
								#FIX 28-07-2023; case hearer should be UNIT PRICE but shows only UNIT or PRCE
								if fsup.strip().upper() == "PRICE" and "UNIT" in palavras_no_header:
									is_palavras_no_header = True
								else:
									is_palavras_no_header = False


					if is_palavras_no_header:
						#FIX 28-07-2023; Case line is same as HEADER
						print ('Verifica se is o HEADER....')
					elif fsup.strip().upper() == "QUOTATION DATE: EXPIRATION: SALESPERSON:":
						#FIX 28-07-2023; Case line is QUOTATION DATE: EXPIRATION: SALESPERSON:
						print ('MEANS next line will have the values for those....')
						proxima_linha = True
					elif proxima_linha and fsup:
						#FIX 28-07-2023
						print ('Guarda a DATA da PROFORMA / FACTURA ....')
						proxima_linha = False


					elif not fsup.strip().startswith('SN:'):
						if contapalavras_header >= 5 and not fim_items:
							#Now check if all Columns for Items are correct ....
							#ITEM| DESCRIPTION| QUANTITY| UNIT PRICE (EUR)| TOTAL PRICE (EUR)
							#this case must have 5 columns with TEXTs...
							totalgeral = ''
							precounitario = ''
							quantidade = ''
							ivacompra_1 = ''


							for idx,cc in reversed(list(enumerate(fsup.split()))):
								print ('contapalavras_header ',contapalavras_header)
								print (len(fsup.split()))
								if len(fsup.split()) > contapalavras_header:
									print ('TEM ESPACO nos ITENS.... ')
									print ('TODO: IDX: last must be Number, LAST-1 also, last-2 also')
									print ('TODO: IDX: First can be Number or TEXT')
									print ('TODO: if NOT IDX: First and not LAST-1 and not LAST-2 than is DESCRIPTION')
									#frappe.throw(porra)
								elif len(fsup.split()) <= 3:
									print ('PODE SER SNs.... CANCEL QTD CHECK')
									break



								print ('===== FIRST IDX02 ======')
								print ('idx ',idx)
								print ('cc ',cc)

								#Check if cash
								print (re.match(cash_pattern,cc.replace('$','')))
								print (cc.strip().isnumeric())
								#If startswith SN: skip


								if re.match(cash_pattern,cc.replace('$','')):
									if not totalgeral:
										totalgeral = cc.replace('$','')
										if not supplierMoeda and "$" in cc:
											supplierMoeda = 'USD'

									elif not precounitario:
										precounitario = cc.replace('$','')
									elif ".00" in cc.strip():
										#FIX 28-07-2023; Case ends with .00 and is QTD
										if not quantidade:
											quantidade = cc.strip().replace('.00','')

								elif contapalavras_header == 5:
									#Check QTD is a Number...
									if len(fsup.split()) > 1:
										print ('size fsup ',len(fsup.split()))
										#FIX 21-12-2022; Check if Currency Symbol...
										if cc.strip() == "€":
											if not supplierMoeda:
												supplierMoeda = 'EUR'
										elif "%" in cc.strip():
											#FIX 28-07-2023 Supplier has VAT/IVA
											if not ivacompra_1:
												ivacompra_1 = cc.strip()

										elif not cc.strip().isnumeric():
											#Gera novamente o OCR bcs QTD is not a Number...
											if quantidade == '':
												#Qtd_isnot_number = True
												print ('QTD is not a NUMBER ', cc)
												#frappe.throw(porra)
												#break
												#SET to ZERO and after Rate and Total added divide to find the QTD
												quantidade = 0

								if cc.strip().isnumeric():
									if contapalavras_header == 5:
										#Assuming that 5 is Total, 4 is Unit Price, 3 is Qtd
										if not idx == 0:
											if not quantidade:
												quantidade = cc
												Qtd_isnot_number = False

							print ('totalgeral ', totalgeral)
							print ('precounitario ', precounitario)
							print ('quantidade ', quantidade)

							#if "0.15065" in fsup:
							#	frappe.throw(porra)

						'''
						#Must be last to avoid running on the top first and still on the HEADER TEXT...
						if palavras_header_counted == False:
							palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
							palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE
							for pp in terpalavras_header_EN:
								if pp.upper() in fsup.strip().upper():
									print ('Palavaheader ', pp.upper())
									if pp.upper() == 'UNIT PRICE' or pp.upper() == 'TOTAL':
										if palavra_preco:
											print ('NAO CONTA HEADER PRECO ', pp.upper())
										if palavra_total:
											print ('NAO CONTA HEADER TOTAL ', pp.upper())
									if not palavra_preco or not palavra_total:
										#To avoid TOTAL AMOUNT and TOTAL being added
										if 'TOTAL AMOUNT' in palavras_no_header and pp.upper() == 'TOTAL':
											print ('SKIP TOTAL')
										elif 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and pp.upper() == 'CODE':
											print ('SKIP CODE and CODE NO')
										else:
											contapalavras_header += 1
											print ('pode contar HEADER ', pp.upper())
											print ('contapalavras_header ', contapalavras_header)
											palavras_no_header.append(pp.upper())

									palavras_header_counted = True
									#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
									if pp.upper() == 'UNIT PRICE (EUR)': # or pp.upper() == 'PRICE':
										palavra_preco = True
									if pp.upper() == 'TOTAL PRICE (EUR)' or pp.upper() == 'TOTAL AMOUNT':
										palavra_total = True
							if contapalavras_header <= 3:
								print ('Scan HEADER AGAIN11111.... ')
						if Qtd_isnot_number:
							break
						'''


						#Must be last to avoid running on the top first and still on the HEADER TEXT...
						print ('VERIFICAR palavras_header_counted ', palavras_header_counted)
						if palavras_header_counted == False:
							palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
							palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE

							for pp in terpalavras_header_EN:
								if pp.upper() in fsup.strip().upper():
									#FIX 28-07-2023; Check if fim_items
									if not fim_items:
										print ('fsup.strip')
										print (fsup.strip().upper())
										print ('Palavaheader ', pp.upper())
										if pp.upper() == 'UNIT PRICE' or pp.upper() == 'TOTAL' or pp.upper() == 'PRICE':
											if palavra_preco:
												print ('NAO CONTA HEADER PRECO ', pp.upper())
											if palavra_total:
												print ('NAO CONTA HEADER TOTAL ', pp.upper())
											if pp.upper() == 'PRICE':
												print (palavras_no_header)
												print ('palavra_preco ', palavra_preco)
												print ('+++++ AAAAAAAA +++++ ')

											#if ('UNIT PRICE' in palavras_no_header  or 'PRICE' in palavras_no_header or 'UNIT' in palavras_no_header) and (pp.upper() == 'UNIT PRICE' or pp.upper() == 'UNIT' or pp.upper() == 'PRICE'):
											if ('UNIT PRICE' in palavras_no_header  or 'PRICE' in palavras_no_header) and (pp.upper() == 'UNIT PRICE' or pp.upper() == 'PRICE'):
												palavra_preco = True
												print ('Skip Unit Price or Unit')

										if not palavra_preco or not palavra_total:
											#To avoid TOTAL AMOUNT and TOTAL being added
											if 'TOTAL AMOUNT' in palavras_no_header and pp.upper() == 'TOTAL':
												print ('SKIP TOTAL')
											elif 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and pp.upper() == 'CODE':
												print ('SKIP CODE and CODE NO')
											elif ('DESCRIPTION OF GOODS' in palavras_no_header  or 'DESCRIPTION' in palavras_no_header) and (pp.upper() == 'DESCRIPTION OF GOODS' or pp.upper() == 'DESCRIPTION'):
												print ('SKIP DESCRIPTION OF GOODS and DESCRIPTION')
												print (palavras_no_header)

											else:
												if pp.upper() == 'PRICE':
													print ('palavras no header ', palavras_no_header)
												if not palavra_preco:
													if pp.upper() == 'UNIT' and 'UNIT' not in palavras_no_header:
														#FIX 28-07-2023
														palavras_no_header.append(pp.upper())
														contapalavras_header += 1
														print ('pode contar HEADER ', pp.upper())
														print ('contapalavras_header ', contapalavras_header)

													#FIX 28-07-2023; if UNIT no more add
													if pp.upper() == 'UNIT':
														palavra_preco = True

												#frappe.throw(porra)

										#palavras_header_counted = True
										if contapalavras_header >= 9:
											#palavras_header_counted = True
											print ('palavras_header_counted SET FALSE')
											print ('contapalavras_header')
											print (palavras_no_header)
										if 'PICTURE' in palavras_no_header:
											palavras_header_counted = True
											print ('PICTURE no HEADER COUNT')
										#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
										if pp.upper() == 'UNIT PRICE (EUR)': # or pp.upper() == 'PRICE':
											palavra_preco = True
										if pp.upper() == 'TOTAL PRICE (EUR)' or pp.upper() == 'TOTAL AMOUNT':
											palavra_total = True
							if contapalavras_header <= 3:
								print ('Scan HEADER AGAIN111111 22222.... ')
						if Qtd_isnot_number:
							break

				if Qtd_isnot_number:
					print ('HOW TO do 250 and if something missing after OCR do in 260 to COMPLETE WITH THE MISSING INFO... INITIALLY WILL ITEMS')
					print ('OCR ocr_pytesseract again with 260DPI')
					facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'eng',260)
				else:
					print ('PODE CONTINUAR....')


				print (facturaSupplier.split('\n'))
				print ('palavras_no_header ', palavras_no_header)

				print ('CALLED OCR_OCR_OCR')
				print ('Qtd_isnot_number ',Qtd_isnot_number)
				return ocr_ocr_ocr (facturaSupplier_tmp,en_palavras_fim_item,en_scan,supplierMoeda,terpalavras_header_EN,palavras_no_header)

				#frappe.throw(porra)
		else:
			#Palavras PT no Header
			print ('Palavras PT no Header')
			'''
			for fsup in facturaSupplier.split('\n'):
				if palavras_header_counted == False:
					palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
					palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE
					print (fsup.strip().upper())
					for pp in terpalavras_header_EN:
						if pp.upper() in fsup.strip().upper():
							print ('Palavaheader ', pp.upper())
							if pp.upper() == 'UNIT PRICE' or pp.upper() == 'TOTAL':
								if palavra_preco:
									print ('NAO CONTA HEADER PRECO ', pp.upper())
								if palavra_total:
									print ('NAO CONTA HEADER TOTAL ', pp.upper())

							if not palavra_preco or not palavra_total:
								#To avoid TOTAL AMOUNT and TOTAL being added
								if 'TOTAL AMOUNT' in palavras_no_header and pp.upper() == 'TOTAL':
									print ('SKIP TOTAL')
								elif 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and pp.upper() == 'CODE':
									print ('SKIP CODE and CODE NO')
								else:
									if not palavra_preco and pp.upper() == "PRICE":
										print ('Pode acrescentar PRICE ao HEADER')
									elif palavra_preco and pp.upper() == "PRICE":
										print ('SKIP ADDING PRICE TO HEADER')
									else:
										contapalavras_header += 1
										print ('pode contar HEADER ', pp.upper())
										print ('contapalavras_header ', contapalavras_header)
										palavras_no_header.append(pp.upper())
							if contapalavras_header >= 6:
								palavras_header_counted = True
							#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
							if pp.upper() == 'UNIT PRICE (EUR)': # or pp.upper() == 'PRICE':
								palavra_preco = True
							if pp.upper() == 'TOTAL PRICE (EUR)' or pp.upper() == 'TOTAL AMOUNT':
								palavra_total = True
					if contapalavras_header <= 3:
						print ('Scan HEADER AGAIN.... ')
			'''
			print ("palavras_no_header ",palavras_no_header)
			print (contapalavras_header)
			#FIX 22-01-2023; Scan table using pd2txt.comecar ...
			print ('Scan table using pd2txt.comecar PORTUGUES...')
			if contapalavras_header <= 4:
				contapalavras_header = 0
				palavras_header_counted = False
				palavras_no_header = []
				adicionapalavra_FIM = False	#To end adding to Header

				print ('Scan table using pd2txt.comecar ...')
				from angola_erp_ocr.api.pdf2txt import extrair_texto
				print ('FILEFINAL')
				print (filefinal)
				textotabela = extrair_texto(filefinal)
				print ('Read file generated....')

				#print (textotabela)
				#print (textotabela[0].split('\n'))
				facturaSupplier_tmp = textotabela
				terpalavras_header = ['VALOR UN', 'VALOR TOTAL LIQ', 'UNIDADE', 'UNI', 'UN', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'QUANT', 'Qtd.', 'PREÇO', 'Pr.Unit', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', 'DESC', 'DEC', 'TAXA', 'IVA']

				print ('facturaSupplier')
				print (facturaSupplier_tmp)
				for fsup in facturaSupplier_tmp:
					print ('2 - TEXTOOOOOOaaaa *********')
					print (fsup.strip())

					print ('00000000')
					print ('TEXTO LINHA: ', fsup)
					for fi in en_palavras_fim_item:
						print ('HEADRE ',fsup.strip().upper())
						print ('fi ', fi.upper())
						if fi.upper() in fsup.strip().upper():
							fim_items = True

					if fsup.strip == "ITEM CODE DESCRIPTION QUANTITY —_ UNIT PRICE TOTAL":
						frappe.throw(porra)

					if not fsup.strip().startswith('SN:'):
						print ('conta PALAVRAS HEADER ', contapalavras_header)
						print ('fim items ', fim_items)
						if contapalavras_header >= 5 and not fim_items:
							#Now check if all Columns for Items are correct ....
							#ITEM| DESCRIPTION| QUANTITY| UNIT PRICE (EUR)| TOTAL PRICE (EUR)
							#this case must have 5 columns with TEXTs...
							totalgeral = ''
							precounitario = ''
							quantidade = ''


							for idx,cc in reversed(list(enumerate(fsup.split()))):
								print ('contapalavras_header ',contapalavras_header)
								print (len(fsup.split()))
								if len(fsup.split()) > contapalavras_header:
									print ('TEM ESPACO nos ITENS.... ')
									print ('TODO: IDX: last must be Number, LAST-1 also, last-2 also')
									print ('TODO: IDX: First can be Number or TEXT')
									print ('TODO: if NOT IDX: First and not LAST-1 and not LAST-2 than is DESCRIPTION')
									#frappe.throw(porra)
								elif len(fsup.split()) <= 3:
									print ('PODE SER SNs.... CANCEL QTD CHECK')
									break



								print ('===== FIRST IDX0 ======')
								print ('idx ',idx)
								print ('cc ',cc)

								#Check if cash
								print (re.match(cash_pattern,cc))
								print (cc.strip().isnumeric())
								#If startswith SN: skip


								if re.match(cash_pattern,cc):
									if not totalgeral:
										totalgeral = cc
									elif not precounitario:
										precounitario = cc
								elif contapalavras_header == 5:
									#Check QTD is a Number...
									if len(fsup.split()) > 1:
										print ('size fsup ',len(fsup.split()))
										#FIX 21-12-2022; Check if Currency Symbol...
										if cc.strip() == "€":
											if not supplierMoeda:
												supplierMoeda = 'EUR'

										elif not cc.strip().isnumeric():
											#Gera novamente o OCR bcs QTD is not a Number...
											if quantidade == '':
												#Qtd_isnot_number = True
												print ('QTD is not a NUMBER ', cc)
												#frappe.throw(porra)
												#break
												#SET to ZERO and after Rate and Total added divide to find the QTD
												quantidade = 0

								if cc.strip().isnumeric():
									if contapalavras_header == 5:
										#Assuming that 5 is Total, 4 is Unit Price, 3 is Qtd
										if not idx == 0:
											if not quantidade:
												quantidade = cc
												Qtd_isnot_number = False

							print ('totalgeral ', totalgeral)
							print ('precounitario ', precounitario)
							print ('quantidade ', quantidade)

							#if "0.15065" in fsup:
							#	frappe.throw(porra)

						#Must be last to avoid running on the top first and still on the HEADER TEXT...
						print ('VERIFICAR palavras_header_counted ', palavras_header_counted)
						if palavras_header_counted == False:
							palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
							palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE

							print ('terpalavras_header ', terpalavras_header)

							for pp in terpalavras_header:
								#Check if two words for HEADER like Valor Un or VALOR LIQ.
								print (fsup.strip().upper().replace('\xa0',' ') == pp.strip().upper())


								#if (pp.upper().strip() in fsup.strip().upper()) or (pp.upper().strip() == fsup.strip().upper()):
								#For some reason might have '\xa0' between...
								if (pp.upper().strip() in fsup.strip().upper()) or (fsup.strip().upper().replace('\xa0',' ') == pp.strip().upper()):
									print ('fsup.strip')
									print (fsup.strip().upper())
									print ('Palavaheader ', pp.upper())
									if pp.upper() == 'PREÇO' or pp.upper() == 'VALOR LIQ.' or pp.upper() == 'Pr.Unit'.upper():
										if palavra_preco:
											print ('NAO CONTA HEADER PRECO ', pp.upper())
										if palavra_total:
											print ('NAO CONTA HEADER TOTAL ', pp.upper())
										if pp.upper() == 'PREÇO':
											print (palavras_no_header)
											print ('palavra_preco ', palavra_preco)
											print ('+++++ AAAAAAAA +++++ ')

										#if ('UNIT PRICE' in palavras_no_header  or 'PRICE' in palavras_no_header or 'UNIT' in palavras_no_header) and (pp.upper() == 'UNIT PRICE' or pp.upper() == 'UNIT' or pp.upper() == 'PRICE'):
										if ('UNIT PRICE' in palavras_no_header  or 'PRICE' in palavras_no_header) and (pp.upper() == 'UNIT PRICE' or pp.upper() == 'PRICE'):
											palavra_preco = True
											print ('Skip Unit Price or Unit')

									print ('palavra_preco ', palavra_preco)
									print ('palavra_total ', palavra_total)
									if not palavra_preco or not palavra_total:
										#To avoid TOTAL AMOUNT and TOTAL being added
										if 'VALOR LIQ.' in palavras_no_header and pp.upper() == 'VALOR LIQ.':
											print ('SKIP VALOR LIQ.')
										elif 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and pp.upper() == 'CODE':
											print ('SKIP CODE and CODE NO')
										elif ('DESCRIPTION OF GOODS' in palavras_no_header  or 'DESCRIPTION' in palavras_no_header) and (pp.upper() == 'DESCRIPTION OF GOODS' or pp.upper() == 'DESCRIPTION'):
											print ('SKIP DESCRIPTION OF GOODS and DESCRIPTION')
											print (palavras_no_header)
										elif 'Descrição'.upper() in palavras_no_header and pp.upper() == 'Descrição'.upper():
											print ('SKIP Descrição')
											print (palavras_no_header)
										elif 'TAXA' in palavras_no_header and pp.upper() == 'TAXA':
											print ('SKIP TAXA')
											print (palavras_no_header)
										elif ('UNI' in palavras_no_header and pp.upper() == 'UNI') or ('UNI' in palavras_no_header and pp.upper() == 'UNIDADE'):
											print ('SKIP UNI or UNIDADE')
											print (palavras_no_header)


										else:
											if pp.upper() == 'PRICE':
												print ('palavras no header ', palavras_no_header)
											if not palavra_preco:
												#Check if word is... ex. cooperativa is not part of header but IVA exists inside....
												if len(pp.split()) == 1:
													adicionapalavra = False
													for ffsup in fsup.split():
														if ffsup.upper().strip() == pp.upper():
															adicionapalavra = True
												else:
													#Case Palavra do Header is a single one but has a space...  ex. 'VALOR LIQ.'
													adicionapalavra = True


												if adicionapalavra:
													#check if last HEADER
													if pp.upper() in palavras_no_header_ultimoHeader:
														adicionapalavra_FIM = True
														palavras_no_header.append(pp.upper())
														contapalavras_header += 1
														print ('pode contar HEADER ', pp.upper())
														print ('contapalavras_header ', contapalavras_header)
													elif adicionapalavra_FIM == False:
														palavras_no_header.append(pp.upper())
														contapalavras_header += 1
														print ('pode contar HEADER ', pp.upper())
														print ('contapalavras_header ', contapalavras_header)



											#frappe.throw(porra)

									#palavras_header_counted = True
									if contapalavras_header >= 9:
										#palavras_header_counted = True
										print ('palavras_header_counted SET FALSE')
										print ('contapalavras_header')
										print (palavras_no_header)
									if 'PICTURE' in palavras_no_header:
										palavras_header_counted = True
										print ('PICTURE no HEADER COUNT')
									#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
									if pp.upper() == 'UNIT PRICE (EUR)': # or pp.upper() == 'PRICE':
										palavra_preco = True
									if pp.upper() == 'TOTAL PRICE (EUR)' or pp.upper() == 'TOTAL AMOUNT':
										palavra_total = True
							if contapalavras_header <= 3:
								print ('Scan HEADER AGAIN22222.... ')
						if Qtd_isnot_number:
							break

				print ('palavras_no_header')
				print (palavras_no_header)
				print ('CALLED OCR_OCR_OCR 0000')
				print ('Qtd_isnot_number ',Qtd_isnot_number)
				#terpalavras_header_EN = terpalavras_header
				print ('PORTUGUES ocr_ocr_ocr =======')
				print ('en_scan ', en_scan)
				print ('terpalavras_header ',terpalavras_header)
				print ('palavras_no_header ',palavras_no_header)
				print ('filefinal ', filefinal)

				palavras_fim_item = ['Metodo de Pagamento','Incidência','Total Retenção']

				#FIX 27-09-2023; Will try aprender_OCR_v1 if items returns NONE
				ocrocrocr = ocr_ocr_ocr (facturaSupplier_tmp,palavras_fim_item,en_scan,supplierMoeda,terpalavras_header,palavras_no_header,filefinal,palavras_no_header_ultimoHeader)
				print ('ocrocrocr')
				print (ocrocrocr)
				print (len(ocrocrocr))
				print (ocrocrocr[7])	#ITEMS
				if len(ocrocrocr) == 8 and ocrocrocr[7] == []:
					return aprender_OCR_v1 (filefinal,"SCRAPE","COMPRAS")
				else:
					return ocrocrocr

				#return ocr_ocr_ocr (facturaSupplier_tmp,palavras_fim_item,en_scan,supplierMoeda,terpalavras_header,palavras_no_header,filefinal,palavras_no_header_ultimoHeader)

			frappe.throw(porra)
		'''
			TODO: Get MUST fields from OCR
		'''
		empresaSupplier = ''
		invoiceNumber = ''
		invoiceDate = ''
		moedaInvoice = ''
		supplierAddress = ''
		supplierEmail = ''
		supplierNIF = ''
		supplierCountry = ''
		supplierPais = ''


		#Items
		itemsSupplierInvoice = []
		itemCode = ''
		itemDescription = ''
		itemRate = ''
		itemQtd = ''
		itemTotal = ''
		itemIVA = ''

		tmpcountry = ''

		#FIX 22-01-2023;   CONTAINER NUMBER
		container_number = ''
		ceal_number = ''
		cartoon_qtd = ''

		#System Currencies ...
		moedassystem = []
		listamoedas = frappe.get_list("Currency",fields=['name'],ignore_permissions=True)
		for ll in listamoedas:
			moedassystem.append(ll.name)



		print ("facturaSupplier")
		#print (facturaSupplier)
		#print (type(facturaSupplier))
		#print (json.loads(facturaSupplier))
		print (facturaSupplier.split('\n'))
		#frappe.throw(porra)

		palavrasexiste_header = False

		tmp_sn = ''	#Will hold SNs

		en_contapalavras_header_banco = 0	#To avoid adding Bank details as SN

		countlines = 1

		fim_items = False

		facturaAGT = False

		for fsup in facturaSupplier.split('\n'):
			print ('=====INICIO =======')
			print (fsup)

			#Check if AGT Invoices
			if "CONTRIBUINTE FISCAL DETALHES DO CLIENTE" in fsup.strip():
				print ('invoiceNumber ', invoiceNumber)
				if "FTM" in invoiceNumber:
					facturaAGT = True

			#FIX 14-12-2022
			for fi in en_palavras_fim_item:
				if fi.upper() in fsup.strip().upper():
					fim_items = True
					#frappe.throw(porra)


			if fsup.strip() != None and fsup.strip() != "":
				if not empresaSupplier:
					'''
					EVITA palavras:
						Original
						2!Via
						2ºVia
					'''
					evitapalavras =['Original','2!Via','2ºVia','Duplicado']
					palavraexiste = False
					for ff in fsup.split(' '):
						#print (ff)
						if ff in evitapalavras:
							#print ('TEM palavra ', ff)
							palavraexiste = True
					if palavraexiste == False:
						#print (fsup)
						#print ('Pode ser NOME DA EMPRESA')
						#Remove if startswith /
						if fsup.strip().startswith('/'):
							empresaSupplier = fsup.strip()[1:]
						else:
							empresaSupplier = fsup.strip()

						#Check if startsWith Customer Name... skip
						if fsup.strip().startswith('Customer Name:'):
							empresaSupplier = ''

					#Check online for Company.... only twice
					if empresaSupplier:
						print ('Verificar Empresa Online')
						procuraonline = False
						if en_scan:
							en_paraempresa_terpalavras = ['TRADING','TR LLC','LLC','L.L.C']
							for tp in en_paraempresa_terpalavras:
								if tp in fsup.upper():
									procuraonline = True
									break
							if procuraonline:
								#FIX 22-01-2023; Remove Expoter:/Exporter:
								fsup_tmp = fsup.replace('Expoter:','').replace('Exporter:','')
								empresa = search_company_online(fsup_tmp)
							else:
								empresa = 'INVALIDO'

						else:
							#For Angola
							empresa = empresaSupplier
							#TODO: if NIF check NIF and get Company name...

						if empresa == 'INVALIDO':
							empresaSupplier = ''
						else:
							print ('RESULTADO Empresa Online')
							print (empresa)
							removerpalavras =['|','Facebook']
							tmpempresa = ''

							for ee in empresa:
								if not ":" in ee:
									for rr in removerpalavras:
										if not tmpempresa:
											if rr == "|":
												print ('poder ser country')
												tmpempresa = ee[:ee.find('|')]
												tmpcountry = ee[ee.find('|')+1:ee.find('-')-1]
											else:
												tmpempresa = ee.replace(rr,'')
										else:
											tmpempresa1 = tmpempresa.replace(rr,'')
											tmpempresa = tmpempresa1
									#Stay with First or Second record from google search...
									break
							if tmpempresa:
								print ('tmpempresa ',tmpempresa)
								print ('tmpcountry ', tmpcountry)
								if tmpempresa.strip().endswith('-'):
									empresaSupplier = tmpempresa.strip()[0:len(tmpempresa.strip())-1]
								else:
									empresaSupplier = tmpempresa.strip()
								if tmpcountry:
									if tmpcountry.upper().strip() == "DUBAI":
										supplierPais = 'United Arab Emirates'

						#frappe.throw(porra)
				if not supplierAddress:
					'''
					TER palavras:
						RUA, AVENIDA
					'''
					if tmpcountry.upper().strip() != "DUBAI":
						if empresaSupplier:
							terpalavras = ['RUA', 'AVENIDA']
							ADDRpalavraexiste = False
							for ff in fsup.split(' '):
								#print (ff)
								if ff in terpalavras:
									#print ('TEM palavra ', ff)
									ADDRpalavraexiste = True
							if ADDRpalavraexiste:
								supplierAddress = fsup.strip()

				if not supplierEmail:
					if "EMAIL:" in fsup.upper():
						#print ('Ainda por fazer....')
						supplierEmail = 'Ainda por fazer....'
				if not supplierNIF:
					if not en_scan:
						if "NIF" in fsup.upper() or "NIF:" in fsup.upper():
							supplierNIF = fsup.replace('NIF:','').replace('NIF','').strip()
							print ('CHECK NIF....ANGOLA1')
							if "NIFE do Adquirente:".upper() in fsup.upper() or "NIF do Adquirente:".upper() in fsup.upper():
								#AGT tem Nif Origem e nif DESTINO
								if "NIFE do Adquirente:".upper() in fsup.upper():
									niforigem = fsup[fsup.find('NIF:')+4:fsup.find('NIFE')].strip()
									#FIX 22-09-2023
									tmp_supplierNIF = niforigem.replace('NIF:','').replace('NIF','').strip()
									print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
									if re.match(nif_pattern,tmp_supplierNIF.strip()):
										supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
										niforigem = supplierNIF

									nifvalido = validar_nif (niforigem)
									print (nifvalido)
									if nifvalido and nifvalido[2]:
										print ('Empresa CORRECTA ', nifvalido[2])
										empresaSupplier = nifvalido[2]
										supplierNIF = nifvalido[0]

									#Check if is for Destiny company!!!!
									nifdestino = fsup[fsup.find('Adquirente:')+11:].strip()

							else:
								nifvalido = validar_nif (supplierNIF)
								print (nifvalido)
								if nifvalido and nifvalido[2]:
									print ('Empresa CORRECTA ', nifvalido[2])
									empresaSupplier = nifvalido[2]
					elif 'TRN :' in fsup.upper().strip():
						print ('TRN aqui....')
						if not supplierNIF:
							supplierNIF = fsup[fsup.upper().find('TRN :')+5:].strip()
							#FIX 22-09-2023
							tmp_supplierNIF = supplierNIF.replace('NIF:','').replace('NIF','').strip()
							print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
							if re.match(nif_pattern,tmp_supplierNIF.strip()):
								supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
								#niforigem = supplierNIF
								nifvalido = validar_nif (supplierNIF)
								print (nifvalido)
								if nifvalido and nifvalido[2]:
									print ('Empresa CORRECTA1 ', nifvalido[2])
									empresaSupplier = nifvalido[2]
									supplierNIF = nifvalido[0]

				if not supplierMoeda:
					terpalavras = ['Moeda','AOA','AKZ','KZ']
					#TODO: List of Currencies to see if on the Document to be OCR..

					Moedapalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Moedapalavraexiste = True
					if Moedapalavraexiste:
						#Check for AOA and AKZ first...
						if "AOA" in fsup.strip() or "AKZ" in fsup.strip() or "KZ" in fsup.strip():
							supplierMoeda = 'KZ'
						else:
							supplierMoeda = fsup.strip().replace('Moeda:','').replace('Moeda','').strip()
							#TODO: Remove CAMBIO and Numbers if exist on the same line...
					else:
						#Check words on doc if any on the list...
						#FIX 23-12-2022
						for mm in moedassystem:
							if mm.upper() != "ALL":
								tmpmoeda = ' ' + mm.upper() + ' '
								if tmpmoeda.upper() in fsup.upper():
									print ('TEM MOEDA NA FACTURA...')
									print (mm.upper())
									print ('tmpmoeda ',tmpmoeda.upper())
									print (fsup.strip().upper())
									supplierMoeda = tmpmoeda.upper().strip().replace(':','')

				if not invoiceDate:
					print ('invoiceDate')
					terpalavras = ['Data Doc.','Data Doc','Invoice Date:','Invoice Date','DATE:','Date']
					Datepalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Datepalavraexiste = True
					if Datepalavraexiste:
						#Loop thro terpalavras
						for tt in terpalavras:
							if fsup.strip().find(tt) != -1:
								invoiceDate1 = fsup.strip()[fsup.strip().find(tt):]
								invoiceDate = invoiceDate1.replace(tt,'').strip()
								break
						print (invoiceDate)
					else:
						#Check if has DATE on fsup
						matches = re.finditer(date_pattern,fsup, re.MULTILINE)
						for matchNum, match in enumerate(matches, start=1):
							print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
							if match.group():
								print('TEM DATA.... ',match.group())
								invoiceDate = match.group()


				if not invoiceNumber:
					#Search for PP FT FR
					#seriesDocs_pattern = r"^([P][P]|[F][T]|[F][R]|[F][T][M])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}|([P][P]|[F][T]|[F][R])\s.{1,4}\/\d{1,5}"
					#FIX 05-01-2023; Included FTM from AGT site
					#seriesDocs_pattern = r"^([F][T][M]|[P][P]|[F][T]|[F][R]).{1}\s\d{1}[a-zA-Z].{1}[0-9]{4}\/.{1,4}|([P][P]|[F][T]|[F][R])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}"
					seriesDocs_pattern = r"^([F][T][M]|[P][P]|[F][T]|[F][R]).{1}\s\d{1}[a-zA-Z].{1}[0-9]{4}\/.{1,4}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}|([P][P]|[F][T]|[F][R])\s.{1,4}\/\d{1,5}"
					#print (re.match(seriesDocs_pattern,fsup.upper().strip()))
					if re.match(seriesDocs_pattern,fsup.upper().strip()):
						invoiceNumber = fsup.upper().strip()
					else:
						if "FT" in fsup.upper().strip() or "PP" in fsup.upper().strip() or "FR" in fsup.upper().strip() or "FTM" in fsup.upper().strip():
							if "FT" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FT'):]
							elif "PP" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('PP'):]
							elif "FR" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FR'):]
							elif "FTM" in fsup.upper().strip():
								#FIX 05-01-2023; Factura do portal da AGT
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FTM'):]

							#print ('tmpseries ',tmpseries)
							#print (re.match(seriesDocs_pattern,tmpseries))
							if re.match(seriesDocs_pattern,tmpseries):
								#Match series
								invoiceNumber = tmpseries
							#frappe.throw(porra)

					#Case Doc is in EN and not from Angola
					terpalavras = ['Invoice No:','Invoice No','INVOICE NUMBER']
					if not invoiceNumber:
						for tt in terpalavras:
							print ('Factura ', tt.upper())
							print (fsup.upper().strip())
							if fsup.upper().strip().find(tt.upper()) != -1:
								invoiceNumber = fsup.upper().strip()[fsup.upper().strip().find(tt.upper()):].replace(tt.upper(),'').replace(':','').strip()
								print ('fac ', invoiceNumber)

				#CONTAINER NUMBER
				if not container_number:
					print ('Container Number')
					terpalavras = ['CONTAINER NUMBER:','CONTAINER NUMBER']
					Containerpalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Containerpalavraexiste = True
					if Containerpalavraexiste:
						#Loop thro terpalavras
						for tt in terpalavras:
							if fsup.strip().find(tt) != -1:
								containernumber_tmp = fsup.strip()[fsup.strip().find(tt):]
								#invoiceDate = invoiceDate1.replace(tt,'').strip()
								break
						print (containernumber_tmp)
						container_number = containernumber_tmp
				if not ceal_number:
					print ('Ceal Number or Seal Number')
					terpalavras = ['CEAL NAMBER','CEAL NUMBER']
					Cealpalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Cealpalavraexiste = True
					if Cealpalavraexiste:
						#Loop thro terpalavras
						for tt in terpalavras:
							if fsup.strip().find(tt) != -1:
								cealnumber_tmp = fsup.strip()[fsup.strip().find(tt):]
								#invoiceDate = invoiceDate1.replace(tt,'').strip()
								break
						print (cealnumber_tmp)
						ceal_number = cealnumber_tmp


				if not itemsSupplierInvoice and fim_items == False:
					#Items
					itemsSupplierInvoice = []
					contaLinhas = ''
					itemCode = ''
					itemDescription = ''
					itemRate = ''
					itemQtd = ''
					itemTotal = ''
					itemIVA = ''

					tmprate = ''
					tmpamount = ''

					'''
					TER palavras Para saber que ITEM TABLES DESCRIPTION:
						UN, UNIDADE, CAIXA, CX, Artigo, Descrição, Qtd., Pr.Unit, Cód. Artigo, V.Líquido
					'''
					contapalavras_header = 0

					en_palavras_banco = ['BANK','ACCOUNT']




					#palavrasexiste_header = False
					if en_scan:
						for pp in terpalavras_header_EN:
							if pp.upper() in fsup.strip().upper():
								contapalavras_header += 1
						for pp1 in en_palavras_banco:
							if pp1.upper() in fsup.strip().upper():
								en_contapalavras_header_banco += 1

					else:
						for pp in terpalavras_header:
							#print ('tamho ',len(fsup.strip()))
							#print ('pp ', pp)
							print (len(fsup.strip()) - fsup.strip().upper().find(pp.upper()))
							if len(fsup.strip()) - fsup.strip().upper().find(pp.upper()) <= 5:
								print ('ULTIMO HEADER')
								print ('pp ', pp)
								#frappe.throw(porra)

							if pp.upper() in fsup.strip().upper():
								contapalavras_header += 1
							#if "%Imp." == pp:
							#	if "%Imp." in fsup.strip():
							#		print ('posicao')
							#		print (fsup.strip().upper().find(pp.upper()))
							#		frappe.throw(porra)
					'''
					TER palavras Para saber que ITEM TABLES:
						UN, UNIDADE, CAIXA, CX
					'''

					terpalavras_item = ['UN', 'UNIDADE', 'CAIXA', 'CX']
					palavraexiste_item = False

					primeiroRegisto = True	#To break creating description with SN
					avoidADDING = False	#When SN or Chassis not add because they are single LINE

					#if "JTGCBAB8906725029" in fsup:
					print ('palavrasexiste_header ',palavrasexiste_header)
					print ('palavraexiste_item ',palavraexiste_item)
					if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1 and en_scan:
						print ('TO SCAN the SN or Chassis')
						palavraexiste_item = True
					#elif len(fsup.strip()) >= 2 and fsup.strip().isnumeric():
					#	#Case Numbers only and has more 3 chars with no DOT or COMMA
					#	if fsup.strip().find('.') == -1 and fsup.strip().find(',') == -1:
					#		print ('Not Currency... might be SERIAL NUMBER')
					#		print (fsup.strip())
					#		palavraexiste_item = True
					#		#frappe.throw(porra)

					#Case above is for Single SN or Chassis
					#This will check len for each if 15 or more each
					#JTFBV71J8B044454

					sao_sn = True
					print ('sao_SN palavraexiste_item ', palavraexiste_item)
					print ('en_contapalavras_header_banco ',en_contapalavras_header_banco)

					evitapalavras_telefone = [ 'Telef.', 'Telef. 244', 'Telef. +244']
					#email_pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
					#FIX 21-12-2022
					email_pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$"

					evitatelefone_items = False
					for telf in evitapalavras_telefone:
						if telf in fsup.strip():
							evitatelefone_items = True
						print ('EMAIL ')
						print ('fsup.strip() ', fsup.strip())
						#print (re.match(email_pattern,fsup.strip()))
					print ('evitatelefone_items ',evitatelefone_items)

					if not evitatelefone_items:
						if not palavraexiste_item:
							#To avoid having twice the SN
							if palavrasexiste_header:
								for cc in fsup.split():
									print ('cc ',cc)
									print ('cc ',cc.strip())
									print ('EMAIL0 ')
									if "@" in cc.strip():
										print (re.match(email_pattern,cc.strip()))
									#FIX 23-12-2022; If starts with SN:
									if cc.startswith('SN:') and not "@" in cc.strip():
										#Save all and break
										tmp_sn = fsup.strip()
										print ('VERIFICAR SE TODOS SAO SNs.... ')
										break
									#FIX 21-12-2022
									if not 'SN:' in cc and not "@" in cc.strip(): # re.match(email_pattern,cc.strip()):
										print ('LEN ', len(cc))
										if len(cc) >= 15:
											#sao_sn = True
											print ('SAO SNs')
											tmp_sn += ' ' + cc.strip()

											#21-12-2022; Check if are SN or just the Description
											retornadescricao = retorna_descricao(fsup.strip())
											print ('retornadescricao ',retornadescricao)
											print ('TESTE if is DESCRIPTION ONLY... might be SERIAL NUMBER')
											print (cc.strip())
											if retornadescricao.strip().find(cc.strip()) != -1:
												print ('FOR NOW REMOVE tmp_sn...')
												tmp_sn = ''

										elif len(cc.strip()) >= 3 and cc.strip().isnumeric():
											#Case Numbers only and has more 3 chars with no DOT or COMMA
											if cc.strip().find('.') == -1 and cc.strip().find(',') == -1:
												#To avoid Bank details as SN
												if en_contapalavras_header_banco >=2:
													print ('Bank details... NOT TO BE ENTERED AS SN')
													tmp_sn = ''
													tmpdescricao = ''
													#en_contapalavras_header_banco = 0
													palavrasexiste_header = False
												else:
													#Avoid NIF
													if not "NIF:" in fsup.strip():
														retornadescricao = retorna_descricao(fsup.strip())
														print ('retornadescricao ',retornadescricao)
														print ('0000 Not Currency... might be SERIAL NUMBER')
														print (cc.strip())

														#Check if Code No exists in Headers...
														if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
															print ('NOT SERIAL NUMBER but ITEM CODE...')
														else:
															#FIX 23-12-2022; Check if Code on start and not SN
															if retornadescricao.find(cc.strip()) > 0:
																tmp_sn += ' ' + cc.strip()

															#FIX: Find a way to get from last column to identify Total, Price, Qtd or
															#Total, VAT, Price, Qtd
															print ('If len 5 means Item, description, quantity, unit price, total price ')
															print (len(palavras_no_header))
															print (palavras_no_header)
															#Check if last 3 ones are numbers...
															tmp_totalprice = 0
															tmp_unitprice = 0
															tmp_qtd = 0
															if len(palavras_no_header) == 5:
																for idx_tmp,cc_tmp in reversed(list(enumerate(fsup.split()))):
																	#Check if cash
																	print (re.match(cash_pattern,cc_tmp))
																	print (cc_tmp.strip().isnumeric())
																	if re.match(cash_pattern,cc_tmp):
																		if not tmp_totalprice:
																			tmp_totalprice = cc_tmp
																		elif not tmp_unitprice:
																			tmp_unitprice = cc_tmp
																	if cc_tmp.strip().isnumeric():
																		if not tmp_qtd:
																			tmp_qtd = cc_tmp.strip()
																			if tmp_sn.strip() == tmp_qtd:
																				print ('REMOVE tmp_sn bcs is same as Qtd')
																				print ('tmp_sn ',tmp_sn)
																				print ('tmp_qtd ', tmp_qtd)
																				tmp_sn = ''
																				break



												#frappe.throw(porra)

										else:
											sao_sn = False

					print ('tmp_sn ',tmp_sn)
					#if "SN: JTFBV71J8B044454 JTFBV71J8B044601 JTFBV71J8B044616" in fsup:
					#	frappe.throw(porra)
					tmp_sn_added = False

					print ("palavrasexiste_header ",palavrasexiste_header)

					if palavrasexiste_header:
						#Tem HEADER entao ve os ITENS...
						for pp in terpalavras_item:
							if pp in fsup.strip():
								#IS an ITEMS so add
								palavraexiste_item = True

						#Check if previous was a Number... ERROR OCR so do Plus 1 as this is First Col or Chars...
						if len(filtered_divs['ITEM']) > 1:
							tmpitemCode = ''
							print ('Check if previous was a Number... ERROR OCR so do Plus 1 as this is First Col or Chars... ')
							print (filtered_divs['ITEM'][len(filtered_divs['ITEM'])-1])
							if filtered_divs['ITEM'][len(filtered_divs['ITEM'])-1].isnumeric():
								if not fsup.strip()[0:1].isnumeric():
									tmpitemCode = str(int(filtered_divs['ITEM'][len(filtered_divs['ITEM'])-1]) + 1)
									print ('tmpitemCode ',tmpitemCode)
									palavraexiste_item = True
									#frappe.throw(porra)

						#Check if startswith a NUMBER...
						print ('XXXpalavraexiste_item ',palavraexiste_item)
						print (fsup.strip()[0:1].isnumeric())
						if "CODE" in palavras_no_header and tmp_sn.startswith('SN:'):
							print ('Caso tenha CODE or CODE NO and tmp_sn')
							print ('Caso tenha CODE or CODE NO and tmp_sn')
							#if "CODE" in palavras_no_header and tmp_sn.startswith('SN:'):
							print ('ANTES ', filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
							filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' ' + tmp_sn
							print ('DEPOIS ', filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
							tmp_sn = ''

						elif palavraexiste_item or fsup.strip()[0:1].isnumeric():
							#Check if tmp_sn and add on previous ITEM and clear
							if tmp_sn !='' and fsup.strip()[0:1].isnumeric():
								retornadescricao = retorna_descricao(fsup.strip())
								print ('retornadescricao ',retornadescricao)
								if not tmp_sn in retornadescricao:
									print (len(filtered_divs['DESCRIPTION']))
									if len(filtered_divs['DESCRIPTION']) > 1:
										print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])

									print ('If len 6 means Item, description, quantity, unit price, total price ')
									print (len(palavras_no_header))
									#Check if last 3 ones are numbers...

									if len(filtered_divs['DESCRIPTION']) > 1:
										filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' SN: ' + tmp_sn
									else:
										print ('PARA REVER DESCRIPTION.....')
										print (filtered_divs['DESCRIPTION'])
										filtered_divs['DESCRIPTION'] += ' SN: ' + tmp_sn
									tmp_sn = ''
									print ('ADDED SNs to DESCRIPTION...')
									print ('ADDED SNs to DESCRIPTION...')
									tmp_sn_added = True
								else:
									tmp_sn = ''

							#Check if First is Numbers... so is a Counter
							if fsup.strip()[0:1].isnumeric():
								contaLinhas = fsup.strip()[0:1]
							#if EN; testing to start from TOTAL, PRICE, QTD in order to prices and Qtd correct
							tmpdescricao = ''
							if en_scan:
								cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'

								for idx,cc in reversed(list(enumerate(fsup.split()))):
									print ('===== IDX0 ======')
									print ('idx ',idx)
									print ('cc ',cc)

									#Check if cash
									print (re.match(cash_pattern,cc))
									print (cc.strip().isnumeric())

									#If last(first) is not Numeric; No longer ITEMs...
									#if primeiroRegisto == False:
									#	palavrasexiste_header = False
									#	break

									#More than 1 can be Items...
									print ('fsup.strip().split() ', fsup.strip().split())
									print ('len(fsup.strip().split()) ', len(fsup.strip().split()))
									print ('palavras_no_header ', palavras_no_header)

									if len(fsup.strip().split()) > 1:
										if re.match(cash_pattern,cc):
											if not itemTotal:
												itemTotal = cc.strip()
											elif not itemRate:
												#Check if has VAT
												if 'VAT' in palavras_no_header and not itemIVA:
													itemIVA = cc.strip()
													print ('aqui add itemIVA')
												elif 'PRICE' in palavras_no_header and 'AMOUNT' in palavras_no_header and 'VAT' in palavras_no_header and ('TOTAL AMOUNT' in palavras_no_header or '‘TOTAL AMOUNT' in palavras_no_header):
													if not tmpamount:
														tmpamount = cc.strip()
														print ('aqui add tmpamount')
													elif not itemRate:
														itemRate = cc.strip()
														print ('aqui add itemRate II')

												else:
													itemRate = cc.strip()
													print ('aqui add itemRate')
											primeiroRegisto = False
										elif cc.strip().isnumeric():
											#Qtd
											print ('Qtd ',itemQtd)
											if not itemQtd and itemQtd == '':
												itemQtd = cc.strip()

											#FIX 21-12-2022; Check if SN is same as QTD
											print ('len description')
											print (len(filtered_divs['DESCRIPTION']))
											if len(filtered_divs['DESCRIPTION']) > 1:
												print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
											#filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' SN: ' + tmp_sn


											#Check if CODE NO in Headers...
											if 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and idx == 1:
												print ('itemCode ', itemCode)
												if not itemCode:
													itemCode = cc.strip()

										else:
											print('String...')
											if idx == 0:
												#First is a Number but OCR was wrong... FIX
												print ('First is a Number but OCR was wrong... FIX ')
												print ('itemCode ',itemCode)
												print ('tmpitemCode ',tmpitemCode)
												if not itemCode and tmpitemCode:
													itemCode = tmpitemCode
											elif not itemQtd and not tmpdescricao:
												itemQtd = 0	#Has ERROR WHEN OCR so no QTD as number returned...

											else:
												#Check if header Code No exists... and if idx 1
												if idx == 1 and 'CODE NO' in palavras_no_header:
													print ('itemCode ', itemCode)
													if not itemCode:
														itemCode = cc.strip().replace('©','').replace('«','')
													#frappe.throw(porra)
												else:
													#Avoid -
													if cc.strip() == '-' or cc.strip() == '—':
														print (' SKIP adding this —')
													else:
														tmpdescricao = cc.strip() + ' ' + tmpdescricao
									if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
										#Add SN JSTJPB7CX5N4008215 to Description
										#tmpdescricao = tmpdescricao + 'SN: ' + cc
										print ('adiciona SN: por algum motivo...')
										tmpdescricao = ' SN: ' + cc
										palavraexiste_item = False
									elif len(fsup.strip().split()) == 1:
										#Has SN bu might be with a DOT the SN
										if not tmp_sn_added:
											print ('Has SN bu might be with a DOT the SN')
											print (fsup.strip())

											#Check if CODE NO in header.. not SERIAL NUMBER!
											if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
												print ('NOT ADDING SN: bcs might not be; is Description continuation...')
												tmpdescricao = ' ' + cc
											else:
												tmpdescricao = ' SN: ' + cc
											palavraexiste_item = False
											itemCode = ''
									elif 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
										if not itemCode and idx == 1:
											#Check if has DOT !!!!
											if cc.find('.') != -1:
												itemCode = cc.strip().replace('(','')


									print ('tmpQtd ', itemQtd)
									print ('tmpdescricao ', tmpdescricao)
									print ('primeiroRegisto ',primeiroRegisto)
									print (len(fsup.split()))
									if idx == len(fsup.split())-1:
										print ('para')
										if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
											print('continua')
										elif len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1:
											print ('NUMERO SERIE.... ADD to DESCRIPTION')
										elif not re.match(cash_pattern,cc):
											tmpdescricao = ''
											avoidADDING = True
											print ('FEZ BREAK')
											break

							#frappe.throw(porra)
							if tmpdescricao:
								print (len(fsup.strip().split()))
								print ('split')
								print (fsup.strip().split())
								if (len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1) or (len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1):
									print (len(fsup.strip()))
									print (fsup.strip())
									print ('tmpdescricao')
									print ('tmpdescricao')
									print ('tmpdescricao')
									print ('tmpdescricao ',tmpdescricao)
									#Add to previous itemDescription
									print (filtered_divs['DESCRIPTION'])
									print (len(filtered_divs['DESCRIPTION']))
									print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
									if tmpdescricao not in filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1]:
										print ('TEM tmpdescricao')
										print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
										print (tmpdescricao)
										filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += tmpdescricao
										#frappe.throw(porra)

									tmpdescricao = ''
									print ('----')
									print (filtered_divs['DESCRIPTION'])

									#frappe.throw(porra)
								else:
									#itemDescription = tmpdescricao
									print ('t1 ', retorna_descricao(fsup.strip()))
									itemDescription = retorna_descricao(fsup.strip())
									print (itemDescription)

									#Check if Code NO exists...
									if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
										if itemCode:
											tmpdescricao = itemDescription.replace(itemCode,'').strip()
											if tmpdescricao.startswith('-') or tmpdescricao.startswith('—'):
												itemDescription = tmpdescricao[1:]
											else:
												itemDescription = tmpdescricao
									print ('itemDesciption depois ', itemDescription)

							#avoidADDING = False	#When SN or Chassis not add because they are single LINE
							for ii in fsup.split(' '):
								print ('----')
								print ('ii ', ii)
								print (re.match(cash_pattern,ii))
								print (ii.strip().isnumeric())

								if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1 and en_scan:
									print ('AVOID ADDING... was only SN')
									avoidADDING = True
								elif len(fsup.strip().split()) == 1 and en_scan:
									print ('ALERT:AVOID ADDING... was only SN')
									avoidADDING = True

								else:
									#Itemcode
									if not itemCode:
										itemCode = ii.strip()
										print ('itemcode ',itemCode)

									elif not itemDescription:
										#itemDescription = ii.strip()
										print ('t2 ', fsup.strip())
										print ('t2 ', retorna_descricao(fsup.strip()))
										itemDescription = retorna_descricao(fsup.strip()) #.replace(str(itemQtd),''))
										print (itemDescription)

										#Check if same as TOTAL LINE ... Might be Serial Numbers or just one with SPACEs...
										print (fsup.strip())
										if itemDescription == fsup.strip():
											if not "(" in fsup.strip() and not "|" in fsup.strip():
												print ('IGUAl... IS Serial Number')
												#frappe.throw(porra)

									elif itemCode and itemDescription and not ii.strip().isnumeric():
										print ('tem itemcode e itemDescription')
										if not en_scan:
											#Deal with Numbers
											if not ii.find(',') != -1: #re.match(cash_pattern,ii): # and ii.find(',') != -1:
												#Deal with Unit
												if not ii.strip() in terpalavras_item:
													#itemDescription = itemDescription + " " + ii.strip()
													print ('t3 ', retorna_descricao(fsup.strip()))
													itemDescription = retorna_descricao(fsup.strip()) #.replace(itemQtd,''))
													print (itemDescription)
									if ii.strip().isnumeric():
										print ('number')
										if not itemQtd and itemQtd == '':
											print ('check itemcode ', itemCode)
											itemQtd = ii.strip()
										elif not itemRate:
											print ('tamanho')
											print (len(ii))

											if len(ii) == 2:
												tmprate = ii.strip()
											else:
												if tmprate != '':
													itemRate = str(tmprate) + str(ii.strip())
													print ('aqui0 ',itemRate)
												else:
													itemRate = ii.strip()
													tmprate = ''
													print ('OUaqui1 ',itemRate)
										elif not itemTotal:
											print ('aqui total')
											itemTotal = ii.strip()
										elif not itemIVA:
											if not en_scan:
												itemIVA = ii.strip()
									elif re.match(cash_pattern,ii) and ii.find(',') != -1:
										#Tem Decimais...
										print ('Tem Decimais...')
										if not itemQtd and itemQtd == '':
											itemQtd = ii.strip()
										elif not itemRate:
											if tmprate != '':
												itemRate = str(tmprate) + str(ii.strip())
												tmprate = ''
												print ('aqui ',itemRate)
											else:
												itemRate = ii.strip()
												tmprate = ''
												print ('OUaqui ',itemRate)

											#itemRate = ii.strip()
										elif not itemTotal:
											print ('OUaqui total')
											if ii.strip() != '0,00':
												itemTotal = ii.strip()
										elif not itemIVA:
											if not en_scan:
												itemIVA = ii.strip()

							print ('avoidADDING ',avoidADDING)
							if avoidADDING:
								#Check if same as TOTAL LINE ... Might be Serial Numbers or just one with SPACEs...
								print (fsup.strip())
								if itemDescription == fsup.strip():
									if not "(" in fsup.strip() and not "|" in fsup.strip() and not ":" in fsup.strip() and not "BAIRRO" in fsup.strip():
										print ('IGUAl... IS Serial Number')
										print ('TO THINK BETTER how to DETECT SERIAL NUMBERS....')
										#frappe.throw(porra)

							print ('CORRIGIR QUNATIDADES ZERO')
							print ('itemQtd ',itemQtd)
							if itemQtd != '' and itemQtd == 0:
								if itemTotal and itemRate:
									print ('itemQtd ',itemQtd)
									print ('itemRate ',itemRate)
									print ('itemTotal ',itemTotal)
									print (str(float(itemTotal.replace(',','')) / float(itemRate.replace(',',''))))

									if float(itemTotal.replace(',','')) / float(itemRate.replace(',','')) == 0:
										itemQtd = str(1)
									else:
										itemQtd = str(float(itemTotal.replace(',','')) / float(itemRate.replace(',','')))
								#frappe.throw(porra)


							print ('Items')
							print ('contaLinhas ',contaLinhas)
							print ('countlines ',countlines)
							print ('itemCode ',itemCode)
							print ('itemDescription ',itemDescription.replace(str(itemQtd),''))
							print ('itemQtd ',itemQtd)
							print ('itemRate ',itemRate)
							print ('itemTotal ',itemTotal)
							print ('itemIVA ',itemIVA)

							print ('itemDescriptionXXXXXX ', itemDescription)

							print ('avoidADDING ',avoidADDING)

							#frappe.throw(porra)
							if not avoidADDING:
								filtered_divs['COUNTER'].append(countlines)
								filtered_divs['ITEM'].append(itemCode)
								#FIX 22-12-2022; removed itemQtd
								if len(itemCode) != len(itemDescription) and len(itemCode) > 5:
									#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').replace(str(itemQtd),'').replace(itemCode,'').strip())
									filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').replace(itemCode,'').strip())
								else:
									#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').replace(str(itemQtd),'').strip())
									filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').strip())
								filtered_divs['QUANTITY'].append(itemQtd)
								filtered_divs['RATE'].append(itemRate)
								filtered_divs['TOTAL'].append(itemTotal)
								filtered_divs['IVA'].append(itemIVA)
								countlines += 1
								print ('Added COUNTER,ITEM,DESCRIPTION,RATE,TOTAL,IVA')
							#frappe.throw(porra)

					#frappe.throw(porra)
					#if tmp_sn == 'SN: 5549545':
					#	frappe.throw(porra)

					print ('contapalavras_header ',contapalavras_header)
					if contapalavras_header >= 5:
						palavrasexiste_header = True

					#if "527041" in fsup.strip() or "KS 527041 K" in fsup.strip():
					#	frappe.throw(porra)

					if "244 913400191 923323564 pjpa65@gmail.com" in fsup.strip() or "244 913400191 923323564" in fsup.strip():
						frappe.throw(porra)

					#if "1HZ O/G" in fsup.strip():
					#	frappe.throw(porra)

					#if "4680569" in fsup.strip(): # "5417178772" in fsup.strip(): #if "0.15065" in fsup.strip():
					#	print (filtered_divs['DESCRIPTION'])
						#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').strip())
					#	if palavrasexiste_header:
					#		print ('supplierNIF ', supplierNIF)
					#	frappe.throw(porra)

				#if itemsSupplierInvoice:
				#Already has list of list... to Append

		print ('empresaSupplier ',empresaSupplier)
		print ('supplierAddress ',supplierAddress)
		print ('email ', supplierEmail)
		print ('supplierNIF ', supplierNIF)
		print ('invoiceNumber ', invoiceNumber)

		print ('!!!!!!!!!!')
		#print (filtered_divs)
		print ('!!!!!!!!!!')
		data = []
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['IVA'], filtered_divs['COUNTER']):
			if 'ITEM' in row[0]:
				continue

			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5], 'COUNTER': row[6]}
			data.append(data_row)

		print('Supplier ', empresaSupplier)
		print ('supplieraddre ', supplierAddress)
		print ('supplierNIF ', supplierNIF)

		print ('supplierPais ', supplierPais)

		if supplierMoeda == 'AOA' or supplierMoeda == 'AKZ' or supplierMoeda == 'KZ':
			empresaPais = 'Angola'
		else:
			if not supplierPais:
				empresaPais = 'DESCONHECIDO'
			else:
				empresaPais = supplierPais
			if supplierMoeda:
				print ('supplierMoeda ',supplierMoeda)
				if supplierMoeda == "EUR":
					if not supplierPais:
						empresaPais = 'Belgium' #DEFAULT for EUR currency
				else:
					#FIX 31-12-2022; if KZ/AOA
					print (supplierMoeda.upper().strip() == 'KZ')
					print (supplierMoeda.upper().strip())
					print (supplierMoeda.upper().replace(':',''))
					if supplierMoeda.upper().replace(':','').strip() == 'KZ' or supplierMoeda.upper().replace(':','').strip() == 'AOA':
						tmppais =pycountry.countries.get(alpha_3='AGO')
					else:
						tmppais =pycountry.countries.get(numeric=pycountry.currencies.get(alpha_3=supplierMoeda.upper().replace(':','').strip()).numeric)
					print ('tmppais ',tmppais.name)
					empresaPais = tmppais.name

		print ('empresaPais ', empresaPais)

		print('Invoice', invoiceNumber)
		print('Date ', invoiceDate)
		print('Moeda ', supplierMoeda)


		pprint(data)
		stop_time = time.monotonic()
		print(round(stop_time-start_time, 2), "seconds")

		return (empresaSupplier,invoiceNumber,invoiceDate,supplierMoeda,supplierAddress,supplierNIF,empresaPais,data)


def aprender_OCR_v1(data,action = "SCRAPE",tipodoctype = None):
	'''
	Last modified: 27-09-2023
	Using to Train or LEARN OCR from PDF files not configurated on the System....
	'''
	start_time = time.monotonic()

	#FIX 22-09-2023; Added words to HEADER
	#terpalavras_header = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qtd.', 'Pr.Unit', 'Cód. Artigo', 'V.Líquido', 'V. Líquido']
	terpalavras_header = ['Total c/ IVA','Totalc/IVA', 'TOTAL ', 'VALOR UN', 'VALOR TOTAL LIQ', 'PREÇO', 'Pr. Unitário', 'Pr.Unit', 'UNIDADE', 'UNI ', 'UN ', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qotd.', 'QUANT', 'Qtd.', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', ' DESC. ', ' DESC ', ' DEC ', ' TAXA ', ' IVA ', ' VA ', ' Arm. ']
	terpalavras_header_EN = ['DESCRIPTION', 'Y/M', 'COLOR', 'FUEL',' QTY', 'ITEM', 'QUANTITY', 'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL']

	#FIX 27-09-2023; Added date format YYYY-MM-DD
	#date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])\s([1-9]{1,2}):([1-9]{2}):[0-9]{2}\s(AM|PM)|([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])\s([1-9]{1,2}):([1-9]{2}):[0-9]{2}\s(AM|PM)|([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])|([1-9][0-9][0-9][0-9])\-([0-9][0-9])\-([0-9][0-9])'
	#cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)'
	cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'
	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}
	filtered_divs = {'COUNTER': [], 'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

	#FIX 26-09-2023
	palavras_no_header = []


	if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
		filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)

	else:
		filefinal = data

	#If no results... than change to OCR
	if ".pdf" in filefinal:

		print ('FAZ OCR COMPRAS 111')
		print ('FAZ OCR COMPRAS 111')
		print ('=================')
		en_scan = False
		#Check if Document is in PT or ENG...
		#FIX 27-07-2023
		#en_terpalavras = ['PROFORMA INVOICE','SALES INVOICE','INVOICE']
		en_terpalavras = ['PROFORMA INVOICE','PROFORMA INVOCIE','SALES INVOICE','INVOICE','QUOTATION']

		#en_palavras_fim_item = ['INCIDENCE','VAT','TAX']
		#FIX 27-07-2023
		en_palavras_fim_item = ['INCIDENCE','VAT', 'TAX','UNTAXED AMOUNT']
		fim_items = False

		pt_palavras_fim_item = ['Processado por programa validado'.upper()]

		contapalavras_header = 0

		#Check first if EN or PT Document...
		import pdfquery
		tmppdf  = pdfquery.PDFQuery(filefinal)
		tmppdf.load(0)
		for engpalav in en_terpalavras:
			print ('engpalav ',engpalav)
			#print (pdf.pq(':contains("{}")'.format(engpalav)).text())
			tt = tmppdf.pq(':contains("{}")'.format(engpalav)).text()
			if tt:
				#print (tt)
				en_scan = True
				print ('TEM INGLES')

		#FIX 27-07-2023; Convert to UPPER to check for HEADER
		if not en_scan:
			facturaSupplier = tmppdf.pq.text().upper()
			for engpalav in en_terpalavras:
				if engpalav in facturaSupplier:
					print ('FIX 27-07-2023')
					print ('DOC is ENGLISH....SCAN again ')
					en_scan = True

		if not en_scan:
			facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'por',250)
			print (facturaSupplier.split('\n'))

			for engpalav in en_terpalavras:
				if engpalav in facturaSupplier:
					print ('DOC is ENGLISH....SCAN again ')
					en_scan = True

		if en_scan:
			#Scan in ENGLISH
			facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'eng',270) #180) #150) retuns line counter but not the rest...
			#Check if needs Scan lower 260 to get all Numbers
			palavras_header_counted = False
			Qtd_isnot_number = False	#To control if needs to OCR again as 260

			for fsup in facturaSupplier.split('\n'):
				print ('TEXTO LINHA: ', fsup)
				for fi in en_palavras_fim_item:
					if fi in fsup.strip():
						fim_items = True

				if contapalavras_header >= 5 and not fim_items:
					#Now check if all Columns for Items are correct ....
					#ITEM| DESCRIPTION| QUANTITY| UNIT PRICE (EUR)| TOTAL PRICE (EUR)
					#this case must have 5 columns with TEXTs...
					totalgeral = ''
					precounitario = ''
					quantidade = ''


					for idx,cc in reversed(list(enumerate(fsup.split()))):
						print ('contapalavras_header ',contapalavras_header)
						print (len(fsup.split()))
						if len(fsup.split()) > contapalavras_header:
							print ('TEM ESPACO nos ITENS.... ')
							print ('TODO: IDX: last must be Number, LAST-1 also, last-2 also')
							print ('TODO: IDX: First can be Number or TEXT')
							print ('TODO: if NOT IDX: First and not LAST-1 and not LAST-2 than is DESCRIPTION')
							#frappe.throw(porra)


						print ('===== FIRST IDX ======')
						print ('idx ',idx)
						print ('cc ',cc)

						#Check if cash
						print (re.match(cash_pattern,cc))
						print (cc.strip().isnumeric())

						if re.match(cash_pattern,cc):
							if not totalgeral:
								totalgeral = cc
							elif not precounitario:
								precounitario = cc
						elif contapalavras_header == 5:
							#Check QTD is a Number...
							if len(fsup.split()) > 1:
								if not cc.strip().isnumeric():
									#Gera novamente o OCR bcs QTD is not a Number...
									if quantidade == '':
										Qtd_isnot_number = True
										print ('QTD is not a NUMBER ', cc)
										break

						if cc.strip().isnumeric():
							if contapalavras_header == 5:
								#Assuming that 5 is Total, 4 is Unit Price, 3 is Qtd
								if not idx == 0:
									if not quantidade:
										quantidade = cc
										Qtd_isnot_number = False

					print ('totalgeral ', totalgeral)
					print ('precounitario ', precounitario)
					print ('quantidade ', quantidade)

					#if "0.15065" in fsup:
					#	frappe.throw(porra)

				#Must be last to avoid running on the top first and still on the HEADER TEXT...
				if palavras_header_counted == False:
					palavra_total = False #TO AVOID counting 'TOTAL PRICE (EUR)' and again TOTAL
					palavra_preco = False #TO AVOID counting 'UNIT PRICE (EUR)' and again UNIT PRICE
					for pp in terpalavras_header_EN:
						if pp.upper() in fsup.strip().upper():
							if pp.upper() == 'UNIT PRICE' or pp.upper() == 'TOTAL':
								if palavra_preco:
									print ('NAO CONTA HEADER ', pp.upper())
								if palavra_total:
									print ('NAO CONTA HEADER ', pp.upper())
							if not palavra_preco or not palavra_total:
								contapalavras_header += 1
								print ('pode contar HEADER')

							palavras_header_counted = True
							#'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL'
							if pp.upper() == 'UNIT PRICE (EUR)':
								palavra_preco = True
							if pp.upper() == 'TOTAL PRICE (EUR)':
								palavra_total = True

				if Qtd_isnot_number:
					break

			if Qtd_isnot_number:
				print ('HOW TO do 250 and if something missing after OCR do in 260 to COMPLETE WITH THE MISSING INFO... INITIALLY WILL ITEMS')
				print ('OCR ocr_pytesseract again with 260DPI')
				facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'eng',260)
			else:
				print ('PODE CONTINUAR....')


			print (facturaSupplier.split('\n'))
			#frappe.throw(porra)
		'''
			TODO: Get MUST fields from OCR
		'''
		empresaSupplier = ''
		invoiceNumber = ''
		invoiceDate = ''
		moedaInvoice = ''
		supplierAddress = ''
		supplierEmail = ''
		supplierNIF = ''
		supplierCountry = ''
		supplierMoeda = ''

		#Items
		itemsSupplierInvoice = []
		itemCode = ''
		itemDescription = ''
		itemRate = ''
		itemQtd = ''
		itemTotal = ''
		itemIVA = ''

		tmpcountry = ''


		#System Currencies ...
		moedassystem = []
		listamoedas = frappe.get_list("Currency",fields=['name'],ignore_permissions=True)
		for ll in listamoedas:
			moedassystem.append(ll.name)



		print ("facturaSupplier")
		#print (facturaSupplier)
		#print (type(facturaSupplier))
		#print (json.loads(facturaSupplier))
		print (facturaSupplier.split('\n'))
		#frappe.throw(porra)

		palavrasexiste_header = False

		tmp_sn = ''	#Will hold SNs

		en_contapalavras_header_banco = 0	#To avoid adding Bank details as SN

		for fsup in facturaSupplier.split('\n'):
			print ('=====INI')
			print ('terpalavras_header ',terpalavras_header)
			print (fsup)

			if fsup.strip() != None and fsup.strip() != "":
				if not empresaSupplier:
					'''
					EVITA palavras:
						Original
						2!Via
						2ºVia
					'''
					evitapalavras =['Original','2!Via','2ºVia','Duplicado']
					palavraexiste = False
					for ff in fsup.split(' '):
						#print (ff)
						if ff in evitapalavras:
							#print ('TEM palavra ', ff)
							palavraexiste = True
					if palavraexiste == False:
						#print (fsup)
						#print ('Pode ser NOME DA EMPRESA')
						#Remove if startswith /
						if fsup.strip().startswith('/'):
							empresaSupplier = fsup.strip()[1:]
						else:
							empresaSupplier = fsup.strip()
					#Check online for Company.... only twice
					if empresaSupplier:
						print ('Verificar Empresa Online')
						procuraonline = False
						if en_scan:
							en_paraempresa_terpalavras = ['TRADING','LLC']
							for tp in en_paraempresa_terpalavras:
								if tp in fsup:
									procuraonline = True
									break
							if procuraonline:
								empresa = search_company_online(fsup)
							else:
								empresa = 'INVALIDO'

						else:
							#For Angola
							empresa = empresaSupplier
							#TODO: if NIF check NIF and get Company name...

						if empresa == 'INVALIDO':
							empresaSupplier = ''

						else:
							print ('RESULTADO Empresa Online')
							print (empresa)
							removerpalavras =['|','Facebook']
							tmpempresa = ''

							for ee in empresa:
								if not ":" in ee:
									for rr in removerpalavras:
										if not tmpempresa:
											if rr == "|":
												print ('poder ser country')
												tmpempresa = ee[:ee.find('|')]
												tmpcountry = ee[ee.find('|')+1:ee.find('-')-1]
											else:
												tmpempresa = ee.replace(rr,'')
										else:
											tmpempresa1 = tmpempresa.replace(rr,'')
											tmpempresa = tmpempresa1
									#Stay with First or Second record from google search...
									break
							if tmpempresa:
								print ('tmpempresa ',tmpempresa)
								print ('tmpcountry ', tmpcountry)
								if tmpempresa.strip().endswith('-'):
									empresaSupplier = tmpempresa.strip()[0:len(tmpempresa.strip())-1]
								else:
									empresaSupplier = tmpempresa.strip()
								if tmpcountry:
									if tmpcountry.upper().strip() == "DUBAI":
										supplierPais = 'United Arab Emirates'
						#frappe.throw(porra)
				if not supplierAddress:
					'''
					TER palavras:
						RUA, AVENIDA
					'''
					if tmpcountry.upper().strip() != "DUBAI":
						if empresaSupplier:
							terpalavras = ['RUA', 'AVENIDA','BELAS BUSINESS']
							ADDRpalavraexiste = False
							for ff in fsup.split(' '):
								#print (ff)
								if ff in terpalavras:
									#print ('TEM palavra ', ff)
									ADDRpalavraexiste = True
							if ADDRpalavraexiste:
								#FIX 22-09-2023; if starts with BELAS...
								if "BELAS BUSINESS" in fsup.strip():
									supplierAddress = fsup.strip().upper()[fsup.strip().upper().find("BELAS BUSINESS"):]
								else:
									supplierAddress = fsup.strip()

				if not supplierEmail:
					if "EMAIL:" in fsup.upper():
						#print ('Ainda por fazer....')
						supplierEmail = 'Ainda por fazer....'
				if not supplierNIF:
					if not en_scan:
						if "NIF" in fsup.upper() or "NIF:" in fsup.upper():
							#FIX 22-09-2023
							tmp_supplierNIF = fsup.replace('NIF:','').replace('NIF','').strip()
							print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
							if re.match(nif_pattern,tmp_supplierNIF.strip()):
								supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
							print ('CHECK NIF....ANGOLA2')
							nifvalido = validar_nif (supplierNIF)
							print (nifvalido)
							if nifvalido and nifvalido[2]:
								print ('Empresa CORRECTA2 ', nifvalido[2])
								if nifvalido != "NIF INVALIDO!!!" and nifvalido != "NIF INVALIDO":
									empresaSupplier = nifvalido[2]
								else:
									empresaSupplier = "NIF INVALIDO NAO CONSEGUI OBTER FORNECEDOR!"
				if not supplierMoeda:
					terpalavras = ['Moeda','AOA','AKZ']
					#TODO: List of Currencies to see if on the Document to be OCR..
					print ('Ver se tem MOEDA AKZ/AOA')

					Moedapalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Moedapalavraexiste = True
					if Moedapalavraexiste:
						#Check for AOA and AKZ first...
						if "AOA" in fsup.strip():
							supplierMoeda = 'KZ'
						elif "AKZ" in fsup.strip():
							supplierMoeda = 'KZ'
						else:
							#FIX 22-09-2023
							if "Moeda:" in fsup.strip():
								supplierMoeda = fsup.strip().replace('Moeda','')
								print ('aqui MOEDA ADDED')
							#TODO: Remove CAMBIO and Numbers if exist on the same line...
					else:
						#Check words on doc if any on the list...
						for mm in moedassystem:
							tmpmoeda = ' ' + mm.upper()
							if tmpmoeda.upper() in fsup.upper():
								print ('TEM MOEDA NA FACTURA...')
								print (mm.upper())
								print ('tmpmoeda ',tmpmoeda.upper())
								print (fsup.strip().upper())
								supplierMoeda = tmpmoeda.upper().strip()

				if not invoiceDate:
					print ('invoiceDate')
					#FIX 27-09-2023; Added Data
					terpalavras = ['Data Doc.','Data Doc','Invoice Date:','Invoice Date', ' Data ']
					Datepalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Datepalavraexiste = True
					if Datepalavraexiste:
						#Loop thro terpalavras
						for tt in terpalavras:
							if fsup.strip().find(tt) != -1:
								invoiceDate1 = fsup.strip()[fsup.strip().find(tt):]
								invoiceDate = invoiceDate1.replace(tt,'').strip()
								break
						print ('aqui invoiceDate')
						print (invoiceDate)
					else:
						#Check if has DATE on fsup
						print ('Check if has DATE on fsup')
						oldinvoicedata = ""
						matches = re.finditer(date_pattern,fsup, re.MULTILINE)
						for matchNum, match in enumerate(matches, start=1):
							print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
							if match.group():
								print('TEM DATA.... ',match.group())
								#FIX 27-09-2023
								if oldinvoicedata == "":
									oldinvoicedata = match.group()
								else:
									if oldinvoicedata <= match.group():
										oldinvoicedata = match.group()
										invoiceDate = match.group()
									elif oldinvoicedata > match.group():
										invoiceDate = match.group()
								#invoiceDate = match.group()


				if not invoiceNumber:
					#Search for PP FT FR
					seriesDocs_pattern = r"^([P][P]|[F][T]|[F][R])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}"
					#print (re.match(seriesDocs_pattern,fsup.upper().strip()))
					if re.match(seriesDocs_pattern,fsup.upper().strip()):
						invoiceNumber = fsup.upper().strip()
					else:
						if "FT" in fsup.upper().strip() or "PP" in fsup.upper().strip() or "FR" in fsup.upper().strip():
							if "FT" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FT'):]
							elif "PP" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('PP'):]
							elif "FR" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FR'):]

							#print ('tmpseries ',tmpseries)
							#print (re.match(seriesDocs_pattern,tmpseries))
							if re.match(seriesDocs_pattern,tmpseries):
								#Match series
								invoiceNumber = tmpseries
							#frappe.throw(porra)

					#Case Doc is in EN and not from Angola
					terpalavras = ['Invoice No:','Invoice No', 'Fatura/Recibo ']
					if not invoiceNumber:
						for tt in terpalavras:
							print ('Factura00 ', tt.upper())
							print (fsup.upper().strip())
							if fsup.upper().strip().find(tt.upper()) != -1:
								invoiceNumber = fsup.upper().strip()[fsup.upper().strip().find(tt.upper()):].replace(tt.upper(),'').replace(':','').replace('ORIGINAL','').strip()
								print ('fac ', invoiceNumber)


				if not itemsSupplierInvoice:
					#Items
					itemsSupplierInvoice = []
					contaLinhas = ''
					itemCode = ''
					itemDescription = ''
					itemRate = ''
					itemQtd = ''
					itemTotal = ''
					itemIVA = ''

					tmprate = ''

					itemTotalcIVA = ''

					'''
					TER palavras Para saber que ITEM TABLES DESCRIPTION:
						UN, UNIDADE, CAIXA, CX, Artigo, Descrição, Qtd., Pr.Unit, Cód. Artigo, V.Líquido
					'''
					contapalavras_header = 0

					en_palavras_banco = ['BANK','ACCOUNT']




					#palavrasexiste_header = False
					if en_scan:
						for pp in terpalavras_header_EN:
							if pp.upper() in fsup.strip().upper():
								contapalavras_header += 1
						for pp1 in en_palavras_banco:
							if pp1.upper() in fsup.strip().upper():
								en_contapalavras_header_banco += 1

					else:
						for pp in terpalavras_header:
							if pp.upper() in fsup.strip().upper():
								print ('Add on contapalavras_header')
								print (pp.upper())
								print (fsup.strip().upper())
								if not pp.upper() in palavras_no_header:
									contapalavras_header += 1
									palavras_no_header.append(pp.upper())

					'''
					TER palavras Para saber que ITEM TABLES:
						UN, UNIDADE, CAIXA, CX
					'''

					#FIX 27-09-2023; added Arm.
					terpalavras_item = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'ARM.']
					palavraexiste_item = False

					primeiroRegisto = True	#To break creating description with SN
					avoidADDING = False	#When SN or Chassis not add because they are single LINE

					#if "JTGCBAB8906725029" in fsup:
					print ('palavrasexiste_header ',palavrasexiste_header)
					print ('palavraexiste_item ',palavraexiste_item)
					if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1 and en_scan:
						print ('TO SCAN the SN or Chassis')
						palavraexiste_item = True
					#elif len(fsup.strip()) >= 2 and fsup.strip().isnumeric():
					#	#Case Numbers only and has more 3 chars with no DOT or COMMA
					#	if fsup.strip().find('.') == -1 and fsup.strip().find(',') == -1:
					#		print ('Not Currency... might be SERIAL NUMBER')
					#		print (fsup.strip())
					#		palavraexiste_item = True
					#		#frappe.throw(porra)

					#Case above is for Single SN or Chassis
					#This will check len for each if 15 or more each
					#JTFBV71J8B044454

					sao_sn = True
					print ('sao_SN palavraexiste_item ', palavraexiste_item)
					print ('en_contapalavras_header_banco ',en_contapalavras_header_banco)

					evitapalavras_telefone = [ 'Telef.', 'Telef. 244', 'Telef. +244']
					#email_pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
					#FIX 21-12-2022
					email_pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$"
					evitatelefone_items = False
					for telf in evitapalavras_telefone:
						if telf in fsup.strip():
							evitatelefone_items = True
						print ('EMAIL1 ')
						print ('fsup.strip() ', fsup.strip())
						#print (re.match(email_pattern,fsup.strip()))
					print ('evitatelefone_items ',evitatelefone_items)

					if not evitatelefone_items:
						if not palavraexiste_item:
							#To avoid having twice the SN
							if palavrasexiste_header:
								for cc in fsup.split():
									print ('cc ',cc)
									print ('cc.strip ',cc.strip())
									print ('EMAIL2 ')
									print (re.match(email_pattern,cc.strip()))

									if not 'SN:' in cc and not re.match(email_pattern,cc.strip()):
										print ('LEN ', len(cc))
										if len(cc) >= 15:
											#sao_sn = True
											print ('SAO SNs')
											tmp_sn += ' ' + cc.strip()
										elif len(cc.strip()) >= 3 and cc.strip().isnumeric():
											#Case Numbers only and has more 3 chars with no DOT or COMMA
											if cc.strip().find('.') == -1 and cc.strip().find(',') == -1:
												#To avoid Bank details as SN
												if en_contapalavras_header_banco >=2:
													print ('Bank details... NOT TO BE ENTERED AS SN')
													tmp_sn = ''
													tmpdescricao = ''
													#en_contapalavras_header_banco = 0
													palavrasexiste_header = False
												else:
													#Avoid NIF
													if not "NIF:" in fsup.strip():
														print ('Not Currency... might be SERIAL NUMBER')
														print (cc.strip())
														tmp_sn += ' ' + cc.strip()
												#frappe.throw(porra)

										else:
											sao_sn = False

					print ('tmp_sn ',tmp_sn)
					#if "SN: JTFBV71J8B044454 JTFBV71J8B044601 JTFBV71J8B044616" in fsup:
					#	frappe.throw(porra)
					tmp_sn_added = False

					#FIX 27-09-2023; for PT SCAN to avoid adding after ITEM TABLEs...
					for ppitemfim in pt_palavras_fim_item:
						print ('tem palavra fim item')
						print (ppitemfim)
						if ppitemfim in fsup.strip().upper():
							avoidADDING = True
					if avoidADDING:
						print ('STOP ADDING... NO MORE ITEMS')
						break

					if palavrasexiste_header:
						#Tem HEADER entao ve os ITENS...
						for pp in terpalavras_item:
							if pp in fsup.strip():
								#IS an ITEMS so add
								palavraexiste_item = True
						#Check if startswith a NUMBER...
						if palavraexiste_item or fsup.strip()[0:1].isnumeric():
							#Check if tmp_sn and add on previous ITEM and clear
							if tmp_sn !='' and fsup.strip()[0:1].isnumeric():
								#FIX 22-09-2023
								if len(filtered_divs['DESCRIPTION']) > 1:
									filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' SN: ' + tmp_sn
									tmp_sn = ''
									print ('ADDED SNs to DESCRIPTION...')
									print ('ADDED SNs to DESCRIPTION...')
									tmp_sn_added = True
								else:
									tmp_sn = ''
									tmp_sn_added = False

							#Check if First is Numbers... so is a Counter
							if fsup.strip()[0:1].isnumeric():
								#FIX 22-09-2023
								if fsup.strip()[:fsup.find(' ')].isnumeric() and len(fsup.strip()[:fsup.find(' ')]) >= 3:
									print ('Cannot be CONTALINAS... must be ITEMCODE/ARTIGO')
								else:
									contaLinhas = fsup.strip()[0:1]
							#if EN; testing to start from TOTAL, PRICE, QTD in order to prices and Qtd correct
							tmpdescricao = ''
							if en_scan:
								cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'

								for idx,cc in reversed(list(enumerate(fsup.split()))):
									print ('===== IDX ======')
									print ('idx ',idx)
									print ('cc ',cc)

									#Check if cash
									print (re.match(cash_pattern,cc))
									print (cc.strip().isnumeric())

									#If last(first) is not Numeric; No longer ITEMs...
									#if primeiroRegisto == False:
									#	palavrasexiste_header = False
									#	break

									#More than 1 can be Items...
									if len(fsup.strip().split()) > 1:
										if re.match(cash_pattern,cc):
											if not itemTotal:
												itemTotal = cc.strip()
											elif not itemRate:
												itemRate = cc.strip()
											primeiroRegisto = False
										elif cc.strip().isnumeric():
											#Qtd
											if not itemQtd:
												itemQtd = cc.strip()
										else:
											#String...
											tmpdescricao = cc.strip() + ' ' + tmpdescricao
									if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
										#Add SN JSTJPB7CX5N4008215 to Description
										#tmpdescricao = tmpdescricao + 'SN: ' + cc
										tmpdescricao = ' SN: ' + cc
										palavraexiste_item = False
									elif len(fsup.strip().split()) == 1:
										#Has SN bu might be with a DOT the SN
										if not tmp_sn_added:
											print ('Has SN bu might be with a DOT the SN')
											print (fsup.strip())
											tmpdescricao = ' SN: ' + cc
											palavraexiste_item = False
											itemCode = ''


									print ('tmpdescricao ', tmpdescricao)
									print ('primeiroRegisto ',primeiroRegisto)
									print (len(fsup.split()))
									if idx == len(fsup.split())-1:
										print ('para')
										if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
											print('continua')
										elif len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1:
											print ('NUMERO SERIE.... ADD to DESCRIPTION')
										elif not re.match(cash_pattern,cc):
											tmpdescricao = ''
											avoidADDING = True
											print ('FEZ BREAK')
											break
							else:
								#FIX 27-09-2023; IF PT SCAN
								print ('PT SCAN; REVERSE FSUP....')
								cash_pattern = r'^[-+]?(?:\d*\.\d+\,\d+)|(?:\d*\s\d+\,\d+)|(?:\d*\,\d+)'

								for idx,cc in reversed(list(enumerate(fsup.split()))):
									print ('===== IDX ======')
									print ('idx ',idx)
									print ('cc ',cc)

									#Check if cash
									print (re.match(cash_pattern,cc))
									print (cc.strip().isnumeric())

									#If last(first) is not Numeric; No longer ITEMs...
									#if primeiroRegisto == False:
									#	palavrasexiste_header = False
									#	break

									#More than 1 can be Items...
									if len(fsup.strip().split()) > 1:
										if re.match(cash_pattern,cc):
											print ('palavras_no_header ', palavras_no_header)
											if "TOTALC/IVA" in palavras_no_header and not itemTotalcIVA:
												if not itemTotalcIVA:
													itemTotalcIVA = cc.strip()
												print ('itemTotalcIVA itemTotalcIVA')

											elif not itemTotal:
												itemTotal = cc.strip()
											elif not itemRate:
												itemRate = cc.strip()
											primeiroRegisto = False
										elif "%" in cc.strip() and ("14" in cc.strip() or "7" in cc.strip() or "5" in cc.strip()):
											#IVA 14 / 7 / 5
											print ('TEM IVA NA LINHAS DO ITENS.... ', cc.strip())
											itemIVA = cc.strip()
										elif cc.strip().isnumeric():
											#Qtd
											if not itemQtd:
												itemQtd = cc.strip()
												#FIX 27-09-2023; Might be ZERO or price might be PT ex. 5 880,00 no DOT
												if itemRate == "0,00":
													#if "," in itemTotal
													itemRate = float(itemTotal.replace(',00','')) / int(itemQtd)


										else:
											#String...
											tmpdescricao = cc.strip() + ' ' + tmpdescricao
									if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
										#Add SN JSTJPB7CX5N4008215 to Description
										#tmpdescricao = tmpdescricao + 'SN: ' + cc
										tmpdescricao = ' SN: ' + cc
										palavraexiste_item = False
									elif len(fsup.strip().split()) == 1:
										#Has SN bu might be with a DOT the SN
										if not tmp_sn_added:
											print ('Has SN bu might be with a DOT the SN')
											print (fsup.strip())
											tmpdescricao = ' SN: ' + cc
											palavraexiste_item = False
											itemCode = ''


									print ('tmpdescricao ', tmpdescricao)
									print ('primeiroRegisto ',primeiroRegisto)
									print (len(fsup.split()))
									if idx == len(fsup.split())-1:
										print ('para')
										if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
											print('continua')
										elif len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1:
											print ('NUMERO SERIE.... ADD to DESCRIPTION')
										elif not re.match(cash_pattern,cc):
											tmpdescricao = ''
											avoidADDING = True
											print ('FEZ BREAK')
											break

							#frappe.throw(porra)
							if tmpdescricao:
								print (len(fsup.strip().split()))
								print ('split')
								print (fsup.strip().split())
								if (len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1) or (len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1):
									print (len(fsup.strip()))
									print (fsup.strip())
									print ('tmpdescricao')
									print ('tmpdescricao')
									print ('tmpdescricao')
									print ('tmpdescricao ',tmpdescricao)
									#Add to previous itemDescription
									print (filtered_divs['DESCRIPTION'])
									print (len(filtered_divs['DESCRIPTION']))
									print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
									if tmpdescricao not in filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1]:
										print ('TEM tmpdescricao')
										print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
										print (tmpdescricao)
										filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += tmpdescricao
										#frappe.throw(porra)

									tmpdescricao = ''
									print ('----')
									print (filtered_divs['DESCRIPTION'])

									#frappe.throw(porra)
								else:
									itemDescription = tmpdescricao

							#avoidADDING = False	#When SN or Chassis not add because they are single LINE
							for ii in fsup.split(' '):
								print ('----')
								print ('ii ', ii)
								print (re.match(cash_pattern,ii))
								print (ii.strip().isnumeric())

								if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1 and en_scan:
									print ('AVOID ADDING... was only SN')
									avoidADDING = True
								elif len(fsup.strip().split()) == 1 and en_scan:
									print ('ALERT:AVOID ADDING... was only SN')
									avoidADDING = True

								else:
									#Itemcode
									if not itemCode:
										itemCode = ii.strip()
										print ('itemcode ',itemCode)

									elif not itemDescription:
										itemDescription = ii.strip()
									elif itemCode and itemDescription and not ii.strip().isnumeric():
										if not en_scan:
											#Deal with Numbers
											if not ii.find(',') != -1: #re.match(cash_pattern,ii): # and ii.find(',') != -1:
												#Deal with Unit
												if not ii.strip() in terpalavras_item:
													itemDescription = itemDescription + " " + ii.strip()
									if ii.strip().isnumeric():
										print ('number')
										if not itemQtd:
											print ('check itemcode ', itemCode)
											itemQtd = ii.strip()
										elif not itemRate:
											print ('tamanho')
											print (len(ii))

											if len(ii) == 2:
												tmprate = ii.strip()
											else:
												if tmprate != '':
													itemRate = str(tmprate) + str(ii.strip())
													print ('aqui0 ',itemRate)
												else:
													itemRate = ii.strip()
													tmprate = ''
													print ('OUaqui1 ',itemRate)
										elif not itemTotal:
											print ('aqui total')
											itemTotal = ii.strip()
										elif not itemIVA:
											if not en_scan:
												itemIVA = ii.strip()
									elif re.match(cash_pattern,ii) and ii.find(',') != -1:
										#Tem Decimais...
										if not itemQtd:
											itemQtd = ii.strip()
										elif not itemRate:
											if tmprate != '':
												itemRate = str(tmprate) + str(ii.strip())
												tmprate = ''
												print ('aqui ',itemRate)
											else:
												itemRate = ii.strip()
												tmprate = ''
												print ('OUaqui ',itemRate)

											#itemRate = ii.strip()
										elif not itemTotal:
											print ('OUaqui total')
											if ii.strip() != '0,00':
												itemTotal = ii.strip()
										elif not itemIVA:
											if not en_scan:
												if not itemIVA:
													itemIVA = ii.strip()

							print ('Items')
							print ('contaLinhas ',contaLinhas)
							print ('itemCode ',itemCode)
							print ('itemDescription ',itemDescription)
							print ('itemQtd ',itemQtd)
							print ('itemRate ',itemRate)
							print ('itemTotal ',itemTotal)
							print ('itemIVA ',itemIVA)

							#frappe.throw(porra)
							if not avoidADDING:
								filtered_divs['COUNTER'].append(contaLinhas)
								filtered_divs['ITEM'].append(itemCode)
								filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').strip())
								filtered_divs['QUANTITY'].append(itemQtd)
								filtered_divs['RATE'].append(itemRate)
								filtered_divs['TOTAL'].append(itemTotal)
								filtered_divs['IVA'].append(itemIVA)

						#frappe.throw(porra)

					print ('contapalavras_header ',contapalavras_header)
					if contapalavras_header >= 5:
						palavrasexiste_header = True

					if "244 913400191 923323564 pjpa65@gmail.com" in fsup.strip() or "244 913400191 923323564" in fsup.strip():
						frappe.throw(porra)

					if "16 TD42 TURBO O/G" in fsup.strip():
						frappe.throw(porra)

					if "0.0298.0" in fsup.strip(): # "5417178772" in fsup.strip(): #if "0.15065" in fsup.strip():
					#	print (filtered_divs['DESCRIPTION'])
						#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').strip())
						if palavrasexiste_header:
							print ('supplierNIF ', supplierNIF)
						frappe.throw(porra)

				#if itemsSupplierInvoice:
				#Already has list of list... to Append

		print ('empresaSupplier ',empresaSupplier)
		print ('supplierAddress ',supplierAddress)
		print ('email ', supplierEmail)
		print ('supplierNIF ', supplierNIF)
		print ('invoiceNumber ', invoiceNumber)

		print ('!!!!!!!!!!')
		#print (filtered_divs)
		print ('!!!!!!!!!!')
		data = []
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['IVA'], filtered_divs['COUNTER']):
			if 'ITEM' in row[0]:
				continue

			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5], 'COUNTER': row[6]}
			data.append(data_row)

		print('Supplier ', empresaSupplier)
		print ('supplieraddre ', supplierAddress)
		print ('supplierNIF ', supplierNIF)
		if supplierMoeda == 'AOA' or supplierMoeda == 'AKZ' or supplierMoeda == 'KZ':
			empresaPais = 'Angola'
		else:
			empresaPais = 'DESCONHECIDO'
			if supplierMoeda:
				print ('supplierMoeda ',supplierMoeda)
				if supplierMoeda == "EUR":
					empresaPais = 'Belgium' #DEFAULT for EUR currency
				else:
					#FIX 31-12-2022; if KZ/AOA
					if supplierMoeda.upper().strip() == 'KZ' or supplierMoeda.upper().strip() == 'AOA':
						tmppais =pycountry.countries.get(alpha_3='AGO')
					else:
						tmppais =pycountry.countries.get(numeric=pycountry.currencies.get(alpha_3=supplierMoeda.strip()).numeric)

					print ('tmppais ',tmppais.name)
					empresaPais = tmppais.name

		print ('supplierPais ', empresaPais)

		print('Invoice', invoiceNumber)
		print('Date ', invoiceDate)
		print('Moeda ', supplierMoeda)


		pprint(data)
		stop_time = time.monotonic()
		print(round(stop_time-start_time, 2), "seconds")

		return (empresaSupplier,invoiceNumber,invoiceDate,supplierMoeda,supplierAddress,supplierNIF,empresaPais,data)


def search_company_online(empresa):

	# Import the beautifulsoup
	# and request libraries of python.
	#import requests
	#import bs4

	# Make two strings with default google search URL
	# 'https://google.com/search?q=' and
	# our customized search keyword.
	# Concatenate them
	start_time = time.monotonic()

	resultados = []
	if empresa:
		text= empresa #"I 1 TMJ EXPRESSO GENERAL TRADING LLC" # "c++ linear search program"
		url = 'https://google.com/search?q=' + text

		# Fetch the URL data using requests.get(url),
		# store it in a variable, request_result.
		request_result=requests.get( url )
		#print ('search_company_online')

		# Creating soup from the fetched request
		soup = bs4.BeautifulSoup(request_result.text,"html.parser")
		filter=soup.find_all("h3")
		#print ('RESULTADO SOUP')
		#print (soup)
		for i in range(0,len(filter)):
			#print(filter[i].get_text())
			resultados.append(filter[i].get_text())

		if resultados:
			stop_time = time.monotonic()
			print(round(stop_time-start_time, 2), "seconds")

			return resultados
		else:
			stop_time = time.monotonic()
			print(round(stop_time-start_time, 2), "seconds")

			return 'INVALIDO'

def validar_nif(nif):
	start_time = time.monotonic()
	if nif:
		print ('verifying... ', nif)
		#FIX 02-01-2023; if timeout tries again
		class TimeoutHTTPAdapter(HTTPAdapter):
			def __init__(self, *args, **kwargs):
				if "timeout" in kwargs:
					self.timeout = kwargs["timeout"]
					del kwargs["timeout"]
				else:
					self.timeout = 5   # or whatever default you want
				super().__init__(*args, **kwargs)
			def send(self, request, **kwargs):
				kwargs["timeout"] = self.timeout
				return super().send(request, **kwargs)

		'''
		NOT YET REQUIRED STILL USING THE OLD
		session = requests.Session()
		adapter = TimeoutHTTPAdapter(timeout=(3, 60), max_retries=Retry(total=2, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504]))
		session.mount("http://", adapter)
		session.mount("https://", adapter)
		start_time = time.monotonic()

		headers= {
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
		}
		site = "https://invoice.minfin.gov.ao/commonServer/common/taxpayer/get/" + str(nif.replace(':','').replace('.','').replace(',','').strip())
		print ('site ',site + '****')

		try:
			#r = session.get("http://httpbin.org/status/503")
			response = session.get(site,headers=headers,verify=False)
			#response = session.post(site1,headers=headers,files={'file': open(ficheiro,'rb')}) #.json()
			print ('response')
			print (response.json())
			frappe.throw(porra)

		except Exception as e:
			print(type(e))
			print(e)

		stop_time = time.monotonic()
		print(round(stop_time-start_time, 2), "seconds")
		response.close()
		session.close()
		'''

		try:
			response  = requests.get("https://invoice.minfin.gov.ao/commonServer/common/taxpayer/get/" + str(nif.replace(':','').replace('.','').replace(',','').strip()),verify=False, timeout=20)
			#check if Response is 502; Does not Exist the site...
			print ('response.status_code ',response.status_code)
			if response.status_code == 502:
				print ('Nao existe o SITE!!!!')
				return ('SITE EM BAIXO.')
			else:
				print ('Tem dados NIF....')
				data = response.json()
				print ('data')
				#print (data['success'])
				print (data)
				if 'status' in data:
					if data['status'] == 500:
						print ('Erro de Servidor!!!')
					elif 'sucess' in data:
						if data['success'] == False:
							print ('NIF INVALIDO!!!')
							return 'NIF INVALIDO'
						else:
							#Success
							nifvalido = data['data']['nif']
							regimeiva = ""
							print ('Valido')
							#verify Regime IVA
							#"regimeIva":"GNAD"
							if data['data']['regimeIva'] != "" and data['data']['regimeIva'] == "GNAD" :
								#GERAL
								regimeiva = 'Regime GERAL'
								print ('Regime GERAL')

							if data['data']['companyName']:
								return nifvalido, regimeiva, data['data']['companyName']
							else:
								return nifvalido, regimeiva, data['data']['nameAbb']



				elif 'success' in data:
					if data['success'] == False:
						print ('NIF INVALIDO!!!')
						return 'NIF INVALIDO'
					else:
						#Success
						nifvalido = data['data']['nif']
						regimeiva = ""
						print ('Valido')
						print ('data ', data)
						#verify Regime IVA
						#"regimeIva":"GNAD"
						if data['data']['regimeIva'] != "" and data['data']['regimeIva'] == "GNAD" :
							#GERAL
							regimeiva = 'Regime GERAL'
							print ('Regime GERAL')
						if data['data']['companyName']:
							return nifvalido, regimeiva, data['data']['companyName']
						else:
							return nifvalido, regimeiva, data['data']['nameAbb']

				else:
					#Success
					nifvalido = data['data']['nif']
					regimeiva = ""
					print ('Valido')
					#verify Regime IVA
					#"regimeIva":"GNAD"
					if data['data']['regimeIva'] != "" and data['data']['regimeIva'] == "GNAD" :
						#GERAL
						regimeiva = 'Regime GERAL'
						print ('Regime GERAL')

					if data['data']['companyName']:
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return nifvalido, regimeiva, data['data']['companyName']
					else:
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return nifvalido, regimeiva, data['data']['nameAbb']



		except requests.exceptions.ReadTimeout:
			print ('SEM LIGACAO.....')
			print ('SEM LIGACAO.....')
		except requests.exceptions.ConnectionError:
			print ('Connection refused.....')
			requests.status_code = "Connection refused"


def aprender_OCR_v2(data,action = "SCRAPE",tipodoctype = None):
	'''
	Last modified: 16-10-2022
	Using to Train or LEARN OCR from PDF files not configurated on the System....
	'''
	start_time = time.monotonic()

	empresaSupplier = ''
	invoiceNumber = ''
	invoiceDate = ''
	moedaInvoice = ''
	supplierAddress = ''
	supplierEmail = ''
	supplierNIF = ''
	supplierCountry = ''
	supplierMoeda = ''

	#Items
	itemsSupplierInvoice = []
	itemCode = ''
	itemDescription = ''
	itemRate = ''
	itemQtd = ''
	itemTotal = ''
	itemIVA = ''

	#terpalavras_header = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qtd.', 'Pr.Unit', 'Cód. Artigo', 'V.Líquido', 'V. Líquido']
	terpalavras_header = ['VALOR UN', 'VALOR TOTAL LIQ', 'UNIDADE', 'UNI', 'UN', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'QUANT', 'Qtd.', 'PREÇO', 'Pr.Unit', 'Codigo', 'Cód. Artigo', 'VALOR TOTAL', 'VALOR LIQ.', 'V.Líquido', 'V. Líquido','%Imp.', 'DESC', 'DEC', 'TAXA', 'IVA']
	terpalavras_header_EN = ['DESCRIPTION', 'Y/M', 'COLOR', 'FUEL',' QTY', 'ITEM', 'QUANTITY', 'UNIT PRICE (EUR)', 'TOTAL PRICE (EUR)', 'UNIT PRICE', 'TOTAL']

	en_palavras_banco = ['BANK','ACCOUNT']
	en_contapalavras_header_banco = 0

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])\s([1-9]{1,2}):([1-9]{2}):[0-9]{2}\s(AM|PM)|([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	#cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)'
	cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'

	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}
	filtered_divs = {'COUNTER': [], 'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}

	#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}

	contaLinhas = 1	#Conta as linhas de Itens....

	if os.path.isfile(frappe.get_site_path('public','files') + data.replace('/files','')):
		filefinal = frappe.get_site_path('public','files') + data.replace('/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)

	else:
		filefinal = data

	#If no results... than change to OCR
	if ".pdf" in filefinal:

		print ('FAZ OCR COMPRAS 222')
		print ('FAZ OCR COMPRAS 222')
		print ('=================')
		en_scan = False
		#Check if Document is in PT or ENG...
		#FIX 27-07-2023
		#en_terpalavras = ['PROFORMA INVOICE','SALES INVOICE','INVOICE']
		en_terpalavras = ['PROFORMA INVOICE','PROFORMA INVOCIE','SALES INVOICE','INVOICE','QUOTATION']

		#en_palavras_fim_item = ['INCIDENCE','VAT','TAX']
		#FIX 27-07-2023
		en_palavras_fim_item = ['INCIDENCE','VAT', 'TAX','UNTAXED AMOUNT']
		fim_items = False

		contapalavras_header = 0

		#Check first if EN or PT Document...
		import pdfquery
		tmppdf  = pdfquery.PDFQuery(filefinal)
		tmppdf.load(0)
		for engpalav in en_terpalavras:
			print ('engpalav ',engpalav)
			#print (pdf.pq(':contains("{}")'.format(engpalav)).text())
			tt = tmppdf.pq(':contains("{}")'.format(engpalav)).text()
			if tt:
				#print (tt)
				en_scan = True
				print ('TEM INGLES')
		if not en_scan:
			facturaSupplier = ocr_pytesseract (filefinal,"COMPRAS",'por',250)
			print (facturaSupplier.split('\n'))

			for engpalav in en_terpalavras:
				if engpalav in facturaSupplier:
					print ('DOC is ENGLISH....SCAN again ')
					en_scan = True

		if en_scan:
			#Scan in ENGLISH
			# Read PDF file and convert it to HTML
			output = StringIO()
			#with open('/tmp/SINV-2022-00021-1.pdf', 'rb') as pdf_file:
			with open(filefinal, 'rb') as pdf_file:
				extract_text_to_fp(pdf_file, output, laparams=LAParams(), output_type='html', codec=None)
			raw_html = output.getvalue()

			# Extract all DIV tags
			tree = html.fromstring(raw_html)
			divs = tree.xpath('.//div')


			#trying Bs
			root = html.tostring(tree)
			soup = bs(root)
			prettyHTML = soup.prettify()

			pagina = 1
			contador = 0
			for pp in prettyHTML.split('span'):
				#print (pp)
				pag = "Page " + str(pagina)
				if pag in pp:

					if pagina == 3:
						frappe.throw(porra)
					pagina += 1

				if "0.15065" in pp:
					frappe.throw(porra)
				print ('======')
				#print (pp[contador].strip('\n').upper())
				#print (pp.strip('\n').upper())
				for pp1 in pp.split('\n'):
					print ('!!!!!')
					print (pp1)
				#if pp1.split('<br/>'):
				#print (pp1.split(','))
				#print (pp.split('\n').split('<br/>'))
				#if pp.strip('\n').split('<br/>'):
				#print (pp.split('\n'))
				#print (len(pp.split('\n')))
				#pagina += 1
				contador += 1
				print ('contador ', contador)

			frappe.throw(porra)

			#print (divs)
			#frappe.throw(porra)

			# Sort and filter DIV tags
			#filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': []}

			temitems = False

			contador = 1


			oldIDXDescription = 0;

			for div in divs:
				# extract styles from a tag
				div_style = div.get('style')
				print ('+++++++++')
				print(div_style)
				print ('-------')
				print (div.text_content().strip('\n').upper())
				fsup = div.text_content().strip('\n').upper()
				print (len(fsup))
				print (fsup.split('\n'))
				print ('-------')
				#frappe.throw(porra)

				#if "4874059" in div.text_content().strip('\n').upper():
				#	tt = div.text_content().strip('\n').upper()
				#	print (len(tt))
				#	print (tt.split('\n'))


				if not invoiceNumber:
					#Search for PP FT FR
					seriesDocs_pattern = r"^([P][P]|[F][T]|[F][R])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}"
					#print (re.match(seriesDocs_pattern,fsup.upper().strip()))
					if re.match(seriesDocs_pattern,fsup.upper().strip()):
						invoiceNumber = fsup.upper().strip()
					else:
						if "FT" in fsup.upper().strip() or "PP" in fsup.upper().strip() or "FR" in fsup.upper().strip():
							if "FT" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FT'):]
							elif "PP" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('PP'):]
							elif "FR" in fsup.upper().strip():
								tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FR'):]

							#print ('tmpseries ',tmpseries)
							#print (re.match(seriesDocs_pattern,tmpseries))
							if re.match(seriesDocs_pattern,tmpseries):
								#Match series
								invoiceNumber = tmpseries
							#frappe.throw(porra)

					#Case Doc is in EN and not from Angola
					terpalavras = ['Invoice No:','Invoice No']
					if not invoiceNumber:
						for tt in terpalavras:
							print ('Factura ', tt.upper())
							print (fsup.upper().strip())
							if fsup.upper().strip().find(tt.upper()) != -1:
								invoiceNumber = fsup.upper().strip()[fsup.upper().strip().find(tt.upper()):].replace(tt.upper(),'').replace(':','').strip()
								print ('fac ', invoiceNumber)


				if not invoiceDate:
					print ('invoiceDate')
					terpalavras = ['Data Doc.','Data Doc','Invoice Date:','Invoice Date','Date']
					Datepalavraexiste = False
					for ff in terpalavras:
						if ff in fsup.strip():
							Datepalavraexiste = True
					if Datepalavraexiste:
						#Loop thro terpalavras
						for tt in terpalavras:
							if fsup.strip().find(tt) != -1:
								invoiceDate1 = fsup.strip()[fsup.strip().find(tt):]
								invoiceDate = invoiceDate1.replace(tt,'').strip()
								break
						print (invoiceDate)
					else:
						#Check if has DATE on fsup
						matches = re.finditer(date_pattern,fsup, re.MULTILINE)
						for matchNum, match in enumerate(matches, start=1):
							print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
							if match.group():
								print('TEM DATA.... ',match.group())
								invoiceDate = match.group()

				for pp in terpalavras_header_EN:

					if pp.upper() in fsup.strip().upper():
						contapalavras_header += 1
						print ('Ver HEADER')
						print (pp)
						print (fsup.strip())
						break

				for pp1 in en_palavras_banco:
					if pp1.upper() in fsup.strip().upper():
						en_contapalavras_header_banco += 1

				print ('contapalavras_header ',contapalavras_header)

				if contapalavras_header >= 5:
					#TEM Headers
					tem_headers = True
					#First will be ITEM
					#Itemcode

					filtered_divs['COUNTER'].append(contaLinhas)

					#Must be Numeric
					if fsup.strip().isnumeric():
						itemCode = fsup.strip()
						filtered_divs['ITEM'].append(itemCode)

					#if not itemCode:
					#	itemCode = fsup.strip()
					#	print ('itemcode ',itemCode)

					#elif not itemDescription:
					#	itemDescription = fsup.strip()


					contaLinhas += 1
				if contaLinhas == 17:
					frappe.throw(porra)
				if "5549545" in div.text_content().strip('\n').upper():
					#frappe.throw(porra)
					print ('aaaaa')

		print ('empresaSupplier ',empresaSupplier)
		print ('supplierAddress ',supplierAddress)
		print ('email ', supplierEmail)
		print ('supplierNIF ', supplierNIF)
		print ('invoiceNumber ', invoiceNumber)

		print ('!!!!!!!!!!')
		print ('COUNTER')
		print (filtered_divs['COUNTER'])
		print ('ITEM')
		print (filtered_divs['ITEM'])
		#print (filtered_divs)
		print ('!!!!!!!!!!')

		stop_time = time.monotonic()
		print(round(stop_time-start_time, 2), "seconds")

def retorna_descricao(fsup):
	'''
		Last Modified 18-10-2022
		To return DESCRICAO of the Item ....
	'''
	start_time = time.monotonic()

	tmpitemTotal = ''
	tmpitemCode = ''
	tmpitemQtd = ''
	tmpitemRate = ''
	tmpdescricao00 = ''

	cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)|(?:\d*\,\d+)'

	#fsup = '1 TOYOTA LAND CRUISER PICK UP 4 DOOR 4.5L - MODEL 2022 DSL 5 52,750.00 263,750.00'
	contapalavras_header = 5

	#print (len(fsup.split()))
	for idx,cc in reversed(list(enumerate(fsup.strip().split()))):
		#print ('idx ', idx)
		#print ('retorna_descricao ',cc)
		#print ('----')
		if len(fsup.strip().split()) > 1:
			if re.match(cash_pattern,cc):
				if not tmpitemTotal:
					tmpitemTotal = cc.strip()
				elif not tmpitemRate:
					tmpitemRate = cc.strip()
				elif not idx == 0:
					#print ('0:ADD TO DESCRICAO....')
					#print ('tmpitemQtd ',tmpitemQtd)
					if tmpitemQtd:
						tmpdescricao00 = cc.strip() + ' ' + tmpdescricao00
					#print (cc.strip())
				primeiroRegisto = False
				#print ('TESTE CASH... ', cc.strip())

			elif cc.strip().isnumeric():
				#Qtd
				if not tmpitemQtd:
					tmpitemQtd = cc.strip()
				else:
					if not idx == 0:
						#print ('ADD TO DESCRICAO....')
						tmpdescricao00 = cc.strip() + ' ' + tmpdescricao00
						#print (cc.strip())
			else:
				#String...
				#print ('DESCRICAO')
				#print ('Check for UN word')
				#print (cc.strip().upper() == 'UN')
				#print (cc.strip().upper())

				if cc.strip().upper() == 'UN':
					#Reset to NONE
					tmpdescricao00 = ''
				else:
					print ('not IDX 0 : ', idx)
					if not idx == 0:
						tmpdescricao00 = cc.strip() + ' ' + tmpdescricao00
		if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
			#Add SN JSTJPB7CX5N4008215 to Description
			#tmpdescricao = tmpdescricao + 'SN: ' + cc
			#print ('TEM SN....')
			tmpdescricao00 = ' SN: ' + cc
			palavraexiste_item = False
		elif len(fsup.strip().split()) == 1:
			#Has SN bu might be with a DOT the SN
			#if not tmp_sn_added:
				#print ('Has SN bu might be with a DOT the SN')
				#print (fsup.strip())
			tmpdescricao00 = ' SN: ' + cc
			palavraexiste_item = False
			tmpitemCode = ''


	#print ('itemCode ',tmpitemCode)
	#print ('itemQtd',tmpitemQtd)
	#print ('itemRate',tmpitemRate)
	#print ('itemTotal',tmpitemTotal)
	#print ('tmpdescricao',tmpdescricao00)

	stop_time = time.monotonic()
	print(round(stop_time-start_time, 2), "seconds")

	return tmpdescricao00.strip()

@frappe.whitelist(allow_guest=True)
def qrcode_decode(ficheiro):
	'''
		QRCode decode from image files....
	'''
	from pyzbar.pyzbar import ZBarSymbol


	start_time = time.monotonic()
	if ficheiro:
		if os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)
		elif os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')):
			filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = data

		print ('filefinal ',filefinal)
	if filefinal:
		#Look fro QRCODE on file
		decode(Image.open(filefinal), symbols=[ZBarSymbol.QRCODE])
	else:
		#Look fro QRCODE on file
		decode(Image.open('pyzbar/tests/qrcode.png'), symbols=[ZBarSymbol.QRCODE])

	if filefinal:
		#Decode from IMAGE
		from pyzbar.pyzbar import decode
		from PIL import Image
		decode(Image.open(filefinal))
	else:
		#Decode from IMAGE
		from pyzbar.pyzbar import decode
		from PIL import Image
		decode(Image.open('pyzbar/tests/code128.png'))

@frappe.whitelist(allow_guest=True)
def qrcode_scan_decode(ficheiro):
	'''
		QRCode Detect and decode from image files....
	'''
	import cv2


	start_time = time.monotonic()
	if ficheiro:
		if os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)
		elif os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')):
			filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = ficheiro

		print ('filefinal ',filefinal)

	if filefinal:
		img = cv2.imread(filefinal)
		detector = cv2.QRCodeDetector()
		data, bbox, s_qrcode = detector.detectAndDecode(img)
		if "portaldocontribuinte" in data:
			print ('Detected QRCODE LINK IN FILE....')
			#print (data)
			print ('verifying... ', data[data.find('?datNumber'):])
			try:
				#response.headers['Content-Type'] = 'application/json; charset=utf-8'
				headers= {
					'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
					'Content-Type': 'application/json; charset=utf-8',
				}

				response  = requests.get(data,headers=headers,verify=False, timeout=5)
				#check if Response is 502; Does not Exist the site...
				if response.status_code == 502:
					print ('Nao existe o SITE!!!!')
					return ('SITE EM BAIXO.')
				else:
					print ('Tem dados NIF....')
					#print (response.content)
					data = response.text
					#print ('data')
					#print (data['success'])
					#print (data)

					#Verify if PAGA
					numeroRecibo = ""
					datadePAGAMENTO = ""
					Contribuinte = ""
					nifContribuinte = ""
					valorPAGO = ""

					if data.find('encontra-se pago e registado no sistema') != -1:
						print ('Nota de Liquidacao ESTA PAGA...')
						from bs4 import BeautifulSoup
						soup = BeautifulSoup(response.content,'html.parser')
						sopa = soup.find(id='panelDARRP_content')
						elements = sopa.find_all("div",class_="form-group col-sm-6".split())
						print("\n".join("{} {}".format(el['class'], el.get_text()) for el in elements))
						for fsup in elements:
							print ('=====')
							texto = fsup.get_text()
							#print (texto)
							if "do Recibo de Pagamento" in texto:
								print ('Numbero do Recibo')
								print (texto[texto.rfind(':')+1:].strip())
								numeroRecibo = texto[texto.rfind(':')+1:].strip()
							elif "Data do Pagamento" in texto:
								print ('Data de Pagamento')
								print (texto[texto.rfind(':')+1:].strip())
								datadePAGAMENTO = texto[texto.rfind(':')+1:].strip()

							elif "Contribuinte" in texto:
								print ('Contribuinte')
								print (texto[texto.rfind(':')+1:].strip())
								Contribuinte = texto[texto.rfind(':')+1:].strip()

							elif "NIF" in texto:
								print ('NIF')
								print (texto[texto.rfind(':')+1:].strip())
								nifContribuinte = texto[texto.rfind(':')+1:].strip()
							elif "Valor" in texto:
								print ('Valor')
								print (texto[texto.rfind(':')+1:].strip())
								valorPAGO = texto[texto.rfind(':')+1:].strip()





			except requests.exceptions.ReadTimeout:
				print ('SEM LIGACAO.....')
				print ('SEM LIGACAO.....')
			except requests.exceptions.ConnectionError:
				print ('Connection refused.....')
				requests.status_code = "Connection refused"

			#Recibo de Pagamento RETENCAO NA FONTE
			if numeroRecibo and datadePAGAMENTO and nifContribuinte and valorPAGO:
				return {
					"tipoDocumento": "Recibo Pagamento Retencao",
					"numeroRecibo": numeroRecibo,
					"datadePAGAMENTO": datadePAGAMENTO,
					"Contribuinte": Contribuinte,
					"nifContribuinte": nifContribuinte,
					"valorPAGO": valorPAGO
				}

		return False

@frappe.whitelist(allow_guest=True)
def liquidacao_generica_tributo(ficheiro):
	'''
		OCR an image file to get either the QRCODE or the Referencia do Documento and SCAN ONLINE
		Last Modified: 20-10-2022
	'''
	import cv2
	import pytesseract

	start_time = time.monotonic()

	if os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/files','')):
		filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)
	elif os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')):
		filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)

	else:
		filefinal = data

	print ('filefinal ',filefinal)

	#ficheiro = '/home/frappe/frappe-bench/sites/tools.angolaerp.co.ao/public/files/Pagto teor.jpeg'
	img = cv2.imread(filefinal)

	# Adding custom options
	custom_config = r'--oem 3 --psm 6'
	textotemp = pytesseract.image_to_string(img, config=custom_config)

	print ('textotemp')
	print (textotemp)

	for tt in textotemp.split('\n'):
		#LIQUIDAGAO GENERICA DE TRIBUTO
		#print (tt)
		if "LIQUIDAGAO GENERICA DE TRIBUTO" in tt or "LIQUIDAÇÃO GENÉRICA DE TRIBUTO" in tt:
			print ('AQUI DEVE TER NUMERO')
			print (tt)
			tmprefdocumento = tt[:tt.find("LIQUIDAGAO GENERICA DE TRIBUTO")]
			print (tmprefdocumento)
			#check | start from there
			refdocumento = tmprefdocumento[tmprefdocumento.find("|")+1:].strip().replace(' ','')
			print (refdocumento)

			#Check if all Numbers...
			#Check 1 by one and replace by a number; only if 1 letter
			print (len(refdocumento))

			#LIQUIDAÇÃO Ref. document must:
			#Start with 22 (YEAR)
			#Followed by 010 (Don't know what if changes after year or period)
			#Total len 15
			if len(refdocumento) == 14:
				if refdocumento.startswith('2010'):
					#Missing 2
					tmprefdocumento = '2' + refdocumento
					refdocumento = tmprefdocumento
			if refdocumento.isnumeric():
				print ('OK... pode validar ONLINE')
			else:
				for x in refdocumento:
					print (x)
					print (x.isnumeric())
					if not x.isnumeric():
						#testing... all number to match the ONLINE LIQUIDAÇÃO
						#TEMP FIX to see if works...
						tmprefdocumento = refdocumento.replace(x,'8')
						refdocumento = tmprefdocumento
						break
			print ('REF ',refdocumento)
			#validar_dlinumber(refdocumento)
			pdf_notaliquidacao = agt_lgt(refdocumento)
			print ('TEM pdf_notaliquidacao ', pdf_notaliquidacao)

			stop_time = time.monotonic()
			print(round(stop_time-start_time, 2), "seconds")

			return pdf_notaliquidacao



@frappe.whitelist(allow_guest=True)
def validar_dlinumber(dlinumber):
	#import requests
	start_time = time.monotonic()
	if dlinumber:
		print ('verifying... ', dlinumber)
		try:
			response.headers['Content-Type'] = 'application/json; charset=utf-8'
			response  = requests.get("https://portaldocontribuinte.minfin.gov.ao/imprimir-verificar-nota-de-liquidacao?dliNumber=" + str(dlinumber),headers=headers,verify=False, timeout=5)
			#check if Response is 502; Does not Exist the site...
			if response.status_code == 502:
				print ('Nao existe o SITE!!!!')
				return ('SITE EM BAIXO.')
			else:
				print ('Tem dados NIF....')
				data = response.json()
				print ('data')
				#print (data['success'])
				print (data)

				#Verify if PAGA
				if data.find('encontra-se paga e registada no sistema') != -1:
					print ('Nota de Liquidacao ESTA PAGA...')


				frappe.throw(porra)
				if 'status' in data:
					if data['status'] == 500:
						print ('Erro de Servidor!!!')
					elif 'sucess' in data:
						if data['success'] == False:
							print ('NIF INVALIDO!!!')
							return 'NIF INVALIDO'
						else:
							#Success
							nifvalido = data['data']['nif']
							regimeiva = ""
							print ('Valido')
							#verify Regime IVA
							#"regimeIva":"GNAD"
							if data['data']['regimeIva'] != "" and data['data']['regimeIva'] == "GNAD" :
								#GERAL
								regimeiva = 'Regime GERAL'
								print ('Regime GERAL')

							if data['data']['companyName']:
								return nifvalido, regimeiva, data['data']['companyName']
							else:
								return nifvalido, regimeiva, data['data']['nameAbb']



				elif 'success' in data:
					if data['success'] == False:
						print ('NIF INVALIDO!!!')
						return 'NIF INVALIDO'
					else:
						#Success
						nifvalido = data['data']['nif']
						regimeiva = ""
						print ('Valido')
						print ('data ', data)
						#verify Regime IVA
						#"regimeIva":"GNAD"
						if data['data']['regimeIva'] != "" and data['data']['regimeIva'] == "GNAD" :
							#GERAL
							regimeiva = 'Regime GERAL'
							print ('Regime GERAL')
						if data['data']['companyName']:
							return nifvalido, regimeiva, data['data']['companyName']
						else:
							return nifvalido, regimeiva, data['data']['nameAbb']

				else:
					#Success
					nifvalido = data['data']['nif']
					regimeiva = ""
					print ('Valido')
					#verify Regime IVA
					#"regimeIva":"GNAD"
					if data['data']['regimeIva'] != "" and data['data']['regimeIva'] == "GNAD" :
						#GERAL
						regimeiva = 'Regime GERAL'
						print ('Regime GERAL')

					if data['data']['companyName']:
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return nifvalido, regimeiva, data['data']['companyName']
					else:
						stop_time = time.monotonic()
						print(round(stop_time-start_time, 2), "seconds")

						return nifvalido, regimeiva, data['data']['nameAbb']



		except requests.exceptions.ReadTimeout:
			print ('SEM LIGACAO.....')
			print ('SEM LIGACAO.....')
		except requests.exceptions.ConnectionError:
			print ('Connection refused.....')
			requests.status_code = "Connection refused"

def agt_lgt(dlinumber):
	'''
		Run nodejs using Numero de Referencia do download REGISTO DE PAGAMENTO - LIQUIDACAO GENERICA
		RETENCAO na FONTE
	'''
	import subprocess

	start_time = time.monotonic()

	if dlinumber:
		#p = subprocess.Popen(['node','../agt_lgt.js', dlinumber], stdout=subprocess.PIPE)
		p = subprocess.Popen(['/home/frappe/.nvm/versions/node/v14.17.3/bin/node','../agt_lgt.js', dlinumber], stdout=subprocess.PIPE)
		out = p.stdout.read()
		print(out)
		if "statusCode: 404" in out.decode("utf-8"):
			print ('Running again....')
			#p = subprocess.Popen(['node','../agt_lgt.js', dlinumber], stdout=subprocess.PIPE)
			p = subprocess.Popen(['/home/frappe/.nvm/versions/node/v14.17.3/bin/node','../agt_lgt.js', dlinumber], stdout=subprocess.PIPE)
			out = p.stdout.read()
			print(out)
			if "statusCode: 404" in out.decode("utf-8"):
				return 'INVALIDO'
			else:
				tmpficheiroPDF = out.decode("utf-8").split('\n')[12]
				ficheiroPDF = tmpficheiroPDF[tmpficheiroPDF.find('VERIFICAR PASTA ')+16:]

				stop_time = time.monotonic()
				print(round(stop_time-start_time, 2), "seconds")

				return out.decode("utf-8") #ficheiroPDF

		else:
			#return out #.decode("utf-8")
			print (out.decode("utf-8"))
			tmpficheiroPDF = out.decode("utf-8").split('\n')[12]
			ficheiroPDF = tmpficheiroPDF[tmpficheiroPDF.find('VERIFICAR PASTA ')+16:]

			stop_time = time.monotonic()
			print(round(stop_time-start_time, 2), "seconds")

			return out.decode("utf-8") # ficheiroPDF

@frappe.whitelist(allow_guest=True)
def ocr_PING():
	print ('CHEGOU AQu......')
	return 'PONG'


def ocr_tables_from_image(ficheiro = None):
	'''
		Requires python 3.6 or higher
		Extracted from:
		https://gist.github.com/huks0/e48d604fc9dd91731bc687d6e3933db4
	'''

	import cv2
	import numpy as np
	import pandas as pd
	#import matplotlib.pyplot as plt
	import csv

	try:
		from PIL import Image
	except ImportError:
		import Image
	import pytesseract

	import fitz

	start_time = time.monotonic()

	#pdffile = "/files/FT-Impressão-FTM 1KO2022_3_A.pdf"
	#pdffile = "/home/frappe/frappe-bench/sites/tools.angolaerp.co.ao/public/files/FT-Impressão-FTM 1KO2022_3_A.pdf"
	pdffile = "/home/frappe/frappe-bench/sites/tools.angolaerp.co.ao/public/files/TESTE_CODE_SINV-2022-00043.pdf"

	if not ficheiro:
		frappe.throw('Precisa de ficheiro...')
	else:

		if os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = ficheiro

	if ".pdf" in filefinal:
		pdffile = filefinal
	else:
		frappe.throw('Ficheiro tem que ser PDF...')

	doc = fitz.open(pdffile)
	zoom = 4
	mat = fitz.Matrix(zoom, zoom)
	count = 0
	# Count variable is to get the number of pages in the pdf
	for p in doc:
		count += 1
	for i in range(count):
		val = f"image_{i+1}.png"
		page = doc.load_page(i)
		pix = page.get_pixmap(matrix=mat)
		#pix.save('/tmp/' + val)
		pix.writePNG('/tmp/' + val)
	doc.close()


	#import matplotlib.pyplot as plt

	file= '/tmp/' + val
	#file= '/tmp/image_1.png'

	#read your file
	#file=r'/tmp/test_table_img.png'
	img = cv2.imread(file,0)
	img.shape

	#thresholding the image to a binary image
	thresh,img_bin = cv2.threshold(img,128,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)

	#inverting the image
	img_bin = 255-img_bin
	cv2.imwrite('/tmp/cv_inverted.png',img_bin)
	#Plotting the image to see the output
	#plotting = plt.imshow(img_bin,cmap='gray')
	#plt.show()

	# countcol(width) of kernel as 100th of total width
	kernel_len = np.array(img).shape[1]//100
	# Defining a vertical kernel to detect all vertical lines of image
	ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
	# Defining a horizontal kernel to detect all horizontal lines of image
	hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
	# A kernel of 2x2
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

	#Use vertical kernel to detect and save the vertical lines in a jpg
	image_1 = cv2.erode(img_bin, ver_kernel, iterations=3)
	vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=3)
	cv2.imwrite("/tmp/vertical.jpg",vertical_lines)
	#Plot the generated image
	#plotting = plt.imshow(image_1,cmap='gray')
	#plt.show()

	#Use horizontal kernel to detect and save the horizontal lines in a jpg
	image_2 = cv2.erode(img_bin, hor_kernel, iterations=3)
	horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=3)
	cv2.imwrite("/tmp/horizontal.jpg",horizontal_lines)
	#Plot the generated image
	#plotting = plt.imshow(image_2,cmap='gray')
	#plt.show()

	# Combine horizontal and vertical lines in a new third image, with both having same weight.
	img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
	#Eroding and thesholding the image
	img_vh = cv2.erode(~img_vh, kernel, iterations=2)
	thresh, img_vh = cv2.threshold(img_vh,128,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	cv2.imwrite("/tmp/img_vh.jpg", img_vh)
	bitxor = cv2.bitwise_xor(img,img_vh)
	bitnot = cv2.bitwise_not(bitxor)
	#Plotting the generated image
	#plotting = plt.imshow(bitnot,cmap='gray')
	#plt.show()

	# Detect contours for following box detection
	contours, hierarchy = cv2.findContours(img_vh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	def sort_contours(cnts, method="left-to-right"):
		import cv2
		# initialize the reverse flag and sort index
		reverse = False
		i = 0
		# handle if we need to sort in reverse
		if method == "right-to-left" or method == "bottom-to-top":
			reverse = True
		# handle if we are sorting against the y-coordinate rather than
		# the x-coordinate of the bounding box
		if method == "top-to-bottom" or method == "bottom-to-top":
			i = 1
		# construct the list of bounding boxes and sort them from top to
		# bottom
		boundingBoxes = [cv2.boundingRect(c) for c in cnts]
		(cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
		key=lambda b:b[1][i], reverse=reverse))
		# return the list of sorted contours and bounding boxes
		return (cnts, boundingBoxes)

	# Sort all the contours by top to bottom.
	contours, boundingBoxes = sort_contours(contours, method="top-to-bottom")
	print ('boundingBoxes ', boundingBoxes)
	#Creating a list of heights for all detected boxes
	#heights = [boundingBoxes[i][3] for i in range(len(boundingBoxes))]

	heights = []
	for i in range(len(boundingBoxes)):
		heights.append(boundingBoxes[i][3])

	#Get mean of heights
	mean = np.mean(heights)

	#Create list box to store all boxes in
	box = []
	# Get position (x,y), width and height for every contour and show the contour on image
	for c in contours:
		x, y, w, h = cv2.boundingRect(c)
		if (w<1000 and h<500):
			image = cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
			box.append([x,y,w,h])

	#plotting = plt.imshow(image,cmap='gray')
	#plt.show()

	#Creating two lists to define row and column in which cell is located
	row=[]
	column=[]
	j=0

	#Sorting the boxes to their respective row and column
	for i in range(len(box)):

		if(i==0):
			column.append(box[i])
			previous=box[i]

		else:
			if(box[i][1]<=previous[1]+mean/2):
				column.append(box[i])
				previous=box[i]

				if(i==len(box)-1):
					row.append(column)

			else:
				row.append(column)
				column=[]
				previous = box[i]
				column.append(box[i])

	print(column)
	print(row)

	#calculating maximum number of cells
	countcol = 0
	for i in range(len(row)):
		countcol = len(row[i])
		if countcol > countcol:
			countcol = countcol

	#Retrieving the center of each column
	#center = [int(row[i][j][0]+row[i][j][2]/2) for j in range(len(row[i])) if row[0]]

	center = []
	for j in range(len(row[i])):
		if row[0]:
			center.append(int(row[i][j][0]+row[i][j][2]/2))

	center=np.array(center)
	center.sort()
	print(center)
	#Regarding the distance to the columns center, the boxes are arranged in respective order

	finalboxes = []
	for i in range(len(row)):
		lis=[]
		for k in range(countcol):
			lis.append([])
		for j in range(len(row[i])):
			diff = abs(center-(row[i][j][0]+row[i][j][2]/4))
			minimum = min(diff)
			indexing = list(diff).index(minimum)
			lis[indexing].append(row[i][j])
		finalboxes.append(lis)


	#from every single image-based cell/box the strings are extracted via pytesseract and stored in a list
	outer=[]
	for i in range(len(finalboxes)):
		for j in range(len(finalboxes[i])):
			inner=''
			if(len(finalboxes[i][j])==0):
				outer.append(' ')
			else:
				for k in range(len(finalboxes[i][j])):
					y,x,w,h = finalboxes[i][j][k][0],finalboxes[i][j][k][1], finalboxes[i][j][k][2],finalboxes[i][j][k][3]
					finalimg = bitnot[x:x+h, y:y+w]
					kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
					border = cv2.copyMakeBorder(finalimg,2,2,2,2, cv2.BORDER_CONSTANT,value=[255,255])
					resizing = cv2.resize(border, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
					dilation = cv2.dilate(resizing, kernel,iterations=1)
					erosion = cv2.erode(dilation, kernel,iterations=2)

					out = pytesseract.image_to_string(erosion)
					if(len(out)==0):
						out = pytesseract.image_to_string(erosion, config='--psm 3')
					inner = inner +" "+ out
				outer.append(inner)

	#Creating a dataframe of the generated OCR list
	arr = np.array(outer)
	dataframe = pd.DataFrame(arr.reshape(len(row), countcol))
	print(dataframe)
	#for dd in dataframe.split('\n'):
	for dd in range(len(dataframe)):
		print ('----')
		print (dd)
		print ('dataframe.loc[dd]')
		print (dataframe.loc[dd])
		print ('[dd][0]')
		for a,b in enumerate(dataframe.loc[dd]):
			if len(b.strip()) >0:
				print ('====')
				print (a)
				print (b)
				print ('tamanho ', len(b.strip()))

	#data = dataframe.style.set_properties(align="left")
	#Converting it in a excel-file
	#data.to_excel("/Users/marius/Desktop/output.xlsx")

	stop_time = time.monotonic()
	print(round(stop_time-start_time, 2), "seconds")



def ocr_pdf_to_image(ficheiro = None):
	'''
		Requires python 3.6 or higher
		Extracted from:
		https://towardsdatascience.com/read-a-multi-column-pdf-with-pytesseract-in-python-1d99015f887a
	'''

	# for manipulating the PDF
	import fitz

	# for OCR using PyTesseract
	import cv2                              # pre-processing images
	import pytesseract                      # extracting text from images
	import numpy as np
	#import matplotlib.pyplot as plt         # displaying output images

	from PIL import Image

	start_time = time.monotonic()

	if not ficheiro:
		frappe.throw('Precisa de ficheiro...')
	else:

		if os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/files','')):
			filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/files','')
			print ('filefinal ',filefinal)
			if filefinal.startswith('.'):
				filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
				filefinal = filefinal1
			print ('filefinal1 ',filefinal)

		else:
			filefinal = ficheiro

	#pdffile = filefinal
	if ".pdf" in filefinal:
		SCANNED_FILE = filefinal
	else:
		frappe.throw('Ficheiro tem que ser PDF...')

	#SCANNED_FILE = 'SINV-2022-00009_1_CC.pdf'


	img = cv2.imread(SCANNED_FILE)

	zoom_x = 2.0 # horizontal zoom
	zoom_y = 2.0 # vertical zoom
	mat = fitz.Matrix(zoom_x, zoom_y)

	doc = fitz.open(SCANNED_FILE)

	#Delete tmp files first
	if os.path.exists('/tmp/input-page-*.png'):
		os.remove('/tmp/input-page-*.png')


	print("Generated pages: ")
	for page in doc:
		pix = page.get_pixmap(matrix=mat)
		print ('SCANNED_FILE.split')
		print (SCANNED_FILE.split('\\'))
		#png = '/tmp/input-' + SCANNED_FILE.split('\\')[-1].split('.')[0] + 'page-%i.png' % page.number
		png = '/tmp/input-page-%i.png' % page.number
		print(png)
		#pix.save(png)
		pix.writePNG(png)

	original_image = cv2.imread('/tmp/input-page-0.png')
	#original_image = cv2.imread('/tmp/input-page-3.png')

	# convert the image to grayscale
	gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
	#plt.figure(figsize=(25, 15))
	#plt.imshow(gray_image, cmap='gray')
	#plt.show()


	# Performing OTSU threshold
	ret, threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
	#plt.figure(figsize=(25, 15))
	#plt.imshow(threshold_image, cmap='gray')
	#plt.show()


	rectangular_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (66, 66))

	# Applying dilation on the threshold image
	dilated_image = cv2.dilate(threshold_image, rectangular_kernel, iterations = 1)
	#plt.figure(figsize=(25, 15))
	#plt.imshow(dilated_image)
	#plt.show()

	# Finding contours
	contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# Creating a copy of the image
	copied_image = original_image.copy()

	with open("/tmp/recognized-kernel-66-66.txt", "w+") as f:
		f.write("")
	f.close()

	mask = np.zeros(original_image.shape, np.uint8)

	# Looping through the identified contours
	# Then rectangular part is cropped and passed on to pytesseract
	# pytesseract extracts the text inside each contours
	# Extracted text is then written into a text file
	for cnt in contours:
		x, y, w, h = cv2.boundingRect(cnt)

		# Cropping the text block for giving input to OCR
		cropped = copied_image[y:y + h, x:x + w]

		with open("/tmp/recognized-kernel-66-66.txt", "a") as f:
			# Apply OCR on the cropped image
			text = pytesseract.image_to_string(cropped, lang='eng', config='--oem 3 --psm 1')
			print(text)
			f.write(text)
		f.close()

		masked = cv2.drawContours(mask, [cnt], 0, (255, 255, 255), -1)

	stop_time = time.monotonic()
	print(round(stop_time-start_time, 2), "seconds")

	#plt.figure(figsize=(25, 15))
	#plt.imshow(masked, cmap='gray')
	#plt.show()

def ocr_ocr_ocr(facturaSupplier,en_palavras_fim_item,en_scan,supplierMoeda,terpalavras_header_EN,palavras_no_header,filefinal = None,palavras_no_header_ultimoHeader = None):
	print ('Running ocr_ocr_ocr ')
	print ('Running ocr_ocr_ocr ')
	print ('Running ocr_ocr_ocr ')

	start_time = time.monotonic()

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])\s([1-9]{1,2}):([1-9]{2}):[0-9]{2}\s(AM|PM)|([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)|(?:\d*\,\d+)'
	filtered_divs = {'COUNTER': [], 'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': [], 'IVA': []}

	#FIX 22-09-2023
	nif_pattern = r'^([0-9]{3})\s([0-9]{3})\s([0-9]{4})|([0-9]{10})|([0-9]{3})\s([0-9]{3})\s([0-9]{3}\s[0-9])'

	empresaSupplier = ''
	invoiceNumber = ''
	invoiceDate = ''
	moedaInvoice = ''
	supplierAddress = ''
	supplierEmail = ''
	supplierNIF = ''
	supplierCountry = ''
	supplierPais = ''


	#Items
	itemsSupplierInvoice = []
	itemCode = ''
	itemDescription = ''
	itemRate = ''
	itemQtd = ''
	itemTotal = ''
	itemIVA = ''

	tmpcountry = ''

	#FIX 22-01-2023;   CONTAINER NUMBER
	container_number = ''
	ceal_number = ''
	cartoon_qtd = ''

	#System Currencies ...
	moedassystem = []
	listamoedas = frappe.get_list("Currency",fields=['name'],ignore_permissions=True)
	for ll in listamoedas:
		moedassystem.append(ll.name)



	print ("facturaSupplier")
	#print (facturaSupplier)
	#print (type(facturaSupplier))
	#print (json.loads(facturaSupplier))
	print (facturaSupplier)
	#frappe.throw(porra)

	palavrasexiste_header = False

	tmp_sn = ''	#Will hold SNs

	en_contapalavras_header_banco = 0	#To avoid adding Bank details as SN

	countlines = 1

	fim_items = False

	facturaAGT = False

	print ('ocr_ocr_ocr')
	print ('ocr_ocr_ocr')
	print ('ocr_ocr_ocr')

	contapalavras_header = 0

	linhaem_branco = False
	linhaAnterior = ''

	proximalinha_factura = False	#Keep Invoice Number
	proximalinha_contentor = False
	proximalinha_data = False

	for fsup in facturaSupplier:
		print ('=====INICIO ======= ocr_ocr_ocr ')
		print (fsup)

		#Check if AGT Invoices
		if "CONTRIBUINTE FISCAL DETALHES DO CLIENTE" in fsup.strip():
			print ('invoiceNumber ', invoiceNumber)
			if "FTM" in invoiceNumber:
				facturaAGT = True

		#FIX 14-12-2022
		for fi in en_palavras_fim_item:
			if fi.upper() in fsup.strip().upper():
				fim_items = True
				#frappe.throw(porra)

		if fsup.strip() == None or fsup.strip() == '':
			linhaem_branco = True
			#palavrasexiste_header = True

		if fsup.strip() != None and fsup.strip() != "":
			if not empresaSupplier:
				'''
				EVITA palavras:
					Original
					2!Via
					2ºVia
				'''
				evitapalavras =['Original','2!Via','2ºVia','Duplicado']
				palavraexiste = False
				for ff in fsup.split(' '):
					#print (ff)
					if ff in evitapalavras:
						#print ('TEM palavra ', ff)
						palavraexiste = True
				if palavraexiste == False:
					#print (fsup)
					#print ('Pode ser NOME DA EMPRESA')
					#Remove if startswith /
					if fsup.strip().startswith('/'):
						empresaSupplier = fsup.strip()[1:]
					else:
						empresaSupplier = fsup.strip()

					#Check if startsWith Customer Name... skip
					if fsup.strip().startswith('Customer Name:'):
						empresaSupplier = ''

				#Check online for Company.... only twice
				if empresaSupplier:
					print ('Verificar Empresa Online')
					procuraonline = False
					if en_scan:
						en_paraempresa_terpalavras = ['TRADING','TR LLC','LLC','L.L.C']
						for tp in en_paraempresa_terpalavras:
							if tp in fsup.upper():
								procuraonline = True
								break
						if procuraonline:
							#FIX 22-01-2023; Remove Expoter:/Exporter:
							fsup_tmp = fsup.replace('Expoter:','').replace('Exporter:','')
							print ('fsup_tmp ', fsup_tmp)
							empresa = search_company_online(fsup_tmp)
						else:
							empresa = 'INVALIDO'

					else:
						#For Angola
						empresa = empresaSupplier
						#TODO: if NIF check NIF and get Company name...

					if empresa == 'INVALIDO':
						empresaSupplier = ''
					else:
						print ('RESULTADO Empresa Online')
						print (empresa)
						removerpalavras =['|','Facebook']
						tmpempresa = ''

						for ee in empresa:
							print ('empresa ', ee)
							if not ":" in ee:
								for rr in removerpalavras:
									if not tmpempresa:
										if rr == "|":
											print ('poder ser country')
											print ('ee ', ee)
											print (ee.find('|'))
											if ee.find('|') != -1:
												tmpempresa = ee[:ee.find('|')]
												tmpcountry = ee[ee.find('|')+1:ee.find('-')-1]
												print ('tmpempresa ',tmpempresa)
												print (tmpcountry)
										else:
											#tmpempresa = ee.replace(rr,'')
											print ('REMOVED FOR NOW...')
									else:
										tmpempresa1 = tmpempresa.replace(rr,'')
										tmpempresa = tmpempresa1
								if tmpempresa:
									#Stay with First or Second record from google search...
									break
						if tmpempresa:
							print ('tmpempresa ',tmpempresa)
							print ('tmpcountry ', tmpcountry)
							if tmpempresa.strip().endswith('-'):
								empresaSupplier = tmpempresa.strip()[0:len(tmpempresa.strip())-1]
							else:
								empresaSupplier = tmpempresa.strip()
							if tmpcountry:
								if tmpcountry.upper().strip() == "DUBAI" or tmpcountry.upper().strip() == "SHARJAH":
									supplierPais = 'United Arab Emirates'

						#frappe.throw(porra)
			if not supplierAddress:
				'''
				TER palavras:
					RUA, AVENIDA
				'''
				if tmpcountry.upper().strip() != "DUBAI":
					if empresaSupplier:
						terpalavras = ['RUA', 'AVENIDA']
						ADDRpalavraexiste = False
						for ff in fsup.split(' '):
							#print (ff)
							if ff in terpalavras:
								#print ('TEM palavra ', ff)
								ADDRpalavraexiste = True
						if ADDRpalavraexiste:
							supplierAddress = fsup.strip()

			if not supplierEmail:
				if "EMAIL:" in fsup.upper():
					#print ('Ainda por fazer....')
					supplierEmail = 'Ainda por fazer....'
			if not supplierNIF:
				if not en_scan:
					if "NIF" in fsup.upper() or "NIF:" in fsup.upper():
						supplierNIF = fsup.replace('NIF:','').replace('NIF','').replace(':','').strip()
						print ('CHECK NIF....ANGOLA3')
						if "NIFE do Adquirente:".upper() in fsup.upper() or "NIF do Adquirente:".upper() in fsup.upper():
							#AGT tem Nif Origem e nif DESTINO
							if "NIFE do Adquirente:".upper() in fsup.upper():
								niforigem = fsup[fsup.find('NIF:')+4:fsup.find('NIFE')].strip()
								#FIX 22-09-2023
								tmp_supplierNIF = niforigem.replace('NIF:','').replace('NIF','').strip()
								print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
								if re.match(nif_pattern,tmp_supplierNIF.strip()):
									supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
									nifvalido = validar_nif (supplierNIF)
									print (nifvalido)
									if nifvalido and nifvalido[2]:
										print ('Empresa CORRECTA3 ', nifvalido[2])
										empresaSupplier = nifvalido[2]
										supplierNIF = nifvalido[0]
								'''
								nifvalido = validar_nif (niforigem)
								print (nifvalido)
								if nifvalido and nifvalido[2]:
									print ('Empresa CORRECTA3 ', nifvalido[2])
									empresaSupplier = nifvalido[2]
									supplierNIF = nifvalido[0]
								'''

								#Check if is for Destiny company!!!!
								nifdestino = fsup[fsup.find('Adquirente:')+11:].strip()

						else:
							#FIX 22-09-2023
							tmp_supplierNIF = supplierNIF.replace('NIF:','').replace('NIF','').strip()
							print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
							if re.match(nif_pattern,tmp_supplierNIF.strip()):
								supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
								nifvalido = validar_nif (supplierNIF)
								print (nifvalido)
								if nifvalido and nifvalido[2]:
									print ('Empresa CORRECTA3 ', nifvalido[2])
									empresaSupplier = nifvalido[2]
									supplierNIF = nifvalido[0]
							'''
							nifvalido = validar_nif (supplierNIF)
							print (nifvalido)
							if nifvalido and nifvalido[2]:
								print ('Empresa CORRECTA ', nifvalido[2])
								empresaSupplier = nifvalido[2]
							'''

				elif 'TRN :' in fsup.upper().strip():
					print ('TRN aqui....')
					if not supplierNIF:
						supplierNIF = fsup[fsup.upper().find('TRN :')+5:].strip()
						#FIX 22-09-2023
						tmp_supplierNIF = supplierNIF.replace('NIF:','').replace('NIF','').strip()
						print ('NIFnumber ', re.match(nif_pattern,tmp_supplierNIF.strip()))
						if re.match(nif_pattern,tmp_supplierNIF.strip()):
							supplierNIF = tmp_supplierNIF[0:re.match(nif_pattern,tmp_supplierNIF.strip()).span()[1]].replace(' ','')
							nifvalido = validar_nif (supplierNIF)
							print (nifvalido)
							if nifvalido and nifvalido[2]:
								print ('Empresa CORRECTA4 ', nifvalido[2])
								empresaSupplier = nifvalido[2]
								supplierNIF = nifvalido[0]

			if not supplierMoeda:
				terpalavras = ['Moeda','AOA','AKZ','KZ']
				#TODO: List of Currencies to see if on the Document to be OCR..

				Moedapalavraexiste = False
				for ff in terpalavras:
					if ff in fsup.strip():
						Moedapalavraexiste = True
				if Moedapalavraexiste:
					#Check for AOA and AKZ first...
					if "AOA" in fsup.strip() or "AKZ" in fsup.strip() or "KZ" in fsup.strip():
						supplierMoeda = 'KZ'
					else:
						supplierMoeda = fsup.strip().replace('Moeda:','').replace('Moeda','').strip()
						#TODO: Remove CAMBIO and Numbers if exist on the same line...
				else:
					#Check words on doc if any on the list...
					#FIX 23-12-2022
					for mm in moedassystem:
						if mm.upper() != "ALL":
							tmpmoeda = ' ' + mm.upper() + ' '
							if tmpmoeda.upper() in fsup.upper():
								print ('TEM MOEDA NA FACTURA...')
								print (mm.upper())
								print ('tmpmoeda ',tmpmoeda.upper())
								print (fsup.strip().upper())
								supplierMoeda = tmpmoeda.upper().strip().replace(':','')

			if not invoiceDate:
				print ('invoiceDate')
				terpalavras = ['Data Doc.','Data Doc','Invoice Date:','Invoice Date','DATE:','Date']
				Datepalavraexiste = False
				for ff in terpalavras:
					if ff in fsup.strip():
						Datepalavraexiste = True
						proximalinha_data = True
				if Datepalavraexiste:
					#Loop thro terpalavras
					for tt in terpalavras:
						if fsup.strip().find(tt) != -1:
							invoiceDate1 = fsup.strip()[fsup.strip().find(tt):]
							invoiceDate = invoiceDate1.replace(tt,'').strip()
							break
					print (invoiceDate)
				else:
					#Check if has DATE on fsup
					matches = re.finditer(date_pattern,fsup, re.MULTILINE)
					for matchNum, match in enumerate(matches, start=1):
						print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
						if match.group():
							print('TEM DATA.... ',match.group())
							invoiceDate = match.group()
					if proximalinha_data:
						invoiceDate = fsup.strip()

			if not invoiceNumber:
				#Search for PP FT FR
				#seriesDocs_pattern = r"^([P][P]|[F][T]|[F][R]|[F][T][M])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}|([P][P]|[F][T]|[F][R])\s.{1,4}\/\d{1,5}"
				#FIX 05-01-2023; Included FTM from AGT site
				#seriesDocs_pattern = r"^([F][T][M]|[P][P]|[F][T]|[F][R]).{1}\s\d{1}[a-zA-Z].{1}[0-9]{4}\/.{1,4}|([P][P]|[F][T]|[F][R])\s.{1,5}\d{2}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}"
				seriesDocs_pattern = r"^([F][T][M]|[P][P]|[F][T]|[F][R]).{1}\s\d{1}[a-zA-Z].{1}[0-9]{4}\/.{1,4}|([P][P]|[F][T]|[F][R])\s.{1,5}\s\d{2}\/\d{1,5}|([P][P]|[F][T]|[F][R])\s.{1,4}\/\d{1,5}"
				#print (re.match(seriesDocs_pattern,fsup.upper().strip()))
				if re.match(seriesDocs_pattern,fsup.upper().strip()):
					invoiceNumber = fsup.upper().strip()
				else:
					if "FT" in fsup.upper().strip() or "PP" in fsup.upper().strip() or "FR" in fsup.upper().strip() or "FTM" in fsup.upper().strip():
						if "FT" in fsup.upper().strip():
							tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FT'):]
						elif "PP" in fsup.upper().strip():
							tmpseries = fsup.upper().strip()[fsup.upper().strip().find('PP'):]
						elif "FR" in fsup.upper().strip():
							tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FR'):]
						elif "FTM" in fsup.upper().strip():
							#FIX 05-01-2023; Factura do portal da AGT
							tmpseries = fsup.upper().strip()[fsup.upper().strip().find('FTM'):]

						#print ('tmpseries ',tmpseries)
						#print (re.match(seriesDocs_pattern,tmpseries))
						if re.match(seriesDocs_pattern,tmpseries):
							#Match series
							invoiceNumber = tmpseries
						#frappe.throw(porra)

				#Case Doc is in EN and not from Angola
				terpalavras = ['Invoice No:','Invoice No','INVOICE NUMBER']
				if not invoiceNumber:
					for tt in terpalavras:
						print ('Factura ', tt.upper())
						print (fsup.upper().strip())
						if fsup.upper().strip().find(tt.upper()) != -1:
							invoiceNumber = fsup.upper().strip()[fsup.upper().strip().find(tt.upper()):].replace(tt.upper(),'').replace(':','').strip()
							print ('fac ', invoiceNumber)
					print (fsup.strip())
					print ('INVOICE NUMBER ')
					if proximalinha_factura:
						invoiceNumber = fsup.strip()
						proximalinha_factura = False
					if fsup.strip().upper() == 'INVOICE NUMBER':
						proximalinha_factura = True

			#CONTAINER NUMBER
			if not container_number:
				print ('Container Number')
				terpalavras = ['CONTAINER NUMBER:','CONTAINER NUMBER']
				Containerpalavraexiste = False
				for ff in terpalavras:
					if ff in fsup.strip():
						Containerpalavraexiste = True
						proximalinha_contentor = True
				if Containerpalavraexiste:
					#Loop thro terpalavras
					for tt in terpalavras:
						if fsup.strip().find(tt) != -1:
							containernumber_tmp = fsup.strip()[fsup.strip().find(tt):]
							#invoiceDate = invoiceDate1.replace(tt,'').strip()
							break
					print (containernumber_tmp)
					container_number = containernumber_tmp
				if proximalinha_contentor:
					container_number = fsup.strip()

			if not ceal_number:
				print ('Ceal Number or Seal Number')
				terpalavras = ['CEAL NAMBER','CEAL NUMBER']
				Cealpalavraexiste = False
				for ff in terpalavras:
					if ff in fsup.strip():
						Cealpalavraexiste = True
				if Cealpalavraexiste:
					#Loop thro terpalavras
					for tt in terpalavras:
						if fsup.strip().find(tt) != -1:
							cealnumber_tmp = fsup.strip()[fsup.strip().find(tt):]
							#invoiceDate = invoiceDate1.replace(tt,'').strip()
							break
					print (cealnumber_tmp)
					ceal_number = cealnumber_tmp


			if not itemsSupplierInvoice and fim_items == False:
				#Items
				itemsSupplierInvoice = []
				contaLinhas = ''
				itemCode = ''
				itemDescription = ''
				itemRate = ''
				itemQtd = ''
				itemTotal = ''
				itemIVA = ''

				tmprate = ''
				tmpamount = ''

				'''
				TER palavras Para saber que ITEM TABLES DESCRIPTION:
					UN, UNIDADE, CAIXA, CX, Artigo, Descrição, Qtd., Pr.Unit, Cód. Artigo, V.Líquido
				'''
				#contapalavras_header = 0

				en_palavras_banco = ['BANK','ACCOUNT']



				#palavrasexiste_header = False
				if en_scan:
					for pp in terpalavras_header_EN:
						#print ('CONTAR terpalavras_header_EN')
						#print ('pp.upper() ',pp.upper())
						#print (fsup.strip().upper())
						if pp.upper() in fsup.strip().upper():
							contapalavras_header += 1
					for pp1 in en_palavras_banco:
						if pp1.upper() in fsup.strip().upper():
							en_contapalaterpalavras_header_ENvras_header_banco += 1

				else:
					print ('SCAN PORTUGUES.....')
					#for pp in terpalavras_header:
					print ('terpalavras_header_EN')
					print (terpalavras_header_EN)
					for pp in terpalavras_header_EN:
						#print ('tamho ',len(fsup.strip()))
						#print ('pp ', pp)
						print (len(fsup.strip()) - fsup.strip().upper().find(pp.upper()))
						if len(fsup.strip()) - fsup.strip().upper().find(pp.upper()) <= 5:
							print ('ULTIMO HEADER')
							print ('pp ', pp)
							#frappe.throw(porra)

						if pp.upper() in fsup.strip().upper():
							#contapalavras_header += 1
							print ('REMOVED FROM HERE THE COUNTER')

						if len(pp.split()) == 1:
							#adicionapalavra = False
							for ffsup in fsup.split():
								if ffsup.upper().strip() == pp.upper():
									#adicionapalavra = True
									print ('VERIFICAR ')
									print (ffsup.upper().strip())
									print (pp.upper())
									#frappe.throw(porra)
									contapalavras_header += 1
						else:
							#Is two words; ex. VALOR LIQ.
							if fsup.upper().strip() == pp.upper():
								#adicionapalavra = True
								print ('VERIFICAR ')
								print (fsup.upper().strip())
								print (pp.upper())
								#frappe.throw(porra)
								contapalavras_header += 1


						#if "%Imp." == pp:
						#	if "%Imp." in fsup.strip():
						#		print ('posicao')
						#		print (fsup.strip().upper().find(pp.upper()))
						#		frappe.throw(porra)
				'''
				TER palavras Para saber que ITEM TABLES:
					UN, UNIDADE, CAIXA, CX
				'''

				terpalavras_item = ['UN', 'UNIDADE', 'CAIXA', 'CX']
				palavraexiste_item = False

				primeiroRegisto = True	#To break creating description with SN
				avoidADDING = False	#When SN or Chassis not add because they are single LINE

				#if "JTGCBAB8906725029" in fsup:
				print ('palavrasexiste_header ',palavrasexiste_header)
				print ('palavraexiste_item ',palavraexiste_item)
				if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1 and en_scan:
					print ('TO SCAN the SN or Chassis')
					palavraexiste_item = True
				#elif len(fsup.strip()) >= 2 and fsup.strip().isnumeric():
				#	#Case Numbers only and has more 3 chars with no DOT or COMMA
				#	if fsup.strip().find('.') == -1 and fsup.strip().find(',') == -1:
				#		print ('Not Currency... might be SERIAL NUMBER')
				#		print (fsup.strip())
				#		palavraexiste_item = True
				#		#frappe.throw(porra)

				#Case above is for Single SN or Chassis
				#This will check len for each if 15 or more each
				#JTFBV71J8B044454

				sao_sn = True
				print ('sao_SN palavraexiste_item ', palavraexiste_item)
				print ('en_contapalavras_header_banco ',en_contapalavras_header_banco)

				evitapalavras_telefone = [ 'Telef.', 'Telef. 244', 'Telef. +244']
				#email_pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
				#FIX 21-12-2022
				email_pattern = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$"

				evitatelefone_items = False
				for telf in evitapalavras_telefone:
					if telf in fsup.strip():
						evitatelefone_items = True
					print ('EMAIL ')
					print ('fsup.strip() ', fsup.strip())
					print (re.match(email_pattern,fsup.strip()))
					if not supplierEmail or supplierEmail == 'Ainda por fazer....':
						if re.match(email_pattern,fsup.strip()):
							supplierEmail = re.match(email_pattern,fsup.strip()).group()

				print ('evitatelefone_items ',evitatelefone_items)
				print ('linhaem_branco ',linhaem_branco)
				if not evitatelefone_items and linhaem_branco:
					if not palavraexiste_item:
						#To avoid having twice the SN
						if palavrasexiste_header:
							for cc in fsup.split():
								print ('cc ',cc)
								print ('cc ',cc.strip())
								print ('EMAIL0 ')
								if "@" in cc.strip():
									print (re.match(email_pattern,cc.strip()))
								#FIX 23-12-2022; If starts with SN:
								if cc.startswith('SN:') and not "@" in cc.strip():
									#Save all and break
									tmp_sn = fsup.strip()
									print ('VERIFICAR SE TODOS SAO SNs.... ')
									break
								#FIX 21-12-2022
								if not 'SN:' in cc and not "@" in cc.strip(): # re.match(email_pattern,cc.strip()):
									print ('LEN ', len(cc))
									if len(cc) >= 15:
										#sao_sn = True
										print ('SAO SNs')
										tmp_sn += ' ' + cc.strip()

										#21-12-2022; Check if are SN or just the Description
										retornadescricao = retorna_descricao(fsup.strip())
										print ('retornadescricao ',retornadescricao)
										print ('TESTE if is DESCRIPTION ONLY... might be SERIAL NUMBER')
										print (cc.strip())
										if retornadescricao.strip().find(cc.strip()) != -1:
											print ('FOR NOW REMOVE tmp_sn...')
											tmp_sn = ''

									elif len(cc.strip()) >= 3 and cc.strip().isnumeric():
										#Case Numbers only and has more 3 chars with no DOT or COMMA
										if cc.strip().find('.') == -1 and cc.strip().find(',') == -1:
											#To avoid Bank details as SN
											if en_contapalavras_header_banco >=2:
												print ('Bank details... NOT TO BE ENTERED AS SN')
												tmp_sn = ''
												tmpdescricao = ''
												#en_contapalavras_header_banco = 0
												palavrasexiste_header = False
											else:
												#Avoid NIF
												if not "NIF:" in fsup.strip():
													retornadescricao = retorna_descricao(fsup.strip())
													print ('retornadescricao ',retornadescricao)
													print ('0000 Not Currency... might be SERIAL NUMBER')
													print (cc.strip())

													#Check if Code No exists in Headers...
													if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
														print ('NOT SERIAL NUMBER but ITEM CODE...')
													else:
														#FIX 23-12-2022; Check if Code on start and not SN
														if retornadescricao.find(cc.strip()) > 0:
															tmp_sn += ' ' + cc.strip()

														#FIX: Find a way to get from last column to identify Total, Price, Qtd or
														#Total, VAT, Price, Qtd
														print ('If len 5 means Item, description, quantity, unit price, total price ')
														print (len(palavras_no_header))
														print (palavras_no_header)
														#Check if last 3 ones are numbers...
														tmp_totalprice = 0
														tmp_unitprice = 0
														tmp_qtd = 0
														if len(palavras_no_header) == 5:
															for idx_tmp,cc_tmp in reversed(list(enumerate(fsup.split()))):
																#Check if cash
																print (re.match(cash_pattern,cc_tmp))
																print (cc_tmp.strip().isnumeric())
																if re.match(cash_pattern,cc_tmp):
																	if not tmp_totalprice:
																		tmp_totalprice = cc_tmp
																	elif not tmp_unitprice:
																		tmp_unitprice = cc_tmp
																if cc_tmp.strip().isnumeric():
																	if not tmp_qtd:
																		tmp_qtd = cc_tmp.strip()
																		if tmp_sn.strip() == tmp_qtd:
																			print ('REMOVE tmp_sn bcs is same as Qtd')
																			print ('tmp_sn ',tmp_sn)
																			print ('tmp_qtd ', tmp_qtd)
																			tmp_sn = ''
																			break



											#frappe.throw(porra)

									else:
										sao_sn = False

				print ('tmp_sn ',tmp_sn)
				#If Description of Goods in Header dont add SN
				print (palavras_no_header)
				print ('DESCRIPTION OF GOODS' in palavras_no_header)
				if 'DESCRIPTION OF GOODS' in palavras_no_header:
					tmp_sn = ''

				#if "SN: JTFBV71J8B044454 JTFBV71J8B044601 JTFBV71J8B044616" in fsup:
				#	frappe.throw(porra)
				tmp_sn_added = False

				print ("palavrasexiste_header ",palavrasexiste_header)

				if fsup.strip().upper() in terpalavras_item:
					if linhaAnterior == "TOTAL":
						#Para adicionar o PRECO...
						linhaAnterior = 'RATE'


				if palavrasexiste_header:
					#Tem HEADER entao ve os ITENS...
					for pp in terpalavras_item:
						if pp.upper() in fsup.strip().upper():
							#IS an ITEMS so add
							palavraexiste_item = True

					#Check if previous was a Number... ERROR OCR so do Plus 1 as this is First Col or Chars...
					if len(filtered_divs['ITEM']) > 1:
						tmpitemCode = ''
						print ('Check if previous was a Number... ERROR OCR so do Plus 1 as this is First Col or Chars... ')
						print (filtered_divs['ITEM'][len(filtered_divs['ITEM'])-1])
						if filtered_divs['ITEM'][len(filtered_divs['ITEM'])-1].isnumeric():
							if not fsup.strip()[0:1].isnumeric():
								tmpitemCode = str(int(filtered_divs['ITEM'][len(filtered_divs['ITEM'])-1]) + 1)
								print ('tmpitemCode ',tmpitemCode)
								palavraexiste_item = True
								#frappe.throw(porra)

					#Check if startswith a NUMBER...
					print ('XXXpalavraexiste_item ',palavraexiste_item)
					print (fsup.strip()[0:1].isnumeric())
					if "CODE" in palavras_no_header and tmp_sn.startswith('SN:'):
						print ('Caso tenha CODE or CODE NO and tmp_sn')
						print ('Caso tenha CODE or CODE NO and tmp_sn')
						#if "CODE" in palavras_no_header and tmp_sn.startswith('SN:'):
						print ('ANTES ', filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
						filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' ' + tmp_sn
						print ('DEPOIS ', filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
						tmp_sn = ''

					elif palavraexiste_item or fsup.strip()[0:1].isnumeric() and linhaem_branco:
						#Check if tmp_sn and add on previous ITEM and clear
						if tmp_sn !='' and fsup.strip()[0:1].isnumeric():
							retornadescricao = retorna_descricao(fsup.strip())
							print ('retornadescricao ',retornadescricao)
							if not tmp_sn in retornadescricao:
								print (len(filtered_divs['DESCRIPTION']))
								if len(filtered_divs['DESCRIPTION']) > 1:
									print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])

								print ('If len 6 means Item, description, quantity, unit price, total price ')
								print (len(palavras_no_header))
								#Check if last 3 ones are numbers...

								if len(filtered_divs['DESCRIPTION']) > 1:
									filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' SN: ' + tmp_sn
								else:
									print ('PARA REVER DESCRIPTION.....')
									print (filtered_divs['DESCRIPTION'])
									filtered_divs['DESCRIPTION'] += ' SN: ' + tmp_sn
								tmp_sn = ''
								print ('ADDED SNs to DESCRIPTION...')
								print ('ADDED SNs to DESCRIPTION...')
								tmp_sn_added = True
							else:
								tmp_sn = ''

						#Check if First is Numbers... so is a Counter
						if fsup.strip()[0:1].isnumeric():
							contaLinhas = fsup.strip()[0:1]
						#if EN; testing to start from TOTAL, PRICE, QTD in order to prices and Qtd correct
						tmpdescricao = ''
						print ('AQUI INGLES OU PT')
						if en_scan:
							cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'

							for idx,cc in reversed(list(enumerate(fsup.split()))):
								print ('===== IDX0 ======')
								print ('idx ',idx)
								print ('cc ',cc)

								#Check if cash
								print (re.match(cash_pattern,cc))
								print (cc.strip().isnumeric())

								#If last(first) is not Numeric; No longer ITEMs...
								#if primeiroRegisto == False:
								#	palavrasexiste_header = False
								#	break

								#More than 1 can be Items...
								print ('fsup.strip().split() ', fsup.strip().split())
								print ('len(fsup.strip().split()) ', len(fsup.strip().split()))
								print ('palavras_no_header ', palavras_no_header)

								if len(fsup.strip().split()) > 1:
									if re.match(cash_pattern,cc):
										if not itemTotal:
											itemTotal = cc.strip()
										elif not itemRate:
											#Check if has VAT
											if 'VAT' in palavras_no_header and not itemIVA:
												itemIVA = cc.strip()
												print ('aqui add itemIVA')
											elif 'PRICE' in palavras_no_header and 'AMOUNT' in palavras_no_header and 'VAT' in palavras_no_header and ('TOTAL AMOUNT' in palavras_no_header or '‘TOTAL AMOUNT' in palavras_no_header):
												if not tmpamount:
													tmpamount = cc.strip()
													print ('aqui add tmpamount')
												elif not itemRate:
													itemRate = cc.strip()
													print ('aqui add itemRate II')

											else:
												itemRate = cc.strip()
												print ('aqui add itemRate')
										primeiroRegisto = False
									elif cc.strip().isnumeric():
										#Qtd
										print ('Qtd ',itemQtd)
										if not itemQtd and itemQtd == '':
											itemQtd = cc.strip()

										#FIX 21-12-2022; Check if SN is same as QTD
										print ('len description')
										print (len(filtered_divs['DESCRIPTION']))
										if len(filtered_divs['DESCRIPTION']) > 1:
											print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
										#filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' SN: ' + tmp_sn


										#Check if CODE NO in Headers...
										if 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and idx == 1:
											print ('itemCode ', itemCode)
											if not itemCode:
												itemCode = cc.strip()

									else:
										print('String...')
										if idx == 0:
											#First is a Number but OCR was wrong... FIX
											print ('First is a Number but OCR was wrong... FIX ')
											print ('itemCode ',itemCode)
											print ('tmpitemCode ',tmpitemCode)
											if not itemCode and tmpitemCode:
												itemCode = tmpitemCode
										elif not itemQtd and not tmpdescricao:
											itemQtd = 0	#Has ERROR WHEN OCR so no QTD as number returned...

										else:
											#Check if header Code No exists... and if idx 1
											if idx == 1 and 'CODE NO' in palavras_no_header:
												print ('itemCode ', itemCode)
												if not itemCode:
													itemCode = cc.strip().replace('©','').replace('«','')
												#frappe.throw(porra)
											else:
												#Avoid -
												if cc.strip() == '-' or cc.strip() == '—':
													print (' SKIP adding this —')
												else:
													tmpdescricao = cc.strip() + ' ' + tmpdescricao
								if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
									#Add SN JSTJPB7CX5N4008215 to Description
									#tmpdescricao = tmpdescricao + 'SN: ' + cc
									print ('adiciona SN: por algum motivo...')
									tmpdescricao = ' SN: ' + cc
									palavraexiste_item = False
								elif len(fsup.strip().split()) == 1:
									#Has SN bu might be with a DOT the SN

									#Because Header has Description of Goods...
									if not itemCode:
										#itemcode = cc.strip()
										if cc.isnumeric():
											print ('PODE SER CODIGO ou QUANTIDADE ou PRECO, TOTAL.... dos ITENS')
											if len(cc) <= 2: # or len(cc) == 3:
												print ('contaLinhas ', contaLinhas)
												print ('countlines ', countlines)
												print ('cc.strip() ',cc.strip())
												print ('linhaAnterior ',linhaAnterior)

												#if linhaem_branco and linhaAnterior == 'TOTAL':
													#Contador...
												#	filtered_divs['COUNTER'].append(cc.strip())
												if not linhaAnterior == 'RATE' and not linhaAnterior == 'TOTAL':
													filtered_divs['COUNTER'].append(cc.strip())
												if linhaAnterior == 'RATE':
													filtered_divs['QUANTITY'].append(cc.strip())
													linhaAnterior = 'QUANTITY'
												elif linhaAnterior == 'TOTAL':
													print ('Carton Carton Carton ', cc.strip())
													linhaAnterior = 'CARTON'
													if linhaem_branco:
														linhaem_branco = False
														print ('SET linhaem_branco FALSE')
												elif int(cc.strip()) > 6:
													print (filtered_divs['COUNTER'])
													#frappe.throw(porra)
										elif len(cc.strip()) > 5:
											print ('Descricao.... dos ITENS')
											frappe.throw(porra)

									elif not tmp_sn_added:
										print ('Has SN bu might be with a DOT the SN')
										print (fsup.strip())

										#Check if CODE NO in header.. not SERIAL NUMBER!
										if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
											print ('NOT ADDING SN: bcs might not be; is Description continuation...')
											tmpdescricao = ' ' + cc
										else:
											tmpdescricao = ' SN: ' + cc
										palavraexiste_item = False
										itemCode = ''
								elif 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
									if not itemCode and idx == 1:
										#Check if has DOT !!!!
										if cc.find('.') != -1:
											itemCode = cc.strip().replace('(','')


								print ('tmpQtd ', itemQtd)
								print ('tmpdescricao ', tmpdescricao)
								print ('primeiroRegisto ',primeiroRegisto)
								print (len(fsup.split()))
								if idx == len(fsup.split())-1:
									print ('para')
									if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
										print('continua')
									elif len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1:
										print ('NUMERO SERIE.... ADD to DESCRIPTION')
									elif not re.match(cash_pattern,cc):
										tmpdescricao = ''
										avoidADDING = True
										print ('FEZ BREAK')
										break
						else:
							print ('=====PORTUGUES')
							cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'

							for idx,cc in reversed(list(enumerate(fsup.split()))):
								print ('===== IDX0 PORTUGUES ======')
								print ('idx ',idx)
								print ('cc ',cc)

								#Check if cash
								print (re.match(cash_pattern,cc))
								print (cc.strip().isnumeric())

								#If last(first) is not Numeric; No longer ITEMs...
								#if primeiroRegisto == False:
								#	palavrasexiste_header = False
								#	break

								#More than 1 can be Items...
								print ('fsup.strip().split() ', fsup.strip().split())
								print ('len(fsup.strip().split()) ', len(fsup.strip().split()))
								print ('palavras_no_header ', palavras_no_header)

								#Check if AOA at end
								if len(fsup.split()) > 1:
									if fsup.split()[1] == 'AOA' or fsup.split()[1] == 'AKZ' or fsup.split()[1] == 'KZ':
										#cc = fsup.split()[0]
										print ('REMOVED CURRENCY AOA from cc')

								if len(fsup.strip().split()) > 1:
									if re.match(cash_pattern,cc):
										if not itemTotal:
											itemTotal = cc.strip()
										elif not itemRate:
											#Check if has VAT
											if 'IVA' in palavras_no_header and not itemIVA:
												itemIVA = cc.strip()
												print ('aqui add itemIVA')
											elif 'PREÇO' in palavras_no_header and 'TOTAL' in palavras_no_header and 'IVA' in palavras_no_header and ('VALOR LIQ.' in palavras_no_header or 'VALOR LIQUIDO' in palavras_no_header):
												if not tmpamount:
													tmpamount = cc.strip()
													print ('aqui add tmpamount')
												elif not itemRate:
													itemRate = cc.strip()
													print ('aqui add itemRate II')

											else:
												itemRate = cc.strip()
												print ('aqui add itemRate')
										primeiroRegisto = False
									elif cc.strip().isnumeric():
										#Qtd
										print ('Qtd ',itemQtd)
										if not itemQtd and itemQtd == '':
											itemQtd = cc.strip()

										#FIX 21-12-2022; Check if SN is same as QTD
										print ('len description')
										print (len(filtered_divs['DESCRIPTION']))
										if len(filtered_divs['DESCRIPTION']) > 1:
											print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
										#filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' SN: ' + tmp_sn


										#Check if CODE NO in Headers...
										if 'CODE NO' in palavras_no_header  or 'CODE' in palavras_no_header and idx == 1:
											print ('itemCode ', itemCode)
											if not itemCode:
												itemCode = cc.strip()

									else:
										print('String...')
										if idx == 0:
											#First is a Number but OCR was wrong... FIX
											print ('First is a Number but OCR was wrong... FIX ')
											print ('itemCode ',itemCode)
											print ('tmpitemCode ',tmpitemCode)
											if not itemCode and tmpitemCode:
												itemCode = tmpitemCode
										elif not itemQtd and not tmpdescricao:
											itemQtd = 0	#Has ERROR WHEN OCR so no QTD as number returned...

										else:
											#Check if header Code No exists... and if idx 1
											if idx == 1 and 'CODE NO' in palavras_no_header:
												print ('itemCode ', itemCode)
												if not itemCode:
													itemCode = cc.strip().replace('©','').replace('«','')
												#frappe.throw(porra)
											else:
												#Avoid -
												if cc.strip() == '-' or cc.strip() == '—':
													print (' SKIP adding this —')
												else:
													tmpdescricao = cc.strip() + ' ' + tmpdescricao
								if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
									#Add SN JSTJPB7CX5N4008215 to Description
									#tmpdescricao = tmpdescricao + 'SN: ' + cc
									print ('adiciona SN: por algum motivo...')
									tmpdescricao = ' SN: ' + cc
									palavraexiste_item = False
								elif len(fsup.strip().split()) <= 2:	#Was 1 but might be 1000 AOA
									#Has SN bu might be with a DOT the SN

									#Because Header has Description of Goods...
									print ('NOT itemCode ', itemCode)
									if not itemCode:
										#itemcode = cc.strip()
										if cc.isnumeric() or cc[:1].isnumeric():
											print ('PODE SER CODIGO ou QUANTIDADE ou PRECO, TOTAL.... dos ITENS')
											if len(cc) <= 2: # or len(cc) == 3:
												print ('contaLinhas ', contaLinhas)
												print ('countlines ', countlines)
												print ('cc.strip() ',cc.strip())
												print ('linhaAnterior ',linhaAnterior)
												print ('Quantity ', len(filtered_divs['QUANTITY']))
												print ('Quantity ',filtered_divs['QUANTITY'])
												if len(filtered_divs['QUANTITY']) == 1 and filtered_divs['QUANTITY'][0] == '':
													filtered_divs['QUANTITY'].remove(filtered_divs['QUANTITY'][0])
													print ('Deleted QUANTIty EMPTY...')

												#if linhaem_branco and linhaAnterior == 'TOTAL':
													#Contador...
												#	filtered_divs['COUNTER'].append(cc.strip())
												if not linhaAnterior == 'RATE' and not linhaAnterior == 'TOTAL' and not len(filtered_divs['QUANTITY']) == 0:
													if not linhaAnterior == 'QUANTITY':
														filtered_divs['COUNTER'].append(cc.strip())

												if linhaAnterior == 'RATE':
													filtered_divs['QUANTITY'].append(cc.strip())
													linhaAnterior = 'QUANTITY'
												elif linhaAnterior == 'TOTAL':
													print ('Carton Carton Carton ', cc.strip())
													linhaAnterior = 'CARTON'
													if linhaem_branco:
														linhaem_branco = False
														print ('SET linhaem_branco FALSE')
												elif int(cc.strip()) > 6:
													print (filtered_divs['COUNTER'])
													#frappe.throw(porra)
												elif linhaAnterior == 'DESCRIPTION' and len(filtered_divs['QUANTITY']) == 0:
													filtered_divs['QUANTITY'].append(cc.strip())
													linhaAnterior = 'QUANTITY'
													print ('111 Added QUANTITY')
												elif linhaAnterior == 'QUANTITY' and len(filtered_divs['QUANTITY']) > 0:
													filtered_divs['QUANTITY'].append(cc.strip())
													linhaAnterior = 'QUANTITY'
													print ('222 Added QUANTITY')
											elif len(cc) > 2:
												#Pode ser Preco ou TOTAL
												print ('Pode ser Preco ou TOTAL')
												print ('contaLinhas ', contaLinhas)
												print ('countlines ', countlines)
												print ('cc.strip() ',cc.strip())
												print ('linhaAnterior ',linhaAnterior)
												print ('Rate ', len(filtered_divs['RATE']))
												print (filtered_divs['RATE'])
												if len(filtered_divs['RATE']) == 1 and filtered_divs['RATE'][0] == '':
													filtered_divs['RATE'].remove(filtered_divs['RATE'][0])
													print ('REMOVED EMPTY RATE ... ')

												print ('+++++')
												if linhaAnterior == 'QUANTITY' and len(filtered_divs['RATE']) == 0:
													filtered_divs['RATE'].append(cc.strip())
													linhaAnterior = 'RATE'
													print ('111 Added RATE')
													avoidADDING = True
												elif linhaAnterior == 'RATE' and len(filtered_divs['RATE']) >= 1 and not '%' in cc.strip():
													#Avoid adding IVA %
													filtered_divs['RATE'].append(cc.strip())
													linhaAnterior = 'RATE'
													print ('2222 Added RATE')
													avoidADDING = True
												elif linhaAnterior == 'RATE' and '%' in cc.strip():
													#Check if 14/7/5 means IVA
													if cc.strip() == '14%' or cc.strip() == '7%' or cc.strip() == '5%':
														#IVA
														print ('IVA but has no DESCOUNT BEFORE..')
														print (len(filtered_divs['IVA']))
														print (filtered_divs['IVA'])
														if len(filtered_divs['IVA']) == 1 and filtered_divs['IVA'][0] == '':
															filtered_divs['IVA'].remove(filtered_divs['IVA'][0])
															print ('***** REMOVED EMPTY IVA.... ')

														filtered_divs['IVA'].append(cc.strip())
														linhaAnterior = 'IVA'
														print ('0000 Added IVA')
														avoidADDING = True

													else:
														linhaAnterior = 'DEC'	#DEsconto
														print ('DESCONTOs.....')
														avoidADDING = True

												elif linhaAnterior == 'DEC' and '%' in cc.strip():
													#IVA because of %
													print ('IVA because of % ')
													filtered_divs['IVA'].append(cc.strip())
													linhaAnterior = 'IVA'
													print ('1111 Added IVA')
													avoidADDING = True

												elif linhaAnterior == 'IVA' and '%' in cc.strip():
													#Check if 14/7/5 means IVA
													if cc.strip() == '14%' or cc.strip() == '7%' or cc.strip() == '5%':
														#IVA
														print ('IVA but has no DESCOUNT BEFORE..')
														filtered_divs['IVA'].append(cc.strip())
														linhaAnterior = 'IVA'
														print ('2222 Added IVA')
														avoidADDING = True

												elif linhaAnterior == 'IVA': # and len(filtered_divs['TOTAL']) == 0:
													if len(filtered_divs['TOTAL']) == 1 and filtered_divs['TOTAL'][0] == '':
														filtered_divs['TOTAL'].remove(filtered_divs['TOTAL'][0])
														print ('REMOVED TOTAL EMPY..... ')

													filtered_divs['TOTAL'].append(cc.strip())
													linhaAnterior = 'TOTAL'
													print ('1111 Added TOTAL')
													avoidADDING = True

												elif linhaAnterior == 'TOTAL': # and len(filtered_divs['TOTAL']) == 0:
													if len(filtered_divs['TOTAL']) == 1 and filtered_divs['TOTAL'][0] == '':
														filtered_divs['TOTAL'].remove(filtered_divs['TOTAL'][0])
														print ('REMOVED TOTAL EMPY..... ')

													filtered_divs['TOTAL'].append(cc.strip())
													linhaAnterior = 'TOTAL'
													print ('2222 Added TOTAL')
													avoidADDING = True


										elif len(cc.strip()) > 5:
											print ('Descricao.... dos ITENS')
											print ('Verifica se UNIDADE/UNI -> CX, KG, etc ')
											print (cc.strip().upper())
											print ('terpalavras_item ',terpalavras_item)
											if cc.strip().upper() in terpalavras_item:
												print ('FAZ PARTE DAS UNIDADES DE MEDIDA.....')
												avoidADDING = True
											print (cc.strip().upper())

											#frappe.throw(porra)

									elif not tmp_sn_added:
										print ('Has SN bu might be with a DOT the SN')
										print (fsup.strip())

										#Check if CODE NO in header.. not SERIAL NUMBER!
										if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
											print ('NOT ADDING SN: bcs might not be; is Description continuation...')
											tmpdescricao = ' ' + cc
										else:
											tmpdescricao = ' SN: ' + cc
										palavraexiste_item = False
										itemCode = ''
								elif 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
									if not itemCode and idx == 1:
										#Check if has DOT !!!!
										if cc.find('.') != -1:
											itemCode = cc.strip().replace('(','')


								print ('tmpQtd ', itemQtd)
								print ('tmpdescricao ', tmpdescricao)
								print ('primeiroRegisto ',primeiroRegisto)
								print (len(fsup.split()))
								if idx == len(fsup.split())-1:
									print ('para')
									if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1:
										print('continua')
									elif len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1:
										print ('NUMERO SERIE.... ADD to DESCRIPTION')
									elif not re.match(cash_pattern,cc):
										#TEM CURRENCY; Continua o loop
										if cc.strip() != 'AOA':
											tmpdescricao = ''
											avoidADDING = True
											print ('FEZ BREAK')
											break

						#frappe.throw(porra)
						print (tmpdescricao)
						print (palavras_no_header)
						if tmpdescricao.strip() not in palavras_no_header and tmpdescricao:
							print (len(fsup.strip().split()))
							print ('split')
							print (fsup.strip().split())
							if (len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1) or (len(fsup.strip()) >= 3 and len(fsup.strip().split()) == 1):
								print (len(fsup.strip()))
								print (fsup.strip())
								print ('tmpdescricao')
								print ('tmpdescricao')
								print ('tmpdescricao')
								print ('tmpdescricao ',tmpdescricao)
								#Add to previous itemDescription
								print (filtered_divs['DESCRIPTION'])
								print (len(filtered_divs['DESCRIPTION']))
								print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
								if tmpdescricao not in filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1]:
									print ('TEM tmpdescricao')
									print (filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1])
									print (tmpdescricao)
									filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += tmpdescricao
									#frappe.throw(porra)

								tmpdescricao = ''
								print ('----')
								print (filtered_divs['DESCRIPTION'])

								#frappe.throw(porra)
							else:
								#itemDescription = tmpdescricao
								print ('t1 ', retorna_descricao(fsup.strip()))
								itemDescription = retorna_descricao(fsup.strip())
								print (itemDescription)

								#Check if Code NO exists...
								if 'CODE NO' in palavras_no_header or 'CODE' in palavras_no_header:
									if itemCode:
										tmpdescricao = itemDescription.replace(itemCode,'').strip()
										if tmpdescricao.startswith('-') or tmpdescricao.startswith('—'):
											itemDescription = tmpdescricao[1:]
										else:
											itemDescription = tmpdescricao
								print ('itemDesciption depois ', itemDescription)

						#avoidADDING = False	#When SN or Chassis not add because they are single LINE
						for ii in fsup.split(' '):
							print ('----')
							print ('ii ', ii)
							print (re.match(cash_pattern,ii))
							print (ii.strip().isnumeric())

							if len(fsup.strip()) >= 15 and len(fsup.strip().split()) == 1 and en_scan:
								print ('AVOID ADDING... was only SN')
								avoidADDING = True
							elif len(fsup.strip().split()) == 1 and en_scan:
								print ('ALERT:AVOID ADDING... was only SN')
								avoidADDING = True

							else:
								#Itemcode
								if not itemCode:
									itemCode = ii.strip()
									print ('itemcode ',itemCode)

								elif not itemDescription:
									#itemDescription = ii.strip()
									print ('t2 ', fsup.strip())
									print ('t2 ', retorna_descricao(fsup.strip()))
									itemDescription = retorna_descricao(fsup.strip()) #.replace(str(itemQtd),''))
									print (itemDescription)

									#Check if same as TOTAL LINE ... Might be Serial Numbers or just one with SPACEs...
									print (fsup.strip())
									if itemDescription == fsup.strip():
										if not "(" in fsup.strip() and not "|" in fsup.strip():
											print ('IGUAl... IS Serial Number')
											#frappe.throw(porra)

								elif itemCode and itemDescription and not ii.strip().isnumeric():
									print ('tem itemcode e itemDescription')
									if not en_scan:
										#Deal with Numbers
										if not ii.find(',') != -1: #re.match(cash_pattern,ii): # and ii.find(',') != -1:
											#Deal with Unit
											if not ii.strip() in terpalavras_item:
												#itemDescription = itemDescription + " " + ii.strip()
												print ('t3 ', retorna_descricao(fsup.strip()))
												itemDescription = retorna_descricao(fsup.strip()) #.replace(itemQtd,''))
												print (itemDescription)
								if ii.strip().isnumeric():
									print ('number')
									if not itemQtd and itemQtd == '':
										print ('check itemcode ', itemCode)
										itemQtd = ii.strip()
									elif not itemRate:
										print ('tamanho')
										print (len(ii))

										if len(ii) == 2:
											tmprate = ii.strip()
										else:
											if tmprate != '':
												itemRate = str(tmprate) + str(ii.strip())
												print ('aqui0 ',itemRate)
											else:
												itemRate = ii.strip()
												tmprate = ''
												print ('OUaqui1 ',itemRate)
									elif not itemTotal:
										print ('aqui total')
										itemTotal = ii.strip()
									elif not itemIVA:
										if not en_scan:
											itemIVA = ii.strip()
								elif re.match(cash_pattern,ii) and ii.find(',') != -1:
									#Tem Decimais...
									print ('Tem Decimais...')
									if not itemQtd and itemQtd == '':
										itemQtd = ii.strip()
									elif not itemRate:
										if tmprate != '':
											itemRate = str(tmprate) + str(ii.strip())
											tmprate = ''
											print ('aqui ',itemRate)
										else:
											itemRate = ii.strip()
											tmprate = ''
											print ('OUaqui ',itemRate)

										#itemRate = ii.strip()
									elif not itemTotal:
										print ('OUaqui total')
										if ii.strip() != '0,00':
											itemTotal = ii.strip()
									elif not itemIVA:
										if not en_scan:
											itemIVA = ii.strip()

						print ('avoidADDING ',avoidADDING)
						if avoidADDING:
							#Check if same as TOTAL LINE ... Might be Serial Numbers or just one with SPACEs...
							print (fsup.strip())
							if itemDescription == fsup.strip():
								if not "(" in fsup.strip() and not "|" in fsup.strip() and not ":" in fsup.strip() and not "BAIRRO" in fsup.strip():
									print ('IGUAl... IS Serial Number')
									print ('TO THINK BETTER how to DETECT SERIAL NUMBERS....')
									#frappe.throw(porra)

						print ('CORRIGIR QUNATIDADES ZERO')
						print ('itemQtd ',itemQtd)
						if itemQtd != '' and itemQtd == 0:
							if itemTotal and itemRate:
								print ('itemQtd ',itemQtd)
								print ('itemRate ',itemRate)
								print ('itemTotal ',itemTotal)
								print (str(float(itemTotal.replace(',','')) / float(itemRate.replace(',',''))))

								if float(itemTotal.replace(',','')) / float(itemRate.replace(',','')) == 0:
									itemQtd = str(1)
								else:
									itemQtd = str(float(itemTotal.replace(',','')) / float(itemRate.replace(',','')))
							#frappe.throw(porra)


						print ('Items')
						print ('contaLinhas ',contaLinhas)
						print ('countlines ',countlines)
						print ('itemCode ',itemCode)
						print ('itemDescription N/REPLACE ',itemDescription)
						print ('itemDescription ',itemDescription.replace(str(itemQtd),''))
						print ('itemQtd ',itemQtd)
						print ('itemRate ',itemRate)
						print ('itemTotal ',itemTotal)
						print ('itemIVA ',itemIVA)

						print ('itemDescriptionXXXXXX ', itemDescription)

						print ('avoidADDING ',avoidADDING)

						#frappe.throw(porra)
						if not avoidADDING:
							filtered_divs['COUNTER'].append(countlines)
							filtered_divs['ITEM'].append(itemCode)
							#FIX 22-12-2022; removed itemQtd
							if itemDescription:
								if len(itemCode) != len(itemDescription) and len(itemCode) > 5:
									#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').replace(str(itemQtd),'').replace(itemCode,'').strip())
									filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').replace(itemCode,'').strip())
								else:
									#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').replace(str(itemQtd),'').strip())
									filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').strip())
							filtered_divs['QUANTITY'].append(itemQtd)
							filtered_divs['RATE'].append(itemRate)
							filtered_divs['TOTAL'].append(itemTotal)
							filtered_divs['IVA'].append(itemIVA)
							countlines += 1
							print ('Added COUNTER,ITEM,DESCRIPTION,RATE,TOTAL,IVA')
						elif linhaAnterior == 'DESCRIPTION' and 'CODIGO' in palavras_no_header and linhaem_branco:
							#Add only ITEM and DESCRIPTION
							filtered_divs['COUNTER'].append(countlines)
							filtered_divs['ITEM'].append(itemCode)
							if fsup.strip() != '':
								filtered_divs['DESCRIPTION'].append(fsup.strip())
							countlines += 1
							print ('Added COUNTER,ITEM,DESCRIPTION')

						#frappe.throw(porra)
					else:
						print ('Descricao do ITEM....')
						print ('Descricao do ITEM....')
						print (fsup.strip())
						print ('filtered_divs COUNTER')
						print (filtered_divs['COUNTER'])
						print (len(filtered_divs['COUNTER']))
						#FIX 27-01-2023; REMOVED FOR NOW
						#if filtered_divs['COUNTER']:
						print (len(filtered_divs['DESCRIPTION']))
						print ('linhaem_branco ', linhaem_branco)
						if linhaem_branco:
							print ('Mudou de REGISTO....')
							print ('Mudou de REGISTO....')

							print ('linhaAnterior ',linhaAnterior)
							#Check if Starts with $ can be Unitprice or SUM
							if fsup.strip().startswith('$') and linhaAnterior == 'DESCRIPTION':
								#Rate
								filtered_divs['RATE'].append(fsup.strip().replace('$',''))
								linhaAnterior = 'RATE'
								if not supplierMoeda:
									supplierMoeda = "USD"
							elif fsup.strip().startswith('$') and linhaAnterior == 'QUANTITY':
								#TOTAL /SUM
								filtered_divs['TOTAL'].append(fsup.strip().replace('$',''))
								linhaAnterior = 'TOTAL'
							elif linhaAnterior == 'QUANTITY' and fsup.strip() == 'SET':
								print ('SET SET SET SET ', fsup.strip())
								print ('WHERE to ADD SET')
								#linhaAnterior = 'UNIT'
							elif fsup.strip() == 'TOTAL':
								#End of Items Table...
								print ('End of Items Table... ')
								fim_items = True

								#Reset Counter to be same as Item
								rr = 0
								filtered_divs['COUNTER'] = []
								while rr < len(filtered_divs['ITEM']):
									filtered_divs['COUNTER'].append(rr+1)
									rr += 1


							else:
								#elif linhaAnterior != 'CARTON':
								if linhaem_branco and fsup.strip() != 'CARTON':
									if linhaAnterior == 'TOTAL' and fsup.strip().startswith('$'):
										#Add on RATE
										filtered_divs['RATE'].append(fsup.strip().replace('$',''))
										linhaAnterior = 'RATE'
									else:
										if fsup.strip() != '':
											filtered_divs['DESCRIPTION'].append(fsup.strip())
										#For this case assume First split() as CODE
										print ('Codigo ITEM')
										print (fsup.split()[0].strip())
										#If has - is a code otherwise add all Text
										if fsup.split()[0].strip().find('-') != -1:
											filtered_divs['ITEM'].append(fsup.split()[0].strip())
										else:
											#Check if COdigo on Header
											if 'CODIGO' in palavras_no_header:
												filtered_divs['ITEM'].append(fsup.split()[0].strip())
											else:
												filtered_divs['ITEM'].append(fsup.strip())
										linhaAnterior = 'DESCRIPTION'

										#Check if Counter is less
										if len(filtered_divs['COUNTER']) < len(filtered_divs['ITEM']):
											filtered_divs['COUNTER'].append(len(filtered_divs['COUNTER'])+1)
											print ('Aumenta o Counter....')
							linhaem_branco = False
						else:
							print ('linhaAnterior ',linhaAnterior)
							if linhaAnterior == 'CARTON':
								print ('Linha CARTON tem MAIS QUE NUMEROS...')
							elif len(filtered_divs['DESCRIPTION']) >= 1:
								#filtered_divs['DESCRIPTION'].append(fsup.strip())
								filtered_divs['DESCRIPTION'][len(filtered_divs['DESCRIPTION'])-1] += ' ' + fsup.strip()
							else:
								if fsup.strip() != '':
									filtered_divs['DESCRIPTION'].append(fsup.strip())
							linhaAnterior = 'DESCRIPTION'
							#print (filtered_divs['DESCRIPTION'])
							#frappe.throw(porra)
						print (filtered_divs['COUNTER'])
						print (filtered_divs['DESCRIPTION'])
						print (filtered_divs['ITEM'])
						print (filtered_divs['QUANTITY'])
						print (filtered_divs['RATE'])
						print (filtered_divs['TOTAL'])

						#if 'BUTTON SET FOR RANG' in fsup.strip(): # or 'cruiser LC200 upgrade to 2022' in fsup.strip(): # or 'F142-B1-Bodykit For Land' in fsup.strip():
						#	frappe.throw(porra)

				#frappe.throw(porra)
				#if tmp_sn == 'SN: 5549545':
				#	frappe.throw(porra)
				print ('NO FIM contapalavras_header')
				print ('contapalavras_header ',contapalavras_header)
				print ('TEM linhaem_branco ',linhaem_branco)
				if contapalavras_header >= 5:
					palavrasexiste_header = True
					if fsup.strip() in palavras_no_header_ultimoHeader:
						if palavrasexiste_header:
							palavrasexiste_header = True
						else:
							palavrasexiste_header = False
							print ('palavrasexiste_header SET TO FALSE ')
							frappe.throw(porra)
					else:
						if not linhaem_branco:
							#TO Add TEXT to previous Description...
							palavrasexiste_header = True
						else:
							palavrasexiste_header = False
							print ('REMOVED HERE palavrasexiste_header = False ')
							print ('linhaAnterior ', linhaAnterior)
							if linhaAnterior == 'DESCRIPTION' or linhaAnterior == 'QUANTITY':
								palavrasexiste_header = True
							elif linhaAnterior == 'RATE' or linhaAnterior == 'DEC' or linhaAnterior == 'IVA':
								palavrasexiste_header = True
							elif linhaAnterior == 'TOTAL':
								palavrasexiste_header = True


				#if "527041" in fsup.strip() or "KS 527041 K" in fsup.strip():
				#	frappe.throw(porra)

				if "244 913400191 923323564 pjpa65@gmail.com" in fsup.strip() or "244 913400191 923323564" in fsup.strip():
					frappe.throw(porra)

				#if "1HZ O/G" in fsup.strip():
				#	frappe.throw(porra)

				#if "4680569" in fsup.strip(): # "5417178772" in fsup.strip(): #if "0.15065" in fsup.strip():
				#	print (filtered_divs['DESCRIPTION'])
					#filtered_divs['DESCRIPTION'].append(itemDescription.replace('|','').replace(';','').strip())
				#	if palavrasexiste_header:
				#		print ('supplierNIF ', supplierNIF)
				#	frappe.throw(porra)

			#if itemsSupplierInvoice:
			#Already has list of list... to Append

	print ('empresaSupplier ',empresaSupplier)
	print ('supplierAddress ',supplierAddress)
	print ('email ', supplierEmail)
	print ('supplierNIF ', supplierNIF)
	print ('invoiceNumber ', invoiceNumber)

	print ('!!!!!!!!!!')
	print (len(filtered_divs['COUNTER']))
	print (filtered_divs['COUNTER'])
	print ('ITEM')
	print (len(filtered_divs['ITEM']))
	print (filtered_divs['ITEM'])
	print ('DESCRIPTION')
	print (len(filtered_divs['DESCRIPTION']))
	print (filtered_divs['DESCRIPTION'])
	print (len(filtered_divs['QUANTITY']))
	print (filtered_divs['QUANTITY'])
	print (len(filtered_divs['RATE']))
	print (filtered_divs['RATE'])
	print (len(filtered_divs['TOTAL']))
	print (filtered_divs['TOTAL'])
	print ('IVA +++++++')
	print (len(filtered_divs['IVA']))
	print (filtered_divs['IVA'])
	if len(filtered_divs['IVA']) == 1:
		#Check if empty or null
		if filtered_divs['IVA'][0] == "" or filtered_divs['IVA'][0] == None:
			filtered_divs['IVA'].remove(filtered_divs['IVA'][0])
			print ('Deleted empty IVA')
	print ('!!!!!!!!!!')

	#Check if More DESCRIPTION than QUANT and TOTAL
	'''
		TODO:
		Run
		ocr_pytesseract --args="['/files/FT19-132.pdf','COMPRAS','por',200]"
		to get Items on single line and compare Description + Price + IVA +  TOTAL
		If all 3 (price + iva + total) on same line and Equal means is one Record and the next TEXT/DESCRIPTION is part of the previous Line
	'''
	if not en_scan:
		print (len(filtered_divs['DESCRIPTION']))
		print (filtered_divs['DESCRIPTION'])
		print (len(filtered_divs['QUANTITY']))
		print (filtered_divs['QUANTITY'])

		if len(filtered_divs['DESCRIPTION']) > len(filtered_divs['QUANTITY']):
			print ('RECORDS not the SAME.... ')

			factSupplier_tmp = ocr_pytesseract (filefinal,"COMPRAS",'por',200)
			nextline_items = False
			contaheaders = 0

			cash_pattern = r'^[-+]?(?:\d*\,\d+\.\d+)|(?:\d*\.\d+)'

			contadordescricao = ''
			linha_embranco = False
			linha_apagada = False

			for ff_tmp in factSupplier_tmp.split('\n'):
				print ('VERIFICAR AONDE COMECA HEADER....')
				print (ff_tmp)
				print ('linha_embranco ',linha_embranco)
				print ('nextline_items ',nextline_items)
				if (ff_tmp.strip() == '' or ff_tmp.strip() == None) and nextline_items:
					linha_embranco = True

				if linha_apagada:
					print ('TERMINOU.... verify if QUANTITY and DESCRIPTION MATCH')
					print (len(filtered_divs['DESCRIPTION']))
					print (filtered_divs['DESCRIPTION'])
					print (len(filtered_divs['QUANTITY']))
					print (filtered_divs['QUANTITY'])

					if len(filtered_divs['DESCRIPTION']) == len(filtered_divs['QUANTITY']):
						print ('TERMINOU DELETING LINES... THEY ARE THE SAME... ENDINGGGGG')

						print (len(filtered_divs['DESCRIPTION']))
						print (filtered_divs['DESCRIPTION'])
						print ('Qtd')
						print (len(filtered_divs['QUANTITY']))
						print (filtered_divs['QUANTITY'])
						print ('ITEM')
						print (len(filtered_divs['ITEM']))
						print (filtered_divs['ITEM'])

						print ('Reorder Counter')
						filtered_divs['COUNTER'] = []
						contador = 0
						while contador < len(filtered_divs['ITEM']):
							filtered_divs['COUNTER'].append(contador+1)
							contador += 1

						break
					else:
						linha_apagada = False
						#To continue searching for more lines to delete....

				if ff_tmp.strip() != '' and ff_tmp.strip() != None:
					for hh in palavras_no_header:
						if hh in ff_tmp:
							contaheaders += 1
					for ffitem in en_palavras_fim_item: # = ['Metodo de Pagamento','Incidência','Total Retenção']
						if ffitem in ff_tmp:
							print ('FIM dos ITENS')
							nextline_items = False
							contaheaders = 0

					if nextline_items:
						#Sao itens da Tabela...
						print ('Sao itens da Tabela... ')
						print (ff_tmp)
						temcash = 0
						for idx,cc in reversed(list(enumerate(ff_tmp.split()))):
							if cc == "AOA" or cc == "ACA":
								print ('Moeda...')
							elif re.match(cash_pattern,cc):
								temcash += 1
						if temcash >= 2:
							#Linha tem Price and TOTAL
							#Now checks the DESCRIPTION saved and compares to see if empty line or line with not Cash belongs to where...

							for ffdivs in filtered_divs['DESCRIPTION']:
								print ('filtered_divs')
								print (ffdivs)
								print ('ff_tmp')
								print (ff_tmp)
								if ffdivs in ff_tmp:
									contadordescricao = ffdivs
									break
								else:
									tamanho = len(ffdivs.split())
									palavrasiguais = 0
									for vvv in ffdivs.split():
										if vvv in ff_tmp:
											palavrasiguais += 1
									print ('palavrasiguais ',palavrasiguais)
									print (tamanho)
									print (tamanho - palavrasiguais)
									if (tamanho - palavrasiguais) == 1:
										contadordescricao = ffdivs
										break

							print ('contadordescricao')
							print (contadordescricao)
						elif contadordescricao and linha_embranco:
							print ('JUNTA AS DESCRICOES....')
							contadordescricao1 = contadordescricao + "\n" + ff_tmp
							print ('contadordescricao1')
							print (contadordescricao1)

							print ('JUNTA AS DESCRICOES 1111....')
							contadordescricao1 = contadordescricao + "\n" + ff_tmp
							print ('contadordescricao1')
							print (contadordescricao1)

							for idx,fffdivs in enumerate(filtered_divs['DESCRIPTION']):
								print ('filtered_divs00000')
								print (fffdivs)
								print ('ff_tmp0000')
								print (ff_tmp)
								if ffdivs in ff_tmp:
									print ('MOVER PARA O ANTERIOR...')
									print ('MOVER PARA O ANTERIOR...')
									frappe.throw(porra)
								else:
									tamanho = len(fffdivs.split())
									palavrasiguais = 0
									for vvv in fffdivs.split():
										if vvv in ff_tmp:
											palavrasiguais += 1
									print ('palavrasiguais ',palavrasiguais)
									print (tamanho)
									print (tamanho - palavrasiguais)
									if (tamanho - palavrasiguais) == 1:
										contadordescricao2 = fffdivs
										print ('MOVER PARA O ANTERIOR...')
										print ('MOVER PARA O ANTERIOR...')
										print (idx)
										print (contadordescricao + '\n' + contadordescricao2)
										print (filtered_divs['DESCRIPTION'])
										print ('UPDATE filtered_divs **********')
										filtered_divs['DESCRIPTION'][idx-1] = contadordescricao + ' ' + contadordescricao2
										if len(filtered_divs['DESCRIPTION']) == len(filtered_divs['ITEM']) or len(filtered_divs['ITEM']) > len(filtered_divs['DESCRIPTION']):
											#FIX ITEM TOO
											print ('ITEM TO REMOVE')
											print (filtered_divs['ITEM'][idx])
											print ('OU ', filtered_divs['ITEM'][idx-1])
											filtered_divs['ITEM'].remove(filtered_divs['ITEM'][idx])

										print (filtered_divs['DESCRIPTION'])
										filtered_divs['DESCRIPTION'].remove(filtered_divs['DESCRIPTION'][idx])
										print ('depois ', filtered_divs['DESCRIPTION'])
										print ('depois ITEM ', filtered_divs['ITEM'])
										#frappe.throw(porra)
										linha_apagada = True

										break
						else:
							print ('Might be continuity text from the previous LINE...')
							print ('Might be continuity text from the previous LINE...')
							print (ff_tmp)
							#REMOVED FOR NOW; for now if no split skip
							#if len(ff_tmp.split()) >= 3:

							linha_embranco = True
							if contadordescricao and linha_embranco:
								print ('JUNTA AS DESCRICOES 000....')
								contadordescricao1 = contadordescricao + "\n" + ff_tmp
								print ('contadordescricao1')
								print (contadordescricao1)

								for idx,fffdivs in enumerate(filtered_divs['DESCRIPTION']):
									print ('filtered_divs00000')
									print (fffdivs)
									print ('ff_tmp0000')
									print (ff_tmp)
									if ffdivs in ff_tmp:
										print ('MOVER PARA O ANTERIOR...')
										print ('MOVER PARA O ANTERIOR...')
										frappe.throw(porra)
									else:
										tamanho = len(fffdivs.split())
										palavrasiguais = 0
										for vvv in fffdivs.split():
											if vvv in ff_tmp:
												palavrasiguais += 1
										print ('palavrasiguais ',palavrasiguais)
										print (tamanho)
										print (tamanho - palavrasiguais)
										if (tamanho - palavrasiguais) == 1:
											contadordescricao2 = fffdivs
											print ('MOVER PARA O ANTERIOR...')
											print ('MOVER PARA O ANTERIOR...')
											print (idx)
											print (contadordescricao + '\n' + contadordescricao2)
											print (filtered_divs['DESCRIPTION'])
											print ('UPDATE filtered_divs ++++++++')
											filtered_divs['DESCRIPTION'][idx-1] = contadordescricao + ' ' + contadordescricao2
											if len(filtered_divs['DESCRIPTION']) == len(filtered_divs['ITEM']):
												#FIX ITEM TOO
												filtered_divs['ITEM'].remove(filtered_divs['ITEM'][idx])

											print (filtered_divs['DESCRIPTION'])
											filtered_divs['DESCRIPTION'].remove(filtered_divs['DESCRIPTION'][idx])
											print ('depois ', filtered_divs['DESCRIPTION'])
											print ('depois ITEM ', filtered_divs['ITEM'])
											#frappe.throw(porra)
											linha_apagada = True

											break





					if contaheaders >= 2:
						print ('Proxima linha TRUe')
						nextline_items = True

		#frappe.throw(porra)

	#Check if header has 'DESCRIÇÃO and VALOR LIQ.' means next record are itens
	#Check if line has Metodo de Pagamento means END OF Items

	data = []
	if len(filtered_divs['IVA']) > 0:
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['IVA'], filtered_divs['COUNTER']):
			if 'ITEM' in row[0]:
				continue

			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'Iva': row[5], 'COUNTER': row[6]}
			data.append(data_row)
	else:
		for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL'], filtered_divs['COUNTER']):
			if 'ITEM' in row[0]:
				continue

			data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4], 'COUNTER': row[5]}
			data.append(data_row)


	print('Supplier ', empresaSupplier)
	print ('supplieraddre ', supplierAddress)
	print ('supplierNIF ', supplierNIF)

	print ('supplierPais ', supplierPais)

	if supplierMoeda == 'AOA' or supplierMoeda == 'AKZ' or supplierMoeda == 'KZ':
		empresaPais = 'Angola'
	else:
		if not supplierPais:
			empresaPais = 'DESCONHECIDO'
		else:
			empresaPais = supplierPais
		if supplierMoeda:
			print ('supplierMoeda ',supplierMoeda)
			if supplierMoeda == "EUR":
				if not supplierPais:
					empresaPais = 'Belgium' #DEFAULT for EUR currency
			else:
				#FIX 31-12-2022; if KZ/AOA
				print (supplierMoeda.upper().strip() == 'KZ')
				print (supplierMoeda.upper().strip())
				print (supplierMoeda.upper().replace(':',''))
				if supplierMoeda.upper().replace(':','').strip() == 'KZ' or supplierMoeda.upper().replace(':','').strip() == 'AOA':
					tmppais =pycountry.countries.get(alpha_3='AGO')
				else:
					tmppais =pycountry.countries.get(numeric=pycountry.currencies.get(alpha_3=supplierMoeda.upper().replace(':','').strip()).numeric)
				print ('tmppais ',tmppais.name)
				empresaPais = tmppais.name

	print ('empresaPais ', empresaPais)

	print('Invoice', invoiceNumber)
	print('Date ', invoiceDate)
	print('Moeda ', supplierMoeda)

	#frappe.throw(porra)
	pprint(data)

	#return (empresaSupplier,invoiceNumber,invoiceDate,supplierMoeda,supplierAddress,supplierNIF,empresaPais,data)
	#FIX 23-01-2023

	stop_time = time.monotonic()
	print(round(stop_time-start_time, 2), "seconds")

	return (empresaSupplier,invoiceNumber,invoiceDate,supplierMoeda,supplierAddress,supplierNIF,supplierPais,data)



@frappe.whitelist(allow_guest=True)
def teste_ocr(ficheiro, dpi = 120, oem = 3, psm = 1):
	'''
		OCR an image file to get either the QRCODE or the Referencia do Documento and SCAN ONLINE
		Last Modified: 20-10-2022
	'''
	import cv2
	import pytesseract

	start_time = time.monotonic()

	if os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/files','')):
		filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)
	elif os.path.isfile(frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')):
		filefinal = frappe.get_site_path('public','files') + ficheiro.replace('/public/files','')
		print ('filefinal ',filefinal)
		if filefinal.startswith('.'):
			filefinal1 = "/home/frappe/frappe-bench/sites" + filefinal[1:len(filefinal)]
			filefinal = filefinal1
		print ('filefinal1 ',filefinal)

	else:
		filefinal = data

	print ('filefinal ',filefinal)

	#ficheiro = '/home/frappe/frappe-bench/sites/tools.angolaerp.co.ao/public/files/Pagto teor.jpeg'
	img = cv2.imread(filefinal)

	# Adding custom options
	#custom_config = r'--oem 3 --psm 6'
	print ('dpi ', dpi)
	print ('oem ', oem)
	print ('psm ', psm)
	custom_config = r'--dpi ' + str(dpi) + ' --oem ' + str(oem) + ' --psm ' + str(psm)
	textotemp = pytesseract.image_to_string(img, config=custom_config)

	print ('textotemp')
	#print (textotemp)
	for tt in textotemp.split('\n'):
		#LIQUIDAGAO GENERICA DE TRIBUTO
		#print (tt)
		if "230" in tt or "290" in tt:
			print ('AQUI DEVE TER NUMERO')
			print (tt)
