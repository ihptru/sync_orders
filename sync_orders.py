#-*- coding: utf-8 -*-
# Copyright 2013 ihptru (Igor Popov)
#
# This file is part of sync_orders, which is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This script is made to synchronize recursive file structure to a remote ftp server
# For Python2
# Tested on Linux and Windows
# Linux has issue with non-latin filenames (unicode)
# If it's run on Windows, make sure that AllowReplaceOnRename is true in Windows FTP client (which is false by default)

import ftputil
import time
import os

ftp_host = ""
ftp_login = ""
ftp_pass = ""

remote_path = ""  # must be just a single subdir on ftp server (without separator) in latin
local_path = "" # full path, last directory's name must match `remote_path`
log_filename = ""

def logging(line, log_filename):
	f = open(log_filename,'a')
	f.write(time.ctime() + "  ===  " + line + "\n")
	f.close()

#connect
try:
    host = ftputil.FTPHost(ftp_host, ftp_login, ftp_pass)
    logging("Connected to " + ftp_host, log_filename)
except:
	ll = "Failed to connect to " + ftp_host
	print(ll)
	logging(ll, log_filename)

# walk through server
remote_structure = host.walk(remote_path)
remote_structureList = []
for line in remote_structure:
    remote_structureList.append(line)

# get local file structure
fileList = []
for root, subFolders, files in os.walk(local_path):
    for file in files:
        fileList.append(os.path.join(root,file))

# walk through local file structure, compare with server and perform proper action
for ff_name in fileList:
    local_filename = remote_path + ff_name.split(local_path)[1] #full path (relative)
    local_dirname = os.path.dirname(local_filename) #dir path
    local_dest_filename = os.path.basename(local_filename)  #destination name
    dirFound = 0   # if dir is not found, we create a new directory structure recursively and put file in there
                            # if it's found, we check if file exists in there... if not, we upload it
                            # if it exists in there, we check if it's newer... if so, we upload it too
    for remote_line in remote_structureList:
        if remote_line[0] == local_dirname:
            dirFound = 1    #dir is found
            if local_dest_filename in remote_line[2]:
                host.synchronize_times()
                if host.upload_if_newer(ff_name, local_filename, mode='', callback=None):
                    logging("Re-uploaded file `"+local_dest_filename+"` into `"+local_dirname+"`, remote server had older version.", log_filename)
            else:
                host.upload(ff_name, local_filename, mode='', callback=None)
                logging("Uploaded file `"+local_dest_filename+"` into `"+local_dirname+"`, directory existed.", log_filename)
            break
    if dirFound == 0:
        host.makedirs(local_dirname)
        host.upload(ff_name, local_filename, mode='', callback=None)
        logging("Created directory `"+local_dirname+"` and upload file `"+local_dest_filename+"` in there.", log_filename)

host.close()
print("done")
