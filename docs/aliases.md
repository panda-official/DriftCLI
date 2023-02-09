# Aliases

Aliases are used to simplify communication with a Drift instance.
This way, users don't have to type the IP address or hostname and credentials for the Drift instance each time they want
to use it.

To create an alias, use the following `drift-cli` command:

```shell
drift-cli alias add local
```

Alternatively, you can provide the URL and API token for the storage engine as options:

```shell
drift-cli alias  add -a 127.0.0.1 -p password -b bucket local
```

## Browsing aliases

Once you've created an alias, you can use the `drift-cli` alias command to view it in a list or check its credentials:

```shell

```shell
drift-cli alias ls
drift-cli alias show local
```

## Removing an alias

To remove an alias, use the rm subcommand of `drift-cli` alias:

```shell
drift-cli alias rm play
```
