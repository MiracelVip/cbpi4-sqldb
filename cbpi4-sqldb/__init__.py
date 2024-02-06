# -*- coding: utf-8 -*-
import logging
import asyncio
from cbpi.api import *
from cbpi.api.config import ConfigType
import aiomysql

# Test for Commit 3
logger = logging.getLogger(__name__)

class SensorLogTargetSqlDB(CBPiExtension):

    def __init__(self, cbpi):
        self.cbpi = cbpi

        self.sqldb = self.cbpi.config.get("sql_log_active", False)
        if not self.sqldb:
            return

        self._task = asyncio.create_task(self.run())

    async def run(self):
        config_settings = [
            ("sql_log_active", False, "Do you want to log your values to a sql database? Require reboot.", [{"label": "Yes", "value": True}, {"label": "No", "value": False}], ConfigType.SELECT),
            ("sql_log_server", "", "SQL server address", None, ConfigType.STRING),
            ("sql_log_username", "", "Username for the SQL server", None, ConfigType.STRING),
            ("sql_log_password", "", "Password for the SQL server", None, ConfigType.STRING),
            ("sql_log_database", "", "Name of the SQL database", None, ConfigType.STRING)
        ]

        for setting_name, default_value, description, options, setting_type in config_settings:
            value = getattr(self.cbpi.config, 'get')(setting_name, None)
            if value is None:
                logger.info(f"INIT {setting_name} Setting")
                try:
                    await self.cbpi.config.add(setting_name, default_value, type=setting_type, description=description, source="craftbeerpi", options=options)
                except Exception as e:
                    logger.warning(f'Unable to update global setting "{setting_name}". Error: {e}')

        self.pool = await aiomysql.create_pool(
            host=self.cbpi.config.get("sql_log_server"),
            port=3306,  # Standard MySQL-Port
            user=self.cbpi.config.get("sql_log_username"),
            password=self.cbpi.config.get("sql_log_password"),
            db=self.cbpi.config.get("sql_log_database"),
            loop=asyncio.get_event_loop()
        )

        self.listener_ID = self.cbpi.log.add_sensor_data_listener(self.log_data_to_sqlDB)
        logger.info("SqlDB sensor log target listener ID: {}".format(self.listener_ID))

    async def log_data_to_sqlDB(self, cbpi, id:str, value:str, timestamp, name):
        if not (self.cbpi.config.get("sql_log_active", False) and 
            self.cbpi.config.get("sql_log_server") and 
            self.cbpi.config.get("sql_log_username") and 
            self.cbpi.config.get("sql_log_password") and 
            self.cbpi.config.get("sql_log_database")):
            logger.warning("Not all SQL settings set. ==> Quit function")
            return

        try:
            sensor = self.cbpi.sensor.find_by_id(id)
            if sensor is not None:
                await self.write_sensor_data_to_db(name, id, float(value), timestamp)
        except aiomysql.Error as e:
            logger.error(f"SqlDb ID Error: {e}")

    async def write_sensor_data_to_db(self, sensor_name:str, sensor_id:str, sensor_value:float, timestamp):
        async with self.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {sensor_id} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    value FLOAT,
                    timestamp DATETIME
                )
                """
                await cursor.execute(create_table_query)

                insert_query = f"INSERT INTO {sensor_id} (value, timestamp) VALUES (%s, %s)"
                await cursor.execute(insert_query, (sensor_value, timestamp))
                await connection.commit()

def setup(cbpi):
    cbpi.plugin.register("SensorLogTargetSqlDB", SensorLogTargetSqlDB)
