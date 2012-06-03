from django.conf.urls import patterns, include, url

urlpatterns = patterns('',

  # API URLS.
	url(r'^api/', include('audit.api.urls')),

	# Route everything to the UI.
	# App routing is handled by Backbone.
	url(r'^', 'audit.views.login_page'),
)
