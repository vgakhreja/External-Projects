from pyspark.sql import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from prophecy.utils import *
from prophecy.libs import typed_lit
from job.config.ConfigStore import *
from job.udfs.UDFs import *

def Customer_Orders(spark: SparkSession) -> DataFrame:
    return spark.read\
        .schema(
          StructType([
            StructField("customer_id", IntegerType(), True), StructField("orders", LongType(), False), StructField("amounts", DoubleType(), True), StructField("account_length_days", IntegerType(), True)
        ])
        )\
        .option("header", True)\
        .option("sep", ",")\
        .option("ignoreLeadingWhiteSpace", True)\
        .option("ignoreTrailingWhiteSpace", True)\
        .csv("dbfs:/Prophecy/8d2414fd5624f95be2d3b65f32dcc8c7/CustomersOrders.csv")
