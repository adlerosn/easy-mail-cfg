# Easy Mailer Configurator
#### Postfix + OpenDKIM + CloudFlare

Because setting up DKIM on many servers and domains can be boring.

This is just an automation of a [tutorial](https://fatorbinario.com/linux-como-autenticar-emails-com-dkim-e-postfix/).

## Environment

- Ubuntu Server.
- Python 3.6+

## Running

Create a text file on `/srv/easymail.cfg`. The lines of this files are:

1. Your email which is your login on CloudFlare
2. Your CloudFlare API token
3. domain1
4. domain2
5. domain3
6. ...

Run `make` as root.
