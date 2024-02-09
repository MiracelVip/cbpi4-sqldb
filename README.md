# SensorLogTargetSqlDB for CraftBeerPi

This CraftBeerPi plugin enables the logging of sensor data to an SQL database, providing a robust way to store, analyze, and retrieve sensor readings over time. It allows for greater data persistence and analysis beyond what is available through CraftBeerPi's default storage options.

## Features

- **SQL Database Logging:** Automatically logs sensor data to a specified SQL database.
- **Configurable Logging Conditions:** Only logs data when a certain deviation is met or after a repeated number of identical readings, to reduce database clutter.
- **Automatic Table Creation:** Dynamically creates tables for each sensor, if not already present.
- **Customizable Database Settings:** Allows for the specification of database connection details directly from CraftBeerPi's configuration.

## Configuration

To use the `SensorLogTargetSqlDB` plugin, several configuration options need to be set within CraftBeerPi. These can be configured in the system settings under the plugin configuration section:

- `sql_log_active`: Enable or disable SQL logging. Requires a restart to take effect.
- `sql_log_server`: The address of your SQL server.
- `sql_log_username`: Username for the SQL server.
- `sql_log_password`: Password for the SQL server.
- `sql_log_database`: The name of the SQL database to use for logging.
- `sql_log_min_deviation`: The minimum deviation between sensor readings required to log the data to the database. This helps in avoiding excessive logging of data that hasn't changed significantly.

## Functionality

Upon activation and proper configuration, the plugin listens for sensor data updates. Each new sensor reading is evaluated to determine whether it differs sufficiently from the last logged value (based on the `sql_log_min_deviation` setting) or if it has been repeated a specific number of times (currently hardcoded to 10 repeats). This logic helps in reducing unnecessary writes to the database, thereby optimizing storage and potentially enhancing performance.

The plugin automatically creates a new table for each sensor, named `sensor_{sensorId}`, if it does not already exist. Sensor data are then logged with a timestamp, allowing for historical data analysis and retrieval.

## Writing Logic

1. **Initialization:** Upon startup, the plugin checks if SQL logging is enabled and initializes necessary configurations.
2. **Sensor Data Listening:** Listens for new sensor data from CraftBeerPi.
3. **Data Evaluation:** Determines whether new sensor data should be logged based on predefined conditions (value change or repetition).
4. **Database Interaction:** Handles SQL database connections, table creation, and data insertion asynchronously to ensure minimal impact on CraftBeerPi's performance.
5. **Error Handling:** Logs warnings or errors encountered during database interactions, ensuring the system remains informed of any issues that may affect data logging.

## Setup

To integrate `SensorLogTargetSqlDB` with CraftBeerPi, add the plugin to your CraftBeerPi installation and configure it through the CraftBeerPi interface. Ensure your SQL server is accessible, and the specified database exists before enabling the plugin.

## Dependencies

- CraftBeerPi 4.x
- `aiomysql` for asynchronous SQL database interaction

The dependencies will be installed during setup

## Conclusion

`SensorLogTargetSqlDB` extends CraftBeerPi's capabilities by enabling detailed logging of sensor data to an SQL database, providing a foundation for advanced data analysis and monitoring. By configuring the plugin to suit your logging preferences, you can efficiently manage sensor data storage and retrieval for your brewing activities.
