# Carnet-alexa
Give Alexa the power to control your car from anywhere

## Installing
**Requirements**
* Amazon AWS & developer accounts
* A carnet-enabled Volkswagen

Upload `lambda_function.py` and the  `modules` folder as a .zip file to a new lambda function.<br>
Add your username and password to `lambda_function.py` in the `VWCarnet` constructor.<br>
In the Amazon developer console create a new Alexa Skill and link it to the function.<br>
Copy and paste the contents of `inteactionmodel.json` into the code section of the Skill builder.<br>
Save, build and enjoy.

## A small list of things to ask Alexa
`Alexa ask car net how much battery my car has`
`Alexa ask car net if my car is charging`
`Alexa ask car net, is my car heating`
`Alexa ask car net. What's the status of my car`
`Alexa ask car net where my car is`
`Alexa ask car net start charging my car`
`Alexa ask car net stop heating my car`

## Don't have an Echo?
Look no further than (here)[] or the https version. Great for automation with IFTTT

## Huge Thank you to
@robinostlund: https://github.com/robinostlund/volkswagen-carnet
