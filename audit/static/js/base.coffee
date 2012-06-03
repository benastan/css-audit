window.Audit = ((b) ->
	byId = (id) ->
		return document.getElementById(id)
	$byId = (id) ->
		return $(byId(id))	
	Audit = window.Audit
	# Tabs
	$.fn.tabs = () ->
		this.each () ->
			$this = $ this
			tabControls = $this.find('.tabs').find('> li')
			tabContent = $this.find('.tab-content').find('> div')
			tabControls.each (index) ->
				$tab = $ this
				content = tabContent.eq index
				others = tabContent.not content
				$tab.click () ->
					others.removeClass 'active'
					content.addClass 'active'
					tabControls.removeClass 'active'
					$tab.addClass 'active'
			tabContent.first().addClass 'active'
			tabControls.first().addClass 'active'
	$ ($) ->
		$.extend Audit,
			mainContent: $byId('main-content')
			pageContent: $byId('page-content')
			mainNav: $byId('main-nav')
			loginForm: $byId('login-form')
			userBanner: $byId('user-banner')
			$: (selector) ->
				Audit.mainContent.find(selector)
		Audit.$.html = (html) ->
			return Audit.mainContent.html(html)
		$body = $('body')
		Audit.templates.loginForm = Audit.mainContent.html()
		Audit.monitor()
		$('a').live 'click', (e) ->
			$this = $ this
			if $this.hasClass 'own-handler'
				return
			href = $this.attr 'href'
			if href.substr(0,4) isnt 'http'
				e.preventDefault()
				Audit.router.navigate href,
					trigger: true
		Audit.user.session = new Audit.Session
		initialLogin = _.once () ->
			Audit.router.login()
		Audit.monitor.push 'verifyAuthentication', (() ->
			Audit.user.session.fetch
				error: () ->
					Audit.user.session.ended()
					if not b.History.started
						initialLogin()
					else
						Audit.router.navigate 'login',
							trigger: true), 5
				success: (rsp) ->
		$body.bind
			sessionWipe: () ->
				Audit.user.session.destroy()
			authenticated: () ->
				# for each of the types of entities,
				# fetch all of the user's objects and 
				# get top level sets created. 
				entities =
					paths: 'PathSet'
					projects: 'ProjectSet'
					sheets: 'SheetSet'
				settings = 
					success: _.after _(entities).values().length, Audit.router.beginAuthenticatedSession
				_.each entities, (entity, key) ->
					Audit.user[key] = new Audit[entity]
					Audit.user[key].fetch settings
		$('.template').each () ->
			Audit.templates[this.id] = _.template(this.innerHTML)

		# make sure to try authenticating immediately.
		Audit.monitor.expedite 'verifyAuthentication'
	Audit
)(Backbone)
