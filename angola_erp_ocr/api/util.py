# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 28/08/2022


from __future__ import unicode_literals

import frappe
import angola_erp_ocr.util
from angola_erp_ocr.util import ocr_pdf
from angola_erp_ocr.util import pdf_scrape
import os

from angola_erp_ocr.angola_erp_ocr.doctype.ocr_read import ocr_read
import re

import xml.etree.ElementTree as ET

@frappe.whitelist(allow_guest=True)
def lepdfocr(data,action = "SCRAPE",tipodoctype = None):
	#default is SCRAPE
	#tipodoctype if Compras means will create a Purchase Order or Invoice.


	if tipodoctype.upper() == "COMPRAS":
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
			temScrape = pdf_scrape.pdfscrape(filefinal,None,'COMPRAS')
			print ('RESULTADO COMPRAS')
			print (temScrape)


			print ('Now check the TXT generated and return the info required for creating the Invoice...')
			print ('Now check the TXT generated and return the info required for creating the Invoice...')
			ficheiro = temScrape
			#print ('ficheiro ', ficheiro)
			print ('Verify if file exists ....')
			print (frappe.get_site_path() + ficheiro)
			if os.path.isfile(ficheiro):
				tree = ET.parse(ficheiro)
			else:
				print ('Ficheiro nao existe.. ' + ficheiro)
				return ('Ficheiro nao existe.. ' + ficheiro)

			root = tree.getroot()


			facturanumero = ""
			datafactura = ""
			Cliente_Empresa = ""
			Cliente_EmpresaNIF = ""

			listadeItems = []
			listaitem = {}

			itemdescricao = ""
			itemquantidade = ""
			itempreco = ""
			itemtotal = ""

			proximalinha = False
			proximalinhaDate = False
			proximalinhaNIF = False

			proximalinhaDESCRIPTION = False

			cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)'
			date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
			iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

			#Gets Date from Invoice...
			label = pdf.pq('LTTextLineHorizontal:contains("Date")')
			left_corner = float(label.attr('x0'))
			bottom_corner = float(label.attr('y0'))
			datafactura = pdf.pq('LTTextLineHorizontal:in_bbox("%s, %s, %s, %s")' % (
        left_corner, bottom_corner - 12, left_corner + 350, bottom_corner)).text()

			print ('excuting import.....')
			for elem in root:
				print (elem)
				print ('elem.tag ',elem.tag)
				for ltpage in elem:
					print ('ltpage.tag ',ltpage.tag)
					for ltrect in ltpage:
						print ('ltrect.tag ',ltrect.tag)
						for lttextlinehor in ltrect:
							print ('linha LTTextLineHorizontal')
							print ('lttextlinehor.tag ',lttextlinehor.tag)
							print (lttextlinehor.text)
							for lttextboxhor in lttextlinehor:
								print ('linha LTTextBoxHorizontal')
								print ('lttextboxhor.tag ',lttextboxhor.tag)
								print (lttextboxhor.text.strip())

			return

			print ('excuting import.....')
			for elem in root:
				print (elem)
				print ('elem.tag ',elem.tag)
				for ltpage in elem:
					print ('ltpage.tag ',ltpage.tag)
					for ltrect in ltpage:
						print ('ltrect.tag ',ltrect.tag)
						for lttextlinehor in ltrect:
							print ('lttextlinehor.tag ',lttextlinehor.tag)
							print (lttextlinehor.text.strip())
							#print ('CASH ',re.match(cash_pattern,lttextlinehor.text))
							#print ('Date ',re.match(date_pattern,lttextlinehor.text))

							#Check what Text...
							#Invoice Number on this specific case
							if "INVOICE NO:" in lttextlinehor.text:
								facturanumero = lttextlinehor.text[lttextlinehor.text.find('INVOICE NO:')+11:]
								print ('facturanumero ',facturanumero)

							elif "Date" in lttextlinehor.text:
								proximalinhaDate = True
							elif proximalinhaDate == True:
								proximalinhaDate = False
								#Still need to check if is DATE format...
								if re.match(date_pattern,lttextlinehor.text):
									datafactura = lttextlinehor.text
									print ('datafactura ',datafactura)
							elif "CONSIGNEE NAME:" in lttextlinehor.text:
								proximalinha = True
							elif proximalinha == True:
								proximalinha = False
								Cliente_Empresa = lttextlinehor.text
								print ('Cliente_Empresa ',Cliente_Empresa)
							elif "NIF:" in lttextlinehor.text:
								Cliente_EmpresaNIF = lttextlinehor.text[lttextlinehor.text.find('NIF:')+4:]
								print ('Cliente_EmpresaNIF ',Cliente_EmpresaNIF)
							elif "ITEM" in lttextlinehor.text:
								#Next line will be order number...
								print ('Next line will be order number...')
							elif "DESCRIPTION" in lttextlinehor.text:
								#Next line description of the Item
								print ('Next line description of the Item...')
								proximalinhaDESCRIPTION = True
							elif proximalinhaDESCRIPTION == True:
								proximalinhaDESCRIPTION = False
								itemdescricao = lttextlinehor.text
								print ('itemdescricao ',itemdescricao)

							if lttextlinehor.tag == "LTFigure":
								#Pode ter Quantidade, precos,...
								print ('Pode ter Quantidade, precos,...')
								for ltfigure in lttextlinehor:
									print ('ltfigure.tag ',ltfigure.tag)
									if ltfigure.tag == "LTTextLineHorizontal":
										for lttextlinehor_figure in ltfigure:
											print ('lttextlinehor_figure.tag ',lttextlinehor_figure.tag)
											print (lttextlinehor_figure.text.strip())






				#if 'LTTextLineHorizontal' in elem.tag:
				#	print (elem.name)
				#	print (elem.name)


	elif action == "SCRAPE":
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

def ocr_pytesseract (filefinal):
	#Podemos fazer OCR with tesseract before trying with pytesseract
	# File, Language, DPI
	cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)'
	date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
	iban_pattern = r'^([A][O][O][E]|[A][O][0][6]|[A][0][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'

	ocr_tesserac = ""
	ocr_tesserac1 = ""

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
				elif ("Transacção".upper() in dd.upper() or "Transacgao".upper() in dd.upper()) and multiexpress:
					if not numeroOperacao:
						numeroOperacao = dd.split(' ')[2]
						print ('numeroTransacao ',numeroOperacao)
					frappe.throw(porra)
				elif ("IBAN:" in dd or "BAN:" in dd) and multiexpress:
					if not ibanOrigem:
						ibanOrigem = dd.split(' ')[1]
						print ('ibanOrigem ',ibanOrigem)

				elif "Net Empresas por" in dd and bfatransferencia:
					empresaOrigem0 = dd.strip()[dd.strip().find('Net Empresas por')+16:]
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
					.replace('junho','06').replace('julho','07').replace('agosto','08').replace('setembro','09').replace('outubro','10').replace('novembro','11').replace('dezembro','12')

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
					print ('empresaOrigem0 ',empresaOrigem0)
					print ('empresaOrigem1 ',empresaOrigem1)

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
					descricaoPagamento = tmpdescricao.strip()
					print ('descricaoPagamento ',descricaoPagamento)
				elif "N.º da Operação" in dd and bfatransferencia:
					numeroOperacao = dd.strip()[dd.strip().rfind(' '):].strip()
					print ('numeroOperacao ',numeroOperacao)

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
						#frappe.throw(porra)


				elif re.match(cash_pattern,dd.strip()):
					print ('VALOR PAGO. ',re.match(cash_pattern,dd.strip()))
					#if len(re.match(cash_pattern,dd.strip())) > 3:

					if mcexpress:
						#IBAN Destinatario
						if not valorPAGO:
							valorPAGO = dd.replace(' ,',',').strip()
							print ('valorPAGO mcexpress ',valorPAGO)
					elif bfatransferencia:
						if not valorPAGO:
							valorPAGO = dd.strip()
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
						print (re.match(cash_pattern,ff.strip()))
						if re.match(cash_pattern,ff.strip()):
							if bfatransferencia and not valorPAGO:
								valorPAGO = ff.strip()



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
		print ('Redo the OCR with eng, 200')
		print ('Redo the OCR with eng, 200')
		print ('Redo the OCR with eng, 200')
		ocr_tesserac = angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_document(filefinal,'eng',False,250)
		print (ocr_tesserac)

		print ('TERA DE FAZER O OCR......')
		print ('TERA DE FAZER O OCR......')
		print ('TERA DE FAZER O OCR......')
		return ocr_pdf.ocr_pdf(input_path=filefinal)
