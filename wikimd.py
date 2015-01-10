#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os, errno
from markdown2 import markdown
from subprocess import Popen
from hashlib import sha512
from flask import Flask, render_template, request, Response, redirect, session, url_for
app = Flask(__name__)
app.secret_key = 'LHlhdeuhlkeuKJHLuwhdlajLz7ZO7h3ohdo3o'

import config

DATADIR = '%s/data' % os.path.dirname(os.path.realpath(__file__))


def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc:
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def init():
	mkdir_p(DATADIR)
	os.system('''
			pushd %s > /dev/null
			[ -d .git ] || git init
			popd > /dev/null
			''' % DATADIR)


@app.route("/")
@app.route("/<path:path>")
def home(path=''):

	pathsegments = path.strip('/').split('/')
	pathsegments = pathsegments if pathsegments[0] else pathsegments[1:]
	breadcrum = [('⌂','/')] \
			+ [ (pathsegments[i], '/' + '/'.join(pathsegments[:i+1]))
					for i in range(len(pathsegments)) ]

	path = '%s/%s' % (DATADIR, path)

	if os.path.isdir(path):
		path += 'index' if path.endswith('/') else '/index'
	path += '.md'
	content = ''
	if os.path.isfile(path):
		with open(path, 'r') as f:
			content = f.read()

	# Navigation we want to show
	nav = []
	if session.get('user'):
		nav = ('logout','edit')
	elif config.USER:
		nav = ('login',)
	else:
		nav = ('edit',)

	if content and request.args.get('edit') is None:
		return render_template('wiki.html', path=request.path, nav=nav,
				content=markdown(content), breadcrum=breadcrum)
	if session.get('user') or not config.USER:
		return render_template('editor.html', path=request.path, content=content,
				breadcrum=breadcrum, nav=nav)
	if not request.args.get('edit') is None:
		return '', 404
	return render_template('wiki.html', path=request.path, nav=nav,
			content='No content', breadcrum=breadcrum)


@app.route("/", methods=['POST'])
@app.route("/<path:path>", methods=['POST'])
def save(path=''):

	# Check if user is allowed to edit
	if config.USER and not session.get('user'):
		return '', 404

	path = '%s/%s' % (DATADIR, path)

	if os.path.isdir(path):
		path += 'index' if path.endswith('/') else '/index'
	path += '.md'
	mkdir_p(path.rsplit('/',1)[0])
	with open(path, 'w') as f:
		f.write(request.form['content'])

	# Invoke Git
	filename = path[len(DATADIR):].lstrip('/')
	message = request.form.get('message') or ('Edited ' + filename)
	Popen(['git', 'add', filename], cwd=DATADIR ).communicate()
	Popen(['git', 'commit', '-m', message], cwd=DATADIR ).communicate()

	# Return page
	return redirect(request.path)


@app.route('/login', methods=['POST'])
def login():
	user = [u for u in config.USER if u[0] == request.form.get('user')]
	if not user:
		return redirect(url_for('home'))
	user, salt, passwd = user[0]
	if passwd != sha512(salt + request.form.get('password')).hexdigest():
		return redirect(url_for('home'))
	session['user'] = user
	return redirect(url_for('home'))


@app.route('/logout')
def logout():
	# remove user from session if it's there
	session.pop('user', None)
	return redirect(url_for('home'))


init()


if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True)
