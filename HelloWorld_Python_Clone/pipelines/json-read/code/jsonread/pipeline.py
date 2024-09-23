from pyspark.sql import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from jsonread.config.ConfigStore import *
from jsonread.functions import *
from prophecy.utils import *
from jsonread.graph import *

def pipeline(spark: SparkSession) -> None:
    df_HistoricEvents = HistoricEvents(spark)
    df_ExtractAsTable = ExtractAsTable(spark, df_HistoricEvents)
    WriteHistoric(spark, df_ExtractAsTable)

def main():
    spark = SparkSession.builder\
                .config("spark.default.parallelism", "4")\
                .config("spark.sql.legacy.allowUntypedScalaUDF", "true")\
                .enableHiveSupport()\
                .appName("json-read")\
                .getOrCreate()
    Utils.initializeFromArgs(spark, parse_args())
    spark.conf.set("prophecy.metadata.pipeline.uri", "pipelines/json-read")
    registerUDFs(spark)
    
    MetricsCollector.instrument(spark = spark, pipelineId = "pipelines/json-read", config = Config)(pipeline)

if __name__ == "__main__":
    main()
