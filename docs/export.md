# Export Data

In this section, we will show how to export data from a Drift instance by using the `drift-cli export` command.

## Export Raw Data

The `drift-cli export raw` command allows you to export data from a Drift instance to a local folder
on your computer. This can be useful if you want to make a copy of your data for backup or process them locally.

The `drift-cli export raw` command has the following syntax:

```
drift-cli export raw [OPTIONS] SRC DEST
```

`SRC` should be an alias of a Drift instance you want to export data from.

`DEST` should be the destination folder on your computer where you want to save the exported data.

Here is an example of how you might use the `drift-cli export raw` command:

```
drift-cli export raw drift-device ./exported-data --start 2021-01-23 --end 2021-01-24
```

This will export all the raw data from the `drift-device` Drift instance to the `./exported-data` folder on your
computer.
For each topic the CLI will create a separate folder. Each package will be saved as a separate file with the name
`<timestamp>.dp`.

## Available options

Here is a list of the options that you can use with the `drift-cli export` commands:

* `--start`: This option allows you to specify a starting time point for the data that you want to export. Data with
  timestamps newer than this time point will be included in the export. The time point should be in ISO format (e.g.,
  2022-01-01T00:00:00Z).

* `--stop`: This option allows you to specify an ending time point for the data that you want to export. Data with
  timestamps older than this time point will be included in the export. The time point should be in ISO format (e.g.,
  2022-01-01T00:00:00Z).

* `--csv`: This option allows you to export data in csv format. It creates a separate csv file for each topic in the
  exported data and save time series data in a single column with meta information in first row. The meta information
  has the following format: `topic,package count, first timestamp, last timestamp`. The timestamp format is Unix time
  in milliseconds.
* `--topics`: This option allows you to specify a list of topics that you want to export. The list should be a comma
  separated list of topic names. For example, `--topics topic1,topic2,topic3`. You can also use wildcards to specify
  multiple topics. For example, `--topics topic*` will export all topics that start with `topic`.

You also can use the global `--parallel` option to specify the number of entries that you want to export in parallel:

```
drift-cli  --parallel 10  export raw drift-device ./exported-data --start 2021-01-01T00:00:00Z --stop 2021-01-02T00:00:00Z
```
