from distutils import errors
from unittest import result
from matplotlib.pyplot import close
import requests
import json
import os.path
import math

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError




#NOT USING THIS ONE



""" Google Sheets API """

SCOPES = ['https://www.googleapis.com/auth/drive.file']
#SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
spreadsheet = "https://docs.google.com/spreadsheets/d/1mMdL5CWwi7Ms5PA_6Gb_p1ZurBNXqyvzLQDMwYGRpk4/edit#gid=0"#input("Enter your google spreadsheet url: ")

#get ID out of url
templen = len("https://docs.google.com/spreadsheets/d/")
if spreadsheet[:templen] == "https://docs.google.com/spreadsheets/d/":
    sheetsID = spreadsheet[templen:spreadsheet.rfind("/")]



""" College Scorecard API """

pathbase = "https://api.data.gov/ed/collegescorecard/v1/schools.json?"

api_key = "&api_key=Qdls4gd3XlUW5de58tGneppDllpWb9bveoNADwyF"

format = "https://api.data.gov/ed/collegescorecard/v1/schools.json?SEARCH FIELD&FIELDS DISPLAYED&api_key=APIKEY"
example = "https://api.data.gov/ed/collegescorecard/v1/schools.json?school.degrees_awarded.predominant=2,3&fields=id,school.name,2013.student.size"


""" Make Dictionary of College names to their Aliases"""

def find_aliases(): # Not using 
    response = requests.get(pathbase+"school.name="+"Caltech"+"&school.operating=1"+"&fields="+"school.name,school.alias&per_page=100"+api_key)#"school.operating="+"1"+"&fields="+"school.name,school.alias&per_page=100"+api_key)
    data = json.loads(response.text)
    if "errors" in data:
        print(data["errors"])
    elif"error" in data:
        print(data["error"])
    else:
        print(data)
    """else:
        #print(data)
        #Dictionary of aliases to names = (alias(key), name(pair))
        aliasList = {}
        for school in data["results"]:
            if school["school.alias"] != None:
                aliasList[school["school.name"]] = school["school.alias"]

        print(aliasList)

        total = float(data["metadata"]["total"])
        pages = math.ceil(total/float(data["metadata"]["per_page"]))
        print(pages)
        #for page in range(1,int(pages)):
            #response = requests.get(pathbase+"school.operating="+"1"+"&fields="+"school.name,school.alias&per_page=100&page="+str(page)+api_key)"""


""" Google Sheets API Setup """

def main():

    """ Credentials """

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    """ Getting Values """

    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheetsID,range='B1:1').execute()
        attributes = result.get('values',[])[0]

        result = sheet.values().get(spreadsheetId=sheetsID,range='A2:A',majorDimension='COLUMNS').execute()
        collegenames = result.get('values',[])[0]

        testinput = [["b","wow"],["this","a"]]
        sheet.values().update(spreadsheetId=sheetsID, range = "2B:3C", body=testinput).execute()


        if not attributes or not collegenames:
            print("No data found.")
            return
        


    except HttpError as err:
        print(err)
        return


    """ Remove Notes (things in Parentheses)"""
    for list in (attributes,collegenames): #Does it twice for both the attributes and collegenames
        for location in range(len(list)):
            attribute = list[location]
            openParenthese = attribute.find("(")
            closeParenthese = attribute.find(")")
            if openParenthese != -1 and closeParenthese != -1 and openParenthese<closeParenthese:
                list[location] = attribute.replace(attribute[openParenthese:closeParenthese+1], " ").strip()

        
    #print(collegenames)
    #print(attributes)

    
    #For getting the data to fill in the google sheets, do each attribute and go through each college (takes longer but allows us to see if an attribute is wrong with an error)
  
    """ Check attributes are in the list of keys for College Scorecard """

    attribute_list = {"test key": "test value"}
    #attributes = ["test key","test placeholder"]
    values = attribute_list.values()
    for counter in range(len(attributes)):
        if attributes[counter] in values:
            pass
        elif attributes[counter] in attribute_list:
            attributes[counter] = attribute_list[attributes[counter]]
        else:
            attributes[counter] = None
    #print(attributes)

    

    """ Get data from College Scorecard API """

    collegesinfo = []
    #for name in collegenames:
        #response = requests.get(pathbase+"school.operating=1&school.name="+name+"&fields="+"school.name,school.alias"+api_key)
        #data = response.text
        #print(data)





if __name__ == '__main__':
    main()