window.Audit = (($, b) ->
	$body = undefined
	$ () ->
		$body = $ 'body'
	BaseRouter = b.Router.extend
		routes:
			'home': 'projectDashboard'
			'projects/add': 'addProject'
			'projects/:project': 'projectRedirect'
			'projects/:project/:method': 'projectHandler'
			'projects/:project/:method/:page': 'projectHandler'
			'sheets/:sheet': 'projects'
			'projects': 'projectDashboard'
			'login': 'login'
			'*path': 'projectDashboard'
		login: () ->
			$body.trigger('sessionWipe')
			Audit.pageContent.html Audit.templates.loginForm
			Audit.pageContent.tabs()
			form = $('#loginForm')
			if form.length is 0
				undefined
			username = form.find '.username'
			password = form.find '.password'
			errors = Audit.FormUtils.get_errors form
			data = {}
			ajaxSettings =
				url: '/api/authenticate'
				type: 'POST'
				data: {}
			form.live 'submit', (e) ->
				e.preventDefault()
				$.each errors, () ->
					this.hide()
				$.extend data,
					username: username.val()
					password: password.val()
				if (() ->
					if not data.username
						errors['blank-username'].show()
						areErrors = true
					if not data.password
						errors['blank-password'].show()
						areErrors = true
					areErrors)()
					return
				ajaxSettings.data = JSON.stringify data
				$.ajax ajaxSettings
				Audit.monitor.expedite 'verifyAuthentication'
				undefined
			undefined
		addProject: () ->
			project = new Audit.Project
			project.on 'change:id', () ->
				Audit.user.projects.add project
				this.navigate '/projects/'+project.id,
					trigger: true
			Audit.dashboard.setProject project
			Audit.dashboard.infoPage()
		projects: () ->
		projectRedirect: (id) ->
			Audit.router.navigate '/projects/'+id+'/info'
				trigger: true
		projectHandler: (id, method, page) ->
			if not Audit.user.projects.length
				return Audit.router.navigate '/projects/add',
					trigger: true
			project = Audit.user.projects.get id
			if not project
				project = Audit.user.projects.at 0
				return Audit.router.navigate '/projects/'+project.id+'/'+method
					trigger: true
			Audit.dashboard.setProject project
			if method is 'info'
				Audit.dashboard.infoPage()
			else if method is 'paths'
				Audit.dashboard.pathsNavigator(page)
		projectPaths: (id) ->
			project = Audit.user.projects.get id
			if not project
				project = Audit.user.projects.at 0
		beginAuthenticatedSession: () ->
			Audit.pageContent.html ''
			dashboard = new Audit.ProjectDash
			dashboard.render Audit.user.projects
			dashboard.$el.appendTo Audit.pageContent
			Audit.dashboard = dashboard
			if not b.History.started
				b.history.start
					pushState: true
			else
				Audit.router.navigate '',
					trigger: true
	Audit.router = new BaseRouter
	Audit
)(jQuery, Backbone)