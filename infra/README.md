### Overview
The purpose of this part of the package is to manage infrastructure.
Lambda creation, storage, user mgmt, api gateway and cloudfront.
This is not meant to be a run and forget it framework, but a launching point to bootstrap a project.

### Conventions and Assumptions
There are as several assumptions made in the infra package.
1.) Lambda names (in backend/) are the module name.
2.) Lambda entry file is called "main.py", and handler method is called "handler".
