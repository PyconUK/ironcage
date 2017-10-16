# Iron Cage

## What is this?

This is a web application for managing ticket sales, attendee preferences,
the CFP, financial applications, and possibly other aspects of organising PyCon UK.

## How do I run it?

This is a standard Django project.
Dependencies can be installed with `pip install -r requirements.txt`.
A local server can be started with `./manage.py runserver`, and tests can be run with `./manage.py test`.

To run locally, you will need to create a file called `.env`.
You can copy `.env.example` to `.env`, which will be enough to run the tests.
To interact with Stripe, you will need some test API keys.
Ask @inglesp if you would like to use the test API keys for the PyCon UK account.

You will also need to have a Postgres database called `ironcage`.

## Why are you reinventing the wheel?

We are aware of a number of other projects for managing conferences.
However, they are either too opinionated about how a conference should be organised,
in which case they would overly constrain how we run PyCon UK,
or else they attempt to be a framework for building conference management systems,
in which case we risk spending excessive time understanding and fighting a framework.

## Why the name?

The name comes from Weber's [Iron Cage of Bureacracy](https://en.wikipedia.org/wiki/Iron_cage), and I like the sound of a system that
"traps individuals in systems based purely on teleological efficiency, rational calculation and control"!
