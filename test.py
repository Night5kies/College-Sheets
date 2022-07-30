from oauth2client.service_account import ServiceAccountCredentials
import gspread
import requests
import json
import pandas as pd
import numpy as np
import re
import sys

scopes = [
'https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive'
]
credentials = ServiceAccountCredentials.from_json_keyfile_name("ServiceAccID.json", scopes) 
file = gspread.authorize(credentials) 
sheet = file.open_by_url("https://docs.google.com/spreadsheets/d/1o5D9lWDEz_L4VYR5ddJpzvQcXyESkGdDLzVg36YNdy4/edit#gid=0")#.open("Kevin college comparison")  
worksheet = sheet.get_worksheet(0)  


"""response = requests.get("https://api.data.gov/ed/collegescorecard/v1/schools.json?school.name=Harvard&fields=latest.school.zip&api_key=Qdls4gd3XlUW5de58tGneppDllpWb9bveoNADwyF")

#response = requests.get("https://educationdata.urban.org/api/v1/college-university/ipeds/directory/2020/?unitid=166027&fields=address")
data = response.text 
results = json.loads(data)
print(results)
"""

names = ['College Aliases', 'Custom Attributes', 'College Scorecard', 'directory variables', 'directory values', 'institutional-characteristics variables', 'institutional-characteristics values', 'admissions-enrollment variables', 'admissions-enrollment values', 'admissions-requirements variables', 'admissions-requirements values', 'academic-year-tuition variables', 'academic-year-tuition values', 'academic-year-tuition-prof-program variables', 'academic-year-tuition-prof-program values', 'academic-year-room-board-other variables', 'academic-year-room-board-other values', 'program-year-tuition-cip variables', 'program-year-tuition-cip values', 'program-year-room-board-other variables', 'program-year-room-board-other values', '*enrollment-full-time-equivalent variables', '*enrollment-full-time-equivalent values', '*fall-enrollment variables 1', '*fall-enrollment values 1', '*fall-enrollment variables 2', '*fall-enrollment values 2', '*fall-enrollment variables 3', '*fall-enrollment values 3', '*enrollment-headcount variables', '*enrollment-headcount values', 'fall-retention variables', 'fall-retention values', 'finance variables', 'finance values', 'student-faculty-ratio variables', 'student-faculty-ratio values', 'sfa-grants-and-net-price variables', 'sfa-grants-and-net-price values', 'sfa-by-living-arrangement variables', 'sfa-by-living-arrangement values', 'sfa-by-tuition-type variables', 'sfa-by-tuition-type values', 'sfa-all-undergraduates variables', 'sfa-all-undergraduates values', 'sfa-ftft variables', 'sfa-ftft values', 'grad-rates variables', 'grad-rates values', 'grad-rates-200pct variables', 'grad-rates-200pct values', 'grad-rates-pell variables', 'grad-rates-pell values', 'outcome-measures variables', 'outcome-measures values', 'completers variables', 'completers values', 'completions-cip-2 variables', 'completions-cip-2 values', 'completions-cip-6 variables', 'completions-cip-6 values', 'academic-libraries variables', 'academic-libraries values', 'salaries-instructional-staff variables', 'salaries-instructional-staff values', 'salaries-noninstructional-staff variables', 'salaries-noninstructional-staff values']


ExcelDictionaries = pd.ExcelFile('College Sheets Key.xlsx')

CollegeScorecardpathbase = "https://api.data.gov/ed/collegescorecard/v1/schools.json?"
CollegeScorecardapi_key = "&api_key=Qdls4gd3XlUW5de58tGneppDllpWb9bveoNADwyF"

EducationDatapathbase = "https://educationdata.urban.org/api/v1/college-university/ipeds/"

fields= {'College Scorecard': ['latest.school.city', 'latest.school.state', 'latest.admissions.admission_rate.overall', 'id'], 'Education Data': {'student-faculty-ratio': ['student_faculty_ratio', 'student_faculty_ratio'], 'sfa-grants-and-net-price': ['average_grant', 'average_grant']}}

unitid = '166027'
ED_Data = {}
for directory in fields['Education Data']:
    EducationDataFields = ','.join(fields['Education Data'][directory])
    string = (EducationDatapathbase+directory+'/2020/?unitid='+unitid+'&fields='+EducationDataFields)
    print(string)
    EDresponse = requests.get(string)
    EDresults = EDresponse.json()
    ED_Data.update(EDresults['results'][0])



