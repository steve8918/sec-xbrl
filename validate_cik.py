import os
import zipfile
import re
import sys

cik_list = {}
def read_ticket_txt():
	f = open('ticker.txt', 'r')
	file = f.read()
	x = file.split("\n")
	for y in x:
		w = y.split("\t")
		if cik_list.get(w[1]):
			continue
		cik_list[w[1]] = w[0]

sec_folder = "./sec/"

directories = sorted([ f.path.split('/')[-1] for f in os.scandir(sec_folder) if f.is_dir() and f.path.split('/')[-1].isdigit()])
bad_files = []

for directory in directories:
	print("Validating " + directory)
	real_directory = sec_folder + directory

	files = os.listdir(real_directory)

	for file in files:
		full_filename = real_directory + "/" + file
		print("Validating " + full_filename)
		try:
			zf = zipfile.ZipFile(full_filename)
		except:
			print("Problem with " + full_filename)
			bad_files.append(full_filename)
			continue

		for zipped_file in zf.filelist:
			cik_number = None
			with zf.open(zipped_file.filename) as unzipped_file:
				data = str(unzipped_file.read())
				#<identifier scheme='http://www.sec.gov/CIK'>0001429896</identifier>
				re_cik = re.search("identifier scheme=['\"]http:\\/\\/www\\.sec\\.gov\\/CIK['\"]>(.*?)<", data)
				if re_cik is None:
					continue

				cik_number = re_cik.group(1).lstrip("0")
				break

			if cik_number is None:
				print(directory)
				raise Exception

			match_name = directory if directory.isdigit() else cik_list.get(directory, "")
			if cik_number != match_name:
				print("Problem in " + full_filename + ":" + match_name + " != cik " + cik_number)
				raise Exception


print(bad_files)
	#print(directory + ": " + cik_number)
