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
import time

#FOR CHECKING BANK....

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

import asyncio


from selenium.webdriver.chrome.options import Options

def banco_kenve_movimentos(usuario, senha):
	'''
		Reads movimento Banco Keve
		Last Modified: 02-05-2023
	'''

	if not usuario and not senha:
		frappe.throw('Nao tem Usuario e Senha para acessar o site do Banco KEVE')

	chrome_options = Options()
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--disable-dev-shm-usage')
	chrome_options.add_experimental_option('w3c', True)
	d = webdriver.Chrome('/usr/bin/chromedriver',chrome_options=chrome_options)
	d.get('https://corporate.bancokeve.ao/login.htm')

	#d.implicitly_wait(30)

	#Send username
	us = d.find_element(By.ID,'username')
	us.send_keys('asilva148')	#Replace after with usuario

	#Send Pwd
	pw = d.find_element(By.ID,'password')
	pw.send_keys('akcwfyp')	#Replace after with senha

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

	'''
	for aa in d.find_elements(By.CLASS_NAME,'current-number'):
	    if "Dep. Ordem Empresas - Kwanzas" in aa.text:
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



class BancoKeve_mov():

    def bancokeve_setup(self):
		'''
        opt = webdriver.ChromeOptions()
        opt.add_experimental_option('w3c', True)
        #opt.w3c = True
        self.driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver',options=opt)
        self.driver.delete_all_cookies()
		'''

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
		us.send_keys('asilva148')	#Replace after with usuario

		#Send Pwd
		pw = driver.find_element(By.ID,'password')
		pw.send_keys('akcwfyp')	#Replace after with senha

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
        self.usuario_banco, self.senha_banco = nifverificar
