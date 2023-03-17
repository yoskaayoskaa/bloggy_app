#  Bloggy webapp

## Bloggy is a small pet-project developed on Flask.

This app contains main social networks mechanics:   
    - user authentication   
    - text posts    
    - private messages  
    - following mechanism   
    - user profile (editing + deleting)     
    - password recovery via email

### Please follow these steps to run app on your local machine: 

1. Clone this repository.
2. Create a new Python project with virtual environment.
3. Install all dependencies:      


    pip install -r requirements.txt

4. Init local SQLite database:
        

    $ flask db init

5. Make migrations:


    $ flask db migrate
    $ flask db upgrade

6. Run app:


    $ flask run

To make email password recovery active please fulfill the .env file with corresponding data.