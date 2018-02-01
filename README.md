# Carnet-alexa
Give Alexa the power to control your car from anywhere

## Installing
**Requirements**
* Amazon AWS & developer accounts
* A carnet-enabled Volkswagen

Upload `lambda_function.py` and the  `modules` folder as a .zip file to a new lambda function with `lambda_function.main` as the handler and a timeout of 1min 30s or more.<br>
Add your username and password to `lambda_function.py` in the `VWCarnet` constructor.<br>
In the Amazon developer console create a new Alexa Skill with "car net" as the invocation name.<br>
In "Interaction Model" open the skill builder and upload `inteactionmodel.json` in the code section.<br>
Save and build before moving on to the "Configuration" Section.<br>
Check "AWS Lambda ARN" and copy the arn "link" at the top of the lambda page into the default page.<br>
Save and enjoy.

## A small list of things to ask Alexa
`Alexa ask car net how much battery my car has`<br>
`Alexa ask car net if my car is charging`<br>
`Alexa ask car net where my car is`<br>
`Alexa ask car net start charging my car`<br>
`Alexa ask car net stop heating my car`<br>
`Alexa ask car net, is my car heating?`<br>
`Alexa ask car net. What's the status of my car?`

## Don't have an Echo?
Look no further than [here](https://github.com/Strosel/Carnet_http) for the http version. Great for automation with IFTTT

## Huge Thank you to
@robinostlund: https://github.com/robinostlund/volkswagen-carnet
