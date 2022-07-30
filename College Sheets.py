import string
from oauth2client.service_account import ServiceAccountCredentials 
import gspread
import requests
import json
import pandas as pd
import re
import sys
from xlsxwriter.utility import xl_rowcol_to_cell


"""
TO DO:
    - Use sequencematcher to check closeness of user attributes to the key maybe?
    - Add custom attributes to the Google Sheets Dictionary of API keys and add a method to use it in the code 
    - Make some dictionary data names simpler or add an alternative 
    - Education Data Finance DOESN'T WORK for 2018+

    - Could add it so that you get the attributes and college names from a given list or sheet and then create a new one and share it with them.

NOTES:
    - Same Variables/Filters across all Education Data categories is Unitid, year, fips
    - Going to skip Enrollment at this time since it has too much stuff, can work on it later, and no one would probably use it and its hard to detect in attributes
    - For the Education Data API add a "&fields=DESIRED FIELDS" at the end to get only specific ones

    - SERVICE ACCOUNT EMAIL = collegeinfofiller@appspot.gserviceaccount.com
    - IN FIRST COLUMN AND ROW(THE ATTRIBUTES AND NAMES OF COLLEGES) PUT A * IN FRONT OF CELLS THAT ARE JUST NOTES AND NOT MEANT TO HAVE INFO RETRIEVED
    - USE (), [], OR {} FOR NOTES IN THE FIRST COLUMN AND ROWS AS NOTES SO THEY ARE NOT CONSIDERED 
    - ALL SPECIAL CHARACTERS EXCEPT "-" WILL NOT BE CONSIDERED (some colleges have "-" in the name)

"""








""" Variables """


CollegeScorecardpathbase = "https://api.data.gov/ed/collegescorecard/v1/schools.json?"

CollegeScorecardapi_key = "&api_key=Qdls4gd3XlUW5de58tGneppDllpWb9bveoNADwyF"

format = "https://api.data.gov/ed/collegescorecard/v1/schools.json?SEARCH FIELD&fields=FIELDS DISPLAYED&api_key=APIKEY"
example = "https://api.data.gov/ed/collegescorecard/v1/schools.json?school.degrees_awarded.predominant=2,3&fields=id,school.name,2013.student.size"




EducationDatapathbase = "https://educationdata.urban.org/api/v1/college-university/ipeds/"



""" Setup """


scopes = [
'https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive'
]

credentials = ServiceAccountCredentials.from_json_keyfile_name("ServiceAccID.json", scopes) 
file = gspread.authorize(credentials) 

def openSheets(link):
    sheet = file.open_by_url(link)  
    return sheet



""" Get Sheet to Edit/Fill """

EditSheetURL = "https://docs.google.com/spreadsheets/d/1o5D9lWDEz_L4VYR5ddJpzvQcXyESkGdDLzVg36YNdy4/edit#gid=0"#input("Enter the link to the sheet that you would like to fill in using College Sheets: ")
EditSheet = file.open_by_url(EditSheetURL)
worksheet = EditSheet.get_worksheet(0)  
#Could add a way to choose which sheet here instead of automatically getting the first sheet



""" Get College Names and Desired Attributes """


row1 = worksheet.row_values(1)
column1 = worksheet.col_values(1)

row1.pop(0)
column1.pop(0)

attributes = row1
collegenames = column1



""" Remove Notes (things in Parenthesiss)"""

for List in (attributes,collegenames): #Does it twice for both the attributes and collegenames
    for location in range(len(List)):
        attribute = List[location].strip()
        if attribute == '':
            pass
        elif attribute[0] == '*':
            List[location]= ''
        else:
            #Removes things in parenthases as notes
            openParenthesis = attribute.find("(")
            closeParenthesis = attribute.find(")")
            if openParenthesis != -1 and closeParenthesis != -1 and openParenthesis<closeParenthesis:
                List[location] = attribute.replace(attribute[openParenthesis:closeParenthesis+1], "").strip()

            #repeats for brackets and curly braces
            openBracket = attribute.find("[")
            closeBracket = attribute.find("]")
            if openBracket != -1 and closeBracket != -1 and openBracket<closeBracket:
                List[location] = attribute.replace(attribute[openBracket:closeBracket+1], "").strip()

            openCurlyBrace = attribute.find("{")
            closeCurlyBrace = attribute.find("}")
            if openCurlyBrace != -1 and closeCurlyBrace != -1 and openCurlyBrace<closeCurlyBrace:
                List[location] = attribute.replace(attribute[openCurlyBrace:closeCurlyBrace+1], "").strip()

            #Removes all special characters (things that aren't letters and numbers except periods) so it doesn't mess with api info
            List[location] = ''.join(char for char in attribute if char.isalnum() or char in ['.',' ','_',','])

        

    

""" Check which attributes are in the Dictionaries """



#Excel with all of the dictionaries for the APIs
ExcelDictionaries = pd.ExcelFile('College Sheets Key.xlsx')





#College Scorecard 
Scorecard_Dictionary = pd.read_excel(ExcelDictionaries,sheet_name='College Scorecard')
Scorecard_NameOfData = Scorecard_Dictionary['NAME OF DATA ELEMENT']
Scorecard_DevCategory = Scorecard_Dictionary['dev-category']
Scorecard_DataVariables = Scorecard_Dictionary['developer-friendly name']
Scorecard_VariableNames = Scorecard_Dictionary['VARIABLE NAME']
Scorecard_Values = Scorecard_Dictionary['VALUE']
Scorecard_Labels = Scorecard_Dictionary['LABEL']


def CheckScorecardKeys(attribute):
    for column in [Scorecard_NameOfData,Scorecard_VariableNames,Scorecard_DataVariables]:
        for counter in range(len(column)):  
            value = column[counter]
            if  pd.notna(value) and attribute.casefold().strip() == str(value).casefold().strip():
                if Scorecard_DevCategory[counter] == 'root':
                    return Scorecard_DataVariables[counter]
                else:
                    return "latest"+"."+Scorecard_DevCategory[counter]+"."+Scorecard_DataVariables[counter]



#Education Data 
EducationData_VariableSheets = {}
for name in ExcelDictionaries.sheet_names:
    if "variables" in name and '*' not in name:
        sheet = pd.read_excel(ExcelDictionaries,sheet_name=name)
        EducationData_VariableSheets[name] = {'variableNames': sheet['variable'],'labels': sheet['label']} 



def CheckEducationDataKeys(attribute):
    for title in EducationData_VariableSheets:    
        for column in EducationData_VariableSheets[title].values():
            for counter in range(len(column)):  
                value = column[counter]
                if attribute.casefold().strip() == value.casefold().strip(): 
                    return title[:-10],EducationData_VariableSheets[title]['variableNames'][counter] #RETURNS THE SOURCE(removes the "variables" part of the title, so it can now be directly put into the API request) AND THE VARIABLE NAME to add in the "&fields=..."
                value = re.sub("[^a-zA-Z0-9\n]", ' ', value)
                if attribute.casefold().strip() == value.casefold().strip():
                    return title[:-10],EducationData_VariableSheets[title]['variableNames'][counter]



#Custom Attributes
CustomAttributes = pd.read_excel(ExcelDictionaries,sheet_name='Custom Attributes')
CustomAttributeAPIs = CustomAttributes['API']
CustomAttributeNames = CustomAttributes['Attribute Name']
CustomAttributeVariables = CustomAttributes['Variable']
CustomAttributeDirectories = CustomAttributes['Directory']

def CheckCustomAttributes(attribute):
    for counter in range(len(CustomAttributeNames)):
        value = CustomAttributeNames[counter]
        if attribute.casefold().strip() == value.casefold().strip():
            if CustomAttributeAPIs[counter] == 'College Scorecard':
                return CustomAttributeVariables[counter]
            elif CustomAttributeAPIs[counter] == 'Education Data':
                return CustomAttributeDirectories[counter],CustomAttributeVariables[counter]






#CHECKS IF THE USER INPUT ATTRIBUTES ARE IN THE DICTIONARIES AND ADDS THEM TO 'fields'
fields = {'College Scorecard': [], 'Education Data': {}}
for attribute in attributes:
    if attribute != "":

        #Checks if the attribute is in the "Custom Attributes" sheet
        CAtest = CheckCustomAttributes(attribute)
        if CAtest:
            if type(CAtest) == str:
                attributes[attributes.index(attribute)] = CAtest
                fields["College Scorecard"].append(CAtest)
                continue
            elif type(CAtest) == list and len(CAtest) == 2:
                CAsource,CAvariable = CAtest[0],CAtest[1]
                if CAsource in fields["Education Data"]:
                    fields["Education Data"][CAsource].append(CAvariable)
                else:
                    fields["Education Data"][CAsource] = [CAvariable]
                attributes[attributes.index(attribute)] = CAvariable    
                continue

        #Checks if the attribute is in College Scorecard: "Names of Data", "Variable Name", and "Developer-Friendly Name"
        CStest = CheckScorecardKeys(attribute) 
        if CStest:
            attributes[attributes.index(attribute)] = CStest
            fields["College Scorecard"].append(CStest)
            continue



        #Checks if the attribute is in Education Data
        EDtest = CheckEducationDataKeys(attribute)
        if EDtest:
            EDsource,EDvariable = EDtest[0],EDtest[1]
            if EDsource in fields["Education Data"]:
                fields["Education Data"][EDsource].append(EDvariable)
            else:
                fields["Education Data"][EDsource] = [EDvariable]
            attributes[attributes.index(attribute)] = EDvariable    
            continue
            
        

        #If it isn't in either of the above, that attribute is set to ""

        attributes[attributes.index(attribute)] = ""






""" Checks Scorecard Fields """




ScorecardFields = ",".join(fields["College Scorecard"])
if ScorecardFields:
    #PUTS IN FIELDS TO SEE WHICH ONES ARE VALID
    response = requests.get(CollegeScorecardpathbase+"school.operating=1&fields="+ScorecardFields+CollegeScorecardapi_key)
    results = response.json()
    if 'errors' in results or 'error' in results:
        print("SOMETHING WENT WRONG")
        print(results)
        sys.exit()
    #Takes the valid fields and puts it in a list which is then turned into a string
    ScorecardFields = []
    for field in results['results'][0]:
        ScorecardFields.append(field)
    fields["College Scorecard"] = ScorecardFields
    ScorecardFields = ','+','.join(ScorecardFields) #ScorecardFields is now a string of attributes to put into the API, NOT A LIST!!! fields still has the list of attributes


print(fields)








""" Fill in Full college names for college aliases """


CollegeAliasesDictionary = pd.read_excel(ExcelDictionaries,sheet_name='College Aliases')
CollegeAliases = CollegeAliasesDictionary['Aliases']
CollegeFullNames = CollegeAliasesDictionary['Full Names']

for name in collegenames:
    for counter in range(len(CollegeAliases)):
        alias = CollegeAliases[counter]
        if pd.notna(alias):
            if name.casefold().strip() == alias.casefold().strip():
                collegenames[collegenames.index(name)] = CollegeFullNames[counter]






""" Get data from College Scorecard API """


collegeinfo = [] #List of lists which will be used to update the google sheets - Each inner list is the values of a row 
for name in collegenames:
    if name != '':


        """ COLLEGE SCORECARD"""
        
        
        CSresponse = requests.get(CollegeScorecardpathbase+"school.operating=1&school.name="+name+"&fields=id"+ScorecardFields+CollegeScorecardapi_key)
        CSresults = CSresponse.json()
        
        #Checks to see if the result is qualified to be put into the spreadsheet
        if 'errors' in CSresults or 'error' in CSresults:
            print("SOMETHING WENT WRONG")
            print(CSresults)
            sys.exit()
        elif CSresults['metadata']['total'] > 1:
            row = collegenames.index(name)+2
            column = 1
            worksheet.update_cell(row, column, column1[row-2] + ' [NOTE: ?]') #"?" MEANS THAT THE PROGRAM DID NOT FIND ANY COLLEGES UNDER THIS NAME
            continue
        elif CSresults['metadata']['total'] == 0:
            row = collegenames.index(name)+2
            column = 1
            worksheet.update_cell(row, column, column1[row-2] + ' [NOTE: ~]')#"~" MEANS THAT THE PROGRAM FOUND MORE THAN 1 COLLEGE UNDER THIS NAME
            continue
        elif CSresults['metadata']['total'] == 1:


            """ EDUCATION DATA"""


            unitid = str(CSresults['results'][0]['id'])
            ED_Data = {}
            for directory in fields['Education Data']:
                EducationDataFields = ','.join(fields['Education Data'][directory])
                print(directory,EducationDataFields)
                EDresponse = requests.get(EducationDatapathbase+directory+'/2020/?unitid='+unitid+'&fields='+EducationDataFields)
                EDresults = EDresponse.json()
                print(EDresults)
                ED_Data.update(EDresults['results'][0])


            #ADD EVERYTHING TO THE LIST FOR THE ROW
            rowInfo = []
            for attribute in attributes:
                if attribute != '':
                    if attribute in CSresults['results'][0]:
                        rowInfo.append(CSresults['results'][0][attribute])
                    elif attribute in ED_Data:
                        rowInfo.append(ED_Data[attribute])
                else:
                    rowInfo.append('') #Should we have it so that it deletes whatever was there('')? or have it leave what might be there but most likely not(None)
                
            collegeinfo.append(rowInfo)
            

    else:
        collegeinfo.append([])

worksheet.update('B2:'+xl_rowcol_to_cell(len(column1),len(row1)),collegeinfo)