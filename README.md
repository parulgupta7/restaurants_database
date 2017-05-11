# restaurants_database
The restaurants_database is a web application and a JSON API which shows a list of restaurants and their menus.
It also allows a user to sign in through google sign in and creates their own restaurants.
The restaurant which a particular user has created, only that user can edit, delete or update that restaurant.

# Instructions :

## Setup google sign in authentication.
1. Visit the following link : https://console.developers.google.com/project
2. Now, login with your google account.
3. Click on "Create Project" and then name that project.
4. Select credentials menu from left side and create a new OAuth client ID.
5. Then select web application.
6. Update the consent screen by entering your application name and your email ID.
7. Now, open your web application and add following options: 
   (a) In Authorized javascript origins add: http://localhost:5000
   (b) In Authorized redirect URIs add: http://localhost:5000/login and http://localhost:5000/gconnect.
8. Click on create client ID and save.
9. Cick download JSON and save it in project root directory as "client_secrets.JSON"


## Creating database file and setting up server :
1. Use the command vagrant up in the root directory.
2. Now, the vagrant machine will get installed.
3. Once this installation is complete, type "vagrant ssh" to login to the VM.
4. Now, in VM, type command: "cd /vagrant"
5. Now, type "python database_setup.py".
6. This will create the database that is required according to the script.
7. Now, fill the tables of the database with values using "python lotsofmenu.py" command.
8. Now, type "python final_project.py" to start the server.

## Start using the website by typing http://localhost:5000/ in browser.




 
