import os
import functions_framework
import proto
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import language_v1
from google.cloud import bigquery

PROJECT_ID = os.environ.get('GCP_PROJECT', 'wilwang-sandbox')
BQ_DATASET = os.environ.get('BQ_DATASET', 'sandbox_data')
BQ_TABLE = os.environ.get('BQ_TABLE', 'stt_results')

def transcribe_gcs(gcs_uri):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        # parameters for the WAV input file
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        language_code="en-US",

        # use enhanced model for more accurate transcription
        use_enhanced=True,

        # use model that handles audio from phone calls more accurately
        model="phone_call",
    )
    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=360)

    transcription = ""
    for result in response.results:
        transcription += f'{result.alternatives[0].transcript}.\n'
        print(u"Transcript: {}".format(result.alternatives[0].transcript))
        print("Confidence: {}".format(result.alternatives[0].confidence))

    json_str = proto.Message.to_json(response)

    return transcription, json_str


def nlp_analysis(textdata):
    client = language_v1.LanguageServiceClient()
    type_ = language_v1.Document.Type.PLAIN_TEXT
    language = "en"
    document = {"content": textdata, "type_": type_, "language": language}
    encoding_type = language_v1.EncodingType.UTF8

    response = client.analyze_entities(
        request={"document": document, "encoding_type": encoding_type}
    )

    entity_result = proto.Message.to_json(response)

    print ("=====ENTITY_DETECTION=====")
    for entity in response.entities:
        print("Representative name for the entity: {}".format(entity.name))

        # Get entity type, e.g. PERSON, LOCATION, ADDRESS, NUMBER, et al
        print("Entity type: {}".format(language_v1.Entity.Type(entity.type_).name))

        # Get the salience score associated with the entity in the [0, 1.0] range
        print("Salience score: {}".format(entity.salience))

        # Loop over the metadata associated with entity. For many known entities,
        # the metadata is a Wikipedia URL (wikipedia_url) and Knowledge Graph MID (mid).
        # Some entity types may have additional metadata, e.g. ADDRESS entities
        # may have metadata for the address street_name, postal_code, et al.
        for metadata_name, metadata_value in entity.metadata.items():
            print("{}: {}".format(metadata_name, metadata_value))

        # Loop over the mentions of this entity in the input document.
        # The API currently supports proper noun mentions.
        for mention in entity.mentions:
            print("Mention text: {}".format(mention.text.content))

            # Get the mention type, e.g. PROPER for proper noun
            print(
                "Mention type: {}".format(
                    language_v1.EntityMention.Type(mention.type_).name
                )
            )

    response = client.analyze_sentiment(
        request={"document": document, "encoding_type": encoding_type}
    )

    sentiment_result = proto.Message.to_json(response)

    print ("=====DOCUMENT SENTIMENT=====")
    # Get overall sentiment of the input document
    print("Document sentiment score: {}".format(response.document_sentiment.score))
    print("Document sentiment magnitude: {}".format(response.document_sentiment.magnitude))
    
    print ("=====SENTENCE SENTIMENT=====")
    # Get sentiment for all sentences in the document
    for sentence in response.sentences:
        print("Sentence text: {}".format(sentence.text.content))
        print("Sentence sentiment score: {}".format(sentence.sentiment.score))
        print("Sentence sentiment magnitude: {}".format(sentence.sentiment.magnitude))

    return entity_result, sentiment_result

def bq_import(gcs_uri, transcription, transcribe_json, entity_json, sentiment_json):
    client = bigquery.Client()

    table_id = bigquery.Table.from_string(f'{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}')
    rows_to_insert = [
        {
            u"source_file_uri": gcs_uri, 
            u"transcription": transcription, 
            u"transcribe_json": transcribe_json, 
            u"entity_json": entity_json, 
            u"sentiment_json": sentiment_json
        }
    ]

    errors = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))    


@functions_framework.cloud_event
def handle_gcs_event(cloud_event):
    data = cloud_event.data
    bucket = data['bucket']
    file = data['name']
    gcs_uri = f'gs://{bucket}/{file}'

    transcription, transcribe_result = transcribe_gcs(gcs_uri)
    entity_result, sentiment_result = nlp_analysis(transcription)
    bq_import(gcs_uri, transcription, transcribe_result, entity_result, sentiment_result)


## NOTE: REMOVE everything below if creating as a Cloud Function 
# fake a cloud event object
r = type('',(object,),
    {
        "data": 
        { 
            "bucket": "wilwang-sandbox-stt-media-files", 
            "name": "audio-files/commercial_mono.wav" 
        }
    })() 

# execute the handler function
handle_gcs_event(r)