import os
# This will be giving us the fetched directory active
current_directory = os.getcwd()
print(f"Contents of directory: {current_directory}")
# This will list all the files and the folders in the recent directory_contents
directory_contents = os.listdir(current_directory)
# This will print all the items in it
for item in directory_contents:
    print(item)
