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

#read in the train data as spark df
train_df = spark.read \
    .schema(train_schema) \
    .format("csv") \
    .load(train_input)

#Randomly split data into training and test sets. set seed for reproducibility
(trainingData, testData) = train_df.randomSplit([0.7, 0.3], seed=100)

#converting categorical features to numeric indices for model formatting
target = ['click']
indexers = [StringIndexer(inputCol=c, outputCol="{0}_indexed".format(c), handleInvalid="keep") for c in categoryCols]
label = StringIndexer(inputCol= target[0], outputCol="label")


#one hot encoding categorical features to reduce dimensionality for model training:
'''note: one-hot encoding maps a categorical feature, represented as a label index, to a binary vector 
with at most a single one-value indicating the presence of a specific feature value from the set of all feature values.'''

encoder = OneHotEncoderEstimator(
    inputCols=[indexer.getOutputCol() for indexer in indexers],
    outputCols=["{0}_encoded".format(indexer.getOutputCol()) for indexer in indexers],
    dropLast=False)

#combining all the feature columns into a single vector column
assembler = VectorAssembler(
    inputCols= encoder.getOutputCols() + integerCols,
    outputCol= "features")

#creating instance of a logistic regression model
lr = LogisticRegression(maxIter=10)

#laying down pipeline for model fitting
pipeline = Pipeline(stages = indexers + [encoder,assembler,label,lr])


# fit train split  with LogisticRegression model using the pipeline
lr_model = pipeline.fit(trainingData)

#making predictions on test data using the transform method
predictions = lr_model.transform(testData)

#extracting true,predicted and probability to compute log loss 
selected = predictions.select("label", "prediction", "probability")


#---Evaluating Model with Log Loss------#
'''we want to extract the probability of a click which is the first element in the probability column
 so we need a user defined function to manipulate columns of array types since'''
firstelement = f.udf(lambda v:float(v[1]),FloatType())

#computing log loss - pyspark doesn't have a built-in method for this
pyspark_mod = selected.withColumn(
        'logloss'
        , -f.col('label')*f.log(firstelement(f.col('probability'))) - (1.-f.col('label'))*f.log(1.-firstelement(f.col('probability')))
    )

ll = pyspark_mod.agg(f.mean('logloss').alias('ll')).collect()[0]['ll']

#print log loss
print("The log loss from our logistic regression model is: " + str(ll))

