"""cli for interacting with s3 buckets"""
import os, sys, boto3, datetime, random
from botocore.exceptions import ClientError
from pathlib import Path

#list buckets
def list_buckets():
    """returns list of buckets"""
    s3 = boto3.client('s3') #creates s3 client
    response = s3.list_buckets() #call s3 to list buckets
    buckets = [bucket['Name'] for bucket in response['Buckets']] #get list of all bucket names
    resp_string = buckets
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
        # print(f"Bucket ({name}) created succesfully.")
    except ClientError as e:
        print(e)
        return False
    return True

#put objects into bucket
def upload_file(directory, bucket):
    """Uploads file to bucket"""
    s3 = boto3.client('s3') #create s3 client
    tree = [x for x in os.walk(directory)]
    file_ends = [] #folders
    for dir in tree:
        path = dir[0]
        files = dir[2]
        for file in files:
            filepath = path+'/'+file
            file_ends.append(filepath)
    for file in file_ends:
        try:
            response = s3.upload_file(file, bucket, file) #use client to upload file
        except ClientError as e:
            print(e)
            return False
    return True
def upload_changes(file, bucket):
    s3 = boto3.client('s3')
    try:
        response = s3.upload_file(file, bucket, file) #use client to upload file
    except ClientError as e:
        print(e)
        return False
    return True
    
#copy repo
def copy_object(o_bucket, n_bucket):
    """Copies object from 1 bucket to another bucket"""
    s3r = boto3.resource('s3') #create s3 client
    objects = list_objects(o_bucket)
    for file in objects:
        try:
            copy_source = {'Bucket':o_bucket, 'Key':file} #source file and bucket
            s3r.meta.client.copy(copy_source, n_bucket, file) #copy from source to new bucket
            print(f"Successfully moved {file} from {o_bucket} to {n_bucket}")
        except ClientError as e:
            print(e)
            return False
    return True

#download object
def ob_download(bucket, s3_folder, local_dir=None):
    """Downloads objects from bucket"""
    s3 = boto3.resource('s3') #create s3 client
    bucket_objs = s3.Bucket(bucket)
    # objects = list_objects(bucket)
    
    for obj in bucket_objs.objects.filter(Prefix=s3_folder):
        target = obj.key if local_dir is None \
            else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder)) #local path for download
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target)) #create dir(s) if they don't exist locally
        if obj.key[-1] == '/':
            continue #continue if subdirs exist
        bucket_objs.download_file(obj.key, target) #download
