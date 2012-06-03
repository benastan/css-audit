# CSS Audit

An online interface and Restful API for examining and optimizing stylesheets within the context of a web site or application.

# Dependencies

- [Django](https://www.djangoproject.com/)
- [django-compressor](https://github.com/jezdez/django_compressor)
- [node.js](http://nodejs.org/)
- [npm](http://npmjs.org/)
- [CoffeeScript](http://www.coffeescript.org)
- [uglify-js](https://github.com/mishoo/UglifyJS)
- [LESS](http://lesscss.org/)

### Python Dependencies

    easy_install Django
    easy_install django_compressor

#### JavaScript dependencies

    apt-get install nodejs npm
    npm install -g coffee-script
    npm install -g uglify-js
    npm install -g less
    
# Major @TODOs

1. When a WebProject is created, the `/` ApplicationPath is automatically scanned for internal paths, which are in turn scanned for Stylesheets, which are broken down into Selectors, RuleSets and Declarations. This process is currently synchronous; it should be converted into tasks using a task management application like Celery.
2. My #1 goal was to easily allow users to find all unused selectors in a WebProject and, potentially, retrieve a cleaned up version of their stylesheets, without these selectors.
3. Design Stylesheet browser UI. How to display selectors/rules?
4. User needs to be able to query an ApplicationPath to find UI elements that match selectors in a Stylesheet. (It would be cool if users could make CSS- and HTML-wide changes to class/id names.)