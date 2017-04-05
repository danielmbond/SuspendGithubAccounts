#Requires ldap3: pip install ldap3
#Curl must be installed and you need to set the curlexe variable.

import requests
import getpass
import ssl
import csv
import os
from time import sleep
from ldap3 import Server, Connection, ALL, NTLM
import sys

# Configure the next 4 lines
curlexe = "c:/Progra~1/Git/usr/bin/curl.exe"
adDomain = "foo.com"
githubURL = "https://github.foo.com"
ldapServer = "ldap.foo.com"

searchDomain = 'DC=' + adDomain.split(".")[-2] + ',DC=' + adDomain.split(".")[-1]
githubUserApi = githubURL + "/api/v3/users/"
githubUserList = githubURL + "/stafftools/reports/all_users.csv"
adDisabledUsers = []

if sys.version_info[0] < 3:
    raise "Must be using Python 3"

username = input("Username: ")
mypass = getpass.getpass()

curlopts = curlexe + " -u " + username + ":" + mypass + " " + githubUserList + " -k -L > gitusers.csv"
os.system(curlopts)

server = Server(ldapServer, use_ssl=True)

domainuser = adDomain.split(".")[-2] + "\\" + username
conn = Connection(server, user=domainuser, password=mypass, auto_bind=True)

#print(conn)
print("Reading Github user accounts.")
with open('gitusers.csv', newline='') as f:
    reader = csv.reader(f)
    print("Checking AD for disabled accounts.")
    for row in reader:
        if row[5] == 'false':
            sam = "(SamAccountName=" + row[2] + ")"
            adDetails = conn.search(searchDomain, sam, attributes=['useraccountcontrol'])
            if len(conn.entries) > 0 and conn.entries[0].useraccountcontrol == 514:
                print(row[2], "is disabled in AD.")
                adDisabledUsers.append(row[2])

if len(adDisabledUsers) > 0:
    print("\n\nEnter \"Y\" to disable the below accounts")
    print(adDisabledUsers)
    if input().lower() == "y":
        for user in adDisabledUsers:
            print("Suspending ", user)
            url = githubUserApi + user + "/suspended"
            print(url)
            response = requests.put(url, auth=requests.auth.HTTPBasicAuth(username,mypass), verify=False)
    else:
        print("Suspend aborted.")
else:
    print('There are no inactive AD accounts in Github.')
