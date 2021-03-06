#!/usr/bin/python

# XXX Recalculate the sizes for int's instead of char arrays
# XXX Work out how to pre-populate as ints instead of char arrays


import json
import sys
import re
from pprint import pprint

# Horribly quick & dirty check
if len(sys.argv) < 3:
	print "Not enough args"
	print "Usage:",sys.argv[0],"<fingerprint file> <output>"
	print "Possible Outputs:"
	print "  struct    Output C Structures"
	print "  ids       Output Suricata/Snort Signatures"
	print "  idsinit   Output Suricata/Snort Signatures matching only"
	print "            initial handshake (sessionid 0)"
	print "  cleanse   Re-output at JSON with some format un-breaking (beta)"
	print "  xkeyscore OK, it's regex, and not that great, probably best not"
	print "            to use this!"

	exit()

# Open the JSON file
#with open(sys.argv[1]) as data_file:
#	jfile = json.load(data_file)
jfile = []
with open(sys.argv[1]) as f:
    for line in f:
        jfile.append(json.loads(line))

# I don't python, which is clear as I fail to use whatever the switch/case
# style statements and just go if else nuts instead.... Woo!

if (sys.argv[2] == 'cleanse'):
	# Reoutput the database cleaned a little...  e.g. before uploading somewhere
	objcount = len(jfile)
	j2file = []
	with open(sys.argv[1]) as f:
		for line in f:
			j2file.append(json.loads(line))
	# Not the smartest check ever but if the fingerprint is the same, not including
	# id, desc & server it'll flag as a duplicate.  Will miss a 100% identical line,
	# but that's ok because this was for the stuff sort & unique can't handle.
	for i in jfile:
		for x in j2file:
			if i["record_tls_version"] == x["record_tls_version"] and \
				i["tls_version"] == x["tls_version"] and \
				i["ciphersuite_length"] == x["ciphersuite_length"] and \
				i["ciphersuite"] == x["ciphersuite"] and \
				i["compression_length"] == x["compression_length"] and \
				i["compression"] == x["compression"] and \
				i["extensions"] == x["extensions"] and	\
				"e_curves" in i \
				and	i["e_curves"] == x["e_curves"] and \
				"sig_alg" in i and \
				i["sig_alg"] == x["sig_alg"] and \
				"ec_point_fmt" in i and \
				i["ec_point_fmt"] == x["ec_point_fmt"]:
					if i["desc"] != x["desc"]:
						print "# Oh no, 2 signatures match: "+str(i["desc"])+" - "+str(x["desc"])
					#else:
						#print "# Oh no, duplicate copies of: "+str(i["desc"])

		# Fix some minor annoyances
		# I hate commas in quotes in a comma delimited file... I like cut... OK?
		i["desc"] = i["desc"].replace(",", " ")


		# Reprint, hopefully with nicely equally spaced and comma'd and whatever fields
		print "{\"id\": "+str(i["id"])+", \"desc\": \""+i["desc"]+"\", \"record_tls_version\": \"",
		print i["record_tls_version"]+"\", \"tls_version\": \""+i["tls_version"],
		print "\", \"ciphersuite_length\": \""+i["ciphersuite_length"],
		print "\", \"ciphersuite\": \""+i["ciphersuite"]+"\", ",
		print "\"compression_length\": \""+i["compression_length"],
		print "\",  \"compression\": \""+i["compression"]+"\", ",
		print "\"extensions\": \""+i["extensions"]+"\", \"e_curves\": \"",
		if "e_curves" in i:
			print i["e_curves"],
		print "\", \"sig_alg\": \"",
		if "sig_alg" in i:
			print i["sig_alg"],
		print "\", \"ec_point_fmt\": \"",
		if "ec_point_fmt" in i:
			print i["ec_point_fmt"],
		print "\", \"server\": \"\" }"






elif (sys.argv[2] == 'ids') or (sys.argv[2] == 'idsinit'):
	# Creating Snort signatures from the fingerprint data
	# Walk through each entry outputting the appropriate snort rule
	sid = 1000000;
	for i in jfile:

		# Reformat some of the values prior to printing out rules
		# Different format in the JSON to how suricata/snort want it
		# Mostly just removing 0x and changing how bytes are grouped
		i["desc"] = i["desc"].replace(";", ":")
		i["record_tls_version"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', i["record_tls_version"])
		i["tls_version"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', i["tls_version"])
		i["ciphersuite_length"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', i["ciphersuite_length"])
		i["ciphersuite"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', i["ciphersuite"])
		i["compression_length"] = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\1', hex(int(i["compression_length"])))
		i["compression_length"] = re.sub(r'^([0-9A-Fa-f])$', r'0\1', i["compression_length"])
		i["compression"] = re.sub(r'0x([0-9A-Fa-f]{2,2})*', r'\1', i["compression"])
		if "e_curves" in i:
			i["e_curves"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', i["e_curves"])
		if "sig_alg" in i:
			i["sig_alg"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', i["sig_alg"])
		if "ec_point_fmt" in i:
			i["ec_point_fmt"] = re.sub(r'0x([0-9A-Fa-f]{2,2})*', r'\1', i["ec_point_fmt"])


		# Print out the rules
		print "alert tcp any any -> any any (",
		print "msg:\""+i["desc"]+"\"; ",
		# Checks for "handshake" and "record TLS Version"
		print "content: \"|16 "+i["record_tls_version"]+"|\"; offset: 0; depth: 3; rawbytes; ",
		# Checks this is a client hello packet
		print "content: \"|01|\"; distance: 1; rawbytes; ",
		# Checks TLS Version (not record, the real one)
		print "content: \"|"+i["tls_version"]+"|\"; distance: 3; rawbytes; ",
		# Depending on which output was selected use a 0 sessionid length and offset (as there is none)
		if sys.argv[2] == 'idsinit':
			print "content: \"|00|\"; offset: 42; rawbytes; ",
		# Otherwise use byte_jump to jump the offset of the session_id to get to the ciphersuite section
		else:
			print "byte_jump: 1,43,align; ",
		# Lined back up now no matter which option was chosen
		print "content: \"|"+i["ciphersuite_length"]+"|\"; distance: 0; rawbytes; ",
		# CipherSuites
		print "content: \"|"+i["ciphersuite"]+"|\"; distance: 0; rawbytes; ",
		# Compression length and compression types concat'd
		print "content: \"|"+i["compression_length"]+" "+i["compression"]+"|\"; distance: 0; rawbytes; ",

		### Now we get to looping through the extensions and dealing with a few special cases where we are
		### looking at extension content, not just presence and order.

		first_ext = 0;
		# This feels like a fudge, but YOLO, it's forget finesse friday \o/ XXX
		special_ext = 0;
		if len(i["extensions"]) > 0:
			for x in i["extensions"].split(" "):
				# Reformat this extension to something snort-useful
				x = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\1 \2', x)
				if first_ext == 0:
					# First extension requires a "distance: 2;" to jump it past the "extensions length" field
					print "content: \"|"+x+"|\"; rawbytes; distance: 2; ",
					first_ext += 1
				else:
					if special_ext == 0:
						print "byte_jump: 2,0,relative; ",
					else:
						special_ext = 0;
					print "content: \"|"+x+"|\"; rawbytes; distance: 0; ",

				# Deal with the "special" extensions
				# XXX Should update this to include frontloading the lengths.... next
				# e_curves
				if x == "00 0A":
					special_ext = 1;
					ext_len = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\1', hex((len(i["e_curves"])+1)/3))
 					ext_len = re.sub(r'^([0-9A-Fa-f])$', r'0\1 ', ext_len)
					print "content: \"|"+ext_len+i["e_curves"]+"|\"; rawbytes; distance: 0; ",
				# sig_alg
				elif x == "00 0D":
					special_ext = 1;
					ext_len = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\1', hex((len(i["sig_alg"])+1)/3))
 					ext_len = re.sub(r'^([0-9A-Fa-f])$', r'0\1 ', ext_len)
					print "content: \"|"+i["sig_alg"]+"|\"; rawbytes; distance: 0; ",
				# ec_point_fmt
				elif x == "00 0B":
					special_ext = 1;
					ext_len = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\1', hex((len(i["ec_point_fmt"])+1)/3))
 					ext_len = re.sub(r'^([0-9A-Fa-f])$', r'0\1 ', ext_len)
					print "content: \"|"+i["ec_point_fmt"]+"|\"; rawbytes; distance: 0; ",


		print "sid:"+str(sid)+"; rev:1;)"
		sid += 1
		print "\n"


elif (sys.argv[2] == 'xkeyscore'):
	# This is my joke _joke_... ok?  JOKE!  xkeyscore (i.e. regex) exporter
	# offsets are poop in regex, don't actually use!

	# Oh python with your spaces!!!!
	output = ''
	for i in jfile:

		# Reformat some of the values prior to printing out rules
		i["record_tls_version"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', i["record_tls_version"])
		i["tls_version"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', i["tls_version"])
		i["ciphersuite_length"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', i["ciphersuite_length"])
		i["ciphersuite"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', i["ciphersuite"])
		i["compression_length"] = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\\x\1', hex(int(i["compression_length"])))
		i["compression_length"] = re.sub(r'^([0-9A-Fa-f])$', r'\\x\1', i["compression_length"])
		i["compression"] = re.sub(r'0x([0-9A-Fa-f]{2,2})*', r'\\x\1', i["compression"])
		if "e_curves" in i:
			i["e_curves"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', i["e_curves"])
		if "sig_alg" in i:
			i["sig_alg"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', i["sig_alg"])
		if "ec_point_fmt" in i:
			i["ec_point_fmt"] = re.sub(r'0x([0-9A-Fa-f]{2,2})*', r'\\x\1', i["ec_point_fmt"])


		# Print out the rules
		print "# Rule for \""+i["desc"]+"\""
		output = "\"\\x16"+i["record_tls_version"]
		output = output+".*\\x01.*"+i["tls_version"]
		output = output+".*"+i["ciphersuite_length"]+i["ciphersuite"]
		output = output+".*"+i["compression"]

		### Now we get to looping through the extensions and dealing with a few special cases where we are
		### looking at extension content, not just presence and order.
		first_ext = 0;
		# This feels like a fudge, but YOLO, it's forget finesse friday \o/ XXX
		special_ext = 0;
		if len(i["extensions"]) > 0:
			for x in i["extensions"].split(" "):
				# Reformat this extension to something regex-useful
				x = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'\\x\1\\x\2', x)
				if first_ext == 0:
					# First extension requires a "distance: 2;" to jump it past the "extensions length" field
					output = output+x
					first_ext += 1
				else:
					if special_ext != 0:
						special_ext = 0;
					output = output+x

				# Deal with the "special" extensions
				# XXX Should update this to include frontloading the lengths.... next
				# e_curves
				if x == "\\x00\\x0A":
					special_ext = 1;
					ext_len = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\\x\1', hex((len(i["e_curves"])+1)/3))
 					ext_len = re.sub(r'^\\x([0-9A-Fa-f])$', r'0\1', ext_len)
					output = output+ext_len+i["e_curves"]+".*"
				# sig_alg
				elif x == "\\x00\\x0D":
					special_ext = 1;
					ext_len = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\\x\1', hex((len(i["sig_alg"])+1)/3))
 					ext_len = re.sub(r'^\\x([0-9A-Fa-f])$', r'0\1', ext_len)
					output = output+i["sig_alg"]+".*"
				# ec_point_fmt
				elif x == "\\x00\\x0B":
					special_ext = 1;
					ext_len = re.sub(r'0x([0-9A-Fa-f]{1,2})', r'\\x\1', hex((len(i["ec_point_fmt"])+1)/3))
 					ext_len = re.sub(r'^\\x([0-9A-Fa-f])$', r'0\1', ext_len)
					output = output+i["ec_point_fmt"]+".*"


		output = output+"\""
		output = re.sub(' ', '', output)
		print output+"\n"



elif sys.argv[2] == 'struct':
	# Build struct array for use in peoples C
	# Not sorted or indexed or anything for speed, just a dump into an array... YOLO!

	# Work out longest length for string fields... awwwww yeah.. static struct joy
	desc_len = tls_version_len = ciphersuite_len = compression_len = 0
	extensions_len = e_curves_len = sig_alg_len = ec_point_fmt_len = server_name_len = 0
	record_tls_version_len = 0
	objcount = len(jfile)

	for i in jfile:
		# This isn't very neat or nice, buuuuuuut it's not super time critical either so it stays for now.
		# Neatening this little mess up though is on the todo list
		i["ciphersuite"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'0x\1,0x\2,', i["ciphersuite"])
		i["ciphersuite"] = re.sub(r'.$', r'', i["ciphersuite"])
		i["ciphersuite"] = re.sub(r' ', r'', i["ciphersuite"])
		i["extensions"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'0x\1,0x\2,', i["extensions"])
		i["extensions"] = re.sub(r'.$', r'', i["extensions"])
		i["extensions"] = re.sub(r' ', r'', i["extensions"])
		if "compression" in i:
			i["compression"] = re.sub(r'0x([0-9A-Fa-f]{2,2})*', r'0x\1,', i["compression"])
			i["compression"] = re.sub(r'.$', r'', i["compression"])
			i["compression"] = re.sub(r' ', r'', i["compression"])
		if "e_curves" in i:
			i["e_curves"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'0x\1,0x\2,', i["e_curves"])
			i["e_curves"] = re.sub(r'.$', r'', i["e_curves"])
			i["e_curves"] = re.sub(r' ', r'', i["e_curves"])
		# XXX Need more of this checking, didn't realise how badly python would barf
		if "sig_alg" in i:
			i["sig_alg"] = re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})*', r'0x\1,0x\2,', i["sig_alg"])
			i["sig_alg"] = re.sub(r'.$', r'', i["sig_alg"])
			i["sig_alg"] = re.sub(r' ', r'', i["sig_alg"])

		if "ec_point_fmt" in i:
			i["ec_point_fmt"] = re.sub(r'0x([0-9A-Fa-f]{2,2})*', r'0x\1,', i["ec_point_fmt"])
			i["ec_point_fmt"] = re.sub(r'.$', r'', i["ec_point_fmt"])
			i["ec_point_fmt"] = re.sub(r' ', r'', i["ec_point_fmt"])


		if desc_len < len(i["desc"]):
			desc_len = len(i["desc"]) + 1
		if record_tls_version_len < len(i["record_tls_version"]):
			record_tls_version_len = len(i["record_tls_version"]) + 1
		if tls_version_len < len(i["tls_version"]):
			tls_version_len = len(i["tls_version"]) + 1
		if ciphersuite_len < ((len(i["ciphersuite"])/7) * 2):
			ciphersuite_len = ((len(i["ciphersuite"])/7) * 2)
		if compression_len < len(i["compression"]):
			compression_len = len(i["compression"]) + 1
		if extensions_len < len(i["extensions"]):
			extensions_len = len(i["extensions"]) + 1
		if "e_curves" in i:
			if e_curves_len < len(i["e_curves"]):
				e_curves_len = len(i["e_curves"]) + 1
		if "sig_alg" in i:
			if sig_alg_len < len(i["sig_alg"]):
				sig_alg_len = len(i["sig_alg"]) +1
		if "ec_point_fmt" in i:
			if ec_point_fmt_len < len(i["ec_point_fmt"]):
				ec_point_fmt_len = len(i["ec_point_fmt"]) + 1
#		if server_name_len < len(i["server_name"]):
#			server_name_len = len(i["server_name"]) + 1

	# Print the struct layout so this can be one .c or something
	# Need to set more accurate size than "int" for the sizes
	print "struct fingerprint {"
	print "\tint id;"
	print "\tu_char desc["+str(desc_len)+"];"
	print "\tuint16_t record_tls_version;"
	print "\tuint16_t tls_version;"
	print "\tint ciphersuite_length;"
	print "\tuint8_t ciphersuite["+str(ciphersuite_len)+"];"
	print "\tint compression_length;"
	print "\tuint8_t compression["+str(compression_len)+"];"
	print "\tint extensions_length;"
	print "\tuint8_t extensions["+str(extensions_len)+"];"
	print "\tint e_curves_length;"
	print "\tuint8_t e_curves["+str(e_curves_len)+"];"
	print "\tint sig_alg_length;"
	print "\tuint8_t sig_alg["+str(sig_alg_len)+"];"
	print "\tint ec_point_fmt_length;"
	print "\tuint8_t ec_point_fmt["+str(ec_point_fmt_len)+"];"
	print "} fpdb["+str(objcount)+"] = {"

	# Pre-populate a bunch of C structs for people to use in their own Code
	# note: not ordered, indexed or in pretty trees; just at static struct array
	# enjoi the blazing performance ;)
	fp_count = 0
	for i in jfile:
		print "\t{"+str(i["id"])+", \""+i["desc"]+"\", "+i["record_tls_version"]+", "+i["tls_version"]+", ",
		print re.sub(r'0x([0-9A-Fa-f]{2,2})([0-9A-Fa-f]{2,2})$', r'0x\1\2', i["ciphersuite_length"])+", ",
		print "{"+i["ciphersuite"]+"}, "+str(i["compression_length"])+", {"+i["compression"]+"}, ",
		print str(i["extensions"].count('x'))+",",
		print "{"+i["extensions"]+"}",

		if "e_curves" in i:
			print ", "+str(i["e_curves"].count('x')),
			print ", {"+i["e_curves"]+"}",
		else:
			print ",0 , {}",
		if "sig_alg" in i:
			print ", "+str(i["sig_alg"].count('x')),
			print ", {"+i["sig_alg"]+"}",
		else:
			print ",0 , {}",
		if "ec_point_fmt" in i:
			print ", "+str(i["ec_point_fmt"].count('x')),
			print ", {"+i["ec_point_fmt"]+"}",
		else:
			print ",0 , {}",

		fp_count = fp_count + 1

		if fp_count < objcount:
			print "},"
		else:
			print "}"


	print "\t};"

else:
	print "Wat?  Don't understand: ", sys.argv[2]
