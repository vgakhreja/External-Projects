from pyspark.sql import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from prophecy.utils import *
from prophecy.libs import typed_lit
from jsonread.config.ConfigStore import *
from jsonread.functions import *

def WriteHistoric(spark: SparkSession, in0: DataFrame):
    in0.write\
        .format("json")\
        .mode("overwrite")\
        .save("dbfs:/Prophecy/8d2414fd5624f95be2d3b65f32dcc8c7/historic_events_flat.json")
