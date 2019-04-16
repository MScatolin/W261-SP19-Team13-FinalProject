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
from pyspark.ml.classification import LogisticRegression

#set the session for entry to dataframe api
spark = SparkSession \
        .builder \
        .appName("final")\
        .getOrCreate()

sc = spark.sparkContext

train_input = 'gs://trenk27/train_Processed/*.csv'
test_input = 'gs://trenk27/test_Processed/*.csv'
output = 'gs://trenk27/Predicted_Probs'


integerCols = ['intFeature1', 'intFeature2', 'intFeature3', 'intFeature4',
       'intFeature5', 'intFeature6', 'intFeature7', 'intFeature8',
       'intFeature9', 'intFeature10', 'intFeature11', 'intFeature13']
       
categoryCols = ['catFeature1', 'catFeature2','catFeature3',
       'catFeature4', 'catFeature5', 'catFeature6',
       'catFeature7', 'catFeature8', 'catFeature9',
       'catFeature10', 'catFeature11', 'catFeature12',
       'catFeature13', 'catFeature14', 'catFeature15',
       'catFeature16', 'catFeature17', 'catFeature18',
       'catFeature19', 'catFeature20', 'catFeature21',
       'catFeature23', 'catFeature24', 'catFeature25',
       'catFeature26']

#set train and test schemas
outcomeField = [StructField("click", IntegerType(), True)]
quantFields = [StructField(f, DoubleType(), True) for f in integerCols]
qualFields = [StructField(f, StringType(), True) for f in categoryCols]

train_schema = StructType(outcomeField + quantFields + qualFields)
#note test dataset has no target variable
test_schema = StructType(quantFields + qualFields)


#read in the train data as spark df
train_df = spark.read \
    .schema(train_schema) \
    .format("csv") \
    .load(train_input)

#read in the test data as spark df
test_df = spark.read \
    .schema(test_schema) \
    .format("csv") \
    .load(test_input)


#set handle invalid to keep to account for any unseen categorical data in the test set
target = ['click']
indexers = [StringIndexer(inputCol=c, outputCol="{0}_indexed".format(c), handleInvalid="skip") for c in categoryCols]
label = StringIndexer(inputCol= target[0], outputCol="label")


#formatting for logistic regression
encoder = OneHotEncoderEstimator(
    inputCols=[indexer.getOutputCol() for indexer in indexers],
    outputCols=["{0}_encoded".format(indexer.getOutputCol()) for indexer in indexers],
    dropLast=False)

assembler = VectorAssembler(
    inputCols= encoder.getOutputCols() + integerCols,
    outputCol= "features")

lr = LogisticRegression(maxIter=10)

pipeline = Pipeline(stages = indexers + [encoder,assembler,label,lr])


# fit train data with LogisticRegression model using the pipeline
lr_model = pipeline.fit(train_df)

# Make predictions on test data using the transform() method. - LogisticRegression.transform() will only use the 'features' column.
predictions = lr_model.transform(test_df)
selected = predictions.select("prediction", "probability")

#convert probability column to string to write out to csv
selected.withColumn("probability", f.col("probability").cast(StringType())) \
    .repartition(1) \
    .write \
    .option("header", "true") \
    .csv(output)

