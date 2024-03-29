# -*- coding: utf-8 -*-
# Copyright (c) 2022, Helio de Jesus and contributors
# For license information, please see license.txt

#Last modified by HELKYds: 04-03-2022

from __future__ import unicode_literals

import io
import os
import re
import time


from spellchecker import SpellChecker

import frappe
from frappe.model.document import Document

from angola_erp_ocr.angola_erp_ocr.doctype.ocr_language.ocr_language import lang_available


def get_words_from_text(message):
	"""
	This function return only list of words from text. Example: Cat in gloves,
	catches: no mice ->[cat, in, gloves, catches, no, mice]
	"""
	message = re.sub(r'\W+', " ", message)
	word_list = list(filter(None, message.split()))
	return word_list


def get_spellchecked_text(message, language):
	"""
	:param message: return text with correction:
	Example: Cet in glaves cetches no mice -> Cat in gloves catches no mice
	"""
	print ('get_spellchecked_text ')
	print ('=======')
	print (message)
	print ('=======')
	lang = frappe.get_doc("OCR Language", language).lang
	spell_checker = SpellChecker(lang)
	only_words = get_words_from_text(message)
	misspelled = spell_checker.unknown(only_words)
	for word in misspelled:
		corrected_word = spell_checker.correction(word)
		message = message.replace(word, corrected_word)
	return message


class OCRRead(Document):
	def __init__(self, *args, **kwargs):
		self.read_result = None
		self.read_time = None
		super(OCRRead, self).__init__(*args, **kwargs)

	def read_image(self):
		return read_ocr(self)

	def read_image_bg(self, is_async=True, now=False):
		return frappe.enqueue("angola_erp_ocr.angola_erp_ocr.doctype.ocr_read.ocr_read.read_ocr",
							  queue="long", timeout=1500, is_async=is_async,
							  now=now, **{'obj': self})


@frappe.whitelist()
def read_ocr(obj):
	"""Call Tesseract OCR to extract the text from a OCR Read object."""

	if obj is None:
		frappe.msgprint(frappe._("OCR read requires OCR Read doctype."),
						raise_exception=True)

	start_time = time.time()
	text = read_document(
		obj.file_to_read, obj.language or 'eng', obj.spell_checker)
	delta_time = time.time() - start_time

	obj.read_time = str(delta_time)
	obj.read_result = text
	obj.save()

	return text


@frappe.whitelist()
def read_document(path, lang='eng', spellcheck=False, resolucao=150, event="ocr_progress_bar"):
	"""Call Tesseract OCR to extract the text from a document."""

	""" Added resolucao if calling from another software or site... """

	from PIL import Image
	import requests
	import tesserocr #pytesseract

	if path is None:
		return None

	if not lang_available(lang):
		frappe.msgprint(frappe._
						("The selected language is not available. Please contact your administrator."),
						raise_exception=True)

	frappe.publish_realtime(event, {"progress": "0"}, user=frappe.session.user)

	if path.startswith('/assets/'):
		# from public folder
		fullpath = os.path.abspath(path)
	elif path.startswith('/files/'):
		# public file
		fullpath = frappe.get_site_path() + '/public' + path
	elif path.startswith('/private/files/'):
		# private file
		fullpath = frappe.get_site_path() + path
	elif path.startswith('/'):
		# local file (mostly for tests)
		fullpath = os.path.abspath(path)
	else:
		# external link
		fullpath = requests.get(path, stream=True).raw

	ocr = frappe.get_doc("Configuracao OCR") #frappe.get_doc("OCR Settings")

	print ('resolucao ', resolucao)
	print ('lang ', lang)

	text = " "
	paginas = []

	with tesserocr.PyTessBaseAPI(lang=lang) as api:

		if path.endswith('.pdf'):
			from wand.image import Image as wi

			# https://stackoverflow.com/questions/43072050/pyocr-with-tesseract-runs-out-of-memory
			#from frappe import msgprint
			#frappe.msgprint(ocr.resolucao_pdf)
			with wi(filename=fullpath, resolution=resolucao or ocr.resolucao_pdf) as pdf:
				pdf_image = pdf.convert('jpeg')
				i = 0
				size = len(pdf_image.sequence) * 3

				for img in pdf_image.sequence:
					page = wi(image=img)
					with wi(image=img) as img_page:
						image_blob = img_page.make_blob('jpeg')
						#frappe.publish_realtime(
						#	event, {"progress": [i, size]}, user=frappe.session.user)
						#i += 1

						recognized_text = " "

						image = Image.open(io.BytesIO(image_blob))
						api.SetImage(image)
						#frappe.publish_realtime(
						#	event, {"progress": [i, size]}, user=frappe.session.user)
						#i += 1

						recognized_text = api.GetUTF8Text()
						text = text + recognized_text
						paginas.append(recognized_text)

						#frappe.publish_realtime(
						#	event, {"progress": [i, size]}, user=frappe.session.user)
						#i += 1
			print ('PAGINAS')
			print (paginas)
			print ('***********************')
			#TEST TO SEE IF no error is show...
			#pdf_image.destroy()	# frees memory used by Image object.

		else:
			image = Image.open(fullpath)
			api.SetImage(image)
			frappe.publish_realtime(
				event, {"progress": [33, 100]}, user=frappe.session.user)

			text = api.GetUTF8Text()
			frappe.publish_realtime(
				event, {"progress": [66, 100]}, user=frappe.session.user)

	if spellcheck:
		text = get_spellchecked_text(text, lang)

	frappe.publish_realtime(
		event, {"progress": [100, 100]}, user=frappe.session.user)

	return text
