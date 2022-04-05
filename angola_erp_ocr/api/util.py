# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 05/04/2022


from __future__ import unicode_literals

import frappe
import angola_erp_ocr.util
from angola_erp_ocr.util import ocr_pdf
from angola_erp_ocr.util import pdf_scrape
import os

from angola_erp_ocr.angola_erp_ocr.doctype.ocr_read import ocr_read
import re

@frappe.whitelist(allow_guest=True)
def lepdfocr(data,action = "SCRAPE"):
	#TODO: add action SCRAPE or OCR
	#default will SCRAPE

	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)'
	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	ocr_tesserac = ""
	ocr_tesserac1 = ""

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
					""" File, Language, DPI """

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

def find_second_last(text, pattern):
	return text.rfind(pattern, 0, text.rfind(pattern))
