import glob
import os
import csv
import sys
import shutil

tickers = {}
"""
with open('cik_ticker.csv', newline='') as csvfile:
	ticker_reader = csv.reader(csvfile, delimiter='|')
	for row in ticker_reader:
		tickers[row[0]] = row[1].upper()
"""
"""
with open('cik_ticker.csv', newline='') as csvfile:
	ticker_reader = csv.reader(csvfile, delimiter='|')
	for row in ticker_reader:
		if not tickers.get(row[1].upper()):
			tickers[row[1].upper()] = [row[0]]
		else:
			tickers[row[1].upper()].append(row[0])
"""

ticker_list = {}
with open("ticker.txt") as f:
	file = f.read()
	x = file.split("\n")
	for y in x:
		w = y.split("\t")
		if ticker_list.get(w[1]):
			continue
		ticker_list[w[1]] = w[0].upper()

sec_folder = "./sec/"
subfolders = [ f.path.split('/')[-1] for f in os.scandir(sec_folder) if f.is_dir() and f.path.split('/')[-1].isdigit() ]
#subfolders = [ f.path.split('/')[-1] for f in os.scandir(sec_folder) if f.is_dir() and not f.path.split('/')[-1].isdigit() ]

for folder in subfolders:
	ticker = ticker_list.get(folder)
	if not ticker:
		continue
	print(folder + "->" + ticker)
	destination_folder = sec_folder + ticker
	try:
		os.rename(sec_folder + folder, destination_folder)
	except Exception as e:
		print(e)

	"""
	new_ticker = ticker_list.get(folder)
	if not new_ticker:
		continue
	print(folder + "->" + new_ticker)
	destination_folder = sec_folder + new_ticker
	try:
		os.rename(sec_folder + folder, destination_folder)
		pass
	except Exception as e:
		print(e)
		os.rename(sec_folder + folder, destination_folder + "." + folder)
	"""
	"""
	cik = folder.split('.')[1]
	print(sec_folder + folder + "->" + sec_folder + cik)
	os.rename(sec_folder + folder, sec_folder + cik)
	"""

	"""
	current_cik = tickers.get(folder)
	if not current_cik:
		continue

	if len(current_cik) == 1:
		print(folder + "->" + current_cik[0])
		try:
			os.rename(sec_folder + folder, sec_folder + current_cik[0])
		except FileExistsError as e:
			files = os.listdir(sec_folder + current_cik[0])
			if len(files) == 1:
				shutil.rmtree(sec_folder + current_cik[0])
				os.rename(sec_folder + folder, sec_folder + current_cik[0])
	"""

	"""
	if len(tickers[ticker]) == 1:
		print(sec_folder + folder + "->" + sec_folder + tickers[ticker][0])
		try:
			os.rename(sec_folder + folder, sec_folder + tickers[ticker][0])
		except FileExistsError:
			shutil.rmtree(sec_folder + tickers[ticker][0])
			os.rename(sec_folder + folder, sec_folder + tickers[ticker][0])
	"""




