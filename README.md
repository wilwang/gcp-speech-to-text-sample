# Google Speech to Text + Natural Language Processing

This example will take an audio file, transcribe the dialogue to text, and run NLP processing on the transcription. It will save the output to a BigQuery table. The audio file should be saved in a cloud storage bucket. 

The code borrows heavily from code at https://github.com/googleapis/python-speech/blob/HEAD/samples/snippets/beta_snippets.py

It is written in the style of a Cloud Function so that it can be easily used in a function to automatically execute when new files are added to the cloud storage bucket. Look at some [example code] (https://github.com/wilwang/gcp-func-sample) around Cloud Functions to do so.

> This example uses a `wav` media file; different file types will require configuring the parameters for transcription request. Learn more about [encoding types](https://cloud.google.com/speech-to-text/docs/encoding).

# Pre-requisites

1. [Create a Cloud Storage Bucket](https://cloud.google.com/storage/docs/creating-buckets) where you will store media files to transcribe
2. [Enable the appropriate APIs](https://cloud.google.com/endpoints/docs/openapi/enable-api) (Speech to Text and NLP)
3. [Create a service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts) that has the Cloud Speech Administrator, BigQuery Data Editor, and Service Usage Consumer roles in the project
4. Grant the service account Storage Legacy Object Reader permission on the storage bucket created in step 1
5. Create a BigQuery table using [./stt_results.sql](./stt_results.sql)

# Running the code (using Cloud Shell)

The speech-to-txt SDK does not support running with end user credentials from the Google Cloud SDK or Google Cloud Shell. Use the service account to run this code. You will need to download the service account key and store locally where the code can access. In the sample code, the key is stored in a `creds` folder in the same directory as the python code. Set the environment variable GOOGLE_APPLICATION_CREDENTIALS to point to the location of the json key.

```
$ export GOOGLE_APPLICATION_CREDENTIALS=./creds/svc-stt-private-key.json

$ python main.py
```