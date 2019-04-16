# imports
import re
import ast
import time
import numpy as np
import pandas as pd
import pyspark
#pyspark dependencies
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import OneHotEncoderEstimator, StringIndexer, VectorAssembler
from pyspark.sql import SQLContext, functions as f
from pyspark.sql.types import *

#set the session for entry to dataframe api
spark = SparkSession \
        .builder \
        .appName("final")\
        .getOrCreate()

sc = spark.sparkContext


input = 'gs://trenk27/train.txt'
output = 'gs://trenk27/train_Processed'

# 13 features taking integer values and 26 taking categorical values - making total of 39 features + 1 outcome

outcomeField = [StructField("label", IntegerType(), True)]
quantFields = [StructField("intFeature"+str(i+1), IntegerType(), True) for i in np.arange(13)]
qualFields = [StructField("catFeature"+str(i+1), StringType(), True) for i in np.arange(26)]
schema = StructType(outcomeField + quantFields + qualFields)

#load the data into a spark dataframe
df = spark.read \
    .schema(schema) \
    .format("csv") \
    .load(input)

#clean up: drop duplicate rows; rows missing at least 30 out of 39 values (>= 3/4 of row-wise data); columns missing >= 3/4 of data 
drop_cols = ['intFeature12','catFeature22']

df = df.dropDuplicates() \
    .dropna(thresh=30) \
    .drop(*drop_cols)

#bucket categorical missing values into its own sub-category for all releveant columns
categoryCols = [col for col in  df.columns if 'cat' in col]

df = df.fillna("NA_Bucket", subset=categoryCols)

#assuming negative values in intFeature 2 were incorrectly coded and should be null
df = df.withColumn(
    'intFeature2', 
    f.when(f.col('intFeature2') < 0,None).otherwise(f.col('intFeature2'))
    )

#update categorical column values conditioned on the number of observations for each value
for c in categoryCols:
    
    #collect unique values with greater than 30 observations
    bucket = set(df.groupBy(c) \
    .count() \
    .filter(f.col('count') > 30) \
    .select(f.col(c)) \
    .rdd \
    .map(lambda x: x[0]) \
    .collect())
    
    #update dataframe with rare values (fewer than 30) as their own bucketed value
    df = df.withColumn(c, 
                   f.when(f.col(c).isin(bucket)
                        , f.col(c)).otherwise("Rare_Bucket"))


# update integer columns missing values with the column mean
integerCols = [col for col in  df.columns if 'int' in col]

#dict will be used as a parameter in na.fill to identify columns and repsective mean values
mean_dict = {}

for c in integerCols:
    #compute mean for each column
    col_mean = df.select(f.mean(f.col(c)).alias('mean')).collect()[0]['mean']
    mean_dict[c] = col_mean
    
df = df.na.fill(mean_dict)


#log transform int variables
for c in integerCols:
    df = df.withColumn(c, 
                   f.log(f.col(c)+1))


# normalize integer features
for c in integerCols:
    #compute mean for each column
    col_mean = df.select(f.mean(f.col(c)).alias('mean')).collect()[0]['mean']
    col_std = df.select(f.stddev(f.col(c)).alias('std')).collect()[0]['std']
    #update dataframe
    df = df.withColumn(c,(f.col(c) - col_mean)/col_std)

# write df to bucket for later use

df.write \
    .option("header", "true") \
    .csv(output)

