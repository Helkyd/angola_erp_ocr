# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 23/05/2023


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
import time, datetime
from datetime import datetime, date, timedelta


#FOR CHECKING BANK....

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

import asyncio


from selenium.webdriver.chrome.options import Options


class BancoKeve_mov():

	def bancokeve_setup(self):
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--no-sandbox')
		chrome_options.add_argument('--disable-dev-shm-usage')
		chrome_options.add_experimental_option('w3c', True)
		self.driver = webdriver.Chrome('/usr/bin/chromedriver',chrome_options=chrome_options)


	async def pagina_bancokeve(self):
		#nif = "9999999999"
		driver = self.driver
		#driver.get("https://agt.minfin.gov.ao/PortalAGT/#!/servicos/consultar-nif/" + (self.nifverificar or nif))
		driver.get('https://corporate.bancokeve.ao/login.htm')

		driver.implicitly_wait(10)

		#Send username
		us = driver.find_element(By.ID,'username')
		us.send_keys('')	#Replace after with usuario

		#Send Pwd
		pw = driver.find_element(By.ID,'password')
		pw.send_keys('')	#Replace after with senha

		#d.implicitly_wait(30)

		#Click the login button
		driver.find_element(By.ID,'login-button').click()
		driver.implicitly_wait(10)

		'''
		#Check if logged in
		estaligado = False
		for ee in d.find_elements(By.CLASS_NAME,'title'):
			if "Saldo e últimos 5 movimentos" in ee.text:
				print ('Esta logged in')
				#estaligado = True
		'''

		#click Movimentos button
		driver.find_elements(By.CLASS_NAME,'link.movement-link')
		driver.get('https://corporate.bancokeve.ao/cmov_co.htm')

		'''
		for aa in d.find_elements(By.CLASS_NAME,'current-number'):
			if "Dep. Ordem Empresas - Kwanzas" in aa.text:
		'''

		print ('Tenho os Movimentos...')
		num_rows = len (driver.find_elements_by_xpath("//*[@id='cmov_co']/tbody/tr"))
		print("Rows in table are " + repr(num_rows))

		num_cols = len (driver.find_elements_by_xpath("//*[@id='cmov_co']/tbody/tr[1]/td"))
		print("Columns in table are " + repr(num_cols))

		before_XPath = "//*[@id='cmov_co']/tbody/tr["
		aftertd_XPath = "]/td["
		aftertr_XPath = "]"

		#Colunas
		#Data Valor, Numero do Documento, Numero de Operacao, Descricao, Montante AKZ
		datavalor = []
		numero_documento = []
		numero_operacao = []
		descricao_operacao = []
		montante_akz = []

		gravar_dados = False

		numerodoc = False
		numerooper = False
		descoper = False



		import re
		date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'

		for t_row in range(1, (num_rows + 1)):
			numerodoc = False
			numerooper = False
			descoper = False
			montanteakz = False

			for t_column in range(1, (num_cols + 1)):
				FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(t_column) + aftertr_XPath
				cell_text = driver.find_element_by_xpath(FinalXPath).text
				# print(cell_text, end = '               ')
				print(cell_text)

				#Verifica se formato Data
				print (re.match(date_pattern,cell_text))
				if re.match(date_pattern,cell_text):
					gravar_dados = True
					datavalor.append(cell_text)
					numerodoc = True

				elif gravar_dados == True:
					#Verifica se termina com AKZ
					if cell_text == "AKZ":
						gravar_dados = False

					elif numerodoc:
						numero_documento.append(cell_text)
						numerodoc = False
						numerooper = True
					elif numerooper:
						numero_operacao.append(cell_text)
						numerooper = False
						descoper = True
					elif descoper:
						descricao_operacao.append(cell_text)
						descoper = False
						montanteakz = True
					elif montanteakz:
						montante_akz.append(cell_text)
						montanteakz = False
						gravar_dados = False

			print()

		print ('TERMINOU.......')
		print ('datavalor ', len(datavalor))
		print (datavalor)
		print ('numero_document ', len(numero_documento))
		print (numero_documento)
		print ('numero_operacao ', len(numero_operacao))
		print (numero_operacao)
		print ('descricao_operacao ', len(descricao_operacao))
		print (descricao_operacao)
		print ('montante_akz ', len(montante_akz))
		print (montante_akz)
		print ('First record Amount ')
		print (montante_akz[0].split('\n'))
		print (montante_akz[0].split('\n')[0])



	def fechar_bancokeve(self):
		self.driver.close()


	def __init__(self,usuario_banco,senha_banco):
		self.usuario_banco, self.senha_banco = usuario_banco, senha_banco
		print (self.usuario_banco)
		print (self.senha_banco)





@frappe.whitelist(allow_guest=True)
def banco_keve_movimentos(usuario, senha,datainicio_filtro = None, datafim_filtro = None):
	'''
		Reads movimento Banco Keve
		Last Modified: 05-05-2023


	'''


	if not usuario and not senha:
		frappe.throw('Nao tem Usuario e Senha para acessar o site do Banco KEVE')

	chrome_options = Options()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--disable-dev-shm-usage')

	'''
	chrome_options.add_argument("--disable-notifications")
	chrome_options.add_argument('--verbose')
	chrome_options.add_experimental_option("prefs", {
	        "download.default_directory": "/tmp/teste>",
	        "download.prompt_for_download": False,
	        "download.directory_upgrade": True,
	        "safebrowsing_for_trusted_sources_enabled": False,
	        "safebrowsing.enabled": False
	})
	'''
	#chrome_options.add_argument('download.default_directory=/tmp')
	#prefs = {"download.default_directory" : "/tmp/teste"}

	chrome_options.add_experimental_option('w3c', True)
	#chrome_options.add_experimental_option('prefs', prefs)

	d = webdriver.Chrome('/usr/bin/chromedriver',chrome_options=chrome_options)
	d.implicitly_wait(10)
	d.get('https://corporate.bancokeve.ao/login.htm')

	#d.implicitly_wait(30)

	#Send username
	us = d.find_element(By.ID,'username')
	us.send_keys(usuario)

	#Send Pwd
	pw = d.find_element(By.ID,'password')
	pw.send_keys(senha)

	#d.implicitly_wait(30)

	#Click the login button
	d.find_element(By.ID,'login-button').click()
	#d.implicitly_wait(10)

	'''
	#Check if logged in
	estaligado = False
	for ee in d.find_elements(By.CLASS_NAME,'title'):
		if "Saldo e últimos 5 movimentos" in ee.text:
			print ('Esta logged in')
			#estaligado = True
	'''

	#click Movimentos button
	d.find_elements(By.CLASS_NAME,'link.movement-link')
	d.get('https://corporate.bancokeve.ao/cmov_co.htm')
	d.implicitly_wait(10)

	#Get based on Date ....
	d.execute_script("document.getElementsByClassName('tab tab0')[0].className.replace(' active','')")
	d.execute_script("document.getElementsByClassName('tab tab1')[0].className.replace(' tab1',' tab1 active')")
	d.execute_script("document.getElementsByClassName('tab tab1')[0].click()")

	print (d.find_elements(By.CLASS_NAME,'tab.tab1'))

	#d.find_element(By.XPATH,"//span[text()='Pesquisar']").click()
	#print (d.find_element(By.XPATH,"//span[text()='Pesquisar']"))
	#for aa in d.find_elements(By.CLASS_NAME,'tab.tab1'):
	#	print ('click...')
	#	aa.click()

	#aa = d.find_element(By.XPATH,"//span[text()='Pesquisar']")
	#aa.click()

	#Para correr varias vezes mas com datas diferentes....
	vermais_movimentos = True
	#If filled must be with the next date Statement...
	datainicio_next = ""
	datafim_next = ""	#Will always be last day of the Month

	#Colunas
	#Data Valor, Numero do Documento, Numero de Operacao, Descricao, Montante AKZ
	datavalor = []
	numero_documento = []
	numero_operacao = []
	descricao_operacao = []
	montante_akz = []

	contaloop = 0


	while vermais_movimentos == True:
		if datainicio_next:
			d.get('https://corporate.bancokeve.ao/cmov_co.htm')
			d.implicitly_wait(10)

			d.execute_script("document.getElementsByClassName('tab tab0')[0].className.replace(' active','')")
			d.execute_script("document.getElementsByClassName('tab tab1')[0].className.replace(' tab1',' tab1 active')")
			d.execute_script("document.getElementsByClassName('tab tab1')[0].click()")

			#This date will be assinged at the end of the list... if last Record date not == last day of the month
			print ('Continuacao do Statement... ', datainicio_next)
			#datainicio_hidden = d.find_element(By.ID,'hidden_CalendarDateFrom')
			#datainicio_hidden.send_keys("")
			datainicio = d.find_element(By.ID,'CalendarDateFrom')
			datafim = d.find_element(By.ID,'CalendarDateTo')

			datafim_next = datafim_filtro
			datainicio.send_keys(str(datainicio_next))
			datafim.send_keys("31-03-2023")
		else:
			datainicio = d.find_element(By.ID,'CalendarDateFrom')
			datafim = d.find_element(By.ID,'CalendarDateTo')

			if datainicio_filtro:
				print ('datainicio ', datainicio_filtro)
				datainicio.send_keys(str(datainicio_filtro))
			else:
				#Gets current Month less 1
				datainicio_filtro = get_first_day(frappe.utils.add_months(datetime.today(),-1))
				print ('datainicio_filtro ', datainicio_filtro)
				print (datetime.strptime(str(datainicio_filtro), "%Y-%m-%d").strftime("%d-%m-%Y"))
				tmp = datetime.strptime(str(datainicio_filtro), "%Y-%m-%d").strftime("%d-%m-%Y")
				datainicio_filtro = tmp

				datainicio.send_keys(str(datainicio_filtro))

			if datafim_filtro:
				print ('datafim ', datafim_filtro)
				datafim.send_keys(str(datafim_filtro))
			else:
				datafim_filtro = get_last_day(frappe.utils.add_months(datetime.today(),-1))
				print ('datafim_filtro ', datafim_filtro)
				print (datetime.strptime(str(datafim_filtro), "%Y-%m-%d").strftime("%d-%m-%Y"))
				tmp = datetime.strptime(str(datafim_filtro), "%Y-%m-%d").strftime("%d-%m-%Y")
				datafim_filtro = tmp

				datafim.send_keys(str(datafim_filtro))

		#Trying to increase the number of results returned...
		#d.execute_script("document.getElementById('nregcmov').type= ''")
		#d.execute_script("document.getElementById('nregcmov').value= '100'")

		#datafim_hidden = d.find_element(By.ID,'hidden_CalendarDateTo')
		#datafim_hidden.send_keys('20230228')

		d.find_elements(By.ID,'list-by-date')

		#Click Pesquisar
		d.execute_script("document.getElementById('list-by-date').click()")
		#d.implicitly_wait(10)
		print ('Check BOTAO VER MAIS....')
		print (d.find_elements(By.ID,'load-next-movements'))

		#print ('Check BOTAO VER MAIS CLASS....')
		#d.find_elements(By.CLASS_NAME,'nav-button next hollow')

		#print ('botao Exportar')
		#print (d.find_elements(By.XPATH("//li[contains(@title,'???exportExcel???')]/ul/li")))
		#print (d.find_element_by_xpath("//li[@title='???exportExcel???']"))
		#d.find_element_by_xpath("//li[@title='???exportExcel???']").click()
		#d.execute_script("""document.querySelector('[title="???exportExcel???"]').click()""")
		print ('HIDDeNNNNNNN')
		print (d.find_elements(By.CLASS_NAME,'nav-button.next.hollow.hidden'))
		print ('NAO HIDDENNNN')
		print (d.find_elements(By.CLASS_NAME,'nav-button.next.hollow'))

		if d.find_elements(By.CLASS_NAME,'nav-button.next.hollow.hidden'):
			print ('Botao VER MAIS ESCONDIDO.....')
			print ('Botao VER MAIS ESCONDIDO.....')
			print ('Botao VER MAIS ESCONDIDO.....')
			#No need to loop...
			vermais_movimentos = False

		elif d.find_elements(By.ID,'load-next-movements'):
			print ('By class botao not ESCONDIDO')
			print (d.find_elements(By.CLASS_NAME,'nav-button.next.hollow'))
			#d.find_elements(By.CLASS_NAME,'nav-button.next.hollow').click()
			#Get more records....
			#d.find_elements(By.ID,'load-next-movements').click()
			print ('Does not click on Next movements / VER MAIS')
			#d.execute_script("document.getElementById('load-next-movements').click()")
			d.implicitly_wait(5)
			'''
			TODO: If report does not get to last date... and this button exists...
				Should generate again from the last date DATA received to last day of the Month...
				ex. if from 01 of March to 31 and received only until 29th so,
				Generate again from 29th until 31
			'''




		print ('Tenho os Movimentos...')
		num_rows = len (d.find_elements_by_xpath("//*[@id='cmov_co']/tbody/tr"))
		#num_rows1 = d.execute_script("return document.getElementById('cmov_co').rows.length") # d.execute_script("$('#cmov_co tbody tr').length")
		print("Rows in table are " + repr(num_rows))
		#print (num_rows1)

		num_cols = len (d.find_elements_by_xpath("//*[@id='cmov_co']/tbody/tr[1]/td"))
		print("Columns in table are " + repr(num_cols))

		before_XPath = "//*[@id='cmov_co']/tbody/tr["
		aftertd_XPath = "]/td["
		aftertr_XPath = "]"


		gravar_dados = False

		numerodoc = False
		numerooper = False
		descoper = False




		date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'

		for t_row in range(1, (num_rows + 1)):
			numerodoc = False
			numerooper = False
			descoper = False
			montanteakz = False

			stop_for = False

			for t_column in range(1, (num_cols + 1)):
				FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(t_column) + aftertr_XPath
				FinalXPath00 = before_XPath + str(t_row) + aftertr_XPath
				#document.querySelectorAll("#cmov_co>tbody>tr:nth-child(20)")

				try:
					d.find_element_by_xpath(FinalXPath00)
					print ('***** ',d.find_element(By.XPATH,FinalXPath00))
					print ('+++++ ',d.find_element_by_xpath(FinalXPath00))

				except Exception as e:
					if "no such element: Unable to locate element" in str(e):
						print ('means NO MORE ITENS....')
						stop_for = True
						break
				finally:
					if stop_for == False:
						if d.find_element_by_xpath(FinalXPath00):
							cell_text = d.find_element_by_xpath(FinalXPath).text
							# print(cell_text, end = '               ')
							print (' ============')
							print(cell_text)

							#Verifica se formato Data
							#print (re.match(date_pattern,cell_text))
							if re.match(date_pattern,cell_text):
								gravar_dados = True
								datavalor.append(cell_text)
								numerodoc = True

							elif gravar_dados == True:
								#Verifica se termina com AKZ
								if cell_text == "AKZ":
									gravar_dados = False

								elif numerodoc:
									numero_documento.append(cell_text)
									numerodoc = False
									numerooper = True
								elif numerooper:
									numero_operacao.append(cell_text)
									numerooper = False
									descoper = True
								elif descoper:
									descricao_operacao.append(cell_text)
									descoper = False
									montanteakz = True
								elif montanteakz:
									montante_akz.append(cell_text)
									montanteakz = False
									gravar_dados = False

			#print()
			if stop_for:
				break
		print ('Terminou de ler a TABELA com o extracto.....')
		#Now check if last record date is == last day of the month
		print ('verificar se terminou de ler o mes....')
		print ("datafim_filtro ",datafim_filtro)
		print (datavalor[len(datavalor)-1])
		print (datafim_filtro == datavalor[len(datavalor)-1])
		if datafim_filtro == datavalor[len(datavalor)-1]:
			#End While
			vermais_movimentos = False
		else:
			#Set start date again..
			datainicio_next = datavalor[len(datavalor)-1]
			print ('datainicio_next ', datainicio_next)
			print ('contaloop ', contaloop)
			if contaloop == 2:
				vermais_movimentos = False

		contaloop += 1

	print ('TERMINOU ========================')
	print ('datavalor ', len(datavalor))
	#print (datavalor)
	print ('numero_document ', len(numero_documento))
	#print (numero_documento)
	print ('numero_operacao ', len(numero_operacao))
	#print (numero_operacao)
	print ('descricao_operacao ', len(descricao_operacao))
	#print (descricao_operacao)
	print ('montante_akz ', len(montante_akz))
	#print (montante_akz)
	print ('First record Amount ')
	print (montante_akz[0].split('\n'))
	print (montante_akz[0].split('\n')[0])

	return {'datavalor':datavalor,'numero_documento':numero_documento,'numero_operacao':numero_operacao,'descricao_operacao':descricao_operacao,'montante_akz':montante_akz}

#BANCO BFA
@frappe.whitelist(allow_guest=True)
def banco_bfa_movimentos(usuariobanco, senha,datainicio_filtro = None, datafim_filtro = None):
	'''
		Reads movimento Banco BFA
		Last Modified: 23-05-2023
		Uses REQUESTS to pass Cookie to SELENIUM and be able to filter Statements by DATE
		Loops throught all Pages to extract
		BFA reports from LAST DAY to FIRST DAY


	'''


	if not usuariobanco and not senha:
		frappe.throw('Nao tem Usuario e Senha para acessar o site do Banco BFA')

	#Format Dates to Day Month Year
	#Assuming format is 01(D)-03(<<)-2023(YY)
	if datainicio_filtro:
		datainicio_dia = datainicio_filtro[0:2]
		if datainicio_dia.startswith('0'):
			datainicio_dia = datainicio_dia.replace('0','')
		datainicio_mes = datainicio_filtro[3:5]
		#Needs to convert o TEXT
		if datainicio_mes == "01":
			datainicio_mes = 'janeiro'
		elif datainicio_mes == "02":
			datainicio_mes = 'fevereiro'
		elif datainicio_mes == "03":
			datainicio_mes = 'março'
		elif datainicio_mes == "04":
			datainicio_mes = 'abril'
		elif datainicio_mes == "05":
			datainicio_mes = 'maio'
		elif datainicio_mes == "06":
			datainicio_mes = 'junho'
		elif datainicio_mes == "07":
			datainicio_mes = 'julho'
		elif datainicio_mes == "08":
			datainicio_mes = 'agosto'
		elif datainicio_mes == "09":
			datainicio_mes = 'setembro'
		elif datainicio_mes == "10":
			datainicio_mes = 'outubro'
		elif datainicio_mes == "11":
			datainicio_mes = 'novembro'
		elif datainicio_mes == "12":
			datainicio_mes = 'dezembro'

		#Ano
		datainicio_ano = datainicio_filtro[6:10]

	if datafim_filtro:
		datafim_dia = datafim_filtro[0:2]
		if datafim_dia.startswith('0'):
			datafim_dia = datafim_dia.replace('0','')

		datafim_mes = datafim_filtro[3:5]
		#Needs to convert o TEXT
		if datafim_mes == "01":
			datafim_mes = 'janeiro'
		elif datafim_mes == "02":
			datafim_mes = 'fevereiro'
		elif datafim_mes == "03":
			datafim_mes = 'março'
		elif datafim_mes == "04":
			datafim_mes = 'abril'
		elif datafim_mes == "05":
			datafim_mes = 'maio'
		elif datafim_mes == "06":
			datafim_mes = 'junho'
		elif datafim_mes == "07":
			datafim_mes = 'julho'
		elif datafim_mes == "08":
			datafim_mes = 'agosto'
		elif datafim_mes == "09":
			datafim_mes = 'setembro'
		elif datafim_mes == "10":
			datafim_mes = 'outubro'
		elif datafim_mes == "11":
			datafim_mes = 'novembro'
		elif datafim_mes == "12":
			datafim_mes = 'dezembro'

		#Ano
		datafim_ano = datafim_filtro[6:10]


		print ('DATAS de INICIO E FIM ')
		print (datainicio_ano)
		print (datainicio_mes)
		print (datainicio_dia)

		print (datafim_ano)
		print (datafim_mes)
		print (datafim_dia)

	chrome_options = Options()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--disable-dev-shm-usage')

	'''
	chrome_options.add_argument("--disable-notifications")
	chrome_options.add_argument('--verbose')
	chrome_options.add_experimental_option("prefs", {
	        "download.default_directory": "/tmp/teste>",
	        "download.prompt_for_download": False,
	        "download.directory_upgrade": True,
	        "safebrowsing_for_trusted_sources_enabled": False,
	        "safebrowsing.enabled": False
	})
	'''
	#chrome_options.add_argument('download.default_directory=/tmp')
	#prefs = {"download.default_directory" : "/tmp/teste"}

	chrome_options.add_experimental_option('w3c', True)
	#chrome_options.add_experimental_option('prefs', prefs)

	headers = {
		'Host': 'www.bfanetempresas.ao',
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate, br',
		'Content-Type': 'application/x-www-form-urlencoded',
		'Origin': 'https://www.bfanetempresas.ao',
		'Referer': 'https://www.bfanetempresas.ao/Login/login.aspx?ReturnUrl=%2fLogin%2flogin_detail.aspx',
	}

	https_base_url = "https://www.bfanetempresas.ao/Login/login.aspx?ReturnUrl=%2fLogin%2flogin_detail.aspx"
	validation_url = "https://www.bfanetempresas.ao/Login/login.aspx"
	transacao_url = "https://www.bfanetempresas.ao/Transaccoes/CMOV_CO.aspx?idc=143&idsc=74&idl=1#no-back-button"



	d = webdriver.Chrome('/usr/bin/chromedriver',chrome_options=chrome_options)
	d.implicitly_wait(10)

	d.get(https_base_url)
	d.delete_all_cookies()

	request_cookies_browser = d.get_cookies()
	d.implicitly_wait(10)

	s = requests.Session()

	d.implicitly_wait(5)
	#passing the cookies generated from the browser to the session
	#c = [s.cookies.set(c['name'], c['value']) for c in request_cookies_browser]

	for c in request_cookies_browser:
	    s.cookies.set(c['name'], c['value'])

	s.headers.update(headers)
	form_response = s.get(validation_url, params={"userID":usuariobanco})

	d.implicitly_wait(5)

	#passing the cookie of the response to the browser
	#dict_resp_cookies = form_response.cookies.get_dict()

	#response_cookies_browser = [{'name':name, 'value':value} for name, value in dict_resp_cookies.items()]
	#c = [d.add_cookie(c) for c in response_cookies_browser]


	soup = bs(form_response.content)
	viewstate = soup.select("#__VIEWSTATE")[0]['value']
	eventvalidation = soup.select("#__EVENTVALIDATION")[0]['value']
	viewstatugenerator = soup.select("#__VIEWSTATEGENERATOR")[0]['value']

	user_data ={
		"ctl00$ctl00$Utilizador":usuariobanco,
		"ctl00$ctl00$Password": senha,
		"ctl00$ctl00$SubmitBtn": "Entrar" ,
		"__VIEWSTATE":viewstate,
		"__EVENTVALIDATION":eventvalidation,
		"__VIEWSTATEGENERATOR":viewstatugenerator,
		'__VIEWSTATEENCRYPTED':''
	}

	response = s.post(url=https_base_url, params={"userID":usuariobanco}, data=user_data,headers={'Referer': form_response.url})
	d.implicitly_wait(5)

	ultimatransacao = s.post(url=transacao_url,headers={'Referer': form_response.url})
	d.implicitly_wait(10)
	soup1 = bs(ultimatransacao.content,'html.parser')
	tabelamovimentos = soup1.find_all('table')[2]

	print (tabelamovimentos)
	#return

	#passing the cookie of the response to the browser
	dict_resp_cookies = s.cookies.get_dict()
	response_cookies_browser = [{'name':name, 'value':value} for name, value in dict_resp_cookies.items()]
	for c in response_cookies_browser:
	    d.add_cookie(c)

	dict_resp_cookies = response.cookies.get_dict()
	response_cookies_browser = [{'name':name, 'value':value} for name, value in dict_resp_cookies.items()]
	for c in response_cookies_browser:
	    d.add_cookie(c)

	d.get(transacao_url)
	d.implicitly_wait(15)
	#print (d.page_source)
	print (d.find_element(By.ID,'ctl00_ctl00_WP_CMOV_grdCMOV'))

	''' MOVED DOWN
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_rdBtnCustom')[0].checked = true")
	d.implicitly_wait(15)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].disabled = false")
	d.implicitly_wait(15)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].disabled = false")
	d.implicitly_wait(15)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].disabled = false")
	d.implicitly_wait(15)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].disabled = false")
	d.implicitly_wait(15)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].disabled = false")
	d.implicitly_wait(15)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].disabled = false")
	d.implicitly_wait(15)

	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].value = '1'")
	d.implicitly_wait(50)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].value = 'janeiro' ")
	d.implicitly_wait(50)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].value = '2023'")
	d.implicitly_wait(50)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].value = '31'")
	d.implicitly_wait(50)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].value = 'janeiro'")
	d.implicitly_wait(50)
	d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].value = '2023'")
	d.implicitly_wait(50)

	d.execute_script("$('#ctl00_ctl00_WP_CMOV_btnSubmit').click()")
	d.implicitly_wait(100)

	num_rows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
	print (num_rows)

	if num_rows == 1:
		print ('Try again...')
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_rdBtnCustom')[0].checked = true")
		d.implicitly_wait(15)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].disabled = false")
		d.implicitly_wait(15)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].disabled = false")
		d.implicitly_wait(15)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].disabled = false")
		d.implicitly_wait(15)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].disabled = false")
		d.implicitly_wait(15)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].disabled = false")
		d.implicitly_wait(15)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].disabled = false")
		d.implicitly_wait(15)

		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].value = '1'")
		d.implicitly_wait(50)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].value = 'janeiro' ")
		d.implicitly_wait(50)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].value = '2023'")
		d.implicitly_wait(50)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].value = '31'")
		d.implicitly_wait(50)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].value = 'janeiro'")
		d.implicitly_wait(50)
		d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].value = '2023'")
		d.implicitly_wait(50)

		d.execute_script("$('#ctl00_ctl00_WP_CMOV_btnSubmit').click()")
		d.implicitly_wait(100)
		numrows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
		print (numrows)

	num_cols = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr/td"))

	before_XPath = "//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr["
	aftertd_XPath = "]/td["
	aftertr_XPath = "]"

	if num_rows > 1 or numrows > 1:
		if numrows > 1: num_rows = numrows

		for t_row in range(2, (num_rows + 1)):
		    if t_row == 22: #default shows only 22 cols...
		        break

		    for t_column in range(1, (num_cols + 1)):
		        print ('CURRENT ROW ', t_row)
		        print ('CURRENT COL ', t_column)

		        if t_column == 8:
		            break

		        FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(t_column) + aftertr_XPath
		        FinalXPath00 = before_XPath + str(t_row) + aftertr_XPath
		        #document.querySelectorAll("#cmov_co>tbody>tr:nth-child(20)")
		        d.find_element_by_xpath(FinalXPath00)
		        print ('***** ',d.find_element(By.XPATH,FinalXPath00))
		        print ('+++++ ',d.find_element_by_xpath(FinalXPath00))
		        cell_text = d.find_element_by_xpath(FinalXPath).text
		        # print(cell_text, end = '               ')
		        print (' ============')
		        print(cell_text)



	print ('TERMINA AQUI .....')
	return
	'''

	#Para correr varias vezes mas com datas diferentes....
	vermais_movimentos = True
	#If filled must be with the next date Statement...
	datainicio_next = ""
	datafim_next = ""	#Will always be last day of the Month

	#Colunas
	#Data Valor, Numero do Documento, Numero de Operacao, Descricao, Montante AKZ
	datavalor = []
	numero_documento = []
	numero_operacao = []
	descricao_operacao = []
	montante_akz = []

	contaloop = 1


	while vermais_movimentos == True:
		if datainicio_next:
			d.get(transacao_url)
			d.implicitly_wait(15)

			num_rows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
			print ('Pagina seguinte CONTALOOP ')
			print (contaloop)
			print ('num_rows')
			print (num_rows)
			num_cols = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr/td"))


			#d.execute_script("document.getElementsByClassName('tab tab0')[0].className.replace(' active','')")
			#d.execute_script("document.getElementsByClassName('tab tab1')[0].className.replace(' tab1',' tab1 active')")
			#d.execute_script("document.getElementsByClassName('tab tab1')[0].click()")

			#This date will be assinged at the end of the list... if last Record date not == last day of the month
			print ('Continuacao do Statement... ', datainicio_next)
			#datainicio_hidden = d.find_element(By.ID,'hidden_CalendarDateFrom')
			#datainicio_hidden.send_keys("")
			#datainicio = d.find_element(By.ID,'CalendarDateFrom')
			#datafim = d.find_element(By.ID,'CalendarDateTo')

			#datafim_next = datafim_filtro
			#datainicio.send_keys(str(datainicio_next))
			#datafim.send_keys("31-03-2023")
		else:
			#datainicio = d.find_element(By.ID,'CalendarDateFrom')
			#datafim = d.find_element(By.ID,'CalendarDateTo')

			if datainicio_filtro and datafim_filtro:
				print ('datainicio ', datainicio_filtro)
				#datainicio.send_keys(str(datainicio_filtro))
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_rdBtnCustom')[0].checked = true")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].disabled = false")
				d.implicitly_wait(15)

				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].value = '{}' ".format(datainicio_dia)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].value = '{}' ".format(datainicio_mes)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].value = '{}'".format(datainicio_ano)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].value = '{}'".format(datafim_dia)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].value = '{}'".format(datafim_mes)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].value = '{}'".format(datafim_ano)
				d.execute_script(sscript)
				d.implicitly_wait(50)

				d.execute_script("$('#ctl00_ctl00_WP_CMOV_btnSubmit').click()")
				d.implicitly_wait(100)

				num_rows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
				print (num_rows)

				if num_rows == 1:
					print ('Try again...')
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_rdBtnCustom')[0].checked = true")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].disabled = false")
					d.implicitly_wait(15)

					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].value = '{}' ".format(datainicio_dia)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].value = '{}' ".format(datainicio_mes)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].value = '{}'".format(datainicio_ano)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].value = '{}'".format(datafim_dia)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].value = '{}'".format(datafim_mes)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].value = '{}'".format(datafim_ano)
					d.execute_script(sscript)
					d.implicitly_wait(50)

					d.execute_script("$('#ctl00_ctl00_WP_CMOV_btnSubmit').click()")
					d.implicitly_wait(100)
					numrows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
					print (numrows)

				num_cols = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr/td"))


			else:
				#Gets current Month less 1
				datainicio_filtro = get_first_day(frappe.utils.add_months(datetime.today(),-1))
				print ('datainicio_filtro ', datainicio_filtro)
				print (datetime.strptime(str(datainicio_filtro), "%Y-%m-%d").strftime("%d-%m-%Y"))
				tmp = datetime.strptime(str(datainicio_filtro), "%Y-%m-%d").strftime("%d-%m-%Y")
				datainicio_filtro = tmp

				datafim_filtro = get_last_day(frappe.utils.add_months(datetime.today(),-1))
				print ('datafim_filtro ', datafim_filtro)
				print (datetime.strptime(str(datafim_filtro), "%Y-%m-%d").strftime("%d-%m-%Y"))
				tmp = datetime.strptime(str(datafim_filtro), "%Y-%m-%d").strftime("%d-%m-%Y")
				datafim_filtro = tmp

				#Format Dates to Day Month Year
				#Assuming format is 01(D)-03(<<)-2023(YY)
				datainicio_dia = datainicio_filtro[0:2]
				if datainicio_dia.startswith('0'):
					datainicio_dia = datainicio_dia.replace('0','')
				datainicio_mes = datainicio_filtro[3:5]
				#Needs to convert o TEXT
				if datainicio_mes == "01":
					datainicio_mes = 'janeiro'
				elif datainicio_mes == "02":
					datainicio_mes = 'fevereiro'
				elif datainicio_mes == "03":
					datainicio_mes = 'março'
				elif datainicio_mes == "04":
					datainicio_mes = 'abril'
				elif datainicio_mes == "05":
					datainicio_mes = 'maio'
				elif datainicio_mes == "06":
					datainicio_mes = 'junho'
				elif datainicio_mes == "07":
					datainicio_mes = 'julho'
				elif datainicio_mes == "08":
					datainicio_mes = 'agosto'
				elif datainicio_mes == "09":
					datainicio_mes = 'setembro'
				elif datainicio_mes == "10":
					datainicio_mes = 'outubro'
				elif datainicio_mes == "11":
					datainicio_mes = 'novembro'
				elif datainicio_mes == "12":
					datainicio_mes = 'dezembro'

				#Ano
				datainicio_ano = datainicio_filtro[6:10]

				datafim_dia = datafim_filtro[0:2]
				if datafim_dia.startswith('0'):
					datafim_dia = datafim_dia.replace('0','')

				datafim_mes = datafim_filtro[3:5]
				#Needs to convert o TEXT
				if datafim_mes == "01":
					datafim_mes = 'janeiro'
				elif datafim_mes == "02":
					datafim_mes = 'fevereiro'
				elif datafim_mes == "03":
					datafim_mes = 'março'
				elif datafim_mes == "04":
					datafim_mes = 'abril'
				elif datafim_mes == "05":
					datafim_mes = 'maio'
				elif datafim_mes == "06":
					datafim_mes = 'junho'
				elif datafim_mes == "07":
					datafim_mes = 'julho'
				elif datafim_mes == "08":
					datafim_mes = 'agosto'
				elif datafim_mes == "09":
					datafim_mes = 'setembro'
				elif datafim_mes == "10":
					datafim_mes = 'outubro'
				elif datafim_mes == "11":
					datafim_mes = 'novembro'
				elif datafim_mes == "12":
					datafim_mes = 'dezembro'

				#Ano
				datafim_ano = datafim_filtro[6:10]
				print ('====================== DATAS de INICIO E FIM ')
				print (datainicio_ano)
				print (datainicio_mes)
				print (datainicio_dia)

				print (datafim_ano)
				print (datafim_mes)
				print (datafim_dia)

				d.execute_script("$('#ctl00_ctl00_WP_CMOV_rdBtnCustom')[0].checked = true")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].disabled = false")
				d.implicitly_wait(15)
				d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].disabled = false")
				d.implicitly_wait(15)

				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].value = '{}' ".format(datainicio_dia)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].value = '{}' ".format(datainicio_mes)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].value = '{}'".format(datainicio_ano)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].value = '{}'".format(datafim_dia)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].value = '{}'".format(datafim_mes)
				d.execute_script(sscript)
				d.implicitly_wait(50)
				sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].value = '{}'".format(datafim_ano)
				d.execute_script(sscript)
				d.implicitly_wait(50)

				d.execute_script("$('#ctl00_ctl00_WP_CMOV_btnSubmit').click()")
				d.implicitly_wait(100)

				num_rows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
				print (num_rows)

				if num_rows == 1:
					print ('Try again...')
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_rdBtnCustom')[0].checked = true")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].disabled = false")
					d.implicitly_wait(15)
					d.execute_script("$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].disabled = false")
					d.implicitly_wait(15)

					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_day_dd')[0].value = '{}' ".format(datainicio_dia)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_month_dd')[0].value = '{}' ".format(datainicio_mes)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateFrom_year_dd')[0].value = '{}'".format(datainicio_ano)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_day_dd')[0].value = '{}'".format(datafim_dia)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_month_dd')[0].value = '{}'".format(datafim_mes)
					d.execute_script(sscript)
					d.implicitly_wait(50)
					sscript = "$('#ctl00_ctl00_WP_CMOV_ctrlDateTo_year_dd')[0].value = '{}'".format(datafim_ano)
					d.execute_script(sscript)
					d.implicitly_wait(50)

					d.execute_script("$('#ctl00_ctl00_WP_CMOV_btnSubmit').click()")
					d.implicitly_wait(100)
					numrows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
					print (numrows)

				num_cols = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr/td"))



		#Trying to increase the number of results returned...
		#d.execute_script("document.getElementById('nregcmov').type= ''")
		#d.execute_script("document.getElementById('nregcmov').value= '100'")

		#datafim_hidden = d.find_element(By.ID,'hidden_CalendarDateTo')
		#datafim_hidden.send_keys('20230228')

		'''
		d.find_elements(By.ID,'list-by-date')

		#Click Pesquisar
		d.execute_script("document.getElementById('list-by-date').click()")
		#d.implicitly_wait(10)
		print ('Check BOTAO VER MAIS....')
		print (d.find_elements(By.ID,'load-next-movements'))

		print ('HIDDeNNNNNNN')
		print (d.find_elements(By.CLASS_NAME,'nav-button.next.hollow.hidden'))
		print ('NAO HIDDENNNN')
		print (d.find_elements(By.CLASS_NAME,'nav-button.next.hollow'))

		if d.find_elements(By.CLASS_NAME,'nav-button.next.hollow.hidden'):
			print ('Botao VER MAIS ESCONDIDO.....')
			print ('Botao VER MAIS ESCONDIDO.....')
			print ('Botao VER MAIS ESCONDIDO.....')
			#No need to loop...
			vermais_movimentos = False

		elif d.find_elements(By.ID,'load-next-movements'):
			print ('By class botao not ESCONDIDO')
			print (d.find_elements(By.CLASS_NAME,'nav-button.next.hollow'))
			#d.find_elements(By.CLASS_NAME,'nav-button.next.hollow').click()
			#Get more records....
			#d.find_elements(By.ID,'load-next-movements').click()
			print ('Does not click on Next movements / VER MAIS')
			#d.execute_script("document.getElementById('load-next-movements').click()")
			d.implicitly_wait(5)

		'''

		'''
		before_XPath = "//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr["
		aftertd_XPath = "]/td["
		aftertr_XPath = "]"
		'''

		if num_rows > 1 or numrows > 1:
			if numrows > 1: num_rows = numrows
			'''
			for t_row in range(2, (num_rows + 1)):
			    if t_row == 22: #default shows only 22 cols...
			        break

			    for t_column in range(1, (num_cols + 1)):
			        print ('CURRENT ROW ', t_row)
			        print ('CURRENT COL ', t_column)

			        if t_column == 8:
			            break

			        FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(t_column) + aftertr_XPath
			        FinalXPath00 = before_XPath + str(t_row) + aftertr_XPath
			        #document.querySelectorAll("#cmov_co>tbody>tr:nth-child(20)")
			        d.find_element_by_xpath(FinalXPath00)
			        print ('***** ',d.find_element(By.XPATH,FinalXPath00))
			        print ('+++++ ',d.find_element_by_xpath(FinalXPath00))
			        cell_text = d.find_element_by_xpath(FinalXPath).text
			        # print(cell_text, end = '               ')
			        print (' ============')
			        print(cell_text)
			'''



			print ('Tenho os Movimentos...')
			num_rows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
			#num_rows1 = d.execute_script("return document.getElementById('cmov_co').rows.length") # d.execute_script("$('#cmov_co tbody tr').length")
			print("Rows in table are " + repr(num_rows))
			#print (num_rows1)

			num_cols = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr[2]/td"))
			print("Columns in table are " + repr(num_cols))

			before_XPath = "//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr["
			aftertd_XPath = "]/td["
			aftertr_XPath = "]"


			gravar_dados = False

			numerodoc = False
			numerooper = False
			descoper = False




			#date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
			date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])\/([0-9][0-9])\/([1-9][0-9][0-9][0-9])'

			for t_row in range(2, (num_rows + 1)):
				if t_row == 22: #default shows only 22 cols...
					break

				numerodoc = False
				numerooper = False
				descoper = False
				montanteakz = False

				stop_for = False

				for t_column in range(1, (num_cols + 1)):
					FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(t_column) + aftertr_XPath
					FinalXPath00 = before_XPath + str(t_row) + aftertr_XPath
					#document.querySelectorAll("#cmov_co>tbody>tr:nth-child(20)")

					try:
						d.find_element_by_xpath(FinalXPath00)
						print ('***** ',d.find_element(By.XPATH,FinalXPath00))
						print ('+++++ ',d.find_element_by_xpath(FinalXPath00))

					except Exception as e:
						if "no such element: Unable to locate element" in str(e):
							print ('means NO MORE ITENS....')
							stop_for = True
							break
					finally:
						if stop_for == False:
							if d.find_element_by_xpath(FinalXPath00):
								cell_text = d.find_element_by_xpath(FinalXPath).text
								# print(cell_text, end = '               ')
								print (' ============')
								print(cell_text)

								#Verifica se formato Data
								#print (re.match(date_pattern,cell_text))
								if re.match(date_pattern,cell_text):
									gravar_dados = True
									datavalor.append(cell_text)
									numerodoc = True

								elif gravar_dados == True:
									#Verifica se termina com AKZ
									if cell_text == "AKZ":
										gravar_dados = False

									elif numerodoc:
										numero_documento.append(cell_text)
										numerodoc = False
										numerooper = True
									elif numerooper:
										numero_operacao.append(cell_text)
										numerooper = False
										descoper = True
									elif descoper:
										descricao_operacao.append(cell_text)
										descoper = False
										montanteakz = True
									elif montanteakz:
										montante_akz.append(cell_text)
										montanteakz = False
										gravar_dados = False

				#print()
				if stop_for:
					break

		print ('Terminou de ler a TABELA com o extracto.....')
		#Now check if last record date is == last day of the month
		print ('verificar se terminou de ler o mes....')
		print ("datafim_filtro ",datafim_filtro)
		print (datavalor)
		print (datavalor[len(datavalor)-1])
		print (datafim_filtro == datavalor[len(datavalor)-1])
		if datafim_filtro == datavalor[len(datavalor)-1]:
			#End While
			vermais_movimentos = False
		else:
			vermais_movimentos = False	#To avoid looping and stop
			for ll in d.find_elements_by_tag_name("a"):
				if ll.get_attribute('href'):
					#javascript:goTogrdCMOV_pag('')
					if "javascript:goTogrdCMOV_pag('')" in ll.get_attribute('href'):
						print (ll.get_attribute('href'))
						print ('NO MORE PAGES TO EXTRACT.....')
						vermais_movimentos = False
						break

					elif 'javascript:goTogrdCMOV_pag' in ll.get_attribute('href'):
						vermais_movimentos = True
						print (ll.get_attribute('href'))
						ll.click()
						break

			'''
			print ('Check if data')
			print ('Tenho os Movimentos...')
			num_rows = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr"))
			#num_rows1 = d.execute_script("return document.getElementById('cmov_co').rows.length") # d.execute_script("$('#cmov_co tbody tr').length")
			print("Rows in table are " + repr(num_rows))
			#print (num_rows1)

			num_cols = len (d.find_elements_by_xpath("//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr[2]/td"))
			print("Columns in table are " + repr(num_cols))

			before_XPath = "//*[@id='ctl00_ctl00_WP_CMOV_grdCMOV']/tbody/tr["
			aftertd_XPath = "]/td["
			aftertr_XPath = "]"

			gravar_dados = False

			numerodoc = False
			numerooper = False
			descoper = False



			#date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])-([0-9][0-9])-([1-9][0-9][0-9][0-9])'
			date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])|([0-9][0-9])\/([0-9][0-9])\/([1-9][0-9][0-9][0-9])'

			for t_row in range(2, (num_rows + 1)):
				if t_row == 22: #default shows only 22 cols...
					break

				numerodoc = False
				numerooper = False
				descoper = False
				montanteakz = False

				stop_for = False

				for t_column in range(1, (num_cols + 1)):
					FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(t_column) + aftertr_XPath
					FinalXPath00 = before_XPath + str(t_row) + aftertr_XPath
					#document.querySelectorAll("#cmov_co>tbody>tr:nth-child(20)")

					try:
						d.find_element_by_xpath(FinalXPath00)
						print ('***** ',d.find_element(By.XPATH,FinalXPath00))
						print ('+++++ ',d.find_element_by_xpath(FinalXPath00))

					except Exception as e:
						if "no such element: Unable to locate element" in str(e):
							print ('means NO MORE ITENS....')
							stop_for = True
							break
					finally:
						if stop_for == False:
							if d.find_element_by_xpath(FinalXPath00):
								cell_text = d.find_element_by_xpath(FinalXPath).text
								# print(cell_text, end = '               ')
								print (' ============')
								print(cell_text)

								#Verifica se formato Data
								#print (re.match(date_pattern,cell_text))
								if re.match(date_pattern,cell_text):
									gravar_dados = True
									datavalor.append(cell_text)
									numerodoc = True

								elif gravar_dados == True:
									#Verifica se termina com AKZ
									if cell_text == "AKZ":
										gravar_dados = False

									elif numerodoc:
										numero_documento.append(cell_text)
										numerodoc = False
										numerooper = True
									elif numerooper:
										numero_operacao.append(cell_text)
										numerooper = False
										descoper = True
									elif descoper:
										descricao_operacao.append(cell_text)
										descoper = False
										montanteakz = True
									elif montanteakz:
										montante_akz.append(cell_text)
										montanteakz = False
										gravar_dados = False

				#print()
				if stop_for:
					break


			#Check for a 3rd PAGE OR MORE....
			for ll in d.find_elements_by_tag_name("a"):
				if ll.get_attribute('href'):
					#javascript:goTogrdCMOV_pag('')
					if "javascript:goTogrdCMOV_pag('')" in ll.get_attribute('href'):
						print (ll.get_attribute('href'))
						print ('NO MORE PAGES TO EXTRACT.....')
						break
					else:
						print ('+++++++++++++++ MORE PAGES TO EXTRACT.....')
						print ('+++++++++++++++ MORE PAGES TO EXTRACT.....')
						print ('+++++++++++++++ MORE PAGES TO EXTRACT.....')

			'''
			#Set start date again..
			datainicio_next = datavalor[len(datavalor)-1]
			print ('datainicio_next ', datainicio_next)
			print ('contaloop ', contaloop)
			if contaloop == 10:
				vermais_movimentos = False

		contaloop += 1

	print ('TERMINOU ========================')
	print ('datavalor ', len(datavalor))
	#print (datavalor)
	print ('numero_document ', len(numero_documento))
	#print (numero_documento)
	print ('numero_operacao ', len(numero_operacao))
	#print (numero_operacao)
	print ('descricao_operacao ', len(descricao_operacao))
	#print (descricao_operacao)
	print ('montante_akz ', len(montante_akz))
	#print (montante_akz)
	print ('First record Amount ')
	print (montante_akz[0].split('\n'))
	print (montante_akz[0].split('\n')[0])

	return {'datavalor':datavalor,'numero_documento':numero_documento,'numero_operacao':numero_operacao,'descricao_operacao':descricao_operacao,'montante_akz':montante_akz}



def get_first_day(dt, d_years=0, d_months=0):
    # d_years, d_months are "deltas" to apply to dt
    y, m = dt.year + d_years, dt.month + d_months
    a, m = divmod(m-1, 12)
    return date(y+a, m+1, 1)

def get_last_day(dt):
    return get_first_day(dt, 0, 1) + timedelta(-1)
