#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os, errno
from markdown2 import markdown
from subprocess import Popen
from flask import Flask, render_template, request, Response, redirect
app = Flask(__name__)

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
	if content and request.args.get('edit') is None:
		return render_template('wiki.html', path=request.path,
				content=markdown(content), breadcrum=breadcrum)
	return render_template('editor.html', path=request.path, content=content,
			breadcrum=breadcrum)


@app.route("/", methods=['POST'])
@app.route("/<path:path>", methods=['POST'])
def save(path=''):

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


init()


if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=True)
