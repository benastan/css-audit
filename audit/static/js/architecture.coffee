window.Audit = (($, b) ->
	Audit =
		user: {}
		FormUtils: {}
		templates: {}
		Entity:
			models: {}
			views: {}
			collections: {}

	# The monitor
	monitors = {}
	Audit.monitor = () ->
		_.each monitors, (item, index) ->
			if not item then return false
			if item.paused then	return false
			item.countdown--
			if item.countdown is 0
				item.fn()
				item.countdown = item.regularity
		_.delay Audit.monitor, 500
	$.extend Audit.monitor,
		push: (key, fn, regularity) ->
			if not regularity then regularity = 1
			monitors[key] =
				fn: fn,
				regularity: regularity,
				countdown: regularity,
				paused: false
		rm: (key) ->
			monitors[key] = undefined
		pause: (key) ->
			index = $.inArray key
			if index isnt -1 then monitors[key].paused = true
		resume: (key) ->
			index = $.inArray key
			if index isnt -1 then monitors[key].paused = false
		expedite: (key) ->
			if monitors[key]
				monitors[key].countdown = 1
	
	# Form Utilities
	Audit.FormUtils.get_errors = (context) ->
		map = {}
		context.find('.error').each () ->
			$this = $(this)
			$.each $this.attr('class').split(' '), () ->
				map[this] = $this
		map
	Model = b.Model.extend()
	Set = b.Collection.extend
		perpage: 10
		currentPage: 1
		numPages: -> Math.ceil @models.length / @perpage
		nextPage: -> @movePage 1
		previousPage: -> @movePage -1
		movePage: (numPages) ->
			page = @currentPage + numPages
			totalPages = @numPages()
			@currentPage = if page > totalPages then 1 else if page <= 0 then totalPages else page
		getPage: (page) -> @models.slice (@currentPage - 1) * @perpage, @currentPage * @perpage - 1
		getCurrentPage: -> @getPage @currentPage
	UI = b.View.extend
		mappings: {}
		map: {}
		mapDOM: () ->
			map = this.mappings
			_.each map, (item, index) =>
				if typeof item is 'string'
					this.map[index] = this.$ item
				else
					this.map[index] = this.map[item[1]].find item[0]
	BaseNav = UI.extend
		tagName: 'ul'
		className: 'nav'
		template: 'navTemplate'
		render: (collection) ->
			template = Audit.templates[this.template]
			html = template
				projects: collection.models
			this.el.innerHTML = html
	BaseDash = UI.extend
		tagName: 'row'
		entityName: 'Entity'
		template: 'dashTemplate'
		render: (collection) ->
			this.el.innerHTML = Audit.templates[this.template]
				entityName: this.entityName
				entities: collection.models
	Session = Model.extend
		url: '/api/authenticate',
		initialize: () ->
			this.on 'change:id', () ->
				$body.trigger 'authenticated'
		ended: () ->
			this.attributes = {}
			this.id = undefined
	User = Model.extend
		url: '/api/users'
		initialize: () ->
			loaded = _.after 3, () =>
				this.trigger('loaded')
			_.each 'Path Sheet Project'.split(' '), (item) =>
				key = item.toLowerCase()
				this[key] = new eval(item).collection
				this[key].fetch
					success: loaded
		entitiesLoaded: false
	Project = Model.extend
		url: '/api/projects'
		getUrl: () -> if this.id then '/projects/'+this.id else '/projects'
		initialize: () ->
			if this.id
				this.fetchPaths()
			else:
				this.change 'id', _.once () =>
					this.fetchPaths()
		fetchPaths: () ->
			this.paths = new PathSet
			this.paths.add Audit.user.paths.where
				project_id: this.id
	ProjectSet = Set.extend
		url: '/api/projects'
		model: Project
	ProjectDash = UI.extend
		initialize: () ->
			dashboard = this
			map = this.map
			Audit.user.projects.on 'change:name', (model, value) ->
				newName = model.get('name') || 'untitled project'
				map.projectsDropdownItems.filter('.project-'+model.id).find('a').html newName
				if dashboard.project.id is model.id
					dashboard.setTitle newName
			container = $ '#container'
			userBanner = $ '#user-banner'
			name = userBanner.find '.name'
			Audit.user.session.on 'change:id', (model) ->
				container.removeClass 'notLoggedIn'
				name.html model.get 'username'
			Audit.user.session.on 'destroy', () ->
				container.addClass 'notLoggedIn'
			this.pathsNavigatorPage = 0
		id: 'project-dashboard'
		className: 'dashboard'
		entityName: 'Projects'
		mappings:
			title: 'h1'
			projectsDropdown: '#switch-project .dropdown-menu'
			projectsDropdownItems: ['li', 'projectsDropdown']
			newProject: ['.new-project', 'projectsDropdown']
			navigation: '#project-navigation'
			navTabs: ['li', 'navigation']
			infoTab: ['.info', 'navigation']
			pathsTab: ['.paths', 'navigation']
			sheetsTab: ['.sheets', 'navigation']
			entities: ['section', 'navigation']
			entitiesListings: ['ul', 'entities']
			sheetsListing: ['.sheets', 'entities']
			pathsListing: ['.paths', 'entities']
			detailsSection: '#subpage-details'
		events:
			'click nav li': 'changeNav'
		changeNav: (e) ->
			e.preventDefault()
			$tgt = $ e.currentTarget
			$tgt.siblings().removeClass 'active'
			$tgt.addClass 'active'
			this.map.entitiesListings.hide()
			if $tgt.hasClass 'paths'
				this.map.pathsListing.show()
			if $tgt.hasClass 'sheets'
				this.map.sheetsListing.show()
			Audit.router.navigate 'projects/'+this.project.id+'/'+$tgt.find('a').attr('href'),
				trigger: true
		setTitle: (title) ->
			this.map.title.html (title || 'untitled project') + '<span class="badge">project</span>'
		setProject: (project) ->
			if this.project
				this.$el.removeClass if this.project.id then 'project-'+this.project.id else 'project-new'
			if this.project is project
				return
			this.project = project
			this.$el.addClass if this.project.id then 'project-'+this.project.id else 'project-new'
			this.setTitle project.get 'name'
			this.map.entitiesListings.each () ->
				this.innerHTML = ''
		render: (projects) ->
			BaseDash.prototype.render.apply this, arguments
			this.mapDOM()
		infoPage: () ->
			project = this.project
			dashboard = this
			map = this.map
			map.navTabs.removeClass 'active'
			map.infoTab.addClass 'active'
			template = Audit.templates['projectInfoTemplate']
			map.detailsSection.html template
				project: project
			saveBtn = map.detailsSection.find '.save button'
			if project.id
				map.detailsSection.find('.project-url input').attr 'disabled', 'disabled'
			saveBtn.click (e) ->
				e.preventDefault()
				params =
					name: map.detailsSection.find('.project-name').find('input').val()
				options =
					success: () ->
						saveBtn.html('Update!').addClass 'btn-success'
						_.delay (() ->
							saveBtn.html('Update').removeClass 'btn-success'), 500
				if not project.id
					params.url = map.detailsSection.find('.project-url').find('input').val()
					console.log map.detailsSection.find('.project-url')
					options.success = () ->
						saveBtn.html('Saved!').addClass 'btn-success'
						_.delay (() ->
							Audit.dashboard.project = false
							Audit.dashboard.setProject project
							), 500
				console.log params, options
				project.save params, options			
		pathsNavigator: (page) ->
			page || page = 1
			template = Audit.templates['pathsNavigatorTemplate']
			project = this.project
			paths = project.paths
			paths.currentPage = page
			map = this.map
			map.navTabs.removeClass 'active'
			map.pathsTab.addClass 'active'
			map.detailsSection.html template
				currentPage: page
				project: project.id
				numPages: paths.numPages()
			map.pathsTableHolder = this.$ '.pathsTableHolder'
			_.each paths.getCurrentPage(), (path) ->
				view = new PathDash
				view.path = path
				view.render()
				view.$el.appendTo map.pathsTableHolder
		template: 'dashTemplate'
	PathDash = UI.extend
		tagName: 'article'
		className: 'path'
		hasBeenRendered: false
		render: () ->
			if not this.path
				this.renderAddComponent()	
				return
			path = this.path
			template = Audit.templates['pathDashTemplate']
			path.getSheets()
			this.el.innerHTML = template
				path: path.toJSON()
			path.on 'change', _.once () =>
				this.render()
		renderAddComponent: () ->
			false
	Path = Model.extend
		url: '/api/paths'
		initialize: () ->
			if this.id then this.getSheets() else this.on 'change:id', _.once () => this.getSheets()
		set: (key, val) ->
			if typeof key is 'object'
				_.each key, (v, k) => this.set k, v 
				return
			if key is 'url'				
				a = document.createElement('a')
				a.href = val
				this.set 'host', a.host
				this.set 'uri', a.pathname
			Model.prototype.set.apply(this, [key, val]);
		getSheets: () ->
			sheets = new SheetSet
			sheets.add Audit.user.sheets.filter (model) =>
				$.inArray(this.id, model.get('paths')) isnt -1
			this.set 'sheets', sheets
	PathSet = Set.extend
		url: '/api/paths'
		model: Path
	Sheet = Model.extend
		url: '/api/stylesheets'
		initialize: (attributes) ->
			getPaths = () => 
				if Audit.user.paths
					this.paths = Audit.user.paths.filter (model) =>
						$.inArray(this.id, model.get('paths')) isnt -1
					getPaths = () =>
				else
					_.delay getPaths, 50
			if not attributes.id
				this.on 'change:id', getPaths
		set: (attr, value) ->
			if typeof attr is 'object'
				_.each attr, (value, attr) =>
					this.set attr, value
				return
			if attr is 'paths'
				arguments[1] = _.pluck value, 'id'
			if attr is 'url'
				a = document.createElement('a')
				a.href = value
				this.set 'host', a.host
				this.set 'uri', a.pathname
			Model.prototype.set.apply this, arguments
	SheetSet = Set.extend
		url: '/api/stylesheets'
		model: Sheet
	$body = undefined
	$ () ->
		$body = $('body')
	_.each 'Session Project User Path Sheet SheetSet PathSet PathDash ProjectDash ProjectSet'.split(' '), (item) ->
		Audit[item] = eval item
	Audit
)(jQuery, Backbone)
