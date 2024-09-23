from pyspark.sql import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from prophecy.utils import *
from prophecy.libs import typed_lit
from jsonread.config.ConfigStore import *
from jsonread.functions import *

def ExtractAsTable(spark: SparkSession, in0: DataFrame) -> DataFrame:
    flt_col = in0.withColumn("result-events", explode_outer("result.events")).columns
    selectCols = [col("result-events-category1") if "result-events-category1" in flt_col else col("result-events.category1")\
                    .alias("result-events-category1"),                   col("result-events-category2") if "result-events-category2" in flt_col else col("result-events.category2")\
                    .alias("result-events-category2"),                   col("result-events-date") if "result-events-date" in flt_col else col("result-events.date")\
                    .alias("result-events-date"),                   col("result-events-description") if "result-events-description" in flt_col else col("result-events.description")\
                    .alias("result-events-description")]

    return in0.withColumn("result-events", explode_outer("result.events")).select(*selectCols)
