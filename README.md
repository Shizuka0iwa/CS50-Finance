# C$50 Finance

#### Description:

C$50 Finance is a demo application for stock trading.

I made it for a CS50 assignment at Harvard University.


# Features

## View your portfolio in one view.

It shows your balance, total investments, cash balance, and stock holdings. It also shows the real-time market prices of the stocks you hold.

## Quote

You can check the real-time stock prices provided by IEX.

## Buy & Sell

You can buy new stocks or sell the ones you have.

## The Trading History

With this application, you can view your transaction history for the entire period.


# Prerequirsite

- Python 3
- pip
- iex cloud API token
Follow the instruction about [creating constants.py file](##constants.py).
## iex cloud API token
- Visit the [resistration page](https://iexcloud.io/cloud-login#/register/).
- Create an account as "Individual".
- Visit [the console](https://iexcloud.io/console/tokens) to check your API token.
- Save the token in `constants.py` file.


# Installation

## pip
To set up development emvironment, [follow a instruction and install pip](https://pip.pypa.io/en/stable/installation/).

## Install packages
Install packages with pip and requirements.txt

```
$ pip install -r requirements.txt
```

# Files
## application.py
It contains code for routing.

## helpters.py
It contains code for implement the application such as calling API.

## templates
The folder contains html files for the web page.

## static
The folder has style.css file and images folder which contains image data.

## constants.py
You need to create this file on your local. 

- Visit the [resistration page](https://iexcloud.io/cloud-login#/register/).
- Create an account as "Individual".
- Visit [the console](https://iexcloud.io/console/tokens) to check your API token.
- Save the token in `constants.py` file.

Put your API token on the file like this.
```
API_KEY = 'ABC123ABC123'
```


# Development

## Running the application
To run the application, you can start Flask server by running the following command.

```
FLASK_APP=application.py flask run
```

Then you should see a message

```
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

Go to http://127.0.0.1:5000/ and check the home page.

First, you will be redirected to the login page.
If you don't have an account, go to the registration page (click on `Registration` on header or go to http://127.0.0.1:5000/register)  and register an account.

When you register for an account, your default cash value is set as $10,000.