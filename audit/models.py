from django.db import models
import urllib2
from django.contrib.auth.models import User
from django.conf import settings
from urlparse import urlparse
import datetime
import os
import tinycss
from django.core.cache import cache
from pyquery import PyQuery as pyQ
from django.db.models.signals import post_save

# Get absolute url from uri and base url.
# 
# In other words, determine if path is relative
# or absolute, and return a path that can be
# used to request a resource. 
def resolve_url(res, url):
	http = res[0:4]
	root = res[0:1]
	inheritProto = res[0:2]
	if http == 'http':
		return res
	elif inheritProto == '//':
		return 'http:'+res
	elif root == '/':
		parsed = urlparse(url)
		return 'http://'+parsed.netloc+'/' + res[1:]
	else:
		return url + '/' + res

# WebProject model
#
# Represents a set of resources. By configuring
# paths correctly, one can scan an entire web site
# for CSS selectors.
class WebProject(models.Model):
	url = models.TextField()
	name = models.CharField(max_length=64)
	user = models.ForeignKey(User)

# Internet Resource
#
# Abstract class for retrieving the source
# of resources them and storing them in the
# local filesystem.
class InternetResource(models.Model):
	url = models.TextField(blank=False)
	latest = models.CharField(max_length=10)

	class Meta:
		abstract = True
	
	def retrieveSource(self):
		try:
			handle = urllib2.urlopen(self.url)
		except urllib2.HTTPError:
			return False
		else:
			source = ''
			dailyIdentifier = str(datetime.date.today())
			self.latest = dailyIdentifier
			for line in handle:
				source += line
			sourceBin = self.getDataLocation()+'/'+dailyIdentifier
			sourceHandle = open(sourceBin, 'w')
			sourceHandle.write(source)

	def getDataLocation(self):
		dataLocation = settings.DATA_FOLDER+'/'+self.__class__.__name__
		if not os.path.exists(dataLocation):
			os.makedirs(dataLocation)
		return dataLocation+'/'+str(self.id)

	def get_latest_source(self, **kw):
		if not hasattr(self, 'latest') or not self.latest or ('cache' in kw and kw['cache'] is False):
			self.retrieveSource()
		handle = open(self.getDataLocation()+'/'+self.latest, 'r')
		source = handle.read()
		return source

# ApplicationPath
#
# Represents an HTML page. This page
# is query-able via the PyQuery method.
class ApplicationPath(InternetResource):
	project = models.ForeignKey(WebProject, related_name="paths", blank=False)
	user = models.ForeignKey(User, related_name="paths", blank=False)
	requires_authentication = models.BooleanField(default=False)
	isDefault = models.BooleanField(default=False)

	class Meta:
		abstract = False	

	def py_query(self):
		if not hasattr(self, 'pyPath'):
			source = self.get_latest_source()
			self.pyPath = pyQ(source)
		return self.pyPath
	
	def match_selector(self, selector):
		pyPath = self.py_query()
		return pyPath(selector)
		
	def sync_stylesheets(self):
		source = self.get_latest_source()
		doc = pyQ(source)
		links = doc.find('link[rel="stylesheet"]')
		inlineSheets = doc.find('style')
		for sheet in links:
			sheet = pyQ(sheet)
			href = sheet.attr('href')
			url = resolve_url(href, self.project.url);
			sheet = Stylesheet.objects.filter(project=self.project, url=url)
			if len(sheet) != 0:
				sheet = sheet[0]
			else:
				sheet = Stylesheet(url=url)
				sheet.user = self.user
				sheet.project = self.project
				sheet.save()
			sheet.paths.add(self)
			sheet.save()

	def extract_paths(self):
		project = self.project
		user = self.user
		base = ApplicationPath.objects.filter(project=project)
		pyQ = self.py_query()
		links = pyQ('a')
		projectUrl = self.project.url
		netloc = urlparse(projectUrl).netloc
		for link in links:
			if 'href' in link.attrib:
				href = link.attrib['href']
				href = resolve_url(href, projectUrl)
				path = base.filter(url=href) 
				if len(path) == 0:
					parsed = urlparse(href)
					if parsed.netloc == netloc:
						path = ApplicationPath(url=href)
						path.project=project
						path.user=user
						path.save()

# Stylesheet
#
# Represents a stylesheet within a web project.
# Stylesheets are scanned and offer various 
# stats (e.g. 
class Stylesheet(InternetResource):
	project = models.ForeignKey(WebProject, related_name="stylesheets")
	paths = models.ManyToManyField(ApplicationPath, related_name="stylesheets")
	user = models.ForeignKey(User, related_name="stylesheets")
	prototype = models.ForeignKey('self', related_name="clones", null=True)
	origUrl = models.TextField(blank=False)	
	inline = models.BooleanField(blank=False)
	imported = models.BooleanField(blank=False)

	class Meta:
		abstract = False	

	def extract_inline_source(self):
		source = self.get_latest_source()
		doc = pyQ(source)
		sheets = doc.find('style')
		source = ''
		for sheet in sheets:
			source += pyQ(sheet).html()

	def get_parsed_sheet(self):
		source = self.get_latest_source()
		if not hasattr(self, 'sheet'):
			if self.inline is True:
				source = self.extract_inline_source()
			parser = tinycss.make_parser()
			sheet = parser.parse_stylesheet(source)
			self.sheet = sheet
		return self.sheet

	def process_rule_sets(self):
		if len(self.rulesets.all()) > 0:
			return
		sheet = self.get_parsed_sheet()
		for rule in sheet.rules:
			if rule.at_keyword is None:
				ruleset = RuleSet()
				ruleset.project = self.project
				ruleset.user = self.user
				ruleset.stylesheet = self
				ruleset.from_tinycss_ruleset(rule);

class Selector(models.Model):
	stylesheets = models.ManyToManyField(Stylesheet, related_name="selectors")
	users = models.ManyToManyField(User, related_name="selectors")
	project = models.ForeignKey(WebProject, related_name="selectors", blank=False)
	text = models.TextField(blank=False)

class RuleSet(models.Model):
	stylesheet = models.ForeignKey(Stylesheet, related_name="rulesets", blank=False)
	user = models.ForeignKey(User, related_name="rulesets", blank=False)
	project = models.ForeignKey(WebProject, related_name="rulesets", blank=False)
	selector = models.ForeignKey(Selector, related_name="rulesets", blank=False)
	type = models.CharField(max_length=32)
	text = models.TextField()

	def from_tinycss_ruleset(self, ruleset):
		selector_text = ruleset.selector.as_css().replace("\n", '').replace("\r", '')
		project = self.project
		user = self.user
		sheet = self.stylesheet
		selectors = selector_text.split(',')
		for selector_text in selectors:
			selector_text = selector_text.strip()
			try:
				selector = Selector.objects.get(project=project, text=selector_text)
			except Selector.DoesNotExist:
				selector = Selector()
				selector.project = project
				selector.text = selector_text
				selector.save()
				selector.stylesheets.add(sheet)
			selector.users.add(user)
			selector.save()
			self.selector = selector
			self.save()
		for item in ruleset.declarations:
			declaration = Declaration()
			declaration.ruleset = self
			declaration.user = user
			declaration.stylesheet = sheet
			declaration.project = project
			declaration.fromDeclaration(item)
			declaration.save()
		self.save()

class Declaration(models.Model):
	stylesheet = models.ForeignKey(Stylesheet, related_name="declarations", blank=False)
	ruleset = models.ForeignKey(RuleSet, related_name="declarations", blank=False)
	user = models.ForeignKey(User, related_name="declarations", blank=False)
	project = models.ForeignKey(WebProject, related_name="declarations", blank=False)
	name = models.CharField(max_length=128)
	value = models.TextField()
	priority = models.BooleanField(default=False)

	def fromDeclaration(self, declaration):
		self.name = declaration.name
		self.value = declaration.value.as_css()
		print declaration.priority
		if declaration.priority is None:
			self.priority = False
		else:
			self.priority = True

def project_created(sender, **kw):
	project = kw['instance']
	if kw['created']:
		path = ApplicationPath(url=project.url+'/')
		path.project = project
		path.user = project.user
		path.save()

def path_created(sender, **kw):
	path = kw['instance']
	if kw['created']:
		path.sync_stylesheets()
		path.extract_paths()

def sheet_created(sender, **kw):
	sheet = kw['instance']
	if kw['created']:
		sheet.process_rule_sets()

post_save.connect(project_created, sender=WebProject)
post_save.connect(path_created, sender=ApplicationPath)
post_save.connect(sheet_created, sender=Stylesheet)
