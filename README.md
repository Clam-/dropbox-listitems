```listitems.py``` will output to a file the folders of your dropbox and how big they are.

You will need a [Dropbox application developer](https://www.dropbox.com/developers/apps) key and secret.  
Place those details in to a file called ```listitems.json``` or copy and modify the existing ```listitems.json.example```

Example usage:
```
python listitems.py --max-depth=1 --output="Dropbox-2levels.txt"
1. Go to: https://www.dropbox.com/1/oauth2/authorize?response_type=code&client_id=XYZ
2. Click "Allow" (you might have to log in first).
3. Copy the authorization code.
Enter the authorization code here: CHARACTERS
This user ID is 12345678. Pass it to --user on next invocation to skip authorization.
Fetch complete. Saving information to file...
Complete.
```
As the above console output displays, open that URL in your browser on any device.
Log in to your Dropbox account (if you are already not logged in.)
Click Allow to allow the application to access your file and folder information.
Copy/type the code you received after clicking allow in to the program.

On following execution you can use the user ID gathered in the first run to skip authorization on subsequent executions:
```
python listitems.py --user=12345678 --max-depth=3 --output="Dropbox-4levels.txt"
Fetching file and folder information stored on Dropbox. Please wait...
Fetch complete. Saving information to file...
Complete.
```
