# coding: utf-8
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
import urllib.request
import os
import bitly_api
from time import sleep
import glob
import traceback
import re
import logging
import time
from socket import gaierror
from pathlib import Path


def writeData(path, productID, productName, fullProductName, description, additional_details, technical_details, extra_details, similar_product_titles, shortLink, tags):
	try:
		path = path + "\\" + productID
		os.mkdir(path)
	except FileExistsError:
		pass

	writingFile = open(path + "\\details.txt" , "w+", encoding="utf8")

	checkThis = u"▶Check This on Amazon▶"

	writingFile.write(    productName + "\n\n"
						+ checkThis + shortLink + "\n\n"
						+ fullProductName + "\n\n" 
						+ description
						+ "\n\n------------------------------------------\n***** Technical Details *****\n\n" + technical_details
						+ "\n\n------------------------------------------\n***** Additional Details *****\n\n" + additional_details
						+ "\n\n------------------------------------------\n***** Extra Details *****\n\n" + extra_details
						+ "\n\n------------------------------------------\n***** Similar Products *****\n\n" + similar_product_titles
						+ "\n\n------------------------------------------\n***** Tags *****\n\n" + tags)
	writingFile.close()

def downloadImages(driver, productID, path, typeOfPage):
	print(typeOfPage)
	reRunCounter = 0
	if typeOfPage == 'ordinary':
		while True:
			def hoverOverThumbnails(driver):
				print('\tImage Download Method line 1')
				imgThumbnailList = driver.find_elements_by_css_selector('.a-spacing-small.item.imageThumbnail.a-declarative') # Gets the image thumbnail elements
			
				# Hovers over Available Images
				print('\tImage Download Method line 2')
				for item in imgThumbnailList:
					print('\tImage Download Method line 3 inside loop')
					hover = ActionChains(driver).move_to_element(item)
					print('\tImage Download Method line 4 inside loop')
					hover.perform()
					print('\tImage Download Method line 5 inside loop')

				return imgThumbnailList
			def appendImageLink(imgThumbnailList, imgURLs):
				# Gets and downloads
				if (len(imgThumbnailList) != 0):
					run = 0
					print('\nImages found on ' + productID + ' ' + str(len(imgThumbnailList)))
					print('\tImage Download Method line 6')
					while (run < len(imgThumbnailList)):
						print('\tImage Download Method line 7 inside loop')
						imageContainer = driver.find_element_by_css_selector('.image.item.itemNo%s.maintain-height' % (run))
						print('\tImage Download Method line 8 inside loop')
						imageLink = imageContainer.find_element_by_tag_name('img').get_attribute('src')
						print('\tImage Download Method line 9 inside loop')
						imgURLs.append(imageLink)
						# print(imageLink)
						run += 1
					return imgURLs
				else:
					return imgURLs
			
			imgURLs = []
			imgThumbnailList = hoverOverThumbnails(driver)
			imgURLs = appendImageLink(imgThumbnailList, imgURLs)

			if (len(imgThumbnailList) == len(imgURLs)) and (len(imgThumbnailList) != 0 ) and (len(imgURLs) != 0):
				run = 0
				for item in imgURLs:
					urllib.request.urlretrieve(item, path + "\\" + productID + "\\" + "image" + str(run) + ".jpg")
					run += 1
				break
			else:
				print('Attempting rerun on ' + productID)
				reRunCounter += 1
				if (reRunCounter <  5): #Chechs if image download retry code ran more than or equal to five times. If it is it'll break
					continue
				else:
					allFailedProducts.append(link)
					imageDownloadFail = "************************************ ERROR OCCURED ************************************\nFailed to retrive some/all images on: " + productID + "\n"
					logging.error(imageDownloadFail)
					break

	elif typeOfPage == 'old':
		mainListContainer = driver.find_element_by_css_selector('.a-unordered-list.a-nostyle.a-button-list.a-vertical.a-spacing-top-micro')
		thumbnailList = mainListContainer.find_elements_by_css_selector('.a-spacing-small.item.a-declarative')
		expanderFound = 0
		for thumbnail in thumbnailList:
			try:
				thumbnailID = thumbnail.find_element_by_id('altIngressSpan')
				expanderThumbnail = thumbnail.find_element_by_css_selector('.a-button.a-button-thumbnail.a-button-toggle').click()
				expanderFound = 1
			except NoSuchElementException:
				pass
		reRunCounter = 0
		if expanderFound:
			while True: # Rerun/Run image download process, It'll rerun itself if there are any missing images found
				def appendImageLink(driver, imageSrcLinks):
					largePreview = driver.find_element_by_id('ivLargeImage')
					while True:
						try:
							sleep(2)
							imageLink = largePreview.find_element_by_tag_name('img').get_attribute('src')
							if imageLink == "https://images-na.ssl-images-amazon.com/images/G/01/ui/loadIndicators/loading-large_labeled._CB192238949_.gif":
								pass
							else:
								break
						except NoSuchElementException:
							pass
					imageSrcLinks.append(imageLink)

				def processHeroImageAppending(heroImageFound, driver, noOfHeroImageThumbnails, imageSrcLinks):
					while True:
						if heroImageFound == False:
							print('asdfasdfasdf')
							try:
								heroImage = driver.find_element_by_id('ivHeroImage_%s' %(noOfHeroImageThumbnails))
								ActionChains(driver).move_to_element(heroImage).click().perform()
								try:
									appendImageLink(driver, imageSrcLinks)
									heroImageFound = True
								except Exception as e:
									print('Image Download failed')
									error = "************************************ ERROR OCCURED ************************************\nError occured when trying to parse: " + productID + "\n" +traceback.format_exc() + "\n"
									logging.error(error)
								noOfHeroImageThumbnails += 1
							except NoSuchElementException:
								return noOfHeroImageThumbnails
						else:
							return noOfHeroImageThumbnails

				def processNormalImageAppending(heroImageFound, driver, noOfThumbnails, imageSrcLinks):
					while True:
						try:
							popup_image_thumbnails = driver.find_element_by_id('ivImage_%s' % (noOfThumbnails))
							ActionChains(driver).move_to_element(popup_image_thumbnails).click().perform()
							try:
								appendImageLink(driver, imageSrcLinks)
							except:
								print('Image Download failed')
								error = "************************************ ERROR OCCURED ************************************\nError occured when trying to parse: " + productID + "\n" +traceback.format_exc() + "\n"
								logging.error(error)
							noOfThumbnails += 1
						except NoSuchElementException:
							return noOfThumbnails
				# Appeneds image links to a list
				sleep(2)
				noOfThumbnails = 0 # Except Hero Image
				noOfHeroImageThumbnails = 0
				run = 0
				imageSrcLinks = []
				heroImageFound = False
					# Attempt to append Hero Image to list
				noOfHeroImageThumbnails = processHeroImageAppending(heroImageFound, driver, noOfHeroImageThumbnails, imageSrcLinks)
				noOfThumbnails = processNormalImageAppending(heroImageFound, driver, noOfThumbnails, imageSrcLinks)
				# Downloading process Starts here
				# Checks if there are any missing images
				print(str(len(imageSrcLinks)))
				print(str(noOfThumbnails))
				if (len(imageSrcLinks) == (noOfThumbnails + noOfHeroImageThumbnails)):
					run = 0
					for link in imageSrcLinks:
						urllib.request.urlretrieve(link, path + "\\" + productID + "\\" + "image" + str(run) + ".jpg")
						run += 1
					break
				else:
					print('Attempting rerun on ' + productID)
					reRunCounter += 1
					if (reRunCounter <  5): #Chechs if image download retry code ran more than or equal to five times. If it is it'll break
						continue
					else:
						allFailedProducts.append(link)
						imageDownloadFail = "************************************ ERROR OCCURED ************************************\nFailed to retrive some/all images on: " + productID + "\n"
						logging.error(imageDownloadFail)
						break
		else:
			imgThumbnailList = driver.find_elements_by_css_selector('.a-spacing-small.item.imageThumbnail.a-declarative')
			for item in imgThumbnailList:
				hover = ActionChains(driver).move_to_element(item)
				hover.perform()
			run = 0
			while (run < len(imgThumbnailList)):
				imageContainer = driver.find_element_by_css_selector('.image.item.itemNo%s.maintain-height' % (run))
				imageLink = imageContainer.find_element_by_tag_name('img').get_attribute('src')
				run += 1
				urllib.request.urlretrieve(imageLink, path + "\\" + productID + "\\" + "image" + str(run) + ".jpg")

def downloadVideos(driver, productID, path, typeOfPage):
	if typeOfPage == "ordinary":
		# Downloading videos within product Images/first videos (Main Videos)
		try:
			#Check if videos are there.
			try:
				videoCount = driver.find_element_by_xpath('//*[@id="videoCount"]')
				videoThumbnail = driver.find_element_by_css_selector('.a-spacing-small.item.videoThumbnail.videoBlockIngress.videoBlockDarkIngress.a-declarative')
				videoCountText = videoThumbnail.find_element_by_css_selector('.a-size-mini.a-color-secondary.video-count.a-text-bold.a-nowrap').text
				if videoCountText[0].isdigit():
					videoCount = int(videoCountText[0])
				else:
					videoCount = 1
				videoThumbnail.click()  # Click on the video thumbnail
				sleep(2)
				
				# Check for the links once the above element opened. Looks for main videos
				run = 0
				videoLinkContainer = driver.find_element_by_id("vse-ib-rvs")
				secondaryVideoContainers = videoLinkContainer.find_elements_by_css_selector(".a-section.vse-video-item")
				for secondaryVideoContainer in secondaryVideoContainers[0:videoCount]:
					videoLink = secondaryVideoContainer.get_attribute('data-video-url')
					urllib.request.urlretrieve(videoLink, path + "\\" + productID + "\\" + str(run) + ".mp4")
					run += 1
			except NoSuchElementException:
				videoThumbnail = driver.find_elements_by_css_selector('.a-spacing-small.item.videoThumbnail.a-declarative')
				videoLinkContainer = driver.find_element_by_css_selector(".a-text-center.a-fixed-left-grid-col.a-col-right")
				print(len(videoThumbnail))
				run = 0
				for item in videoThumbnail:
					hover = ActionChains(driver).move_to_element(item)
					hover.perform()
					videoLink = videoLinkContainer.find_element_by_tag_name('video').get_attribute('src')
					urllib.request.urlretrieve(videoLink, path + "\\" + productID + "\\" + str(run) + ".mp4")
					run += 1

		except NoSuchElementException:
			print('\nNo Main Video found on ' + productID)
			pass

		# Downloading videos within product Images/first videos (Secondary Videos)
		try:
			run = 0
			videoLinkContainer = driver.find_elements_by_css_selector('.celwidget.aplus-module.premium-module-8-hero-video')
			for secondaryVideoContainer in videoLinkContainer:
				videoLink = secondaryVideoContainer.find_element_by_tag_name('video').get_attribute('src')
				urllib.request.urlretrieve(videoLink, path + "\\" + productID + "\\" + str(run) + ".mp4")
				run += 1
		except NoSuchElementException:
			print('\nNo Secondary Video found on ' + productID)
			pass
	elif typeOfPage == "old":
		mainListContainer = driver.find_element_by_css_selector('.a-unordered-list.a-nostyle.a-button-list.a-vertical.a-spacing-top-micro')
		thumbnailList = mainListContainer.find_elements_by_css_selector('.a-spacing-small.item.a-declarative')
		expanderFound = 0
		for thumbnail in thumbnailList:
			try:
				thumbnailID = thumbnail.find_element_by_id('altIngressSpan')
				expanderThumbnail = thumbnail.find_element_by_css_selector('.a-button.a-button-thumbnail.a-button-toggle')
				expanderFound = 1
			except NoSuchElementException:
				pass
		if expanderFound:
			sleep(2)
			noOfThumbnails = 0
			run = 0
			while True:
				try:
					popup_video_thumbnails = driver.find_element_by_id('ivVideo_%s' % (noOfThumbnails))
					ActionChains(driver).move_to_element(popup_video_thumbnails).click().perform()
					try:
						largePreview = driver.find_element_by_id('ivLargeVideo')
						while True:
							try:
								videoLink = largePreview.find_element_by_tag_name('video').get_attribute('src')
								break
							except Exception:
								print('No video link found')
								error = "************************************ ERROR OCCURED ************************************\nError occured when trying to parse: " + productID + "\n" +traceback.format_exc() + "\n"
								logging.error(error)
								pass
						urllib.request.urlretrieve(videoLink, path + "\\" + productID + "\\" + str(run) + ".mp4")
						run += 1
					except Exception as e:
						print('Video Download failed')
						logging.error(error)
					noOfThumbnails += 1
				except NoSuchElementException:
					break
		else:
			vidThumbnailList = driver.find_elements_by_css_selector('.a-spacing-small.item.videoThumbnail.a-declarative')
			run = 0
			mainVideoContainer = driver.find_element_by_id('main-video-container')
			for item in vidThumbnailList:
				hover = ActionChains(driver).move_to_element(item)
				hover.perform()
				videoLink = mainVideoContainer.find_element_by_tag_name('video').get_attribute('src')
				urllib.request.urlretrieve(videoLink, path + "\\" + productID + "\\" + str(run) + ".mp4")
				run += 1

def getDetails(driver, productID, affiliate_tag):
	shortLink = "https://amazon.com/dp/%s/?tag=%s" % (productID, affiliate_tag) # Makes a short Link outof ID and tag
	# response = bitAmazon.shorten(shortLink) # Shorts the link 
	# shortLink = response['url'] # gets the shortened link

	productTag = driver.find_element_by_id("productTitle").text

	fullProductName = productTag

	tags = productTag[:500].replace("," , " ")
	tags = tags.split(" ")
	tagsText = ""
	for item in tags:
		tagsText += item + ", "
	tagsText += productID

	try:
		# Tries for normal Product Description
		parentDescriptionList = driver.find_element_by_css_selector('.a-section.a-spacing-medium.a-spacing-top-small')
		typeOfPage = 'ordinary'
		try:
			clickHereToExpand = parentDescriptionList.find_element_by_css_selector('.a-expander-prompt')
			clickHereToExpand.click()
		except NoSuchElementException:
			pass
	except NoSuchElementException:
		# Tries for a diffrent Product Description
		parentDescriptionList = driver.find_element_by_css_selector('.a-section.collapsedFeatureBullets.showAllFeatureBullets')
		typeOfPage = 'old'
		try:
			clickHereToExpand = parentDescriptionList.find_element_by_css_selector('.a-button.a-button-toggle.moreFB')
			ActionChains(driver).move_to_element(clickHereToExpand).click().perform()
		except NoSuchElementException:
			clickHereToExpand = parentDescriptionList.find_element_by_id('seeMoreDetailsLink')
			ActionChains(driver).move_to_element(clickHereToExpand).click().perform()
		except selenium.common.exceptions.ElementNotVisibleException:
			clickHereToExpand = parentDescriptionList.find_element_by_id('seeMoreDetailsLink')
			ActionChains(driver).move_to_element(clickHereToExpand).click().perform()

	description = ""
	descriptionList = parentDescriptionList.find_elements_by_tag_name('li')
	for descriptionLiTag in descriptionList:
		descriptionPoint = descriptionLiTag.find_element_by_css_selector('.a-list-item').text
		if descriptionPoint != "":
			description += "• " + descriptionPoint + "\n"

	# Getting technical details
	try:
		technical_details = ""
		technical_details_container = driver.find_element_by_id('prodDetails')
		technical_details_sub_container = technical_details_container.find_element_by_css_selector('.a-column.a-span6')
		technical_details_table = technical_details_sub_container.find_element_by_tag_name('tbody')
		table_rows = technical_details_table.find_elements_by_tag_name('tr')
		neccessaryDetails = ["Manufacturer", "Item model number"]
		for row in table_rows:
			if row.find_element_by_tag_name('th').text in neccessaryDetails:
				technical_details += row.find_element_by_tag_name('th').text + "\t\t|\t\t" + row.find_element_by_tag_name('td').text + "\n"
			else:
				pass
	except NoSuchElementException:
		# technical_details = "***** Unable to find Technical Details *****"
		technical_details= ''

	# Getting additional details
	try:
		additional_details_container = driver.find_element_by_id('productDescription')
		additional_details = additional_details_container.find_element_by_tag_name('p').text
	except NoSuchElementException:
		# additional_details = "***** Unable to find Additional Details *****"
		additional_details= ''

	# Getting Extra details
	try:
		extra_details = driver.find_element_by_id('aplus').text
	except NoSuchElementException:
		# extra_details = "***** Unable to find Extra Details *****"
		extra_details= ''

	# Getting similar item's names
	try:
		similar_product_table = driver.find_element_by_id('HLCXComparisonWidget_feature_div')
		similar_products_container = similar_product_table.find_element_by_css_selector('.comparison_table_image_row')
		similar_product_titles = similar_products_container.find_elements_by_css_selector('.a-size-base')
		similar_product_titles = [i.text for i in similar_product_titles[2:]]
		similar_product_titles = '\n\n'.join(similar_product_titles)
	except NoSuchElementException:
		similar_product_titles = "***** Unable to find similar items *****"

	# try:
	# 	# Loads the whole page by scrollling
	# 	hover_element = driver.find_element_by_id('ask_lazy_load_div')
	# 	hover = ActionChains(driver).move_to_element(hover_element)
	# 	hover.perform()
	# 	time.sleep(1)
	# 	quiz_answers = driver.find_element_by_id('ask-btf-container').text
	# except NoSuchElementException:
		# quiz_answers = "***** Unable to find Answers and Questions *****"

	# hover_element = driver.find_element_by_id('ask_lazy_load_div')
	# hover = ActionChains(driver).move_to_element(hover_element)
	# hover.perform()
	# time.sleep(1)
	# quiz_answers = driver.find_element_by_id('ask-btf-container').text

	yield productTag
	yield fullProductName
	yield description
	yield technical_details
	yield additional_details
	yield extra_details
	yield similar_product_titles
	# yield quiz_answers
	yield shortLink
	yield typeOfPage
	yield tagsText

# initialize the log settings
logging.basicConfig(filename='error.log',level=logging.INFO)
networkErrorDetected = False
allFailedProducts = []

# affiliate_tag = 'zyntreck1pran-20' # Affiliate Tag here
affiliate_tag = '2550k-20'

chrome_path = "data\\chromedriver.exe"
driver = webdriver.Chrome(chrome_path) #Starts chrome

# Get media and details of a product and store it a folder.	
file_names = glob.glob("links *.txt")
if (len(file_names) > 1):
	print("\t\tMore than one link text files found. (Files that are starting with 'links *.txt')")
	exit(5)
elif (len(file_names) == 0):
	print("\t\tNo link text file found. (Files that are starting with 'links *.txt')")
	exit(5)
with open(file_names[0]) as infile:
	for link in infile:
		try:
			driver.get(link)

			link = driver.current_url
			productID = ""
			splitLink = link.split("/")
			for item in splitLink:
				if item[0:2] == "B0":
					productID = item[0:10]
			if productID == "":
				productID = "FAILED TO GET PRODUCT ID"
				error = "************************************ ERROR OCCURED ************************************\nError occured when trying to parse: " + link + "\n" + "Could not find a valid ID" + "\n"
				print(error)
			else:
				if networkErrorDetected:
					driver.refresh()
				# Click on the Change address popup button and dismisses it.
				sleep(20)
				clickOn = driver.find_elements_by_css_selector('.a-button.a-spacing-top-base.a-button-base.glow-toaster-button.glow-toaster-button-dismiss')
				if (len(clickOn) != 0):
					clickOn[0].click()

				path = os.path.dirname(os.path.realpath(__file__))
				print('\nWorking on: ' + productID)
				productName , fullProductName, description, technical_details, additional_details, extra_details, similar_product_titles, shortLink, typeOfPage, tags = getDetails(driver, productID, affiliate_tag)
				writeData(path, productID, productName, fullProductName, description, additional_details, technical_details, extra_details, similar_product_titles, shortLink, tags)
				downloadImages(driver, productID, path, typeOfPage)
				downloadVideos(driver, productID, path, typeOfPage)
		except gaierror:
			networkErrorDetected = True
			print('******************** Connection Lost with Socket********************\n\tRetrying in 5 seconds')
			sleep(5)
			pass
		except urllib.error.URLError:
			networkErrorDetected = True
			print('******************** Connection Lost with urllib/Download********************\n\tRetrying in 5 seconds')
			sleep(5)
			pass
		except bitly_api.bitly_api.BitlyError:
			networkErrorDetected = True
			print('******************** Connection Lost with bitly_api/Link Shortning********************\n\tRetrying in 5 seconds')
			sleep(5)
			pass
		except Exception:
			error = "************************************ ERROR OCCURED ************************************\nError occured when trying to parse: " + link + "\n" +traceback.format_exc() + "\n"
			logging.error(error)
			pass
	infile.close()

for link in allFailedProducts:
	try:
		splitLink = link.split("/")
		for item in splitLink:
			if item[0:2] == "B0":
				productID = item[0:10]
				print(productID)
		if productID == "":
			productID = "FAILED TO GET PRODUCT ID"
			error = "************************************ ERROR OCCURED ************************************\nError occured when trying to parse: " + link + "\n" + "Could not find a valid ID" + "\n"
			print(error)
		driver.get(link)
		path = os.path.dirname(os.path.realpath(__file__))
		print('\nReWorking on: ' + productID)
		productName , description, additional_details, extra_details, shortLink, typeOfPage, tags = getDetails(driver, productID, affiliate_tag)
		writeData(path, productID, productName, description, shortLink)
		downloadImages(driver, productID, path, typeOfPage)
		downloadVideos(driver, productID, path, typeOfPage)
	except:
		print('******************** Connection Lost with Socket********************\n\tRetrying in 5 seconds')