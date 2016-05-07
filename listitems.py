#9:05 - 9:52
from dropbox import DropboxOAuth2FlowNoRedirect, Dropbox
from dropbox.files import FolderMetadata, FileMetadata

from operator import attrgetter
from json import load, dump
from argparse import ArgumentParser
from codecs import open
from os.path import split, join
from os import linesep

# Get your app key and secret from the Dropbox developer website
# put them in json file named "listitems.json"


# Stuffs
# based on my ghetto treeprinter.py:
# https://github.com/Clam-/Misc-Utilities/blob/master/treeprinter.py
class File(object):
	def __init__(self, name="", parent=None, size=0, modtime=0):
		self.name = name
		self.size = size
		self.modtime = modtime
		self.parent = parent

class Folder(File):
	def __init__(self, name="", path="", size=0, modtime=0, parent=None):
		File.__init__(self, name=name, size=size, modtime=modtime, parent=parent)
		self.dirs = {}
		self.files = []
		self.path = path
	
	def getFolder(self, path):
		if path == u"/": return self
		folders = path.lstrip("/").split("/")
		folder = self
		for foldname in folders:
			if foldname in folder.dirs:
				folder = folder.dirs[foldname]
			else:
				n = Folder(name=foldname, path=join(folder.path, foldname), parent=folder)
				folder.dirs[foldname] = n
				folder = n
		return folder
	
	def addFile(self, f):
		self.files.append(f)
		self.size += f.size
		parent = self.parent
		while parent:
			parent.size += f.size
			parent = parent.parent

def iterateFolder(path, dbx):
	hasmore = True
	listing = dbx.files_list_folder(path, recursive=True)
	while hasmore:
		for obj in listing.entries:
			yield obj
		hasmore = listing.has_more
		listing = dbx.files_list_folder_continue(listing.cursor)

def processFolder(path, obj, dbx):
	# preprocess list before diving
	for item in iterateFolder(path, dbx):
		if isinstance(item, FileMetadata):
			folder, file = split(item.path_lower)
			obj.getFolder(folder).addFile(File(name=item.name, parent=item, size=item.size, modtime=item.client_modified))

def size_to_human(size, unit=1024, round=5):
	if size:
		unit_name = 'byt'
		size=int(size)
		if size > unit:
			size = size/float(unit)
			unit_name = 'KiB'
		if size > unit:
			size = size/float(unit)
			unit_name = 'MiB'
		if size > unit:
			size = size/float(unit)
			unit_name = 'GiB'
		size = str(size)
		if round:
			if len(size) > round:
				size = size[0:round].rstrip(".")
		return size+unit_name
	else: 
		return ""

def printtree(node, options, level, outf):
	#if not dirfirst, combine lists
	#sort lists
	if options.depth >= 0 and level > options.depth:
		return
	combined = node.dirs.values()
	combined.sort(key=attrgetter('size'), reverse=True)
	if level == 0: prefix = ""
	else:
		prefix = ("  " * level)
	#{name} #{size} #{modtime} #{createtime}
	for item in combined:
		size = size_to_human(item.size, round=3)
		if isinstance(item, Folder):
			#recurse
			outf.write(u"{0}{1: <8}{2}{3}".format(prefix, size, item.path, linesep))
			printtree(item, options, level+1, outf)
		else:
			pass
			#TODO: File and more folder stuff.

def auth(app_creds):
	flow = DropboxOAuth2FlowNoRedirect(app_creds['app_key'], app_creds['app_secret'])

	authorize_url = flow.start()

	print "1. Go to: " + authorize_url
	print "2. Click \"Allow\" (you might have to log in first)."
	print "3. Copy the authorization code."
	auth_code = raw_input("Enter the authorization code here: ").strip()

	try:
		access_token, user_id = flow.finish(auth_code)
		if "_USERS" not in app_creds:
			app_creds["_USERS"] = {}
		app_creds["_USERS"][user_id] = access_token
		print "This user ID is %s. Pass it to --user on next invocation to skip authorization." % user_id
		dump(app_creds, open("listitems.json", "wb"))
	except Exception, e:
		print 'Error: %s' % (e,)
		exit(1)
	return access_token

if __name__ == "__main__":
	app_creds = load(open("listitems.json", "rb"))
	
	parser = ArgumentParser(description='List contents of a Dropbox account.')
	parser.add_argument('--user', metavar='email', dest="user", default=None,
		help="Username (email) of Dropbox account for follow-up logins.")
	parser.add_argument('-o', '--output', metavar='FILE', dest="outfile", default=None,
		help="Filename of output folder list.")
	parser.add_argument('--max-depth', metavar='N', type=int, dest="depth", default=None,
		help="To what depth of nesting will folders be displayed. By default all files and folders will be displayed.")
	parser.add_argument("--sort-by", dest="sortby", default="name",
		help="Sort by one of the following: [name, size]. Default: name. ONLY SIZE IMPLEMENTED AT THIS TIME.")
	options = parser.parse_args()

	if not options.user:
		access_token = auth(app_creds)
	else:
		if options.user in app_creds.get("_USERS", {}):
			access_token = app_creds.get("_USERS", {})[options.user]
		else:
			access_token = auth(app_creds)

	if options.outfile:
		outf = open(options.outfile, "wb", "utf-8")
	else:
		outf = open("dropbox.txt", "wb", "utf-8")
	dbx = Dropbox(access_token)

	root = Folder("/", "")
	print "Fetching file and folder information stored on Dropbox. Please wait..."
	processFolder(root.path, root, dbx)
	print "Fetch complete. Saving information to file..."
	printtree(root, options, 0, outf)
	outf.flush()
	outf.close()
	print "Complete."