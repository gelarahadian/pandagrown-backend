# <center>Pandagrown</center>

## Description ##
Pandagrown is an innovative hi-tech company committed to sustainable agriculture, specifically focusing on the cultivation of hemp. Pandagrown harnesses the power of blockchain technology, the green economy, and eco-friendly policies in the management of its business. The company offers investors an opportunity to participate in a unique investment model, providing a return on investment through the sale of hemp. In addition, we share a portion of our income with panda conservation efforts to make a positive impact on endangered species.
### Software Requirements
Python3, PostgreSQL, Redis
## Installation
### To install pip (Python's package manager) using Python, you can follow these steps:
##### Download get-pip.py: If Python is installed, you can download the get-pip.py script, which is used to install pip. You can download it from the official website:
#### 
```html
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
```
  or
```html
  wget https://bootstrap.pypa.io/get-pip.py
```
  Install pip: Run the following command to install pip using the get-pip.py script:
```html
  python get-pip.py
```
  This command will download and install pip along with its dependencies.

#####  Verify Installation: After the installation is complete, you can verify that pip has been installed correctly by running the following command:
####
```html
  pip --version
```
  You should see the version of pip displayed.
#### Creating a virtual environment (venv) for a Django project is a good practice to isolate your project's dependencies and avoid conflicts with other Python projects. Here's how to create a venv for a Django project
####
##### Navigate to Your Project Directory:
Open a terminal or command prompt and navigate to the root directory of your Django project. If you're not in the project directory, you can use the cd command to change to the project's root directory.
```html
  cd /path/to/your/django/project
```
#####  Create a Virtual Environment:
You can create a virtual environment using the venv module, which is included in Python 3.3 and later. Run the following command, replacing venv with the name you want to give to your virtual environment:

```html
  python -m venv venv
```
#####  Activate the Virtual Environment:
You need to activate the virtual environment to use it. The activation command depends on your operating system:
######    On Linux/macOS:
####
```html
  source venv/bin/activate
```
######    On Windows:
####
```html
  venv\Scripts\activate
```
###  Install Django and Project Dependencies:
With the virtual environment active, you can now install Django and any other project-specific dependencies using pip. For Django, you can simply run:
```html
  pip install django
```
To install packages listed in a requirements.txt file using pip, you can use the following command:
```html
  pip install -r requirements.txt
```
### To migrate db, you can use the following command:
```html
  python manage.py makemigrations
  python manage.py migrate
 ```
##### To create superuser, you can use follow command
####
```html
  python manage.py createsuperuser
```
### Installing Redis as message broker
  You can reference following link to install redis on your machine
```html
  https://redis.io/docs/getting-started/installation/
```
### Run using Command Prompt
 
Navigate to the project folder which has manage.py file then run the following command on cmd
```html
  python3 -m daphne -b [Server Ip Address] panda_backend.asgi:application
  celery -A panda_backend worker --loglevel=info
```

###             Tech stack
`Backend` : Python3 
####
`Framework` : Django 
####
`Database` : PostgreSQL 
####
`Client Communication`: WebSocket 
####
`Message Broker`: Redis 


## How to use

### Email Setting
Administrator should create email setting before publishing this service on admin panel.

##### Sign Up Setting
SIGNUP Setting
```html
  EMAIL_CODE: 'SIGNUP'
  SUBJECT: 'You can input appropriate subject'
  EMAIL_BODY: {{LAST_NAME}} and {{VERIFY_LINK}} should be involved in email body.
```
##### Forgot Password Setting
FORGOT PASSWORD Setting
```html
  EMAIL_CODE: 'FORGOT_PASSWORD'
  SUBJECT: 'You can input appropriate subject'
  EMAIL_BODY: {{LAST_NAME}} and {{RESET_LINK}} should be involved in email body.
```
##### Seed Step Setting
SEED STEP Setting will be used when user purchases plant.
```html
  EMAIL_CODE: 'SEED_STEP'
  SUBJECT: 'You can input appropriate subject'
  EMAIL_BODY: {{NAME}}, {{STEP}} and {{HOUSE}} should be involved in email body.
```
##### Refferral Setting
REFERRAL Setting will be used when user referr his friend to join into this service.
```html
  EMAIL_CODE: 'REFERRAL'
  SUBJECT: 'You can input appropriate subject'
  EMAIL_BODY: {{USERNAME}}, {{REFERR_NAME}} and {{REFERR_LINK}} should be involved in email body.
```

### Notification Setting
Administrator should create notification setting before publishing this service on admin panel.

##### Withdraw Setting
Withdraw Setting
```html
  Type: 'Withdraw'
  Content: {{NAME}}, {{ACTION}} and {{BALANCE}} should be involved in content.
```
##### Purchase Setting
Purchase Setting
```html
  Type: 'Purchase'
  Content: {{SEED_NAME}} should be involved in content.
```
##### Seed Step Setting
Seed Step Setting
```html
  Type: 'Seed_Step'
  Content: {{NAME}}, {{SEED_NAME}}, {{STEP}} and {{HOUSE}} should be involved in content.
```
##### Sell Harvest Setting
Sell Harvest Setting
```html
  Type: 'Sell_Harvest'
  Content: {{NAME}}, {{ACTION}} and {{BALANCE}} should be involved in content.
```
##### Profile Update Setting
Profile Update Setting
```html
  Type: 'Profile_Update'
  Content: {{NAME}}, {{BALANCE_TYPE}} and {{POST_BALANCE}} should be involved in content.
```
### Currenty Setting
Administrator can apply currency settings. But there is a need to follow under rules.
Symbol is most important because this service is using symbols to get current value of tokens.
There are some samples which you can use:
```html
  Name      Symbol       Unit
  Bitcoin   bitcoin      BTC 
  Ethereum  ethereum     ETH
  Tether    tether       USDT
  BNB       binancecoin  BNB
  BUSD      BUSD         BUSD
```