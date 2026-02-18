
# TODO:  Make this thing work.  Getting timed out...


import paramiko

def list_files_via_sftp(host, port, username, password, directory="."):
    try:
        # Initialize the SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Accept unknown host keys

        # Connect to the server
        # print("Connecting via SSH...")
        ssh.connect(hostname=host, port=port, username=username, password=password)
        # print("Connection established!")

        # Open an SFTP session
        sftp = ssh.open_sftp()

        # List files in the specified directory
        print(f"Listing files in directory: {directory}")
        files = sftp.listdir(directory)  # Lists only filenames
        for file_name in files:
            print(file_name)

        # Optional: Use listdir_attr() to get file attributes like size, modification time, etc.
        print("\nDetailed file information:")
        file_attributes = sftp.listdir_attr(directory)  # Returns file attributes
        for file_attr in file_attributes:
            print(f"{file_attr.filename} - size: {file_attr.st_size}, modified: {file_attr.st_mtime}")

        # Close SFTP and SSH connections
        sftp.close()
        ssh.close()
    except Exception as e:
        print(f"Error: {e}")



# SSH server details
host = "compass.pnl.gov"
port = 22  # Default SSH port
username = "flue473"
password = ""
directory = "/compass/fme200002/slosh_flooding/tempest_doc_gis"  # Directory to list files

# Call the function
list_files_via_sftp(host, port, username, password, directory)