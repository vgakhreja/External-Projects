from pyspark.sql import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from prophecy.utils import *
from prophecy.libs import typed_lit
from jsonread.config.ConfigStore import *
from jsonread.functions import *

def HistoricEvents(spark: SparkSession) -> DataFrame:
    return spark.read\
        .format("json")\
        .option("multiLine", True)\
        .schema(
          StructType([
            StructField("result", StructType([
              StructField("count", StringType(), True), StructField("events", ArrayType(
              StructType([
                StructField("category1", StringType(), True), StructField("category2", StringType(), True), StructField("date", StringType(), True), StructField("description", StringType(), True), StructField("granularity", StringType(), True), StructField("lang", StringType(), True)
            ]), 
              True
          ), True)
            ]), True)
        ])
        )\
        .load("dbfs:/Prophecy/8d2414fd5624f95be2d3b65f32dcc8c7/old_events_data.json")
