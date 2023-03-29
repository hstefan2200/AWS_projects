"""CLI Menu for interacting with DynamoDB via AWS SDK"""
import sys
import boto3
from boto3.dynamodb.conditions import Key

#Create "Courses Table": CourseID(HASH), Subject, CatalogNbr, Title
def create_table(t_name, key_name):
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.create_table(
        TableName = t_name, #define table name
        KeySchema = [
                { #define key schema
                'AttributeName': key_name,
                'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions = [
                { #define attribute for key schema
                    'AttributeName': key_name,
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
def put_items(t_name):
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.Table(t_name) #set table
    item_list = []
    for i in range(10): #iterate over 4 attribute input questions
        while 1: 
            c_id = input("Please enter Course ID (ie: '6980'):\n")
            if not c_id:
                continue
            break
        while 1:
            subject = input("Please enter Subject (ie: 'SDEV'):\n")
            if not subject:
                continue
            break
        while 1:
            cat_nbr = input("Please enter Catalog Number (ie: '400'):\n")
            if not cat_nbr:
                continue
            break
        while 1:
            title = input("Please enter Title (ie: Secure Programming in the Cloud):\n")
            if not title:
                continue
            break
        ind_item = [c_id, subject, cat_nbr, title] #create list for individual course item
        item_list.append(ind_item) #append each item to list of items
    for item in item_list: #iterate over nested list, assign attributes based on index
        course_id = item[0]
        subject = item[1]
        cat_nbr = item[2]
        title = item[3]
        table.put_item(Item={ #put_item() method for each attribute in each item
            'CourseID': course_id,
            'Subject': subject.upper(),
            'CatalogNbr': cat_nbr,
            'Title': title
        })
    print(f"Added 10 items to table {t_name}")
    
#create a secondary index to search by non-key attributes
def create_sec_index():
    dynamodb = boto3.client('dynamodb') #set client
    response = dynamodb.update_table(
        AttributeDefinitions = [ #define attributes to use as secondary keys
            {
                'AttributeName': 'Subject',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'CatalogNbr',
                'AttributeType': 'S'
            },
            ],
        TableName='Courses',
        GlobalSecondaryIndexUpdates = [{
            'Create': { #create secondary index
                'IndexName': 'SubNbr',
                'KeySchema': [
                    {
                        'AttributeName': 'Subject',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'CatalogNbr',
                        'KeyType': 'RANGE'
                    },
                    ],
                    'Projection': { #project all attributes in this index (need to be able to search for other attributes)
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }}
            },
            ]
        )
    print("Created secondary index")
        
#CLI Menu to: Search for Subject & CatalogNbr ->return Title
def course_search(t_name):
    dynamodb = boto3.resource('dynamodb') #set resource
    table = dynamodb.Table(t_name) #set table
    print("Welcome to Class Search Tool!\nYou will need to enter a Subject and Catalog Number to begin searching")
    while 1: #get subject, repeat if skipped
        subject = input("Please enter a subject (ie: 'SDEV'):\n")
        if not subject:
            continue
        break
    while 1: #get catalog number, repeat if skipped
        catalog_nbr = input("Please enter a catalog number (ie: '400'):\n")
        if not catalog_nbr:
            continue
        break
    response = table.query(
        IndexName='SubNbr', #set index to use
        KeyConditionExpression=Key('Subject').eq(subject.upper()) & Key('CatalogNbr').eq(catalog_nbr) #set keys to search by
        )
    return response['Items'] #returns list of matching items
    
def display_search(t_name):
    while 1:
        results = course_search(t_name) #get list of matching items
        if not results:
            print("Could not find any results matching that subject and catalog number") #if list empty, return fail phrase
        else:
            for course in results:
                print(f"\n{course['Subject']}{course['CatalogNbr']}: {course['Title']}") #if list not empty, return course subject, number and title
        cont = input("Would you like to continue searching? (Enter 'Y' or 'N':\n")
        if cont.lower() =='n': #ask if user wants to continue searching or exit
            print("Goodbye")
            sys.exit()
        continue

# create_table('Courses', 'CourseID')
# put_items('Courses')
#create_sec_index()


def main():
    display_search('Courses')
#run main
if __name__ == '__main__':
    main()
