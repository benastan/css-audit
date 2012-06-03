# Create your views here.
from django.template import Template, Context
from django.template.loader import get_template
from django.http import HttpResponse

def login_page(request):
	t = get_template('login.html')
	res = HttpResponse()
	res.write(t.render(Context({
		'body_id': 'login-page'
	})));
	return res
