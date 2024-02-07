# -*- coding: utf-8 -*-
import logging
import asyncio
from cbpi.api import *
from cbpi.api.config import ConfigType
import aiomysql

logger = logging.getLogger(__name__)

class SensorLogTargetSqlDB(CBPiExtension):
    def __init__(self, cbpi):
        self.cbpi = cbpi
        # Check if SQL logging is activated in the config
        self.sqldb = self.cbpi.config.get("sql_log_active", False)
        if not self.sqldb:
            return
        
        # Dictionary to store the last value and repeat count of each sensor
        self.lastValues = {}

        # Start the main task for this extension
        self._task = asyncio.create_task(self.run())

    def shouldWriteSensorData(self, sensorId, sensorValue):
        """
        Determines whether a new sensor value should be written to the database.
        It checks against the last value for changes greater than the configured deviation or if the same value repeats 10 times.
        """
        lastValue = self.lastValues.get(sensorId, {'value': None, 'repeats': 0})

        if lastValue['value'] is None or abs(sensorValue - lastValue['value']) >= self.cbpi.config.get("sql_log_min_deviation") or lastValue['repeats'] >= 9:
            self.lastValues[sensorId] = {'value': sensorValue, 'repeats': 0}
            return True, lastValue['repeats'] >= 9
        else:
            return False, False

    async def run(self):
        """
        Initializes the configuration settings and establishes a connection pool to the SQL database.
        """
        configSettings = [
            ("sql_log_active", False, "Do you want to log your values to an SQL database? Requires reboot.", [{"label": "Yes", "value": True}, {"label": "No", "value": False}], ConfigType.SELECT),
            ("sql_log_server", "", "SQL server address", None, ConfigType.STRING),
            ("sql_log_username", "", "Username for the SQL server", None, ConfigType.STRING),
            ("sql_log_password", "", "Password for the SQL server", None, ConfigType.STRING),
            ("sql_log_database", "", "Name of the SQL database", None, ConfigType.STRING),
            ("sql_log_min_deviation", 0.3, "Minimum deviation for logging to SQL database", None, ConfigType.NUMBER)
        ]

        for settingName, defaultValue, description, options, settingType in configSettings:
            value = getattr(self.cbpi.config, 'get')(settingName, None)
            if value is None:
                logger.info(f"Initializing setting {settingName}")
                try:
                    await self.cbpi.config.add(settingName, defaultValue, type=settingType, description=description, source="craftbeerpi", options=options)
                except Exception as e:
                    logger.warning(f'Unable to update global setting "{settingName}". Error: {e}')

        # Create a connection pool for the SQL database
        self.pool = await aiomysql.create_pool(
            host=self.cbpi.config.get("sql_log_server"),
            port=3306,  # Standard MySQL port
            user=self.cbpi.config.get("sql_log_username"),
            password=self.cbpi.config.get("sql_log_password"),
            db=self.cbpi.config.get("sql_log_database"),
            loop=asyncio.get_event_loop()
        )

        # Register a listener for sensor data
        self.listenerID = self.cbpi.log.add_sensor_data_listener(self.logDataToSqlDB)
        logger.info(f"SqlDB sensor log target listener ID: {self.listenerID}")

    async def logDataToSqlDB(self, cbpi, id, value, timestamp, name):
        """
        Logs sensor data to the SQL database if it meets the criteria defined in shouldWriteSensorData.
        """
        if not all([self.cbpi.config.get(k) for k in ["sql_log_active", "sql_log_server", "sql_log_username", "sql_log_password", "sql_log_database"]]):
            logger.warning("Not all SQL settings set. ==> Quit function")
            return

        try:
            sensor = self.cbpi.sensor.find_by_id(id)
            if sensor:
                shouldWrite, isRepeated = self.shouldWriteSensorData(id, float(value))
                if shouldWrite or isRepeated:
                    await self.writeSensorDataToDb(name, id, float(value), timestamp)
        except aiomysql.Error as e:
            logger.error(f"SQL DB Error: {e}")

    async def writeSensorDataToDb(self, sensorName, sensorId, sensorValue, timestamp):
        """
        Writes the sensor data into the corresponding table in the SQL database.
        """
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                # Ensure the table exists
                createTableQuery = f"""
                CREATE TABLE IF NOT EXISTS sensor_{sensorId} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    value FLOAT,
                    timestamp DATETIME
                )
                """
                await cursor.execute(createTableQuery)

                # Insert the new sensor value
                insertQuery = f"INSERT INTO sensor_{sensorId} (value, timestamp) VALUES (%s, %s)"
                await cursor.execute(insertQuery, (sensorValue, timestamp))
                await connection.commit()

def setup(cbpi):
    cbpi.plugin.register("SensorLogTargetSqlDB", SensorLogTargetSqlDB)
