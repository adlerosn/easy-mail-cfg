# Easy Mailer Configurator
#### Postfix + OpenDKIM + CloudFlare

Because setting up DKIM on many servers and domains can be boring.

This is just an automation of a [tutorial](https://fatorbinario.com/linux-como-autenticar-emails-com-dkim-e-postfix/).

## Environment

- Ubuntu Server
- Python 3.6+

## Running

Create a text file on `/srv/easymail.cfg`. The lines of this files are:

1. Your email which is your login on CloudFlare
2. Your CloudFlare API token
3. Email for DMARC reports
4. Server's IP v4
5. Server's IP v6
6. domain 1
7. domain 2
8. domain 3
9. ...

Run `make` as root.
