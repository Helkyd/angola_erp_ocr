# -*- coding: utf-8 -*-
# Copyright (c) 2016, Helio de Jesus and contributors
# For license information, please see license.txt


#Date Changed: 02/05/2023


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
		Last Modified: 04-05-2023


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


	datainicio = d.find_element(By.ID,'CalendarDateFrom')
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


	datafim = d.find_element(By.ID,'CalendarDateTo')
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



	if d.find_elements(By.ID,'load-next-movements'):
		#Get more records....
		#d.find_elements(By.ID,'load-next-movements').click()
		print ('Does not click on Next movements / VER MAIS')
		#d.execute_script("document.getElementById('load-next-movements').click()")
		#d.implicitly_wait(10)
		'''
		TODO: If report does not get to last date... and this button exists...
			Should generate again from the last date DATA received to last day of the Month...
			ex. if from 01 of March to 31 and received only until 29th so,
			Generate again from 29th until 31
		'''




	print ('Tenho os Movimentos...')
	num_rows = len (d.find_elements_by_xpath("//*[@id='cmov_co']/tbody/tr"))
	print("Rows in table are " + repr(num_rows))

	num_cols = len (d.find_elements_by_xpath("//*[@id='cmov_co']/tbody/tr[1]/td"))
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
			cell_text = d.find_element_by_xpath(FinalXPath).text
			# print(cell_text, end = '               ')
			print (' ============')
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

	return (datavalor,numero_documento,numero_operacao,descricao_operacao,montante_akz)



def get_first_day(dt, d_years=0, d_months=0):
    # d_years, d_months are "deltas" to apply to dt
    y, m = dt.year + d_years, dt.month + d_months
    a, m = divmod(m-1, 12)
    return date(y+a, m+1, 1)

def get_last_day(dt):
    return get_first_day(dt, 0, 1) + timedelta(-1)
