#! /usr/bin/python
# coding: utf-8

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, qDebug, QDateTime
from os import rename, path, mkdir, remove, rmdir, startfile
from sys import argv, path as syspath
from urllib.request import urlopen                                                                                                                                                            
from urllib.parse import quote 
from requests import get
from bs4 import BeautifulSoup
# pip install bs4
from pyunpack import Archive
# pip install pyunpack
# pip install patool
# rar.exe or 7zip.exe 
syspath.append(path.dirname(path.dirname(path.abspath(__file__))))
from LogPrintFile.LogPrintFile import LogPrintFile
from FilesProcessing.FilesProcessing import FilesProcessing


class ManageArchivesMP3(QObject):
	"""unzip archives music, clean complet and control folder name, download cover beatport and find isrc label."""
						
	def __init__(self, parent=None):
		"""Init."""
		super(ManageArchivesMP3, self).__init__(parent)
		self.pathExtract = ""
		self.parent = parent
		self.fileNames = None
		self.fileName = None
		self.cleanName = ""
		self.fileArchive = None
		self.beatPort = ""
		self.beatPortCover = ""
		self.catalogLabel = ""
		self.FilesProcess = FilesProcessing(self)
		self.logProcess = LogPrintFile(path.join(path.dirname(path.abspath(__file__)), 'LOG'), 'ManageArchivesMP3', True, 30)

	def processExtractionFiles(self, pathExtract):
		"""Extract list Archives."""
		self.pathExtract = pathExtract
		# build list
		self.fileNames = self.FilesProcess.folder_list_files(self.pathExtract, False, ('.zip', '.rar'))
		# extract file archives list
		self.anomalies = False
		count = 1
		for self.fileName in self.fileNames:
			self.fileName = path.basename(self.fileName)
			self.beatPort = ""
			self.beatPortCover = ""
			self.catalogLabel = ""
			self.writelogfile('START OPERATIONS ({}/{})'.format(str(count),str(len(self.fileNames))), self.pathExtract, False)
			# clean name
			self.fileArchive = path.join(self.pathExtract, self.fileName)
			self.writelogfile('ARCHIVE NAME', self.fileName)
			self.cleanFolderName()
			self.writelogfile('CLEAN NAME', self.cleanName)
			# search url beatport
			self.searchBeatPort()
			if self.beatPort == '':
				self.writelogfile('BEATPORT URL PRODUCT', 'not find')
			else:
				self.writelogfile('BEATPORT URL PRODUCT', self.beatPort)
				# find reference catalog label with BeatPort
				self.findCatalogLabelBeatPort()
			# build folder name
			if self.catalogLabel == "" or self.cleanName[0] == '[':
				self.folderArchive = path.join(self.pathExtract, self.cleanName)
				self.writelogfile('FOLDER', self.cleanName)
			else:
				self.folderArchive = path.join(self.pathExtract, "[" + self.catalogLabel + "] " + self.cleanName)
				self.writelogfile('FOLDER', "[" + self.catalogLabel + "] " + self.cleanName)
			# exist ?
			if not path.exists(self.folderArchive):
				# extract
				self.writelogfile('CREATE FOLDER', self.folderArchive)
				mkdir(self.folderArchive)
				self.writelogfile('EXTRACTION', self.fileArchive)
				Archive(self.fileArchive).extractall(self.folderArchive)
				# correction parasit folder
				resultFiles = self.FilesProcess.folder_list_files(self.folderArchive, False)
				resultfolders = self.FilesProcess.folder_list_folders(self.folderArchive)
				if len(resultFiles) == 0 and len(resultfolders) == 1:
					self.writelogfile('CORECTION FOLDER', '(' + str(len(resultFiles)) + ', ' + str(len(resultfolders)) + ') MOVE FILES')
					src = path.join(self.folderArchive, resultfolders[0])
					self.FilesProcess.folder_move(src, self.folderArchive)
					self.writelogfile('CORECTION FOLDER', 'DELETE "' + resultfolders[0]+ '"')					
					rmdir(src)
				# no cover, download with BeatPort
				covers = self.FilesProcess.folder_list_files(self.folderArchive, True, ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.bmp', '.tiff'))
				if len(covers) == 0 and self.beatPort != '':
					# download cover
					self.downloadCoverBeatPort()
					self.writelogfile('COVER URL BEATPORT', self.beatPortCover)
					self.writelogfile('WRITE COVER FILE', path.join(self.folderArchive, "cover.jpg"))
				else:
					if len(covers) == 0:
						self.writelogfile('COVER URL BEATPORT', 'WARINING No Cover')
						self.anomalies = True
					else:
						self.writelogfile('COVER URL BEATPORT', 'No Action')
				#self.writelogfile('  DELETE', self.fileArchive)
				#remove(self.fileArchive)
				count += 1
			else:
				self.writelogfile('FOLDER EXIST', self.folderArchive)
			# next
			self.writelogfile('-'*22, '')
		if self.anomalies:
			self.writelogfile('END OPERATIONS.\n', "problem cover", False)
		else:
			self.writelogfile('END OPERATIONS.\n', '', False)
		self.logProcess.view_log_file()

	def cleanFolderName(self):
		self.cleanName = self.fileName
		self.cleanName = self.cleanName.replace("-psy-music.ru","").replace("_"," ").replace("--","-")
		tab = self.cleanName[:-4].split('-')
		if len(tab) == 2: 
			self.cleanName = tab[0].strip() + " - " + tab[1].strip()
		else:
			if len(tab) == 3:
				self.cleanName = tab[0].strip() + " - " + tab[1].strip() + " (" + tab[2].strip() + ")" 
			else:
				if len(tab) == 4:
					self.cleanName = tab[0].strip() + " - " + tab[1].strip() + " (" + tab[3].strip() + ")" 
				else:
					if len(tab) == 5:
						self.cleanName = tab[0].strip() + " - " + tab[1].strip() + " (" + tab[3].strip() + ")" 
					else:
						if len(tab) == 6:
							self.cleanName = "[" + tab[2].strip().replace("(","").replace(")","") + "] " +  tab[0].strip() + " - " + tab[1].strip() + " (" + tab[4].strip() + ")"
		self.cleanName = self.cleanName.strip()

	def searchBeatPort(self):
		"""Search product www.beatport.com and extract url product."""
		self.beatPort = ""
		query = self.cleanName.replace('VA - ', '').replace(' ', '+')
		url = "https://www.beatport.com/search?q=" + quote(query)
		response = urlopen(url)
		html = response.read()
		soup = BeautifulSoup(html, 'html.parser')
		for vid in soup.findAll(attrs={'class':'release-artwork-parent'}):
			self.beatPort = 'https://www.beatport.com' + vid['href']
			break
		if self.beatPort == "":
			for vid in soup.findAll(attrs={'class':'buk-track-artwork-parent'}):
				self.beatPort = 'https://www.beatport.com' + vid.contents[1].attrs['href']
				break

	def downloadCoverBeatPort(self):
		"""Download cover with BeatPort."""
		self.beatPortCover = ""
		response = urlopen(self.beatPort)
		html = response.read()
		soup = BeautifulSoup(html, 'html.parser')
		for vid in soup.findAll(attrs={'class':'interior-release-chart-artwork interior-release-chart-artwork--desktop'}):
			self.beatPortCover = vid.attrs['src']
			break
		img_data = get(self.beatPortCover).content
		with open(path.join(self.folderArchive, "cover.jpg"), 'wb') as handler:
			handler.write(img_data)
	
	def findCatalogLabelBeatPort(self):
		"""find Catalog reference label with BeatPort."""
		response = urlopen(self.beatPort)
		html = response.read()
		soup = BeautifulSoup(html, 'html.parser')
		for vid in soup.findAll(attrs={'class':'interior-release-chart-content-list interior-release-chart-content-item--desktop'}):
			self.catalogLabel = vid.contents[5].contents[3].contents[0]
			break
	
	def writelogfile(self, operation, line, modification = True, writeconsole = True):
		"""Display and Record Log."""
		print('{:>22} : {}  '.format(operation, line))
		self.logProcess.write_log_file(operation, line, modification, writeconsole)


if __name__ == '__main__':
	app = QApplication(argv)
	if len(argv)>1:
		# prod
		myfolder = argv[1]
	else:
		# test envt
		myfolder = r'E:\\Download\\__Extract'
	# class
	BuildProcess = ManageArchivesMP3()
	# download list
	BuildProcess.processExtractionFiles(myfolder)
