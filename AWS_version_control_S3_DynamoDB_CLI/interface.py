import boto3, os, sys, random, time, re
from datetime import datetime
from botocore.exceptions import ClientError
from pathlib import Path
from s3_functions import (create_bucket, list_buckets, list_objects, upload_changes,
                          upload_file, copy_object, ob_download)
from dynamodb_functions import create_table, put_items, changes_tracking, put_new_version, repo_summary


def get_repo(name=None, version=None):
    """see if repo exists or not"""
    new_or_not = False
    #new repos
    if name is None and version is None:
        new_or_not = True
        print("To create a new repository, you will need to provide a name and version number\n")
        while 1:
            name = input("Please enter the name of your project:\n")
            if not name:
                continue
            break
        while 1:
            try:
                version = float(input("Please enter the version of your project:\n"))
            except ValueError:
                print("Please enter the version in the form of a float (ie: 1.0, or 3.45):\n")
                continue
            break
    #existing repos
    existing_buckets = list_buckets()
    b = name + 'v' + str(version)
    if b in existing_buckets:
        new_or_not = False
    return name, version, new_or_not

def tree(dir_path, prefix):
    """Pretty print filetree"""
    #tree characters
    space =  '    '
    branch = '│   '
    tee =    '├── '
    last =   '└── '
    #list of dirs/file in path
    contents = list(dir_path.iterdir())
    #create list of tree characters based on length of tree
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        yield prefix + pointer + path.name #generate tree characters + filename
        if path.is_dir(): # extend the prefix and recurse:
            extension = branch if pointer == tee else space #remove 'tee' character from prefix, and replace with 'branch' if dir
            yield from tree(path, prefix=prefix+extension) #recurse
def dir_walk(base_dir, file_or_dir):
    file_dict = {}
    dir_dict = {}
    for root, dirs, files in os.walk(Path(base_dir)):
        for filename in files:
            f_path = os.path.join(root, filename)
            file_dict[f_path] = filename #create dict of filepath and filename
        for dirname in dirs:
            d_path = os.path.join(root, dirname)
            dir_dict[d_path] = dirname #create dict of dirpath and dirname
    while 1:
        for line in tree(Path(base_dir), ""):
            print(line) #print tree
        upload = ""
        if file_or_dir == 'file':
            upload_ch = input("Please enter the name of a file to upload:\n")
            for file_p, file_n in file_dict.items():
                if upload_ch == file_n:
                    upload = file_p #check if file in dict, set choice to filepath
            if not upload:
                print("Selection not found")
                continue
        elif file_or_dir == 'dir':
            upload_ch = input("Please enter the name of a directory to upload:\n")
            for dir_p, dir_n in dir_dict.items():
                if upload_ch == dir_n:
                    upload = dir_p #check if dir in dict, set choice to dirpath
            if not upload:
                print("Selection not found")
                continue
        break
    return upload

class Repository(object):
    """Repository object"""
    def __init__(self, name, version, new):
        self.name = name
        self.version = version

    #create bucket
    def create_bucket(self):
        """creates s3 bucket """
        bucket_name = self.name + 'v' + str(self.version)
        create_bucket(bucket_name)
        print("Created bucket", bucket_name, "in your S3 buckets")
    #create table
    def new_table(self):
        """creates dynamodb table """
        table_name = self.name + '_metadata'
        create_table(table_name, self.name, str(self.version))
        print("Created Table", table_name, "in your DynamoDB tables")
    #upload project
    def upload_project(self):
        """uploads files and data to s3 bucket and dynamodb table """
        #bucket stuff
        bucket_name = self.name + 'v' + str(self.version)
        directory = dir_walk('./', 'dir') #select file/folder from cwd
        #dynamodb stuff
        table_name = self.name + '_metadata'
        dt = str(datetime.now())
        put_items(table_name, self.name, bucket_name, str(self.version), directory, dt) #upload data to table
        print("Updated table", table_name, "in your DynamoDB tables.")
        upload_file(directory, bucket_name) #upload directory to bucket
        print("Uploaded", directory, "to your", bucket_name, "bucket.")
        
    #staging/new version stuff
    #copy repo to new version -> 
    #create new bucket (same file struct. new version), create new table (same attr. new version)
    def new_version(self):
        """creates new version (new bucket, new table item) """
        print("Creating a new version")
        up_version = 0.1 + self.version

        #new bucket
        bucket_name = self.name + 'v' + str(self.version)
        self.version = round(up_version, 1) #add .1 to version
        n_bucket_name = self.name + 'v' + str(self.version) #name remains the same
        create_bucket(n_bucket_name) #create new bucket
        print("wait a few seconds while your bucket is created")
        time.sleep(20) #allow bucket to be created
        print("Created bucket", n_bucket_name, "in your S3 buckets")
        copy_object(bucket_name, n_bucket_name) #copy objects from previous version to new version
        #new table item
        table_name = self.name + '_metadata'
        dt = str(datetime.now())
        directory = list_objects(bucket_name)
        put_new_version(table_name, self.name, n_bucket_name, str(self.version), directory, dt)
    
    def upload_changes(self):
        """upload files individually """
        while 1:
            file_sel = dir_walk('./', 'file') #get file to upload
            bucket_name = self.name + 'v' + str(self.version)
            upload_changes(file_sel, bucket_name) #uplaod file to bucket
            
            note_in = input("If you want to add a description of changes made, please add it beow:\n")
            notes = file_sel + ': ' + note_in #add notes of changes made
            table_name = self.name + '_metadata'
            changes_tracking(table_name, self.name, str(self.version), file_sel, notes) #append table item
            exit = input("Enter 'exit' to stop, or 'cont' to continue uploading:\n")
            if exit.lower() == 'exit':
                break
            continue
        
    def summary(self):
        """get summary of a repo """
        table_name = self.name + '_metadata'
        repo_summary(table_name, self.name, str(self.version))
        
    def download_repo(self):
        """download entire bucket """
        bucket_name = self.name + 'v' + str(self.version)
        folder = './' #folder in bucket
        local_path = '../' + bucket_name #local folder to download (just goes back 1 directory)
        ob_download(bucket_name, folder, local_path)
        

"""create repo menu:
(auotmatically generates version#, creates bucket, creates table,
upload project to bucket, uploads metadata to table, returns summary of repo)"""
def new_repo(obj):
    """calls create_bucket(), new_table(), and upload_project() functions """
    print("please wait while we create your bucket")
    time.sleep(20)
    obj.create_bucket()
    print("please wait while we create your table")
    time.sleep(10)
    obj.new_table()
    obj.upload_project()
    
def new_repo_menu():
    """menu for creating new repo (gets name, version, checks if exists """
    print("Creating a new repository")
    while 1:
        r_name, r_version, is_nw = get_repo() #check if exists
        if is_nw:
            cur_repo = Repository(r_name, r_version, is_nw) #creates object
            new_repo(cur_repo) #creates new repo
            break
        else:
            print("That repository already exists")
            continue
        
"""manage existing repo menu #1:
first checks for changes made in gui/console (s3 does not match dynamodb)
(selects repo ->returns summary->opens management menu for that repo(branching, staging, pulls?merge?)"""
def select_existing_repo():
    """select existing repo menu """
    existing_buckets = list_buckets() #get list of buckets
    rgx = re.compile(r'v[0-9]\.[0-9]')
    existing_repos = list(filter(rgx.search, existing_buckets)) #filter buckets by 'vx.x'
    while 1:
        for r in existing_repos:
            n = r.split('v')[0]
            v = r.split('v')[1]
            print(f'Name: {n}, Version: {v}')
        existing_name = input("Please enter the name of the repo from the above list:\n")
        while 1: #choose repo
            try:
                existing_version = float(input("Please enter the version of the repo from the above list:\n"))
            except ValueError:
                print("Please enter version in the form of a float")
                continue
            break
        ex = existing_name + 'v' + str(existing_version)
        if ex in existing_repos: #check if exists
            break
        print("Cannot find that repo. Please Try again")
        continue
    ex_repo = Repository(existing_name, existing_version, False) #create and return object
    return ex_repo
    
def next_version():
    """select and create new version of existing repo """
    repo_sel = select_existing_repo()
    repo_sel.new_version()
    
def change_version():
    """select and upload files to existing repo """
    repo_sel = select_existing_repo()
    repo_sel.upload_changes()

def get_summary():
    """select and get summary of existing repo """
    repo_sel = select_existing_repo()
    repo_sel.summary()

def repo_dl():
    """select and download existing repo """
    repo_sel = select_existing_repo()
    repo_sel.download_repo()

def existing_menu():
    """menu for managin existing repos """
    print("Manage Existing Repository\nSelect an option below")
    while 1:
        choice = input("1: Create a new Version\n2: Upload new or changed files to repo\n3: Get summary of repository\n4:Download Repository\n")
        if choice not in ('1', '2', '3', '4'):
            print("Please enter '1', '2', '3' or '4'")
            continue
        break
    if choice == '1':
        next_version()
    if choice == '2':
        change_version()
    if choice == '3':
        get_summary()
    if choice == '4':
        repo_dl()
        
        
"""initial menu:
(create new repo, manage existing repo->(branching, staging, pulls?? ))"""
def menu_1():
    """ welcome menu """
    print("Welcome to AWS version control, please choose an option below:\n")
    while True:
        choice = input("1: Create a new repository\n2: Manage an existing repository\n3: Exit\n")
        if choice not in ('1', '2', '3'):
            continue
        break
    return choice
    
def main():
    """handling menu choices"""
    while 1:
        choice = menu_1() #get choice
        if choice=='1':
            new_repo_menu()
            continue
        elif choice =='2':
            existing_menu()
            continue
        elif choice == '3':
            print("goodbye")
            sys.exit()
            break
#run main
if __name__ == '__main__':
    main()
