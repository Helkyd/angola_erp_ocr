#Extracted from https://www.thepythoncode.com/article/extract-text-from-images-or-scanned-pdf-python
#Last Modifed by HELKYD 26-03-2022

from __future__ import unicode_literals

import frappe


# pytesseract needs python3.7> servers are still on 3.5/3.6

# Installation
# MAYBE NOT REQUIRED: sudo apt-get update && sudo apt-get install cmake libopenmpi-dev python3.7-dev zlib1g-dev
# pip3 install --upgrade pip
# pip3 install Filetype==1.0.7 numpy==1.19.4 opencv-python==4.4.0.46 pandas==1.1.4 Pillow==8.0.1 PyMuPDF==1.18.9 pytesseract==0.3.7
# Install languages
# sudo apt-get install tesseract-ocr-por fra eng and maybe spa


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

#Campos que devem ter Dados; otherwise redo the OCR with a diff language
mustNumOperacao = False
mustValorOperacao = False
mustIBANCreditado = False
mustDataPagamento = False

mustIBANDestinatario  = False

numeroOperacao = ""
valorDepositado = ""
empresaOrigem0 = ""
empresaOrigem1 = ""
Datapagamento = ""

contaCreditada = ""

def pix2np(pix):
	"""
	Converts a pixmap buffer into a numpy array
	"""
	# pix.samples = sequence of bytes of the image pixels like RGBA
	#pix.h = height in pixels
	#pix.w = width in pixels
	# pix.n = number of components per pixel (depends on the colorspace and alpha)
	im = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
		pix.h, pix.w, pix.n)
	try:
		im = np.ascontiguousarray(im[..., [2, 1, 0]])  # RGB To BGR
	except IndexError:
		# Convert Gray to RGB
		im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
		im = np.ascontiguousarray(im[..., [2, 1, 0]])  # RGB To BGR
	return im

# Image Pre-Processing Functions to improve output accurracy
# Convert to grayscale
def grayscale(img):
	return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Remove noise
def remove_noise(img):
	return cv2.medianBlur(img, 5)

# Thresholding
def threshold(img):
	# return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
	return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

# dilation
def dilate(img):
	kernel = np.ones((5, 5), np.uint8)
	return cv2.dilate(img, kernel, iterations=1)

# erosion
def erode(img):
	kernel = np.ones((5, 5), np.uint8)
	return cv2.erode(img, kernel, iterations=1)

# opening -- erosion followed by a dilation
def opening(img):
	kernel = np.ones((5, 5), np.uint8)
	return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

# canny edge detection
def canny(img):
	return cv2.Canny(img, 100, 200)

# skew correction
def deskew(img):
	coords = np.column_stack(np.where(img > 0))
	angle = cv2.minAreaRect(coords)[-1]
	if angle < -45:
		angle = -(90 + angle)
	else:
		angle = -angle
	(h, w) = img.shape[:2]
	center = (w//2, h//2)
	M = cv2.getRotationMatrix2D(center, angle, 1.0)
	rotated = cv2.warpAffine(
		img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
	return rotated

# template matching
def match_template(img, template):
	return cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

def convert_img2bin(img):
	"""
	Pre-processes the image and generates a binary output
	"""
	# Convert the image into a grayscale image
	output_img = grayscale(img)
	# Invert the grayscale image by flipping pixel values.
	# All pixels that are grater than 0 are set to 0 and all pixels that are = to 0 are set to 255
	output_img = cv2.bitwise_not(output_img)
	# Converting image to binary by Thresholding in order to show a clear separation between white and blacl pixels.
	output_img = threshold(output_img)
	return output_img

def display_img(title, img):
	"""Displays an image on screen and maintains the output until the user presses a key"""
	cv2.namedWindow('img', cv2.WINDOW_NORMAL)
	cv2.setWindowTitle('img', title)
	cv2.resizeWindow('img', 1200, 900)
	# Display Image on screen
	cv2.imshow('img', img)
	# Mantain output until user presses a key
	cv2.waitKey(0)
	# Destroy windows when user presses a key
	cv2.destroyAllWindows()

def generate_ss_text(ss_details):
	"""Loops through the captured text of an image and arranges this text line by line.
	This function depends on the image layout."""
	# Arrange the captured text after scanning the page
	parse_text = []
	word_list = []
	last_word = ''
	# Loop through the captured text of the entire page
	for word in ss_details['text']:
		# If the word captured is not empty
		if word != '':
			# Add it to the line word list
			word_list.append(word)
			last_word = word
		if (last_word != '' and word == '') or (word == ss_details['text'][-1]):
			parse_text.append(word_list)
			word_list = []
	return parse_text

def search_for_text(ss_details, search_str):
	"""Search for the search string within the image content"""
	# Find all matches within one page
	results = re.findall(search_str, ss_details['text'], re.IGNORECASE)
	# In case multiple matches within one page
	for result in results:
		yield result

def save_page_content(pdfContent, page_id, page_data):
	"""Appends the content of a scanned page, line by line, to a pandas DataFrame."""
	if page_data:
		for idx, line in enumerate(page_data, 1):
			line = ' '.join(line)
			pdfContent = pdfContent.append(
				{'page': page_id, 'line_id': idx, 'line': line}, ignore_index=True
			)
	return pdfContent

def save_file_content(pdfContent, input_file):
	"""Outputs the content of the pandas DataFrame to a CSV file having the same path as the input_file
	but with different extension (.csv)"""
	content_file = os.path.join(os.path.dirname(input_file), os.path.splitext(
		os.path.basename(input_file))[0] + ".csv")
	pdfContent.to_csv(content_file, sep=',', index=False)
	return content_file

def calculate_ss_confidence(ss_details: dict):
	"""Calculate the confidence score of the text grabbed from the scanned image."""
	# page_num  --> Page number of the detected text or item
	# block_num --> Block number of the detected text or item
	# par_num   --> Paragraph number of the detected text or item
	# line_num  --> Line number of the detected text or item
	# Convert the dict to dataFrame
	df = pd.DataFrame.from_dict(ss_details)
	# Convert the field conf (confidence) to numeric
	df['conf'] = pd.to_numeric(df['conf'], errors='coerce')
	# Elliminate records with negative confidence
	df = df[df.conf != -1]
	# Calculate the mean confidence by page
	conf = df.groupby(['page_num'])['conf'].mean().tolist()
	print ('conf ',conf)
	if conf == []:
		#Ficheiro sem qualidade de imagem...
		return 'ERRO_QUALIDADE'
	return conf[0]

def ocr_img(
		img: np.array, input_file: str, search_str: str,linguas_set: str,
		highlight_readable_text: bool = False, action: str = 'Highlight',
		show_comparison: bool = False, generate_output: bool = True, linguas: bool = False):
	"""Scans an image buffer or an image file.
	Pre-processes the image.
	Calls the Tesseract engine with pre-defined parameters.
	Calculates the confidence score of the image grabbed content.
	Draws a green rectangle around readable text items having a confidence score > 30.
	Searches for a specific text.
	Highlight or redact found matches of the searched text.
	Displays a window showing readable text fields or the highlighted or redacted text.
	Generates the text content of the image.
	Prints a summary to the console."""
	# If image source file is inputted as a parameter
	if input_file:
		# Reading image using opencv
		img = cv2.imread(input_file)
	# Preserve a copy of this image for comparison purposes
	initial_img = img.copy()
	highlighted_img = img.copy()
	# Convert image to binary
	bin_img = convert_img2bin(img)
	# Calling Tesseract
	# Tesseract Configuration parameters
	# oem --> OCR engine mode = 3 >> Legacy + LSTM mode only (LSTM neutral net mode works the best)
	# psm --> page segmentation mode = 6 >> Assume as single uniform block of text (How a page of text can be analyzed)
	#config_param = r'--oem 3 --psm 6'

	#Casos ha em que fra+por nao mostra o numero da Operacao...
	#Para este casos a lang muda pra FRA+ENG
	print ('linguas ', linguas)
	print ('input_file ',input_file)
	if input_file and filetype.is_image(input_file):
		#testing...
		#config_param = r'--oem 3 --psm 12 -l spa+fra+por' # fra+spa' # spa+fra' #fra+por' #fra+eng'
		#config_param = r'--oem 3 --psm 12 -l fra+por' # fra+spa' # spa+fra' #fra+por' #fra+eng'

		config_param = r'--oem 3 --psm 12 -l fra+por' # GET All; menos IBAN e nomeDestinatario

		if linguas:
			config_param = r'--oem 3 --psm 4 -l eng' #GETs IBAN with error on AO0E instead of 06; the REST IS WRONG
		print ('linguas ', linguas)
		print ('linguas_set ', linguas_set)
	elif linguas:
		config_param = r'--oem 3 --psm 4 -l fra+por' # fra+spa' # spa+fra' #fra+por' #fra+eng'
		#frappe.throw(porra)
	else:
		#old
		print ('linguas_set ', linguas_set)
		print (linguas_set != None)

		if linguas_set != None:
			config_param = r'--oem 3 --psm 4 -l ' + linguas_set #fra+eng+spa' # fra+spa' # spa+fra' #fra+por' #fra+eng'
			#frappe.throw(porra)
		else:
			config_param = r'--oem 3 --psm 4 -l spa+fra+por' # fra+spa' # spa+fra' #fra+por' #fra+eng'
			#config_param = r'--oem 3 --psm 13 -l spa+fra+por' #TESTING on scanned not very visible...
			#frappe.throw(porra)
		#frappe.throw(porra)
	#config_param = r'--oem 3 --psm 6 -l fra+eng' #fra+eng'

	# Feeding image to tesseract
	details = pytesseract.image_to_data(
		bin_img, output_type=Output.DICT, config=config_param) #lang='eng')
	# The details dictionary contains the information of the input image
	# such as detected text, region, position, information, height, width, confidence score.
	ss_confidence = calculate_ss_confidence(details)
	if ss_confidence == "ERRO_QUALIDADE":
		frappe.throw("ERRO_QUALIDADE")

	boxed_img = None
	# Total readable items
	ss_readable_items = 0
	# Total matches found
	ss_matches = 0
	for seq in range(len(details['text'])):
		# Consider only text fields with confidence score > 30 (text is readable)
		if float(details['conf'][seq]) > 30.0:
			ss_readable_items += 1
			# Draws a green rectangle around readable text items having a confidence score > 30
			if highlight_readable_text:
				(x, y, w, h) = (details['left'][seq], details['top']
								[seq], details['width'][seq], details['height'][seq])
				boxed_img = cv2.rectangle(
					img, (x, y), (x+w, y+h), (0, 255, 0), 2)
			# Searches for the string
			if search_str:
				results = re.findall(
					search_str, details['text'][seq], re.IGNORECASE)
				for result in results:
					ss_matches += 1
					if action:
						# Draw a red rectangle around the searchable text
						(x, y, w, h) = (details['left'][seq], details['top']
										[seq], details['width'][seq], details['height'][seq])
						# Details of the rectangle
						# Starting coordinate representing the top left corner of the rectangle
						start_point = (x, y)
						# Ending coordinate representing the botton right corner of the rectangle
						end_point = (x + w, y + h)
						#Color in BGR -- Blue, Green, Red
						if action == "Highlight":
							color = (0, 255, 255)  # Yellow
						elif action == "Redact":
							color = (0, 0, 0)  # Black
						# Thickness in px (-1 will fill the entire shape)
						thickness = -1
						boxed_img = cv2.rectangle(
							img, start_point, end_point, color, thickness)

	if ss_readable_items > 0 and highlight_readable_text and not (ss_matches > 0 and action in ("Highlight", "Redact")):
		highlighted_img = boxed_img.copy()
	# Highlight found matches of the search string
	if ss_matches > 0 and action == "Highlight":
		cv2.addWeighted(boxed_img, 0.4, highlighted_img,
						1 - 0.4, 0, highlighted_img)
	# Redact found matches of the search string
	elif ss_matches > 0 and action == "Redact":
		highlighted_img = boxed_img.copy()
		#cv2.addWeighted(boxed_img, 1, highlighted_img, 0, 0, highlighted_img)
	# save the image
	cv2.imwrite("highlighted-text-image.jpg", highlighted_img)
	# Displays window showing readable text fields or the highlighted or redacted data
	if show_comparison and (highlight_readable_text or action):
		title = input_file if input_file else 'Compare'
		conc_img = cv2.hconcat([initial_img, highlighted_img])
		display_img(title, conc_img)
	# Generates the text content of the image
	output_data = None
	if generate_output and details:
		output_data = generate_ss_text(details)
	# Prints a summary to the console
	if input_file:
		summary = {
			"File": input_file, "Total readable words": ss_readable_items, "Total matches": ss_matches, "Confidence score": ss_confidence
		}
		# Printing Summary
		print("## Summary ########################################################")
		print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
		print("###################################################################")
	return highlighted_img, ss_readable_items, ss_matches, ss_confidence, output_data
	# pass image into pytesseract module
	# pytesseract is trained in many languages
	#config_param = r'--oem 3 --psm 6'
	#details = pytesseract.image_to_data(img,config=config_param,lang='eng')
	# print(details)
	# return details

def image_to_byte_array(image: Image):
	"""
	Converts an image into a byte array
	"""
	imgByteArr = BytesIO()
	image.save(imgByteArr, format=image.format if image.format else 'JPEG')
	imgByteArr = imgByteArr.getvalue()
	return imgByteArr

def ocr_file(**kwargs):
	"""Opens the input PDF File.
	Opens a memory buffer for storing the output PDF file.
	Creates a DataFrame for storing pages statistics
	Iterates throughout the chosen pages of the input PDF file
	Grabs a screen-shot of the selected PDF page.
	Converts the screen-shot pix to a numpy array
	Scans the grabbed screen-shot.
	Collects the statistics of the screen-shot(page).
	Saves the content of the screen-shot(page).
	Adds the updated screen-shot (Highlighted, Redacted) to the output file.
	Saves the whole content of the PDF file.
	Saves the output PDF file if required.
	Prints a summary to the console."""
	input_file = kwargs.get('input_file')
	output_file = kwargs.get('output_file')
	search_str = kwargs.get('search_str')
	pages = kwargs.get('pages')
	highlight_readable_text = kwargs.get('highlight_readable_text')
	action = kwargs.get('action')
	show_comparison = kwargs.get('show_comparison')
	generate_output = kwargs.get('generate_output')

	#Added Language aqui para poder add or reduce....
	linguas = kwargs.get('linguas')
	linguas_set = kwargs.get('linguas_set')

	# Opens the input PDF file
	pdfIn = fitz.open(input_file)
	# Opens a memory buffer for storing the output PDF file.
	pdfOut = fitz.open()
	# Creates an empty DataFrame for storing pages statistics
	dfResult = pd.DataFrame(
		columns=['page', 'page_readable_items', 'page_matches', 'page_total_confidence'])
	# Creates an empty DataFrame for storing file content
	if generate_output:
		pdfContent = pd.DataFrame(columns=['page', 'line_id', 'line'])
	# Iterate throughout the pages of the input file
	for pg in range(pdfIn.pageCount):
		if str(pages) != str(None):
			if str(pg) not in str(pages):
				continue
		# Select a page
		page = pdfIn[pg]
		# Rotation angle
		rotate = int(0)
		# PDF Page is converted into a whole picture 1056*816 and then for each picture a screenshot is taken.
		# zoom = 1.33333333 -----> Image size = 1056*816
		# zoom = 2 ---> 2 * Default Resolution (text is clear, image text is hard to read)    = filesize small / Image size = 1584*1224
		# zoom = 4 ---> 4 * Default Resolution (text is clear, image text is barely readable) = filesize large
		# zoom = 8 ---> 8 * Default Resolution (text is clear, image text is readable) = filesize large
		zoom_x = 2
		zoom_y = 2
		# The zoom factor is equal to 2 in order to make text clear
		# Pre-rotate is to rotate if needed.
		mat = fitz.Matrix(zoom_x, zoom_y).preRotate(rotate)
		# To captue a specific part of the PDF page
		# rect = page.rect #page size
		# mp = rect.tl + (rect.bl - (0.75)/zoom_x) #rectangular area 56 = 75/1.3333
		# clip = fitz.Rect(mp,rect.br) #The area to capture
		# pix = page.getPixmap(matrix=mat, alpha=False,clip=clip)
		# Get a screen-shot of the PDF page
		# Colorspace -> represents the color space of the pixmap (csRGB, csGRAY, csCMYK)
		# alpha -> Transparancy indicator
		pix = page.getPixmap(matrix=mat, alpha=False, colorspace="csGRAY")
		# convert the screen-shot pix to numpy array
		img = pix2np(pix)
		# Erode image to omit or thin the boundaries of the bright area of the image
		# We apply Erosion on binary images.
		#kernel = np.ones((2,2) , np.uint8)
		#img = cv2.erode(img,kernel,iterations=1)
		upd_np_array, pg_readable_items, pg_matches, pg_total_confidence, pg_output_data \
			= ocr_img(img=img, input_file=None, search_str=search_str, highlight_readable_text=highlight_readable_text  # False
					  , action=action  # 'Redact'
					  , show_comparison=show_comparison  # True
					  , generate_output=generate_output  # False
					  , linguas=linguas #False
					  , linguas_set=linguas_set
					  )
		# Collects the statistics of the page
		dfResult = dfResult.append({'page': (pg+1), 'page_readable_items': pg_readable_items,
								   'page_matches': pg_matches, 'page_total_confidence': pg_total_confidence}, ignore_index=True)
		if generate_output:
			pdfContent = save_page_content(
				pdfContent=pdfContent, page_id=(pg+1), page_data=pg_output_data)
		# Convert the numpy array to image object with mode = RGB
		#upd_img = Image.fromarray(np.uint8(upd_np_array)).convert('RGB')
		upd_img = Image.fromarray(upd_np_array[..., ::-1])
		# Convert the image to byte array
		upd_array = image_to_byte_array(upd_img)
		# Get Page Size
		"""
		#To check whether initial page is portrait or landscape
		if page.rect.width > page.rect.height:
			fmt = fitz.PaperRect("a4-1")
		else:
			fmt = fitz.PaperRect("a4")

		#pno = -1 -> Insert after last page
		pageo = pdfOut.newPage(pno = -1, width = fmt.width, height = fmt.height)
		"""
		pageo = pdfOut.newPage(
			pno=-1, width=page.rect.width, height=page.rect.height)
		pageo.insertImage(page.rect, stream=upd_array)
		#pageo.insertImage(page.rect, stream=upd_img.tobytes())
		#pageo.showPDFpage(pageo.rect, pdfDoc, page.number)
	content_file = None
	if generate_output:
		content_file = save_file_content(
			pdfContent=pdfContent, input_file=input_file)
	summary = {
		"File": input_file, "Total pages": pdfIn.pageCount,
		"Processed pages": dfResult['page'].count(), "Total readable words": dfResult['page_readable_items'].sum(),
		"Total matches": dfResult['page_matches'].sum(), "Confidence score": dfResult['page_total_confidence'].mean(),
		"Output file": output_file, "Content file": content_file
	}
	# Printing Summary
	print("## Summary ########################################################")
	print("\n".join("{}:{}".format(i, j) for i, j in summary.items()))
	print("\nPages Statistics:")
	print(dfResult, sep='\n')
	print("###################################################################")
	pdfIn.close()
	if output_file:
		pdfOut.save(output_file)
	pdfOut.close()

def ocr_folder(**kwargs):
	"""Scans all PDF Files within a specified path"""
	input_folder = kwargs.get('input_folder')
	# Run in recursive mode
	recursive = kwargs.get('recursive')
	search_str = kwargs.get('search_str')
	pages = kwargs.get('pages')
	action = kwargs.get('action')
	generate_output = kwargs.get('generate_output')
	# Loop though the files within the input folder.
	for foldername, dirs, filenames in os.walk(input_folder):
		for filename in filenames:
			# Check if pdf file
			if not filename.endswith('.pdf'):
				continue
			# PDF File found
			inp_pdf_file = os.path.join(foldername, filename)
			print("Processing file =", inp_pdf_file)
			output_file = None
			if search_str:
				# Generate an output file
				output_file = os.path.join(os.path.dirname(
					inp_pdf_file), 'ocr_' + os.path.basename(inp_pdf_file))
			ocr_file(
				input_file=inp_pdf_file, output_file=output_file, search_str=search_str, pages=pages, highlight_readable_text=False, action=action, show_comparison=False, generate_output=generate_output
			)
		if not recursive:
			break

def is_valid_path(path):
	"""Validates the path inputted and checks whether it is a file path or a folder path"""
	if not path:
		raise ValueError(f"Invalid Path")
	if os.path.isfile(path):
		return path
	elif os.path.isdir(path):
		return path
	else:
		raise ValueError(f"Invalid Path {path}")


def parse_args():
	"""Get user command line parameters"""
	parser = argparse.ArgumentParser(description="Available Options")
	parser.add_argument('-i', '--input-path', type=is_valid_path,
						required=True, help="Enter the path of the file or the folder to process")
	parser.add_argument('-a', '--action', choices=[
						'Highlight', 'Redact'], type=str, help="Choose to highlight or to redact")
	parser.add_argument('-s', '--search-str', dest='search_str',
						type=str, help="Enter a valid search string")
	parser.add_argument('-p', '--pages', dest='pages', type=tuple,
						help="Enter the pages to consider in the PDF file, e.g. (0,1)")
	parser.add_argument("-g", "--generate-output", action="store_true", help="Generate text content in a CSV file")
	path = parser.parse_known_args()[0].input_path
	if os.path.isfile(path):
		parser.add_argument('-o', '--output_file', dest='output_file',
							type=str, help="Enter a valid output file")
		parser.add_argument("-t", "--highlight-readable-text", action="store_true", help="Highlight readable text in the generated image")
		parser.add_argument("-c", "--show-comparison", action="store_true", help="Show comparison between captured image and the generated image")
	if os.path.isdir(path):
		parser.add_argument("-r", "--recursive", action="store_true", help="Whether to process the directory recursively")
	# To Porse The Command Line Arguments
	args = vars(parser.parse_args())
	# To Display The Command Line Arguments
	print("## Command Arguments #################################################")
	print("\n".join("{}:{}".format(i, j) for i, j in args.items()))
	print("######################################################################")
	return args

'''
if __name__ == '__main__':
	# Parsing command line arguments entered by user
	args = parse_args()
	# If File Path
	if os.path.isfile(args['input_path']):
		# Process a file
		if filetype.is_image(args['input_path']):
			ocr_img(
				# if 'search_str' in (args.keys()) else None
				img=None, input_file=args['input_path'], search_str=args['search_str'], highlight_readable_text=args['highlight_readable_text'], action=args['action'], show_comparison=args['show_comparison'], generate_output=args['generate_output']
			)
		else:
			ocr_file(
				input_file=args['input_path'], output_file=args['output_file'], search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=args['pages'], highlight_readable_text=args['highlight_readable_text'], action=args['action'], show_comparison=args['show_comparison'], generate_output=args['generate_output']
			)
	# If Folder Path
	elif os.path.isdir(args['input_path']):
		# Process a folder
		ocr_folder(
			input_folder=args['input_path'], recursive=args['recursive'], search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=args['pages'], action=args['action'], generate_output=args['generate_output']
		)
'''

def ang_read_csv_content(fcontent, ignore_encoding=False):
	#Read semmicolon instead of comma
	rows = []

	if not isinstance(fcontent, text_type):
		decoded = False
		for encoding in ["utf-8", "windows-1250", "windows-1252"]:
			try:
				fcontent = text_type(fcontent, encoding)
				decoded = True
				break
			except UnicodeDecodeError:
				continue

		if not decoded:
			frappe.msgprint(_("Unknown file encoding. Tried utf-8, windows-1250, windows-1252."), raise_exception=True)

	fcontent = fcontent.encode("utf-8")
	content  = [ ]
	for line in fcontent.splitlines(True):
		if six.PY2:
			content.append(line)
		else:
			content.append(frappe.safe_decode(line))

	try:
		rows = []
		podeler = False	#read data

		linhaseguinte = False
		outralinha = False
		duaslinhasdepois = False

		global mustNumOperacao
		global mustValorOperacao
		global mustIBANCreditado
		global mustDataPagamento

		global numeroOperacao
		global valorDepositado
		global empresaOrigem0
		global empresaOrigem1
		global Datapagamento

		global contaCreditada

		for row in csv.reader(content,delimiter=';'):
			r = []
			for val in row:
				val = val.strip()
				#print ("val", val.split(','))
				print (len(val.split(',')))
				print ('com aspas ',len(val.split('"')))
				if len(val.split('"'))>2:
					print ("val", val.split(',')[2])
				vv = val.splitlines(True)
				print ('vv ', vv)
				print ('aspas ', val.split('"'))
				if len(val.split('"')) > 1:
					print ('aspas1 ', val.split('"')[1])

				if len(val.split('"')) > 1:
					print ('outro tratamento....')
					print ('aspas1 ', val.split('"')[1])
					val0 = val.split('"')[1]
					print ('outralinha ',outralinha)
					if outralinha:
						print ('lda ',val0.upper().find('LDA'))
						print ('limitada', val0.upper().find('LIMITADA'))
						if val0.upper().find('LDA') != -1 or val0.upper().find('LIMITADA') != -1:
							empresaOrigem1 = val0[0:val0.upper().find('LDA')+3] or val0[0:val0.upper().find('LIMITADA')+8]
						print ('empresaOrigem0 ',empresaOrigem0)
						print ('empresaOrigem1 ',empresaOrigem1)

						linhaseguinte = False
						outralinha = False
					elif not outralinha and val0.find(' sobre a conta ') != -1:
						#Get company second line only
						linhaseguinte = False
						outralinha = False

						if len(val0.split('"')) > 1:
							print ('Empresa tem virgulas....procura por LDA ou Limitada')
							print ('aspas2 ', val0.split('"')[1])
							if val0.split('"')[1].upper().find('LDA') != -1 or val0.split('"')[1].upper().find('LIMITADA') != -1:
								empresaOrigem1 = val0[0:val0.split('"')[1].upper().find('LDA')] or val0[0:val0.split('"')[1].upper().find('LIMITADA')]
							else:
								empresaOrigem1 = dados.replace('"','')
						else:
							empresaOrigem1 = dados.replace('"','')
						print ('TEM empresaOrigem0 ',empresaOrigem0)
						print ('TEM empresaOrigem1 ',empresaOrigem1)


					elif " AKZ" in val0 and valorDepositado == "":
						#Valor depositado...
						print ('valor ',val0[val0.find("+"):])
						valorDepositado = val0[val0.find("+")+2:]
						duaslinhasdepois = True
						mustValorOperacao = True

					elif duaslinhasdepois:
						#To get Description of the payment....
						duaslinhasdepois = False
						descricaoPagamento = val0.strip().replace('-','') if val0.strip().startswith('-') else val0.strip()
						#print (val0.strip().startswith('-'))
						print ('descricaoPagamento ',descricaoPagamento)


				elif val.split(',')[2]:
					#Has data...
					print ("val", val.split(',')[2])
					dados = val.split(',')[2]

					#Check if numbers... might be numeroOperacao
					if dados[dados.rfind(' '):].strip().isnumeric():
						#numeros....
						if mustNumOperacao == False and numeroOperacao == "":
							numeroOperacao = dados[dados.rfind(' '):].strip()
							mustNumOperacao = True
							print ('TEM operacao ', numeroOperacao)

					elif "Pagamento" in dados or "Mensalidade" in dados:
						#check if Pagamento ou Mensalidade on descricao....
						duaslinhasdepois = False
						descricaoPagamento = dados.strip().replace('-','') if dados.strip().startswith('-') else dados.strip()
						#print (val0.strip().startswith('-'))
						print ('TEM descricaoPagamento ',descricaoPagamento)


					if "COMPROVATIVO" in dados.upper():
						#Proxima line tera a Data e Empresa que fez transferencia
						linhaseguinte = True
					if "N.º da Operação" in dados:
						#Get last info... numbers
						print ('operacao ', dados[dados.rfind(" "):].strip())
						numeroOperacao = dados[dados.rfind(" "):].strip()
						mustNumOperacao = True
					elif "Conta Debitada" in dados:
						#Get last info... numbers
						print ('debitada ', dados[dados.rfind(" "):].strip())
						contaDebitada = dados[dados.rfind(" "):].strip()
					elif "Conta/IBAN Creditado" in dados or "Conta/IBAN " in dados:
						#Get last info... numbers
						print ('creditada ', dados[dados.rfind(" "):].strip())
						contaCreditada = dados[dados.rfind(" "):].strip()
						mustIBANCreditado = True


					elif linhaseguinte:
						if dados.find('foi realizada') != -1:
							Datapagamento = dados[0:dados.find('foi realizada')].strip()
							dia = Datapagamento[3:5]
							mes0 = Datapagamento[Datapagamento.find('de ')+2:len(Datapagamento)].strip()
							mes = mes0[0:mes0.find('de')].strip()
							ano = Datapagamento[len(Datapagamento)-5:].strip()
							print ('Datapagamento ',Datapagamento)
							print ('dia ', dia)
							print ('mes ', mes)
							print ('ano ', ano)
							mes0 = mes.strip().replace('janeiro','01').replace('fevereiro','02').replace('margo','03').replace('março','03').replace('abril','04').replace('maio','05') \
							.replace('junho','06').replace('julho','07').replace('agosto','08').replace('setembro','09').replace('outubro','10').replace('novembro','11').replace('dezembro','12')

							mes = mes0

							Datapagamento = dia + "-" + mes + "-" + ano
							print ('Datapagamento ',Datapagamento)

							#Inicio da Empresa que fez a transferencia
							print ('dados ', dados[dados.find('Net Empresas por ')+17:len(dados)])
							empresaOrigem0 = dados[dados.find('Net Empresas por ')+17:len(dados)]
							outralinha = True
							mustDataPagamento = True

						elif outralinha:
							print ('outra linha com Nome da Empresa')
							linhaseguinte = False
							outralinha = False

							if len(val.split('"')) > 1:
								print ('Empresa tem virgulas....procura por LDA ou Limitada')
								print ('aspas1 ', val.split('"')[1])
								if val.split('"')[1].upper().find('LDA') != -1 or val.split('"')[1].upper().find('LIMITADA') != -1:
									empresaOrigem1 = val[0:val.split('"')[1].upper().find('LDA')] or val[0:val.split('"')[1].upper().find('LIMITADA')]
								else:
									empresaOrigem1 = dados.replace('"','')
							else:
								empresaOrigem1 = dados.replace('"','')
							print ('empresaOrigem0 ',empresaOrigem0)
							print ('empresaOrigem1 ',empresaOrigem1)

		#Check if True
		if mustNumOperacao and mustIBANCreditado and mustValorOperacao and mustDataPagamento:
			print ('ESTA TUDO EM ORDEM....')
			print ('RESUMO')
			if empresaOrigem0:
				print ('Empresa ', empresaOrigem0 + ' ' +  empresaOrigem1)
			else:
				print ('Empresa ', empresaOrigem1)
			print ('data ', Datapagamento)
			print ('Operacao ', numeroOperacao)
			print ('Debitado ', contaDebitada)
			print ('Creditada ', contaCreditada)
			print ('Valor ', valorDepositado)
			print ('Descricao ', descricaoPagamento)

		else:
			print ('Repetir OCR... sem uma lingua...')
			print ('numeroOperacao ',mustNumOperacao)
			print ('ibancredito ',mustIBANCreditado)
			print ('valor ',mustValorOperacao)
			print ('Data ',mustDataPagamento)

			return 'RepetirOCR'
		return 'Fazendo....'

	except Exception:
		frappe.msgprint(_("Not a valid Comma Separated Value (CSV File)"))
		raise



@frappe.whitelist(allow_guest=True)
def ocr_pdf(**kwargs):
	# Parsing command line arguments entered by user
	print ('args ',kwargs)

	args = kwargs
	print (args)
	if args['input_path']:
		output_file = None
		pages = 0
		highlight_readable_text = 0
		action = "Highlight"
		show_comparison = 0
		generate_output = 1
		linguas_set = None
		linguas = False

	#Private from another Site...
	if '/private/files/' in args['input_path']:
		#Get Secrest from site_config...
		print ('Get Secrest from site_config...')
		print ('Site externo')
		conn = FrappeClient(args['input_path'][0:args['input_path'].find('/private/')])



	# If File Path
	elif os.path.isfile(args['input_path']):
		# Process a file
		print ('Site FILE')
		if filetype.is_image(args['input_path']):
			print ('File is IMAGEM')
			search_str = None
			highlight_readable_text = 1
			ggg = ocr_img(
				# if 'search_str' in (args.keys()) else None
				img=None, input_file=args['input_path'], search_str=search_str, highlight_readable_text=highlight_readable_text, action=action, show_comparison=show_comparison, generate_output=generate_output, linguas_set=linguas_set,linguas=linguas
			)

			#Check if following words are present ....
			ispagamento = False	#Must have Multicaixa/MULEICOISO , automatico/outomárico

			numeroTransacao = ""
			contaOrigem = ""

			ibanDestino = ""
			valorTransferencia = ""
			horaEMISSAO = ""
			nomeDestinatario = ""
			dataEMISSAO = ""

			outraslinhas = False

			global mustIBANDestinatario

			for x in ggg:
				if type(x) == list:
					for a,b in enumerate(x):
						if b != []:
							if "MULEICOISO" in b:
								#MULTICAIXA
								ispagamento = True
							elif "outomárico" in b:
								ispagamento = True
							elif "TRANSACÇÃO:" in b or "TRANSACGAD:" in b:
								print ("Tem Transacao ", b[0])
								print ("Tem Transacao1 ", b[1])
								if b[1]:
									numeroTransacao = b[1]
							elif "CONTA" in b:
								outraslinhas = True
								print ('Fica atento tem conta...')
							elif outraslinhas == True:
								print ('sera a CONTA!!!! ', b)
								outraslinhas = False
								contaOrigem = b[0]
							else:
								#Verifica se tem numeros....
								print ('Numero ', len(b))
								print ('Numero b0 ', b[0])
								if len(b) >1:
									print ('Numero b1 ', b[1])
								#Check se Data
								#date_pattern = '^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])'
								date_pattern = r'^([1-9][0-9][0-9][0-9])\/([0-9][0-9])\/([0-9][0-9])'
								print (re.match(date_pattern,b[0]))
								if re.match(date_pattern,b[0]):
									#Founda dataEMISSAO
									dataEMISSAO = b[0]
									if len(b) >1:
										horaEMISSAO = b[1]

								if len(b) >1:
									print ('Numero1 ', b[1])
									print ('Numeros so ',b[0].isnumeric())
									print ('Numeros so ',b[1].isnumeric())
									#caso sim pode ser o IBAN... ainda mal formado...
									if b[1].isnumeric():
										ibanDestino = b[1]

									if "KZ" in b[1]:
										#Valor transferencia
										frappe.throw(porra)
										valorTransferencia = b[0]

									cash_pattern = r'^[-+]?(?:\d*\.\d+|\d+)'
									print ('CASH ',re.match(cash_pattern,b[0]))
									if re.match(cash_pattern,b[0]):
										#CASH
										if "." in b[0] and "," in b[0]:
											valorTransferencia = b[0]

								elif b[0].isnumeric():
									#caso sim pode ser o IBAN... ainda mal formado...
									ibanDestino = b[0]

			#Resumo
			print ('RESUMO OCR ++++++++++++')
			print ('numeroTransacao', numeroTransacao )
			print ('contaOrigem ', contaOrigem)
			print ('dataEMMISSAO ', dataEMISSAO)
			print ('ibanDestino ', ibanDestino)
			print ('valorTransferencia ', valorTransferencia)
			print ('horaEMISSAO ', horaEMISSAO)
			print ('Nome Destinatario ', nomeDestinatario)

			if not mustIBANDestinatario:
				print ('ERRO Run again to ge IBAN...')
				print ('ERRO Run again to ge IBAN...')
				search_str = None
				highlight_readable_text = 1
				ggg = ocr_img(
					# if 'search_str' in (args.keys()) else None
					img=None, input_file=args['input_path'], search_str=search_str, highlight_readable_text=highlight_readable_text, action=action, show_comparison=show_comparison, generate_output=generate_output, linguas_set=linguas_set,linguas=True
				)
				for x in ggg:
					if type(x) == list:
						for a,b in enumerate(x):
							if b != []:
								print ('SO QUERO IBAN....')
								print ('Numero ', len(b))
								print ('Numero b0 ', b[0])
								if len(b) >1:
									print ('Numero b1 ', b[1])
									iban_pattern = r'^([A][O][O][E]|[A][O][0][6]).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{4}).([0-9]{1})'
									print ('IBAN DEST. ',re.match(iban_pattern,b[1]))
									if re.match(iban_pattern,b[1]):
										#IBAN
										ibanDestino = b[1].replace('AOOE','AO06')
										mustIBANDestinatario = True
										break
				if not mustIBANDestinatario:
					#ERROOO
					print ('ERRO OCR... NAO consegui o IBAN Destinatorio...')
				else:
					print ('TUDO OK')
					#Resumo
					print ('RESUMO OCR ++++++++++++')
					print ('numeroTransacao', numeroTransacao )
					print ('contaOrigem ', contaOrigem)
					print ('dataEMMISSAO ', dataEMISSAO)
					print ('ibanDestino ', ibanDestino)
					print ('valorTransferencia ', valorTransferencia)
					print ('horaEMISSAO ', horaEMISSAO)
					print ('Nome Destinatario ', nomeDestinatario)



		else:
			ocr_file(
				input_file=args['input_path'], output_file=output_file, search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=pages, highlight_readable_text=highlight_readable_text, action=action, show_comparison=show_comparison, generate_output=generate_output, linguas_set=linguas_set,linguas=linguas
			)

			#After OCR now reads the file and get the Data...
			#Check if local file
			if "https://" in args['input_path']:
				print ('From another server...')
			else:
				#print ('content_file ',args['input_path'].replace('.pdf','.csv'))
				contentfile = args['input_path'].replace('.pdf','.csv')
				with open(contentfile, "rb") as fileobj:
					filedata = fileobj.read()
				#print (filedata)
				if ang_read_csv_content(filedata) == "RepetirOCR":
					print ('VAI REPETIR OCR....')
					print ('VAI REPETIR OCR....')
					print ('VAI REPETIR OCR....')
					print ('VAI REPETIR OCR....')

					print (' mustNumOperacao ',  mustNumOperacao)
					print ('mustIBANCreditado ',mustIBANCreditado)
					print ('mustValorOperacao ',   mustValorOperacao)
					print ('data ', mustDataPagamento)

					#Keep values .. in case on the new search not found and clean ....
					if mustNumOperacao:
						OldnumeroOperacao = numeroOperacao
					else:
						OldnumeroOperacao = ""
					if mustIBANCreditado:
						OldcontaCreditada = contaCreditada
					else:
						OldcontaCreditada = ""
					if mustValorOperacao:
						OldvalorDepositado = valorDepositado
					else:
						OldvalorDepositado = ""
					if mustDataPagamento:
						OldDatapagamento = Datapagamento
					else:
						OldDatapagamento = ""


					ocr_file(
						input_file=args['input_path'], output_file=output_file, search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=pages, highlight_readable_text=highlight_readable_text, action=action, show_comparison=show_comparison, generate_output=generate_output, linguas=True
					)
					if "https://" in args['input_path']:
						print ('From another server...')
					else:
						#print ('content_file ',args['input_path'].replace('.pdf','.csv'))
						contentfile = args['input_path'].replace('.pdf','.csv')
						with open(contentfile, "rb") as fileobj:
							filedata = fileobj.read()
						#print (filedata)
						if ang_read_csv_content(filedata) == "RepetirOCR":
							print ('Tenta novamente outras linguas00000...')
							#frappe.throw(porra)
							ocr_file(
								input_file=args['input_path'], output_file=output_file, search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=pages, highlight_readable_text=highlight_readable_text, action=action, show_comparison=show_comparison, generate_output=generate_output, linguas=False, linguas_set = 'fra+eng+spa'
							)
							#print ('content_file ',args['input_path'].replace('.pdf','.csv'))
							contentfile = args['input_path'].replace('.pdf','.csv')
							with open(contentfile, "rb") as fileobj:
								filedata = fileobj.read()
							#print (filedata)
							if ang_read_csv_content(filedata) == "RepetirOCR":
								print ('Tenta novamente outras linguas...')
								#frappe.throw(porra)
								ocr_file(
									input_file=args['input_path'], output_file=output_file, search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=pages, highlight_readable_text=highlight_readable_text, action=action, show_comparison=show_comparison, generate_output=generate_output, linguas=False, linguas_set = 'fra+spa'
								)
								#print ('content_file ',args['input_path'].replace('.pdf','.csv'))
								contentfile = args['input_path'].replace('.pdf','.csv')
								with open(contentfile, "rb") as fileobj:
									filedata = fileobj.read()
								#print (filedata)
								if ang_read_csv_content(filedata) == "RepetirOCR":
									print ('ERRO apos 4 OCR continua sem DADOS....')
									return 'Ficheiro nao Suportado. Envie com melhor qualidade de PDF ou Imagem.'


	# If Folder Path
	elif os.path.isdir(args['input_path']):
		# Process a folder
		print ('Folder')
		ocr_folder(
			input_folder=args['input_path'], recursive=args['recursive'], search_str=args['search_str'] if 'search_str' in (args.keys()) else None, pages=args['pages'], action=args['action'], generate_output=args['generate_output']
		)
