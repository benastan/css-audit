from django.conf.urls import patterns, include, url
from audit.api.handlers import *
from piston.resource import Resource

auth = UserIsAuthenticated()
not_found_handler = Resource(NotFoundHandler)
project_handler = Resource(WebProjectHandler, authentication=auth)
stylesheet_handler = Resource(StylesheetHandler, authentication=auth)
path_handler = Resource(PathHandler, authentication=auth)
user_handler = Resource(UserHandler, authentication=auth)
authentication_handler = Resource(AuthenticationHandler)
rule_handler = Resource(RuleSetHandler, authentication=auth)
selector_handler = Resource(SelectorHandler, authentication=auth)
declaration_handler = Resource(DeclarationHandler, authentication = auth)

urlpatterns = patterns('',
	url(r'^authenticate$', authentication_handler),
	url(r'^users/(?P<user_id>[^/]+)', user_handler),
	url(r'^users$', user_handler),
	url(r'^projects/(?P<project_id>[^/]+)', project_handler),
	url(r'^projects$', project_handler),
	url(r'^stylesheets/(?P<sheet_id>\d+)/(?P<resource>[^/]+)', stylesheet_handler),
	url(r'^stylesheets/(?P<sheet_id>[^/]+)', stylesheet_handler),
	url(r'^stylesheets$', stylesheet_handler),
	url(r'^paths/(?P<path_id>\d+)/(?P<resource>[^/]+)', path_handler),
	url(r'^paths/(?P<path_id>[^/]+)', path_handler),
	url(r'^paths$', path_handler),
	url(r'^rules/(?P<rule_id>[^/]+)', rule_handler),
	url(r'^rules$', rule_handler),
	url(r'^selectors/(?P<selector_id>[^/]+)', selector_handler),
	url(r'^selectors$', selector_handler),
	url(r'^declarations/(?P<declaration_id>[^/]+)', declaration_handler),
	url(r'^declarations$', declaration_handler),
#	url(r'', not_found_handler)
)
