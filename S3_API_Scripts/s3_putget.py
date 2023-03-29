"""Menu for granting perms to a user (allowing them to get an object from one of your buckets),
    or getting an object from someone else's bucket (which you have permission to access)."""
import subprocess
import boto3
import sys
from botocore.exceptions import ClientError

#list buckets
def list_buckets():
    """returns list of buckets"""
    s3 = boto3.client('s3') #creates s3 client
    response = s3.list_buckets() #call s3 to list buckets
    buckets = [bucket['Name'] for bucket in response['Buckets']] #get list of all bucket names
    #resp_string = f"Bucket list: {buckets}"
    return buckets

#list bucket objects
def list_objects(bucket):
    """returns list of objects in bucket"""
    s3 = boto3.client('s3') #creates s3 client
    try:
        response = s3.list_objects_v2(Bucket=bucket) #call s3 to list objects
        if 'Contents'in response:
            objects = [key['Key'] for key in response['Contents']] #get list of object Keys, if objects exist
        else:
            objects = [] #if no objects, return empty list
    except ClientError as e:
        print(e)
        return False
    return objects

#Grant access to another user
def grant_perm():
    print("Need 3 args: \n\t1: Bucket name\n\t2: Key\n\t3: Canonical ID\n")
    print("-----------------------------------------")
    bucket_list = list_buckets()
    print("Available buckets: " + str(bucket_list))
    while 1:
        bucket = input("Please enter the name of the bucket:\n")
        if bucket not in bucket_list:
            continue
        break
    ob_list = list_objects(bucket)
    print("Available objects: " + str(ob_list))
    while 1:
        key = input("Please enter the name of the object to grant access:\n")
        if key not in ob_list:
            continue
        break
    can_id = input("Lastly, please provide the canonical ID of the user you want to grant access to:\n")
    subprocess.call(["./s3_grant_read.sh", bucket, key, can_id])
    # subprocess.check_call(["./s3_grant_read.sh", bucket, key, can_id])

#get object from another user
def get_outside_ob():
    print("Need 3 args: \n\t1: Bucket name\n\t2: Key\n\t3: Filename for local save\n")
    print("-----------------------------------------")
    bucket = input("Please enter the name of the bucket:\n")
    key = input("Please enter the name of the object to download:\n")
    save_name = input("Lastly, please enter the name of the file for saving locally:\n")
    subprocess.call(["./s3_get_object.sh", bucket, key, save_name])
    # subprocess.check_call(["./s3_get_object.sh", bucket, key, save_name])

def menu():
    print("1: Grant read access to another user\n2: Get object from another user\n3: Exit")
    while 1:
        sel = input("Please select an option from the menu above:\n")
        if sel not in ("1", "2", "3"):
            print("Please enter '1','2' or '3':\n")
            continue
        break
    return sel
    
def main():
    while 1:
        sel = menu()
        if sel == "1":
            grant_perm()
            continue
        elif sel == "2":
            get_outside_ob()
            continue
        elif sel == "3":
            print("Goodbye")
            sys.exit()
            break
        
#run main
if __name__ == '__main__':
    main()