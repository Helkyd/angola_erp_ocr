# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 14/10/2022


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

@frappe.whitelist(allow_guest=True)
def lepdfocr(data,action = "SCRAPE",tipodoctype = None):
	#default is SCRAPE
	#tipodoctype if Compras means will create a Purchase Order or Invoice.


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
					if scrapeTXT[7]:
						print (scrapeTXT[7][0])
						return scrapeTXT
					else:
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
									evitapalavras =['Original','2!Via','2ºVia']
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
										supplierNIF = fsup.replace('NIF','').replace('NIF:','').strip()
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
									terpalavras_header = ['UN', 'UNIDADE', 'CAIXA', 'CX', 'Artigo', 'Descrição', 'Qtd.', 'Pr.Unit', 'Cód. Artigo', 'V.Líquido', 'V. Líquido']



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

						return (empresaSupplier,invoiceNumber,invoiceDate,supplierMoeda,supplierAddress,supplierNIF,empresaPais,data)


				else:
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

		else:
			filefinal = data

		#If no results... than change to OCR
		if ".pdf" in filefinal:
			temScrape = pdf_scrape.pdfscrape_perpage(filefinal)
			print ('RESULTADO temScrape')
			print (temScrape)
			if temScrape == None:
				return

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
			print ('IMAGE FILE')
			print ('IMAGE FILE')
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
		return ocr_pytesseract (filefinal)

		#Might use after if no results from above..
		#return ocr_pdf.ocr_pdf(input_path=data)

def find_second_last(text, pattern):
	return text.rfind(pattern, 0, text.rfind(pattern))

def ocr_pytesseract (filefinal,tipodoctype = None):
	#Podemos fazer OCR with tesseract before trying with pytesseract
	# File, Language, DPI
	#cash to include . and , ex. 44.123,00 / 44.123,97
	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'
	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	ocr_tesserac = ""
	ocr_tesserac1 = ""

	#Added to OCR COMPRAS...; 14-10-2022
	if tipodoctype != None and tipodoctype.upper() == "COMPRAS":
		print ('Tenta ocr_pytesseract.... but reading all Lines and checking for the required fields...')
		return angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'por',False,250) #ocr_tesserac
		#frappe.throw(porra)

	ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'por',False,200) #180) #200)
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

	referenciadocumento = ""


	if "RECIBO DE PAGAMENTO" in ocr_tesserac or "EMITIDO EM: RF PORTAL DO CONTRIBUINTE" in ocr_tesserac or "EMITIDO EM: RF PORTAL BO CONTRIBUINTE" in ocr_tesserac or "MCX DEBIT" in ocr_tesserac or "COMPROVATIVO DA OPERACAO" in ocr_tesserac or "COMPROVATIVO DA OPERAÇÃO" in ocr_tesserac or "Comprovativo Digital" in ocr_tesserac or "MULTICAIXA Express." in ocr_tesserac:
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

		if "MCX DEBIT" in ocr_tesserac or "Comprovativo Digital" in ocr_tesserac:
			#Check if TRANSACÇÃO
			if "TRANSACÇÃO:" in ocr_tesserac:
				print ('Transacao MCX DEBIT')
				print ('Transacao MCX DEBIT')


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
				#frappe.throw(porra)

				if "LIQUIDAÇÃO GENÉRICA DE TRIBUTO" in dd.strip():
					print ('Numero Referencia..')
					print (dd[0:dd.find(' ')])
					print (dd[0:dd.find(' ')].strip().isnumeric())
					referenciadocumento = dd[0:dd.find(' ')].strip()
					print (referenciadocumento)
					#frappe.throw(porra)
				elif "COMPROVATIVO DA OPERACAO" in dd or "COMPROVATIVO DA OPERAÇÃO" in dd:
					bfatransferencia = True
				elif "Comprovativo Digital" in dd or "MULTICAIXA Express." in dd:
					multiexpress = True
				elif "Data-Hora" in dd:
					if multiexpress:
						datadePAGAMENTO = str(dd.split(' ')[2]) + " " + str(dd.split(' ')[3])
						print ('datadePAGAMENTO ',datadePAGAMENTO)
				elif "Destinatário" in dd or "Destinatario" in dd:
					if multiexpress:
						nomeDestinatario = dd[dd.find('|')+1:len(dd)].strip()
						print ('nomeDestinatario ',nomeDestinatario)
				elif "IBAN" in dd and multiexpress:
					print ('IBAN DEST. ',re.match(iban_pattern,dd.split(' ')[2].strip()))
					if not ibanDestino:
						if re.match(iban_pattern,dd.split(' ')[2].strip()):
							ibanDestino = dd.split(' ')[2].strip()
							print ('ibanDestino ',ibanDestino)
					#frappe.throw(porra)
				elif "Montante" in dd and multiexpress:
					print ('Montante ',re.match(cash_pattern,dd.split(' ')[2].strip()))
					if not valorPAGO:
						valorPAGO = dd.split(' ')[2].strip()
						print ('valorPAGO ',valorPAGO)
						frappe.throw(porra)
				elif ("Transacção".upper() in dd.upper() or "Transacgao".upper() in dd.upper()) and multiexpress:
					if not numeroOperacao:
						numeroOperacao = dd.split(' ')[2]
						print ('numeroTransacao ',numeroOperacao)
					frappe.throw(porra)
				elif ("IBAN:" in dd or "BAN:" in dd) and multiexpress:
					if not ibanOrigem:
						ibanOrigem = dd.split(' ')[1]
						print ('ibanOrigem ',ibanOrigem)

				elif "Net Empresas por" in dd and bfatransferencia or "Nect Empresas por" in dd and bfatransferencia:
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

					Datapagamento = dia + "-" + mes + "-" + ano
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
						contaCreditada = dd.strip()[dd.strip().rfind(' '):].strip()
						print ('contaCreditada ',contaCreditada)
					elif not contaOrigem:
						contaOrigem = dd.strip()[dd.strip().rfind(' '):].strip()
						print ('contaOrigem ',contaOrigem)

					#frappe.throw(porra)

				elif bfatransferencia and len(dd.split(' ')) >=13:
					#Conta numero Origem ou DESTINO
					print ('origem/destino ',dd.split(' ')[12])
					if len(dd.split(' ')[12]) == 14 and contaOrigem and contaOrigem.strip() != dd.split(' ')[12].strip():
						#Conta DESTINO
						contaCreditada = dd.split(' ')[12].strip()
						print ('contaCreditada ',contaCreditada)
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

				elif "INDUSTRIAL" in dd.strip() or "A28" in dd.strip():
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
					frappe.throw(porra)

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

				elif "N.CAIXA:" in dd or "N.CATXA:" in dd:
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



					print ('contaOrigem ',contaOrigem)
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
							contaCreditada = ibanDestino


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

				elif "Nº REFERÊNCIA DO PAGAMENTO" in dd:
					temreferenciaDar = True
				elif dd.startswith("AO06") or dd.startswith("A006") or dd.startswith("AONE") or dd.startswith("ACO6"):
					print ('IBAN....')
					print (len(dd))
					print (dd)
					print (dd.replace(',','.').replace(' ','').strip())
					tmpiban = dd.replace(',','.').replace(' ','').replace('AONE','AO06').replace('C006','0006').replace('ACO6','AO06').strip()
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
				"contaOrigem": contaOrigem,
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
		lerpdfocr = ocr_pdf.lerPdf_ocr(filefinal,6,'por')
		print ('lerpdfocr')
		print (lerpdfocr)
		if lerpdfocr and ".pdf" in lerpdfocr:
			bancoBic = False
			contaOrigem = ''
			dataEMISSAO = ''
			numeroDocumento = ''
			numeroOperacao = ''
			descricaoPagamento = ''
			valorPAGO = ''
			ibanDestino = ''

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

					#Check IF Designaçäo: Conta BIC Empresas - Moeda Nacional
					#Check fo Conta de Origem:
					if "Conta de Origem:" in val:
						contaOrigem = val[val.find('Conta de Origem:')+17:].strip()
					if "Data do movimento" in val:
						dataEMISSAO = val[val.find('Data do movimento')+18:].strip()
					if "Designaçäo: Conta BIC Empresas - Moeda Nacional" in val or "Designação: Conta BIC Empresas - Moeda Nacional" in val:
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
					if "Descrição do movimento" in val:
						descricaoPagamento = val[val.find('Descrição do movimento')+23:].strip()

					if "Valor a debitar" in val:
						valorPAGO = val[val.find('Valor a debitar')+16:].strip()

			#Return values if
			if dataEMISSAO and contaOrigem and valorPAGO:
				return {
					"bancoBic": bancoBic,
					"numeroTransacao": numeroDocumento or numeroOperacao,
					"datadePAGAMENTO": dataEMISSAO,
					"contaOrigem": contaOrigem,
					"ibanDestino": ibanDestino,
					"valorPAGO": valorPAGO
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

	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'
	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	contaOrigem = ''
	ibanDestino = ''
	numeroTransacao = ''
	dataEMISSAO = ''
	valorPAGO = ''
	mcexpress = False

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
	filtered_divs = {'ITEM': [], 'DESCRIPTION': [], 'QUANTITY': [], 'RATE': [], 'TOTAL': []}
	temitems = False

	contador = 1

	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|^([0-9][0-9])\-([0-9][0-9])\-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'
	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)|(?:\d*\.\d+\,\d+|\d+)' #r'^[-+]?(?:\d*\.\d+|\d+)'

	oldIDXDescription = 0;

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
						filtered_divs['TOTAL'].append(div.text_content().strip('\n'))
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


			'''
			if TOTALx_LEFT_BORDER < int(left) < TOTALx_RIGHT_BORDER:
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
						filtered_divs['TOTAL'].append(div.text_content().strip('\n'))
						print ('AQUI2 AQUI2 ', div.text_content().strip('\n'))


					#Check if has $ €
					if "€" in div.text_content().strip('\n'):
						moedainvoice = "Eur"
					elif "$" in div.text_content().strip('\n'):
						moedainvoice = "Usd"
			'''
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
	for row in zip(filtered_divs['ITEM'], filtered_divs['DESCRIPTION'], filtered_divs['QUANTITY'], filtered_divs['RATE'], filtered_divs['TOTAL']):
		if 'ITEM' in row[0]:
			continue

		data_row = {'ID': row[0].split(' ')[0], 'Description': row[1], 'Quantity': row[2], 'Rate': row[3], 'Total': row[4]}
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
