"""cli for interacting with s3 buckets"""
import os
import sys
import boto3
import datetime
import random
from botocore.exceptions import ClientError
from pathlib import Path

#list buckets
def list_buckets():
    """returns list of buckets"""
    s3 = boto3.client('s3') #creates s3 client
    response = s3.list_buckets() #call s3 to list buckets
    buckets = [bucket['Name'] for bucket in response['Buckets']] #get list of all bucket names
    resp_string = f"Bucket list: {buckets}"
    return resp_string


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
    
    
#list folders in a bucket
def list_folders(bucket):
    """returns list of folders in bucket"""
    ob_list = list_objects(bucket) #call list_objects()
    folder_list = []
    for ob in ob_list:
        path_s = "".join(ob.split("/")[:-1]) #find folders
        if path_s:
            folder_list.append(path_s + "/") #if folders are found, add to list
    return folder_list


#create bucket
def create_bucket(name, region=None):
    """Creates bucket"""
    try:
        if region is None:
            s3 = boto3.client('s3') #create s3 client
            s3.create_bucket(Bucket = name) #create bucket
        else:
            s3 = boto3.client('s3') #create s3 client
            loc = {'LocationConstraint':region} #set region
            s3.create_bucket(Bucket=name, CreateBucketConfiguration=loc) #create bucket
        print(f"Bucket ({name}) created succesfully.")
    except ClientError as e:
        print(e)
        return False
    return True
    
def create_bucket_proc():
    """calls create_bucket() and implments naming convention"""
    fname = input("Please enter your first name:\n") 
    lname = input("Please enter your last name:\n")
    suffix_num = random.randint(100000, 999999)
    name = fname.lower() + lname.lower() + "-" + str(suffix_num) #generate name
    create_bucket(name) #calls create bucket
    print("Operation successful\n")
    print(list_buckets())


#put objects into bucket
def upload_file(f_name, bucket, ob_name=None):
    """Uploads file to bucket"""
    if ob_name is None:
        ob_name = os.path.basename(f_name)
    s3 = boto3.client('s3') #create s3 client
    try:
        response = s3.upload_file(f_name, bucket, ob_name) #use client to upload file
        print(f"Successfully uploaded {f_name}")
    except ClientError as e:
        print(e)
        return False
    return True
    
def upload_file_proc():
    """select bucket/folder and calls upload_file()"""
    print(list_buckets())
    bucket = input("Please enter the name of your bucket from the list above:\n") #select bucket
    f_list = list_folders(bucket)
    if f_list:
        print(list_folders(bucket))
        f_choice = input("Would you like to upload file to one of the existing folders('Y' or 'N')?\n") #if folders, select folder
    else:
        f_choice = input("Would you like to upload file to a new folder-- ('Y' or 'N')?\n") #if no folders, create new folder
    if f_choice.lower() == 'y':
        pref_name = input("Please enter the name of the existing folder, or enter the name of a new folder:\n")
        p_name = ''.join(c for c in pref_name if c not in '/') #generate new folder name (folders don't really exist in s3, it is just a name followed by '/')
    else:
        p_name = ''
    
    x = Path('./')
    print(list(filter(lambda y:y.is_file(), x.iterdir())))
    f_name = input("Please enter a file name from the list above:\n") #select file from cwd
    if f_choice.lower() == 'y':
        p_f_name = p_name + '/' + f_name
        upload_file(f_name, bucket, p_f_name) #upload file (to folder)
    else:
        upload_file(f_name, bucket) #upload file
    print("Operation successful")
    print(list_objects(bucket))
    
    
#delete object in bucket
def delete_object(f_name, bucket, ob_name=None):
    """Deletes object in bucket"""
    if ob_name is None:
        ob_name = os.path.basename(f_name)
    s3 = boto3.client('s3') #create s3 client
    try:
        response = s3.delete_object(Bucket = bucket, Key = f_name) #call client to delete object
        print(f"Successfully deleted {f_name}")
    except ClientError as e:
        print(e)
        return False
    return True
    
def delete_object_proc():
    """selects bucket and calls delete_object()"""
    print(list_buckets())
    bucket = input("Please enter the name of the bucket from the list above:\n") #select bucket
    ob_list = list_objects(bucket)
    print(ob_list)
    while 1:
        f_name = input("Please enter the name of the file from the list above:\n") #select object to delete
        if f_name not in ob_list:
            print("Make sure you have entered the filename correctly.\nTry again.")
            continue
        break
    delete_object(f_name, bucket) #delete object
    print("Operation successful")
    print(list_objects(bucket))
    
    
#delete bucket
def delete_bucket(bucket):
    """Deletes bucket"""
    s3 = boto3.client('s3') #create s3 client
    try:
        response = s3.delete_bucket(Bucket=bucket) #calls client to delete bucket
        print(f"successfully deleted bucket {bucket}")
    except ClientError as e:
        print(e)
        return False
    return True
    
def delete_bucket_proc():
    """Selects bucket and calls delete_bucket() + warns if bucket is not impty"""
    print(list_buckets())
    bucket = input("Please enter the name of the bucket from the list above:\n") #select bucket
    obj_list = list_objects(bucket)
    if not obj_list:
        try:
            delete_bucket(bucket) #if bucket is empty, deletes bucket
        except ClientError as e:
            print(e)
            return False
            
    else:        
        print("WARNING: The bucket you are trying to delete is not empty\n")
        inp = input("Would you like to delete anyways? ('Y' or 'N')") #if bucket not empty, ask to continue
        if inp.lower() == 'y':
            bucket1 = boto3.resource('s3').Bucket(bucket)
            bucket1.objects.all().delete() #force delete objects in bucket
            bucket1.delete() #delete bucket
            print("Operation successful")
            print(list_buckets())
        else:
            print("Operation aborted") #cancel operation
            print(list_buckets())
            

#copy object from 1 bucket to another
def copy_object(o_bucket, f_name, n_bucket):
    """Copies object from 1 bucket to another bucket"""
    s3 = boto3.resource('s3') #create s3 client
    try:
        copy_source = {'Bucket':o_bucket, 'Key':f_name} #source file and bucket
        s3.meta.client.copy(copy_source, n_bucket, f_name) #copy from source to new bucket
        print(f"Successfully moved {f_name} from {o_bucket} to {n_bucket}")
    except ClientError as e:
        print(e)
        return False
    return True
    
def copy_object_proc():
    """Selects orginating bucket, destination bucket, and file, and calls copy_object()"""
    print(list_buckets())
    o_bucket = input("Please enter the name of the bucket you wish to copy from:\n") #select origin bucket
    print(list_buckets())
    n_bucket = input("Please enter the name of the bucket you wish to copy to:\n") #select dest.bucket
    ob_list = list_objects(o_bucket)
    print(ob_list)
    while 1:
        f_name = input(f"Please enter the name of the file you wish to copy from {o_bucket} to {n_bucket}\n") #select file from orig. bucket
        if f_name not in ob_list:
            print("Please make sure you have entered the name of the file correctly.\nTry again.") #check if file exists
            continue
        break
    copy_object(o_bucket, f_name, n_bucket) #copy object
    print("Operation Successful")
    print(list_objects(n_bucket))


#download object
def ob_download(f_name, bucket, path_name):
    """Downloads object from bucket"""
    s3 = boto3.resource('s3') #create s3 client
    try:
        s3.Bucket(bucket).download_file(Key=f_name, Filename=path_name) #download file
        print(f"successfully downloaded file {f_name}")
    except ClientError as e:
        print(e)
        return False
    return True
    
def ob_download_proc():
    """selects bucket and file, calls download_file()"""
    print(list_buckets())
    bucket = input("Please enter the name of the bucket you wish to download from:\n") #select bucket
    ob_list = list_objects(bucket)
    print(ob_list)
    while 1:
        f_name = input("Please enter the name of the file you wish to download:\n") #select file
        if f_name not in ob_list:
            print("Please make sure you have entered the name of the file correctly.\nTry again.") #check if file exists
            continue
        break
    h, s, t = f_name.partition('/') #if folder ('foldername/filename'), split at '/' ---for destination name
    if not t:
        p_name = h #if not folder, file name=f_name
    else:
        p_name = t #if folder, file name = tail(f_name)
    ob_download(f_name, bucket, p_name) #download object
    print("Operation Successful")
    

#exit
def exit_f():
    """Prints datetime and exits program"""
    cur_dt = str(datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")) #format date and time
    print(f"Exiting. {cur_dt}") #print datetime
    print("Goodbye.")
    sys.exit() #exit


#CLI menu
def menu():
    """Displays menu and user's choice"""
    print("S3 bucket interface\n")
    while 1:
        print("Please select an option below:")
        #choice for menu selection
        choice = input("1: Create an S3 bucket\n2: Upload object to a bucket\n3: Delete object in a bucket\n4: Delete bucket\n5: Move object from one bucket to another\n6: Download an object from a bucket\n7: Exit\n")
        if choice not in ('1', '2', '3', '4', '5', '6', '7'): #check if choice is valid
            print("Please enter '1', '2', '3', '4', '5', '6', or '7'\n")
            continue
        break
    return choice


#main function
def main():
    """Calls menu, and the corresponding function to user's choice"""
    while True:
        choice = menu()
        if choice == '1':
            create_bucket_proc() #1 = create bucket
            continue
        elif choice == '2':
            upload_file_proc()#2 = upload
            continue
        elif choice == '3':
            delete_object_proc() #3 = delete object
            continue
        elif choice == '4':
            delete_bucket_proc() #4 = delete bucket
            continue
        elif choice == '5':
            copy_object_proc() #5 = copy object
            continue
        elif choice == '6':
            ob_download_proc() #6 = download object
            continue
        elif choice == '7':
            exit_f() #7 = exit program
            break


#run main
if __name__ == '__main__':
    main()
