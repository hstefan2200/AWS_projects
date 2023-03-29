import sys, boto3, os, json
from pathlib import Path
from boto3.dynamodb.conditions import Key

def create_table(t_name, project_name, project_version):
    """Creates table """
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.create_table(
        TableName = t_name, #define table name
        KeySchema = [
                { #define key schema
                    'AttributeName': project_name,
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'Version',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions = [
                { #define attribute for key schema
                    'AttributeName': project_name,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'Version',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput = { #set throttling thresholds
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
    print("Table status:", table.table_status)
    
#Put 10 items into Courses table, each item must have all attributes
def put_items(table_name, name, bucket_name, version, f_name, date):
    """inserts data into table item """
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.Table(table_name) #set table
    #need:
    #class vars: table_name, name, bucket_name, version,
    #extras: f_name(function var), datetime(function var), folders, notes, bucket_URI??
    tree = [x for x in os.walk(f_name)]
    file_ends = [] #folders
    for dir in tree:
        path = dir[0]
        files = dir[2]
        for file in files:
            filepath = path+'/'+file
            file_ends.append(filepath)
    notes = input("If you would like to add a description, please add it here:\n") #notes
    project_name = name
    project_version = version
    table.put_item(Item={ #put_item() method for each attribute in each item
        project_name: name,
        'Version': version,
        'Bucket': bucket_name,
        'Creation_Date': date,
        'Files': file_ends,
        'Notes': notes
    })

def put_new_version(table_name, name, bucket_name, version, file_list, date):
    """new item in table for new version """
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.Table(table_name) #set table
    notes = input("If you would like to add a description, please add it here:\n") #notes
    project_name = name
    project_version = version
    changes_list = []
    change_notes = []
    table.put_item(Item={ #put_item() method for each attribute in each item
        project_name: name,
        'Version': version,
        'Bucket': bucket_name,
        'Creation_Date': date,
        'Files': file_list,
        'Notes': notes,
        'Changes': changes_list,
        'Change_Notes': change_notes
    })    

#add changes attribute to table item
def changes_tracking(table_name, name, version, file_changed, notes):
    """appends files, changes, and notes attributes when files are uploaded """
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.Table(table_name) #set table
    project_name = name
    change_notes = notes
    response = table.update_item(
    Key={
        project_name: name,
        'Version': version
    },
    UpdateExpression="SET Changes = list_append(Changes, :new_change), Change_Notes = list_append(Change_Notes, :file_notes), Files = list_append(Files, :new_change)",
    ExpressionAttributeValues={
        ':new_change': [file_changed],
        ':file_notes': [change_notes]
    },
    )

def repo_summary(table_name, project_name, version):
    """get summary of repo based on data in item """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.get_item(
    Key={
        project_name: project_name,
        'Version': version
    }
    )
    repo_sum = response['Item']
    file_list = repo_sum['Files']
    if 'Change_Notes' in repo_sum:
        changes_list = repo_sum['Change_Notes']
    print(f"Name: {project_name}\nVersion: {repo_sum['Version']}\nBucket: {repo_sum['Bucket']}")
    print("\nFiles in repository:")
    for file in file_list:
        print(file)
    if 'Change_Notes' in repo_sum:
        print("\nChanged files and notes:")
        for change in changes_list:
            print(change)
        