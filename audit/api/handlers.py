from piston.handler import BaseHandler, AnonymousBaseHandler
from audit.models import *
from django.http import HttpResponse
import json
from django.contrib.auth.models import User
from piston.resource import Resource
from piston.utils import rc
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError

class NotFoundHandler(BaseHandler):
	allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')

	def read(self, request):
		return rc.NOT_FOUND

	def update(self, request):
		return rc.NOT_FOUND

	def create(self, request):
		return rc.NOT_FOUND
	
	def delete(self, request):
		return rc.NOT_FOUND

class UserIsAuthenticated():
	def is_authenticated(self, request):
		if request.user.is_authenticated() is True:
			return True
		else:
			return False
	
	def challenge(self):
		res = HttpResponse()
		res['Content-Type'] = 'application/json';
		res.write(json.dumps({
			'error': 'not authenticated'
		}))
		return res

class AuthenticationHandler(BaseHandler):
	allowed_methods = ('GET', 'POST', 'DELETE')
	model = User
	fields = ('username', 'id')
	exclude = ('email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'is_staff', 'last_login', 'password', 'date_joined')

	def read(self, request):
		if (request.user.is_authenticated()):
			return request.user
		else:
			return rc.NOT_FOUND

	def delete(self, request):
		logout(request)
		return rc.DELETED
	
	def create(self, request):
		if not request.raw_post_data or request.raw_post_data is None:
			return rc.BAD_REQUEST
		if request.user.is_authenticated is True:
			return rc.DUPLICATE_ENTRY
		try:
			params = json.loads(request.raw_post_data)
		except ValueError:
			return rc.BAD_REQUEST
		if not 'password' in params or params['password'] is None or not 'username' in params or params['username'] is None:
			return rc.BAD_REQUEST
		user = authenticate(username=params['username'], password=params['password'])
		if user is None:
			return rc.NOT_FOUND
		elif not user.is_active:
			return rc.DELETED
		login(request, user)
		return user

class AnonymousUserHandler(AnonymousBaseHandler):
	allowed_methods = ('GET', 'POST')
	model = User
	field = ('id', 'username',)	
	exclude = ('email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'is_staff', 'last_login', 'password', 'date_joined')

	def read(self, request, user_id=None):
		base = User.objects
		if user_id:
			return base.get(id=user_id)
		else:
			return base.all()

	def create(self, request):
		params = json.loads(request.raw_post_data)
		if not 'email' in params or params['email'] is None or not 'password' in params or params['password'] is None or not 'username' in params or params['username'] is None:
			return rc.BAD_REQUEST
		try:
			user = User.objects.create_user(params['username'], params['email'], params['password'])
		except IntegrityError:
			return rc.DUPLICATE_ENTRY
		else:
			user = authenticate(username=params['username'], password=params['password'])
			login(request, user)
			return user
		
class UserHandler(BaseHandler):
	anonymous = AnonymousUserHandler
	allowed_methods = ('GET', 'DELETE')
	fields = ('id', 'name', 'email',)	
	model = User

	def read(self, request, user_id=None):
		base = User.objects
		if user_id:
			try:
				user = base.get(id=user_id, is_active=True)
			except User.DoesNotExist:
				return rc.NOT_FOUND
			else:
				return user
		else:
			return base.filter(is_active=True)

	def delete(self, request, user_id):
		if (not request.user.is_superuser and request.user.id != user_id):
			return rc.FORBIDDEN
		else:
			try:
				user = User.objects.get(id=user_id)
			except User.DoesNotExist:
				return rc.NOT_FOUND
			else:
				user.is_active = False
				user.save()
				return rc.DELETED
				

class WebProjectHandler(BaseHandler):
	allowed_methods = ('GET', 'POST', 'PUT', 'DELETE',)
	fields = ('id', 'url', 'name')
	
	def read(self, request, project_id=None, resource=None):
		base = WebProject.objects
		if project_id:
			return base.get(id=project_id)
		else:
			return base.all()
	
	def create(self, request):
		user = request.user
		try:
			params = json.loads(request.raw_post_data)
		except ValueError:
			return rc.BAD_REQUEST
		if not 'url' in params:
			return rc.BAD_REQUEST
		url = params['url']
		project = WebProject.objects.filter(url=url)
		if len(project) > 0:
			return rc.DUPLICATE_ENTRY
		project = WebProject(url=url);
		if 'name' in params:
			project.name = params['name']
		project.user = user
		project.save()
		return project
	
	def update(self, request):
		user = request.user
		try:
			params = json.loads(request.raw_post_data)
		except ValueError:
			return rc.BAD_REQUEST
		if not 'id' in params:
			return rc.BAD_REQUEST
		try:
			project = WebProject.objects.get(id=params['id'])
		except WebProject.DoesNotExist:
			return rc.NOT_FOUND
		else:
			if 'name' in params:
				project.name = params['name']
			if 'url' in params:
				project.url = params['url']
			print project.name
			print params['name']
			project.save()
			return project

class StylesheetHandler(BaseHandler):
	allowed_methods = ('GET',)
#	model = Stylesheet
	fields = ('id', 'url', 'inline', 'imported', ('project', ('id', 'url', 'name')), ('paths', ('id','url')), ('selectors', ('id', 'name')))

	def read(self, request, sheet_id=None, resource=None):
		user = request.user
		q = request.GET
		base = Stylesheet.objects.filter(user=user)
		if sheet_id:
			sheet = base.filter(id=sheet_id)
			if len(sheet) == 0:
				return rc.NOT_FOUND
			else:
				sheet = sheet[0]
				if resource:
					if resource == 'source':
						return {
							'source': sheet.get_latest_source()
						}
				else:
					return sheet
		else:
			if 'project' in q:
				base = base.filter(project=q['project'])
			if 'path' in q:
				base = base.filter(paths=q['path'])
			return base

class PathHandler(BaseHandler):
	allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
	fields = ('id', 'url', 'project_id') 

	def read(self, request, path_id=None, resource=None):
		user = request.user
		base = ApplicationPath.objects.filter(user=user)
		if path_id:
			path = base.filter(id=path_id)
			if len(path) == 0:
				return rc.NOT_FOUND
			path = path[0]
			if resource:
				if resource == 'source':
					return {'source': path.get_latest_source()}
			return path
		else:
			q = request.GET
			if 'project' in q:
				base = base.filter(project=q['project'])
			if 'stylesheet' in q:
				base = base.filter(stylesheets=q['stylesheet'])
			if 'isDefault' in q:
				isDefault = q['isDefault']
				if isDefault == 'false' or isDefault == 'False':
					isDefault = False
				base = base.filter(isDefault=bool(isDefault))
			return base

	def create(self, request):
		print request.raw_post_data
		user = request.user
		try:
			params = json.loads(request.raw_post_data)
		except ValueError:
			return rc.BAD_REQUEST
		if not 'url' in params or not 'project' in params:
			return rc.BAD_REQUEST
		project = WebProject.objects.filter(id=params['project'])
		if len(project) == 0:
			return rc.BAD_REQUEST
		path = ApplicationPath(url=params['url'], project=project[0], user=user)
		path.save()
		return path

	def update(self, request, path_id):
		base = ApplicationPath.objects
		path = base.get(id=path_id)
		new = json.loads(request.raw_post_data)
		print new['url']
		if 'url' in new: 
			path.url = new['url']
		path.save()
		return path

class RuleSetHandler(BaseHandler):
	allowed_methods = ('GET')
#	fields = ('id', ('project', ('id')), ('selector', ('id', 'text')), ('stylesheet', ('id', 'url')), ('declarations', ('id', 'name', 'value', 'priority')))
	fields = ('id', 'project_id', ('selector', ('id', 'text')), ('declarations', ('name', 'value', 'id')))
#	fields = ('id', 'project': ('id'), 'path': ('id'), 'selector': ('id', 'text'), 'declarations': ('id', 'name', 'value'))

	def read(self, request, rule_id=None):
		q = request.GET
		user = request.user
		base = RuleSet.objects.filter(user=user)

		if rule_id is not None:
			rule = base.filter(id=rule_id)
			if len(rule) == 0:
				return rc.NOT_FOUND
			else:
				return rule[0]
		else:
			if 'stylesheet' in q:
				base = base.filter(stylesheet=int(q['stylesheet']))
			if 'project' in q:
				base = base.filter(stylesheet=int(q['project']))
			if 'selector' in q:
				base = base.filter(selector=int(q['selector']))
			if 'declaration' in q:
				base = base.filter(declarations=int(q['declaration']))
#			if not 'page' in q:
#				q['page'] = 0
#			if not 'perpage' in q:
#				q['perpage'] = 10
#			start = page * perpage
#			end = (page + 1) * perpage - 1
			return base

class SelectorHandler(BaseHandler):
	allowed_methods = ('GET')
	fields = ('id', 'text')

	def read(self, request, selector_id=None):
		user = request.user
		base = Selector.objects.filter(users=user)

		if selector_id is not None:
			base = base.filter(id=selector_id)
			if len(selector) == 0:
				return rc.NOT_FOUND
			else:
				return base[0]
		else:
			q = request.GET
			if 'text' in q:
				base = base.filter(text=q['text'])
			if 'rule' in q:
				base = base.filter(rules=q['rule'])
			if 'stylesheet' in q:
				base = base.filter(stylesheets=q['stylesheet'])
			return base

class DeclarationHandler(BaseHandler):
	allowed_methods = ('GET')
	fields = ('id', 'name', 'value', 'priority', ('ruleset', ('id', ('selector', ('id', 'text')))))

	def read(self, request, declaration_id=None):
		user = request.user
		base = Declaration.objects
		if declaration_id is not None:
			declaration = base.filter(id=declaration_id, user=user)
			if len(declaration) == 0:
				return rc.NOT_FOUND
			else:
				return declaration[0]
		else:
			q = request.GET
			if 'name' in q and 'value' in q:
				return base.filter(name=q['name'], value=q['value'])
			elif 'name' in q:
				return base.filter(name=q['name'])
			elif 'value' in q:
				return base.filter(value=q['name'])
			else:
				res = base.filter(user=user)
				return res[0:100]
