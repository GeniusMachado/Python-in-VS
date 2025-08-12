import os

# Get the current working directory
current_directory = os.getcwd()
print(f"Contents of directory: {current_directory}")

# List all files and folders in the current directory
directory_contents = os.listdir(current_directory)

# Print each item
for item in directory_contents:
    print(item)
