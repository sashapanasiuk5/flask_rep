import json
import requests
import pprint
from datetime import datetime, timedelta
import math
import re


def selectData(object):
    items = object['results']
    data = list()
    for item in items:
        id = item['id']
        periodicity = item['properties']['Periodicity']['multi_select']
        set_date = item['properties']['Set date']['date']
        due_date = item['properties']['Due Date']['date']
        object = {
            'id':id,
            'periodicity':periodicity,
            'set_date':set_date,
            'due_date':due_date
        }
        data.append(object)
    return data

def getDatabase(id, key):
    headers = {
                'accept': 'application/json',
                'Authorization': 'Bearer '+key,
               'Notion-Version': '2022-06-28',
               }
    payload = {"page_size": 100,
               "filter":{
                   "and":[
                       {
                           "property": "Status",
                           "select": {
                               "equals": "DONE"
                           }
                       },{
                           "property":"Periodicity",
                           "multi_select":{
                               "does_not_contain":"On demand"
                           }
                       },{
                           "property": "Periodicity",
                           "multi_select": {
                               "is_not_empty": True
                           }
                       }]
                    }
               }
    url = 'https://api.notion.com/v1/databases/'+id+'/query'

    response = requests.post(url,json=payload, headers=headers)

    return json.loads(response.text)

def getPeriodicity(peridocity_select):
  for select in peridocity_select:
    have_periodicity = re.search("\dt\/", select['name']);
    
    if have_periodicity:
      result = select['name']
    elif select['name'] == "Daily":
      result = "Daily"
  return result
def parsePeriodicity(peridocity):

    times = peridocity[0]
    if times == 'D':
        return "Daily"
    else:
        times = int(times)
        if peridocity[3].isalpha():
            number_of_periods = 1
            period = peridocity[3]

        else:
            number_of_periods = int(peridocity[3])
            period = peridocity[4]
        return times, number_of_periods, period


def calculateTaskTimeToPerform(num_of_periods, period):
  if period == "w":
    return timedelta(days=1)
  else:
    if num_of_periods > 1:
      return timedelta(days=14)
    else:
      return timedelta(days=7)



def getNextDueDate(times, num_of_periods, period, currentDate, prevDueDate):
    days = (7*num_of_periods,30*num_of_periods)[period == 'm']    
    days_in_interval = math.floor(days / times)

    intervals = list([0]*times)
    t=0
    nextDueDate = prevDueDate

    for i in range(times):
        t += days_in_interval
        intervals[i]=t

    
    tasktime = calculateTaskTimeToPerform(num_of_periods, period)
    
    while (nextDueDate - currentDate) <= tasktime :
      nextDueDate += timedelta(days=days_in_interval)
      
    return nextDueDate
        
    
def UpdateTask(id, props, key):
  headers = {
                'accept': 'application/json',
                'Authorization': 'Bearer '+key,
               'Notion-Version': '2022-06-28',
               }
  data = {
    "properties":props
  }

  url = 'https://api.notion.com/v1/pages/'+id

  response = requests.patch(url,json=data, headers=headers)
  

if __name__ == '__main__':
    file = open("config.json", "r")
    config = json.loads(file.read())
    file.close()
    key = config['key']
    db_id = config['database_id']
    records = getDatabase(db_id, key)
    tasks = selectData(records)

    #time = datetime.datetime.strptime('2020-12-16', "%Y-%m-%d")
    currentDate = datetime.today()
    updateData = list()
    for task in tasks:
      prevDueDate = datetime.strptime(task['due_date']['start'], "%Y-%m-%d")
      periodicity_string = getPeriodicity(task["periodicity"])
      
      if periodicity_string == "Daily":
        nextDueDate = currentDate.strftime("%Y-%m-%d")
        setDate = nextDueDate
      else:
        times, number_of_periods, period = parsePeriodicity(periodicity_string)
        nextDueDate = getNextDueDate(times, number_of_periods, period,currentDate, prevDueDate)
        setDate = (nextDueDate-calculateTaskTimeToPerform(number_of_periods, period)).strftime("%Y-%m-%d")
        nextDueDate = nextDueDate.strftime("%Y-%m-%d")

     
      taskProperties = {
          "Due Date":{
            "date":{
              "start":nextDueDate
            }
          },
          "Set date":{
            "date":{
                "start":setDate
            }
          },
          "Status":{
            "select":{
              "name":"DONE"
            }
          }
      }
      if setDate == currentDate.strftime("%Y-%m-%d"):
        taskProperties['Status']["select"]["name"] = "TO DO"

      UpdateTask(task['id'], taskProperties, key)
   