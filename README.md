## Cisco AAA config tool

This tool was meant to help deploy and validate AAA configuration for Cisco devices. It logs in with local account, configures AAA, logs out and logs back in with AD creds.

## Instructions

- Put your config in a text file, see "aaa-config" as an example
- Put list of IPs or hostname in a file, see "site1.txt" as an example
- Run "python async-config.py"

```
(.venv) host:/automation/cisco-aaa$ python async-config.py 
enter local username: netops
enter local password: 
enter ad username: jbeam
enter ad password: 
enter enable password: 
enter name of inventory file: site1.txt
enter name of configuration file: aaa-config
First we are going to deploy stuff.
CONFIGURING HOST 172.28.87.44 ...
CONFIGURING HOST 172.28.87.45 ...
Connection succeeded.
Connection succeeded.
Config succeeded on 172.28.87.44
Config succeeded on 172.28.87.45
Next we are going to validate login with AD credentials.
CONFIGURING HOST 172.28.87.44 ...
CONFIGURING HOST 172.28.87.45 ...
Connection succeeded.
Connection succeeded.
validation succeeded on 172.28.87.44
validation succeeded on 172.28.87.45
All done!
```
