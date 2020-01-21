from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, qDebug, QDateTime
from os import walk, rename, path, mkdir, remove, rmdir
from sys import argv
from codecs import open
from urllib import request, parse
import requests
from glob import glob
from shutil import move
from bs4 import BeautifulSoup
# pip install bs4
from pyunpack import Archive
# pip install pyunpack
# pip install patool
# rar.exe or 7zip.exe 


class ManageArchivesMP3(QObject):
	"""build list folders name, search youtube and download first video find format mp4."""
						
	def __init__(self, pathExtract, parent=None):
		"""Init."""
		super(ManageArchivesMP3, self).__init__(parent)
		self.pathExtract = pathExtract
		self.parent = parent
		self.fileNames = None
		self.fileName = None
		self.cleanName = ""
		self.fileArchive = None
		self.beatPort = ""
		self.beatPortCover = ""
		self.catalogLabel = ""
		self.logFileName = QDateTime.currentDateTime().toString('yyMMddhhmmss') + "_ManageArchivesMP3.log"
		self.logFileName = path.join(path.dirname(path.abspath(__file__)), "LOG", self.logFileName)

	def processExtractionFiles(self):
		"""Extract list Archives."""
		# build list
		self.fileNames = self.listFiles(self.pathExtract)
		# extract file archives list
		for self.fileName in self.fileNames:
			self.beatPort = ""
			self.writeLogFile('Traitement: ' + '"' + self.fileName + '"')
			# clean name
			self.fileArchive = path.join(self.pathExtract, self.fileName)
			self.writeLogFile('  BEFORE : ' + self.fileName)
			self.cleanFolderName()
			self.writeLogFile('  AFTER  : ' + self.cleanName)
			# search url beatport
			self.searchBeatPort()
			self.writeLogFile('  BEPORT : ' + self.beatPort)
			# find reference catalog label with BeatPort
			self.findCatalogLabelBeatPort()
			# build folder name
			if self.catalogLabel == "" or self.cleanName[0] == '[':
				self.folderArchive = path.join(self.pathExtract, self.cleanName)
			else:
				self.folderArchive = path.join(self.pathExtract, "[" + self.catalogLabel + "] " + self.cleanName)
			self.writeLogFile('  FOLDER : ' + self.folderArchive)
			# exist ?
			if not path.exists(self.folderArchive):
				# extract
				self.writeLogFile('  CREATE : ' + self.folderArchive)
				mkdir(self.folderArchive)
				self.writeLogFile('  EXTRACT: ' + self.fileArchive)
				Archive(self.fileArchive).extractall(self.folderArchive)
				# correction parasit folder
				resultFiles = self.listFiles(self.folderArchive)
				resultfolders = self.listFolders(self.folderArchive)
				if len(resultFiles) == 0 and len(resultfolders) == 1:
					self.writeLogFile('  FOLDER : (' + str(len(resultFiles)) + ', ' + str(len(resultfolders)) + ') DELETE "' + resultfolders[0]+ '"')
					src = path.join(self.folderArchive, resultfolders[0])
					self.moveAllFilesinDir(src, self.folderArchive)
					rmdir(src)
				# no cover, download with BeatPort
				covers = list(self.getListFiles(self.folderArchive, ('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.bmp', '.tiff')))
				if len(covers) == 0:
					# download cover
					self.downloadCoverBeatPort()
					self.writeLogFile('  COVER  : ' + self.beatPortCover)
					self.writeLogFile('  WRITE  : ' + path.join(self.folderArchive, "cover.jpg"))
				#self.writeLogFile('  DELETE : ' + self.fileArchive)
				#remove(self.fileArchive)
			else:
				self.writeLogFile('  EXIST  : ' + self.folderArchive)
			self.writeLogFile("\n")

	def listFiles(self, path):
		"""Build list files."""
		for _, _, filenames in walk(path):
			break
		return filenames

	def listFolders(self, path):
		"""Build list folders."""
		for _, dirs, _ in walk(path):
			break
		return dirs

	def moveAllFilesinDir(self, srcDir, dstDir):
		"""Move files and folders command."""
		# Check if both the are directories
		if path.isdir(srcDir) and path.isdir(dstDir) :
			# Iterate over all the files in source directory
			for filePath in glob(srcDir + '\*'):
				# Move each file to destination Directory
				move(filePath, dstDir)

	def getListFiles(self, folder, masks=None, exact=None):
		"""Build files list."""
		blacklist = ['desktop.ini', 'Thumbs.db']
		for folderName, subfolders, filenames in walk(folder):
			if subfolders:
				for subfolder in subfolders:
					getListFiles(subfolder, masks, exact)
			for filename in filenames:
				if masks is None:
					# no mask
					if filename not in blacklist:
						yield path.join(folderName, filename)
				else:
					# same
					if exact:
						if filename.lower() in masks:
							if filename not in blacklist:
									yield path.join(folderName, filename)
					else:
						# mask joker
						for xmask in masks:
							if filename[-len(xmask):].lower() in xmask:
								if filename not in blacklist:
									yield path.join(folderName, filename)

	def cleanFolderName(self):
		self.cleanName = self.fileName.replace("-psy-music.ru","").replace("_"," ").replace("--","-")
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
							self.cleanName = "[" + tab[2].strip().Replace("(","").Replace(")","") + "] " +  tab[0].trim() + " - " + tab[1].trim + " (" + tab[4].trim + ")"
		self.cleanName = self.cleanName.strip()

	def searchBeatPort(self):
		"""Search product www.beatport.com and extract url product."""
		self.beatPort = ""
		query = parse.quote(self.cleanName)
		url = "https://www.beatport.com/search?q=" + query
		response = request.urlopen(url)
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
		response = request.urlopen(self.beatPort)
		html = response.read()
		soup = BeautifulSoup(html, 'html.parser')
		for vid in soup.findAll(attrs={'class':'interior-release-chart-artwork interior-release-chart-artwork--desktop'}):
			self.beatPortCover = vid.attrs['src']
			break
		img_data = requests.get(self.beatPortCover).content
		with open(path.join(self.folderArchive, "cover.jpg"), 'wb') as handler:
			handler.write(img_data)
	
	def findCatalogLabelBeatPort(self):
		"""find Catalog reference label with BeatPort."""
		response = request.urlopen(self.beatPort)
		html = response.read()
		soup = BeautifulSoup(html, 'html.parser')
		for vid in soup.findAll(attrs={'class':'interior-release-chart-content-list interior-release-chart-content-item--desktop'}):
			self.catalogLabel = vid.contents[5].contents[3].contents[0]
			break

	def writeLogFile(self, line, writeconsole = True):
		"""Write log file."""
		text_file = open(self.logFileName, "a", 'utf-8')
		text_file.write(line+"\n")
		text_file.close()
		if writeconsole:
			print(line)

if __name__ == '__main__':
	app = QApplication(argv)
	# class
	BuildProcess = ManageArchivesMP3("D:\\WorkDev\\MP3TrtFiles")
	# download list
	BuildProcess.processExtractionFiles()
